#!/usr/bin/env python3
"""
The highlight sequence as a BINARY channel, decoded rather than concatenated.

WHY (and why this file exists)
The dissect:highlights agent in the strange-loop workflow returned without
writing its candidate file, so this covers its job directly rather than leave
a silent gap in the record.

STATUS.md already rules out the highlight spans as PHRASES: concatenations,
acrostics, first/last-word null ciphers, per colour and per page, 0 hits. What
it does not cover is the spans as a BIT SEQUENCE. The column uses exactly two
highlight devices -- an orange bar and a knocked-out bar (white on the dark
page 77, black elsewhere) -- which is a binary alphabet over 38 ordered
symbols, and a two-symbol alphabet over an ordered sequence is precisely the
shape of a Baconian cipher.

38 is not a multiple of 5, so a clean Bacon read needs either an offset, a
grouping choice, or extra symbols. The three marks found in marks_ordered.tsv
(two underlines, one strikethrough) fold in at their page positions to make
41; dropping or grouping differently gives 35 or 40. All of these are tried.

WHAT IS MEASURED, NOT ASSUMED
Every decode is scored for English with the project's own null model
(englishness.zscore: a string is scored against random permutations of its own
letters, which controls for letter frequency exactly). Real English sits near
z >= +8; order-free strings sit at z ~ 0. A decode is only worth deriving keys
from if it reads as language, and the report says plainly whether any does.

  python3 wf/highlight_bits.py --selftest
  python3 wf/highlight_bits.py
"""
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import englishness as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Bacon's 24-letter alphabet (I=J, U=V) and the modern 26-letter variant
BACON24 = "ABCDEFGHIKLMNOPQRSTUWXYZ"
BACON26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def load_highlights():
    fn = os.path.join(ROOT, "highlights_ordered.tsv")
    out = []
    for line in open(fn, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            out.append((int(p[0]), p[1], p[2]))
    return out


def load_marks():
    fn = os.path.join(ROOT, "marks_ordered.tsv")
    out = []
    if not os.path.exists(fn):
        return out
    for line in open(fn, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 7:
            out.append((int(p[0]), p[1], p[6]))
    return out


def bits_from(seq, orange_is_one=True):
    """orange -> one class, every knocked-out bar (black or white) -> other."""
    b = []
    for _, colour, _ in seq:
        is_orange = colour.strip().lower() == "orange"
        v = 1 if is_orange else 0
        b.append(v if orange_is_one else 1 - v)
    return b


def bacon(bits, alphabet, offset=0):
    b = bits[offset:]
    out = []
    for i in range(0, len(b) - 4, 5):
        v = 0
        for x in b[i:i + 5]:
            v = v * 2 + x
        out.append(alphabet[v] if v < len(alphabet) else "?")
    return "".join(out)


def variants():
    """(label, bit list) for every defensible reading of the sequence."""
    hl = load_highlights()
    mk = load_marks()
    out = []
    for pol in (True, False):
        tag = "orange=1" if pol else "orange=0"
        out.append((f"highlights[{tag}]", bits_from(hl, pol)))
        if mk:
            # fold the underlines/strikethrough in at their page positions,
            # marks treated as the same class as the knocked-out bars and,
            # separately, as the orange class
            for mval, mtag in ((0, "marks=0"), (1, "marks=1")):
                merged = []
                bits = bits_from(hl, pol)
                for i, (pg, _, _) in enumerate(hl):
                    merged.append(bits[i])
                    for mpg, _, _ in mk:
                        if mpg == pg and i == max(
                                j for j, (p2, _, _) in enumerate(hl) if p2 == pg):
                            merged.append(mval)
                out.append((f"highlights+marks[{tag},{mtag}]", merged))
    return out


def report():
    rng = random.Random(12345)
    body = open(os.path.join(ROOT, "article_transcript.txt"),
                encoding="utf-8").read()
    pos = E.zscore(E.letters(body[:1200]), 200, rng)
    neg_src = list(E.letters(body[:1200]))
    rng.shuffle(neg_src)
    neg = E.zscore("".join(neg_src), 200, rng)  # already letters()
    print(f"controls: English prose z={pos[0]:+.2f}   shuffled prose z={neg[0]:+.2f}")
    print()
    best = []
    for label, bits in variants():
        for alpha, aname in ((BACON24, "bacon24"), (BACON26, "bacon26")):
            for off in range(5):
                txt = bacon(bits, alpha, off)
                if len(txt) < 4:
                    continue
                z = E.zscore(E.letters(txt), 200, rng)[0]
                best.append((z, f"{label} {aname} off={off}", txt))
    best.sort(reverse=True)
    print(f"{len(best)} decodes, ranked by englishness z:")
    for z, lab, txt in best[:12]:
        print(f"  z={z:+6.2f}  {lab:44s} {txt}")
    print()
    top = best[0][0] if best else 0.0
    print(f"highest decode z = {top:+.2f}; English control z = {pos[0]:+.2f}")
    if top < pos[0] / 2:
        print("VERDICT: no decode reads as English. The highlight/mark binary "
              "sequence does not carry a Baconian plaintext.")
    else:
        print("VERDICT: a decode scores near the English control -- inspect it.")
    return best


def selftest():
    ok = True
    hl = load_highlights()
    good = len(hl) == 38
    print(f"  38 highlight spans: {'OK' if good else 'FAIL'} ({len(hl)})")
    ok &= good
    mk = load_marks()
    good = len(mk) == 3
    print(f"  3 marks: {'OK' if good else 'FAIL'} ({len(mk)})")
    ok &= good
    b = bits_from(hl)
    good = set(b) == {0, 1} and len(b) == 38
    print(f"  binary over 38 symbols: {'OK' if good else 'FAIL'}")
    ok &= good
    # positive control: Bacon must round-trip a planted word
    word = "BACON"
    planted = []
    for ch in word:
        v = BACON24.index(ch)
        planted += [int(x) for x in format(v, "05b")]
    good = bacon(planted, BACON24) == word
    print(f"  bacon decodes a planted word: {'OK' if good else 'FAIL'} "
          f"({bacon(planted, BACON24)})")
    ok &= good
    rng = random.Random(1)
    # englishness.zscore scores the RAW string against its own shuffles, and
    # its trigram table is lowercase -- so the caller must normalise first.
    z_eng = E.zscore(E.letters("the quick brown fox jumps over the lazy dog "
                               "and then the other cat sat on the mat"),
                     200, rng)[0]
    good = z_eng > 2
    print(f"  englishness separates real English: {'OK' if good else 'FAIL'} "
          f"(z={z_eng:+.2f})")
    ok &= good
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed")
    print()
    report()
