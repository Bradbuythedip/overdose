#!/usr/bin/env python3
"""
Apply the mirror-writing transforms to an ARBITRARY phrase corpus.

gen_mirror.py hardcodes its input (the highlighted-phrase catalogue), so the
mirror transforms have only ever been applied to highlighted phrases -- never
to the article's running body text, which was itself missing from the corpus
until now. Mirror writing is the one explicit clue Keiser gave
(x.com/maxkeiser/status/1632391507008278528, 5 Mar 2023, quoting the Della
Sala & Cubelli mirror-writing paper), so the body text deserves it too.

Reuses gen_mirror's primitives rather than reimplementing them, so both paths
stay consistent.

Transforms (the four with a real claim to "mirror", x3 cases each):
  M1  full character reversal          -- Leonardo-style right-to-left
  M2  word-order reversal              -- line read backwards
  M7  each word reversed in place      -- word-local mirroring
  M4  atbash                           -- the classical "mirror" substitution

  python3 mirror_transform.py --in /tmp/transcript_phrases.txt \
                              --out /tmp/transcript_mirror.txt
"""
import argparse, re, sys

from gen_mirror import atbash, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-len", type=int, default=200)
    a = ap.parse_args()

    out = set()

    def add(s):
        if s and 3 <= len(s) <= a.max_len:
            out.add(s)

    n = 0
    for line in open(a.inp, encoding="utf-8", errors="replace"):
        s = line.rstrip("\n")
        if not s.strip():
            continue
        n += 1
        for t in (s[::-1],                                   # M1
                  " ".join(reversed(words(s))),              # M2
                  " ".join(w[::-1] for w in words(s)),       # M7
                  atbash(s)):                                # M4
            add(t)
            add(t.lower())
            add(t.upper())

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")
    sys.stderr.write(f"{n:,} input phrases -> {len(out):,} mirror variants "
                     f"-> {a.out}\n")


if __name__ == "__main__":
    main()
