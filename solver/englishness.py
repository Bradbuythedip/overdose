#!/usr/bin/env python3
"""
Is any every-Nth extraction actually hidden English?

Brute-forcing 13,540 extracted strings as brainwallet passphrases only answers
"is one of these the key". The prior question is cheaper and more informative:
does ANY of them contain English word order at all? If a null cipher is really
there, the extracted text reads as language; if not, every extraction is just a
reshuffling of the article's letters.

THE NULL MODEL (no dictionary needed, and none is installed here)
An every-Nth extraction from English prose inherits the source's LETTER
DISTRIBUTION but destroys its ORDER. So the right null for a given extraction
is a random permutation of its own letters -- same letters, same frequencies,
order deliberately broken. Scoring the extraction against its own shuffles
controls for letter frequency exactly, which a raw trigram count would not:
a string rich in E, T, A scores high on English trigrams whether or not it
says anything.

score  = common-English-trigram hits per character
z      = (score - mean(shuffled scores)) / sd(shuffled scores)

Real English lands at z of roughly +8 and up. Order-free extractions sit at
z ~ 0 by construction. The script prints a positive control (the article's own
prose) and a negative control (that prose shuffled) so the scale is anchored
rather than asserted.

  python3 englishness.py --in /tmp/everynth.txt --transcript article_transcript.txt
"""
import argparse, random, re, sys

# Common English trigrams. Frequency-ordered lists vary in the tail; only the
# set membership matters here, since the shuffle null absorbs any weighting bias.
TRIGRAMS = set("""
the and ing ion tio ent ati for her ter hat tha ere ate his con res ver all ons
nce men ith ted ers pro thi wit are ess not ive out eve est ust oth ill any per
und rea sta int com ist ard ain ort our ure end has ough igh ction tion
""".split())


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def score(s):
    if len(s) < 3:
        return 0.0
    n = sum(1 for i in range(len(s) - 2) if s[i:i + 3] in TRIGRAMS)
    return n / (len(s) - 2)


def zscore(s, shuffles, rng):
    base = score(s)
    chars = list(s)
    vals = []
    for _ in range(shuffles):
        rng.shuffle(chars)
        vals.append(score("".join(chars)))
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)
    sd = var ** 0.5
    if sd == 0:
        return 0.0, base, m
    return (base - m) / sd, base, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--shuffles", type=int, default=40)
    ap.add_argument("--min-len", type=int, default=40)
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()

    rng = random.Random(20260913)

    # ---- controls, so the z scale is anchored rather than asserted ----
    raw = open(a.transcript, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    raw = re.sub(r"^=== PAGE.*$", "", raw, flags=re.M)
    prose = letters(raw)
    zp, bp, mp = zscore(prose, a.shuffles, rng)
    shuffled = list(prose)
    rng.shuffle(shuffled)
    zn, bn, mn = zscore("".join(shuffled), a.shuffles, rng)
    sys.stderr.write(f"  POSITIVE control (article prose, {len(prose)} chars): "
                     f"z = {zp:+.1f}  (score {bp:.4f} vs shuffled {mp:.4f})\n")
    sys.stderr.write(f"  NEGATIVE control (same letters, shuffled):          "
                     f"z = {zn:+.1f}  (score {bn:.4f} vs shuffled {mn:.4f})\n")
    if zp < 5:
        sys.exit("positive control failed -- scorer is not detecting English")
    sys.stderr.write("  controls OK\n\n")

    rows = []
    n = 0
    for line in open(a.inp, encoding="utf-8", errors="replace"):
        s = letters(line.strip())
        if len(s) < a.min_len:
            continue
        n += 1
        z, base, mean = zscore(s, a.shuffles, rng)
        rows.append((z, len(s), base, line.strip()[:120]))

    rows.sort(reverse=True)
    sys.stderr.write(f"scored {n:,} extractions of >= {a.min_len} letters\n\n")
    sys.stderr.write(f"  top {a.top} by englishness z:\n")
    for z, ln, base, s in rows[:a.top]:
        sys.stderr.write(f"    z={z:+6.2f}  len={ln:5d}  {s[:100]}\n")

    if not rows:
        return

    # ---- family-wise null ----
    # "highest z = 5.6" means nothing on its own: with this many extractions,
    # some large z is expected, and z from a shuffle test on short strings is
    # skewed and discrete rather than normal, so a textbook tail probability
    # would be wrong. Build the null empirically instead -- shuffle EVERY
    # extraction once and score the shuffled family exactly the same way. The
    # real family only carries signal if its maximum beats the null family's.
    null = []
    for _, ln, _, s in rows:
        t = list(letters(s) if len(letters(s)) >= a.min_len else "")
        if not t:
            continue
        rng.shuffle(t)
        z, _, _ = zscore("".join(t), a.shuffles, rng)
        null.append(z)
    null.sort(reverse=True)

    top = rows[0][0]
    nmax = null[0] if null else float("nan")
    n95 = null[max(int(len(null) * 0.05) - 1, 0)] if null else float("nan")
    sys.stderr.write(f"\n  real family : max z = {top:+.2f}  "
                     f"(n={len(rows)})\n")
    sys.stderr.write(f"  null family : max z = {nmax:+.2f}, "
                     f"95th pct {n95:+.2f}  (same strings, letters shuffled)\n")
    sys.stderr.write(f"  prose control: z = {zp:+.1f}\n  ")
    if top > nmax:
        sys.stderr.write("above the shuffled null -- NOT yet a signal, see below\n")
    else:
        sys.stderr.write("NO SIGNAL: the best extraction does not beat the "
                         "shuffled null, so every extraction is consistent "
                         "with a reordering of the article's letters and none "
                         "contains hidden English\n")

    sys.stderr.write("""
  CAUTION -- this null is not sufficient on its own.
  Shuffling an extraction's letters controls for letter FREQUENCY but not for
  the EXTRACTION OPERATION, and some operations inflate the trigram score by
  themselves. Measured here: mirror-then-take-every-2nd-letter of this article
  scores z=+5.49, which looks like signal against the shuffled null (max
  +4.06) -- but running the SAME operation on word-shuffled copies of the
  article, where no hidden message can exist by construction, gives mean +4.63
  and max +7.45. So +5.49 is unremarkable and the apparent signal is an
  artifact of the operation.

  Before believing any high z here, re-run that extraction's own operation on
  word-shuffled copies of the source and compare against THAT distribution.
  A real hidden message looks like the prose control (z ~ +70), not like +5.
""")


if __name__ == "__main__":
    main()
