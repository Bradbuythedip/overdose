#!/usr/bin/env python3
"""
BILEVEL LENS -- measurements on the embedded 1-bit text masks of scan/Scan1.pdf.

Every function prints numbers.  Run sections by name:
    python3 wf/clue_bilevel.py inventory
    python3 wf/clue_bilevel.py coverage
    python3 wf/clue_bilevel.py components
    python3 wf/clue_bilevel.py classdiff
    python3 wf/clue_bilevel.py margins
"""
import os, sys, io
import numpy as np
import pymupdf
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "scan", "Scan1.pdf")
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
CACHE = "/tmp/bilevel_cache"


def doc():
    return pymupdf.open(PDF)


def inventory():
    d = doc()
    rows = []
    for i, pg in enumerate(d):
        p = PAGE_MAP[i]
        raw = pg.get_contents()
        imgs = pg.get_images(full=True)
        print(f"\n=== pdf idx {i}  printed p{p}  rect={pg.rect}  rot={pg.rotation}  "
              f"nimages={len(imgs)}")
        for x in imgs:
            xref = x[0]
            info = d.extract_image(xref)
            w, h = info["width"], info["height"]
            rects = pg.get_image_rects(xref)
            r = rects[0] if rects else None
            dpix = dpiy = None
            if r is not None and r.width and r.height:
                dpix = w / (r.width / 72.0)
                dpiy = h / (r.height / 72.0)
            print(f"  xref={xref:4d} {w:5d}x{h:5d} ext={info['ext']:4s} "
                  f"cs={info.get('colorspace')} bpc={info.get('bpc')} "
                  f"bytes={len(info['image']):8d} "
                  f"dpi={None if dpix is None else f'{dpix:.1f}x{dpiy:.1f}'} "
                  f"rect={None if r is None else (round(r.x0,1),round(r.y0,1),round(r.x1,1),round(r.y1,1))}")
            rows.append((p, xref, w, h, info["ext"], info.get("bpc"), dpix))
    return rows


def _load(xref, d=None):
    d = d or doc()
    info = d.extract_image(xref)
    im = Image.open(io.BytesIO(info["image"]))
    return im, info


def masks_index():
    """printed page -> (xref, w, h) of the largest 1-bit image, if any."""
    d = doc()
    out = {}
    for i, pg in enumerate(d):
        p = PAGE_MAP[i]
        best = None
        for x in pg.get_images(full=True):
            info = d.extract_image(x[0])
            if info.get("bpc") == 1:
                if best is None or info["width"] * info["height"] > best[1] * best[2]:
                    best = (x[0], info["width"], info["height"])
        out[p] = best
    return out


def coverage():
    d = doc()
    mi = masks_index()
    print(f"{'page':>5} {'xref':>6} {'W':>6} {'H':>6} {'dpi':>7} {'inkfrac':>9} {'inkpx':>10}")
    for p in sorted(mi):
        m = mi[p]
        if m is None:
            print(f"{p:5d} {'--':>6} {'--':>6} {'--':>6} {'--':>7} {'NO MASK':>9}")
            continue
        xref, w, h = m
        im, info = _load(xref, d)
        a = np.array(im.convert("1"))
        # extracted PNG polarity: True == the bit the ImageMask PAINTS (ink)
        ink = int(a.sum())
        frac = ink / a.size
        dpi = 400.0
        print(f"{p:5d} {xref:6d} {w:6d} {h:6d} {dpi:7.1f} {frac:9.5f} {ink:10d}")


