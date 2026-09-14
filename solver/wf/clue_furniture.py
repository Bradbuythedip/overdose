#!/usr/bin/env python3
"""
FURNITURE lens -- measure every non-body element on the 8 scanned pages of
solver/scan/Scan1.pdf (printed pages 72-79) and settle the physical structure
of the sheets.

    python3 wf/clue_furniture.py all          # everything below
    python3 wf/clue_furniture.py survey       # placed-image inventory
    python3 wf/clue_furniture.py streams      # content-stream stencils + fills
    python3 wf/clue_furniture.py runhead      # running heads
    python3 wf/clue_furniture.py strips       # the six OVERDOSE bitmaps compared
    python3 wf/clue_furniture.py folio        # page numbers
    python3 wf/clue_furniture.py sidebar      # rotated issue slug + direction
    python3 wf/clue_furniture.py edges        # which edge is torn (binding side)
    python3 wf/clue_furniture.py leaf         # recto/verso + leaf pairing

COORDINATES.  The PDF stores every sheet upside down (MediaBox 612x792,
/Rotate 0, content 180 deg).  Everything here is reported in the PRINTED page
frame: origin top-left of the page as read, units = points (1/72 in).
Conversion from a PDF-frame rect (x,y,w,h with PDF's bottom-left origin):
    printed_x = 612 - (x + w)          printed_y_from_top = y
"""
import argparse, os, re, sys, io
import pymupdf
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "scan", "Scan1.pdf")
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
INV = {v: k for k, v in PAGE_MAP.items()}
W_PT, H_PT = 612.0, 792.0
PAGES = sorted(INV)


def printed_rect(r):
    return (W_PT - r.x1, H_PT - r.y1, W_PT - r.x0, H_PT - r.y0)


_cache = {}
def render(pr, dpi=400):
    """PIL RGB image of printed page `pr` in READING orientation."""
    k = (pr, dpi)
    if k in _cache:
        return _cache[k]
    d = pymupdf.open(PDF)
    pg = d[INV[pr]]
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72))
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).rotate(180)
    _cache[k] = im
    return im


# ------------------------------------------------------------------ 1 survey
def survey():
    print("== placed images, printed frame ==")
    d = pymupdf.open(PDF)
    for pr in PAGES:
        pg = d[INV[pr]]
        print(f"\n-- printed page {pr} (pdf index {INV[pr]}) --")
        for info in pg.get_images(full=True):
            xref, w, h, bpc = info[0], info[2], info[3], info[4]
            for r in pg.get_image_rects(xref):
                x0, y0, x1, y1 = printed_rect(r)
                print(f"   xref {xref:3d} {w:5d}x{h:5d} bpc={bpc} "
                      f"x[{x0:6.1f},{x1:6.1f}] y[{y0:6.1f},{y1:6.1f}] "
                      f"({x1-x0:6.1f} x {y1-y0:6.1f} pt) dpi={w/((r.x1-r.x0)/72):.0f}")


# ----------------------------------------------------------------- 2 streams
CM = re.compile(
    r"q\s+((?:[\d.]+\s+){1,3}(?:rg|g))\s+([\d.]+)\s+0\s+0\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+cm\s*/(\w+)\s+Do\s+Q")

def streams():
    """Every stencil the scanner emitted, with the flat fill colour it painted
    it in.  These RGBs are exact numbers stored in the file -- no thresholding,
    no JPEG blur."""
    print("== content-stream stencils: exact fill colours ==")
    d = pymupdf.open(PDF)
    for pr in PAGES:
        pg = d[INV[pr]]
        cs = pg.read_contents().decode("latin-1")
        mode = "TEXTOFF" if "TEXTOFF" in cs else ("TEXTON" if "TEXTON" in cs else "?")
        print(f"\n-- printed page {pr}: scanner mode {mode}, stream {len(cs)} bytes --")
        for col, w, h, tx, ty, obj in CM.findall(cs):
            parts = col.split()
            if parts[-1] == "g":
                v = float(parts[0]); rgb = (v, v, v)
            else:
                rgb = tuple(float(p) for p in parts[:3])
            w, h, tx, ty = map(float, (w, h, tx, ty))
            px = W_PT - (tx + w)
            print(f"   /{obj:<7s} {w:7.2f} x {h:6.2f} pt at printed x{px:7.2f} y{ty:7.2f}"
                  f"   fill = ({rgb[0]*255:5.1f},{rgb[1]*255:5.1f},{rgb[2]*255:5.1f})")


