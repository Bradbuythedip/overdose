#!/usr/bin/env python3
"""Full-length mnemonics only (no sliding windows) - the priority subset of r2."""
import sys
from mnemonic import Mnemonic
W=Mnemonic("english").wordlist
SEQ={
 'words_in':[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'words_nol':[2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'words_mag':[2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
              85000000000,2000000000000,51,95,1969,10],
 'words_one':[2008,1,1,1,40,1971,10,1,2011,1,1000000000,42,20000,100000,6,2017,1,12000,51,85,
              1000000000,2,1000000000000,51,95,1969,10],
 'ext':[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,1,12000,1,51,1,85,2,51,95,0,1,1969,10],
 'first12_w':[2008,1,1,1,40,1971,10,1,2011,1,42,20000],
 'tail12_w':[20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'mid12_w':[40,1971,10,1,2011,1,42,20000,100000,6,2017,12000],
 'dedup_w':[2008,1,40,1971,10,2011,42,20000,100000,6,2017,12000,51,85,2,95,1969],
 'quant':[40,6,1000000000,1000000000,1000000000000],
}
for k in list(SEQ): SEQ['r_'+k]=SEQ[k][::-1]
def conv(v,c):
    if c=='mod': return v%2048
    if c=='inrange': return v if v<2048 else None
    if c=='last3': return int(str(v)[-3:])
    if c=='last4mod': return int(str(v)[-4:])%2048
    if c=='digsum': return sum(int(x) for x in str(v))
    if c=='rev': return int(str(v)[::-1])%2048
    if c=='sq': return (v*v)%2048
    if c=='x11': return (v*11)%2048
    if c=='and2047': return v&2047
out=[]
for n,s in SEQ.items():
    for c in ['mod','inrange','last3','last4mod','digsum','rev','sq','x11','and2047']:
        for base in (0,1):
            idx=[]; ok=True
            for v in s:
                g=conv(v,c)
                if g is None: ok=False; break
                idx.append((g-base)%2048)
            if not ok: continue
            ws=[W[i] for i in idx]
            m=' '.join(ws)
            out += [m, m.upper(), ' '.join(ws[::-1]), m.replace(' ','')]
seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'priority mnemonics')
