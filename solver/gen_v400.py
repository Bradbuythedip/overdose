#!/usr/bin/env python3
"""
Passphrase corpus from the 400 dpi vision readings.

The isolated-bold reading is the one a NULL cipher would use: 39 words that
are emphasised inside running text, as against the six display passages set
bold wholesale. Those 39 are the closest thing this article has to a
deliberately marked word list, and they have never been swept, because until
the lossless scan no reading of them was trustworthy.

Generated per reading (isolated bold, first-of-run, all bold, bar text) and
per page as well as whole-article, since the payload could be page-scoped:

  the phrase itself, in eight casing/joining conventions
  the initials of its words, both cases
  every contiguous window of 3..12 words
  the words reversed, and the letters mirrored — "mirror writing" is a
    stated clue, so every reading gets its mirror

  python3 gen_v400.py --selftest
  python3 gen_v400.py --out /tmp/v400_phrases.txt
"""
import argparse, itertools, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vision400_readings import load, runs, WORD


def casings(ws):
    """Eight ways the same word list is conventionally written."""
    lo = [w.lower() for w in ws]
    out = [" ".join(ws), " ".join(lo), " ".join(w.capitalize() for w in lo),
           " ".join(lo).upper(), "".join(lo), "".join(w.capitalize() for w in lo),
           "-".join(lo), "_".join(lo)]
    return out


def strip(w):
    m = WORD.findall(w)
    return m[0] if m else ""


def expand(ws, tag, out):
    ws = [strip(w) for w in ws]
    ws = [w for w in ws if w]
    if not ws:
        return
    for s in casings(ws):
        out.add(s)
    ini = "".join(w[0] for w in ws)
    out.add(ini)
    out.add(ini.lower())
    out.add(ini.upper())
    # mirror: a stated clue, applied to every reading rather than guessed at.
    # Both cases — a reversal emitted only in the source's own capitalisation
    # would miss the lowercase form of any capitalised phrase.
    for s in casings(ws[::-1]):
        out.add(s)
    out.add(" ".join(ws).lower()[::-1])
    out.add(ini[::-1])
    out.add(ini.lower()[::-1])
    for n in range(3, 13):
        for i in range(len(ws) - n + 1):
            out.add(" ".join(ws[i:i + n]).lower())
            out.add("".join(ws[i:i + n]).lower())


def selftest():
    """Expansion must produce the exact conventional forms, not near-misses."""
    out = set()
    expand(["Nayib", "Bukele"], "t", out)
    want = {"nayib bukele", "Nayib Bukele", "NAYIB BUKELE", "nayibbukele",
            "NayibBukele", "nayib-bukele", "nayib_bukele", "NB", "nb",
            "bukele nayib"}
    miss = want - out
    for w in sorted(want):
        sys.stderr.write(f"    {'ok ' if w in out else 'MISS'} {w!r}\n")
    sys.stderr.write(f"  {len(out)} forms from a 2-word reading\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if not miss else "FAIL\n"))
    return not miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="scan400/bold_vision_400.json")
    ap.add_argument("--out", default="/tmp/v400_phrases.txt")
    ap.add_argument("--isolated", type=int, default=6)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("generator does not produce the forms it claims")
    if a.selftest:
        return

    rows = list(load(a.json))
    out = set()
    for pg in [None] + sorted({r[0] for r in rows}):
        sel = [r for r in rows if pg is None or r[0] == pg]
        words = [r[2] for r in sel]
        bold = [r[3] for r in sel]
        bar = [r[4] for r in sel]
        _, own = runs(bold)
        readings = {
            "iso": [w for w, b, o in zip(words, bold, own)
                    if b and o <= a.isolated],
            "all": [w for w, b in zip(words, bold) if b],
            "bar": [w for w, c in zip(words, bar) if c],
        }
        first, prev = [], False
        for w, b in zip(words, bold):
            if b and not prev:
                first.append(w)
            prev = b
        readings["first"] = first
        for k, ws in readings.items():
            expand(ws, f"{pg or 'all'}:{k}", out)

    out.discard("")
    with open(a.out, "w", encoding="utf-8") as fh:
        for s in sorted(out):
            fh.write(s + "\n")
    sys.stderr.write(f"\n  {len(out)} phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
