#!/usr/bin/env python3
"""Wave 7: every named entity crossed with every number that appears in the
   article, in all the usual join/case forms."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, SURNAME, FIRST, EXTRA
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)

ALL_ENT = NAMES + [e[0] for e in EXTRA] + ["Stacy Herbert", "Keiser Report",
                                           "Max and Stacy"]
NUMS = ["20", "24", "21", "51", "42", "95", "85", "2", "1", "12000", "12,000",
        "100000", "100,000", "20000", "20,000", "6", "10", "40", "2008", "2009",
        "2011", "2017", "2021", "1971", "1969", "1517", "73", "75", "76", "77",
        "78", "79", "1e6", "51%", "42%", "95%", "20BTC", "20btc"]
JOINS = ["", " ", "-", "_", ".", "#", "/"]

for n in ALL_ENT:
    bases = [n, n.lower(), n.upper(), nosp(n), nosp(n).lower(), nosp(n).upper()]
    for b in bases:
        for num in NUMS:
            for sep in JOINS:
                A(b + sep + num)
                A(num + sep + b)
# surnames / first names with the headline numbers
for s in SURNAME + FIRST + ["Herbert"]:
    for b in (s, s.lower(), s.upper()):
        for num in ["20", "24", "21", "2021", "1969", "51", "95", "20btc", "20BTC"]:
            for sep in ["", " ", "-", "_"]:
                A(b + sep + num); A(num + sep + b)

# number-run strings built from the article's figures, tagged with the author
RUNS = ["2051429585", "20242151", "2008201120172021", "196919712008",
        "202420212011", "5142952085", "7375767778 79", "7379", "7579"]
HEADS = ["Max Keiser", "maxkeiser", "MAXKEISER", "Stacy Herbert", "stacyherbert",
         "Overdose", "overdose", "Max and Stacy", "maxandstacy", "Keiser", "keiser"]
for r in RUNS:
    A(r); A(r[::-1])
    for h in HEADS:
        for sep in ["", " ", "-", "_"]:
            A(h + sep + r); A(r + sep + h)
            A((h + sep + r).lower()); A((r + sep + h).lower())

# entity + "20 BTC" spelled many ways
BTC20 = ["20 BTC", "20BTC", "20 btc", "20btc", "twenty BTC", "twentybtc",
         "twenty bitcoin", "TwentyBitcoin", "20 bitcoin", "20bitcoin",
         "XX BTC", "2000000000 sats", "2,000,000,000 sats", "2000000000",
         "20.00000000", "20.0 BTC"]
for n in ALL_ENT:
    for b in (n, n.lower(), nosp(n), nosp(n).lower()):
        for t in BTC20:
            for sep in ["", " ", "-", "_"]:
                A(b + sep + t); A(t + sep + b)
                A((b + sep + t).lower()); A((t + sep + b).lower())

seen, out = set(), []
for s in o:
    if s not in seen:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_wave7.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"WAVE7 {len(out)}")
