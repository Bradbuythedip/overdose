#!/usr/bin/env python3
"""
Count the PHYSICAL highlight bars, which is not the same as the 38 spans.

WHY
highlights_ordered.tsv is a SEMANTIC catalogue: it was made by reading the
pages, so one row is one phrase. A phrase that wraps across a line break is
printed as TWO bars, and two phrases on one line can share one bar. The
workflow critic flagged this and it matters, because wf/highlight_bits.py
tested the sequence as 38 ordered binary symbols. If the true mark count is
not 38, that bitstream was built on the wrong alphabet length and its negative
result does not describe the real channel.

So: measure the bars instead of counting the rows.

A bar is a contiguous horizontal run of highlight ink on ONE text line. Three
classes are segmented separately rather than collapsed:

    orange      spot-ink bar, dark type on orange            (light pages)
    black       solid black bar, type knocked out white      (light pages)
    white       light bar on the dark brown ground (p77)     -- the OPPOSITE
                object to a black knockout: positive type restored, not
                reverse type. The critic is right that collapsing these two
                into one "knocked-out" class throws a symbol away.

  python3 wf/bar_census.py --selftest
  python3 wf/bar_census.py
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pages

SOLVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINW, MINH = 60, 18          # at 400 dpi: 0.15 in wide, 0.045 in tall


def masks(pr, dpi=400):
    from PIL import Image
    im = Image.open(pages.page_path(pr, dpi=dpi)).convert("RGB")
    a = np.asarray(im).astype(int)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    g = a.mean(axis=2)
    orange = (R > 190) & (G > 90) & (G < 190) & (B < 130)
    dark_page = g.mean() < 128
    if dark_page:
        # p77: light bars on a dark brown ground
        white = (g > 150) & ~orange
        return {"orange": orange, "white": white}
    black = (g < 95) & ~orange
    return {"orange": orange, "black": black}


def bars(mask):
    """A bar is a SOLID region, which is what separates it from body text.

    Two earlier attempts failed and are worth recording. Eroding the raw mask
    fragments each bar, because the type sitting on it punches holes (knocked-
    out white text in a black bar, dark type on an orange bar): black counted 1
    against a catalogued 10. Closing the holes first then over-counts wildly --
    284 -- because the "dark pixels" mask also contains all the body text, and
    horizontal closing welds each text line into a bar-shaped blob.

    What actually distinguishes a bar is LOCAL FILL: a solid bar is 70-100%
    covered over its whole box, while a line of type is 10-25% covered. So
    threshold the local density, not the pixels.

    Returns (x0, x1, y0, y1) boxes.
    """
    from scipy import ndimage
    dens = ndimage.uniform_filter(mask.astype(np.float32), size=(15, 45))
    solid = dens > 0.62
    solid = ndimage.binary_erosion(solid, structure=np.ones((5, 1)))
    lab, n = ndimage.label(solid)
    out = []
    for sl in ndimage.find_objects(lab):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if w >= MINW and h >= MINH:
            out.append((sl[1].start, sl[1].stop, sl[0].start, sl[0].stop))
    out.sort(key=lambda b: (b[2], b[0]))
    return out


def census():
    total = {}
    seq = []
    for pr in (75, 76, 77, 78, 79):
        m = masks(pr)
        line = []
        for cls, mk in m.items():
            bs = bars(mk)
            total[cls] = total.get(cls, 0) + len(bs)
            for b in bs:
                seq.append((pr, cls, b))
            line.append(f"{cls}={len(bs)}")
        print(f"  p{pr}: " + "  ".join(line))
    seq.sort(key=lambda t: (t[0], t[2][2], t[2][0]))
    print(f"\nphysical bars by class: {total}")
    print(f"TOTAL physical bars: {sum(total.values())}")
    return seq, total


def selftest():
    ok = True
    try:
        from scipy import ndimage          # noqa: F401
        print("  scipy: OK")
    except ImportError:
        print("  scipy: FAIL"); return False
    # planted controls: one bar detected, a thin rule rejected
    m = np.zeros((300, 800), bool); m[100:140, 100:500] = True
    good = len(bars(m)) == 1
    print(f"  detects a planted bar: {'OK' if good else 'FAIL'}")
    ok &= good
    m2 = np.zeros((300, 800), bool); m2[100:103, 100:500] = True
    good = len(bars(m2)) == 0
    print(f"  rejects a 3px rule: {'OK' if good else 'FAIL'}")
    ok &= good
    # NEGATIVE control that matters: a line of type (sparse stipple) is not a bar
    m4 = np.zeros((300, 800), bool)
    for x in range(100, 500, 9):
        m4[100:130, x:x + 3] = True          # ~33% fill, like body text
    good = len(bars(m4)) == 0
    print(f"  rejects a line of type: {'OK' if good else 'FAIL'} ({len(bars(m4))})")
    ok &= good
    # two stacked bars must not merge into one
    m3 = np.zeros((300, 800), bool)
    m3[100:140, 100:500] = True; m3[150:190, 100:500] = True
    good = len(bars(m3)) == 2
    print(f"  keeps stacked bars separate: {'OK' if good else 'FAIL'} "
          f"({len(bars(m3))})")
    ok &= good
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed")
    print()
    seq, total = census()
    cat = {"orange": 22, "black": 10, "white": 6}
    print(f"\nhighlights_ordered.tsv SPAN counts: {cat} (total {sum(cat.values())})")
    print("A span is a phrase; a bar is a physical mark. They differ wherever a")
    print("phrase wraps a line break or two phrases share one bar.")
