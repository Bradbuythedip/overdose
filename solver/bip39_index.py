#!/usr/bin/env python3
"""
The article's numbers as indices into the BIP-39 WORDLIST itself.

THE OBSERVATION
The BIP-39 English wordlist has exactly 2048 entries. Extract the numerals from
the article in printed order and a striking number of them fall natively in
range:

    2008  1971  2011  2017  1969  42  40  51  85  95  10  6  2  1

Those are years, percentages and counts in the prose -- and every one of them
is also a legal index into a 2048-word list. A puzzle author who wanted a
mnemonic recoverable from printed text, without printing the words, would do
exactly this.

WHY IT IS WORTH RUNNING EVEN THOUGH INDEX CIPHERS USUALLY FAIL
BIP-39 carries a checksum: the last word encodes 4 bits of entropy hash for a
12-word phrase, 8 bits for 24. So a wrong reading fails with probability 15/16
or 255/256. That makes this SELF-CERTIFYING -- no address, no balance, no
network, and therefore immune to the oracle blindness that makes every "0
funded hits" here ambiguous.

  python3 bip39_index.py --selftest
  python3 bip39_index.py
"""
import argparse, hashlib, itertools, re, sys

try:
    from mnemonic import Mnemonic
except ImportError:
    sys.exit("needs: pip install mnemonic")

MNE = Mnemonic("english")
WL = MNE.wordlist
assert len(WL) == 2048


def numerals(path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    body = "\n".join(l for l in raw.splitlines()
                     if not l.startswith("#") and not l.startswith("==="))
    words_out = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "forty": 40}
    out = []
    for m in re.finditer(r"\d[\d,]*|\b(" + "|".join(words_out) + r")\b",
                         body, re.I):
        t = m.group(0)
        out.append(words_out[t.lower()] if t.isalpha()
                   else int(t.replace(",", "")))
    return out


def to_words(seq, base=0, mod=True):
    """Indices -> wordlist entries. base=1 means the text is 1-indexed."""
    out = []
    for n in seq:
        i = n - base
        if mod:
            i %= 2048
        elif not (0 <= i < 2048):
            return None
        out.append(WL[i])
    return out


def windows(words, sizes=(12, 15, 18, 21, 24)):
    for k in sizes:
        for i in range(0, max(0, len(words) - k + 1)):
            yield i, k, words[i:i + k]


def check(ws):
    try:
        return MNE.check(" ".join(ws))
    except Exception:
        return False


def variants(nums):
    """Named orderings and transforms of the numeral sequence."""
    yield "raw", nums
    yield "reversed", nums[::-1]
    yield "in_range_only", [n for n in nums if n < 2048]
    yield "in_range_rev", [n for n in nums if n < 2048][::-1]
    yield "mod2048", [n % 2048 for n in nums]
    yield "digitsum", [sum(int(d) for d in str(n)) for n in nums]
    yield "cumulative", list(itertools.accumulate(nums))
    yield "diffs", [abs(b - a) for a, b in zip(nums, nums[1:])]
    yield "sorted", sorted(nums)
    yield "unique", list(dict.fromkeys(nums))
    yield "unique_rev", list(dict.fromkeys(nums))[::-1]
    # years only -- the striking subset
    yield "years", [n for n in nums if 1900 <= n <= 2048]
    yield "years_rev", [n for n in nums if 1900 <= n <= 2048][::-1]
    # each number's digits as separate indices
    yield "digits", [int(d) for n in nums for d in str(n)]


