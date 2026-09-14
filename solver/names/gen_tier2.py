#!/usr/bin/env python3
"""Tier-2 HD core (trimmed): canonical real-world aliases, publication entities,
   possessive phrases, and one-alias-per-entity concatenations."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_wave3 as W3
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ","")
o=[]
def A(s):
    if s and len(s)<3500: o.append(s)

# core forms of every real-world alias
for k,v in W3.ALIAS.items():
    for a in v:
        for f in (a, a.lower(), a.upper(), nosp(a), nosp(a).lower(), nosp(a).upper()):
            A(f)

# publication / issue entities x heads
PUB=["Bitcoin Magazine","Bitcoin Magazine Issue 24","Issue 24","El Salvador Issue",
 "Fall 2021","Overdose","Overdose Bitcoin Magazine","Max Keiser Overdose",
 "Bitcoin is Toxic AF","Toxic Bitcoin Maximalist","Go Bitcoin Toxic Maximalist"]
HEADS=["Max Keiser","Stacy Herbert","Max and Stacy","Keiser Report","Nayib Bukele","Satoshi"]
for p in PUB:
    for f in (p,p.lower(),p.upper(),nosp(p),nosp(p).lower(),nosp(p).upper()): A(f)
    for h in HEADS:
        for x,y in ((p,h),(h,p)):
            for sep in ["", " ", "-"]:
                j=sep.join([x,y]); A(j); A(j.lower()); A(nosp(j).lower())

# possessive / ownership phrases
OWN=["Max Keiser","Max","Stacy","Stacy Herbert","Max and Stacy","Satoshi","Nayib Bukele"]
TH=["20 BTC","20BTC","twenty bitcoin","bitcoin","private key","key","wallet","seed","overdose"]
for ow in OWN:
    for th in TH:
        for pat in (f"{ow}s {th}",f"{ow}'s {th}",f"{th} of {ow}",f"{th} for {ow}",
                    f"{ow} {th}",f"{th} {ow}"):
            A(pat); A(pat.lower()); A(nosp(pat).lower())

# one-alias-per-entity concatenations + acrostics
KEYS=list(W3.ALIAS.keys())
for idx in (0,1,2):
    lst=[W3.ALIAS[k][idx] if len(W3.ALIAS[k])>idx else W3.ALIAS[k][0] for k in KEYS]
    for sep in ["", " ", ",", "-", "\n"]:
        for L in (lst,lst[::-1]):
            j=sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn=sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())
    for f in (lambda x:x[0], lambda x:x.split()[-1][0]):
        a="".join(f(x) for x in lst); A(a); A(a.lower()); A(a.upper()); A(a[::-1])

# alias x Overdose / 20BTC / toxic / Max Keiser, tightest joins, canonical alias only
for k,v in W3.ALIAS.items():
    for a in v[:4]:
        for x in ["Overdose","20BTC","toxic","Max Keiser","Stacy"]:
            for p,q in ((a,x),(x,a)):
                j=" ".join([p,q]); A(j.lower()); A(nosp(j).lower())

seen,out=set(),[]
for s in o:
    if s not in seen: seen.add(s); out.append(s)
open(os.path.join(OUT,"names_tier2.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print(f"TIER2 {len(out)}")
