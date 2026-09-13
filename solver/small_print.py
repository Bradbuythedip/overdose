#!/usr/bin/env python3
"""
Find SMALL printed text anywhere on the pages, systematically.

THE GAP
Every vision pass over these pages read them at roughly 2000 px on the long
edge. The body type is ~30 px tall at full resolution, so it reads fine at that
scale — but anything set smaller (photo credits, captions, fine print, text
inside the artwork, a serial, a handwritten note) is illegible there and would
simply have been skipped. "@ANNABELLEBAZ" was only spotted because it happened
to be large enough.

Rather than guess where to zoom, this locates candidate small text
programmatically: connected components in a height band well below the body
type, grouped into horizontal runs of several glyphs. Isolated specks and
halftone noise do not form runs; words do.

Each run is cropped and upscaled so it can be read directly.

  python3 small_print.py --page ../IMG_6244.jpeg --out /tmp/ocr/small_p73
"""
import argparse, os, sys

import numpy as np
from PIL import Image

import bold_extract as B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--min-h", type=int, default=6, help="min glyph height, px @scale")
    ap.add_argument("--max-h", type=int, default=30, help="max glyph height, px @scale")
    ap.add_argument("--min-glyphs", type=int, default=4)
    a = ap.parse_args()

    im, g = B.load_gray(a.page, a.scale)
    ink, thr, bars = B.ink_mask(g)

    # small components only -- the body type is filtered out by max-h
    comps = B.components(ink, a.min_h, a.max_h, 8)
    sys.stderr.write(f"{os.path.basename(a.page)}: {len(comps)} components in the "
                     f"{a.min_h}-{a.max_h}px height band\n")
    if not comps:
        return

    # group into horizontal runs: same baseline, small horizontal gaps
    lines = B.group_lines(comps, tol=6 * a.scale)
    runs = []
    for ln in lines:
        ln = sorted(ln, key=lambda c: c["bbox"][0])
        cur = [ln[0]]
        for prev, c in zip(ln, ln[1:]):
            gap = c["bbox"][0] - prev["bbox"][2]
            h = max(prev["bbox"][3] - prev["bbox"][1], 1)
            if gap > 3 * h:
                if len(cur) >= a.min_glyphs:
                    runs.append(cur)
                cur = [c]
            else:
                cur.append(c)
        if len(cur) >= a.min_glyphs:
            runs.append(cur)

    # drop runs that sit inside the main body-text block: those are just body
    # glyphs whose bounding boxes happened to fall in the band
    hs = np.array([c["bbox"][3] - c["bbox"][1] for c in comps])
    body_h = float(np.median(hs))
    keep = []
    for r in runs:
        mh = float(np.median([c["bbox"][3] - c["bbox"][1] for c in r]))
        if mh <= body_h * 0.8:
            keep.append((mh, r))
    keep.sort(key=lambda x: x[0])

    sys.stderr.write(f"  {len(runs)} horizontal runs, {len(keep)} smaller than "
                     f"0.8x the median glyph height ({body_h:.1f}px)\n")

    pad = 6
    made = 0
    for i, (mh, r) in enumerate(keep[:40]):
        x0 = min(c["bbox"][0] for c in r) - pad
        y0 = min(c["bbox"][1] for c in r) - pad
        x1 = max(c["bbox"][2] for c in r) + pad
        y1 = max(c["bbox"][3] for c in r) + pad
        w, h = x1 - x0, y1 - y0
        if w < 20 or h < 6:
            continue
        z = max(2, min(10, int(220 / max(h, 1))))
        crop = im.crop((x0, y0, x1, y1)).resize((w * z, h * z), Image.LANCZOS)
        p = f"{a.out}_run{i:02d}_h{mh:.0f}.png"
        crop.save(p)
        made += 1
        sys.stderr.write(f"    run {i:02d}  glyph_h={mh:4.1f}  {len(r):3d} glyphs  "
                         f"at ({x0//a.scale},{y0//a.scale})  {w}x{h}  -> {p}\n")
    sys.stderr.write(f"  wrote {made} crops\n")


if __name__ == "__main__":
    main()
