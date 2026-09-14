#!/usr/bin/env python3
"""
Is the sub-word bold on page 77 a real weight channel, or a distressed face?

WHY PAGE 77 DECIDES IT
This project ruled out per-CHARACTER bold twice, on the grounds that the calls
tracked glyph identity rather than weight: across the earlier pages v/i/l/u/d
were called bold ten to thirty times more often than a/c/n/o. That argument was
computed on 212 dpi JPEG of small dark-on-light type, and it may have been
measuring the measurement.

Page 77 is different, and it was never examined, because it is the one page the
scanner produced no text mask for — it is printed white-on-dark, so there was
no black-on-white layer to separate, and it also happens to have been scanned
upside down. Rotated and rendered at 600 dpi it is by a wide margin the best
conditioned text in the artefact: large, wide-tracked, high-contrast. At that
resolution the sub-word bold is plainly visible — "star(ve) to (death) as (the)
resu(l)t" — so the question is no longer whether it can be seen but what it is.

THE DISCRIMINATOR
A cipher needs TWO WEIGHTS OF ONE FACE. A distressed typewriter face needs only
one weight with uneven ink. They differ in a way that does not depend on
reading anything:

  cipher            instances of the SAME letter fall into two separated
                    clusters, because the same glyph is set both ways
  distressed face   instances of the same letter form ONE spread-out cluster,
                    because ink varies continuously and per-glyph

So the test is within-letter bimodality, run per letter identity and pooled,
against the operation-matched unimodal null already calibrated in gap_cipher
(7% realised false-positive rate at a nominal 5%).

A second, assumption-free check needs no transcript alignment at all: find
repeated WORDS on the page and ask whether the same word appears at two
different weights.

  python3 p77_weight.py --selftest
  python3 p77_weight.py --img <600dpi p77 png>
"""
import argparse, os, re, sys
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage

from gap_cipher import bic_1_vs_2, null_margin

Image.MAX_IMAGE_PIXELS = None

# The body lines of p77, in print order. Display headline (17-21) excluded:
# it is a different face at a different size and would confound weight.
BODY = list(range(1, 17)) + list(range(22, 33))


