#!/usr/bin/env python3
"""
The highlight bars as SPATIAL data -- position and size, not colour or text.

THE LEAD
`SOLVE_PROMPT.md` names this: "The orange and black bars are positioned
deliberately. Their coordinates, lengths, or per-line counts are a numeric
sequence nobody has treated as data."

Still true. `parse_typography.py` parses bars out of MARKED-UP TEXT -- it reads
`[O:...]` and `[B:...]` annotations a human typed -- so it has the bars' word
content, never their pixels. `highlight_sequence.py` uses the text;
`highlight_color.py` uses the colour. Nobody has measured where the bars ARE.

WHY IT SURVIVES THE CAPACITY BOUND
`channel_capacity.md` showed every discrete editorial channel combined carries
124 bits, four short of a 12-word mnemonic. Bar colour is 38 bits and is dead.
But bar GEOMETRY is 38 bars x (x0, x1, y, width, height) -- 190 numbers at ~10
bits each. It is one of the few channels with room for a key, and the only one
of those that has never been measured.

THE CONFOUND, WHICH IS THE WHOLE PROBLEM
A bar's width is mostly determined by the words inside it: a highlight is drawn
around text, so longer text means a wider bar. Any "signal" in the width
sequence is therefore mostly a restatement of the text lengths already swept.
So this reports the correlation between bar width and the character count of
its text, and treats the RESIDUAL -- the part of the width the text does not
explain -- as the candidate channel.

  python3 bar_geometry.py --selftest
  python3 bar_geometry.py --out bars.tsv
"""
import argparse, sys

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("needs opencv")
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

PAGES = (75, 76, 77, 78, 79)


def masks(page, base="hires"):
    a = np.asarray(Image.open(f"{base}/p{page}_400dpi.png").convert("RGB")
                   ).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    orange = (R > 185) & (G > 85) & (G < 195) & (B < 120)
    if page == 77:
        # page 77 is white-on-dark-brown: the knockout bar is the WHITE one
        knock = (R > 200) & (G > 195) & (B > 185)
    else:
        knock = (R < 95) & (G < 95) & (B < 95)
    return a.shape, orange, knock


def bars_from(mask, min_w=120, min_h=28, max_h=200):
    """Bars are wide, short, SOLID rectangles.

    OPENING, not closing. On page 77 the body text is white on dark brown and
    the highlight bars are also white, so colour cannot separate them. A
    morphological CLOSE merges adjacent white text into phantom bars -- the
    first version of this file reported 39 bars on p77 against a catalogue of
    8, and the bad count silently corrupted the confound check downstream.

    An OPEN erodes thin strokes away first: text disappears, a solid bar
    survives. Solidity is then checked on the ORIGINAL mask, not the opened
    one, so a bar that is genuinely solid passes and a lucky blob of text does
    not.
    """
    m = (mask * 255).astype(np.uint8)
    er = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, er)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, _lab, stats, _c = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, _a = stats[i]
        if w < min_w or not (min_h <= h <= max_h):
            continue
        if w < 1.8 * h:
            continue
        if mask[y:y + h, x:x + w].mean() < 0.62:
            continue
        out.append((int(x), int(y), int(w), int(h)))
    return sorted(out, key=lambda b: (b[1], b[0]))


def collect(base="hires", orange_only=True):
    """ORANGE ONLY, and that is a measured limitation rather than a choice.

    Orange appears nowhere else on these pages, so an orange region IS a
    highlight bar and detection is unambiguous. The knocked-out bars are not
    separable by colour: on a white page black ink is also body text, display
    type and the ink-scribble graphics, and measuring window density shows the
    densest dark regions on p75 and p78 are the BITCOIN IS TOXIC AF headline
    (0.57) and the X FUCK ALL X scribble (0.25) -- not bars. On p77 the body
    text is white on dark brown, the same value as the white bars.

    Separating those needs OCR-level segmentation, not thresholding. So this
    measures the 22 orange bars, which the catalogue independently counts as 22
    orange runs, and says so rather than reporting a number it cannot support.
    """
    rows = []
    for p in PAGES:
        shape, orange, knock = masks(p, base)
        pairs = [("orange", orange)] if orange_only else \
                [("orange", orange), ("knock", knock)]
        for col, m in pairs:
            for x, y, w, h in bars_from(m):
                rows.append({"page": p, "colour": col, "x0": x, "y": y,
                             "w": w, "h": h, "x1": x + w})
    rows.sort(key=lambda r: (r["page"], r["y"], r["x0"]))
    return rows


