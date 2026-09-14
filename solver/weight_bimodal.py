#!/usr/bin/env python3
"""Decisive test: are there TWO font weights in the body text, or one weight
plus print noise?

Method avoids both OCR and pitch fitting. Segment glyphs per line; keep ONLY the
lines where the glyph count exactly equals the non-space character count of the
transcription, which makes the letter assignment unambiguous. Then, per letter,
compare ink mass across all its instances.

Two real weights  -> per-letter distribution is BIMODAL (clear high cluster)
Print/scan noise  -> per-letter distribution is UNIMODAL
"""

# --- migrated to the scan: the phone photos were removed (see pages.py) ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pages as _pages
from PIL import Image
import numpy as np, collections, sys, statistics

THRESH = 128
PAGES = [(_pages.page_path(75),'p75',(250,1560)), (_pages.page_path(76),'p76',(250,1560)),
         (_pages.page_path(78),'p78',(250,1600)), (_pages.page_path(79),'p79',(300,1600))]

def lines_of(bw, min_h=14):
    rows = bw.sum(axis=1); on = rows > 4
    out=[]; s=None
    for i,v in enumerate(on):
        if v and s is None: s=i
        elif not v and s is not None:
            if i-s>=min_h: out.append((s,i))
            s=None
    if s is not None and len(on)-s>=min_h: out.append((s,len(on)))
    return out

def glyphs(bw,y0,y1,gap=2):
    cols = bw[y0:y1].sum(axis=0)>0
    out=[]; s=None
    for i,v in enumerate(cols):
        if v and s is None: s=i
        elif not v and s is not None: out.append((s,i)); s=None
    if s is not None: out.append((s,len(cols)))
    m=[]
    for a,b in out:
        if m and a-m[-1][1] < gap: m[-1]=(m[-1][0],b)
        else: m.append((a,b))
    return [(a,b) for a,b in m if b-a>=3]

mass = collections.defaultdict(list)
matched = 0; total = 0
for img,pg,(x0,x1) in PAGES:
    g = np.asarray(Image.open(f'/home/user/overdose/{img}').convert('L'),dtype=np.float32)[:,x0:x1]
    bw = g < THRESH
    ink = np.clip(THRESH-g,0,None)
    txt = [l.rstrip('\n') for l in open(f'transcript/{pg}.txt') if l.strip()]
    L = lines_of(bw)
    for (y0,y1) in L:
        gl = glyphs(bw,y0,y1)
        if len(gl) < 8: continue
        total += 1
        # find a transcription line whose non-space length matches exactly
        cands = [t for t in txt if len(t.replace(' ','')) == len(gl)]
        if len(cands) != 1: continue      # require an unambiguous match
        chars = cands[0].replace(' ','')
        matched += 1
        for (a,b),ch in zip(gl,chars):
            mass[ch].append(float(ink[y0:y1,a:b].sum())/ (b-a))
print(f"lines segmented={total} unambiguously matched={matched}")
print(f"letters with >=15 instances:\n")
print(f"{'ch':>3} {'n':>4} {'median':>8} {'p90/med':>8} {'max/med':>8} {'gap':>7}  verdict")
bim=0; uni=0
for ch,v in sorted(mass.items(), key=lambda kv:-len(kv[1])):
    if len(v) < 15 or not ch.isalnum(): continue
    a=np.array(sorted(v)); med=np.median(a)
    p90=np.percentile(a,90); mx=a.max()
    # largest relative jump in the upper half = evidence of a separate cluster
    half=a[len(a)//2:]
    jumps=np.diff(half)/med if len(half)>2 else np.array([0])
    gap=float(jumps.max()) if len(jumps) else 0.0
    verdict = "BIMODAL?" if gap>0.35 else "unimodal"
    if gap>0.35: bim+=1
    else: uni+=1
    print(f"{ch:>3} {len(v):>4} {med:>8.0f} {p90/med:>8.2f} {mx/med:>8.2f} {gap:>7.2f}  {verdict}")
print(f"\nletters judged bimodal: {bim}   unimodal: {uni}")
