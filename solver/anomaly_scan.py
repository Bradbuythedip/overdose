#!/usr/bin/env python3
"""
Hypothesis-free anomaly scan: find WHERE the article stops looking like English.

EVERY test in this project so far has been hypothesis-first — guess a
mechanism, build it, check the chain. That only pays off if the guess is right,
and roughly twenty guesses have now missed.

This inverts it. Any encoding embedded in text leaves a statistical trace: a
region carrying base58, hex, a key, or a substitution-ciphered payload does not
have the letter statistics of English prose. So rather than guessing the
mechanism, scan for the trace and let it point at the mechanism.

Measured per sliding window, on the article and on a matched baseline:
  index of coincidence     English ~0.066, random letters ~0.038
  chi-square against English letter frequencies
  Shannon entropy per character
  vowel ratio
  proportion of characters that are base58-legal

The baseline is the G D Schott paper — 8,490 words of ordinary published
English, the same register, processed identically. Comparing the article's
window distribution against the paper's separates "this article is unusual
prose" from "this REGION is not prose at all".

  python3 anomaly_scan.py --selftest
  python3 anomaly_scan.py
"""
import argparse, math, re, sys
from collections import Counter

import numpy as np

ENG = {  # standard English letter frequencies
    'a': .0817, 'b': .0150, 'c': .0278, 'd': .0425, 'e': .1270, 'f': .0223,
    'g': .0202, 'h': .0609, 'i': .0697, 'j': .0015, 'k': .0077, 'l': .0403,
    'm': .0241, 'n': .0675, 'o': .0751, 'p': .0193, 'q': .0010, 'r': .0599,
    's': .0633, 't': .0906, 'u': .0276, 'v': .0098, 'w': .0236, 'x': .0015,
    'y': .0197, 'z': .0007}
B58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def ic(s):
    n = len(s)
    if n < 2:
        return 0.0
    c = Counter(s)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))


def chi2(s):
    n = len(s)
    if n < 10:
        return 0.0
    c = Counter(s)
    return sum((c.get(k, 0) - n * p) ** 2 / (n * p) for k, p in ENG.items())


def entropy(s):
    n = len(s)
    if not n:
        return 0.0
    c = Counter(s)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def vowels(s):
    return sum(1 for ch in s if ch in "aeiou") / max(len(s), 1)


def windows(s, w, step):
    return [s[i:i + w] for i in range(0, max(len(s) - w + 1, 1), step)]


def profile(s, w=120, step=10):
    out = []
    for i, win in enumerate(windows(s, w, step)):
        if len(win) < w:
            continue
        out.append((i * step, ic(win), chi2(win), entropy(win), vowels(win)))
    return np.array(out) if out else np.zeros((0, 5))


def selftest():
    """A planted non-English region must show up as an outlier."""
    import random
    rng = random.Random(3)
    eng = letters("the markets sensed bitcoin was coming and started to crash "
                  "markets are like that they discount stuff in advance markets "
                  "are the central nervous system of the global economy " * 12)
    # plant a base58 key-like blob in the middle
    blob = "".join(rng.choice("abcdefghijkmnpqrstuvwxyz") for _ in range(120))
    spiked = eng[:600] + blob + eng[600:]
    p_clean = profile(eng)
    p_spike = profile(spiked)
    if len(p_clean) < 5 or len(p_spike) < 5:
        sys.stderr.write("  SELFTEST FAIL (too little data)\n")
        return False
    base_ic = float(np.median(p_clean[:, 1]))
    worst = float(p_spike[:, 1].min())
    sep = base_ic - worst
    sys.stderr.write(f"  clean English median IC {base_ic:.4f}, "
                     f"lowest IC with a planted random blob {worst:.4f}\n")
    ok = sep > 0.008
    sys.stderr.write(f"  planted non-English region detected: "
                     f"{'OK' if ok else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", default="article_transcript.txt")
    ap.add_argument("--baseline", default="/tmp/schott.txt")
    ap.add_argument("--window", type=int, default=120)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("scanner cannot detect a planted anomaly; refusing to report")
    if a.selftest:
        return

    raw = open(a.article, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    raw = re.sub(r"^=== PAGE.*$", "", raw, flags=re.M)
    art = letters(raw)
    base = letters(open(a.baseline, encoding="utf-8").read())

    pa = profile(art, a.window)
    pb = profile(base, a.window)
    sys.stderr.write(f"\n  article {len(art):,} letters -> {len(pa)} windows\n")
    sys.stderr.write(f"  baseline {len(base):,} letters -> {len(pb)} windows\n\n")

    names = ["index of coincidence", "chi2 vs English", "entropy/char", "vowel ratio"]
    for k, nm in enumerate(names, start=1):
        av, bv = pa[:, k], pb[:, k]
        sys.stderr.write(f"  {nm:22} article {av.mean():8.4f} +/- {av.std():.4f}   "
                         f"baseline {bv.mean():8.4f} +/- {bv.std():.4f}\n")

    # per-window z against the BASELINE distribution, not the article's own
    sys.stderr.write("\n  most anomalous article windows "
                     "(z against the baseline distribution):\n")
    z = np.zeros(len(pa))
    for k in (1, 2, 3, 4):
        mu, sd = pb[:, k].mean(), pb[:, k].std() or 1
        z += np.abs((pa[:, k] - mu) / sd)
    order = np.argsort(z)[::-1]
    for i in order[:8]:
        off = int(pa[i, 0])
        sys.stderr.write(f"    offset {off:5}  z={z[i]:5.1f}  "
                         f"IC={pa[i,1]:.4f}  chi2={pa[i,2]:6.1f}  "
                         f"{art[off:off+60]}\n")

    # how anomalous is the WORST article window against the baseline's worst?
    zb = np.zeros(len(pb))
    for k in (1, 2, 3, 4):
        mu, sd = pb[:, k].mean(), pb[:, k].std() or 1
        zb += np.abs((pb[:, k] - mu) / sd)
    sys.stderr.write(f"\n  article worst-window z {z.max():.1f}   "
                     f"baseline worst-window z {zb.max():.1f}\n  ")
    sys.stderr.write("ANOMALY: a region of the article is less English-like than "
                     "anything in a matched English text\n"
                     if z.max() > zb.max() else
                     "NO ANOMALY: every article window is as English-like as "
                     "ordinary prose — no embedded non-English region\n")

    b58 = sum(1 for c in re.sub(r"\s", "", raw) if c in B58)
    tot = len(re.sub(r"\s", "", raw))
    sys.stderr.write(f"\n  base58-legal characters: {b58}/{tot} "
                     f"({b58/max(tot,1)*100:.1f}%)\n")


if __name__ == "__main__":
    main()
