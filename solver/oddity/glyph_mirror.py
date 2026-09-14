#!/usr/bin/env python3
"""
Per-glyph MIRROR detector.

Keiser's one follow-up clue was mirror writing (he quoted G D Schott's paper).
Every mirror test in this repo so far has been a STRING reversal or a whole-page
image flip.  Nobody has asked the physical question: is any single glyph on the
page printed mirror-reversed?  In a monospace typewriter face that is visible.

Method: pull every ink blob of glyph size, normalise to a 24x24 box, and for
each glyph find its nearest neighbour among all other glyphs upright (d_up) and
the nearest neighbour of its horizontal flip (d_flip).  A glyph that matches the
corpus far better mirrored than upright is a mirrored glyph.
"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage

def glyphs(path, rot180=True):
    im = Image.open(path).convert('L')
    if rot180: im = im.rotate(180)
    a = np.asarray(im).astype(np.uint8)
    ink = a < 120                       # dark ink only
    lab, n = ndimage.label(ink)
    objs = ndimage.find_objects(lab)
    out = []
    for i, sl in enumerate(objs, 1):
        if sl is None: continue
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if not (14 <= h <= 60 and 6 <= w <= 55): continue
        m = (lab[sl] == i)
        if m.sum() < 40: continue
        if m.sum() / (h * w) > 0.92: continue        # solid block
        out.append((sl[1].start, sl[0].start, w, h, m))
    return out

def norm(m, S=24):
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((S, S), Image.BILINEAR)
    v = np.asarray(im).astype(np.float32) / 255.0
    v -= v.mean()
    nrm = np.linalg.norm(v)
    return v / nrm if nrm > 1e-6 else v

def run(paths):
    G, meta = [], []
    for p in paths:
        gs = glyphs(p)
        for x, y, w, h, m in gs:
            G.append(norm(m)); meta.append((p, x, y, w, h))
        sys.stderr.write(f'{p}: {len(gs)} glyphs\n')
    X = np.stack([g.ravel() for g in G])
    F = np.stack([np.fliplr(g).ravel() for g in G])
    sys.stderr.write(f'total {len(X)} glyphs, correlating...\n')
    # cosine similarity; vectors already zero-mean unit-norm
    best_up = np.empty(len(X)); best_fl = np.empty(len(X))
    jup = np.empty(len(X), dtype=int); jfl = np.empty(len(X), dtype=int)
    B = 400
    for s in range(0, len(X), B):
        e = min(s + B, len(X))
        Cu = X[s:e] @ X.T
        Cf = F[s:e] @ X.T
        for k in range(e - s):
            Cu[k, s + k] = -9; Cf[k, s + k] = -9
        jup[s:e] = Cu.argmax(1); best_up[s:e] = Cu.max(1)
        jfl[s:e] = Cf.argmax(1); best_fl[s:e] = Cf.max(1)
    gain = best_fl - best_up
    order = np.argsort(-gain)
    print(f'{"gain":>6} {"sim_up":>7} {"sim_flip":>8}  page  x     y     w  h')
    for i in order[:30]:
        p, x, y, w, h = meta[i]
        print(f'{gain[i]:6.3f} {best_up[i]:7.3f} {best_fl[i]:8.3f}  '
              f'{p.split("/")[-1]:20s} {x:5d} {y:5d} {w:3d} {h:3d}')
    print()
    print(f'glyphs where mirrored match beats upright: '
          f'{int((gain>0).sum())} / {len(X)}')
    print(f'gain mean {gain.mean():.4f} sd {gain.std():.4f} max {gain.max():.4f}')
    z = (gain - gain.mean()) / gain.std()
    print(f'max z = {z.max():.2f}; glyphs with z>5: {int((z>5).sum())}')
    np.save('/home/user/overdose/solver/oddity/glyph_gain.npy', gain)
    import json
    json.dump([[m[0], int(m[1]), int(m[2]), int(m[3]), int(m[4])] for m in meta],
              open('/home/user/overdose/solver/oddity/glyph_meta.json', 'w'))

if __name__ == '__main__':
    run(sys.argv[1:])
