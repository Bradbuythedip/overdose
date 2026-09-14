#!/usr/bin/env python3
"""Round 6: the number sequence as indices into the ordered highlight list."""
import re, sys
H=[l.split('\t')[2].strip() for l in open('/home/user/overdose/solver/highlights_ordered.tsv',
   encoding='utf-8') if not l.startswith('#') and l.count('\t')>=2]
P=[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
E=[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,1,12000,1,51,1,85,2,51,95,0,1,1969,10]
NL=[2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
YR=[2008,1971,2011,2017,1969]; PC=[42,51,51,95]
SETS={'P':P,'E':E,'NL':NL,'YR':YR,'PC':PC,'rP':P[::-1],'rE':E[::-1]}
out=[]
def a(s):
    if s and len(str(s))<3900: out.append(str(s))
n=len(H)
for name,s in SETS.items():
    for base in (0,1):
        idx=[(x-base)%n for x in s]
        sel=[H[i] for i in idx]
        for sep in [' ','','\n',' | ','. ']:
            t=sep.join(sel); a(t); a(t.lower()); a(t.upper())
        # first letters of the selected highlights
        t=''.join(x[0] for x in sel); a(t); a(t.lower()); a(t.upper()); a(t[::-1])
        # first word of each
        t=' '.join(x.split()[0] for x in sel); a(t); a(t.lower()); a(t.replace(' ',''))
        # last word of each
        t=' '.join(x.rstrip('.,').split()[-1] for x in sel); a(t); a(t.lower()); a(t.replace(' ',''))
        # Nth character of the concatenated highlight text
        HT=''.join(H); HA=re.sub(r'[^A-Za-z]','',HT); HN=re.sub(r'\s+','',HT)
        for txt in (HT,HA,HN):
            o=''.join(txt[(x-base)%len(txt)] for x in s)
            a(o); a(o.lower()); a(o.upper()); a(o[::-1])
        # Nth word of the concatenated highlight text
        HW=re.findall(r"[A-Za-z']+",HT)
        o=' '.join(HW[(x-base)%len(HW)] for x in s); a(o); a(o.lower()); a(o.replace(' ',''))
        o=''.join(HW[(x-base)%len(HW)][0] for x in s); a(o); a(o.lower()); a(o.upper())
seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'round6')
