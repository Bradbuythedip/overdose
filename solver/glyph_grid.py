#!/usr/bin/env python3
"""
Per-CHARACTER weight on a monospace grid, with the alignment self-verified.

WHY A GRID AND NOT CONNECTED COMPONENTS
Every previous per-character attempt in this project segmented glyphs as
connected components, and that is the thing that broke them. The face is
deliberately distressed: strokes have gaps, so one character arrives as two or
three components, while an i or a colon arrives as two more. Component counts
therefore overshoot the character count by 10-20% and by a different amount on
every line. Any alignment built on them shifts identities after the first
broken glyph, and a shifted alignment does not fail loudly — it produces
confident per-letter statistics about the wrong letters.

The face is monospaced, so there is a better segmentation available: a fixed
pitch grid. Each character owns one cell. Broken strokes rejoin inside their
cell, i-dots sit above their stems, and spaces are simply empty cells.

The page is justified by TRACKING — the pitch is stretched per line to fill the
measure, and on page 77 it ranges from 47 to 67 px at 600 dpi — so pitch and
offset are fitted per line rather than assumed global.

THE ALIGNMENT IS CHECKED, NOT ASSUMED
The transcript says which cells must be spaces. A correct fit puts almost no
ink in those cells and plenty in the rest. The separation between the two is
reported per line, and a line that does not separate cleanly is DROPPED. This
is a real check: a grid off by one cell smears ink into the space cells and
the line is rejected rather than silently mis-assigning every character.

  python3 glyph_grid.py --selftest
  python3 glyph_grid.py --img <png> --pageno 77 --lines 21:22:11
"""
import argparse, json, os, re, sys
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage

from p77_weight import ink_of, glyphs, lines_of, transcript, stroke

Image.MAX_IMAGE_PIXELS = None


def fit_grid(colink, text, x0, x1):
    """Fit (offset, pitch) so transcript spaces land on low-ink cells.

    Grid search over a plausible range, scoring by the gap between mean ink in
    non-space cells and mean ink in space cells. Returns (off, pitch, score,
    per-cell ink).
    """
    n = len(text)
    if n < 4:
        return None
    isspace = np.array([c == " " for c in text])
    if isspace.sum() == 0 or (~isspace).sum() == 0:
        return None
    best = None
    span = x1 - x0
    # The grid must SPAN the line, so pitch is near span/(n-1). A wide search
    # lets pitch and offset trade off to fake a whole-cell shift, which defeats
    # the space-cell check; +-12% is generous for tracking variation.
    p0 = span / max(n - 1.0, 1)
    for pitch in np.linspace(0.88 * p0, 1.12 * p0, 60):
        for off in np.linspace(x0 - 0.45 * pitch, x0 + 0.45 * pitch, 25):
            edges = off + np.arange(n + 1) * pitch
            if edges[-1] > len(colink) + pitch:
                continue
            cells = np.array([
                colink[max(int(edges[i]), 0):max(int(edges[i + 1]), 0)].sum()
                for i in range(n)], dtype=float)
            if cells.sum() <= 0:
                continue
            c = cells / cells.max()
            sc = float(c[~isspace].mean() - c[isspace].mean())
            if best is None or sc > best[2]:
                best = (off, pitch, sc, cells)
    return best


def space_null(colink, text, x0, x1, trials=30, seed=11):
    """Best score obtainable with the SAME number of spaces in wrong places.

    An absolute score threshold cannot say whether an alignment is right: a
    long line with many correct spaces scores well even with one space out of
    place, and a short line scores badly even when perfect. Permuting this
    line's own spaces gives the score distribution for a wrong transcript of
    exactly this shape, so the real fit has to beat its own null.
    """
    rng = np.random.default_rng(seed)
    n, k = len(text), text.count(" ")
    if k == 0:
        return 1e9
    best = -1e9
    for _ in range(trials):
        pos = rng.choice(np.arange(1, n - 1), size=k, replace=False)
        t = "".join(" " if i in set(pos.tolist()) else "x" for i in range(n))
        f = fit_grid(colink, t, x0, x1)
        if f and f[2] > best:
            best = f[2]
    return best


def measure_page(img, pageno, first, tfirst, nlines, skip=(), verbose=True):
    ink, thr = ink_of(img)
    H, W = ink.shape
    s = H / 6600.0
    gl = glyphs(ink, int(20 * s), int(150 * s), int(60 * s))
    lines = [l for l in lines_of(gl, tol=22 * s) if len(l) >= 6]
    tl = transcript(pageno)
    if verbose:
        sys.stderr.write(f"  {os.path.basename(img)} {W}x{H}, Otsu {thr}, "
                         f"{len(lines)} lines, transcript {len(tl)}\n")

    out = []
    for k in range(nlines):
        di = first + k
        if di in skip or di >= len(lines) or tfirst - 1 + k >= len(tl):
            continue
        line = lines[di]
        text = tl[tfirst - 1 + k]
        y0 = min(c["bbox"][1] for c in line)
        y1 = max(c["bbox"][3] for c in line)
        x0 = min(c["bbox"][0] for c in line)
        x1 = max(c["bbox"][2] for c in line)
        band = ink[y0:y1, :]
        colink = band.sum(axis=0).astype(float)
        fit = fit_grid(colink, text, x0, x1)
        if fit is None:
            continue
        off, pitch, score, cells = fit
        nul = space_null(colink, text, x0, x1)
        ok = score > nul
        if verbose:
            tag = "ok" if ok else ("DROPPED: a wrong space pattern fits this "
                                   "line as well as the transcript does")
            sys.stderr.write(f"    line {di:3} <- t{tfirst+k:3}  pitch "
                             f"{pitch:5.1f}  score {score:5.2f}  "
                             f"null {nul:5.2f}  {tag}\n")
        if not ok:
            continue
        # Per-cell stroke width from the distance transform of that cell only.
        d = ndimage.distance_transform_edt(np.pad(band, 1))[1:-1, 1:-1]
        rec = []
        for i, ch in enumerate(text):
            a = max(int(off + i * pitch), 0)
            b = max(int(off + (i + 1) * pitch), 0)
            cm = band[:, a:b]
            cd = d[:, a:b]
            v = cd[cm]
            sw = float(2.0 * v[v >= np.percentile(v, 70)].mean()) if v.size else 0.0
            rec.append({"ch": ch, "ink": float(cm.sum()), "sw": sw})
        out.append({"line": di, "tline": tfirst + k, "text": text,
                    "pitch": pitch, "score": score, "cells": rec})
    return out


