#!/usr/bin/env python3
"""
Read the BOLD runs off the pages, at full coverage this time.

WHY IT IS WORTH REDOING
Task #9 ran a whole-word bold null-cipher and returned 0 hits. It ran against
`wf/glyphs_p*.tsv`, which `looking_at_the_pages.md` measured as holding 61% of
the article -- 46% of page 77 and **15% of page 79**. So on the two pages where
coverage was worst, most bold words were never extracted at all, and the null
covers text the detector never saw.

`curve_residual.py` fixed the extraction: chaining glyphs left-to-right along
the baseline instead of bucketing by shared y recovers 1,083 glyphs on p79
against 149, and 1,489 on p77 against 593 -- line counts now matching the
printed line counts. This reads bold off that.

WHAT BOLD IS AND IS NOT
`bold_cipher_resolved.md` established that PER-CHARACTER weight tracks letter
identity: P(bold | character) is 0.158 for `c` and 0.476 for `a`, chi-square
93.9 on df 22. That is the font, and this does not dispute it.

But whole-word and whole-RUN bold is a different measurement. Looking at the
pages, bold appears in long contiguous runs -- one on p79 spans two and a half
lines and ends mid-line at "connect" -- which is editorial emphasis, a channel
distinct from both the highlight colour and the per-glyph font effect. Runs are
what this extracts.

THE CONTROL IS PUBLISHED
`looking_at_the_pages.md` records a ground truth: on p75 line 6 the old
detector flagged 14 of 56 glyphs and all 14 fell inside "They discount stuff in
advance.", none outside. A stroke-width measure that cannot reproduce that
separation is not measuring boldness, and its output is not worth sweeping.

  python3 bold_runs.py --selftest
  python3 bold_runs.py --pages 75,76,77,78,79 --out boldruns.tsv
"""
import argparse, sys

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("needs opencv")

import curve_residual as CR

BASE, IMG = CR.BASE, CR.IMG


def stroke_width(mask):
    """Mean stroke width of a glyph: 2x the mean distance-to-edge of its ink.

    Robust to glyph size and shape in a way that ink-area is not -- a bold `a`
    and a regular `m` can carry the same ink, but not the same stroke.
    """
    d = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 3)
    v = d[d > 0]
    return float(2.0 * v.mean()) if v.size else 0.0


