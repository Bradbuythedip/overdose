#!/usr/bin/env python3
"""
Detect per-character BOLD marking in the Overdose page scans.

Keiser (tweet 1607378060172460032, Dec 2022): "Like George Sand's hidden
cryptography, I have hidden private keys in the text." George Sand's trick is a
positional/null cipher. In these pages the marking is not position but WEIGHT:
individual characters are set in a bold face mid-word ("r-ipped", "c-e-ntra-l",
"b-ank-e-rs"), which no ordinary emphasis does.

This segments text lines and glyphs, measures per-glyph ink density and stroke
width, and flags outliers as bold. It does not OCR -- it emits crops of the
flagged glyphs in reading order so they can be read off reliably.

  python3 bold_extract.py IMG_6247.jpeg --out /tmp/od/p76
"""
import argparse, os, sys
from PIL import Image
import numpy as np

def load_gray(path):
    im = Image.open(path).convert('L')
    return im, np.asarray(im, dtype=np.float32)

def find_lines(bw, min_gap=6, min_h=10):
    rows = bw.sum(axis=1)
    on = rows > (0.004 * bw.shape[1] * 255)
    lines, s = [], None
    for i, v in enumerate(on):
        if v and s is None: s = i
        elif not v and s is not None:
            if i - s >= min_h: lines.append((s, i))
            s = None
    if s is not None and len(on) - s >= min_h: lines.append((s, len(on)))
    return lines

def glyphs_in_line(bw, y0, y1, min_gap=2):
    seg = bw[y0:y1]
    cols = seg.sum(axis=0)
    on = cols > 0
    out, s = [], None
    for i, v in enumerate(on):
        if v and s is None: s = i
        elif not v and s is not None:
            out.append((s, i)); s = None
    if s is not None: out.append((s, len(on)))
    # merge fragments separated by < min_gap (dotted i, quotes)
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] < min_gap: merged[-1] = (merged[-1][0], b)
        else: merged.append((a, b))
    return [(a, b) for a, b in merged if b - a >= 3]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('--out', default='/tmp/od/bold')
    ap.add_argument('--thresh', type=float, default=150)
    ap.add_argument('--zoom', type=int, default=5)
    ap.add_argument('--sigma', type=float, default=1.0,
                    help='flag glyphs this many stdevs above the line mean stroke width')
    ap.add_argument('--x0', type=int, default=0, help='left edge of body text column')
    ap.add_argument('--x1', type=int, default=0, help='right edge (0 = image width)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    im, g = load_gray(a.image)
    if a.x1 == 0: a.x1 = g.shape[1]
    g = g[:, a.x0:a.x1]                 # crop out torn margins and the sidebar
    im = im.crop((a.x0, 0, a.x1, im.height))
    bw = (g < a.thresh).astype(np.float32) * 255      # ink = 1
    lines = find_lines(bw)
    sys.stderr.write(f"{a.image}: {im.size}, {len(lines)} text lines\n")
    report = open(os.path.join(a.out, 'bold_report.tsv'), 'w')
    report.write("line\tglyph\tx0\tx1\ty0\ty1\tdensity\tline_mean\tline_std\tz\tflag\n")
    nb = 0
    for li, (y0, y1) in enumerate(lines):
        gl = glyphs_in_line(bw, y0, y1)
        if len(gl) < 5: continue
        dens = []
        for x0, x1 in gl:
            box = (bw[y0:y1, x0:x1] > 0)
            # stroke width = mean length of horizontal ink runs (weight, not shape)
            runs = []
            for row in box:
                c = 0
                for v in row:
                    if v: c += 1
                    elif c: runs.append(c); c = 0
                if c: runs.append(c)
            runs = [r for r in runs if r >= 2]        # ignore antialias specks
            dens.append(float(np.median(runs)) if runs else 0.0)
        dens = np.array(dens)
        mu, sd = dens.mean(), dens.std() + 1e-9
        for (x0, x1), d in zip(gl, dens):
            z = (d - mu) / sd
            flag = 'BOLD' if z >= a.sigma else ''
            if flag: nb += 1
            report.write(f"{li}\t{x0}\t{x0}\t{x1}\t{y0}\t{y1}\t{d:.4f}\t{mu:.4f}\t{sd:.4f}\t{z:.2f}\t{flag}\n")
        # emit an annotated strip per line for visual read-back
        strip = im.crop((0, max(0, y0-4), im.width, min(im.height, y1+4)))
        strip = strip.resize((strip.width*2, strip.height*2), Image.LANCZOS)
        strip.save(os.path.join(a.out, f'line_{li:03d}.png'))
    report.close()
    sys.stderr.write(f"flagged {nb} bold glyphs -> {a.out}/bold_report.tsv\n")

if __name__ == '__main__':
    main()
