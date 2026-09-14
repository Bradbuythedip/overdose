#!/usr/bin/env python3
"""Wave 5: per-page entity groupings, consonant skeletons, leet, and
   name x article-signature-phrase crosses."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)

# ---- entities grouped by the page they appear on --------------------------
P75 = ["Bitcoin", "Wall Street", "Jamie Dimon", "Vitalik Buterin", "mEthereum", "Satoshi"]
P76 = ["George Clinton", "James Brown", "Martin Luther", "Vatican", "Peter Schiff",
       "Friends", "Manhattan Bank", "El Salvador", "International Monetary Fund",
       "IMF", "Twitter", "Nayib Bukele", "Volcano Bonds", "Mike Novogratz", "Wall Street"]
P77 = ["El Salvador", "Jack Mallers", "Strike", "Bhutan", "XRP", "Roger Ver",
       "Block Size War", "Faketoshi", "London", "Peter McCormack", "BCH", "BSV",
       "ETH", "ADA", "Elvis Costello"]
P78 = ["Michael Saylor", "Nic Carter", "Marty Bent", "America", "Afghanistan",
       "Genesis Block"]
P79 = ["John", "Yoko", "Amsterdam", "Stacy", "Max Keiser"]
PAGES = {"p75": P75, "p76": P76, "p77": P77, "p78": P78, "p79": P79}

def dump(lst):
    for sep in ["", " ", ",", ", ", "-", "_", "\n", "|"]:
        for L in (lst, lst[::-1]):
            j = sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn = sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())
    for f in (lambda x: x[0], lambda x: x[-1], lambda x: x.split()[-1][0],
              lambda x: x.split()[0][0]):
        a = "".join(f(x) for x in lst)
        for g in (a, a.lower(), a.upper(), a[::-1], a.lower()[::-1],
                  " ".join(a), "-".join(a), ".".join(a)):
            A(g)
    a2 = "".join("".join(w[0] for w in x.split()) for x in lst)
    for g in (a2, a2.lower(), a2.upper(), a2[::-1]): A(g)
    for k in (2, 3, 4):
        b = "".join(x[:k] for x in lst)
        A(b); A(b.lower()); A(b.upper()); A(b[::-1])

for nm, lst in PAGES.items():
    dump(lst)
    # page tag prefix/suffix
    tag = nm
    for sep in ["", " ", "-", "_"]:
        j = sep.join(lst); A(tag + j); A(j + tag); A((tag + j).lower())
# all pages, one name per page (first-named on each page)
dump([PAGES[k][0] for k in ("p75", "p76", "p77", "p78", "p79")])
dump([PAGES[k][-1] for k in ("p75", "p76", "p77", "p78", "p79")])
# page-list concatenations of the per-page acrostics
acr = "".join("".join(x[0] for x in PAGES[k]) for k in ("p75","p76","p77","p78","p79"))
for g in (acr, acr.lower(), acr.upper(), acr[::-1], acr.lower()[::-1]): A(g)

# ---- consonant skeletons / vowel strips ----------------------------------
VOW = set("aeiouAEIOU")
def skel(s): return "".join(c for c in s if c not in VOW)
def vows(s): return "".join(c for c in s if c in VOW)
for n in NAMES + SURNAME + FIRST + ["Stacy Herbert", "Keiser Report", "Max and Stacy"]:
    for fn in (skel, vows):
        for base in (n, nosp(n)):
            v = fn(base)
            if v:
                A(v); A(v.lower()); A(v.upper()); A(v[::-1])
for sub in (NAMES, PEOPLE, SURNAME, FIRST):
    for fn in (skel, vows):
        v = fn("".join(nosp(x) for x in sub))
        if v:
            A(v); A(v.lower()); A(v.upper()); A(v[::-1])

# ---- leet forms of the principal names ------------------------------------
LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "b": "8", "g": "9"}
def leet(s):
    return "".join(LEET.get(c.lower(), c) for c in s)
for n in ["Max Keiser", "Stacy Herbert", "Max and Stacy", "Keiser Report", "Satoshi",
          "Nayib Bukele", "El Salvador", "Overdose", "Bitcoin", "Faketoshi",
          "Michael Saylor", "Jack Mallers", "Roger Ver", "Vitalik Buterin"]:
    for base in (n, n.lower(), nosp(n), nosp(n).lower()):
        A(leet(base)); A(leet(base).lower()); A(leet(base).upper())

# ---- name x the article's signature phrases -------------------------------
SIG = ["toxic af", "Toxic AF", "Bitcoin is toxic AF", "Layer 1", "layer1",
       "UTXO ghetto", "honey badgering", "honey-badgering", "rabbit hole",
       "hyperbitcoinized", "Volcano Bonds", "buying the dip", "fiat cuck bucks",
       "51% attack", "51 attack", "Genesis Block", "peace and love",
       "peace love and understanding", "the agony and ecstasy",
       "We've seen some shit", "Weve seen some shit", "Full Stop",
       "scammer paradise", "shitcoiner", "nocoiner", "Toxic Bitcoin Maximalists",
       "Cosmic Now", "black hole of the Cosmic Now", "Open your heart to Bitcoin"]
HEAD = ["Max Keiser", "Stacy Herbert", "Max and Stacy", "Keiser Report", "Satoshi",
        "Nayib Bukele", "El Salvador", "Bitcoin", "Overdose", "Max", "Stacy", "Keiser"]
for h in HEAD:
    for s in SIG:
        for a, b in ((h, s), (s, h)):
            for sep in ["", " ", "-", "_", ": "]:
                j = sep.join([a, b])
                A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower()); A(nosp(j).upper())

# ---- every entity joined to Max Keiser's sign-off --------------------------
SIGNOFF = ["MAX KEISER", "Max Keiser", "maxkeiser", "-- MAX KEISER", "by Max Keiser",
           "Max Keiser, Bitcoin Magazine", "Overdose by Max Keiser"]
for n in NAMES:
    for s in SIGNOFF:
        for a, b in ((n, s), (s, n)):
            for sep in ["", " ", ", "]:
                j = sep.join([a, b]); A(j); A(j.lower()); A(nosp(j).lower())

seen, out = set(), []
for s in o:
    if s not in seen:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_wave5.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"WAVE5 {len(out)}")
