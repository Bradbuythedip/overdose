#!/usr/bin/env python3
"""
Per-character weight AFTER removing glyph identity — the honest final test.

THE QUESTION THIS SETTLES
At 600 dpi page 77 plainly shows what looks like sub-word bold: "star(ve) to
(death) as (the) resu(l)t". Measured on a verified monospace grid, two weight
populations really are present (BIC +201 against a unimodal null of -9). But
the heavy calls are wildly uneven across letter identities — l 50%, e 28%,
i 26% against a 0%, o 0%, r 0%, s 5%, t 6%. That is the signature of a
DISTRESSED FACE in which each glyph is drawn with its own ink weight, not of a
cipher.

Identity and weight are therefore confounded, and neither the pooled test nor
the per-letter table can separate them. This does:

    residual = stroke width / (mean stroke width for THAT letter identity)

Dividing out each letter's own mean removes the face's built-in per-glyph
weight entirely. What is left is how heavy this particular instance is
compared with other instances of the same letter — which is exactly, and only,
what a cipher would modulate. If a bold/regular channel exists, the residuals
are bimodal. If the article merely uses a distressed face, they are not.

This is the per-character analogue of word_bold.py's least-squares ink
coefficients, which established the same confound at the word level.

  python3 char_cipher.py --selftest
  python3 char_cipher.py --img <png> --pageno 77
"""
import argparse, json, os, sys
from collections import defaultdict

import numpy as np

from glyph_grid import fit_grid, space_null
from p77_weight import ink_of, glyphs, lines_of, transcript
from gap_cipher import bic_1_vs_2, null_margin

from scipy import ndimage


def automap(img, pageno, verbose=True):
    """Map detected lines to transcript lines by best verified grid fit.

    Hand-supplied index ranges are guesswork and were wrong twice; every
    detected line is instead scored against every transcript line and keeps the
    best match, provided that match also beats the line's own
    space-permutation null.
    """
    ink, thr = ink_of(img)
    H, W = ink.shape
    s = H / 6600.0
    gl = glyphs(ink, int(20 * s), int(150 * s), int(60 * s))
    lines = [l for l in lines_of(gl, tol=22 * s) if len(l) >= 6]
    tl = transcript(pageno)
    if verbose:
        sys.stderr.write(f"  {os.path.basename(img)} {W}x{H}: {len(lines)} "
                         f"detected lines, {len(tl)} transcript lines\n")

    # Score every (detected line, transcript line) pair, then choose the best
    # MONOTONIC assignment. Greedy first-come matching is not good enough: it
    # sent a line below the headline back up to a headline line, because a
    # display line of similar length fits many space patterns. Print order is a
    # hard constraint, so impose it.
    geom, cand = [], {}
    for di, line in enumerate(lines):
        y0 = min(c["bbox"][1] for c in line)
        y1 = max(c["bbox"][3] for c in line)
        x0 = min(c["bbox"][0] for c in line)
        x1 = max(c["bbox"][2] for c in line)
        colink = ink[y0:y1, :].sum(axis=0).astype(float)
        geom.append((y0, y1, x0, x1, colink))
        for ti, text in enumerate(tl):
            if " " not in text.strip() or len(text) < 8:
                continue
            f = fit_grid(colink, text, x0, x1)
            if f is not None:
                cand[(di, ti)] = f

    nd, nt = len(lines), len(tl)
    NEG = -1e9
    dp = np.full((nd + 1, nt + 1), 0.0)
    bk = np.zeros((nd + 1, nt + 1), dtype=np.int8)
    for i in range(1, nd + 1):
        for j in range(1, nt + 1):
            opts = [(dp[i - 1, j], 1), (dp[i, j - 1], 2)]
            f = cand.get((i - 1, j - 1))
            if f is not None:
                opts.append((dp[i - 1, j - 1] + f[2], 3))
            v, b = max(opts)
            dp[i, j], bk[i, j] = v, b
    pairs, i, j = [], nd, nt
    while i > 0 and j > 0:
        b = bk[i, j]
        if b == 3:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif b == 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()

    out = []
    for di, ti in pairs:
        f = cand[(di, ti)]
        text = tl[ti]
        y0, y1, x0, x1, colink = geom[di]
        score = f[2]
        nul = space_null(colink, text, x0, x1)
        if score <= nul:
            continue
        off, pitch, _, _ = f
        band = ink[y0:y1, :]
        d = ndimage.distance_transform_edt(np.pad(band, 1))[1:-1, 1:-1]
        cells = []
        for i, ch in enumerate(text):
            a, b = max(int(off + i * pitch), 0), max(int(off + (i + 1) * pitch), 0)
            cm, cd = band[:, a:b], d[:, a:b]
            v = cd[cm]
            sw = float(2.0 * v[v >= np.percentile(v, 70)].mean()) if v.size else 0.0
            cells.append((ch, sw))
        out.append({"di": di, "ti": ti + 1, "text": text, "score": score,
                    "null": nul, "cells": cells})
        if verbose:
            sys.stderr.write(f"    line {di:3} -> transcript {ti+1:3}  "
                             f"score {score:.2f} > null {nul:.2f}   "
                             f"{text[:46]}\n")
    return out


