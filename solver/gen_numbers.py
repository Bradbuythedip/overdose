#!/usr/bin/env python3
"""
The printed-numbers trail, enumerated exhaustively instead of by hand.

THE INVENTORY, CONFIRMED INDEPENDENTLY
21 numbers are printed in the body of pages 75-79. Extracted from this repo's
pixel-verified transcript they are, in print order:

  2008 1 1 1 1971 10 1 2011 1 42 20000 100000 2017 12000 51 85 2 51 95 1969 10

which matches a separate agent's inventory exactly, including the three "Layer
1" ones. So the input is not in doubt; only what to do with it is.

WHY THIS DOES NOT FILTER ON A BIP-39 CHECKSUM
A hand-run of this trail reported three checksum passes from about 45 trials
and correctly called it chance: a 12-word BIP-39 checksum is 4 bits, so 1 in 16
of ANY word list passes, and 45/16 is about 3. A checksum cannot be used as
evidence at these trial counts — and worse, filtering on it throws away 15 of
every 16 candidates for no reason, including the right one if its convention
differs by an off-by-one.

The chain is the filter that works. Screening a derived address against
56,795,328 funded scriptPubKeys is a ~2^-160 test per address, so there is no
base-rate problem and no need to pre-filter at all. Every candidate is derived
whether or not its checksum passes.

Each emitted phrase is expanded downstream by full_sweep.py into 7 direct key
hashes plus 5 seed derivations (BIP-39 PBKDF2 among them) across ~72 HD paths,
so a word list is tried both as a mnemonic and as a passphrase.

WHAT IS ENUMERATED
  subsets      all 21; the 18 with the Layer 1 labels dropped; per page;
               first/last 12; in-range only; years only; years dropped;
               consecutive duplicates collapsed
  orderings    print order, reversed (mirror writing is a stated clue),
               ascending, descending
  conventions  nine ways to turn a number into a 0..2047 word index, each in
               0-based and 1-based form, including the last-3-digits reading
               that the hand-run used
  windows      every 12/15/18/21/24-word window of each resulting sequence
  renderings   the numbers as text in a dozen separator and formatting styles
  entropy      the 56-digit stream as an integer -> bytes, left- and
               right-padded to 16/24/32 bytes and hashed, which the hand-run
               declined to try on the grounds that 184 bits "should not be
               padded". That is a taste argument, not evidence, and padding
               costs nothing to test.

  python3 gen_numbers.py --selftest
  python3 gen_numbers.py --out /tmp/numbers.txt
"""
import argparse, hashlib, itertools, re, sys

from mnemonic import Mnemonic

WORDS = Mnemonic("english").wordlist
assert len(WORDS) == 2048

# (value, page, line, is_layer1_label)
NUMBERS = [
    (2008, 75, 3, False), (1, 75, 18, True), (1, 75, 19, True),
    (1, 75, 28, True), (1971, 76, 7, False), (10, 76, 8, False),
    (1, 76, 9, False), (2011, 76, 9, False), (1, 76, 24, False),
    (42, 77, 1, False), (20000, 77, 3, False), (100000, 77, 4, False),
    (2017, 77, 10, False), (12000, 77, 19, False), (51, 77, 24, False),
    (85, 78, 12, False), (2, 78, 14, False), (51, 79, 6, False),
    (95, 79, 7, False), (1969, 79, 19, False), (10, 79, 22, False),
]


# Page 72, the "NUMBERS" department page FACING the column opener. Not part of
# OVERDOSE — it has its own footer and its own sources — but the column's
# orange highlight reads "The numbers don't lie", and the facing section is
# literally called NUMBERS. That is a cheap thing to test and an expensive
# thing to assume, so it is swept separately and labelled speculative rather
# than merged into the column's own inventory.
P72 = [165, 572, 2020, 48, 93044, 2026, 39, 358, 2026, 145, 2019]
P72_LABELLED = [(v, 72, 0, False) for v in P72]


def extract(path="article_transcript.txt"):
    """Re-read the numbers from the transcript so the table above is checked."""
    raw = open(path, encoding="utf-8").read()
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    out = []
    for num, body in zip(it, it):
        for i, l in enumerate([x for x in body.splitlines() if x.strip()], 1):
            for m in re.finditer(r"\d[\d,]*", l):
                out.append((int(m.group(0).replace(",", "")), int(num), i))
    return out


