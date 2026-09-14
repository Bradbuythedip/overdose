#!/usr/bin/env python3
"""Wave 10: windows around each anomaly with the anomaly CORRECTED.
Not literal article spans -- each differs from the page by the fix.  If Keiser
typed the passphrase into a wallet he would have typed it in standard English;
the oddity on the page may be the printer's, not his."""
import re
B='\n'.join(l for l in open('/home/user/overdose/solver/article_transcript.txt',
            encoding='utf-8').read().split('\n')
            if not l.startswith('#') and not l.startswith('==='))
F=re.sub(r'\s+',' ',B).strip()
FIX = [('10years','10 years'), ('mEthereum','Ethereum'),
       ('Bitcoins coattails',"Bitcoin's coattails"),
       ('snake oil salesmen','snake oil salesman'),
       ('pouring over spreadsheets','poring over spreadsheets'),
       ('gargantuanly wasteful','gargantuan and wasteful'),
       ('nailing the Vatican','nailing the Wittenberg door'),
       ('Elvis Costello was right','Nick Lowe was right'),
       ('$85 BILLION','$85 billion'),
       ('Full Stop.','Full stop.'),
       ("Jack Mallers' Strike","Jack Mallers's Strike"),
       ('shitcoinery','shitcoinnery'),
       ('hyperbitcoinized','hyper-bitcoinized'),
       ('cuck-bucks','cuck bucks'),
       ('honey-badgering','honey badgering'),
       ('(Sorry Bhutan','(Sorry Bhutan)')]
out=[]
def add(s):
    s=s.strip()
    if 6 < len(s) < 4000: out.append(s)
for bad, good in FIX:
    i = F.find(bad)
    if i < 0: continue
    fixed = F[:i] + good + F[i+len(bad):]
    words = fixed.split()
    # word index of the fix
    wi = len(fixed[:i].split())
    span = len(good.split())
    for a in range(0, 13):
        for b in range(0, 13):
            seg = ' '.join(words[max(0, wi-a): wi+span+b])
            add(seg); add(seg.lower())
            add(seg.rstrip('.,?!;:'))
            add(''.join(seg.split()).lower())
    add(good); add(good.lower()); add(good.upper())
    add(bad + ' ' + good); add(good + ' ' + bad)
# the whole piece with every fix applied, per page-sized chunk
fixed_all = F
for bad, good in FIX:
    fixed_all = fixed_all.replace(bad, good)
for cut in (3, 4, 5, 6):
    L = len(fixed_all)//cut
    for k in range(cut):
        seg = fixed_all[k*L:(k+1)*L]
        if len(seg) < 4000:
            add(seg); add(seg.lower())
            add(''.join(c for c in seg if c.isalpha()).lower())
seen=set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
