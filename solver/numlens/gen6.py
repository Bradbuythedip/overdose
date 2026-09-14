#!/usr/bin/env python3
"""Round 5: extended inventory incl. 'near zero' and the ordinal 'first's."""
import re, sys, functools, operator
RAW=open('/home/user/overdose/solver/article_transcript.txt',encoding='utf-8').read()
lines=[l for l in RAW.split('\n') if not l.startswith('#')]
page,pages,body=None,{},[]
for l in lines:
    m=re.match(r'=== PAGE (\d+)',l)
    if m: page=int(m.group(1)); pages[page]=[]; continue
    if page is not None: pages[page].append(l); body.append(l)
BODY='\n'.join(body)

# full printed inventory incl. ordinals, ONE, and near-zero
EXT=[2008,1,1,1, 40,1971,10,1,2011,1, 42,20000,100000,6,2017,1,12000,1,51,1, 85,2, 51,95,0,1,1969,10]
# same, ordinals dropped, zero kept
ZER=[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,0,1969,10]
# zero appended to the plain printed sequence
P0 =[2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10,0]
# ordinals only
ORD=[1,1,1]
# the quantity-words only, in order: Forty six billion BILLION trillion zero
QW =[40,6,1000000000,1000000000,1000000000000,0]
SETS={'EXT':EXT,'ZER':ZER,'P0':P0,'ORD':ORD,'QW':QW,
      'rEXT':EXT[::-1],'rZER':ZER[::-1],'rP0':P0[::-1],
      'EXTnz':[x for x in EXT if x],'dEXT':list(dict.fromkeys(EXT))}
SEPS=['',' ','-',',','.','/',':','_','+','|',', ']
out=[]
def add(s):
    if s is None: return
    s=str(s)
    if s and len(s)<3900: out.append(s)

for n,s in SETS.items():
    for seq in (s,s[::-1],sorted(s),sorted(s,reverse=True)):
        for sep in SEPS: add(sep.join(str(x) for x in seq))
    j=''.join(str(x) for x in s)
    add(j[::-1]); add('0x'+j)
    tot=sum(s); nz=[x for x in s if x]
    prod=functools.reduce(operator.mul,nz,1)
    add(tot); add(str(tot)[::-1]); add(prod); add(prod%(1<<256))
    add(functools.reduce(operator.xor,[abs(x) for x in s],0))
    add(sum(int(c) for c in j))
    d=[s[i+1]-s[i] for i in range(len(s)-1)]
    for sep in ['',' ','-',',']:
        add(sep.join(str(x) for x in d)); add(sep.join(str(abs(x)) for x in d))
    c,t=[],0
    for x in s: t+=x; c.append(t)
    for sep in ['',' ',',','-']: add(sep.join(str(x) for x in c))
    # raw 32-byte keys
    v=int(j)%(1<<256)
    add(f'{v:064x}'); add(f'{v:064x}'.upper()); add(v.to_bytes(32,'little').hex())
    for pad in (j.rjust(64,'0'),j.ljust(64,'0'),j[:64],j[-64:]):
        if len(pad)==64: add(pad); add(pad.upper())
    pos=[x for x in s if x>=0]
    b1=bytes(x%256 for x in pos)
    for bb in (b1.rjust(32,b'\0'),b1.ljust(32,b'\0'),b1[:32],b1[-32:],
               b1[::-1].rjust(32,b'\0'),b1[::-1].ljust(32,b'\0')):
        if len(bb)==32: add(bb.hex()); add(bb.hex().upper())
    for w in (2,4):
        for e in ('big','little'):
            bs=b''.join((x%(1<<(8*w))).to_bytes(w,e) for x in pos)
            for bb in (bs.rjust(32,b'\0'),bs.ljust(32,b'\0'),bs[:32],bs[-32:]):
                if len(bb)==32: add(bb.hex())
    ab=j.encode()
    for bb in (ab.rjust(32,b'\0'),ab.ljust(32,b'\0'),ab[:32],ab[-32:],ab.ljust(32,b' ')):
        if len(bb)==32: add(bb.hex())

# char/word indices with the extended sequences
NORMS={'nospace':re.sub(r'\s+','',BODY),'alpha':re.sub(r'[^A-Za-z]','',BODY),
       'alnum':re.sub(r'[^A-Za-z0-9]','',BODY),'raw':BODY,
       'collapse':re.sub(r'\s+',' ',BODY).strip(),'lowalpha':re.sub(r'[^a-z]','',BODY.lower())}
WORDS=re.findall(r"[A-Za-z']+",BODY)
for n,s in SETS.items():
    if len(s)<4: continue
    for nn,txt in NORMS.items():
        for base in (0,1):
            o=''.join(txt[(x-base)%len(txt)] for x in s)
            add(o); add(o.lower()); add(o.upper()); add(o[::-1])
        c,t=[],0
        for x in s: t+=x; c.append(t)
        for base in (0,1):
            o=''.join(txt[(x-base)%len(txt)] for x in c)
            add(o); add(o.lower()); add(o[::-1])
    for base in (0,1):
        w=' '.join(WORDS[(x-base)%len(WORDS)] for x in s)
        add(w); add(w.lower()); add(w.upper()); add(w.replace(' ','')); add(w.replace(' ','').lower())
        a=''.join(WORDS[(x-base)%len(WORDS)][0] for x in s)
        add(a); add(a.lower()); add(a.upper()); add(a[::-1])

# surface forms incl. zero / first
SURF=['2008','Layer 1','Layer 1','Layer 1','Forty','1971','10years','$1','2011','$1 billion',
      '42%','20,000','100,000','six','2017','ONE','12,000','first','51%','first','$85 BILLION',
      '$2 trillion','51%','95%','near zero','first','1969','10 years']
for sep in ['',' ','-',', ','/']:
    for seq in (SURF,SURF[::-1]):
        t=sep.join(seq); add(t); add(t.lower()); add(t.upper())

seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'round5')
