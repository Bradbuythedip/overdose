#!/usr/bin/env python3
"""
Per-WORD bold detection that controls for what the word is made of.

WHY THE EARLIER ATTEMPTS FAILED
Both the stroke-width detector and a naive ink-per-glyph ratio confound GLYPH
IDENTITY with WEIGHT. "MAXIMALIST" inks far more than "till" at identical
weight, so any measure that does not know which characters a word contains is
measuring vocabulary, not typography. Measured on p78, ink-per-glyph
normalised per line gives a UNIMODAL distribution with a long right tail — no
separation between regular and bold at all.

THE FIX
Least squares. Every word's ink should be approximately the sum of a
per-character ink coefficient over its characters:

    A x = b        A[i][c] = count of character c in word i
                   b[i]    = measured ink area of word i
                   x[c]    = ink contributed by one instance of character c

Fit x over all words on the page. Since most words are regular, the fit learns
regular-weight coefficients. A word's bold-ness is then its residual ratio,
b[i] / (A x)[i] — measured ink over predicted-at-regular-weight — which is
free of the vocabulary confound by construction.

Alignment to the transcript is required to know each word's characters, and is
checked rather than assumed: a page whose detected line count or per-line word
count disagrees with the transcript is REPORTED AND SKIPPED, not silently
mis-aligned. A wrong alignment would shift every character and produce
confident nonsense.

  python3 word_bold.py --page ../IMG_6249.jpeg --pageno 78
"""
import argparse, re, sys

import numpy as np

import bold_extract as B
from bacon_cipher import words_of_line

NON_BODY = {"bitcoin is toxic af", "max keiser"}


def transcript_lines(pageno, path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    for num, body in zip(it, it):
        if int(num) == int(pageno):
            return [l.strip() for l in body.splitlines() if l.strip()]
    return []


def measure(path, pageno, scale=2, verbose=True):
    im, g = B.load_gray(path, scale)
    ink, thr, bars = B.ink_mask(g)
    comps = B.components(ink, 14 * scale // 2, 90 * scale // 2, 40)
    lines = [l for l in B.group_lines(comps, tol=12 * scale) if len(l) >= 8]
    wmed = float(np.median([c["bbox"][2] - c["bbox"][0] for c in comps]))

    tl = [l for l in transcript_lines(pageno) if l.lower() not in NON_BODY]
    det = []
    for ln in lines:
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        gl = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.45 * hmed]
        if len(gl) >= 4:
            det.append(words_of_line(gl, wmed))

    if verbose:
        sys.stderr.write(f"  detected {len(det)} text lines, transcript has "
                         f"{len(tl)} body lines\n")
    if len(det) != len(tl):
        if verbose:
            sys.stderr.write("  ALIGNMENT MISMATCH — skipping this page rather "
                             "than mis-assigning characters\n")
        return None

    rows, inks, labels = [], [], []
    aligned = 0
    for dwords, tline in zip(det, tl):
        twords = re.findall(r"[A-Za-z0-9$%'-]+", tline)
        if len(dwords) != len(twords):
            continue                       # skip only this line
        aligned += 1
        for dw, tw in zip(dwords, twords):
            rows.append(tw)
            inks.append(sum(int(c["mask"].sum()) for c in dw))
            labels.append(tw)
    if verbose:
        sys.stderr.write(f"  {aligned}/{len(tl)} lines word-aligned, "
                         f"{len(rows)} words measured\n")
    if len(rows) < 40:
        return None

    chars = sorted({c for w in rows for c in w.lower() if c.isalnum()})
    idx = {c: i for i, c in enumerate(chars)}
    A = np.zeros((len(rows), len(chars)))
    for i, w in enumerate(rows):
        for c in w.lower():
            if c in idx:
                A[i, idx[c]] += 1
    b = np.array(inks, dtype=float)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    pred = A @ x
    ok = pred > 1
    ratio = np.ones(len(rows))
    ratio[ok] = b[ok] / pred[ok]
    return labels, ratio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--pageno", required=True)
    a = ap.parse_args()

    r = measure(a.page, a.pageno)
    if r is None:
        sys.exit("could not align this page")
    labels, ratio = r

    h, e = np.histogram(ratio, bins=20, range=(0.4, 2.4))
    sys.stderr.write("\n  residual ratio (measured ink / predicted-at-regular):\n")
    for i in range(20):
        sys.stderr.write(f"    {e[i]:.2f}-{e[i+1]:.2f} "
                         f"{'#'*int(60*h[i]/max(h.max(),1))} {h[i]}\n")

    for thr in (1.15, 1.25, 1.35):
        sys.stderr.write(f"  fraction >= {thr}: {(ratio>=thr).mean():.3f}\n")

    order = np.argsort(ratio)[::-1]
    sys.stderr.write("\n  heaviest 25 words (should be the visibly bold ones):\n    ")
    sys.stderr.write(" ".join(f"{labels[i]}({ratio[i]:.2f})" for i in order[:25]))
    sys.stderr.write("\n\n  lightest 12 words:\n    ")
    sys.stderr.write(" ".join(f"{labels[i]}({ratio[i]:.2f})" for i in order[-12:]))
    sys.stderr.write("\n")


if __name__ == "__main__":
    main()
