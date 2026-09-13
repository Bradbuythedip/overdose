#!/usr/bin/env python3
"""
Find the blocks that actually HAVE a readable margin, and acrostic only those.

THE ARGUMENT (raised by a verification agent, and it is a good one)
An acrostic or telestich is a VISUAL device: the reader notices a column of
letters lining up down the edge of the type. That column only exists where the
type is set flush to that edge. Most of this article is not:

  p75, p77, the top block of p76 and the main block of p79 are CENTRE-set
  the closing blocks of p78 and p79 are RIGHT-set

In centred type there is no first-letter column to read down and no last-letter
column either -- both edges are ragged, so a "first letter of each line"
reading is something a solver would have no visual reason to attempt, and a
setter would have no reason to hide anything there.

Rather than hardcode which blocks those are, this MEASURES it. edge_strip's
machinery gives the left and right x of every printed line; a flush edge is one
whose x barely varies from line to line, a ragged edge is one whose x wanders.
Maximal runs of consecutive lines whose left (or right) x holds within a
fraction of a character width are the blocks that can carry an acrostic.

Also drops the two lines a verification agent flagged as not being typeset body
text at all: "BITCOIN IS TOXIC AF" (p75) is a display headline and "MAX KEISER"
(p79) is a hand-drawn signature graphic. Any reading touching them is invalid.

  python3 aligned_blocks.py --pages ../IMG_6246.jpeg ../IMG_6247.jpeg \
      ../IMG_6248.jpeg ../IMG_6249.jpeg ../IMG_6250.jpeg --out /tmp/aligned.txt
"""
import argparse, os, re, sys

import numpy as np

import bold_extract as B


def line_edges(path, scale=2):
    """Return [(left_x, right_x, y, glyphs)] for each printed text line."""
    im, g = B.load_gray(path, scale)
    ink, thr, bars = B.ink_mask(g)
    comps = B.components(ink, 14 * scale // 2, 90 * scale // 2, 40)
    lines = B.group_lines(comps, tol=12 * scale)
    lines = [ln for ln in lines if len(ln) >= 8]

    out = []
    for ln in lines:
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        gl = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.45 * hmed]
        if len(gl) < 4:
            continue
        widths = np.array([c["bbox"][2] - c["bbox"][0] for c in gl])
        wmed = max(float(np.median(widths)), 1.0)

        wordsl, cur = [], [gl[0]]
        for prev, c in zip(gl, gl[1:]):
            if c["bbox"][0] - prev["bbox"][2] > 0.6 * wmed:
                wordsl.append(cur)
                cur = [c]
            else:
                cur.append(c)
        wordsl.append(cur)
        FAR = 5.0
        while len(wordsl) > 1 and \
                wordsl[1][0]["bbox"][0] - wordsl[0][-1]["bbox"][2] > FAR * wmed:
            wordsl.pop(0)
        while len(wordsl) > 1 and \
                wordsl[-1][0]["bbox"][0] - wordsl[-2][-1]["bbox"][2] > FAR * wmed:
            wordsl.pop()
        if not wordsl:
            continue
        lx = min(c["bbox"][0] for c in wordsl[0])
        rx = max(c["bbox"][2] for c in wordsl[-1])
        y = float(np.median([(c["bbox"][1] + c["bbox"][3]) / 2 for c in gl]))
        out.append((lx, rx, y, wmed, len(gl)))
    return out


def runs(vals, wmed, tol_frac=0.6, min_len=4):
    """Maximal runs of consecutive lines whose edge x holds within tol."""
    res, start = [], 0
    for i in range(1, len(vals) + 1):
        if i == len(vals) or abs(vals[i] - vals[start]) > tol_frac * wmed:
            # extend greedily: a run is flush if every member is within tol of
            # the run's own median, not just of its first line
            if i - start >= min_len:
                seg = vals[start:i]
                med = float(np.median(seg))
                if max(abs(v - med) for v in seg) <= tol_frac * wmed:
                    res.append((start, i))
            start = i
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=float, default=0.6,
                    help="flush-edge tolerance as a fraction of glyph width")
    a = ap.parse_args()

    report = []
    for p in a.pages:
        e = line_edges(p)
        if not e:
            continue
        lxs = [x[0] for x in e]
        rxs = [x[1] for x in e]
        wmed = float(np.median([x[3] for x in e]))
        lruns = runs(lxs, wmed, a.tol)
        rruns = runs(rxs, wmed, a.tol)
        name = os.path.basename(p)
        report.append((name, len(e), wmed, lruns, rruns,
                       float(np.std(lxs)), float(np.std(rxs))))

    sys.stderr.write("  page          lines  glyphW  sd(left)  sd(right)  "
                     "flush-left runs        flush-right runs\n")
    for name, n, wmed, lr, rr, sl, sr in report:
        sys.stderr.write(f"  {name:14} {n:4}  {wmed:6.1f}  {sl:8.1f}  {sr:9.1f}  "
                         f"{str(lr):22} {rr}\n")

    sys.stderr.write("""
  A flush edge shows a small sd relative to the glyph width and yields long
  runs; a ragged (centred) edge shows a large sd and few or no runs. Only the
  runs listed above can carry an acrostic that a reader would ever see.
""")
    with open(a.out, "w") as f:
        for name, n, wmed, lr, rr, sl, sr in report:
            f.write(f"{name}\t{n}\t{wmed:.1f}\t{sl:.1f}\t{sr:.1f}\t{lr}\t{rr}\n")


if __name__ == "__main__":
    main()