def components(min_px=6, max_px=200000):
    from scipy import ndimage
    d = doc()
    mi = masks_index()
    print(f"{'page':>5} {'ncomp':>7} {'>=6px':>7} {'glyphish':>9} {'medW':>5} {'medH':>5}")
    for p in sorted(mi):
        if mi[p] is None:
            print(f"{p:5d} {'NO MASK':>7}")
            continue
        xref, w, h = mi[p]
        im, _ = _load(xref, d)
        a = np.array(im.convert("1"))
        ink = a
        lab, n = ndimage.label(ink)
        sizes = ndimage.sum(ink, lab, range(1, n + 1))
        objs = ndimage.find_objects(lab)
        ws = np.array([o[1].stop - o[1].start for o in objs])
        hs = np.array([o[0].stop - o[0].start for o in objs])
        big = sizes >= min_px
        # glyph-ish: bbox height between 0.5x and 3x the modal height
        gh = hs[big]
        if len(gh):
            mh = int(np.median(gh))
            gl = big & (hs >= 0.5 * mh) & (hs <= 3 * mh) & (ws <= 6 * mh)
        else:
            mh = 0; gl = big
        print(f"{p:5d} {n:7d} {int(big.sum()):7d} {int(gl.sum()):9d} "
              f"{int(np.median(ws[big])) if big.any() else 0:5d} {mh:5d}")




def paint():
    """Every ImageMask stencil with the flat fill colour the scanner painted it in."""
    import re
    d = doc()
    print(f"{'page':>4} {'obj':>7} {'W':>5} {'H':>5} {'dpi':>6} "
          f"{'fill r,g,b':>18} {'#hex':>8} {'x0':>6} {'y0':>6} {'w_pt':>6} {'h_pt':>6} {'bytes':>7}")
    tot = 0
    for i in range(8):
        pg = d[i]; p = PAGE_MAP[i]
        c = pg.read_contents().decode("latin-1")
        # q ... cm ... /ObjN Do ... Q  blocks
        for blk in re.finditer(
                r"q\s*(.*?)([\d.]+) 0 0 ([\d.]+) ([\d.-]+) ([\d.-]+) cm\s*/(\w+) Do\s*Q",
                c, re.S):
            pre, sw, sh, tx, ty, name = blk.groups()
            g = re.findall(r"([\d.]+)\s+g\b", pre)
            rg = re.findall(r"([\d.]+) ([\d.]+) ([\d.]+)\s+rg\b", pre)
            if rg:
                col = tuple(float(v) for v in rg[-1])
            elif g:
                col = (float(g[-1]),) * 3
            else:
                col = None
            xref = int(pg.get_xobjects()[0][0]) if False else None
            # resolve name -> xref
            xr = None
            for x in pg.get_images(full=True):
                if x[7] == name:
                    xr = x[0]
            info = d.extract_image(xr)
            if info.get("bpc") != 1:
                continue
            tot += 1
            w, h = info["width"], info["height"]
            dpi = w / (float(sw) / 72.0)
            hx = "-" if col is None else "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in col)
            cs = "-" if col is None else ",".join(f"{v:.3f}" for v in col)
            print(f"{p:4d} {name:>7} {w:5d} {h:5d} {dpi:6.1f} {cs:>18} {hx:>8} "
                  f"{float(tx):6.1f} {float(ty):6.1f} {float(sw):6.1f} {float(sh):6.1f} {len(info['image']):7d}")
    print("total 1-bit stencils:", tot)


def _stencils():
    """[(page, name, xref, colour, rect_pt_pdfbottomleft, w,h)] for all 1-bit."""
    import re
    d = doc()
    out = []
    for i in range(8):
        pg = d[i]; p = PAGE_MAP[i]
        c = pg.read_contents().decode("latin-1")
        for blk in re.finditer(
                r"q\s*(.*?)([\d.]+) 0 0 ([\d.]+) ([\d.-]+) ([\d.-]+) cm\s*/(\w+) Do\s*Q",
                c, re.S):
            pre, sw, sh, tx, ty, name = blk.groups()
            g = re.findall(r"([\d.]+)\s+g\b", pre)
            rg = re.findall(r"([\d.]+) ([\d.]+) ([\d.]+)\s+rg\b", pre)
            col = tuple(float(v) for v in rg[-1]) if rg else ((float(g[-1]),)*3 if g else None)
            xr = None
            for x in pg.get_images(full=True):
                if x[7] == name:
                    xr = x[0]
            info = d.extract_image(xr)
            if info.get("bpc") != 1:
                continue
            out.append(dict(page=p, name=name, xref=xr, col=col,
                            x=float(tx), y=float(ty), w=float(sw), h=float(sh),
                            px=info["width"], py=info["height"]))
    return out


