#!/usr/bin/env python3
"""
OVERDOSE page furniture as key material, with the designer now identified.

The credit on the spread, @ANNABELLEBAZ, is Annabelle Bazinet, Bitcoin
Magazine's Director of Product Design -- the person who laid out the pages
(clue_ledger.md #23). Her handle and name, the byline forms, the running head,
the sign-off and the art director's name were never swept as strings (grep:
none), alone and joined with the column's own names. Low prior; cheap.
"""
NAMES = ["@ANNABELLEBAZ", "ANNABELLEBAZ", "annabellebaz", "Annabelle Bazinet", "Annabelle Baz", "Bazinet", "annabelle bazinet",
         "Tommy Marcheschi", "Marcheschi", "with Max Keiser", "OVERDOSE with Max Keiser", "Overdose with Max Keiser",
         "OVERDOSE by Max Keiser", "Bitcoin Magazine | El Salvador", "Bitcoin Magazine El Salvador", "MAX KEISER", "Max Keiser",
         "OVERDOSE MAX KEISER", "BITCOIN IS TOXIC AF MAX KEISER", "Photography by Annabelle Bazinet", "Photo @ANNABELLEBAZ",
         "Annabelle Bazinet Max Keiser", "Max Keiser Annabelle Bazinet", "OVERDOSE Annabelle Bazinet", "Annabelle Bazinet OVERDOSE",
         "Annabelle Bazinet El Salvador", "annabellebaz overdose", "ANNABELLEBAZ OVERDOSE", "@ANNABELLEBAZ OVERDOSE 20 BTC",
         "Annabelle", "Bazinet Keiser", "Keiser Bazinet", "BTC Inc", "BTC Media", "Bitcoin Magazine Issue 24", "The El Salvador Issue",
         "Bitcoin Magazine The El Salvador Issue", "Issue 24 OVERDOSE", "Fall 2021 OVERDOSE", "OVERDOSE 2021", "OVERDOSE Issue 24"]

def forms():
    out = []
    for i, s in enumerate(NAMES):
        for k, v in (("", s), ("/lower", s.lower()), ("/upper", s.upper()), ("/nospace", s.replace(" ", "")),
                     ("/nospace_lower", s.replace(" ", "").lower()), ("/alnum_lower", "".join(c for c in s if c.isalnum()).lower())):
            out.append((f"{i}{k}", v))
    seen, uniq = set(), []
    for t, v in out:
        if v and v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); tags = [t for t, _ in F]
    return len(set(tags)) == len(tags) and all(v for _, v in F) and ("0", "@ANNABELLEBAZ") in F

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
