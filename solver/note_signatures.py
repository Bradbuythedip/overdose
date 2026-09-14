#!/usr/bin/env python3
"""
The two SIGNATURES printed on the banknote, which the serial identifies.

THE CHAIN
`looking_at_the_pages.md` established that the $100 bill on pages 73/74 is one
cutout reused across the spread, and every legible copy carries the same value:

    CL 76841714 A     with L12 beside the CL

Confirmed again here by reading the clearest copy on p74 at 3x. So the serial
is not a sequence; it is ONE deliberate value shown repeatedly. That is
emphasis, and it is why the serial has had more attention than anything else
in this project.

Every framing so far treated the serial as MATERIAL (hash it), as a CHECKSUM
(does a derivation reproduce it), as ENTROPY (seed an RNG with it), or as
INDICES. This is a different question: what does the serial IDENTIFY?

On a Federal Reserve Note the serial's first letter is the series letter and
the second is the issuing district -- so `CL` is series C, district L (12, San
Francisco), and the separately printed `L12` is the district repeated. The
series letter fixes the series year, and the series year fixes WHOSE SIGNATURES
ARE PRINTED ON THE NOTE: the Treasurer of the United States and the Secretary
of the Treasury.

So the bill carries two names that are not written anywhere in the article and
are recoverable only by reading the serial as a catalogue number. For a puzzle
built on a photographed banknote, that is the one piece of information the
note contains which the reader must go and look up.

HONEST CAVEAT
The series-letter-to-year mapping for $100 notes is stated from reference
knowledge, not read off the scan -- the printed "SERIES" line is well under
the resolution of these images. So every plausible modern series is swept, not
just series C, and the sweep does not depend on my mapping being right.

  python3 note_signatures.py --selftest
  python3 note_signatures.py --out notesig.txt
"""
import argparse, itertools, sys

# (series, Treasurer of the United States, Secretary of the Treasury)
SERIES = [
    ("1990", "Catalina Vasquez Villalpando", "Nicholas F. Brady"),
    ("1993", "Mary Ellen Withrow", "Lloyd Bentsen"),
    ("1996", "Mary Ellen Withrow", "Robert E. Rubin"),
    ("1999", "Mary Ellen Withrow", "Lawrence H. Summers"),
    ("2001", "Rosario Marin", "Paul H. O'Neill"),
    ("2003", "Rosario Marin", "John W. Snow"),
    ("2003A", "Anna Escobedo Cabral", "John W. Snow"),
    ("2006", "Anna Escobedo Cabral", "Henry M. Paulson Jr."),
    ("2006A", "Anna Escobedo Cabral", "Henry M. Paulson Jr."),
    ("2009", "Rosa Gumataotao Rios", "Timothy F. Geithner"),
    ("2009A", "Rosa Gumataotao Rios", "Timothy F. Geithner"),
    ("2013", "Rosa Gumataotao Rios", "Jacob J. Lew"),
    ("2017", "Jovita Carranza", "Steven T. Mnuchin"),
    ("2017A", "Jovita Carranza", "Steven T. Mnuchin"),
]

SERIAL, DIGITS, DISTRICT = "CL76841714A", "76841714", "L12"
# printed on every Federal Reserve Note
LEGENDS = [
    "THE UNITED STATES OF AMERICA",
    "FEDERAL RESERVE NOTE",
    "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE",
    "ONE HUNDRED DOLLARS",
    "Treasurer of the United States",
    "Secretary of the Treasury",
    "IN GOD WE TRUST",
    "Benjamin Franklin",
    "Independence Hall",
    "San Francisco",
    "Federal Reserve Bank of San Francisco",
]


def variants(s):
    out = {s, s.upper(), s.lower(), s.replace(" ", ""),
           s.replace(" ", "").upper(), s.replace(" ", "").lower(),
           s.replace(".", "").replace(",", ""),
           "".join(w[0] for w in s.split() if w),          # initials
           "".join(w[0] for w in s.split() if w).upper(),
           s.split()[-1] if s.split() else s,               # surname
           s.split()[0] if s.split() else s}
    return {x for x in out if x}


