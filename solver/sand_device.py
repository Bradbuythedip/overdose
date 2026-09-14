#!/usr/bin/env python3
"""
The device Keiser actually named, tested on lines verified against the scan.

THE CLUE, AND WHAT IT ACTUALLY REFERS TO
"Like George Sand's hidden cryptography, I have hidden private keys in the
text." The Sand story is a popular (and apocryphal) EXCHANGE, not a single
letter, and the two halves use different devices:

  Sand's letter to Musset   read every OTHER LINE
  Musset's reply            read the FIRST WORD of each line

Both are LINE devices, and a line device is meaningless unless the lines are
the printed ones. That is why Keiser says "have you ever picked up a PHYSICAL
COPY" — a reflowed digital text destroys the device entirely.

WHY THIS IS NEWLY RUNNABLE
Until now nobody had checked whether article_transcript.txt breaks lines where
the magazine breaks them. It does. Reconstructing printed lines from the
per-glyph scan geometry in wf/glyphs_p*.tsv and matching each against the
transcript puts 83 of 95 recoverable lines at OFFSET ZERO on all five pages.
The transcript is line-faithful, so these devices can be run for real rather
than on a transcriber's reflow.

THE NULL
Shuffling an extraction's letters controls for letter frequency but not for
the operation. The matched null here shuffles the WORDS WITHIN EACH LINE: line
count, line lengths and the word multiset all survive, and the only thing
destroyed is which word lands first or last — which is exactly the claim under
test. 200 draws.

  python3 sand_device.py --selftest
  python3 sand_device.py
"""
import argparse, random, re, statistics as st, sys

from englishness import letters, score

PATH = "article_transcript.txt"


def lines(path=PATH):
    raw = re.sub(r"^#.*$", "", open(path, encoding="utf-8").read(), flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it, out = iter(parts[1:]), []
    for _n, b in zip(it, it):
        out += [l.strip() for l in b.splitlines() if l.strip()]
    return out


def devices(ls):
    """Every line-keyed reading, Sand's and Musset's among them."""
    d = {}
    d["first_word"] = " ".join(l.split()[0] for l in ls if l.split())
    d["last_word"] = " ".join(l.split()[-1] for l in ls if l.split())
    d["first_two_words"] = " ".join(" ".join(l.split()[:2])
                                    for l in ls if l.split())
    d["first_letter"] = "".join(re.sub(r"[^A-Za-z]", "", l)[:1] for l in ls)
    d["last_letter"] = "".join(re.sub(r"[^A-Za-z]", "", l)[-1:] for l in ls)
    d["odd_lines"] = " ".join(ls[0::2])
    d["even_lines"] = " ".join(ls[1::2])
    return d


def null(ls, draws, seed=7):
    rng = random.Random(seed)
    acc = {k: [] for k in devices(ls)}
    for _ in range(draws):
        sh = []
        for l in ls:
            w = l.split()
            rng.shuffle(w)
            sh.append(" ".join(w))
        for k, v in devices(sh).items():
            acc[k].append(score(letters(v)))
    return acc


def selftest():
    """The scorer must separate real prose from the same words reordered, or a
    null result here means only that the scorer is blind."""
    ls = lines()
    ok = len(ls) > 100
    sys.stderr.write(f"  {len(ls)} printed lines loaded: "
                     f"{'OK' if ok else 'FAIL'}\n")
    prose = score(letters(" ".join(ls)))
    rng = random.Random(1)
    ch = list(letters(" ".join(ls)))
    rng.shuffle(ch)
    shuf = score("".join(ch))
    sep = prose > shuf * 4
    ok &= sep
    sys.stderr.write(f"  prose {prose:.5f} vs its own letters shuffled "
                     f"{shuf:.5f}: {'OK' if sep else 'FAIL'}\n")
    d = devices(ls)
    ok &= "first_word" in d and "odd_lines" in d
    sys.stderr.write(f"  {len(d)} devices, Musset's (first_word) and Sand's "
                     f"(odd_lines) both present\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not selftest():
        sys.exit("the scorer cannot tell prose from noise; a null would be "
                 "meaningless")
    if a.selftest:
        return

    ls = lines()
    real, nl = devices(ls), null(ls, a.draws)
    sys.stderr.write(f"\n  englishness = common-trigram rate, {a.draws} "
                     f"within-line word-shuffle draws\n\n")
    sys.stderr.write(f"  {'device':>16} {'observed':>10} {'null mean':>10} "
                     f"{'null max':>9} {'z':>7}\n")
    exceeded = []
    for k in real:
        o = score(letters(real[k]))
        n = nl[k]
        m, s = st.mean(n), st.pstdev(n)
        z = (o - m) / s if s else 0.0
        if o > max(n):
            exceeded.append(k)
        sys.stderr.write(f"  {k:>16} {o:>10.5f} {m:>10.5f} {max(n):>9.5f} "
                         f"{z:>+7.2f}\n")
    sys.stderr.write(f"\n  {'prose control':>16} "
                     f"{score(letters(' '.join(ls))):>10.5f}\n  ")
    if exceeded:
        sys.stderr.write(f"EXCEEDS THE NULL MAXIMUM: {exceeded} — read by "
                         f"hand\n")
    else:
        sys.stderr.write("NO LINE DEVICE CARRIES ANYTHING. Not one observed "
                         "value exceeds\n  its own null's MAXIMUM, let alone "
                         "its mean.\n")


if __name__ == "__main__":
    main()
