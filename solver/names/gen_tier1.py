#!/usr/bin/env python3
"""Tier-1 core for the full-HD pass: the highest-prior name strings."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import ENT, EXTRA, NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST
OUT = os.path.dirname(os.path.abspath(__file__))
ALL_ENT = NAMES + [e[0] for e in EXTRA]
def nosp(s): return s.replace(" ","")
o = []
def P(s):
    if s and len(s) < 3500: o.append(s)

# a. canonical + basic case/space forms of every named entity
for n in ALL_ENT + SURNAME + FIRST + ["Herbert","Lennon","Ono","Nakamoto"]:
    for f in (n, n.lower(), n.upper(), nosp(n), nosp(n).lower(), nosp(n).upper(),
              n.replace(" ","_"), n.replace(" ","-"), nosp(n).lower()[::-1]):
        P(f)

# b. Stacy / Keiser core, heavy
SK = ["Max and Stacy","Max & Stacy","Stacy and Max","Stacy and I","Stacy Herbert",
 "Max Keiser","Keiser Report","The Keiser Report","Max Keiser and Stacy Herbert",
 "Stacy Herbert and Max Keiser","Max Keiser Stacy Herbert","Max Stacy","Stacy Max",
 "Keiser Herbert","Max and Stacy Keiser","Stacy and I have been living in here",
 "Max","Stacy","Keiser","Herbert","MaxK","StacyH","MKSH","MK","SH"]
for s in SK:
    for f in (s, s.lower(), s.upper(), nosp(s), nosp(s).lower(), nosp(s).upper(),
              s.replace(" ","_"), s.replace(" ","-"), s.lower()[::-1], nosp(s).lower()[::-1]):
        P(f)
    for x in ["Overdose","20BTC","20 BTC","toxic","Bitcoin","El Salvador","1969","10years"]:
        for a,b in ((s,x),(x,s)):
            for sep in ["", " ", "-", "_"]:
                j = sep.join([a,b]); P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower())

# c. full-list concatenations in printed order
def cat(lst):
    r=[]
    for sep in ["", " ", ",", ", ", "-", "_", "\n"]:
        for L in (lst, lst[::-1]):
            j=sep.join(L); r+=[j,j.lower(),j.upper()]
            jn=sep.join(nosp(x) for x in L); r+=[jn,jn.lower(),jn.upper()]
    return r
for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, ALL_ENT,
            PEOPLE+PLACES+ORGS+BRANDS, NAMES+["Stacy Herbert"], ["Overdose"]+NAMES):
    for s in cat(sub): P(s)

# d. acrostics
def acros(lst):
    a1="".join(x[0] for x in lst)
    a2="".join("".join(w[0] for w in x.split()) for x in lst)
    a3="".join(x.split()[-1][0] for x in lst)
    a4="".join(x[-1] for x in lst)
    r=[]
    for a in (a1,a2,a3,a4):
        r+=[a,a.lower(),a.upper(),a[::-1],a.lower()[::-1],a.upper()[::-1],
            " ".join(a)," ".join(a).upper(),"-".join(a),".".join(a)]
    return r
for sub in (NAMES,NAMES[::-1],PEOPLE,PEOPLE[::-1],PLACES,ORGS,BRANDS,SURNAME,FIRST,
            ALL_ENT,PEOPLE+PLACES,PEOPLE+PLACES+ORGS+BRANDS):
    for s in acros(sub): P(s)

# e. adjacent pairs, tight
for i in range(len(NAMES)-1):
    a,b=NAMES[i],NAMES[i+1]
    for sep in ["", " ", " and "]:
        j=sep.join([a,b]); P(j); P(j.lower()); P(nosp(j).lower())

# f. entity x 4 crossing terms, tightest forms only
for n in ALL_ENT:
    for c in ["Overdose","20BTC","Max Keiser","toxic"]:
        for a,b in ((n,c),(c,n)):
            for sep in ["", " "]:
                j=sep.join([a,b]); P(j); P(j.lower()); P(nosp(j).lower())

# g. linked people
LINK=[("John","Yoko"),("John Lennon","Yoko Ono"),("George Clinton","James Brown"),
 ("Michael Saylor","Nic Carter","Marty Bent"),("Nayib Bukele","El Salvador"),
 ("Jack Mallers","Strike"),("Vitalik Buterin","mEthereum"),("Roger Ver","Faketoshi"),
 ("Martin Luther","Vatican"),("Jamie Dimon","Wall Street"),("Max Keiser","Stacy Herbert")]
for tup in LINK:
    for perm in itertools.permutations(tup):
        for sep in ["", " ", " and "]:
            j=sep.join(perm); P(j); P(j.lower()); P(nosp(j).lower())

seen,out=set(),[]
for s in o:
    if s not in seen: seen.add(s); out.append(s)
open(os.path.join(OUT,"names_tier1.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print(f"TIER1 {len(out)}")
