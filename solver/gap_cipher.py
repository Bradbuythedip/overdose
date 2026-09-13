#!/usr/bin/env python3
"""
WORD-SPACING as the hidden channel, measured on lossless 320 dpi bilevel masks.

WHY THIS, AND WHY ONLY NOW
Every typographic attack so far has gone after WEIGHT — bold as a null cipher,
bold as a Bacon cipher. Weight is the wrong signal for this artefact: the face
is a distressed typewriter, its glyphs vary in ink by design, and the measured
per-word calls never separated cleanly. Spacing is a different physical
quantity and a better one here, for a reason specific to this article: the
face is a TYPEWRITER face, so if it is monospaced every character advance is
one fixed pitch and a word gap is an integer number of pitches. One space
versus two is then a clean binary symbol — the oldest text-steganography
channel there is, and one that survives typesetting, printing and scanning.
It also matches the clue better than weight does: a key hidden IN THE TEXT,
invisible to a reader, is what double spaces are.

A FIRST VERSION OF THIS SCRIPT PRODUCED A CONFIDENT "NO CHANNEL" THAT WAS
WORTHLESS, and the reason is recorded here so it is not repeated. It sliced
lines by row-ink profile over the full page width, which merged body text with
the rotated sidebar and headline, giving 687px line-start spreads and word
"gaps" averaging 147px. Its null — the dip statistic on letter gaps — returned
exactly 1.00 on every page, because letter gaps are small integers and a
histogram of few distinct integer values always contains a perfect valley. A
saturated null cannot calibrate anything. Both faults are fixed below:
segmentation is by connected component, and the test is a BIC comparison
between one- and two-component Gaussian mixtures, calibrated against synthetic
unimodal samples matched to each page's own n, mean and sd.

  python3 gap_cipher.py --selftest
  python3 gap_cipher.py
"""
import argparse, glob, json, math, os, sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def load_mask(path):
    a = np.asarray(Image.open(path).convert("L"))
    dark = a < 128
    return dark if dark.mean() < 0.5 else ~dark


def components(ink, min_h, max_h, min_px):
    """Connected components of ink, as bounding boxes. Iterative flood fill."""
    from scipy import ndimage
    lab, n = ndimage.label(ink)
    out = []
    for sl, i in zip(ndimage.find_objects(lab), range(1, n + 1)):
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        h = y1 - y0
        if h < min_h or h > max_h:
            continue
        if int((lab[sl] == i).sum()) < min_px:
            continue
        out.append((x0, y0, x1, y1))
    return out


def group_lines(boxes, tol):
    """Group glyph boxes into text lines by vertical centre."""
    if not boxes:
        return []
    rows = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    lines, cur = [], [rows[0]]
    for b in rows[1:]:
        c = (b[1] + b[3]) / 2
        cc = np.mean([(x[1] + x[3]) / 2 for x in cur])
        if abs(c - cc) <= tol:
            cur.append(b)
        else:
            lines.append(cur)
            cur = [b]
    lines.append(cur)
    return [sorted(l, key=lambda b: b[0]) for l in lines if len(l) >= 8]


def bic_1_vs_2(v, iters=80):
    """BIC of a 1-component vs a 2-component Gaussian fit (EM).

    Returns (bic1 - bic2, mu_lo, mu_hi, weight_hi). Positive means the
    two-component model is preferred.
    """
    v = np.asarray(v, dtype=float)
    n = len(v)
    if n < 40:
        return -1e9, 0, 0, 0
    s = max(v.std(), 1e-6)
    ll1 = float(np.sum(-0.5 * ((v - v.mean()) / s) ** 2 - math.log(s * math.sqrt(2 * math.pi))))
    bic1 = 2 * math.log(n) - 2 * ll1

    lo, hi = np.percentile(v, 25), np.percentile(v, 75)
    mu = np.array([lo, hi], dtype=float)
    sd = np.array([s, s], dtype=float)
    w = np.array([0.5, 0.5])
    for _ in range(iters):
        p = np.stack([w[k] * np.exp(-0.5 * ((v - mu[k]) / sd[k]) ** 2)
                      / (sd[k] * math.sqrt(2 * math.pi)) for k in range(2)])
        tot = p.sum(axis=0) + 1e-300
        r = p / tot
        nk = r.sum(axis=1) + 1e-12
        w = nk / n
        mu = (r * v).sum(axis=1) / nk
        sd = np.sqrt((r * (v - mu[:, None]) ** 2).sum(axis=1) / nk)
        sd = np.maximum(sd, 0.35)          # sub-pixel floor: gaps are integers
    ll2 = float(np.sum(np.log(tot)))
    bic2 = 5 * math.log(n) - 2 * ll2
    o = np.argsort(mu)
    return bic1 - bic2, float(mu[o[0]]), float(mu[o[1]]), float(w[o[1]])


def null_margin(n, mean, sd, step=1.0, trials=300, seed=7):
    """Largest BIC margin a UNIMODAL sample of the same shape produces.

    This is the operation-matched null. Anything the real data scores below
    this is what the estimator does to data with no second cluster in it.

    300 trials, not a few dozen: the threshold is an upper-tail percentile, and
    estimating it from 40 draws left the realised false-positive rate at 17%
    against a nominal 5%.

    `step` must match the data's own quantization. Gaps are measured in whole
    pixels and then divided by their line's glyph width, so a normalised gap
    lands on a grid of 1/width, not on integers. Rounding the null to integers
    while the data sits on a 1/30 grid compares two different distributions and
    the margin it yields means nothing.
    """
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(trials):
        v = np.round(rng.normal(mean, sd, n) / step) * step
        out.append(bic_1_vs_2(v)[0])
    return float(np.percentile(out, 95))


