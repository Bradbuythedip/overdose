#!/usr/bin/env python3
"""
Exhaustive candidate set for the $100 note in the Overdose artwork.

The note is identified as: serial CL76841714A, series 2009A, district mark L12
(L = 12th Federal Reserve district, San Francisco). Earlier passes tested
"CL76841714A" and "L12" alone; the series year was not known then, and the
combinations of the three fields were never enumerated.

Worth doing carefully because the note is the one object in the article that
Keiser demonstrably MIRRORED: on page 73 the bill is printed fully reversed,
every glyph on it reading backwards, and mirror writing is his only stated
clue. So every candidate here is also emitted reversed.

Also emits the integer readings of the digit fields, to be tested as raw
private keys rather than as passphrases -- a small integer is a valid (if
absurd) secp256k1 scalar, and it costs nothing to rule out.

  python3 gen_banknote.py --out /tmp/banknote.txt --ints /tmp/banknote_ints.txt
"""
import argparse, itertools, re, sys

SERIAL = "CL76841714A"
DIGITS = "76841714"
PREFIX = "CL"
SUFFIX = "A"
SERIES = "2009A"
SERIES_YEAR = "2009"
DISTRICT = "L12"
DISTRICT_LETTER = "L"
DISTRICT_NUM = "12"
DISTRICT_CITY = "San Francisco"


def atbash(s):
    out = []
    for c in s:
        if "a" <= c <= "z":
            out.append(chr(ord("z") - (ord(c) - ord("a"))))
        elif "A" <= c <= "Z":
            out.append(chr(ord("Z") - (ord(c) - ord("A"))))
        else:
            out.append(c)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ints", required=True)
    a = ap.parse_args()

    fields = [SERIAL, SERIES, SERIES_YEAR, DISTRICT, DIGITS, PREFIX + DIGITS,
              DIGITS + SUFFIX, DISTRICT_LETTER, DISTRICT_NUM, DISTRICT_CITY,
              "100", "$100", "One Hundred Dollars", "FEDERAL RESERVE NOTE",
              "THE UNITED STATES OF AMERICA", "Series 2009A", "SERIES 2009A"]

    base = set(fields)

    # every ordered combination of the three identifying fields, with the
    # separators a person would plausibly use
    triples = [SERIAL, SERIES, DISTRICT]
    for r in (2, 3):
        for combo in itertools.permutations(triples, r):
            for sep in ("", " ", "-", "_", ",", ", "):
                base.add(sep.join(combo))

    # serial paired with the year, and with the district number
    for other in (SERIES, SERIES_YEAR, DISTRICT, DISTRICT_NUM, "100"):
        for sep in ("", " ", "-"):
            base.add(SERIAL + sep + other)
            base.add(other + sep + SERIAL)

    # digit-field concatenations
    base.add(DIGITS + SERIES_YEAR)
    base.add(SERIES_YEAR + DIGITS)
    base.add(DIGITS + DISTRICT_NUM)
    base.add(DISTRICT_NUM + DIGITS)
    base.add(DIGITS + SERIES_YEAR + DISTRICT_NUM)

    out = set()
    for s in base:
        for v in (s, s.lower(), s.upper(), s.title()):
            for t in (v, v[::-1], atbash(v), atbash(v)[::-1]):
                if 2 <= len(t) <= 200:
                    out.add(t)
                # alphanumeric-only form
                n = re.sub(r"[^A-Za-z0-9]", "", t)
                if 2 <= len(n) <= 200:
                    out.add(n)

    with open(a.out, "w") as f:
        for p in sorted(out):
            f.write(p + "\n")

    # integer readings, to be tried as raw private keys
    ints = set()
    for d in (DIGITS, DIGITS[::-1], SERIES_YEAR, DIGITS + SERIES_YEAR,
              SERIES_YEAR + DIGITS, DIGITS + DISTRICT_NUM,
              DISTRICT_NUM + DIGITS, "100", "20"):
        try:
            ints.add(int(d))
        except ValueError:
            pass
    # the serial with letters mapped to their alphabet positions (C=3, L=12, A=1)
    ints.add(int("312" + DIGITS + "1"))
    ints.add(int(DIGITS) * 100)
    with open(a.ints, "w") as f:
        for i in sorted(ints):
            f.write(f"{i}\n")

    sys.stderr.write(f"{len(out):,} banknote phrases -> {a.out}\n")
    sys.stderr.write(f"{len(ints)} integer readings -> {a.ints}\n")


if __name__ == "__main__":
    main()