def build():
    out = set()
    for ser, treas, sec in SERIES:
        for n in (treas, sec):
            out |= variants(n)
        # the pair, in both printed orders
        for a, b in ((treas, sec), (sec, treas)):
            out.add(f"{a} {b}")
            out.add(f"{a}{b}")
            out.add((a + b).replace(" ", ""))
            out.add(f"{a} and {b}")
        # crossed with the serial, the district, and the series year
        for tag in (SERIAL, DIGITS, DISTRICT, ser, "Series " + ser):
            for n in (treas, sec):
                out.add(f"{n} {tag}")
                out.add(f"{tag} {n}")
                out.add((n + tag).replace(" ", ""))
        out.add(f"Series {ser}")
        out.add(f"SERIES {ser}")
    for L in LEGENDS:
        out |= variants(L)
        for tag in (SERIAL, DIGITS, DISTRICT):
            out.add(f"{L} {tag}")
            out.add(f"{tag} {L}")
    # series C specifically -- what the CL prefix indicates
    for ser, treas, sec in SERIES:
        if ser.startswith("2001"):
            for a, b in itertools.permutations((treas, sec, SERIAL, DISTRICT), 2):
                out.add(f"{a} {b}")
                out.add(f"{a}{b}".replace(" ", ""))
    # every signatory crossed with every note legend, and with the article's
    # own title and byline -- the note and the column are the two halves of the
    # spread and a passphrase could join them
    ARTICLE = ["OVERDOSE", "Overdose", "Max Keiser", "MAX KEISER",
               "El Salvador", "BITCOIN IS TOXIC AF", "20 BTC"]
    names = sorted({n for _s, t, x in SERIES for n in (t, x)})
    for n in names:
        sur = n.split()[-1]
        for other in LEGENDS + ARTICLE:
            for a, b in ((n, other), (other, n), (sur, other), (other, sur)):
                out.add(f"{a} {b}")
                out.add(f"{a}{b}".replace(" ", ""))
    # surnames alone, paired, in both orders
    surs = sorted({n.split()[-1] for _s, t, x in SERIES for n in (t, x)})
    for a, b in itertools.permutations(surs, 2):
        out.add(f"{a} {b}")
        out.add(f"{a}{b}")
        for tag in (SERIAL, DIGITS, DISTRICT):
            out.add(f"{a} {b} {tag}")
            out.add(f"{a}{b}{tag}")
    return sorted(x for x in out if 0 < len(x) < 400)


def selftest():
    ok = True
    ok &= len(SERIES) >= 12
    sys.stderr.write(f"  {len(SERIES)} note series with both signatures\n")
    # series C is the one the CL prefix indicates
    c = [s for s in SERIES if s[0] == "2001"]
    ok &= len(c) == 1 and c[0][1] == "Rosario Marin"
    sys.stderr.write(f"  series C (2001) -> {c[0][1]} / {c[0][2]}: "
                     f"{'OK' if c else 'FAIL'}\n")
    v = variants("Paul H. O'Neill")
    ok &= "PHO" in v and "O'Neill" in v
    sys.stderr.write(f"  variants give initials and surname "
                     f"({len(v)} of \"Paul H. O'Neill\"): "
                     f"{'OK' if 'PHO' in v else 'FAIL'}\n")
    c = build()
    # a floor with a reason: 14 series x 2 signatories x ~10 variants each is
    # 280 before any pairing, and the pairings multiply that severalfold.
    floor = len(SERIES) * 2 * 10
    ok &= len(c) > floor
    sys.stderr.write(f"  {len(c):,} candidates (floor {floor}, "
                     f"= series x signatories x variants)\n")
    # none of these names may appear in the article, or they are not new
    try:
        body = open("article_transcript.txt", encoding="utf-8").read().lower()
        clash = [n for _s, t, x in SERIES for n in (t, x)
                 if n.split()[-1].lower() in body]
        sys.stderr.write(f"  signatory surnames already in the article: "
                         f"{clash if clash else 'none'}\n")
        ok &= not clash
    except OSError:
        pass
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="notesig.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the signature table is wrong; refusing")
    if a.selftest:
        return
    c = build()
    open(a.out, "w", encoding="utf-8").write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c):,} candidates -> {a.out}\n"
                     f"  next: python3 try_phrases.py --in {a.out} "
                     f"--label notesig\n")


if __name__ == "__main__":
    main()