def glyphs_with_weight(page):
    """(cx, baseline, w, h, stroke, height-normalised stroke) per glyph."""
    path = f"{BASE}/{IMG[page]}"
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, []
    th = cv2.threshold(cv2.GaussianBlur(img, (3, 3), 0), 0, 255,
                       cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if page == 77:
        th = cv2.bitwise_not(th)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(th, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if not (12 <= a <= 4000 and 3 <= w <= 80 and 4 <= h <= 90):
            continue
        if h > 6 * w or w > 8 * h:
            continue
        sw = stroke_width(lab[y:y + h, x:x + w] == i)
        out.append((float(cent[i][0]), float(y + h), w, h, sw,
                    sw / max(h, 1)))
    return img.shape, out


def runs_from(line, thresh):
    """Contiguous bold/regular runs along one line, as (is_bold, n_glyphs)."""
    out = []
    cur, n = None, 0
    for g in line:
        b = g[5] >= thresh
        if b == cur:
            n += 1
        else:
            if cur is not None:
                out.append((cur, n))
            cur, n = b, 1
    if cur is not None:
        out.append((cur, n))
    return out


def selftest():
    ok = True
    # stroke_width must separate a thick stroke from a thin one
    thin = np.zeros((40, 40), bool); thin[10:30, 19:21] = True
    thick = np.zeros((40, 40), bool); thick[10:30, 15:25] = True
    st, sk = stroke_width(thin), stroke_width(thick)
    good = sk > 2 * st
    ok &= good
    sys.stderr.write(f"  stroke width separates 2px from 10px strokes: "
                     f"{st:.2f} vs {sk:.2f} {'OK' if good else 'FAIL'}\n")

    # THE PUBLISHED CONTROL. p75 line 6 -- "They discount stuff in advance."
    # was measured as 14 of 56 glyphs bold, all inside the phrase. The line is
    # found by locating the line whose glyph count is ~56 in the upper third.
    shape, gl = glyphs_with_weight(75)
    if shape is None:
        sys.stderr.write("  p75 unreadable: FAIL\n")
        return False
    lines = CR.group_lines([(g[0], g[1], g[2], g[3]) for g in gl])
    by_key = {(round(g[0], 1), round(g[1], 1)): g for g in gl}
    sys.stderr.write(f"  p75: {len(gl)} glyphs, {len(lines)} lines\n")

    # bimodality: a page with real bold emphasis should NOT have a unimodal
    # normalised-stroke distribution
    ns = np.array([g[5] for g in gl])
    lo, hi = np.percentile(ns, [25, 75])
    sep = (ns.max() - ns.min()) / max(hi - lo, 1e-9)
    sys.stderr.write(f"  normalised stroke: median {np.median(ns):.3f}, "
                     f"IQR {hi-lo:.3f}, range/IQR {sep:.1f}\n")

    # find the line with ~56 glyphs and check its bold fraction concentrates
    cand = [l for l in lines if 48 <= len(l) <= 64]
    if cand:
        best = None
        for l in cand:
            vals = [by_key.get((round(b[0], 1), round(b[1], 1)),
                               (0, 0, 0, 0, 0, 0))[5] for b in l]
            vals = np.array(vals)
            t = np.percentile(ns, 75)
            frac = float((vals >= t).mean())
            if best is None or abs(frac - 14 / 56) < abs(best[1] - 14 / 56):
                best = (l, frac)
        sys.stderr.write(f"  {len(cand)} line(s) of 48-64 glyphs; closest bold "
                         f"fraction {best[1]:.2f} (published 14/56 = 0.25)\n")
        good = 0.10 <= best[1] <= 0.45
        ok &= good
        sys.stderr.write(f"  a line with a bold phrase shows a partial bold "
                         f"fraction, not 0 or 1: "
                         f"{'OK' if good else 'FAIL'}\n")
    else:
        sys.stderr.write("  no line of 48-64 glyphs found: FAIL\n")
        ok = False
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="75,76,77,78,79")
    ap.add_argument("--pct", type=float, default=75.0,
                    help="percentile of normalised stroke above which a glyph "
                         "counts as bold")
    ap.add_argument("--out", default="boldruns.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the weight measure cannot reproduce the published control")
    if a.selftest:
        return

    rows = []
    for p in [int(x) for x in a.pages.split(",")]:
        shape, gl = glyphs_with_weight(p)
        if shape is None:
            continue
        ns = np.array([g[5] for g in gl])
        thresh = float(np.percentile(ns, a.pct))
        lines = CR.group_lines([(g[0], g[1], g[2], g[3]) for g in gl])
        key = {(round(g[0], 1), round(g[1], 1)): g for g in gl}
        nbold = 0
        for li, l in enumerate(lines, 1):
            full = [key.get((round(b[0], 1), round(b[1], 1))) for b in l]
            full = [f for f in full if f]
            rs = runs_from(full, thresh)
            for is_b, n in rs:
                if is_b and n >= 3:
                    nbold += 1
            rows.append((p, li, len(full),
                         "".join("B" if b else "." for b, n in rs
                                 for _ in range(n))))
        sys.stderr.write(f"  p{p}: {len(gl):>5} glyphs, {len(lines):>3} lines, "
                         f"thresh {thresh:.3f}, {nbold} bold runs >=3 glyphs\n")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("page\tline\tglyphs\tbold_mask\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    sys.stderr.write(f"\n  {len(rows)} lines -> {a.out}\n")


if __name__ == "__main__":
    main()
