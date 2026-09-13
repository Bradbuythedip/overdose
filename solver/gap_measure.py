#!/usr/bin/env python3
"""
Measure inter-word gaps, in character-cell units, from the page images.

WHY THIS ONE IS WORTH DOING AT THIS RESOLUTION
----------------------------------------------
The per-character bold cipher died because the bold/regular stroke delta is
under one pixel at ~215 dpi (see window/bold_cipher_resolved.md). Gap width is
a completely different proposition: one character cell is ~30 px here, so a
two-cell gap differs from a one-cell gap by ~30 px. That is orders of magnitude
above the noise floor. If the article encodes anything in spacing, this can
read it.

And the article visibly does have anomalous gaps:
    "Really?          Yes."
    "Fact:          It's Layer 1 for every great thing"
    "at XRP.        Get ready to experience shitcoin hell."
    "Marty Bent -     who spend their days pouring over spreadsheets"
Those space counts in article_transcript.txt are eyeballed. These are measured.

METHOD
------
The body face is a typewriter font, so glyph origins should lie on a fixed
pitch grid. The pitch is estimated per line as the median of within-word
advances, then each inter-glyph advance is converted to cells. A normal word
space is 1 cell; anything >= 2 is flagged.

The script does NOT assume the font is monospace -- it reports how tightly the
advances actually quantize, so if the grid assumption fails that shows up as a
poor quantization residual rather than as confident nonsense.

  python3 gap_measure.py --page ../IMG_6247.jpeg
"""
import argparse, os, sys

import numpy as np

import bold_extract as B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--min-cells", type=int, default=2,
                    help="report gaps of at least this many cells")
    a = ap.parse_args()

    im, g = B.load_gray(a.page, a.scale)
    ink, thr, bars = B.ink_mask(g)
    comps = B.components(ink, 14 * a.scale // 2, 90 * a.scale // 2, 40)

    # Confine to the main text column. The torn page edge and the rotated
    # "Bitcoin Magazine | El Salvador" sidebar produce components that get
    # grouped into text lines and then read as 20-30 cell "gaps" -- they are
    # column jumps, not spacing. Keep the dense middle of the x distribution.
    if comps:
        xs_all = np.array([c["bbox"][0] for c in comps])
        lo, hi = np.percentile(xs_all, [4, 97])
        margin = 3 * a.scale
        comps = [c for c in comps
                 if lo - margin <= c["bbox"][0] <= hi + margin]

    lines = B.group_lines(comps, tol=12 * a.scale)

    sys.stderr.write(f"{os.path.basename(a.page)}  {len(comps)} glyphs, "
                     f"{len(lines)} lines\n")

    all_res, findings = [], []
    for li, ln in enumerate(lines):
        if len(ln) < 8:
            continue
        # drop marks that are too small to be letters (periods, quotes):
        # they sit inside a cell and would corrupt the advance sequence.
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        gl = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.45 * hmed]
        if len(gl) < 8:
            continue
        xs = np.array([c["bbox"][0] for c in gl], dtype=float)
        adv = np.diff(xs)
        if len(adv) < 6:
            continue
        # pitch = median of the advances that are plainly within-word
        small = adv[adv <= np.percentile(adv, 60)]
        pitch = float(np.median(small)) if len(small) else float(np.median(adv))
        if pitch <= 2:
            continue
        cells = adv / pitch
        # how well do advances land on integers? (grid-assumption check)
        res = np.abs(cells - np.round(cells))
        all_res.append(float(np.median(res)))

        for k, c in enumerate(cells):
            n = int(round(c))
            # advance of n cells = n-1 spaces. Cap at 15: anything wider is a
            # column jump or a dropped word, not deliberate spacing.
            if a.min_cells + 1 <= n <= 16:
                findings.append((li, k, n - 1, float(c),
                                 int(xs[k]), int(gl[k]["bbox"][1])))

    if all_res:
        med = float(np.median(all_res))
        sys.stderr.write(f"  grid quantization residual (median |cells - "
                         f"round(cells)|): {med:.3f}\n")
        sys.stderr.write("  " + ("advances quantize well -- monospace grid holds"
                                 if med < 0.15 else
                                 "POOR quantization -- treat cell counts as "
                                 "unreliable") + "\n")

    sys.stderr.write(f"  {len(findings)} gaps of >= {a.min_cells} spaces\n")
    for li, k, spaces, raw, x, y in findings:
        sys.stderr.write(f"    line {li:3d} pos {k:3d}  {spaces} spaces "
                         f"(raw {raw:.2f} cells)  at x={x} y={y}\n")

    print("\t".join(["line", "pos", "spaces", "raw_cells", "x", "y"]))
    for row in findings:
        li, k, spaces, raw, x, y = row
        print(f"{li}\t{k}\t{spaces}\t{raw:.3f}\t{x}\t{y}")


if __name__ == "__main__":
    main()
