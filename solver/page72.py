#!/usr/bin/env python3
"""
Page 72 -- a page of the spread that was never in the corpus, and a SECOND
banknote serial.

HOW IT WAS MISSED
`article_transcript.txt` holds body copy for pages 75-79.
`looking_at_the_pages.md` found that 73 and 74 were also absent. Nobody knew
about **72**, because the working images were seven phone JPEGs of pages 73-79.
The uploaded scan `Scan1.PDF` has eight pages, and the extra one is 72: a full
page headed NUMBERS, facing the article's opening spread.

It names Keiser's own stated clue in display type:

    165  WESTERN UNION LOCATIONS IN PALESTINE
    572  WESTERN UNION LOCATIONS IN EL SALVADOR

-- and "Obviously, 'El Salvador' is a clue" is one of the three things he ever
said about this puzzle.

THE SECOND SERIAL
Page 72 carries a ghosted banknote behind the type. Isolating the faint layer
(keeping only mid-greys, discarding both the black display type and the white
paper) reads its serial clearly:

    KB 46279860

That is NOT CL 76841714 A. `looking_at_the_pages.md` established that every
legible bill across pages 73/74 is one cutout reused -- always CL76841714A --
and six modules have been built around that value. This is a different note,
and nothing has ever been run against it.

  python3 page72.py --selftest
  python3 page72.py --out p72.txt
"""
import argparse, itertools, sys

SERIAL2 = "KB46279860"
SER2_LETTERS, SER2_DIGITS = "KB", "46279860"
SERIAL1 = "CL76841714A"
SER1_DIGITS = "76841714"

# every string set in type on page 72, read at 400 dpi
LINES = [
    "NUMBERS",
    "165", "WESTERN UNION", "LOCATIONS IN", "PALESTINE",
    "572", "EL SALVADOR",
    "165 WESTERN UNION LOCATIONS IN PALESTINE",
    "572 WESTERN UNION LOCATIONS IN EL SALVADOR",
    "In 2020,", "WESTERN UNION", "GENERATED REVENUE", "OF $4.8 BILLION",
    "In 2020, WESTERN UNION GENERATED REVENUE OF $4.8 BILLION",
    "The global", "REMITTANCE", "MARKET SIZE", "is projected to reach",
    "$930.44 BILLION BY 2026",
    "The global REMITTANCE MARKET SIZE is projected to reach "
    "$930.44 BILLION BY 2026",
    "Based on a compound annual growth rate of 3.9%",
    "taken from historical remittance industry growth data",
    "The global", "DIGITAL", "REMITTANCE", "MARKET",
    "is estimated to reach", "$35.8 BILLION BY 2026",
    "The global DIGITAL REMITTANCE MARKET is estimated to reach "
    "$35.8 BILLION BY 2026",
    "This is up from", "$14.5 BILLION BY 2019",
    "72",
]
# the numerals, in printed order
NUMS72 = ["165", "572", "2020", "4.8", "930.44", "2026", "3.9",
          "35.8", "2026", "14.5", "2019", "72"]


def variants(s):
    out = {s, s.upper(), s.lower(), s.replace(" ", ""),
           s.replace(" ", "").upper(), s.replace(" ", "").lower(),
           s[::-1], "".join(c for c in s if c.isalnum())}
    return {x for x in out if x}


def build():
    out = set()
    for L in LINES:
        out |= variants(L)

    # THE SECOND SERIAL, every form the first one was ever tested in
    for s in (SERIAL2, SER2_DIGITS, SER2_LETTERS,
              "KB 46279860", "KB 4627 9860"):
        out |= variants(s)
        out.add(s[::-1])
        out.add(s.lower())
    # with a trailing letter, since a US serial is letter-digits-letter and the
    # last character is overprinted by the headline
    for t in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        out.add(SERIAL2 + t)
        out.add((SERIAL2 + t).lower())
        out.add(SER2_DIGITS + t)

    # the two serials together -- two notes, two values
    for a, b in itertools.permutations((SERIAL2, SERIAL1, SER2_DIGITS,
                                        SER1_DIGITS), 2):
        out.add(f"{a} {b}")
        out.add(f"{a}{b}")
    # digits of both, summed and concatenated
    out.add(SER1_DIGITS + SER2_DIGITS)
    out.add(SER2_DIGITS + SER1_DIGITS)
    out.add(str(int(SER1_DIGITS) + int(SER2_DIGITS)))
    out.add(str(int(SER2_DIGITS) - int(SER1_DIGITS)))
    out.add(str(abs(int(SER1_DIGITS) - int(SER2_DIGITS))))

    # the page's numerals as a sequence
    for join in ("", " ", "-", ","):
        out.add(join.join(NUMS72))
        out.add(join.join(NUMS72[::-1]))
    out.add("".join(n.replace(".", "") for n in NUMS72))

    # crossed with the article's own anchors and Keiser's stated clue
    ANCH = ["OVERDOSE", "El Salvador", "ELSALVADOR", "Max Keiser", "MAXKEISER",
            "Palestine", "Western Union", "WESTERNUNION", "20 BTC", "NUMBERS"]
    for a in ANCH:
        for b in (SERIAL2, SER2_DIGITS, SERIAL1, "165", "572", "72"):
            out.add(f"{a} {b}")
            out.add(f"{b} {a}")
            out.add(f"{a}{b}")
            out.add(f"{b}{a}")
    return sorted(x for x in out if 0 < len(x) < 400)


def selftest():
    ok = True
    ok &= SERIAL2 == "KB46279860" and len(SER2_DIGITS) == 8
    sys.stderr.write(f"  second serial {SERIAL2!r}: "
                     f"{len(SER2_LETTERS)} letters + {len(SER2_DIGITS)} "
                     f"digits {'OK' if len(SER2_DIGITS)==8 else 'FAIL'}\n")
    ok &= SERIAL2 != SERIAL1
    sys.stderr.write(f"  and it differs from {SERIAL1!r}: "
                     f"{'OK' if SERIAL2!=SERIAL1 else 'FAIL'}\n")
    # it must be genuinely absent from everything already swept
    import os
    seen = False
    for f in ("article_transcript.txt", "candidates_v2.txt", "furniture.txt"):
        if os.path.exists(f):
            if SER2_DIGITS in open(f, encoding="utf-8", errors="ignore").read():
                seen = True
                sys.stderr.write(f"  NOTE: {SER2_DIGITS} already appears in {f}\n")
    ok &= not seen
    sys.stderr.write(f"  absent from the existing corpora, i.e. untested: "
                     f"{'OK' if not seen else 'FAIL'}\n")
    c = build()
    floor = 26 + len(LINES)
    ok &= len(c) > floor
    sys.stderr.write(f"  {len(c):,} candidates (floor {floor})\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="p72.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("page 72 inventory is wrong; refusing")
    if a.selftest:
        return
    c = build()
    open(a.out, "w", encoding="utf-8").write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c):,} candidates -> {a.out}\n"
                     f"  next: python3 try_phrases.py --in {a.out} "
                     f"--label p72\n")


if __name__ == "__main__":
    main()
