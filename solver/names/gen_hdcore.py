#!/usr/bin/env python3
"""The sharp HD core: the most plausible name-lens brainwallet strings."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, EXTRA
import gen_wave3 as W3

OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)
ALL_ENT = NAMES + [e[0] for e in EXTRA]

# 1. every entity: canonical / lower / upper / nospace forms
for n in ALL_ENT + SURNAME + FIRST + ["Herbert", "Lennon", "Ono", "Nakamoto", "Wright"]:
    A(n); A(n.lower()); A(nosp(n)); A(nosp(n).lower()); A(nosp(n).upper())

# 2. Stacy / Keiser core -- heaviest weight
SK = ["Max and Stacy", "Max & Stacy", "Stacy and Max", "Stacy and I", "Stacy Herbert",
      "Max Keiser", "Keiser Report", "The Keiser Report",
      "Max Keiser and Stacy Herbert", "Stacy Herbert and Max Keiser",
      "Max Keiser Stacy Herbert", "Max Stacy", "Keiser Herbert",
      "Stacy and I have been living in here",
      "Max", "Stacy", "Keiser", "Herbert", "MKSH"]
for s in SK:
    for f in (s, s.lower(), s.upper(), nosp(s), nosp(s).lower(), nosp(s).upper(),
              s.replace(" ", "_"), s.replace(" ", "-"),
              s.lower()[::-1], nosp(s).lower()[::-1]):
        A(f)
    for x in ["Overdose", "20BTC", "20 BTC", "toxic", "bitcoin",
              "El Salvador", "1969", "10years"]:
        for a, b in ((s, x), (x, s)):
            for sep in ["", " "]:
                j = sep.join([a, b]); A(j); A(j.lower()); A(nosp(j).lower())

# 3. full-list concatenations, printed order
for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, ALL_ENT,
            PEOPLE + PLACES + ORGS + BRANDS, NAMES + ["Stacy Herbert"]):
    for sep in ["", " ", ",", "-", "\n"]:
        for L in (sub, sub[::-1]):
            j = sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn = sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())

# 4. acrostics
for sub in (NAMES, NAMES[::-1], PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST,
            ALL_ENT, PEOPLE + PLACES, PEOPLE + PLACES + ORGS + BRANDS):
    for f in (lambda x: x[0], lambda x: x[-1], lambda x: x.split()[-1][0]):
        a = "".join(f(x) for x in sub)
        for g in (a, a.lower(), a.upper(), a[::-1], a.lower()[::-1], a.upper()[::-1]):
            A(g)
    a2 = "".join("".join(w[0] for w in x.split()) for x in sub)
    for g in (a2, a2.lower(), a2.upper(), a2[::-1]): A(g)

# 5. adjacent pairs, printed order
for i in range(len(NAMES) - 1):
    a, b = NAMES[i], NAMES[i + 1]
    for sep in ["", " ", " and "]:
        j = sep.join([a, b]); A(j); A(j.lower()); A(nosp(j).lower())

# 6. entity x the four crossing terms
for n in ALL_ENT:
    for c in ["Overdose", "20BTC", "Max Keiser", "toxic"]:
        for a, b in ((n, c), (c, n)):
            j = " ".join([a, b]); A(j.lower()); A(nosp(j).lower()); A(nosp(j).upper())

# 7. real-world aliases of every named entity
for k, v in W3.ALIAS.items():
    for a in v:
        A(a); A(a.lower()); A(nosp(a).lower()); A(nosp(a))

# 8. publication entities + possessive phrases
PUB = ["Bitcoin Magazine", "Bitcoin Magazine Issue 24", "Issue 24",
       "El Salvador Issue", "Fall 2021", "Overdose", "Max Keiser Overdose",
       "Bitcoin is Toxic AF", "Toxic Bitcoin Maximalist",
       "Go Bitcoin Toxic Maximalist", "Bitcoin Magazine El Salvador"]
for p in PUB:
    A(p); A(p.lower()); A(p.upper()); A(nosp(p)); A(nosp(p).lower())
for ow in ["Max Keiser", "Max", "Stacy", "Stacy Herbert", "Max and Stacy",
           "Satoshi", "Nayib Bukele"]:
    for th in ["20 BTC", "20BTC", "twenty bitcoin", "bitcoin",
               "private key", "key", "wallet", "seed"]:
        for pat in (f"{ow}s {th}", f"{ow}'s {th}", f"{th} of {ow}", f"{ow} {th}"):
            A(pat); A(pat.lower()); A(nosp(pat).lower())

# 9. linked people
LINK = [("John", "Yoko"), ("John Lennon", "Yoko Ono"),
        ("George Clinton", "James Brown"),
        ("Michael Saylor", "Nic Carter", "Marty Bent"),
        ("Nayib Bukele", "El Salvador"), ("Jack Mallers", "Strike"),
        ("Vitalik Buterin", "mEthereum"), ("Roger Ver", "Faketoshi"),
        ("Martin Luther", "Vatican"), ("Jamie Dimon", "Wall Street"),
        ("Max Keiser", "Stacy Herbert")]
for tup in LINK:
    for perm in itertools.permutations(tup):
        for sep in ["", " ", " and "]:
            j = sep.join(perm); A(j); A(j.lower()); A(nosp(j).lower())

seen, out = set(), []
for s in o:
    if s not in seen:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_hdcore.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"HDCORE {len(out)}")
