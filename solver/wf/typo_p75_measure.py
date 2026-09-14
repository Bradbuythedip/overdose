"""Per-character ink measurement for page 75 (IMG_6246) to support letter-level bold calls.
Monospace typewriter face: fit pitch+offset per line using the transcript, measure ink per cell,
then compare each glyph to the median of the same glyph across regular text."""

# --- migrated to the scan: the phone photos were removed (see pages.py) ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pages as _pages
import numpy as np
from PIL import Image, ImageDraw
import json, sys, os

PAGE=_pages.page_path(75)
OUT='/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p75'
lines_txt = [
"BITCOIN IS TOXIC AF",
"Here's the bitter truth. Bitcoin was not a reaction",
"to the Global Financial Crisis of 2008. It caused it.",
"Really?          Yes.",
"The markets sensed Bitcoin was coming and started to crash.",
"Markets are like that. They discount stuff in advance. Markets are",
"the central nervous system of the global economy. They are the sum of",
"all our neuroses. The cypherpunks were publishing the white paper",
"around that time - after years of trying - and a collective panic",
"arose in the global unconscious of money printers, banking",
"terrorists, stock traders,   central bank arsonists, Wall Street",
"and Jamie Dimon. The Bitcoin rabbit hole was opening - the black hole",
"of the Cosmic Now - and it had fiat markets in its sight.",
"In fact, all the chaos you see around you these days is caused by",
"Bitcoin. And nothing could be better. Nocoiners and shitcoiners,",
"and even some Bitcoiners, consider this view toxic. Everybody's",
"complaining about \"Toxic Bitcoin Maximalists\" these days.",
"Look, toxicity is Layer 1 of the protocol.",
"Fact:          It's Layer 1 for every great thing",
"that's ever been invented or discovered.",
"It's only the language of the shameless opportunists trying",
"to cash in by riding Bitcoins coattails that give it a bad name.",
"Vitalik Buterin came up with the \"Maximalist\" epithet.",
"Now he's slinging proof of stake at the mEthereum lab.",
"Don't fall for shitcoinery.",
"Keep your dignity.",
"Go Bitcoin Toxic Maximalist,",
"the Layer 1 of the whole Satoshi experience.",
"You wouldn't be digging blindly with your bare",
"hands in the muck of Bitcoin's rabbit hole if this",
"weren't true. Anything worth hearing is hard to listen",
"to. Nice, pleasant words from con men and shitcoiners",
"are easy listening for the gullible and unloved.",
]

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
assert len(rows)==33, len(rows)

def ink_mask(band):
    """band: HxW luminance. Return boolean ink mask, handling black bars (white-on-black)."""
    H,W=band.shape
    colmed=np.median(band,axis=0)
    bar=colmed<90
    # smooth bar mask a little
    ink=np.zeros_like(band,dtype=bool)
    ink[:,~bar]=band[:,~bar]<110
    ink[:,bar]=band[:,bar]>150
    return ink,bar

results=[]
dbg=im.copy(); dr=ImageDraw.Draw(dbg)
for li,(y0,y1) in enumerate(rows):
    if li==0: continue  # stencil headline
    txt=lines_txt[li]
    band=g[y0-4:y1+4,:]
    ink,bar=ink_mask(band)
    colink=ink.sum(axis=0)
    xs=np.where(colink>0)[0]
    xs=xs[(xs>200)&(xs<1600)]
    xstart,xend=xs.min(),xs.max()
    n=len(txt)
    best=None
    # search pitch & offset: cells k: [off+k*p, off+(k+1)*p)
    for p in np.arange(18.0,20.5,0.05):
        for off in np.arange(xstart-12, xstart+2, 0.5):
            sc=0.0
            for k,ch in enumerate(txt):
                a=int(round(off+k*p)); b=int(round(off+(k+1)*p))
                s=colink[a:b].sum()
                if ch==' ': sc+=s*3
                else: sc-=min(s,60)  # reward ink where letters expected
            # penalise ink beyond last cell
            b=int(round(off+n*p)); sc+=colink[b:b+40].sum()*3
            if best is None or sc<best[0]: best=(sc,p,off)
    sc,p,off=best
    cells=[]
    for k,ch in enumerate(txt):
        a=int(round(off+k*p)); b=int(round(off+(k+1)*p))
        cell=ink[:,a:b]
        area=int(cell.sum())
        # stroke thickness proxy: area / (number of ink runs boundary) -> use area/ perimeter approx
        # perimeter approx via count of ink pixels with a non-ink 4-neighbour
        pad=np.pad(cell,1)
        edge=cell & ~(pad[:-2,1:-1]&pad[2:,1:-1]&pad[1:-1,:-2]&pad[1:-1,2:])
        per=int(edge.sum())
        cells.append(dict(k=k,ch=ch,x0=a,x1=b,area=area,per=per,bar=bool(bar[a:b].mean()>0.5)))
        if ch!=' ':
            dr.rectangle([a,y0-4,b-1,y1+4],outline=(255,0,0) if not bar[a:b].mean()>0.5 else (0,255,0))
    results.append(dict(line=li+1,text=txt,pitch=float(p),off=float(off),score=float(sc),cells=cells))
    print(f"line {li+1:2d} pitch={p:.2f} off={off:.1f} score={sc:.0f} xstart={xstart} xend={xend} n={n} predicted_end={off+n*p:.0f}")
dbg.save(f'{OUT}/cells_debug.png')
json.dump(results,open(f'{OUT}/cells.json','w'))
