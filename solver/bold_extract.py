#!/usr/bin/env python3
"""
Quantitative per-character bold detection on the Overdose pages.

WHY THIS IS DIFFERENT FROM WHAT WAS TRIED BEFORE
------------------------------------------------
Earlier passes at the bold null-cipher were vision-agent eyeballing, and the
per-character finding was recorded as "held unconfirmed" on the theory that
the phone-scan JPEGs were too coarse. Zooming a line at 2x shows that is too
pessimistic -- "but George Clinton and James Brown clones" plainly shows bold
running at CHARACTER level and crossing word boundaries ("Cl" bold, "inton"
not). So the signal is there; what was missing was a measurement.

THE MEASUREMENT
---------------
The body font is a monospace typewriter face, and bold differs from regular by
STROKE THICKNESS. Thickness can be measured glyph-independently with a distance
transform: for a character's ink mask, the mean of the Euclidean distance
transform over the ink is half the mean stroke width. A bold 'e' and a bold 'M'
are both thicker than their regular twins, so -- unlike raw ink density, which
confounds glyph shape with weight ('M' inks more than 'i' at any weight) --
this needs no per-letter normalization and no OCR to be correct.

Highlighted runs (orange and black bars) are handled separately: inside a black
bar the text is knocked out white-on-black, so the ink polarity is inverted
there. Those regions are detected and inverted rather than silently producing
garbage components.

Output per page:
  - stroke-width histogram (to show whether the distribution is actually
    bimodal, i.e. whether "bold" is a real class or an artifact of thresholding)
  - an annotated page with bold components boxed
  - a reading-order strip image of just the bold characters, so the payload can
    be read off directly without trusting OCR

  python3 bold_extract.py --page ../IMG_6247.jpeg --out /tmp/ocr/p76
"""
import argparse, os, sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def load_gray(path, scale=2):
    im = Image.open(path).convert("L")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    return im, np.asarray(im, dtype=np.uint8)


def ink_mask(g):
    """Binarize to ink=True, handling knocked-out text inside dark bars.

    A global Otsu split separates paper from ink over most of the page, but
    inside a solid highlight bar the polarity flips. Bars are found as large
    dark blobs; within them the local polarity is inverted so knocked-out
    characters register as ink too.
    """
    hist = np.bincount(g.ravel(), minlength=256).astype(float)
    tot = hist.sum()
    w = np.cumsum(hist)
    m = np.cumsum(hist * np.arange(256))
    mt = m[-1]
    denom = w * (tot - w)
    # Degenerate splits (all pixels on one side) must be EXCLUDED, not merely
    # guarded against division by zero: with denom forced to 1 the t=255 bin
    # scores (mt*tot - mt)^2 and always wins, which silently binarizes the whole
    # page to "ink" and yields ~200 components instead of thousands.
    valid = denom > 0
    # sigma_B^2 = (m*tot - w*mt)^2 / (tot^2 * w * (tot-w)). The tot factor on m
    # is not optional: dropping it makes the score climb monotonically with the
    # threshold and Otsu returns ~254 on any page.
    num = (m * tot - w * mt) ** 2
    var = np.where(valid, num / np.where(valid, denom, 1), -1.0)
    thr = int(np.argmax(var))

    dark = g < thr
    # Solid highlight bars: dark regions that survive heavy erosion.
    bars = ndimage.binary_erosion(dark, np.ones((9, 9)), iterations=2)
    bars = ndimage.binary_dilation(bars, np.ones((9, 9)), iterations=3)

    ink = dark & ~bars
    if bars.any():
        # inside bars, ink is the light (knocked-out) pixels
        ink |= bars & (g > thr)
    return ink, thr, bars