def selftest():
    """Identity normalisation must kill an identity effect and keep a cipher."""
    rng = np.random.default_rng(4)
    letters = "abcdefghilnorst"
    # Face weights: each identity has its own intrinsic stroke width.
    face = {c: rng.uniform(4.0, 8.0) for c in letters}

    # Case 1: distressed face ONLY. Strong identity effect, no channel.
    ch1, sw1 = [], []
    for _ in range(600):
        c = rng.choice(list(letters))
        ch1.append(c)
        sw1.append(face[c] * rng.normal(1.0, 0.06))
    r1 = residuals(ch1, np.array(sw1))
    m1 = bic_1_vs_2(r1, sd_floor=0.02 * r1.std())[0]
    n1 = null_margin(len(r1), r1.mean(), r1.std(), step=0.005,
                     sd_floor=0.02 * r1.std())
    ok1 = m1 <= n1
    sys.stderr.write(f"  face only:      residual BIC {m1:+8.1f} vs null "
                     f"{n1:+7.1f} -> {'correctly no channel' if ok1 else 'FALSE POSITIVE'}\n")

    # Case 2: the same face PLUS a real 1.4x bold channel on 25% of characters.
    ch2, sw2 = [], []
    for _ in range(600):
        c = rng.choice(list(letters))
        bold = rng.random() < 0.25
        ch2.append(c)
        sw2.append(face[c] * (1.4 if bold else 1.0) * rng.normal(1.0, 0.06))
    r2 = residuals(ch2, np.array(sw2))
    m2, lo, hi, w = bic_1_vs_2(r2, sd_floor=0.02 * r2.std())
    n2 = null_margin(len(r2), r2.mean(), r2.std(), step=0.005,
                     sd_floor=0.02 * r2.std())
    ok2 = m2 > n2 and hi / max(lo, 1e-9) > 1.15
    sys.stderr.write(f"  face + cipher:  residual BIC {m2:+8.1f} vs null "
                     f"{n2:+7.1f}, {lo:.2f}/{hi:.2f} -> "
                     f"{'channel recovered' if ok2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok1 and ok2 else "FAIL\n"))
    return ok1 and ok2


def residuals(chars, sw):
    """Stroke width divided by the mean for that letter identity."""
    tot, cnt = defaultdict(float), defaultdict(int)
    for c, v in zip(chars, sw):
        tot[c] += v
        cnt[c] += 1
    return np.array([sw[i] / (tot[c] / cnt[c]) for i, c in enumerate(chars)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--pageno", type=int, default=77)
    ap.add_argument("--out", default="/tmp/char_cipher.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("identity normalisation fails its controls; refusing")
    if a.selftest:
        return

    rows = automap(a.img, a.pageno)
    if len(rows) < 5:
        sys.exit(f"only {len(rows)} lines aligned; not enough to test")

    chars, sw, where = [], [], []
    for r in rows:
        v = np.array([x for _, x in r["cells"]])
        nz = v[v > 0]
        med = np.median(nz) if nz.size else 1.0
        for i, (ch, x) in enumerate(r["cells"]):
            if ch.isalpha() and x > 0:
                chars.append(ch.lower())
                sw.append(x / med)
                where.append((r["ti"], i))
    sw = np.array(sw)
    sys.stderr.write(f"\n  {len(rows)} lines aligned, {len(sw)} characters\n")

    # Before normalisation: how big is the identity effect?
    by = defaultdict(list)
    for c, v in zip(chars, sw):
        by[c].append(v)
    means = {c: float(np.mean(v)) for c, v in by.items() if len(v) >= 8}
    if means:
        lo_c = min(means, key=means.get)
        hi_c = max(means, key=means.get)
        sys.stderr.write(f"  identity effect: {lo_c!r} mean "
                         f"{means[lo_c]:.2f} ... {hi_c!r} mean "
                         f"{means[hi_c]:.2f}  ({means[hi_c]/means[lo_c]:.2f}x "
                         f"across letters)\n")

    res = residuals(chars, sw)
    fl = 0.02 * res.std()
    m, lo, hi, w = bic_1_vs_2(res, sd_floor=fl)
    nul = null_margin(len(res), res.mean(), res.std(), step=0.005, sd_floor=fl)
    sys.stderr.write(f"\n  AFTER removing glyph identity: n={len(res)}  "
                     f"mean {res.mean():.3f}  sd {res.std():.3f}\n")
    sys.stderr.write(f"    BIC margin {m:+.1f}   unimodal null 95th pct "
                     f"{nul:+.1f}\n")
    sys.stderr.write(f"    two-component fit {lo:.3f} / {hi:.3f}  "
                     f"ratio {hi/max(lo,1e-9):.2f}  heavy weight {w:.3f}\n")
    real = m > nul and hi / max(lo, 1e-9) > 1.15 and 0.05 < w < 0.7
    sys.stderr.write("    " + (
        "CHANNEL: the same letter is set at two weights — a per-character "
        "cipher is present\n" if real else
        "NO CHANNEL: once each letter is compared with other instances of "
        "ITSELF, the weights are one population. The visible sub-word bold is "
        "the distressed face drawing each glyph at its own weight.\n"))

    json.dump({"lines": [{k: v for k, v in r.items() if k != "cells"}
                         for r in rows],
               "n": len(res), "bic": m, "null": nul, "lo": lo, "hi": hi,
               "weight": w, "channel": bool(real)},
              open(a.out, "w"), indent=1)
    sys.stderr.write(f"\n  -> {a.out}\n")


if __name__ == "__main__":
    main()
