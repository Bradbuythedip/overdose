#!/usr/bin/env python3
"""Read the spread as a marked-up PROOF: the strikethrough is a delete mark.
Emit the whole piece and each page with the struck run removed, in every
normalisation, plus the complement (only the struck run kept)."""
import re
RAW=open('/home/user/overdose/solver/article_transcript.txt',encoding='utf-8').read()
ST="(and 10years of watching Peter Schiff miss buying bitcoin"
pages=re.split(r'=== PAGE (\d+) \(([^)]*)\) ===', RAW)
blocks={}
for i in range(1,len(pages),3):
    blocks[f'p{pages[i]}']=pages[i+2]
keys=list(blocks); blocks['ALL']=''.join(blocks[k] for k in keys)
for n in (2,3,4,5):
    for i in range(len(keys)-n+1):
        blocks['+'.join(keys[i:i+n])]=''.join(blocks[k] for k in keys[i:i+n])
out=[]
def add(s):
    if not s: return
    s=s.strip()
    if 8<len(s)<3990 and '\n' not in s: out.append(s)
def norms(t):
    one=re.sub(r'\s+',' ',t).strip()
    yield one; yield one.lower(); yield one.upper()
    yield one.replace(' ',''); yield one.replace(' ','').lower()
    yield ''.join(c for c in one if c.isalpha())
    yield ''.join(c for c in one if c.isalpha()).lower()
    yield re.sub(r'[^A-Za-z0-9]','',one); yield re.sub(r'[^A-Za-z0-9]','',one).lower()
    yield one[::-1]; yield ' '.join(one.split()[::-1])
for name,t in blocks.items():
    flat=re.sub(r'\s+',' ',t)
    if ST in flat:
        cut=flat.replace(ST+' ','').replace(ST,'')
        for v in norms(cut): add(v)
    else:
        # pages that do not contain it still get the no-op variant once
        pass
# whole piece with the deletion, chunked to fit
allflat=re.sub(r'\s+',' ',blocks['ALL']).strip()
cut=allflat.replace(ST+' ','')
for base in (cut, cut.lower(), ''.join(c for c in cut if c.isalpha()).lower()):
    for k in (3990, 2048, 1024, 512, 256, 128, 64):
        add(base[:k]); add(base[-k:])
    for n in (2,3,4):
        L=len(base)//n
        for j in range(n): add(base[j*L:(j+1)*L])
seen=set()
for s in out:
    if s not in seen: seen.add(s); print(s)
