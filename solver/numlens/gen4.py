#!/usr/bin/env python3
"""Round 3: dates, line/acrostic indices, spelled-out English, curve-order reductions."""
import re, sys, functools, operator, itertools
N_CURVE = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
lines=[l for l in RAW.split('\n') if not l.startswith('#')]
page,pages,body=None,{},[]
for l in lines:
    m=re.match(r'=== PAGE (\d+)',l)
    if m: page=int(m.group(1)); pages[page]=[]; continue
    if page is not None: pages[page].append(l); body.append(l)
BODY='\n'.join(body)
BLINES=[l for l in body if l.strip()]
WORDS=re.findall(r"[A-Za-z']+",BODY)
SENTS=[s.strip() for s in re.split(r'(?<=[.!?])\s+',re.sub(r'\s+',' ',BODY)) if s.strip()]

P  = [2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
B  = [2008,1971,40,10,1,2011,1,42,20000,100000,6,12000,2017,51,85,2,51,95,1969,10]
NL = [2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
NU = [2008,1,1,1,1971,10,1,2011,1,42,20000,100000,2017,12000,51,85,2,51,95,1969,10]
EX = [2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
      85000000000,2000000000000,51,95,1969,10]
SETS={'P':P,'B':B,'NL':NL,'NU':NU,'EX':EX,
      'YR':[2008,1971,2011,2017,1969],'PC':[42,51,51,95],'DL':[1,1,85,2],
      'SMALL':[1,1,1,40,10,1,1,42,6,51,85,2,51,95,10],
      'WORDQ':[40,6,1000000000,1000000000000]}
out=[]
def add(s):
    if s is None: return
    s=str(s)
    if s and len(s)<3900: out.append(s)

# --- acrostic / structural indices ---
for n,s in SETS.items():
    pos=[x for x in s if x>0]
    for base in (0,1):
        # first letter of the Nth word
        t=''.join(WORDS[(x-base)%len(WORDS)][0] for x in pos)
        add(t); add(t.lower()); add(t.upper()); add(t[::-1])
        # first letter of the Nth line
        t=''.join(BLINES[(x-base)%len(BLINES)].strip()[0] for x in pos if BLINES[(x-base)%len(BLINES)].strip())
        add(t); add(t.lower()); add(t[::-1])
        # Nth line, whole
        add(' '.join(BLINES[(x-base)%len(BLINES)].strip() for x in pos))
        # first letter of the Nth sentence
        t=''.join(SENTS[(x-base)%len(SENTS)][0] for x in pos)
        add(t); add(t.lower()); add(t[::-1])
        # Nth word of each page's word list
        for pn,pl in pages.items():
            pw=re.findall(r"[A-Za-z']+",'\n'.join(pl))
            if not pw: continue
            add(' '.join(pw[(x-base)%len(pw)] for x in pos))
            add(''.join(pw[(x-base)%len(pw)][0] for x in pos))
    # stepping cipher: walk the text taking steps from the sequence, cycling
    for txt in (re.sub(r'[^A-Za-z]','',BODY), re.sub(r'\s+','',BODY), BODY):
        for start in (0,1):
            i=start; o=[]
            for k in range(60):
                i+= pos[k%len(pos)]
                if i>=len(txt): i%=len(txt)
                o.append(txt[i])
            t=''.join(o); add(t); add(t.lower()); add(t[:len(pos)]); add(t[:len(pos)].lower())

# --- dates ---
DATES=['20090103','03012009','19710815','08151971','19690325','03251969','25031969',
       '20110101','20170801','08012017','19690601','20210907','09072021','20081031',
       '31102008','10312008','2008-10-31','2009-01-03','1971-08-15','1969-03-25']
for d in DATES:
    add(d); add(d[::-1])
    for e in DATES:
        if d!=e:
            add(d+e); add(d+'-'+e)
for v in (20090103,19710815,19690325,20081031,20210907):
    add(f'{v:064x}'); add(str(v))

# --- spelled-out English ---
ONES=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven',
      'twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen']
TENS=['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']
def spell(n):
    if n<20: return ONES[n]
    if n<100: return TENS[n//10]+('' if n%10==0 else ' '+ONES[n%10])
    if n<1000: return ONES[n//100]+' hundred'+('' if n%100==0 else ' '+spell(n%100))
    if n<10**6: return spell(n//1000)+' thousand'+('' if n%1000==0 else ' '+spell(n%1000))
    if n<10**9: return spell(n//10**6)+' million'+('' if n%10**6==0 else ' '+spell(n%10**6))
    if n<10**12: return spell(n//10**9)+' billion'+('' if n%10**9==0 else ' '+spell(n%10**9))
    return spell(n//10**12)+' trillion'+('' if n%10**12==0 else ' '+spell(n%10**12))
for n,s in SETS.items():
    for seq in (s,s[::-1]):
        for sep in [' ','','-',', ']:
            t=sep.join(spell(x) for x in seq if x>=0)
            add(t); add(t.upper()); add(t.title())
    # years read as "nineteen seventy one"
    def yr(v):
        return spell(v//100)+' '+(spell(v%100) if v%100 else 'hundred') if 1000<=v<2100 else spell(v)
    for sep in [' ','-']:
        t=sep.join(yr(x) for x in seq if x>=0); add(t); add(t.upper())

# --- curve-order and modular reductions ---
for n,s in SETS.items():
    j=''.join(str(x) for x in s); v=int(j)
    for m in (N_CURVE, 1<<256, 1<<160, 10**77):
        r=v%m
        if 0<r<N_CURVE: add(f'{r:064x}'); add(f'{r:064x}'.upper())
    tot=sum(s); prod=functools.reduce(operator.mul,[x for x in s if x],1)
    for r in (tot,prod%N_CURVE,(v*v)%N_CURVE,pow(v,2,N_CURVE),v%N_CURVE):
        if 0<r<N_CURVE: add(f'{r:064x}')
    add(str(tot)); add(str(prod))

# --- 20000/100000 pairing and 51/42/95 arithmetic ---
for a,b in [(20000,100000),(100000,20000)]:
    for op,nm in [(operator.add,'+'),(operator.sub,'-'),(operator.mul,'*')]:
        r=op(a,b); add(str(r)); add(f'{abs(r):064x}')
    add(str(b//a)); add(f'{a}{b}'); add(f'{a}:{b}'); add(f'{a}/{b}'); add(f'{a}-{b}')
for c in itertools.permutations([51,42,95,51]):
    add(''.join(str(x) for x in c))
for r in (51*51, 51+51, 42*95, 51*42*95, 51+42+95, 5151, 2601, 21000000-20, 21000000//20):
    add(str(r)); add(f'{r:064x}')

# --- counts / meta ---
for c in (20,21,23,27,19,5,4,2):
    add(str(c)); add(f'{c:064x}')
add('23 numbers'); add('21 numbers'); add('20 BTC'); add('20BTC')

seen,fin=set(),[]
for x in out:
    x=x.strip()
    if x and x not in seen: seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin),'round3')
