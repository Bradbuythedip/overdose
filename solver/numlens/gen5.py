#!/usr/bin/env python3
"""Round 4: the concatenated digit stream as a cipher (A1Z26 pairs, base-N chunks)."""
import sys, itertools
P  = [2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
B  = [2008,1971,40,10,1,2011,1,42,20000,100000,6,12000,2017,51,85,2,51,95,1969,10]
NL = [2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
NU = [2008,1,1,1,1971,10,1,2011,1,42,20000,100000,2017,12000,51,85,2,51,95,1969,10]
EX = [2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
      85000000000,2000000000000,51,95,1969,10]
SETS={'P':P,'B':B,'NL':NL,'NU':NU,'EX':EX,'rP':P[::-1],'rB':B[::-1],'rNL':NL[::-1],'rNU':NU[::-1]}
out=[]
def add(s):
    s=str(s)
    if s and len(s)<3900: out.append(s)

for name,s in SETS.items():
    for j in (''.join(str(x) for x in s), ''.join(str(x) for x in s)[::-1],
              ' '.join(str(x) for x in s).replace(' ','')):
        for off in (0,1):
            d=j[off:]
            # 2-digit groups -> A1Z26 (and mod 26)
            g2=[d[i:i+2] for i in range(0,len(d)-1,2)]
            t=''.join(chr(64+int(g)) for g in g2 if g.isdigit() and 1<=int(g)<=26)
            add(t); add(t.lower()); add(t[::-1]); add(t.lower()[::-1])
            t=''.join(chr(65+(int(g)-1)%26) for g in g2 if g.isdigit())
            add(t); add(t.lower()); add(t[::-1])
            t=''.join(chr(65+int(g)%26) for g in g2 if g.isdigit())
            add(t); add(t.lower())
            # 2-digit groups as ASCII+offset
            for base in (32,64,96):
                t=''.join(chr(base+int(g)) for g in g2 if g.isdigit() and 32<=base+int(g)<127)
                add(t); add(t.lower())
            # 3-digit groups mod 26 and as ASCII
            g3=[d[i:i+3] for i in range(0,len(d)-2,3)]
            t=''.join(chr(65+int(g)%26) for g in g3 if g.isdigit()); add(t); add(t.lower())
            t=''.join(chr(int(g)) for g in g3 if g.isdigit() and 32<=int(g)<127)
            add(t); add(t.lower())
            # single digits -> letters
            t=''.join(chr(97+int(c)) for c in d if c.isdigit()); add(t); add(t.upper()); add(t[::-1])
        # digit stream as bytes: pairs -> byte values, 32-byte keys
        g2=[d for d in [j[i:i+2] for i in range(0,len(j)-1,2)] if d.isdigit()]
        bb=bytes(int(g)%256 for g in g2)
        for v in (bb.rjust(32,b'\0'), bb.ljust(32,b'\0'), bb[:32], bb[-32:]):
            if len(v)==32: add(v.hex()); add(v.hex().upper())
        # digit stream split into 3-digit bytes
        g3=[d for d in [j[i:i+3] for i in range(0,len(j)-2,3)] if d.isdigit()]
        bb=bytes(int(g)%256 for g in g3)
        for v in (bb.rjust(32,b'\0'), bb.ljust(32,b'\0')):
            if len(v)==32: add(v.hex())
        # the digit string itself in chunks
        for k in (4,5,6,8):
            for sep in ('-',' ',':'):
                add(sep.join(j[i:i+k] for i in range(0,len(j),k)))

seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'round4')
