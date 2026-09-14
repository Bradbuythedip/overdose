#!/usr/bin/env python3
"""
Find every strikethrough rule in the column, on the 400 dpi ink separation.

WHY THIS IS REOPENED
An earlier session concluded no strikethroughs or underlines exist, from
3x-LANCZOS-upscaled crops -- and LANCZOS manufactures continuous edges, so that
method could neither confirm nor refute them. Measured instead on the scanner's
own lossless CCITT G4 ink separation at 400 dpi, page 76 carries an obvious
one: a continuous 1,132 px (2.83 in) rule through "(and 10years of watching
Peter Schiff miss buying bitcoin". The earlier negative was an artifact of the
method, not a property of the page.

A strikethrough is an editorial mark an author makes deliberately, so its
distribution over the column is a channel worth measuring.

WHAT COUNTS AS A RULE, AND WHAT IS EXCLUDED
The knocked-out highlight bars are also solid ink and also produce long runs.
They are separated geometrically: a rule is WIDE and THIN, a bar is WIDE and
TALL. Components are kept only when

    width >= 200 px (0.5 in)   and   height <= 14 px (0.035 in)
    (a rule crosses glyphs, so it is found as a cluster of long row-runs,
    not as a connected component)

Pages 74 and 77 have no black separation (74 is the full-bleed photograph, 77
is printed white on dark brown), so 77 is measured from the colour render by
thresholding its knocked-out white text instead.

  python3 wf/strikethrough.py --selftest
  python3 wf/strikethrough.py
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pages

MIN_W, MAX_H, MIN_FILL = 200, 14, 0.85


def row_runs(row, minw):
    """Maximal contiguous True runs of at least minw, as (x0, x1)."""
    idx = np.flatnonzero(np.diff(np.concatenate(([0], row.view(np.int8), [0]))))
    out = []
    for a, b in zip(idx[0::2], idx[1::2]):
        if b - a >= minw:
            out.append((int(a), int(b)))
    return out


def components(ink):
    """Find RULES as clusters of long horizontal runs across adjacent rows.

    A strikethrough is connected to every glyph it crosses, so connected-
    component bounding boxes are tall and sparse and cannot be used. What
    separates a rule from a knocked-out highlight bar is vertical extent:
    a rule persists for a few rows, a bar for tens of them.
    """
    H, W = ink.shape
    per_row = {}
    for y in range(H):
        r = row_runs(ink[y], MIN_W)
        if r:
            per_row[y] = r
    out, used = [], set()
    for y in sorted(per_row):
        for i, (x0, x1) in enumerate(per_row[y]):
            if (y, i) in used:
                continue
            ys, cx0, cx1 = [y], x0, x1
            yy = y + 1
            while yy in per_row:
                nxt = None
                for j, (a, b) in enumerate(per_row[yy]):
                    if (yy, j) in used:
                        continue
                    if min(cx1, b) - max(cx0, a) > 0.5 * (cx1 - cx0):
                        nxt = (j, a, b); break
                if nxt is None:
                    break
                j, a, b = nxt
                used.add((yy, j)); ys.append(yy)
                cx0, cx1 = min(cx0, a), max(cx1, b)
                yy += 1
            h = len(ys)
            if h <= MAX_H:
                w = cx1 - cx0
                fill = ink[ys[0]:ys[-1] + 1, cx0:cx1].mean()
                out.append((cx0, ys[0], w, h, float(fill)))
    return out


def page_ink(pr):
    """Boolean ink array for a printed page, plus a label for the source."""
    from PIL import Image
    m = pages.mask_path(pr)
    if m is not None:
        a = np.asarray(Image.open(m).convert("L"))
        return (a > 127), "400dpi ink separation"
    # no separation: threshold the colour render (page 77 is white-on-dark)
    a = np.asarray(Image.open(pages.page_path(pr, dpi=400)).convert("L"))
    if a.mean() < 128:                       # dark ground -> ink is the light text
        return (a > 160), "400dpi render (dark ground)"
    return (a < 100), "400dpi render"


def scan():
    found = {}
    for pr in sorted(pages.PRINTED):
        if pr < 73:                          # page 72 is NUMBERS, not the column
            continue
        ink, src = page_ink(pr)
        comps = components(ink)
        comps.sort(key=lambda c: (c[1], c[0]))
        found[pr] = comps
        print(f"page {pr} [{src}] {ink.shape}: {len(comps)} rule(s)")
        for x, y, w, h, f in comps:
            print(f"    x={x:5d} y={y:5d}  {w:5d}x{h:<3d} px "
                  f"({w/400:.2f} in)  fill {f:.2f}")
    return found


def selftest():
    ok = True
    try:
        from scipy import ndimage           # noqa: F401
        print("  scipy available: OK")
    except ImportError:
        print("  scipy available: FAIL")
        return False
    # positive control: a synthetic rule must be detected
    ink = np.zeros((200, 800), bool)
    ink[100:103, 50:600] = True
    c = components(ink)
    good = len(c) == 1 and c[0][2] == 550 and c[0][3] == 3
    print(f"  detects a planted 550px rule: {'OK' if good else 'FAIL'} ({c})")
    ok &= good
    # negative control: a tall solid bar (a highlight) must be REJECTED
    ink = np.zeros((200, 800), bool)
    ink[60:120, 50:600] = True
    c = components(ink)
    good = len(c) == 0
    print(f"  rejects a 60px-tall highlight bar: {'OK' if good else 'FAIL'}")
    ok &= good
    # the known page-76 rule must be recovered
    ink, _ = page_ink(76)
    c = components(ink)
    good = any(w > 900 for _, _, w, _, _ in c)
    print(f"  recovers the page-76 rule: {'OK' if good else 'FAIL'} "
          f"({len(c)} comps, widest "
          f"{max([w for _,_,w,_,_ in c], default=0)} px)")
    ok &= good
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed")
    print()
    scan()
