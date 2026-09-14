#!/usr/bin/env python3
"""Companion to glyph_mirror: is any glyph printed ROTATED 180 (the other
physical form of 'mirror writing'), or vertically flipped?"""
import sys, numpy as np
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from glyph_mirror import glyphs, norm

G, meta = [], []
for p in sys.argv[1:]:
    for x, y, w, h, m in glyphs(p):
        G.append(norm(m)); meta.append((p.split('/')[-1], x, y))
X = np.stack([g.ravel() for g in G])
R = np.stack([np.rot90(g, 2).ravel() for g in G])
V = np.stack([np.flipud(g).ravel() for g in G])
print(f'{len(X)} glyphs')
for name, Q in (('rot180', R), ('vflip', V)):
    bu = np.empty(len(X)); bq = np.empty(len(X))
    for s in range(0, len(X), 400):
        e = min(s + 400, len(X))
        Cu = X[s:e] @ X.T; Cq = Q[s:e] @ X.T
        for k in range(e - s):
            Cu[k, s + k] = -9; Cq[k, s + k] = -9
        bu[s:e] = Cu.max(1); bq[s:e] = Cq.max(1)
    gain = bq - bu
    z = (gain - gain.mean()) / gain.std()
    i = int(np.argmax(gain))
    print(f'{name}: beats-upright {int((gain>0).sum())}/{len(X)}  '
          f'max gain {gain.max():.3f}  max z {z.max():.2f}  '
          f'z>5 {int((z>5).sum())}  top at {meta[i]}')
