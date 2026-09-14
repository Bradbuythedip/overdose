"""Per-glyph stroke-width estimate for page 79 lines (support for typography transcription).
Per line: deskew by searching the rotation that sharpens the line's ink profile, isolate the
line band, upsample 4x, label connected components, merge vertically stacked parts (i-dots),
estimate stroke width w ~= 4*mean(EDT over ink) in 1x pixels, write annotated chunks."""

# --- migrated to the scan: the phone photos were removed (see pages.py) ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pages as _pages
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage as ndi
import json

S='/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p79/'
im=Image.open(_pages.page_path(79)).convert('RGB')
rows=[(306,348),(357,394),(408,437),(458,490),(508,545),(560,596),(611,648),(665,706),(718,752),(770,803),(820,856),(873,907),(923,958),(969,1013),(1028,1060),(1079,1110),
(1301,1333),(1355,1382),(1410,1436),(1475,1510),(1529,1563),(1608,1645),(1664,1696),(1716,1752),(1768,1802)]
X0,X1=300,1600
H=48   # half-height of generous crop
Z=4
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',20)
except Exception: font=ImageFont.load_default()

def lum(arr):
    a=arr.astype(int); return (a[:,:,0]*299+a[:,:,1]*587+a[:,:,2]*114)//1000

results={}; meta={}
for i,(y0,y1) in enumerate(rows,1):
    yc=(y0+y1)//2
    big=im.crop((X0-60,yc-H-20,X1+60,yc+H+20))   # extra margin for rotation
    best=None
    for ang in np.arange(-1.5,5.01,0.25):
        r=big.rotate(ang,resample=Image.BILINEAR,fillcolor=(255,255,255))
        L=lum(np.array(r))
        prof=(L[20:-20,60:-60]<105).sum(axis=1).astype(float)
        s=np.var(prof)
        if best is None or s>best[1]: best=(ang,s)
    ang=best[0]
    r=big.rotate(ang,resample=Image.BILINEAR,fillcolor=(255,255,255)).crop((60,20,60+(X1-X0),20+2*H))
    L=lum(np.array(r))
    ink1=(L<105)
    if i in (1,2):
        bigb=ndi.binary_opening(ink1,structure=np.ones((6,6)))
        bar=ndi.binary_dilation(bigb,iterations=2)
        ink1=np.where(bar,(L>150),ink1)
    prof=ink1.sum(axis=1)
    # band: contiguous rows with ink (>2) containing the center row H (search nearest nonzero)
    c=H
    if prof[c]<=2:
        nz=np.nonzero(prof>2)[0]; c=nz[np.argmin(abs(nz-H))]
    t=c
    while t>0 and prof[t-1]>2: t-=1
    b=c
    while b<len(prof)-1 and prof[b+1]>2: b+=1
    band=(t,b)
    crop=r.resize((r.width*Z,r.height*Z),Image.LANCZOS)
    L4=lum(np.array(crop)); ink=(L4<105)
    if i in (1,2):
        bigb=ndi.binary_opening(ink,structure=np.ones((6*Z,6*Z)))
        bar=ndi.binary_dilation(bigb,iterations=2*Z)
        ink=np.where(bar,(L4>150),ink)
    lab,n=ndi.label(ink)
    comps=[]
    for k,sl in enumerate(ndi.find_objects(lab),1):
        m=(lab[sl]==k); area=m.sum()
        if area<6*Z*Z: continue
        # keep glyphs whose vertical extent lies mostly within the band (allow 3px slack)
        if sl[0].start<(band[0]-3)*Z or sl[0].stop>(band[1]+4)*Z: continue
        comps.append({'x0':sl[1].start,'x1':sl[1].stop,'y0':sl[0].start,'y1':sl[0].stop,'k':k,'area':int(area)})
    comps.sort(key=lambda c:c['x0'])
    merged=[]
    for c in comps:
        if merged:
            p=merged[-1]
            ov=min(p['x1'],c['x1'])-max(p['x0'],c['x0'])
            if ov>0.5*min(p['x1']-p['x0'],c['x1']-c['x0']):
                p['x0']=min(p['x0'],c['x0']);p['x1']=max(p['x1'],c['x1']);p['y0']=min(p['y0'],c['y0']);p['y1']=max(p['y1'],c['y1']);p['ks'].append(c['k']);p['area']+=c['area']
                continue
        c['ks']=[c['k']]; merged.append(c)
    edt=ndi.distance_transform_edt(ink)
    out=[]
    for c in merged:
        m=np.isin(lab[c['y0']:c['y1'],c['x0']:c['x1']],c['ks'])
        e=edt[c['y0']:c['y1'],c['x0']:c['x1']][m]
        out.append({'xc':round((c['x0']+c['x1'])/2/Z+X0,1),'x0':round(c['x0']/Z+X0,1),'x1':round(c['x1']/Z+X0,1),
                    'w':round(4*e.mean()/Z,2),'h':round((c['y1']-c['y0'])/Z,1),'cy0':c['y0']/Z,'cy1':c['y1']/Z,'area':c['area']})
    results[i]=out; meta[i]={'angle':float(ang),'band':band}
    for part,(px0,px1) in enumerate([(300,740),(720,1160),(1140,1600)]):
        ZZ=5
        cr=r.crop((px0-X0,band[0]-6,px1-X0,band[1]+6)).resize(((px1-px0)*ZZ,(band[1]-band[0]+12)*ZZ),Image.LANCZOS)
        ann=Image.new('RGB',(cr.width,cr.height+70),(255,255,255))
        ann.paste(cr,(0,70))
        d=ImageDraw.Draw(ann)
        j=0
        for c in out:
            if px0<=c['xc']<px1:
                w=c['w']
                col=(200,0,0) if w>=3.6 else ((0,130,0) if w<3.05 else (0,0,220))
                lx=(c['xc']-px0)*ZZ
                d.text((lx-16, 2+(30 if j%2 else 0)),'%.1f'%w,fill=col,font=font)
                d.line((lx,28+(30 if j%2 else 0),lx,70+(c['cy0']-band[0]+6)*ZZ),fill=col,width=2)
                d.rectangle(((c['x0']-px0)*ZZ,70+(c['cy0']-band[0]+6)*ZZ,(c['x1']-px0)*ZZ,70+(c['cy1']-band[0]+6)*ZZ),outline=col)
                j+=1
        ann.save(S+'ann%02d_%d.png'%(i,part))
json.dump({'glyphs':results,'meta':meta},open(S+'strokes.json','w'),indent=0)
for i in results:
    print(i,'ang=%.2f band=%s n=%d'%(meta[i]['angle'],meta[i]['band'],len(results[i])),' '.join('%.1f'%c['w'] for c in results[i]))
