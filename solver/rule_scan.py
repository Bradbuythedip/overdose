#!/usr/bin/env python3
"""
Find every drawn horizontal rule on the pages: underlines, strikethroughs.

WHY
Reading the pages turned up two typographic events that are neither bold nor
highlight, and that appear once each:

  p75  "They discount stuff in advance."  is UNDERLINED
  p76  "(and 10years of watching Peter Schiff miss buying bitcoin"  is STRUCK

Both are distinct channels from the two this project has studied. And the
strikethrough stops at the LINE BREAK, not at the end of the parenthetical it
sits in -- "since I started honey-badgering him to buy some at $1 back in
2011)" continues the same clause unstruck. A designer striking a phrase strikes
the phrase. Striking exactly one printed line is a positional marker.

That is worth measuring rather than eyeballing, because a paper crease, a fold
shadow or a scanner artefact all look like a rule to the eye. This finds every
long horizontal dark run on every page and reports where it is, so the two
observed marks can be confirmed and any others found.

METHOD
Binarise, then for each pixel row count dark pixels inside a sliding horizontal
window. A text row is dark in short bursts with gaps; a drawn rule is dark
almost continuously across its extent. So the discriminator is the longest
CONTIGUOUS dark run in the row, not the row's total ink.

  python3 rule_scan.py --selftest
  python3 rule_scan.py
"""

# --- migrated to the scan: the phone photos were removed (see pages.py) ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pages as _pages
import argparse, sys

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("needs opencv")

PAGES = {73: _pages.page_path(73), 74: _pages.page_path(74), 75: _pages.page_path(75),
         76: _pages.page_path(76), 77: _pages.page_path(77), 78: _pages.page_path(78),
         79: _pages.page_path(79)}
BASE = "/home/user/overdose/public/images"


def longest_run(row):
    """Longest contiguous True run in a boolean row."""
    best = cur = 0
    for v in row:
        cur = cur + 1 if v else 0
        if cur > best:
            best = cur
    return best


def find_rules(path, min_frac=0.12, invert=False):
    """Rows whose longest contiguous dark run exceeds min_frac of page width."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, []
    th = cv2.threshold(cv2.GaussianBlur(img, (3, 3), 0), 0, 255,
                       cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if invert:
        th = cv2.bitwise_not(th)
    dark = th > 0
    h, w = dark.shape
    need = int(w * min_frac)
    hits = []
    for y in range(h):
        r = longest_run(dark[y])
        if r >= need:
            xs = np.nonzero(dark[y])[0]
            hits.append((y, r, int(xs.min()), int(xs.max())))
    # collapse adjacent rows into bands
    bands, cur = [], None
    for y, r, x0, x1 in hits:
        if cur and y - cur[1] <= 3:
            cur = (cur[0], y, max(cur[2], r), min(cur[3], x0), max(cur[4], x1))
        else:
            if cur:
                bands.append(cur)
            cur = (y, y, r, x0, x1)
    if cur:
        bands.append(cur)
    return (h, w), bands


def selftest():
    ok = True
    # a PLANTED rule must be found, and body text must NOT be reported
    page = np.full((400, 1000), 255, np.uint8)
    for i in range(20):                       # fake text: short dark bursts
        for x in range(60, 940, 28):
            cv2.rectangle(page, (x, 40 + i * 16), (x + 14, 52 + i * 16), 0, -1)
    cv2.imwrite("/tmp/_rule_text.png", page)
    _s, bands = find_rules("/tmp/_rule_text.png")
    ok &= len(bands) == 0
    sys.stderr.write(f"  text alone reports {len(bands)} rules (want 0): "
                     f"{'OK' if not bands else 'FAIL - fires on text'}\n")

    cv2.line(page, (120, 200), (880, 200), 0, 2)
    cv2.imwrite("/tmp/_rule_line.png", page)
    _s, bands2 = find_rules("/tmp/_rule_line.png")
    good = len(bands2) >= 1 and any(abs(b[0] - 200) <= 3 for b in bands2)
    ok &= good
    sys.stderr.write(f"  a planted 760px rule at y=200 is found: "
                     f"{[b[0] for b in bands2]} "
                     f"{'OK' if good else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-frac", type=float, default=0.12)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the rule detector fires on text or misses a planted rule")
    if a.selftest:
        return

    sys.stderr.write(f"\n  horizontal rules >= {a.min_frac:.0%} of page width\n\n")
    for p, fn in sorted(PAGES.items()):
        shape, bands = find_rules(f"{BASE}/{fn}", a.min_frac, invert=(p == 77))
        if shape is None:
            sys.stderr.write(f"  p{p}: unreadable\n")
            continue
        h, w = shape
        sys.stderr.write(f"  p{p}  {w}x{h}  {len(bands)} rule band(s)\n")
        for y0, y1, run, x0, x1 in bands:
            sys.stderr.write(f"       y {y0:>5}-{y1:<5} x {x0:>5}-{x1:<5} "
                             f"run {run:>5}px ({run/w:.0%} of width)  "
                             f"y/h {y0/h:.3f}\n")


if __name__ == "__main__":
    main()