def transcript(pageno=77, path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    for num, body in zip(it, it):
        if int(num) == pageno:
            return [l.strip() for l in body.splitlines() if l.strip()]
    return []


def ink_of(path, invert=None):
    """Boolean ink mask, with the POLARITY DECIDED FROM THE DATA.

    Page 77 is white text on dark paper, the other pages are the reverse, and
    getting this backwards does not fail loudly — it segments the paper as if
    it were ink and returns a few hundred fragments that look like a plausible
    glyph count. Ink is whichever side of the threshold is the minority class.
    """
    g = np.asarray(Image.open(path).convert("L")).astype(np.float32)
    # Otsu, with the numerator's `tot` factor that an earlier version of this
    # project dropped — without it the score climbs monotonically and the
    # threshold comes back as 254 on every page.
    h, _ = np.histogram(g, bins=256, range=(0, 256))
    tot = h.sum()
    idx = np.arange(256)
    w = np.cumsum(h)
    mt = float((idx * h).sum())
    m = np.cumsum(idx * h)
    num = (m * tot - w * mt) ** 2
    den = (tot ** 2) * w * (tot - w)
    valid = den > 0                      # degenerate splits excluded, not fudged
    score = np.where(valid, num / np.where(valid, den, 1), -1.0)
    thr = int(np.argmax(score))
    bright = g > thr
    ink = bright if bright.mean() < 0.5 else ~bright
    if invert is not None:                       # explicit override for tests
        ink = (g <= thr) if invert else (g > thr)
    return ink, thr


def glyphs(ink, min_h, max_h, min_px):
    lab, n = ndimage.label(ink)
    objs = ndimage.find_objects(lab)
    out = []
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if not (min_h <= y1 - y0 <= max_h):
            continue
        m = lab[sl] == i
        if int(m.sum()) < min_px:
            continue
        out.append({"bbox": (x0, y0, x1, y1), "mask": m})
    return out


def stroke(m):
    """Mean stroke width = 2x the mean distance-to-edge over the ridge."""
    d = ndimage.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
    v = d[m]
    if v.size == 0:
        return 0.0
    return float(2.0 * v[v >= np.percentile(v, 70)].mean())


def merge_marks(line, xtol=0.55):
    """Merge components that are parts of ONE character.

    Connected components are not characters: the dot of an i or j, the two
    halves of a colon, a quote mark and an accent each arrive separately. A
    raw component count therefore overshoots the character count — here by
    roughly 15% — and any transcript alignment built on it silently shifts
    every identity after the first split glyph. Components whose horizontal
    extents overlap by more than `xtol` of the narrower one are combined.
    """
    out = []
    for c in sorted(line, key=lambda c: c["bbox"][0]):
        if out:
            px0, py0, px1, py1 = out[-1]["bbox"]
            x0, y0, x1, y1 = c["bbox"]
            ov = min(px1, x1) - max(px0, x0)
            if ov > 0 and ov >= xtol * min(px1 - px0, x1 - x0):
                nb = (min(px0, x0), min(py0, y0), max(px1, x1), max(py1, y1))
                m = np.zeros((nb[3] - nb[1], nb[2] - nb[0]), dtype=bool)
                for g in (out[-1], c):
                    gx0, gy0, gx1, gy1 = g["bbox"]
                    m[gy0 - nb[1]:gy1 - nb[1], gx0 - nb[0]:gx1 - nb[0]] |= g["mask"]
                out[-1] = {"bbox": nb, "mask": m}
                continue
        out.append(c)
    return out


def lines_of(gl, tol):
    rows = sorted(gl, key=lambda c: (c["bbox"][1] + c["bbox"][3]) / 2)
    out, cur = [], [rows[0]]
    for c in rows[1:]:
        cc = np.mean([(x["bbox"][1] + x["bbox"][3]) / 2 for x in cur])
        if abs((c["bbox"][1] + c["bbox"][3]) / 2 - cc) <= tol:
            cur.append(c)
        else:
            out.append(cur)
            cur = [c]
    out.append(cur)
    return [sorted(l, key=lambda c: c["bbox"][0]) for l in out]


def selftest():
    """Two-weight text must be called; one-weight distressed text must not."""
    rng = np.random.default_rng(5)
    n = 240
    # A single weight with heavy per-glyph ink variation — a distressed face.
    distressed = rng.normal(6.0, 1.1, n)
    nul = null_margin(n, distressed.mean(), distressed.std(), step=0.05)
    m1 = bic_1_vs_2(distressed)[0]
    ok1 = m1 <= nul
    sys.stderr.write(f"  distressed single weight: margin {m1:+.1f} vs null "
                     f"{nul:+.1f} -> {'correctly not called' if ok1 else 'FALSE POSITIVE'}\n")
    # Two genuine weights, 1.5x apart, with the same per-glyph noise.
    two = np.concatenate([rng.normal(6.0, 0.6, 170), rng.normal(9.0, 0.6, 70)])
    m2, lo, hi, w = bic_1_vs_2(two)
    nul2 = null_margin(len(two), two.mean(), two.std(), step=0.05)
    ok2 = m2 > nul2 and hi / lo > 1.25
    sys.stderr.write(f"  two real weights: margin {m2:+.1f} vs null {nul2:+.1f}, "
                     f"{lo:.1f}/{hi:.1f} (ratio {hi/lo:.2f}) -> "
                     f"{'detected' if ok2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok1 and ok2 else "FAIL\n"))
    return ok1 and ok2


def words_of(line, wgap=0.55):
    """Split a line's glyphs into words at gaps wider than `wgap` of a pitch."""
    w = float(np.median([c["bbox"][2] - c["bbox"][0] for c in line])) or 1.0
    out, cur = [], [line[0]]
    for a, b in zip(line, line[1:]):
        if (b["bbox"][0] - a["bbox"][2]) > wgap * w:
            out.append(cur)
            cur = [b]
        else:
            cur.append(b)
    out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--pageno", type=int, default=77)
    ap.add_argument("--first", type=int, default=21,
                    help="index of the first detected line of the block")
    ap.add_argument("--tfirst", type=int, default=22,
                    help="transcript line number that block starts at")
    ap.add_argument("--nlines", type=int, default=11)
    ap.add_argument("--skip", type=int, nargs="*", default=[29],
                    help="detected lines to drop (knocked-out highlight bars)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("estimator fails its controls; refusing to report")
    if a.selftest:
        return

    ink, thr = ink_of(a.img)
    H, W = ink.shape
    s = H / 6600.0
    gl = glyphs(ink, int(20 * s), int(150 * s), int(60 * s))
    lines = [merge_marks(l) for l in lines_of(gl, tol=22 * s) if len(l) >= 6]
    sys.stderr.write(f"\n  {os.path.basename(a.img)} {W}x{H}, Otsu {thr}, "
                     f"{len(gl)} components, {len(lines)} lines\n")

    tl = transcript(a.pageno)
    blk = [(i, lines[i]) for i in
           range(a.first, min(a.first + a.nlines, len(lines)))
           if i not in a.skip]
    twant = [tl[a.tfirst - 1 + k] for k in range(a.nlines)
             if (a.first + k) not in a.skip]

    # Per-WORD alignment with a per-word count check. Whole-line alignment
    # fails here because the distressed face breaks some strokes into two
    # components, so a line can overshoot by a few glyphs; aligning word by
    # word confines the damage to the word that broke instead of shifting every
    # identity after it.
    per_letter = defaultdict(list)
    per_word = defaultdict(list)
    used = skipped = 0
    for (li, line), text in zip(blk, twant):
        dwords = words_of(line)
        twords = text.split()
        if len(dwords) != len(twords):
            skipped += len(twords)
            continue
        v = np.array([stroke(c["mask"]) for c in line])
        med = np.median(v) or 1.0
        k = 0
        for dw, tw in zip(dwords, twords):
            n = len(dw)
            vals = v[k:k + n] / med
            k += n
            if n != len(tw):
                skipped += 1
                continue
            used += 1
            per_word[tw.lower().strip(".,'\"()")].append(float(np.mean(vals)))
            for ch, x in zip(tw.lower(), vals):
                if ch.isalpha():
                    per_letter[ch].append(float(x))

    sys.stderr.write(f"  {used} words aligned, {skipped} skipped on a count "
                     f"mismatch\n")
    if used < 40:
        sys.exit("too little aligned text to test per-letter weight")

    allv = np.array([x for v in per_letter.values() for x in v])
    fl = 0.02 * allv.std()
    m, lo, hi, wt = bic_1_vs_2(allv, sd_floor=fl)
    nul = null_margin(len(allv), allv.mean(), allv.std(), step=0.005,
                      sd_floor=fl)
    cut = 0.5 * (lo + hi)
    sys.stderr.write(f"\n  POOLED n={len(allv)}  BIC {m:+.1f} vs null {nul:+.1f}"
                     f"  fit {lo:.3f}/{hi:.3f} ratio {hi/max(lo,1e-9):.2f}"
                     f"  heavy {wt:.3f}  cut {cut:.3f}\n")

    # THE DISCRIMINATOR. If weight is a channel, the SAME letter must appear at
    # both weights. If the face merely inks some glyph shapes more heavily, each
    # letter sits wholly on one side of the cut.
    sys.stderr.write("\n  per-letter: does the same glyph occur at both "
                     "weights?\n")
    split = kept = 0
    for ch in sorted(per_letter):
        v = np.array(per_letter[ch])
        if len(v) < 10:
            continue
        kept += 1
        frac = float((v > cut).mean())
        both = 0.12 <= frac <= 0.88
        split += both
        sys.stderr.write(f"    {ch!r} n={len(v):4}  heavy {frac*100:5.1f}%  "
                         f"mean {v.mean():.2f}  range {v.min():.2f}-{v.max():.2f}"
                         f"  {'BOTH weights' if both else ''}\n")
    sys.stderr.write(f"\n  {split}/{kept} letters occur at BOTH weights\n")
    sys.stderr.write("  " + (
        "WEIGHT IS A CHANNEL: the same glyph is set both ways, so this is not "
        "the face inking some shapes more heavily\n" if split >= 0.6 * kept else
        "GLYPH IDENTITY, NOT WEIGHT: each letter sits on one side of the cut, "
        "which is what a distressed face does\n"))

    rep = [(w, float(np.mean(v)), len(v)) for w, v in per_word.items()
           if len(v) >= 3]
    rep.sort(key=lambda t: -t[2])
    sys.stderr.write("\n  repeated words, mean weight per occurrence:\n")
    for w, _, n in rep[:14]:
        vs = per_word[w]
        sys.stderr.write(f"    {w!r:16} x{n:2}  " +
                         " ".join(f"{x:.2f}" for x in vs) + "\n")


if __name__ == "__main__":
    main()
