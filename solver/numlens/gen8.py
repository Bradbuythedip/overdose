#!/usr/bin/env python3
"""Round 7: per-number base conversion, then concatenated (the other 'as hex')."""
import sys
P=[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
E=[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,1,12000,1,51,1,85,2,51,95,0,1,1969,10]
NL=[2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
NU=[2008,1,1,1,1971,10,1,2011,1,42,20000,100000,2017,12000,51,85,2,51,95,1969,10]
B=[2008,1971,40,10,1,2011,1,42,20000,100000,6,12000,2017,51,85,2,51,95,1969,10]
YR=[2008,1971,2011,2017,1969]; PC=[42,51,51,95]
SETS={'P':P,'E':E,'NL':NL,'NU':NU,'B':B,'YR':YR,'PC':PC}
for k in list(SETS): SETS['r'+k]=SETS[k][::-1]
out=[]
def a(s):
    if s and len(str(s))<3900: out.append(str(s))
for n,s in SETS.items():
    for sep in ['',' ','-',':','_',',']:
        for w in (0,2,4,8):
            h=sep.join(format(x,'0%dx'%w) if w else format(x,'x') for x in s)
            a(h); a(h.upper())
            o=sep.join(format(x,'o') for x in s); a(o)
            b=sep.join(format(x,'b') for x in s); a(b)
    # per-number hex, no sep, padded/truncated to a 32-byte key
    for w in (0,2,4,8):
        h=''.join(format(x,'0%dx'%w) if w else format(x,'x') for x in s)
        for pad in (h.rjust(64,'0'),h.ljust(64,'0'),h[:64],h[-64:]):
            if len(pad)==64: a(pad); a(pad.upper())
        a(h); a(h.upper()); a(h[::-1])
    # binary stream packed into bytes
    bs=''.join(format(x,'b') for x in s)
    bb=bytes(int(bs[i:i+8].ljust(8,'0'),2) for i in range(0,len(bs),8))
    for v in (bb.rjust(32,b'\0'),bb.ljust(32,b'\0'),bb[:32],bb[-32:]):
        if len(v)==32: a(v.hex())
    # each number as a fixed-width decimal field
    for w in (2,3,4,6,8):
        t=''.join(str(x).zfill(w)[-w:] for x in s); a(t); a(t[::-1])
        for pad in (t.rjust(64,'0'),t.ljust(64,'0'),t[:64],t[-64:]):
            if len(pad)==64 and pad.isdigit(): a(pad)
seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'round7')
