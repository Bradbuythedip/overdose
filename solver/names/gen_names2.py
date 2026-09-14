#!/usr/bin/env python3
"""Wave 2: priority set for full-HD, plus a broader wave for --no-hd."""
import itertools, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import ENT, EXTRA, NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST
OUT = os.path.dirname(os.path.abspath(__file__))

ALL_ENT = NAMES + [e[0] for e in EXTRA]

def nosp(s): return s.replace(" ", "")
def forms(s):
    return [s, s.lower(), s.upper(), nosp(s), nosp(s).lower(), nosp(s).upper()]

# ===================== PRIORITY (full HD) ================================
prio = []
def P(s):
    if s and len(s) < 3500: prio.append(s)

# 1. canonical entity forms
for n in ALL_ENT:
    for f in forms(n): P(f)
    P(n.replace(" ", "_")); P(n.replace(" ", "-"))
    P(nosp(n)[::-1]); P(n.lower()[::-1])
for s in SURNAME + FIRST + ["Herbert","Lennon","Ono","Nakamoto","Wright"]:
    for f in forms(s): P(f)

# 2. the Stacy / Keiser core -- heaviest coverage
SK = ["Max and Stacy","Max & Stacy","Stacy and Max","Stacy and I",
 "Stacy Herbert","Max Keiser","Keiser Report","The Keiser Report",
 "Max Keiser and Stacy Herbert","Stacy Herbert and Max Keiser",
 "Max Keiser Stacy Herbert","MaxAndStacy","StacyAndMax","Max Stacy",
 "Stacy Max","Keiser Herbert","Herbert Keiser","Max and Stacy Keiser",
 "Stacy and I have been living in here","Stacy and I have been living in here for 10years",
 "Max","Stacy","Keiser","Herbert","MaxK","StacyH","MK","SH","MKSH"]
for s in SK:
    for f in forms(s): P(f)
    P(s.replace(" ","_")); P(s.replace(" ","-")); P(s.replace(" ","."))
    P(s[::-1]); P(s.lower()[::-1]); P(nosp(s).lower()[::-1]); P(nosp(s)[::-1])
    for x in ["Overdose","overdose","20BTC","20 BTC","toxic","TOXIC",
              "Bitcoin","bitcoin","El Salvador","1969","10years","2021"]:
        for a,b in ((s,x),(x,s)):
            for sep in ["", " ", "-", "_"]:
                j = sep.join([a,b])
                P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower()); P(nosp(j).upper())

# 3. full-list concatenations, printed order
def cat(lst):
    r = []
    for sep in ["", " ", ",", ", ", "-", "_", "\n", "|"]:
        for L in (lst, lst[::-1]):
            j = sep.join(L)
            r += [j, j.lower(), j.upper()]
            jn = sep.join(nosp(x) for x in L)
            r += [jn, jn.lower(), jn.upper()]
    return r
for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST,
            PEOPLE+PLACES+ORGS+BRANDS, ALL_ENT,
            NAMES+["Stacy Herbert"], ["Overdose"]+NAMES, NAMES+["Overdose"],
            [n for n in NAMES if " " in n], [n for n in NAMES if " " not in n]):
    for s in cat(sub): P(s)

# 4. acrostics, every flavour
def acros(lst):
    a1 = "".join(x[0] for x in lst)
    a2 = "".join("".join(w[0] for w in x.split()) for x in lst)
    a3 = "".join(x.split()[-1][0] for x in lst)
    a4 = "".join(x[-1] for x in lst)
    a5 = "".join(x.split()[-1][-1] for x in lst)
    r = []
    for a in (a1,a2,a3,a4,a5):
        r += [a, a.lower(), a.upper(), a[::-1], a.lower()[::-1], a.upper()[::-1],
              " ".join(a), " ".join(a).upper(), "-".join(a), ".".join(a)]
    return r
for sub in (NAMES, NAMES[::-1], PEOPLE, PEOPLE[::-1], PLACES, ORGS, BRANDS,
            SURNAME, FIRST, ALL_ENT, PEOPLE+PLACES, PEOPLE+PLACES+ORGS+BRANDS,
            [n for n in NAMES if " " in n]):
    for s in acros(sub): P(s)

# 5. adjacent pairs / triples, tight joins only (bulk joins go in wave-2 nohd)
for i in range(len(NAMES)-1):
    a,b = NAMES[i], NAMES[i+1]
    for sep in ["", " ", "-", "_", " and "]:
        j = sep.join([a,b]); P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower())
