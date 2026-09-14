#!/usr/bin/env python3
"""
Everything PRINTED on the pages that the transcript never contained.

WHAT LOOKING AT THE PAGES TURNED UP
`article_transcript.txt` holds body copy for pages 75-79 and nothing else. The
spread is 73-79, and every page carries printed text outside the body column
that no sweep has ever seen:

  p73/74   the OVERDOSE masthead in display serif, the byline "with Max
           Keiser", the photographer credit @ANNABELLEBAZ, and the banknote
           itself -- printed MIRRORED, so "100 DOLLARS" and "THE UNITED STATES
           OF AMERICA" read backwards on the page
  p77      a painted "SHIT" graphic, bottom left, white on the dark ground
  p78      a black scribble reading "X FUCK ALL X", with the article's own
           pull-quote reversed out in white inside it -- the THIRD printing of
           "The economy of love is infinitely more efficient than hate and war"
  p79      the handwritten "MAX KEISER" signature with a heart between the
           words, and a drawn Bitcoin symbol
  all      the orange "OVERDOSE" running head, the vertical "Bitcoin Magazine |
           El Salvador" folio, and the page numbers 73-79

This is not a cipher hypothesis. It is the observation that a corpus described
as "the article" was missing the parts of the article that are not body copy --
including the two words a person is most likely to notice on the spread, SHIT
and FUCK ALL, and the only thing on any page written in Keiser's own hand.

  python3 page_furniture.py --selftest
  python3 page_furniture.py --out furniture.txt
"""
import argparse, itertools, sys

RUNNING_HEAD = ["OVERDOSE", "Overdose", "overdose"]
FOLIO = ["Bitcoin Magazine", "El Salvador", "Bitcoin Magazine | El Salvador",
         "Bitcoin Magazine El Salvador", "BitcoinMagazineElSalvador"]
PAGES = [str(n) for n in range(73, 80)]
BYLINE = ["with Max Keiser", "withMaxKeiser", "Max Keiser", "MAX KEISER",
          "MAXKEISER", "maxkeiser"]
CREDIT = ["@ANNABELLEBAZ", "ANNABELLEBAZ", "annabellebaz", "@annabellebaz",
          "Annabelle Baz", "AnnabelleBaz"]
GRAPHIC = ["SHIT", "shit", "Shit",
           "FUCK ALL", "FUCKALL", "fuck all", "fuckall",
           "X FUCK ALL X", "XFUCKALLX",
           "The economy of love is infinitely more efficient than hate and war.",
           "The economy of love is infinitely more efficient than hate and war"]
SIGNATURE = ["MAX KEISER", "MAX <3 KEISER", "MAX heart KEISER", "MAXKEISER",
             "Max Keiser <3", "MAX KEISER love"]
NOTE = ["100 DOLLARS", "THE UNITED STATES OF AMERICA",
        "ONE HUNDRED DOLLARS", "FEDERAL RESERVE NOTE",
        "CL76841714A", "CL 76841714 A", "L12", "L 12",
        # as printed: mirrored
        "SRALLOD 001", "ACIREMA FO SETATS DETINU EHT"]
MASTHEAD = ["OVERDOSE with Max Keiser", "OVERDOSEwithMaxKeiser",
            "OVERDOSE Max Keiser", "OVERDOSE 73", "OVERDOSE El Salvador"]


def groups():
    return {
        "running_head": RUNNING_HEAD,
        "folio": FOLIO,
        "pages": PAGES,
        "byline": BYLINE,
        "credit": CREDIT,
        "graphic": GRAPHIC,
        "signature": SIGNATURE,
        "banknote": NOTE,
        "masthead": MASTHEAD,
    }


def expand(s):
    """Case and punctuation variants of one string."""
    out = {s, s.upper(), s.lower(), s.title(), s.replace(" ", ""),
           s.replace(" ", "").upper(), s.replace(" ", "").lower(),
           s[::-1], "".join(c for c in s if c.isalnum())}
    return {x for x in out if x}


def build():
    g = groups()
    out = set()
    for vals in g.values():
        for v in vals:
            out |= expand(v)
    # every ordered pair across DIFFERENT groups, joined four ways
    names = list(g)
    for a, b in itertools.permutations(names, 2):
        for x in g[a][:8]:
            for y in g[b][:8]:
                out.add(f"{x} {y}")
                out.add(f"{x}{y}")
                out.add(f"{x}-{y}")
                out.add(f"{x}_{y}")
    # the whole page furniture of one page, concatenated in reading order
    for p in PAGES:
        out.add(f"OVERDOSE {p} Bitcoin Magazine El Salvador")
        out.add(f"OVERDOSE{p}")
        out.add(f"Bitcoin Magazine El Salvador {p}")
    # the three printings of the repeated sentence, and the two graphic words
    out.add("SHIT FUCK ALL")
    out.add("FUCK ALL SHIT")
    out.add("OVERDOSE SHIT FUCK ALL")
    return sorted(x for x in out if 0 < len(x) < 400)


def selftest():
    ok = True
    g = groups()
    ok &= "SHIT" in g["graphic"] and "FUCK ALL" in g["graphic"]
    sys.stderr.write(f"  the two graphic words are present: "
                     f"{'OK' if 'SHIT' in g['graphic'] else 'FAIL'}\n")
    ok &= "@ANNABELLEBAZ" in g["credit"]
    sys.stderr.write(f"  the photographer credit is present: "
                     f"{'OK' if '@ANNABELLEBAZ' in g['credit'] else 'FAIL'}\n")
    e = expand("Max Keiser")
    ok &= "MAXKEISER" in e and "resieK xaM" in e
    sys.stderr.write(f"  expand() gives case, spacing and reversal variants "
                     f"({len(e)} of 'Max Keiser'): "
                     f"{'OK' if 'MAXKEISER' in e else 'FAIL'}\n")
    c = build()
    ok &= len(c) > 2000
    sys.stderr.write(f"  {len(c):,} candidates built\n")
    # none of this may already be in the transcript, or it is not new
    try:
        body = open("article_transcript.txt", encoding="utf-8").read()
        for w in ("FUCK ALL", "@ANNABELLEBAZ", "SHIT"):
            if w in body:
                sys.stderr.write(f"  NOTE: {w!r} IS already in the transcript\n")
        absent = [w for w in ("FUCK ALL", "@ANNABELLEBAZ")
                  if w not in body]
        sys.stderr.write(f"  absent from the transcript, i.e. genuinely "
                         f"untested: {absent}\n")
        ok &= len(absent) == 2
    except OSError:
        pass
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="furniture.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the furniture inventory is wrong; refusing")
    if a.selftest:
        return
    c = build()
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c):,} candidates -> {a.out}\n"
                     f"  next: python3 try_phrases.py --in {a.out} "
                     f"--label furniture\n")


if __name__ == "__main__":
    main()