# ----------------------------------------------------------------- 3 runhead
RH_WIN = {72: (505, 600), 73: (40, 110), 74: (505, 580), 75: (40, 110),
          76: (500, 580), 77: (40, 110), 78: (505, 580), 79: (40, 96)}

def runhead(dpi=400):
    print("== running head, window y 41-51 pt ==")
    S = dpi / 72.0
    for pr in PAGES:
        x0, x1 = RH_WIN[pr]
        im = render(pr, dpi)
        g = np.asarray(im.convert("L")).astype(int)
        rgb = np.asarray(im).astype(int)
        sg = g[int(41*S):int(51*S), int(x0*S):int(x1*S)]
        sr = rgb[int(41*S):int(51*S), int(x0*S):int(x1*S)]
        paper = np.median(sg)
        m = (sg > paper + 45) if pr == 77 else (sg < paper - 45)
        ys, xs = np.where(m)
        med = np.median(sr[m], axis=0)
        outer = (x0 + xs.min()/S) if pr % 2 else (W_PT - (x0 + xs.max()/S))
        print(f"  p{pr}  x[{x0+xs.min()/S:6.2f},{x0+xs.max()/S:6.2f}] "
              f"y[{41+ys.min()/S:5.2f},{41+ys.max()/S:5.2f}]  "
              f"w={(xs.max()-xs.min()+1)/S:5.2f} cap={(ys.max()-ys.min()+1)/S:4.2f}pt "
              f"medRGB={tuple(int(v) for v in med)}  offset-from-outer-edge={outer:5.2f}pt")


# ------------------------------------------------------------------- 4 folio
def folio(dpi=400):
    print("== page number, window y 744-768 pt, both outer corners ==")
    S = dpi / 72.0
    for pr in PAGES:
        im = render(pr, dpi)
        g = np.asarray(im.convert("L")).astype(int)
        rgb = np.asarray(im).astype(int)
        hit = False
        for nm, (x0, x1) in (("LEFT ", (20, 72)), ("RIGHT", (558, 600))):
            sg = g[int(744*S):int(768*S), int(x0*S):int(x1*S)]
            sr = rgb[int(744*S):int(768*S), int(x0*S):int(x1*S)]
            paper = np.median(sg)
            best = None
            for t in (40, 55, 70, 85, 100):      # p72's hatched stock needs more
                m = (sg > paper + t) if pr == 77 else (sg < paper - t)
                ys, xs = np.where(m)
                if len(xs) < 400:
                    continue
                w = (xs.max()-xs.min()+1)/S; h = (ys.max()-ys.min()+1)/S
                if 7 < w < 14 and 7 < h < 11:     # a two-digit folio
                    best = (m, ys, xs, w, h, t); break
            if best is None:
                continue
            m, ys, xs, w, h, t = best
            hit = True
            med = np.median(sr[m], axis=0)
            print(f"  p{pr} {nm} x[{x0+xs.min()/S:6.2f},{x0+xs.max()/S:6.2f}] "
                  f"y[{744+ys.min()/S:6.2f},{744+ys.max()/S:6.2f}] w={w:5.2f} cap={h:4.2f}pt "
                  f"medRGB={tuple(int(v) for v in med)} n={len(xs)} thr={t}")
        if not hit:
            print(f"  p{pr} ** NO FOLIO in either bottom corner **")


# ----------------------------------------------------------------- 5 sidebar
SB_WIN = {72: (580, 604), 74: (586, 600), 76: (580, 604), 78: (580, 604),
          73: (18, 38), 75: (17, 37), 77: (16, 36), 79: (20, 40)}