CONVENTIONS = {
    "mod2048":   lambda v: v % 2048,
    "last3":     lambda v: (v % 1000) % 2048,
    "last2":     lambda v: (v % 100) % 2048,
    "clamp":     lambda v: v if v < 2048 else v % 2048,
    "digitsum":  lambda v: sum(int(c) for c in str(v)) % 2048,
    "revdigits": lambda v: int(str(v)[::-1]) % 2048,
    "mod1626":   lambda v: v % 1626,          # arbitrary-modulus control
    "sqmod":     lambda v: (v * v) % 2048,
    "sumdig3":   lambda v: (v % 1000 + sum(int(c) for c in str(v))) % 2048,
}


def subsets(nums):
    """Named subsets of the number list, each still in print order."""
    vals = [n[0] for n in nums]
    out = {
        "all21": vals,
        "drop_layer1": [n[0] for n in nums if not n[3]],
        "first12": vals[:12], "last12": vals[-12:],
        "inrange": [v for v in vals if v < 2048],
        "years": [v for v in vals if 1900 <= v <= 2030],
        "noyears": [v for v in vals if not (1900 <= v <= 2030)],
        "nonone": [v for v in vals if v != 1],
    }
    coll = []
    for v in vals:
        if not coll or coll[-1] != v:
            coll.append(v)
    out["collapsed"] = coll
    for p in sorted({n[1] for n in nums}):
        out[f"p{p}"] = [n[0] for n in nums if n[1] == p]
    return out


def orderings(seq):
    return {"fwd": list(seq), "rev": list(seq)[::-1],
            "asc": sorted(seq), "desc": sorted(seq, reverse=True)}


def article_words(path="article_transcript.txt"):
    """The article's body words, whole-article and per page."""
    raw = open(path, encoding="utf-8").read()
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    allw, per = [], {}
    for num, body in zip(it, it):
        w = re.findall(r"[A-Za-z']+", body)
        per[int(num)] = w
        allw.extend(w)
    return allw, per


def index_readings(seq, allw, per):
    """Numbers used as POSITIONS into the text rather than as values.

    A hand-run of this trail indexed the numbers into the Genesis coinbase and
    into the column CHARACTER by character. Word-level indexing is the more
    natural reading of "the numbers don't lie" pointing at a text, and it was
    not tried. Both 0- and 1-based, wrapped modulo the corpus length, and
    mirrored — mirror writing is a stated clue.
    """
    out = set()
    corpora = [("all", allw)] + [(f"p{p}", w) for p, w in sorted(per.items())]
    for _, words in corpora:
        if len(words) < 2:
            continue
        for base in (0, 1):
            for rev in (False, True):
                src = words[::-1] if rev else words
                sel = [src[(v - base) % len(src)] for v in seq]
                out.add(" ".join(sel))
                out.add(" ".join(sel).lower())
                out.add("".join(w[0] for w in sel).lower())
    return out


def renderings(seq):
    """The numbers as text, in the styles a person would actually type."""
    s = [str(v) for v in seq]
    out = [" ".join(s), ",".join(s), "-".join(s), "".join(s), "\n".join(s),
           ", ".join(s), " ".join(f"{v:,}" for v in seq)]
    out.append("".join(s)[::-1])
    return out


def entropy_phrases(seq):
    """The digit stream as key material, including the padded forms."""
    digits = "".join(str(v) for v in seq)
    out = set()
    try:
        n = int(digits)
    except ValueError:
        return out
    raw = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    for size in (16, 24, 32):
        out.add(raw.rjust(size, b"\0").hex())
        out.add(raw.ljust(size, b"\0").hex())
        out.add(raw[:size].rjust(size, b"\0").hex())
    out.add(hashlib.sha256(digits.encode()).hexdigest())
    out.add(hashlib.sha256(raw).hexdigest())
    # the same 32-byte forms read as BIP-39 entropy -> a real 24-word mnemonic
    m = Mnemonic("english")
    for h in list(out):
        try:
            b = bytes.fromhex(h)
        except ValueError:
            continue
        if len(b) in (16, 24, 32):
            out.add(m.to_mnemonic(b))
    return out


