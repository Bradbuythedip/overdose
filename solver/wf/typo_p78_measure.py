"""Page 78: per-line pitch (autocorrelation of column ink profile) and per-glyph
stroke width (2 x 90th pct of EDT inside ink), normalized by pitch. Bars (orange/black)
handled by inverting ink inside black bars. Output: per-line glyph strings with sw/pitch."""

# --- migrated to the scan: the phone photos were removed (see pages.py) ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pages as _pages
import numpy as np
from PIL import Image
from scipy import ndimage
im=Image.open(_pages.page_path(78)).convert('RGB')
a=np.array(im).astype(float); g=a.mean(axis=2)
R,G,B=a[...,0],a[...,1],a[...,2]
rows=[(292,328),(348,378),(408,436),(460,493),(514,546),(626,662),(677,714),(734,766),(786,831),(841,882),(895,934),(950,984),(999,1041),(1056,1089),(1164,1200),(1219,1253),(1271,1302),(1323,1361),(1438,1484),(1493,1540),(1557,1591),(1610,1640)]
lines=open('/home/user/overdose/solver/article_transcript.txt').read().split('=== PAGE 78 (IMG_6249) ===')[1].split('=== PAGE 79')[0].strip('\n').split('\n')
lines=[l for l in lines if l.strip()]
X0,X1=230,1580
for li,(y0,y1) in enumerate(rows):
    band=g[y0-5:y1+5,X0:X1]; bR=R[y0-5:y1+5,X0:X1]; bB=B[y0-5:y1+5,X0:X1]
    # black bar: column median very dark
    colmed=np.median(band,axis=0); bar=colmed<90; bar=ndimage.binary_closing(bar,iterations=4)
    ink=np.zeros_like(band,dtype=bool)
    ink[:,~bar]=band[:,~bar]<110
    ink[:,bar]=band[:,bar]>150
    # kill specks
    lab,n=ndimage.label(ink); sz=ndimage.sum(ink,lab,range(1,n+1))
    for i,s in enumerate(sz):
        if s<5: ink[lab==i+1]=False
    prof=ink.sum(axis=0).astype(float); prof-=prof.mean()
    ac=np.correlate(prof,prof,mode='full')[len(prof)-1:]
    ac/=ac[0]
    lo,hi=14,30; pk=lo+int(np.argmax(ac[lo:hi]))
    # refine with parabolic interp
    y_1,y0_,y1_=ac[pk-1],ac[pk],ac[pk+1]; pitch=pk+0.5*(y_1-y1_)/(y_1-2*y0_+y1_)
    edt=ndimage.distance_transform_edt(ink)
    # glyph segmentation by column runs
    colink=ink.sum(axis=0); runs=[]; inr=False
    for x,v in enumerate(colink):
        if v>0 and not inr: s=x; inr=True
        elif v==0 and inr: inr=False; runs.append([s,x])
    if inr: runs.append([s,len(colink)])
    merged=[]
    for r in runs:
        if merged and r[0]-merged[-1][1]<=1: merged[-1][1]=r[1]
        else: merged.append(r)
    segs=[]
    for a_,b_ in merged:
        w=b_-a_; k=max(1,int(round(w/(pitch*0.72))))
        if w>pitch*1.05 and k>1:
            step=w/k; segs+= [[int(round(a_+j*step)),int(round(a_+(j+1)*step))] for j in range(k)]
        else: segs.append([a_,b_])
    txt=lines[li]; chars=[c for c in txt if c!=' ']
    vals=[]
    for s,e in segs:
        m=ink[:,s:e]; d=edt[:,s:e][m]
        if d.size<3: vals.append(None); continue
        vals.append(2*np.percentile(d,90))
    out=[]
    ok=len(segs)==len(chars)
    for i,(s,e) in enumerate(segs):
        c=chars[i] if ok and i<len(chars) else '?'
        v=vals[i]; out.append(f'{c}{v/pitch*10:.1f}' if v else f'{c}--')
    print(f'L{li+1:2d} pitch={pitch:5.2f} nseg={len(segs)} nch={len(chars)} {"OK" if ok else "MISMATCH"}')
    print('   ',' '.join(out))