def sidebar(dpi=400, save=None):
    print('== rotated slug "Bitcoin Magazine | El Salvador", window y 335-475 pt ==')
    S = dpi / 72.0
    crops = {}
    for pr in PAGES:
        x0, x1 = SB_WIN[pr]
        im = render(pr, dpi)
        g = np.asarray(im.convert("L")).astype(int)
        rgb = np.asarray(im).astype(int)
        sg = g[int(335*S):int(475*S), int(x0*S):int(x1*S)]
        sr = rgb[int(335*S):int(475*S), int(x0*S):int(x1*S)]
        m = (sg > 170) if pr in (74, 77) else (sg < 170)
        ys, xs = np.where(m)
        med = np.median(sr[m], axis=0)
        y0p, y1p = 335 + ys.min()/S, 335 + ys.max()/S
        print(f"  p{pr} edge={'RIGHT' if pr%2==0 else 'LEFT '} "
              f"x[{x0+xs.min()/S:6.2f},{x0+xs.max()/S:6.2f}] y[{y0p:6.2f},{y1p:6.2f}] "
              f"len={y1p-y0p:6.2f}pt medRGB={tuple(int(v) for v in med)}")
        crops[pr] = im.crop((int((x0+xs.min()/S-1)*S), int((y0p-2)*S),
                             int((x0+xs.max()/S+1)*S), int((y1p+2)*S))).convert("L")
        if save:
            crops[pr].rotate(90 if pr % 2 else -90, expand=True).save(
                os.path.join(save, f"sidebar_{pr}.png"))
    ref = np.asarray(crops[73].rotate(90, expand=True).resize((700, 64))).astype(float)
    ref = (ref - ref.mean()) / ref.std()
    print("\n  reading direction -- normalised correlation against p73 rotated CCW:")
    for pr in PAGES:
        o = {}
        for nm, ang in (("ccw", 90), ("cw", -90)):
            a = np.asarray(crops[pr].rotate(ang, expand=True).resize((700, 64))).astype(float)
            if pr in (74, 77):
                a = 255 - a
            a = (a - a.mean()) / (a.std() + 1e-9)
            o[nm] = float((a * ref).mean())
        b = max(o, key=o.get)
        print(f"   p{pr}: ccw={o['ccw']:+.3f} cw={o['cw']:+.3f} -> reads "
              f"{'TOP-TO-BOTTOM' if b == 'ccw' else 'BOTTOM-TO-TOP'}")


# ------------------------------------------------------------------- 6 edges
def edges(dpi=400, save=None):
    """The binding edge is torn; the scanner's own 1-bit separation isolates
    the ragged fringe as a tall thin region on exactly one side."""
    print("== torn (binding) edge vs clean (trimmed) edge ==")
    d = pymupdf.open(PDF)
    for pr in PAGES:
        pg = d[INV[pr]]
        marks = []
        for info in pg.get_images(full=True):
            xref, w, h = info[0], info[2], info[3]
            for r in pg.get_image_rects(xref):
                x0, y0, x1, y1 = printed_rect(r)
                wpt, hpt = x1 - x0, y1 - y0
                if wpt < 20 and hpt > 30 and (x0 < 20 or x1 > W_PT - 20):
                    marks.append((xref, "LEFT" if x0 < 20 else "RIGHT",
                                  round(x0, 1), round(x1, 1), round(y0, 1), round(y1, 1)))
        if marks:
            side = marks[0][1]
            print(f"  p{pr}: scanner isolated {len(marks)} ragged-edge strip(s) on the "
                  f"{side}: " + ", ".join(f"xref{m[0]} x[{m[2]},{m[3]}] y[{m[4]},{m[5]}]" for m in marks))
        else:
            print(f"  p{pr}: no isolated edge strip (tear too shallow / no mask)")
        if save:
            im = render(pr, dpi); S = dpi / 72.0
            L = im.crop((0, int(120*S), int(24*S), int(680*S)))
            R = im.crop((int(588*S), int(120*S), int(612*S), int(680*S)))
            c = Image.new("RGB", (L.width + R.width + 20, L.height), (255, 0, 0))
            c.paste(L, (0, 0)); c.paste(R, (L.width + 20, 0))
            c.rotate(-90, expand=True).save(os.path.join(save, f"edges_{pr}.png"))


