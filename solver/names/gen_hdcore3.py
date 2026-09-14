#!/usr/bin/env python3
"""HD tier 3: the principal names carrying the article's numbers and the
   common brainwallet suffixes, plus surname/first-name chains."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, SURNAME, FIRST
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)

TOP = ["Max Keiser", "Stacy Herbert", "Max and Stacy", "Keiser Report", "Satoshi",
       "Nayib Bukele", "El Salvador", "Jack Mallers", "Michael Saylor",
       "Vitalik Buterin", "Peter Schiff", "Roger Ver", "Faketoshi", "Bitcoin",
       "Overdose", "Amsterdam", "John", "Yoko", "Keiser", "Stacy", "Max"]
NUMS = ["20", "24", "21", "51", "42", "95", "85", "12000", "100000", "20000",
        "2008", "2011", "2017", "2021", "1971", "1969", "73", "79", "20btc",
        "20BTC", "2021btc"]
SUFF = ["bitcoin", "btc", "BTC", "toxic", "overdose", "maximalist", "hodl",
        "key", "wallet", "seed", "!", "?", "1", "123"]

for n in TOP:
    bases = [n, n.lower(), n.upper(), nosp(n), nosp(n).lower(), nosp(n).upper()]
    for b in bases:
        for num in NUMS:
            for sep in ["", " ", "-", "_"]:
                A(b + sep + num); A(num + sep + b)
        for s in SUFF:
            A(b + s); A(s + b); A(b + " " + s); A(b + "-" + s); A(b + "_" + s)
        A(b + b)

# surname chains and first-name chains of every length, printed order
SUR = [x.split()[-1] for x in NAMES if " " in x]
FN = [x.split()[0] for x in NAMES if " " in x]
for lst in (SUR, FN):
    for w in range(2, len(lst) + 1):
        for i in range(len(lst) - w + 1):
            win = lst[i:i + w]
            for sep in ["", " ", "-"]:
                j = sep.join(win); A(j); A(j.lower()); A(j.upper())

# exclude what has already been through the full HD stack
done = set()
for fn in ("names_hdcore.txt", "names_hdcore2.txt"):
    for l in open(os.path.join(OUT, fn), encoding="utf-8"):
        done.add(l.rstrip("\n"))
seen, out = set(), []
for s in o:
    if s and s not in seen and s not in done:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_hdcore3.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"HDCORE3 {len(out)}")
