#!/usr/bin/env python3
"""Decisive test: do heavy glyphs form contiguous, word-aligned RUNS (editorial
emphasis) or scattered singletons (a per-character cipher)?"""
exec(open('weight_bimodal.py').read().split('mass = collections.defaultdict(list)')[0])
import numpy as np, collections

recs=[]   # (page, line_text_nospace, [ratios])
per_letter=collections.defaultdict(list)
lines_kept=[]
for img,pg,(x0,x1) in PAGES:
    g = np.asarray(Image.open(f'/home/user/overdose/{img}').convert('L'),dtype=np.float32)[:,x0:x1]
    bw = g < THRESH; ink = np.clip(THRESH-g,0,None)
    txt=[l.rstrip('\n') for l in open(f'transcript/{pg}.txt') if l.strip()]
    for (y0,y1) in lines_of(bw):
        gl=glyphs(bw,y0,y1)
        if len(gl)<8: continue
        cands=[t for t in txt if len(t.replace(' ',''))==len(gl)]
        if len(cands)!=1: continue
        spaced=cands[0]
        vals=[float(ink[y0:y1,a:b].sum())/(b-a) for a,b in gl]
        med=np.median(vals)
        if med<=0: continue
        # skip highlight-bar lines (huge ink)
        if max(vals)/med > 3.0 and np.mean([v>2*med for v in vals])>0.25: continue
        lines_kept.append((spaced,vals))
        for ch,v in zip(spaced.replace(' ',''),vals): per_letter[ch].append(v)

norm={ch: np.median(v) for ch,v in per_letter.items() if len(v)>=8}
TH=1.30
runs=[]; aligned=0; total_runs=0; singles=0
bold_total=0; glyph_total=0
for spaced,vals in lines_kept:
    chars=spaced.replace(' ','')
    flags=[]
    for ch,v in zip(chars,vals):
        m=norm.get(ch)
        flags.append(bool(m and v/m>=TH))
    glyph_total+=len(flags); bold_total+=sum(flags)
    # map glyph index -> index in spaced string
    idxmap=[i for i,c in enumerate(spaced) if c!=' ']
    i=0
    while i<len(flags):
        if flags[i]:
            j=i
            while j+1<len(flags) and flags[j+1]: j+=1
            L=j-i+1; runs.append(L); total_runs+=1
            if L==1: singles+=1
            s=idxmap[i]; e=idxmap[j]
            starts_word = (s==0 or spaced[s-1]==' ')
            ends_word   = (e==len(spaced)-1 or spaced[e+1]==' ')
            if starts_word and ends_word: aligned+=1
            i=j+1
        else: i+=1
print(f"lines used: {len(lines_kept)}   glyphs: {glyph_total}   heavy: {bold_total} ({100*bold_total/glyph_total:.1f}%)")
print(f"heavy runs: {total_runs}")
c=collections.Counter(runs)
print("run-length distribution:")
for L in sorted(c): print(f"   len {L:>2}: {c[L]:>4}  {'#'*min(60,c[L])}")
print(f"\nsingle-character runs: {singles}/{total_runs} = {100*singles/max(1,total_runs):.1f}%")
print(f"runs exactly spanning whole word(s): {aligned}/{total_runs} = {100*aligned/max(1,total_runs):.1f}%")
print(f"mean run length: {np.mean(runs):.2f}")
print("""
INTERPRETATION
  cipher    -> most runs length 1, few word-aligned
  editorial -> long runs, high word-alignment""")