# -------------------------------------------------------------------- 7 leaf
def leaf():
    print("== physical structure ==")
    print("""
  Every page carries its running head, its folio (7 of 8 -- page 77 has none)
  and its rotated issue slug on ONE edge, and the torn binding fringe on the
  other:

      page   furniture edge    torn (binding) edge
        72       RIGHT               LEFT
        73       LEFT                RIGHT
        74       RIGHT               LEFT
        75       LEFT                RIGHT
        76       RIGHT               LEFT
        77       LEFT                RIGHT
        78       RIGHT               LEFT
        79       LEFT                RIGHT

  Folios, running heads and edge slugs sit in the OUTER margin, never the
  gutter.  So the EVEN pages are right-hand pages (rectos) and the ODD pages
  are left-hand pages (versos) -- the reverse of the ordinary convention.

  A leaf is recto + the verso on its back, i.e. (even, even+1):

      leaves  :  72|73     74|75     76|77     78|79
      spreads :  71-72     73-74     75-76     77-78     79-80

  This inverts window/outside_the_box.md (which superimposed 73/74, 75/76 and
  77/78 as leaves -- those are the facing spreads) and window/page71.md (which
  made 71|72 a leaf -- they face each other).
""")


# ------------------------------------------------------------------ 8 strips
RH_XREF = {73: 8, 74: 27, 75: 38, 76: 51, 78: 78, 79: 66}

def strips():
    """The six OVERDOSE running heads are separate 1-bit XObjects. Measure the
    art itself (ink = the LIGHT class in these masks) and compare the six."""
    print("== OVERDOSE running-head bitmaps (1-bit XObjects, 400 dpi) ==")
    d = pymupdf.open(PDF)
    bits = {}
    for pr, xr in RH_XREF.items():
        im = Image.open(io.BytesIO(d.extract_image(xr)["image"])).convert("L")
        a = np.asarray(im) > 127
        ys, xs = np.where(a)
        bits[pr] = a
        print(f"  p{pr} xref{xr:3d} {im.size[0]}x{im.size[1]}px  "
              f"cap={(ys.max()-ys.min()+1)/400*72:5.2f}pt  "
              f"width={(xs.max()-xs.min()+1)/400*72:6.2f}pt  ink px={a.sum()}")
    norm = {}
    for pr, a in bits.items():
        ys, xs = np.where(a)
        sub = a[ys.min():ys.max()+1, xs.min():xs.max()+1]
        norm[pr] = np.asarray(Image.fromarray((sub*255).astype("uint8")).resize((230, 30))) > 127
    ks = sorted(norm)
    print("\n  pairwise IoU after normalising each to its ink bbox:")
    print("        " + "  ".join(f"p{k}" for k in ks))
    for i in ks:
        print(f"    p{i} " + "  ".join(f"{(norm[i]&norm[j]).sum()/max(1,(norm[i]|norm[j]).sum()):.3f}" for j in ks))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="all")
    ap.add_argument("--save", default=None, help="directory for crop images")
    a = ap.parse_args()
    if a.save:
        os.makedirs(a.save, exist_ok=True)
    fns = {"survey": survey, "streams": streams, "runhead": runhead,
           "folio": folio, "sidebar": lambda: sidebar(save=a.save),
           "edges": lambda: edges(save=a.save), "leaf": leaf, "strips": strips}
    if a.cmd == "all":
        for k in ("survey", "streams", "runhead", "strips", "folio", "sidebar", "edges", "leaf"):
            print("\n" + "=" * 72); fns[k]()
    else:
        fns[a.cmd]()