def components(ink, min_h, max_h, min_px):
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(lab)
    out = []
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        if not (min_h <= h <= max_h) or w < 2 or w > max_h * 2:
            continue
        sub = lab[sl] == i
        if sub.sum() < min_px:
            continue
        out.append({"bbox": (xs.start, ys.start, xs.stop, ys.stop),
                    "mask": sub, "label": i, "npx": int(sub.sum())})
    return out


def stroke_width(mask):
    """Mean stroke width = 2 * mean(EDT over ink), padded so the border of the
    crop is not treated as background-adjacent incorrectly."""
    p = np.pad(mask, 1)
    d = ndimage.distance_transform_edt(p)
    v = d[p]
    if v.size == 0:
        return 0.0
    return float(2.0 * v.mean())


def group_lines(comps, tol):
    """Group components into text lines by vertical overlap, then sort each
    line left-to-right and the lines top-to-bottom."""
    cs = sorted(comps, key=lambda c: (c["bbox"][1] + c["bbox"][3]) / 2)
    lines, cur, cy = [], [], None
    for c in cs:
        y = (c["bbox"][1] + c["bbox"][3]) / 2
        if cy is None or abs(y - cy) <= tol:
            cur.append(c)
            cy = y if cy is None else (cy * (len(cur) - 1) + y) / len(cur)
        else:
            lines.append(sorted(cur, key=lambda k: k["bbox"][0]))
            cur, cy = [c], y
    if cur:
        lines.append(sorted(cur, key=lambda k: k["bbox"][0]))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--min-h", type=int, default=14)
    ap.add_argument("--max-h", type=int, default=90)
    ap.add_argument("--min-px", type=int, default=40)
    ap.add_argument("--z", type=float, default=2.0,
                    help="stroke-width z-score above the line median to call bold")
    a = ap.parse_args()

    im, g = load_gray(a.page, a.scale)
    ink, thr, bars = ink_mask(g)
    sys.stderr.write(f"{os.path.basename(a.page)}  {im.size}  otsu={thr}  "
                     f"ink={ink.mean()*100:.1f}%  bars={bars.mean()*100:.1f}%\n")

    comps = components(ink, a.min_h * a.scale // 2, a.max_h * a.scale // 2,
                       a.min_px)
    sys.stderr.write(f"  {len(comps)} character-like components\n")
    if not comps:
        sys.exit("no components -- check thresholds")

    for c in comps:
        c["sw"] = stroke_width(c["mask"])

    sw = np.array([c["sw"] for c in comps])
    qs = np.percentile(sw, [5, 25, 50, 75, 95])
    sys.stderr.write("  stroke width percentiles (5/25/50/75/95): "
                     + " ".join(f"{q:.2f}" for q in qs) + "\n")

    # Histogram, printed so bimodality can be judged rather than assumed.
    h, edges = np.histogram(sw, bins=28)
    sys.stderr.write("  stroke-width histogram:\n")
    for k in range(len(h)):
        sys.stderr.write(f"    {edges[k]:5.2f}-{edges[k+1]:5.2f} "
                         f"{'#' * int(60 * h[k] / max(h.max(), 1))} {h[k]}\n")

    # Bold is judged WITHIN a line: font size and exposure vary down the page,
    # so a global cutoff would just re-detect the largest type.
    lines = group_lines(comps, tol=12 * a.scale)
    bold = []
    for ln in lines:
        if len(ln) < 4:
            continue
        v = np.array([c["sw"] for c in ln])
        med, mad = np.median(v), np.median(np.abs(v - np.median(v)))
        if mad <= 0:
            continue
        for c in ln:
            if (c["sw"] - med) / (1.4826 * mad) >= a.z:
                bold.append(c)
    sys.stderr.write(f"  {len(lines)} text lines, {len(bold)} bold components "
                     f"({len(bold)/len(comps)*100:.1f}% of glyphs)\n")

    # ---- the decisive test: is bolding word-level or character-level? ----
    # Prior passes tried whole-word bold (0 hits) and left per-character bold
    # "unconfirmed". Those two hypotheses make opposite predictions about the
    # distribution of per-word bold fraction:
    #   word-level bolding  -> fractions pile up at exactly 0.0 and 1.0
    #   character cipher    -> a real population of intermediate fractions
    # Punctuation is excluded first: a period is a compact blob, so its mean
    # EDT (and hence apparent stroke width) is inflated relative to a letter.
    boldset = {id(c) for c in bold}
    fracs, mixed = [], []
    for ln in lines:
        if len(ln) < 4:
            continue
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        glyphs = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.5 * hmed]
        if len(glyphs) < 4:
            continue
        widths = np.array([c["bbox"][2] - c["bbox"][0] for c in glyphs])
        wmed = max(np.median(widths), 1)
        words, cur = [], [glyphs[0]]
        for prev, c in zip(glyphs, glyphs[1:]):
            if c["bbox"][0] - prev["bbox"][2] > 0.6 * wmed:
                words.append(cur)
                cur = [c]
            else:
                cur.append(c)
        words.append(cur)
        for wd in words:
            if len(wd) < 3:
                continue
            f = sum(1 for c in wd if id(c) in boldset) / len(wd)
            fracs.append(f)
            if 0.0 < f < 1.0:
                mixed.append((f, wd))

    if fracs:
        fr = np.array(fracs)
        sys.stderr.write(f"\n  per-word bold fraction over {len(fr)} words "
                         f"(>=3 letters, punctuation excluded):\n")
        for lo, hi, lab in [(-.01, .001, "0.0  (no bold)"),
                            (.001, .34, "0-1/3"), (.34, .67, "1/3-2/3"),
                            (.67, .999, "2/3-1"), (.999, 1.01, "1.0  (all bold)")]:
            n = int(((fr > lo) & (fr <= hi)).sum())
            sys.stderr.write(f"    {lab:16} {'#'*int(50*n/max(len(fr),1))} {n}\n")
        sys.stderr.write(f"  -> {len(mixed)} partially-bold words "
                         f"({len(mixed)/len(fr)*100:.1f}%)\n")

    # annotated page
    ann = im.convert("RGB")
    d = ImageDraw.Draw(ann)
    for c in bold:
        x0, y0, x1, y1 = c["bbox"]
        d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=(255, 0, 0), width=3)
    ann.save(a.out + "_annotated.png")

    # reading-order strip of just the bold glyphs -- read the payload visually,
    # with no dependence on OCR being right
    if bold:
        order = []
        for ln in lines:
            row = [c for c in ln if c in bold]
            if row:
                order.append(row)
        pad = 6
        cw = max(c["bbox"][2] - c["bbox"][0] for c in bold) + pad
        ch = max(c["bbox"][3] - c["bbox"][1] for c in bold) + pad
        ncol = max(len(r) for r in order)
        strip = Image.new("L", (ncol * cw, len(order) * ch), 255)
        for r, row in enumerate(order):
            for k, c in enumerate(row):
                x0, y0, x1, y1 = c["bbox"]
                strip.paste(im.crop((x0, y0, x1, y1)), (k * cw + pad // 2,
                                                        r * ch + pad // 2))
        strip.save(a.out + "_boldstrip.png")
        sys.stderr.write(f"  wrote {a.out}_boldstrip.png "
                         f"({len(order)} rows)\n")

    with open(a.out + "_bold.tsv", "w") as f:
        f.write("x0\ty0\tx1\ty1\tstroke_width\tnpx\n")
        for c in sorted(bold, key=lambda c: (c["bbox"][1], c["bbox"][0])):
            x0, y0, x1, y1 = c["bbox"]
            f.write(f"{x0}\t{y0}\t{x1}\t{y1}\t{c['sw']:.3f}\t{c['npx']}\n")
    sys.stderr.write(f"  wrote {a.out}_annotated.png, {a.out}_bold.tsv\n")


if __name__ == "__main__":
    main()
