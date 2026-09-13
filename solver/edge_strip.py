#!/usr/bin/env python3
"""
Cut the TRUE left-edge and right-edge word of every printed line, from pixels.

WHY: column_cipher.py reads the line-edge null ciphers off article_transcript.txt,
whose line breaks are my transcription of the printed lines. One misread line
break silently shifts every entry in the column and there would be no sign of
it. This derives the same two columns independently, from the image, and
renders them as strip images so they can be read directly -- no OCR, no
transcription, nothing to trust but the pixels.

If the two derivations agree, the column cipher result is sound. If they
disagree, the transcript is wrong and the disagreement says exactly where.

Reuses bold_extract's binarization, component and line-grouping code, and the
same text-column bounding that gap_measure.py needed to keep the torn page edge
and the rotated sidebar out of the line grouping.

  python3 edge_strip.py --page ../IMG_6247.jpeg --out /tmp/ocr/p76edge
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
    a = ap.parse_args()

    im, g = B.load_gray(a.page, a.scale)
    ink, thr, bars = B.ink_mask(g)
    comps = B.components(ink, 14 * a.scale // 2, 90 * a.scale // 2, 40)

    # Do NOT clip the text column by percentile here. gap_measure.py can afford
    # that because it only needs advances between glyphs, but this tool reads
    # the LEFT EDGE, and a 4th-percentile lower bound removes exactly the first
    # character of every line in the page's left-aligned block -- which showed
    # up as "rolling" for "trolling", "ovogratz" for "Novogratz", "aybe" for
    # "Maybe". Keep every glyph and drop non-text by line size instead: the
    # rotated sidebar and the torn page edge never form lines of 8+ glyphs.
    lines = B.group_lines(comps, tol=12 * a.scale)
    lines = [ln for ln in lines if len(ln) >= 8]        # real text lines only

    left, right = [], []
    for ln in lines:
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        gl = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.45 * hmed]
        if len(gl) < 4:
            continue
        widths = np.array([c["bbox"][2] - c["bbox"][0] for c in gl])
        wmed = max(float(np.median(widths)), 1.0)

        # split the line into words on gaps wider than ~0.6 of a glyph width
        wordsl, cur = [], [gl[0]]
        for prev, c in zip(gl, gl[1:]):
            if c["bbox"][0] - prev["bbox"][2] > 0.6 * wmed:
                wordsl.append(cur)
                cur = [c]
            else:
                cur.append(c)
        wordsl.append(cur)
        if not wordsl:
            continue

        # Reject leading/trailing debris by DISTANCE rather than by position.
        # The torn page edge and the rotated sidebar sit tens of character
        # widths away from the text; a real inter-word gap is 1-2. Percentile
        # clipping cannot separate these, because on a page with both a
        # centred block and a left-aligned block the tear and the genuine
        # first letters occupy the same x range.
        FAR = 5.0
        while len(wordsl) > 1 and \
                wordsl[1][0]["bbox"][0] - wordsl[0][-1]["bbox"][2] > FAR * wmed:
            wordsl.pop(0)
        while len(wordsl) > 1 and \
                wordsl[-1][0]["bbox"][0] - wordsl[-2][-1]["bbox"][2] > FAR * wmed:
            wordsl.pop()
        if not wordsl:
            continue

        def box(wd):
            return (min(c["bbox"][0] for c in wd), min(c["bbox"][1] for c in wd),
                    max(c["bbox"][2] for c in wd), max(c["bbox"][3] for c in wd))

        left.append(box(wordsl[0]))
        right.append(box(wordsl[-1]))

    sys.stderr.write(f"{os.path.basename(a.page)}: {len(lines)} text lines, "
                     f"{len(left)} edge words\n")
    if not left:
        sys.exit("no lines found")

    for name, boxes in (("left", left), ("right", right)):
        pad = 8
        cw = max(b[2] - b[0] for b in boxes) + pad
        ch = max(b[3] - b[1] for b in boxes) + pad
        strip = Image.new("L", (cw, ch * len(boxes)), 255)
        for i, b in enumerate(boxes):
            strip.paste(im.crop(b), (pad // 2, i * ch + pad // 2))
        p = f"{a.out}_{name}.png"
        strip.save(p)
        sys.stderr.write(f"  wrote {p}  ({len(boxes)} words, {strip.size})\n")


if __name__ == "__main__":
    main()
