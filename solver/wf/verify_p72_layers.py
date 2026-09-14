#!/usr/bin/env python3
"""Independent check: which of page 72's printed elements have zero ink in the
three 1-bit CCITT separations, and which survive only in the 200 dpi JPEG."""
import io, numpy as np, pymupdf
from PIL import Image
from scipy import ndimage as ndi

PDF='/home/user/overdose/solver/scan/Scan1.pdf'
S=400/72.0; W,H=3400,4400
d=pymupdf.open(PDF); p=d[1]                      # pdf page idx 1 == printed 72
info={im['xref']:im for im in p.get_image_info(xrefs=True)}

# --- 1-bit separations.  These are /ImageMask + CCITTFaxDecode; pymupdf hands
# them back as 1-bit PNGs in which WHITE (255) is the painted ink.
lay={}
for x in (17,18,19):
    a=np.array(Image.open(io.BytesIO(d.extract_image(x)['image'])).convert('L'))
    ink=a>=128
    x0,y0,x1,y1=[v*S for v in info[x]['bbox']]
    tw,th=int(round(x1-x0)),int(round(y1-y0))
    r=np.array(Image.fromarray((ink*255).astype(np.uint8)).resize((tw,th),Image.NEAREST))>127
    c=np.zeros((H,W),bool); ox,oy=int(round(x0)),int(round(y0)); c[oy:oy+th,ox:ox+tw]=r
    lay[x]=c
    print(f'xref {x}: {a.shape[1]}x{a.shape[0]}, native ink {ink.mean()*100:.2f}%, placed ({ox},{oy}) {tw}x{th}')
comp=lay[17]|lay[18]|lay[19]

# --- 200 dpi colour layer, native and on the 400 dpi canvas
Ln=np.array(Image.open(io.BytesIO(d.extract_image(16)['image'])).convert('L'))
Lc=np.array(Image.open(io.BytesIO(d.extract_image(16)['image'])).convert('RGB')
            .resize((W,H),Image.LANCZOS).convert('L'))
print(f'\nx16 native {Ln.shape[1]}x{Ln.shape[0]}, paper median L={np.median(Ln):.0f}, page min L={Ln.min()}')

# --- blind segmentation: union of both layers, then block into elements
u=comp|(Lc<120)
dd=ndi.binary_dilation(ndi.binary_dilation(u,np.ones((1,61))),np.ones((25,1)))
lab,n=ndi.label(dd)
print(f'\n{"box (400dpi canvas)":<30}{"mask%":>8}{"colour minL":>12}   verdict')
zeros=[]
for i,sl in enumerate(ndi.find_objects(lab),1):
    ys,xs=sl
    if (xs.stop-xs.start)*(ys.stop-ys.start)<3000: continue
    mk=comp[sl].mean()*100; mn=int(Lc[sl].min())
    v='COLOUR-LAYER ONLY' if mk<0.01 else ('mask' if mn>180 else 'both')
    if mk<0.01: zeros.append((xs.start,ys.start,xs.stop,ys.stop))
    print(f'{str((xs.start,ys.start,xs.stop,ys.stop)):<30}{mk:8.2f}{mn:12d}   {v}')

# --- named elements, per separation, plus native-resolution levels
BOX={'Sources:':(2760,520,2920,575),'footerL URLs':(1600,310,2935,520),
     'folio 72':(118,169,238,240),'$14.5':(1855,855,2145,960),
     'ctl footerR URLs':(422,320,1510,538),'ctl BILLION BY 2019':(1049,858,1858,958),
     'ctl 165 numerals':(1845,3693,2030,3768),'ctl 572 numerals':(920,3691,1105,3767)}
print(f'\n{"element":<21}{"x17%":>8}{"x18%":>8}{"x19%":>8}{"native minL":>12}{"p5":>7}')
for k,(x0,y0,x1,y1) in BOX.items():
    b=Ln[y0//2:y1//2, x0//2:x1//2]
    print(f'{k:<21}'+''.join(f'{lay[x][y0:y1,x0:x1].mean()*100:8.2f}' for x in (17,18,19))
          +f'{b.min():12d}{np.percentile(b,5):7.1f}')

# --- how much of the colour layer's ink is those four elements
m=Ln[40:2160,40:1600].copy()
for k,(x0,y0,x1,y1) in BOX.items():
    if k.startswith('ctl'): continue
    m[max(0,y0//2-40):y1//2-40, max(0,x0//2-40):x1//2-40]=255
print(f'\ncolour layer min L, inner page          = {Ln[40:2160,40:1600].min()}')
print(f'colour layer min L, those 4 boxes blanked = {m.min()}')
