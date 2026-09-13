"""Segment glyphs by column-projection runs and match to transcript; measure ink area & stroke width."""
import numpy as np
from PIL import Image, ImageDraw
import json
from scipy import ndimage
exec(open('/home/user/overdose/solver/wf/typo_p75_measure.py').read().split("im=Image.open(PAGE)")[0])  # reuse lines_txt, paths

im=Image.open(PAGE).convert('RGB')
g=np.array(im.convert('L')).astype(float)
col=g[:,230:1530]
dark=(col<120).sum(axis=1)
rows=[]; inrun=False
for y,v in enumerate(dark):
    if v>4 and not inrun: start=y; inrun=True
    elif v<=4 and inrun:
        inrun=False
        if y-start>8: rows.append((start,y))

def ink_mask(band):
    colmed=np.median(band,axis=0)
    bar=colmed<90
    bar=ndimage.binary_closing(bar,iterations=3)
    ink=np.zeros_like(band,dtype=bool)
    ink[:,~bar]=band[:,~bar]<115
    ink[:,bar]=band[:,bar]>150
    return ink,bar

PITCH=18.9
out=[]
dbg=im.copy(); dr=ImageDraw.Draw(dbg)
for li,(y0,y1) in enumerate(rows):
    if li==0: continue
    txt=lines_txt[li]
    chars=[c for c in txt if c!=' ']
    band=g[y0-4:y1+4,:]
    ink,bar=ink_mask(band)
    ink[:, :200]=False; ink[:,1600:]=False
    # remove tiny specks
    lab,nl=ndimage.label(ink)
    sizes=ndimage.sum(ink,lab,range(1,nl+1))
    for i,s in enumerate(sizes):
        if s<6: ink[lab==i+1]=False
    colink=ink.sum(axis=0)
    runs=[]; inrun=False
    for x,v in enumerate(colink):
        if v>0 and not inrun: s=x; inrun=True
        elif v==0 and inrun:
            inrun=False; runs.append([s,x])
    if inrun: runs.append([s,len(colink)])
    # merge runs separated by <=1 px
    merged=[]
    for r in runs:
        if merged and r[0]-merged[-1][1]<=1: merged[-1][1]=r[1]
        else: merged.append(r)
    runs=merged
    # split wide runs (touching glyphs)
    segs=[]
    for a,b in runs:
        w=b-a
        k=max(1,int(round(w/ (PITCH*0.72))))  # glyph ink width ~ 0.7 pitch
        if w>PITCH*1.05 and k>1:
            step=w/k
            for j in range(k): segs.append([int(round(a+j*step)),int(round(a+(j+1)*step))])
        else: segs.append([a,b])
    # apostrophes/quotes/periods/commas are narrow; 'i' dots separate? (dot joins stem usually via label? no: dot is separate component but same columns) fine.
    out.append(dict(line=li+1,text=txt,nchars=len(chars),nsegs=len(segs),segs=segs))
    flag='' if len(segs)==len(chars) else '  <-- MISMATCH'
    print(f"line {li+1:2d}: chars={len(chars)} segs={len(segs)}{flag}")
    for a,b in segs:
        dr.rectangle([a,y0-4,b-1,y1+4],outline=(255,0,0))
dbg.save(f'{OUT}/segs_debug.png')
json.dump(out,open(f'{OUT}/segs.json','w'))