def selftest():
    """A synthetic monospace line with known spaces must align exactly."""
    text = "ab cd  ef ghi"
    pitch, h = 20, 30
    W = len(text) * pitch + 40
    img = np.zeros((h + 20, W), dtype=bool)
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        x = 20 + i * pitch
        img[10:10 + h, x + 3:x + pitch - 3] = True
    col = img.sum(axis=0).astype(float)
    xs = np.flatnonzero(col)
    fit = fit_grid(col, text, xs[0], xs[-1])
    ok = fit is not None
    if ok:
        off, p, sc, cells = fit
        c = cells / cells.max()
        sp = [i for i, ch in enumerate(text) if ch == " "]
        nz = [i for i, ch in enumerate(text) if ch != " "]
        ok = max(c[i] for i in sp) < 0.15 and min(c[i] for i in nz) > 0.5
        sys.stderr.write(f"  fitted pitch {p:.1f} (true {pitch}), score "
                         f"{sc:.2f}\n")
        sys.stderr.write(f"  max ink in a SPACE cell {max(c[i] for i in sp):.3f}"
                         f", min ink in a LETTER cell "
                         f"{min(c[i] for i in nz):.3f}\n")
    # A WRONG transcript must be rejected, or the check is worthless. Leading
    # a space onto the front is not wrong, only translated, and the fitter can
    # legitimately absorb that; the control has to move a space RELATIVE to the
    # others so no offset can rescue it.
    nul = space_null(col, text, xs[0], xs[-1])
    sys.stderr.write(f"  true score {sc:.2f} vs best wrong-space-pattern "
                     f"score {nul:.2f}\n")
    ok = ok and sc > nul
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--pageno", type=int, default=77)
    ap.add_argument("--lines", default="21:22:11",
                    help="firstDetected:firstTranscript:count")
    ap.add_argument("--skip", type=int, nargs="*", default=[])
    ap.add_argument("--out", default="/tmp/grid.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("grid fitter cannot align a synthetic line; refusing")
    if a.selftest:
        return

    f, t, n = (int(x) for x in a.lines.split(":"))
    res = measure_page(a.img, a.pageno, f, t, n, skip=set(a.skip))
    json.dump(res, open(a.out, "w"), indent=1)
    sys.stderr.write(f"\n  {len(res)} lines aligned -> {a.out}\n")

    per = defaultdict(list)
    for ln in res:
        v = np.array([c["sw"] for c in ln["cells"] if c["ch"] != " "])
        med = np.median(v[v > 0]) or 1.0
        for c in ln["cells"]:
            if c["ch"].isalpha():
                per[c["ch"].lower()].append(c["sw"] / med)
    allv = np.array([x for v in per.values() for x in v])
    if len(allv) < 60:
        sys.exit("too few characters")

    from gap_cipher import bic_1_vs_2, null_margin
    fl = 0.02 * allv.std()
    m, lo, hi, wt = bic_1_vs_2(allv, sd_floor=fl)
    nul = null_margin(len(allv), allv.mean(), allv.std(), step=0.005, sd_floor=fl)
    cut = 0.5 * (lo + hi)
    sys.stderr.write(f"\n  n={len(allv)}  BIC {m:+.1f} vs null {nul:+.1f}  "
                     f"fit {lo:.3f}/{hi:.3f} ratio {hi/max(lo,1e-9):.2f}  "
                     f"heavy {wt:.3f}  cut {cut:.3f}\n")

    sys.stderr.write("\n  does the SAME letter occur at both weights?\n")
    split = kept = 0
    for ch in sorted(per):
        v = np.array(per[ch])
        if len(v) < 10:
            continue
        kept += 1
        frac = float((v > cut).mean())
        both = 0.12 <= frac <= 0.88
        split += both
        sys.stderr.write(f"    {ch!r} n={len(v):4}  heavy {frac*100:5.1f}%  "
                         f"{'BOTH' if both else ''}\n")
    sys.stderr.write(f"\n  {split}/{kept} letters occur at BOTH weights\n  ")
    sys.stderr.write("WEIGHT IS A CHANNEL\n" if split >= 0.6 * kept else
                     "GLYPH IDENTITY, NOT WEIGHT\n")

    for ln in res:
        v = np.array([c["sw"] for c in ln["cells"] if c["ch"] != " "])
        med = np.median(v[v > 0]) or 1.0
        s = "".join(("*" if c["sw"] / med > cut else ".") if c["ch"] != " "
                    else " " for c in ln["cells"])
        sys.stderr.write(f"    {ln['text']}\n    {s}\n")


if __name__ == "__main__":
    main()
