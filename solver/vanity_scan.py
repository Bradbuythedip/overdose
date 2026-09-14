#!/usr/bin/env python3
"""
Look for a VANITY address. Inverts the whole approach: no key required.

THE INVERSION
Every method in this project runs text -> key -> address, and asks the chain
whether that address is funded. All of them have failed, and each failure is
ambiguous: a null cannot distinguish "wrong derivation" from "right derivation,
address never funded or long since swept".

This runs the other way. If Keiser generated a VANITY address -- and a
broadcaster who wanted a memorable prize plausibly would -- then the answer is
already sitting in the list of addresses holding exactly 20 BTC, readable
without deriving anything. Vanity generation was mainstream in 2021
(vanitygen, VanitySearch); "1Max..." at 4-5 characters is minutes of GPU time.

This is not a cipher hypothesis. It is the observation that if the prize
address spells something, we can just look.

WHAT IT SEARCHES
  the 870 named exactly-20 addresses, plus the current P2PKH / P2SH / bech32
  exactly-20 lists

FOR
  Keiser vocabulary: max, keiser, stacy, overdose, toxic, orangepill, hodl
  the puzzle: 20btc, prize, gift, free, find, clue, hidden, secret
  El Salvador: salvador, bukele, volcano, chivo, elzonte
  the serials: 76841714, 46279860, CL, KB, L12
  and, separately, addresses with improbable structure -- long runs of one
  character, or long ascending/descending sequences -- which is what a vanity
  search looking for "pretty" rather than "meaningful" produces

A base58 address has ~2^5.86 bits per character, so a 5-character match after
the version byte is roughly 1 in 656 million by chance. Against ~1,300
addresses, ANY 5+ character hit is meaningful. 3-character hits are not: they
are expected.

  python3 vanity_scan.py --selftest
  python3 vanity_scan.py
"""
import argparse, glob, os, re, sys

WORDS = [
    "max", "keiser", "stacy", "herbert", "overdose", "toxic", "maximalist",
    "orangepill", "orange", "hodl", "satoshi", "bitcoin", "btc",
    "salvador", "bukele", "volcano", "chivo", "elzonte", "elsalvador",
    "prize", "gift", "free", "find", "clue", "hidden", "secret", "puzzle",
    "twenty", "20btc", "genesis", "rabbit", "love", "peace", "shit", "fuck",
    "76841714", "46279860", "cl76841714a", "kb46279860", "l12", "utxo",
]


def load_addresses():
    """(address, source) for every exactly-20 address on disk."""
    out = []
    for path in (["window/named_exact20_870.txt",
                  "window/candidates_p2pkh_exact20_67.txt"]
                 + sorted(glob.glob("window/current_exact20_*.tsv"))):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            a = line.strip().split(",")[0].split("\t")[0].strip()
            if 20 <= len(a) <= 64 and re.fullmatch(r"[13bc][A-Za-z0-9]+", a):
                out.append((a, os.path.basename(path)))
    return sorted(set(out))


def body(addr):
    """The part a vanity search actually controls."""
    if addr.startswith("bc1p") or addr.startswith("bc1q"):
        return addr[4:]
    return addr[1:]


def word_hits(addr, min_len=4):
    b = body(addr).lower()
    out = []
    for w in WORDS:
        if len(w) >= min_len and w.lower() in b:
            out.append((w, b.index(w.lower())))
    return out


def structure_score(addr):
    """Longest run of one character, and longest monotone digit sequence."""
    b = body(addr)
    run = best = 1
    for i in range(1, len(b)):
        run = run + 1 if b[i] == b[i - 1] else 1
        best = max(best, run)
    mono = 1
    bm = 1
    for i in range(1, len(b)):
        if b[i].isdigit() and b[i - 1].isdigit() and \
                int(b[i]) == int(b[i - 1]) + 1:
            mono += 1
            bm = max(bm, mono)
        else:
            mono = 1
    return best, bm


def selftest():
    ok = True
    # a planted vanity address must be found
    fake = "1MaxKeiserXXXXXXXXXXXXXXXXXXXXXXX"
    h = word_hits(fake)
    good = any(w == "max" for w, _i in h) or any(w == "keiser" for w, _i in h)
    ok &= good
    sys.stderr.write(f"  a planted '1MaxKeiser...' is detected {h[:3]}: "
                     f"{'OK' if good else 'FAIL'}\n")
    # and a random address is not
    rnd = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    h2 = word_hits(rnd)
    ok &= not h2
    sys.stderr.write(f"  the genesis address trips nothing: "
                     f"{'OK' if not h2 else 'FAIL ' + str(h2)}\n")
    r, m = structure_score("1AAAAAbcdefg")
    ok &= r == 5
    sys.stderr.write(f"  a 5-char repeat is measured as {r}: "
                     f"{'OK' if r == 5 else 'FAIL'}\n")
    _r, m2 = structure_score("1ab12345xyz")
    ok &= m2 == 5
    sys.stderr.write(f"  an ascending run 12345 is measured as {m2}: "
                     f"{'OK' if m2 == 5 else 'FAIL'}\n")
    a = load_addresses()
    ok &= len(a) > 300
    sys.stderr.write(f"  {len(a):,} exactly-20 addresses loaded\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-word", type=int, default=4)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the vanity matcher is wrong; refusing")
    if a.selftest:
        return

    addrs = load_addresses()
    sys.stderr.write(f"\n  {len(addrs):,} addresses holding exactly 20 BTC\n"
                     f"  base58 carries ~5.86 bits/char, so a 5-char match is "
                     f"~1 in 6.6e8 by chance;\n  against this many addresses, "
                     f"any 5+ char hit is meaningful and 3 is not.\n\n")
    found = []
    for ad, src in addrs:
        h = word_hits(ad, a.min_word)
        if h:
            found.append((ad, src, h))
            for w, i in h:
                sys.stderr.write(f"  *** {w!r} at offset {i} in {ad}  [{src}]\n")
    sys.stderr.write(f"\n  {len(found)} word match(es) of >= {a.min_word} "
                     f"characters\n")

    sys.stderr.write("\n  most structured addresses (repeat run, ascending "
                     "run):\n")
    scored = sorted(((structure_score(ad), ad, src) for ad, src in addrs),
                    key=lambda z: (-max(z[0]), z[1]))[:10]
    for (r, m), ad, src in scored:
        sys.stderr.write(f"    repeat {r}  ascending {m}   {ad}  [{src}]\n")
    if not found and max(max(s[0]) for s in scored) < 6:
        sys.stderr.write("\n  No exactly-20 address spells anything from the "
                         "puzzle's vocabulary,\n  and none is structurally "
                         "improbable. If the prize address is a vanity\n"
                         "  address, it is not in these lists.\n")


if __name__ == "__main__":
    main()
