#!/usr/bin/env python3
"""Curated high-priority number-lens strings for the full HD stack."""
import re, sys, functools, operator, itertools
RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
lines = [l for l in RAW.split('\n') if not l.startswith('#')]
page, pages, body = None, {}, []
for l in lines:
    m = re.match(r'=== PAGE (\d+)', l)
    if m: page=int(m.group(1)); pages[page]=[]; continue
    if page is not None: pages[page].append(l); body.append(l)
BODY='\n'.join(body)

P  = [2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
B  = [2008,1971,40,10,1,2011,1,42,20000,100000,6,12000,2017,51,85,2,51,95,1969,10]
NL = [2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
NU = [2008,1,1,1,1971,10,1,2011,1,42,20000,100000,2017,12000,51,85,2,51,95,1969,10]
EX = [2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
      85000000000,2000000000000,51,95,1969,10]
YR = [2008,1971,2011,2017,1969]; PC=[42,51,51,95]; DL=[1,1,85,2]
SETS = {'P':P,'B':B,'NL':NL,'NU':NU,'EX':EX,'YR':YR,'PC':PC,'DL':DL}

out=[]
def add(s):
    if s and len(str(s))<3900: out.append(str(s))

for n,s in SETS.items():
    for seq in (s, s[::-1]):
        for sep in ['',' ','-',',','.','/',':','_','+']:
            add(sep.join(str(x) for x in seq))
    j=''.join(str(x) for x in s)
    add(j[::-1]); add('0x'+j)
    tot=sum(s); prod=functools.reduce(operator.mul,[x for x in s if x],1)
    add(tot); add(str(tot)[::-1]); add(prod); add(prod%(1<<256))
    add(functools.reduce(operator.xor,[abs(x) for x in s],0))
    add(sum(int(c) for c in j))
    d=[s[i+1]-s[i] for i in range(len(s)-1)]
    for sep in ['',' ','-',',']:
        add(sep.join(str(x) for x in d)); add(sep.join(str(abs(x)) for x in d))
    c,t=[],0
    for x in s: t+=x; c.append(t)
    for sep in ['',' ',',','-']: add(sep.join(str(x) for x in c))
    # 64-hex raw keys
    v=int(j)%(1<<256)
    add(f'{v:064x}'); add(f'{v:064x}'.upper()); add(v.to_bytes(32,'little').hex())
    for pad in (j.rjust(64,'0'), j.ljust(64,'0'), j[:64], j[-64:]):
        if len(pad)==64: add(pad); add(pad.upper())
    pos=[x for x in s if x>=0]
    b1=bytes(x%256 for x in pos)
    for bb in (b1.rjust(32,b'\0'),b1.ljust(32,b'\0'),b1[::-1].rjust(32,b'\0'),b1[::-1].ljust(32,b'\0')):
        if len(bb)==32: add(bb.hex()); add(bb.hex().upper())
    for w in (2,4):
        for e in ('big','little'):
            bs=b''.join((x%(1<<(8*w))).to_bytes(w,e) for x in pos)
            for bb in (bs.rjust(32,b'\0'),bs.ljust(32,b'\0'),bs[:32],bs[-32:]):
                if len(bb)==32: add(bb.hex())
    ab=j.encode()
    for bb in (ab.rjust(32,b'\0'),ab.ljust(32,b'\0'),ab[:32],ab[-32:],ab.ljust(32,b' ')):
        if len(bb)==32: add(bb.hex())

# printed surface forms
SURF=['2008','1','1','1','Forty','1971','10','1','2011','1 billion','42','20,000','100,000',
      'six','2017','12,000','51','85','2','51','95','1969','10']
SURF2=['2008','Forty','1971','10years','$1','2011','$1 billion','42%','20,000','100,000','six',
       '2017','12,000','51%','$85 BILLION','$2 trillion','51%','95%','1969','10 years']
for src in (SURF,SURF2):
    for sep in ['',' ','-',', ','/']:
        for seq in (src, src[::-1]):
            s=sep.join(seq); add(s); add(s.lower()); add(s.upper())

# character indices into the article
NORMS={'raw':BODY,'nospace':re.sub(r'\s+','',BODY),'alpha':re.sub(r'[^A-Za-z]','',BODY),
       'alnum':re.sub(r'[^A-Za-z0-9]','',BODY),
       'collapse':re.sub(r'\s+',' ',BODY).strip(),'lowalpha':re.sub(r'[^a-z]','',BODY.lower())}
for pn,pl in pages.items(): NORMS[f'p{pn}']=re.sub(r'[^A-Za-z]','','\n'.join(pl))
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

# striking standalone
for a in ['51','42','95','21000000','21,000,000','20000','100000','20,000','100,000','5142',
          '425195','954251','51425195','204251','2151','4251']:
    add(a); add(a*2); add(a[::-1])
for p in itertools.permutations(['51','42','95']):
    for sep in ['',' ','-','/',':']: add(sep.join(p))
for v in (51,42,95,21000000,20000,100000,5142,425195,51425195,2000000000000,85000000000):
    add(f'{v:064x}'); add(v.to_bytes(32,'little').hex()); add(str(v))
add('20000100000'); add('10000020000'); add('20,000 100,000'); add('100,000 20,000')

# keyword + sequence
for k in ['Overdose','overdose','MaxKeiser','Max Keiser','Bitcoin','bitcoin','ElSalvador',
          'El Salvador','Layer1','Satoshi','VolcanoBonds','Stacy']:
    for n in ('P','B','NL','YR','PC'):
        j=''.join(str(x) for x in SETS[n]); js=' '.join(str(x) for x in SETS[n])
        add(k+j); add(j+k); add(k+' '+js); add(js+' '+k); add(k+'-'+j)

seen,fin=set(),[]
for x in out:
    x=str(x).strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'curated')