def expected_by_chance(size_counts):
    """How many checksum-valid mnemonics this many windows yields from NOISE.

    THIS IS THE POINT OF THE FUNCTION. BIP-39 spends k*11/33 bits on the
    checksum, so a 12-word window passes 1 time in 16 BY ACCIDENT. Test 1,477
    windows and roughly 49 of them validate whatever you feed in. Reporting
    "63 checksum-valid mnemonics!" without this number is how a null becomes a
    headline -- and the first run of this file did exactly that before the
    expectation was computed.

    A result only means something if observed materially exceeds expected.
    """
    exp = 0.0
    for k, c in size_counts.items():
        exp += c * 2.0 ** -(k * 11 // 33)
    return exp


def selftest():
    ok = True
    ok &= len(WL) == 2048
    sys.stderr.write(f"  BIP-39 english wordlist: {len(WL)} words "
                     f"{'OK' if len(WL)==2048 else 'FAIL'}\n")
    # the canonical vector: entropy 0 -> all 'abandon' + 'about'
    m = MNE.to_mnemonic(b"\x00" * 16)
    ok &= m == "abandon " * 11 + "about"
    sys.stderr.write(f"  zero entropy -> {m[:28]}…: "
                     f"{'OK' if m.startswith('abandon abandon') else 'FAIL'}\n")
    ok &= check(m.split()) and not check((m[:-5] + "zoo").split())
    sys.stderr.write(f"  checksum accepts the valid phrase and rejects a "
                     f"broken one: {'OK' if check(m.split()) else 'FAIL'}\n")
    # index mapping must be exact
    ok &= WL[0] == "abandon" and WL[2047] == "zoo"
    sys.stderr.write(f"  WL[0]={WL[0]!r} WL[2047]={WL[2047]!r}: "
                     f"{'OK' if WL[0]=='abandon' and WL[2047]=='zoo' else 'FAIL'}\n")
    # a PLANTED sequence must be recovered, or a null here means nothing
    target = MNE.to_mnemonic(bytes(range(16)))
    idx = [WL.index(w) for w in target.split()]
    got = to_words(idx, base=0, mod=True)
    ok &= got == target.split() and check(got)
    sys.stderr.write(f"  a planted 12-word mnemonic round-trips through the "
                     f"index mapping: {'OK' if got == target.split() else 'FAIL'}\n")

    nums = numerals()
    inr = [n for n in nums if n < 2048]
    sys.stderr.write(f"  {len(nums)} numerals in the article, {len(inr)} "
                     f"natively in 0..2047\n")
    sys.stderr.write(f"    {nums}\n")
    # the null must be computed, not assumed. 483 twelve-word windows alone
    # yield ~30 valid mnemonics from noise.
    e = expected_by_chance({12: 483, 15: 384, 18: 285, 21: 198, 24: 127})
    good = 48 < e < 50
    ok &= good
    sys.stderr.write(f"  null expectation for the real window census: "
                     f"{e:.1f} valid mnemonics from NOISE "
                     f"{'OK' if good else 'FAIL'}\n")
    ok &= abs(expected_by_chance({12: 16}) - 1.0) < 1e-9
    sys.stderr.write(f"  16 twelve-word windows -> exactly 1.0 expected: "
                     f"{'OK' if abs(expected_by_chance({12:16})-1.0)<1e-9 else 'FAIL'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="bip39_index_candidates.txt")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the wordlist mapping or checksum is wrong; refusing")
    if a.selftest:
        return

    import collections
    nums = numerals()
    hits, tried, phrases = [], 0, set()
    size_counts = collections.Counter()
    by_variant = collections.Counter()
    for vname, seq in variants(nums):
        if not seq:
            continue
        for base in (0, 1):
            for mod in (True, False):
                ws = to_words(seq, base, mod)
                if not ws:
                    continue
                for i, k, w in windows(ws):
                    tried += 1
                    size_counts[k] += 1
                    phrases.add(" ".join(w))
                    if check(w):
                        by_variant[vname] += 1
                        hits.append((vname, base, mod, i, k, " ".join(w)))
                        sys.stderr.write(
                            f"\n  *** CHECKSUM-VALID BIP-39 MNEMONIC\n"
                            f"      {' '.join(w)}\n"
                            f"      from {vname}, base={base}, mod={mod}, "
                            f"window {i}..{i+k}\n")
                        sys.stderr.flush()

    exp = expected_by_chance(size_counts)
    sys.stderr.write(f"\n  {tried:,} windows tested, {len(hits)} "
                     f"checksum-valid mnemonic(s)\n")
    sys.stderr.write(f"  EXPECTED BY CHANCE: {exp:.1f}   "
                     f"observed/expected = {len(hits)/max(exp,1e-9):.2f}\n")
    if hits:
        sys.stderr.write(f"  by variant: {dict(by_variant)}\n")
    if len(hits) < exp * 2:
        sys.stderr.write(
            "\n  NOT A SIGNAL. BIP-39 spends 1 bit in 33 on the checksum, so a\n"
            "  12-word window validates 1 time in 16 from pure noise. This many\n"
            "  valid mnemonics is what the window count buys for free.\n")
        meaningful = [h for h in hits
                      if h[0] in ("raw", "reversed", "years", "years_rev",
                                  "in_range_only", "in_range_rev", "unique")]
        sys.stderr.write(
            f"  Variants that would have MEANT something "
            f"(raw / years / in-range): {len(meaningful)}\n")
    else:
        sys.stderr.write(
            f"\n  {len(hits)} against {exp:.1f} expected is a real excess. "
            f"Examine by variant.\n")
    with open(a.out, "w", encoding="utf-8") as fh:
        for p in sorted(phrases):
            fh.write(p + "\n")
    sys.stderr.write(f"  {len(phrases):,} phrases -> {a.out}\n")
    if not hits:
        sys.stderr.write(
            "  No ordering of the article's numerals maps onto a "
            "checksum-valid\n  BIP-39 mnemonic through the wordlist index.\n")


if __name__ == "__main__":
    main()