def classdiff():
    """Mean colour of the 200 dpi JPEG UNDER each stencil's ink vs beside it."""
    d = doc()
    st = _stencils()
    jp = {}
    for i in range(8):
        p = PAGE_MAP[i]
        for x in d[i].get_images(full=True):
            info = d.extract_image(x[0])
            if info.get("bpc") == 8:
                jp[p] = np.array(Image.open(io.BytesIO(info["image"])).convert("RGB"))
    print(f"{'page':>4} {'obj':>7} {'inkpx':>8} "
          f"{'JPEG under ink':>22} {'JPEG beside':>22} {'dE':>6} {'paintcolour':>12}")
    for s in st:
        J = jp[s["page"]]            # 1700x2200, page-space, y from TOP
        H, W = J.shape[:2]
        sx, sy = W / 612.0, H / 792.0
        # stencil rect in pdf bottom-left -> image top-left
        x0 = int(round(s["x"] * sx)); x1 = int(round((s["x"] + s["w"]) * sx))
        yt = int(round((792 - s["y"] - s["h"]) * sy)); yb = int(round((792 - s["y"]) * sy))
        x0, x1 = max(0, x0), min(W, x1); yt, yb = max(0, yt), min(H, yb)
        if x1 - x0 < 4 or yb - yt < 4:
            continue
        info = d.extract_image(s["xref"])
        a = np.array(Image.open(io.BytesIO(info["image"])).convert("1"))
        m = np.array(Image.fromarray(a.astype(np.uint8) * 255)
                     .resize((x1 - x0, yb - yt), Image.NEAREST)) > 127
        sub = J[yt:yb, x0:x1].astype(float)
        if m.sum() < 20 or (~m).sum() < 20:
            ink_c = sub[m].mean(0) if m.sum() else np.array([np.nan]*3)
            bg_c = sub[~m].mean(0) if (~m).sum() else np.array([np.nan]*3)
        else:
            ink_c = sub[m].mean(0); bg_c = sub[~m].mean(0)
        dE = float(np.linalg.norm(ink_c - bg_c))
        pc = "-" if s["col"] is None else "#%02X%02X%02X" % tuple(int(round(v*255)) for v in s["col"])
        f = lambda v: "(%3.0f,%3.0f,%3.0f)" % tuple(v)
        print(f"{s['page']:>4} {s['name']:>7} {int(a.sum()):8d} "
              f"{f(ink_c):>22} {f(bg_c):>22} {dE:6.1f} {pc:>12}")


