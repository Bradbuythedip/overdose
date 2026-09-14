#!/usr/bin/env python3
"""Words that exist on the page only as ARTWORK -- no text sweep can see them.
  p73  OVERDOSE masthead + "with Max Keiser" + 5 pills + $100 note
  p76  two grey brush X / cross marks
  p77  "SHIT" in white splatter
  p78  "FUCK ALL" hand-scrawled, with X marks, over the pull-quote
  p79  barbed wire, a hand-drawn Bitcoin symbol, 5 pills, handwritten MAX KEISER
"""
import itertools, re
G = ['SHIT', 'FUCK ALL', 'FUCKALL', 'fuck all', 'OVERDOSE', 'MAX KEISER',
     'with Max Keiser', 'barbed wire', 'B', 'bitcoin symbol', 'X', 'XX',
     'pills', 'banknote', 'CL76841714A']
out=[]
def add(*xs):
    for x in xs:
        if not x: continue
        x=x.strip()
        if 2<len(x)<4000: out.append(x)
def addv(*xs):
    for s in xs:
        w=[x for x in re.split(r'\s+',s) if x]
        add(s, s.lower(), s.upper(), ''.join(w), ''.join(w).lower(),
            ''.join(w).upper(), s[::-1], s.lower()[::-1],
            ''.join(x.capitalize() for x in w))
for g in G: addv(g)
# the graphic words in printed page order
SEQ = ['OVERDOSE', 'SHIT', 'FUCK ALL', 'MAX KEISER']
for sep in ['', ' ', '-', ',', '_', ' | ']:
    add(sep.join(SEQ)); add(sep.join(s.lower() for s in SEQ))
    add(sep.join(SEQ[::-1])); add(sep.join(s.replace(' ','') for s in SEQ))
addv(''.join(s[0] for s in SEQ))
addv('OVERDOSE SHIT FUCK ALL MAX KEISER')
addv('SHIT FUCK ALL', 'FUCK ALL SHIT', 'shitfuckall', 'SHITFUCKALL')
# crossed with the prize and the title
for a in ['SHIT','FUCKALL','FUCK ALL','OVERDOSE','MAXKEISER']:
    for b in ['20','20BTC','2021','73','79','24','ElSalvador','10years','mEthereum']:
        add(a+b, a+' '+b, b+a, (a+b).lower(), (a+b).upper())
# the pull-quote the FUCK ALL scrawl sits on
PQ='The economy of love is infinitely more efficient than hate and war.'
addv(PQ.rstrip('.'))
for a in ['FUCK ALL','FUCKALL','SHIT']:
    add(a+' '+PQ, PQ+' '+a, (a+PQ).replace(' ','').lower())
# the graphic X marks
addv('X marks', 'two X', 'XX marks the spot', 'X marks the spot')
seen=set()
for s in out:
    if s not in seen: seen.add(s); print(s)