def measure(path, verbose=True):
    ink = load_mask(path)
    H, W = ink.shape
    scale = H / 3456.0
    boxes = components(ink, int(14 * scale), int(90 * scale), int(30 * scale))
    lines = group_lines(boxes, tol=12 * scale)
    if not lines:
        return None
    wmed = float(np.median([b[2] - b[0] for b in boxes]))

    # Body lines only: the sidebar is rotated and the headline is display size.
    hs = np.array([np.median([b[3] - b[1] for b in l]) for l in lines])
    hmed = float(np.median(hs))
    body = [l for l, h in zip(lines, hs) if 0.7 * hmed <= h <= 1.4 * hmed]

    # Gaps are normalised by THEIR OWN LINE's glyph width before being pooled.
    # Without this the test is trivially confounded by type size: p78 sets half
    # its lines as large display bold, so pooling raw pixel gaps across sizes
    # produces two clusters that mean nothing but "two point sizes on a page".
    # A monospace double-space is 2x the pitch of its own line, so the ratio
    # the channel would produce survives normalisation while the confound does
    # not.
    gaps, letter = [], []
    for l in body:
        lw = float(np.median([b[2] - b[0] for b in l])) or wmed
        for a, b in zip(l, l[1:]):
            d = (b[0] - a[2]) / lw
            if d < 0:
                continue
            (gaps if d > 0.6 else letter).append(d)
    if verbose:
        sys.stderr.write(f"\n  {os.path.basename(path)}: {len(boxes)} glyphs, "
                         f"{len(lines)} lines ({len(body)} body), "
                         f"glyph width median {wmed:.1f}px\n")
    return np.array(gaps, dtype=float), np.array(letter, dtype=float), wmed


def selftest():
    """A page with planted double spaces must beat its own unimodal null."""
    rng = np.random.default_rng(1)
    n = 300
    # False-positive RATE, not a single draw. The threshold is the null's 95th
    # percentile, so by construction ~5% of unimodal samples exceed it; testing
    # one draw against it would fail one run in twenty for no reason. What has
    # to hold is that the rate is near its nominal 5%.
    nul = null_margin(n, 10, 1.2)
    fp = sum(1 for _ in range(60)
             if bic_1_vs_2(np.round(rng.normal(10, 1.2, n)))[0] > nul)
    sys.stderr.write(f"  unimodal false-positive rate {fp}/60 "
                     f"({fp/60*100:.0f}%) at a nominal 5% threshold "
                     f"(null 95th pct {nul:+.1f})\n")
    ok1 = fp <= 9

    mixed = np.concatenate([rng.normal(10, 1.2, 200), rng.normal(20, 1.2, 100)])
    m, lo, hi, w = bic_1_vs_2(mixed)
    nul2 = null_margin(len(mixed), mixed.mean(), mixed.std())
    sys.stderr.write(f"  planted 1:2 spacing: BIC margin {m:+.1f} vs null "
                     f"{nul2:+.1f}, means {lo:.1f}/{hi:.1f} "
                     f"(ratio {hi/max(lo,1e-9):.2f}), heavy weight {w:.2f}\n")
    ok2 = m > nul2 and 1.7 < hi / lo < 2.3
    sys.stderr.write(f"  detected planted channel: {'OK' if ok2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok1 and ok2 else "FAIL\n"))
    return ok1 and ok2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--masks", nargs="+",
                    default=sorted(glob.glob("scan400/p*_mask.png")))
    ap.add_argument("--out", default="/tmp/gap_bits.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("estimator fails its own controls; refusing to report")
    if a.selftest:
        return

    rep = {}
    for path in a.masks:
        r = measure(path)
        if r is None:
            continue
        gaps, letter, wmed = r
        if len(gaps) < 60:
            sys.stderr.write("    too few word gaps to test\n")
            continue
        # Gaps wider than three pitches are column breaks, bar edges and
        # paragraph indents, not spaces. Excluded by size, not by percentile:
        # a percentile cut would keep them on a page that has many.
        g = gaps[(gaps >= 0.6) & (gaps <= 3.0)]
        m, lo, hi, w = bic_1_vs_2(g)
        nul = null_margin(len(g), g.mean(), g.std(), step=1.0 / wmed)
        ratio = hi / max(lo, 1e-9)
        sys.stderr.write(f"    word gaps n={len(g)} of {len(gaps)}  "
                         f"mean {g.mean():.2f} pitches  sd {g.std():.2f}  "
                         f"(1 pitch ~{wmed:.0f}px)\n")
        sys.stderr.write(f"    BIC margin {m:+.1f}   unimodal null 95th pct "
                         f"{nul:+.1f}\n")
        sys.stderr.write(f"    two-component fit: {lo:.2f} / {hi:.2f} pitches  "
                         f"ratio {ratio:.2f}  heavy weight {w:.2f}\n")
        real = m > nul and 1.6 < ratio < 2.6 and 0.05 < w < 0.6
        sys.stderr.write("    " + ("CHANNEL: two gap widths in a ~1:2 ratio, "
                                   "beyond the unimodal null\n" if real else
                                   "no channel: gap widths are one population "
                                   "once the null is accounted for\n"))
        rep[os.path.basename(path)] = {
            "n": int(len(g)), "mean": float(g.mean()), "sd": float(g.std()),
            "bic_margin": m, "null95": nul, "lo": lo, "hi": hi,
            "ratio": ratio, "weight_hi": w, "channel": bool(real)}
        if real:
            cut = 0.5 * (lo + hi)
            rep[os.path.basename(path)]["bits"] = "".join(
                "1" if x > cut else "0" for x in gaps)

    json.dump(rep, open(a.out, "w"), indent=1)
    sys.stderr.write(f"\n  -> {a.out}\n")


if __name__ == "__main__":
    main()
