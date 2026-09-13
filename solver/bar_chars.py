#!/usr/bin/env python3
"""
Which characters do the highlight bars ACTUALLY cover, to the pixel?

THE GAP
highlights_ordered.tsv records the highlighted PHRASES, transcribed by word.
But a highlight is a rectangle, not a word selection: it has hard left and
right edges that can land mid-word. If the bar geometry is the cipher — and
that is the most Keiser-ish mechanism on the page, being visual and impossible
for a reader to miss — then a word-level catalogue is the wrong input, and
every test run against it was testing the wrong string.

This measures it. For each bar: which glyph boxes fall inside it, and what the
first and last covered glyph are. A bar that clips a word mid-way is exactly
the signal a character-level highlight cipher would produce, and it would be
invisible to every pass done so far.

Emits per bar: page, geometry, glyph count, and whether each edge lands cleanly
between words or cuts through one. The edge-cutting bars are the interesting
ones.

  python3 bar_chars.py --page ../IMG_6247.jpeg
"""
import argparse, os, sys

import numpy as np
from scipy import ndimage

import bold_extract as B


def find_bars(g, thr, scale):
    """Solid highlight rectangles: dark blobs that survive heavy erosion."""
    dark = g < thr
    core = ndimage.binary_erosion(dark, np.ones((9, 9)), iterations=2)
    core = ndimage.binary_dilation(core, np.ones((9, 9)), iterations=3)
    lab, n = ndimage.label(core)
    out = []
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        # a text highlight is wide, short, and at least a few characters long
        if h < 8 * scale or h > 40 * scale or w < 20 * scale:
            continue
        out.append((xs.start, ys.start, xs.stop, ys.stop))
    return sorted(out, key=lambda b: (b[1], b[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()

    im, g = B.load_gray(a.page, a.scale)
    ink, thr, bars_mask = B.ink_mask(g)
    bars = find_bars(g, thr, a.scale)
    comps = B.components(ink, 14 * a.scale // 2, 90 * a.scale // 2, 40)

    sys.stderr.write(f"{os.path.basename(a.page)}: {len(bars)} highlight bars, "
                     f"{len(comps)} glyphs\n\n")
    if not comps:
        return
    wmed = float(np.median([c["bbox"][2] - c["bbox"][0] for c in comps]))

    clipped = 0
    for bi, (x0, y0, x1, y1) in enumerate(bars):
        inside = [c for c in comps
                  if c["bbox"][0] >= x0 - 2 and c["bbox"][2] <= x1 + 2
                  and c["bbox"][1] >= y0 - 6 and c["bbox"][3] <= y1 + 6]
        if len(inside) < 2:
            continue
        inside.sort(key=lambda c: c["bbox"][0])

        # does either edge cut through a glyph, or through a word?
        near_l = [c for c in comps
                  if abs(c["bbox"][0] - x0) < 3 * wmed
                  and c["bbox"][1] >= y0 - 6 and c["bbox"][3] <= y1 + 6]
        near_r = [c for c in comps
                  if abs(c["bbox"][2] - x1) < 3 * wmed
                  and c["bbox"][1] >= y0 - 6 and c["bbox"][3] <= y1 + 6]
        cutl = any(c["bbox"][0] < x0 - 2 < c["bbox"][2] for c in near_l)
        cutr = any(c["bbox"][0] < x1 + 2 < c["bbox"][2] for c in near_r)
        if cutl or cutr:
            clipped += 1
        sys.stderr.write(
            f"  bar {bi:02d}  y={y0//a.scale:5}  x={x0//a.scale:5}-{x1//a.scale:<5} "
            f"{len(inside):3d} glyphs  width={(x1-x0)/wmed:5.1f} chars  "
            f"{'LEFT-CUT ' if cutl else ''}{'RIGHT-CUT' if cutr else ''}\n")

    sys.stderr.write(f"\n  bars whose edge cuts through a glyph: {clipped}\n")
    sys.stderr.write("  " + ("a character-level highlight cipher would show many "
                             "cut edges\n" if clipped > len(bars) * 0.3 else
                             "edges land between characters -- the highlighting is "
                             "word-aligned, so the word-level catalogue is the "
                             "correct input after all\n"))


if __name__ == "__main__":
    main()