def hl_text():
    """The catalogued highlight text, for the confound check."""
    out = []
    try:
        for line in open("highlights_ordered.tsv", encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                out.append((p[0], p[1], p[2]))
    except OSError:
        pass
    return out


def selftest():
    ok = True
    # a PLANTED bar must be found, and text must not be mistaken for one
    img = np.zeros((600, 1400), bool)
    for i in range(14):                      # fake text: short blobs
        img[100 + i * 30:118 + i * 30, 80:110] = True
    found = bars_from(img)
    ok &= len(found) == 0
    sys.stderr.write(f"  text blobs alone yield {len(found)} bars (want 0): "
                     f"{'OK' if not found else 'FAIL'}\n")
    img[300:346, 200:900] = True             # a 700x46 bar
    f2 = bars_from(img)
    good = any(abs(b[2] - 700) < 90 and abs(b[3] - 46) < 30 for b in f2)
    ok &= good
    sys.stderr.write(f"  a planted 700x46 bar is found as {f2[:1]}: "
                     f"{'OK' if good else 'FAIL'}\n")
    # REGRESSION: a ROW of white text on a dark page must not close into a
    # bar. This is what produced 39 phantom bars on p77.
    line = np.zeros((600, 1400), bool)
    for x in range(120, 1200, 34):
        line[280:316, x:x + 20] = True      # 32 glyph-ish blobs on one line
    f3 = bars_from(line)
    ok &= len(f3) == 0
    sys.stderr.write(f"  a row of 32 text blobs does not close into a bar "
                     f"({len(f3)} found): {'OK' if not f3 else 'FAIL'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bars.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the bar detector fires on text or misses a planted bar")
    if a.selftest:
        return

    rows = collect()
    sys.stderr.write(f"\n  {len(rows)} bars detected at 400 dpi "
                     f"(catalogue lists 38 highlight runs)\n\n")
    from collections import Counter
    c = Counter((r["page"], r["colour"]) for r in rows)
    for p in PAGES:
        sys.stderr.write(f"    p{p}: orange {c[(p,'orange')]:>3}   "
                         f"knock {c[(p,'knock')]:>3}\n")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("page\tcolour\tx0\tx1\ty\tw\th\n")
        for r in rows:
            fh.write(f"{r['page']}\t{r['colour']}\t{r['x0']}\t{r['x1']}\t"
                     f"{r['y']}\t{r['w']}\t{r['h']}\n")
    sys.stderr.write(f"\n  -> {a.out}\n")

    # THE CONFOUND: how much of bar width is just the text inside it?
    txt = [t for t in hl_text() if t[1] == "orange"]
    # PER-PAGE gate. Global totals matching is not alignment: p76 and p78
    # over-detect by one each and p79 under-detects by two, netting to zero,
    # because the catalogue splits a multi-line highlight per LINE while the
    # detector sees one connected orange region. Checking only the total
    # reported a 22 = 22 match and a correlation that was pairing noise.
    from collections import Counter
    cd = Counter(r["page"] for r in rows)
    ct = Counter(int(t[0]) for t in txt)
    mismatch = {p: (cd[p], ct[p]) for p in set(cd) | set(ct) if cd[p] != ct[p]}
    if mismatch:
        sys.stderr.write(
            f"\n  CONFOUND CHECK SKIPPED. Per-page counts disagree "
            f"(detected, catalogued): {mismatch}\n"
            f"  A multi-line highlight is one orange region but several "
            f"catalogue rows, so\n  bar i is not text i. Global totals "
            f"matching is not alignment.\n")
    elif txt and abs(len(rows) - len(txt)) > 4:
        sys.stderr.write(
            f"\n  CONFOUND CHECK SKIPPED. {len(rows)} bars detected against "
            f"{len(txt)} catalogued\n  runs, so bar i is not text i and any "
            f"correlation between them would be\n  pairing noise. Fix the "
            f"detector before trusting the number.\n")
    elif txt and len(rows) >= 10:
        n = min(len(rows), len(txt))
        w = np.array([r["w"] for r in rows[:n]], float)
        L = np.array([len(t[2]) for t in txt[:n]], float)
        if w.std() > 0 and L.std() > 0:
            r = float(np.corrcoef(w, L)[0, 1])
            sys.stderr.write(
                f"\n  CONFOUND CHECK, {n} paired bars\n"
                f"    corr(bar width, characters of its text) = {r:+.3f}\n")
            if abs(r) > 0.6:
                sys.stderr.write(
                    "    Bar width is largely the text length, which the "
                    "corpus already\n    sweeps. Only the RESIDUAL is a new "
                    "channel.\n")
            else:
                sys.stderr.write(
                    "    Width is NOT explained by text length -- unusual for "
                    "a highlight\n    drawn around words, and worth a closer "
                    "look.\n")


if __name__ == "__main__":
    main()
