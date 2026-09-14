#!/usr/bin/env python3
"""Wave 4: prompt-order lists, publication entities, possessives, key-nouns,
   and 3-combinations of the most prominent names."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ","")
o=[]
def A(s):
    if s and len(s)<3500: o.append(s)

# -- 1. alternative canonical orderings of the cast -------------------------
CAST_A = ["Satoshi","Vitalik Buterin","Jamie Dimon","Peter Schiff","Nayib Bukele",
 "Mike Novogratz","Jack Mallers","Roger Ver","Faketoshi","Peter McCormack",
 "Michael Saylor","Nic Carter","Marty Bent","Stacy Herbert","Max Keiser",
 "Elvis Costello","George Clinton","James Brown","Martin Luther","John","Yoko"]
CAST_B = ["El Salvador","Bhutan","Afghanistan","London","Amsterdam","Manhattan Bank",
 "IMF","International Monetary Fund","Wall Street","Vatican","Strike",
 "XRP","BCH","BSV","ETH","ADA","mEthereum"]
CAST_C = CAST_A + CAST_B
CAST_D = sorted(NAMES)
CAST_E = sorted(NAMES, key=len)
LISTS = {"castA":CAST_A,"castB":CAST_B,"castC":CAST_C,"castD":CAST_D,"castE":CAST_E,
         "castA_sur":[x.split()[-1] for x in CAST_A],
         "castA_first":[x.split()[0] for x in CAST_A]}
for nm,lst in LISTS.items():
    for sep in ["", " ", ",", ", ", "-", "_", "\n", "|", ";"]:
        for L in (lst, lst[::-1]):
            j=sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn=sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())
    for f in (lambda x:x[0], lambda x:x[-1],
              lambda x:x.split()[-1][0], lambda x:x.split()[0][0]):
        a="".join(f(x) for x in lst)
        A(a); A(a.lower()); A(a.upper()); A(a[::-1]); A(a.lower()[::-1]); A(" ".join(a))
    a2="".join("".join(w[0] for w in x.split()) for x in lst)
    A(a2); A(a2.lower()); A(a2.upper()); A(a2[::-1])
    for k in (2,3,4):
        b="".join(x[:k] for x in lst); A(b); A(b.lower()); A(b.upper()); A(b[::-1])

# -- 2. publication / issue entities ---------------------------------------
PUB = ["Bitcoin Magazine","Bitcoin Magazine Issue 24","Issue 24","BM24",
 "Bitcoin Magazine El Salvador","El Salvador Issue","The El Salvador Issue",
 "Fall 2021","Bitcoin Magazine Fall 2021","BTC Inc","Overdose",
 "Overdose Bitcoin Magazine","Max Keiser Overdose","Bitcoin is Toxic AF",
 "BITCOIN IS TOXIC AF","Toxic Bitcoin Maximalist","Toxic Bitcoin Maximalists",
 "Go Bitcoin Toxic Maximalist","pages 73 79","p73 p79","73-79","75-79"]
HEADS = ["Max Keiser","Stacy Herbert","Max and Stacy","Keiser Report","Nayib Bukele",
 "El Salvador","Satoshi","Bitcoin"]
for p in PUB:
    for f in (p,p.lower(),p.upper(),nosp(p),nosp(p).lower(),nosp(p).upper(),
              p.replace(" ","_"),p.replace(" ","-"),p.lower()[::-1]): A(f)
    for h in HEADS:
        for x,y in ((p,h),(h,p)):
            for sep in ["", " ", "-", "_", ", "]:
                j=sep.join([x,y]); A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower())

# -- 3. possessive / natural-language name phrases --------------------------
OWNERS = ["Max Keiser","Max","Keiser","Stacy","Stacy Herbert","Max and Stacy",
 "Satoshi","Nayib Bukele","Bukele","Jack Mallers","Michael Saylor","John and Yoko"]
THINGS = ["20 BTC","20BTC","twenty bitcoin","twenty BTC","bitcoin","private key",
 "key","wallet","seed","brainwallet","overdose","rabbit hole","stash","treasure",
 "gift","prize","20 bitcoin"]
for ow in OWNERS:
    for th in THINGS:
        for pat in (f"{ow}s {th}", f"{ow}'s {th}", f"{th} of {ow}", f"{th} for {ow}",
                    f"{ow} {th}", f"{th} {ow}"):
            A(pat); A(pat.lower()); A(pat.upper())
            A(nosp(pat)); A(nosp(pat).lower())

# -- 4. name + key-noun -----------------------------------------------------
KN = ["key","privatekey","private key","seed","wallet","brainwallet","passphrase",
 "password","secret","address","btc","bitcoin","20","20btc","hodl","sats"]
for n in NAMES + ["Stacy Herbert","Keiser Report","Max and Stacy"]:
    b=[n, n.lower(), nosp(n).lower(), nosp(n)]
    for x in b:
        for k in KN:
            A(x+k); A(k+x); A(x+" "+k); A(k+" "+x); A(x+"-"+k); A(x+"_"+k)

# -- 5. all 3-combinations of the 14 most prominent names -------------------
TOP = ["Max Keiser","Stacy Herbert","Satoshi","Nayib Bukele","El Salvador",
 "Jack Mallers","Michael Saylor","Vitalik Buterin","Peter Schiff","Jamie Dimon",
 "Roger Ver","Faketoshi","John","Yoko"]
for c in itertools.combinations(TOP,3):
    for sep in ["", " ", "-"]:
        j=sep.join(c); A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower())
for c in itertools.permutations(TOP,2):
    for sep in ["", " ", "-", "_", " and "]:
        j=sep.join(c); A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower())

# -- 6. surname chains of increasing length, printed order ------------------
SUR = [x.split()[-1] for x in NAMES if " " in x]
for w in range(2, len(SUR)+1):
    for i in range(len(SUR)-w+1):
        win=SUR[i:i+w]
        for sep in ["", " ", "-"]:
            j=sep.join(win); A(j); A(j.lower()); A(j.upper())
FN = [x.split()[0] for x in NAMES if " " in x]
for w in range(2, len(FN)+1):
    for i in range(len(FN)-w+1):
        win=FN[i:i+w]
        for sep in ["", " "]:
            j=sep.join(win); A(j); A(j.lower()); A(j.upper())

seen,out=set(),[]
for s in o:
    if s not in seen: seen.add(s); out.append(s)
open(os.path.join(OUT,"names_wave4.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print(f"WAVE4 {len(out)}")