def p77_resolution():
    """p77 has no stencil: its text is sampled only in the 200 dpi JPEG."""
    from scipy import ndimage
    d = doc()
    for p, xref in [(77, 45), (78, 73), (76, 49)]:
        info = d.extract_image(xref)
        J = np.array(Image.open(io.BytesIO(info["image"])).convert("L"))
        print(f"p{p} jpeg {J.shape[1]}x{J.shape[0]} -> {J.shape[1]/(612/72.0):.1f} dpi")
    # x-height of body text: p77 from the jpeg, p78 from its 400 dpi stencil
    info = d.extract_image(45)
    J = np.array(Image.open(io.BytesIO(info["image"])).convert("L"))
    # p77 is white text on dark brown -> ink is BRIGHT
    reg = J[600:1600, 300:1400]
    thr = (reg.max().astype(int) + reg.min().astype(int)) // 2
    ink = reg > thr
    lab, n = ndimage.label(ink)
    objs = ndimage.find_objects(lab)
    hs = np.array([o[0].stop - o[0].start for o in objs])
    ws = np.array([o[1].stop - o[1].start for o in objs])
    k = (hs >= 3) & (hs <= 40) & (ws >= 2) & (ws <= 40)
    print(f"p77 JPEG body components n={int(k.sum())} median glyph bbox "
          f"{int(np.median(ws[k]))}x{int(np.median(hs[k]))} px at 200 dpi")
    info = d.extract_image(74)
    A = np.array(Image.open(io.BytesIO(info["image"])).convert("1"))
    reg = A[1200:2400, 400:2200]
    lab, n = ndimage.label(reg)
    objs = ndimage.find_objects(lab)
    hs = np.array([o[0].stop - o[0].start for o in objs])
    ws = np.array([o[1].stop - o[1].start for o in objs])
    k = (hs >= 6) & (hs <= 80) & (ws >= 4) & (ws <= 80)
    print(f"p78 STENCIL body components n={int(k.sum())} median glyph bbox "
          f"{int(np.median(ws[k]))}x{int(np.median(hs[k]))} px at 400 dpi")


def stencil_raster(page, dpi=200):
    """Union of every stencil's ink for one printed page, in page space."""
    d = doc()
    W = int(round(612 * dpi / 72.0)); H = int(round(792 * dpi / 72.0))
    S = np.zeros((H, W), bool)
    for s in _stencils():
        if s["page"] != page:
            continue
        info = d.extract_image(s["xref"])
        a = np.array(Image.open(io.BytesIO(info["image"])).convert("1"))
        x0 = int(round(s["x"] * dpi / 72.0)); x1 = int(round((s["x"] + s["w"]) * dpi / 72.0))
        yt = int(round((792 - s["y"] - s["h"]) * dpi / 72.0))
        yb = int(round((792 - s["y"]) * dpi / 72.0))
        tw, th = max(1, x1 - x0), max(1, yb - yt)
        m = np.array(Image.fromarray(a.astype(np.uint8) * 255).resize((tw, th), Image.BILINEAR)) > 40
        xa, xb = max(0, x0), min(W, x1); ya, yb2 = max(0, yt), min(H, yb)
        S[ya:yb2, xa:xb] |= m[ya - yt:yb2 - yt, xa - x0:xb - x0]
    return S


def jpeg_only_text(page, dpi=200, dark=170, dilate=3):
    """Glyph-sized dark components in the COLOUR layer with zero stencil overlap."""
    from scipy import ndimage
    d = doc()
    idx = [k for k, v in PAGE_MAP.items() if v == page][0]
    xr = [x[0] for x in d[idx].get_images(full=True)
          if d.extract_image(x[0]).get("bpc") == 8][0]
    J = np.array(Image.open(io.BytesIO(d.extract_image(xr)["image"])).convert("L"))
    S = stencil_raster(page, dpi)
    S = ndimage.binary_dilation(S, np.ones((dilate, dilate), bool))
    ink = J < dark
    lab, n = ndimage.label(ink)
    objs = ndimage.find_objects(lab)
    keep = []
    for i, o in enumerate(objs, 1):
        h = o[0].stop - o[0].start; w = o[1].stop - o[1].start
        if not (3 <= h <= 60 and 2 <= w <= 60):
            continue
        sel = lab[o] == i
        if S[o][sel].any():
            continue
        keep.append((o[1].start, o[0].start, w, h, int(sel.sum())))
    print(f"p{page}: stencil ink {int(S.sum())} px @200dpi; "
          f"JPEG dark comps total {n}; glyph-sized with ZERO stencil overlap = {len(keep)}")
    return keep, J, S


def jpeg_only_all():
    for p in [72, 73, 74, 75, 76, 77, 78, 79]:
        try:
            jpeg_only_text(p)
        except Exception as e:
            print(p, "ERR", e)


if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    globals()[fn](*sys.argv[2:])