for i in range(len(NAMES)-2):
    a,b,c = NAMES[i],NAMES[i+1],NAMES[i+2]
    for sep in ["", " "]:
        j = sep.join([a,b,c]); P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower())

# 6. every entity x the four crossing terms, tight
for n in ALL_ENT:
    for c in ["Overdose","20BTC","20 BTC","Max Keiser","toxic"]:
        for a,b in ((n,c),(c,n)):
            for sep in ["", " ", "-", "_"]:
                j = sep.join([a,b])
                P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower()); P(nosp(j).upper())

# 7. semantically paired people
LINK = [("John","Yoko"),("John Lennon","Yoko Ono"),("George Clinton","James Brown"),
 ("Michael Saylor","Nic Carter"),("Nic Carter","Marty Bent"),
 ("Michael Saylor","Nic Carter","Marty Bent"),("Nayib Bukele","El Salvador"),
 ("Jack Mallers","Strike"),("Vitalik Buterin","mEthereum"),
 ("Roger Ver","Faketoshi"),("Faketoshi","Peter McCormack"),
 ("Martin Luther","Vatican"),("Jamie Dimon","Wall Street"),
 ("Mike Novogratz","Wall Street"),("Peter Schiff","Bitcoin"),
 ("Max Keiser","Stacy Herbert"),("IMF","El Salvador"),("Bhutan","XRP"),
 ("Satoshi","Genesis Block"),("Amsterdam","John and Yoko")]
for tup in LINK:
    for perm in itertools.permutations(tup):
        for sep in ["", " ", "-", "_", " and ", "&"]:
            j = sep.join(perm)
            P(j); P(j.lower()); P(nosp(j)); P(nosp(j).lower()); P(nosp(j).upper())

seen, out = set(), []
for s in prio:
    if s not in seen: seen.add(s); out.append(s)
open(os.path.join(OUT,"names_prio.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print(f"PRIO {len(out)}")

# ===================== WAVE 2 BROAD (--no-hd) ============================
more = []
def M(s):
    if s and len(s) < 3500: more.append(s)

YEARS = ["2021","2011","1971","2008","2017","1969","2009","20","21","51","42","95"]
SUFF  = ["","!","?",".","1","123","bitcoin","btc","BTC","Bitcoin","20","20btc",
         "overdose","toxic","keiser","stacy","maximalist","hodl"]
for n in ALL_ENT + SURNAME + FIRST + ["Stacy Herbert","Keiser Report"]:
    base = [n, n.lower(), nosp(n), nosp(n).lower(), nosp(n).upper()]
    for b in base:
        for y in YEARS:
            M(b+y); M(y+b); M(b+" "+y); M(y+" "+b); M(b+"-"+y); M(b+"_"+y)
        for s in SUFF:
            if s: M(b+s); M(s+b); M(b+" "+s)
        M(b+b); M(b+b+b)

# every unordered pair of ALL entities (not just adjacent) - bulk
for a,b in itertools.combinations(ALL_ENT, 2):
    for x,y in ((a,b),(b,a)):
        j = nosp(x)+nosp(y)
        M(j); M(j.lower())
        j2 = x+" "+y
        M(j2); M(j2.lower())

# every unordered pair of surnames
for a,b in itertools.permutations(SURNAME+["Herbert"], 2):
    M(a+b); M((a+b).lower()); M(a+" "+b); M((a+" "+b).lower())

# initials pairs/triples
INI = ["".join(w[0] for w in n.split()) for n in ALL_ENT]
for r in (2,3):
    for combo in itertools.permutations(sorted(set(INI)), r):
        j = "".join(combo); M(j); M(j.lower())
        if len(more) > 400000: break

# per-category acrostic variants with separators
for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST):
    for k in range(1, 6):
        a = "".join(x[:k] for x in sub)
        M(a); M(a.lower()); M(a.upper()); M(a[::-1]); M(a.lower()[::-1])
        b = "".join(x.split()[-1][:k] for x in sub)
        M(b); M(b.lower()); M(b.upper()); M(b[::-1])

# sliding windows over the printed-order name list (2..8 names)
for w in range(2, 9):
    for i in range(len(NAMES)-w+1):
        win = NAMES[i:i+w]
        for sep in ["", " ", "-"]:
            j = sep.join(win); M(j); M(j.lower())
            jn = sep.join(nosp(x) for x in win); M(jn); M(jn.lower())

seen2, out2 = set(seen), []
for s in more:
    if s not in seen2: seen2.add(s); out2.append(s)
open(os.path.join(OUT,"names_more.txt"),"w",encoding="utf-8").write("\n".join(out2)+"\n")
print(f"MORE {len(out2)}")