def selftest():
    """The hardcoded inventory must match the transcript, and a known
    mnemonic must round-trip through the index conventions."""
    got = [(v, p, l) for v, p, l in extract()]
    want = [(v, p, l) for v, p, l, _ in NUMBERS]
    ok = got == want
    sys.stderr.write(f"  transcript has {len(got)} numbers, table has "
                     f"{len(want)}: {'MATCH' if ok else 'MISMATCH'}\n")
    if not ok:
        sys.stderr.write(f"    transcript {got[:6]}\n    table      {want[:6]}\n")

    # A word index convention must actually produce the intended words.
    idx = [CONVENTIONS["last3"](v) for v in (2008, 1971, 12000)]
    ws = [WORDS[i] for i in idx]
    sys.stderr.write(f"  last3 of 2008/1971/12000 -> {idx} -> {ws}\n")
    ok2 = idx == [8, 971, 0] and ws[0] == WORDS[8]
    sys.stderr.write(f"  index convention arithmetic: {'OK' if ok2 else 'FAIL'}\n")

    # Padding must produce a decodable 32-byte value, not a truncated one.
    ph = entropy_phrases([2008, 1971])
    hexes = [p for p in ph if len(p) == 64 and re.fullmatch(r"[0-9a-f]+", p)]
    ok3 = len(hexes) >= 2
    sys.stderr.write(f"  entropy padding produced {len(hexes)} distinct "
                     f"32-byte hex forms: {'OK' if ok3 else 'FAIL'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok and ok2 and ok3 else "FAIL\n"))
    return ok and ok2 and ok3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/numbers.txt")
    ap.add_argument("--set", choices=("column", "p72"), default="column")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("inventory or convention arithmetic is wrong; refusing")
    if a.selftest:
        return

    out = set()
    SRC = NUMBERS if a.set == "column" else P72_LABELLED
    subs = subsets(SRC)
    # Contiguous windows of the NUMBER list itself. The hand-run tried a few
    # cuts by eye ("drop the three Layer 1 labels"); every contiguous run of a
    # mnemonic-legal length is cheap to enumerate and removes the guesswork.
    base_vals = [n[0] for n in SRC]
    nolayer = [n[0] for n in SRC if not n[3]]
    for tag, src in (("win21", base_vals), ("win18", nolayer)):
        for L in (12, 15, 18, 21):
            for st in range(0, max(len(src) - L + 1, 0)):
                subs[f"{tag}_{L}_{st}"] = src[st:st + L]

    allw, per = article_words()
    sys.stderr.write(f"  article corpus: {len(allw)} words, "
                     f"{len(per)} pages\n")

    for sname, vals in subs.items():
        if not vals:
            continue
        for oname, seq in orderings(vals).items():
            for r in renderings(seq):
                out.add(r)
            out |= entropy_phrases(seq)
            out |= index_readings(seq, allw, per)
            for cname, fn in CONVENTIONS.items():
                for base in (0, 1):
                    idx = [(fn(v) - base) % 2048 for v in seq]
                    words = [WORDS[i] for i in idx]
                    out.add(" ".join(words))
                    for L in (12, 15, 18, 21, 24):
                        if len(words) < L:
                            continue
                        for st in range(len(words) - L + 1):
                            out.add(" ".join(words[st:st + L]))
                    # short lists padded up to 12 with the BIP-39 zero word,
                    # which is what the hand-run's "zoo zoo" kludge amounted to
                    if len(words) < 12:
                        out.add(" ".join(words + [WORDS[0]] * (12 - len(words))))
                        out.add(" ".join([WORDS[0]] * (12 - len(words)) + words))

    out.discard("")
    with open(a.out, "w", encoding="utf-8") as fh:
        for s in sorted(out):
            fh.write(s.replace("\n", " ") + "\n")
    sys.stderr.write(f"\n  {len(out)} candidate phrases -> {a.out}\n")
    sys.stderr.write(f"  (no checksum filter applied — every candidate is "
                     f"derived and screened against the chain)\n")


if __name__ == "__main__":
    main()
