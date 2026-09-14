#!/usr/bin/env python3
"""
FURNITURE lens: measure every non-body element on the 8 scanned pages.

  python3 wf/clue_furniture.py survey      # placed-image inventory, printed coords
  python3 wf/clue_furniture.py folio       # locate + measure page numbers
  python3 wf/clue_furniture.py runhead     # OVERDOSE running heads
  python3 wf/clue_furniture.py sidebar     # rotated Bitcoin Magazine | El Salvador
  python3 wf/clue_furniture.py leaf        # recto/verso + which pages share a leaf

Coordinates: every reported coordinate is in the PRINTED page frame (reading
orientation, origin top-left, inches), obtained by rotating the PDF frame 180.
The PDF stores each sheet upside down (rotation flag 0, content 180 deg).
"""
import argparse, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf
from PIL import Image
import numpy as np
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "scan", "Scan1.pdf")
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
INV = {v: k for k, v in PAGE_MAP.items()}
W_PT, H_PT = 612.0, 792.0


def printed_rect(r):
    """PDF-frame rect -> printed-frame rect (x0,y0,x1,y1) in points, 180 rot."""
    return (W_PT - r.x1, H_PT - r.y1, W_PT - r.x0, H_PT - r.y0)


def survey():
    d = pymupdf.open(PDF)
    for pi in sorted(PAGE_MAP, key=lambda k: PAGE_MAP[k]):
        pg = d[pi]
        pr = PAGE_MAP[pi]
        print(f"\n=== printed page {pr} (pdf index {pi}) ===")
        for info in pg.get_images(full=True):
            xref = info[0]
            w, h = info[2], info[3]
            bpc = info[4]
            cs = info[5]
            rects = pg.get_image_rects(xref)
            for r in rects:
                px0, py0, px1, py1 = printed_rect(r)
                print(f"  xref {xref:3d} {w:5d}x{h:5d} bpc={bpc} cs={cs:12s} "
                      f"printed pt x[{px0:6.1f},{px1:6.1f}] y[{py0:6.1f},{py1:6.1f}] "
                      f"({px1-px0:6.1f} x {py1-py0:6.1f})  dpi={w/((r.x1-r.x0)/72):.0f}")


def render(pr, dpi=400):
    """Return PIL RGB image of printed page pr in READING orientation."""
    d = pymupdf.open(PDF)
    pg = d[INV[pr]]
    m = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = pg.get_pixmap(matrix=m)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return im.rotate(180)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--dpi", type=int, default=400)
    a = ap.parse_args()
    if a.cmd == "survey":
        survey()
    else:
        print("unknown cmd", a.cmd)


# ---------------------------------------------------------------- page edges
def page_edges(dpi=200):
    """Locate the paper boundary on each side; report straight (trimmed) vs
    ragged (torn from the binding) by the std-dev of the edge position."""
    print("page | side  | mean_px  std_px  -> verdict")
    out = {}
    for pr in sorted(INV):
        im = render(pr, dpi).convert("L")
        a = np.asarray(im).astype(int)
        H, W = a.shape
        # scanner background beyond the sheet is the brightest, flattest region.
        bg = np.percentile(a[:, :6], 95)
        res = {}
        for side in ("left", "right"):
            rows = range(int(H * 0.08), int(H * 0.92), 4)
            pos = []
            for y in rows:
                line = a[y]
                if side == "left":
                    xs = np.where(line < bg - 6)[0]
                    pos.append(xs[0] if len(xs) else 0)
                else:
                    xs = np.where(line < bg - 6)[0]
                    pos.append(xs[-1] if len(xs) else W - 1)
            pos = np.array(pos, float)
            res[side] = (pos.mean(), pos.std())
            v = "RAGGED(torn)" if pos.std() > 4 else "straight(trim)"
            print(f"  {pr} | {side:5s} | {pos.mean():7.1f} {pos.std():7.2f}  -> {v}")
        out[pr] = res
    return out


# ---------------------------------------------------------- furniture blocks
def _ink_bbox(a, thresh, box):
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    m = sub < thresh
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def runhead(dpi=400):
    """Running head: bbox in printed points, mean RGB of its ink."""
    S = dpi / 72.0
    print("page | bbox pt x[..] y[..]  | w x h pt | ink RGB | n_px")
    for pr in sorted(INV):
        im = render(pr, dpi)
        g = np.asarray(im.convert("L")).astype(int)
        rgb = np.asarray(im).astype(int)
        H, W = g.shape
        band = (0, int(30 * S), W, int(70 * S))
        if pr == 77:      # knockout: light ink on dark ground
            sub = g[band[1]:band[3], :]
            m = sub > 110
        else:
            sub = g[band[1]:band[3], :]
            m = sub < 170
        ys, xs = np.where(m)
        if len(xs) == 0:
            print(f"  {pr} | none"); continue
        bb = (xs.min(), band[1] + ys.min(), xs.max() + 1, band[1] + ys.max() + 1)
        sel = np.zeros(g.shape, bool)
        sel[band[1]:band[3], :] = m
        px = rgb[sel]
        print(f"  {pr} | x[{bb[0]/S:6.1f},{bb[2]/S:6.1f}] y[{bb[1]/S:5.1f},{bb[3]/S:5.1f}]"
              f" | {(bb[2]-bb[0])/S:5.1f} x {(bb[3]-bb[1])/S:4.1f}"
              f" | ({px[:,0].mean():5.1f},{px[:,1].mean():5.1f},{px[:,2].mean():5.1f})"
              f" | {len(px)}")


def folio(dpi=400):
    """Page number: bbox in printed points and ink RGB, both bottom corners."""
    S = dpi / 72.0
    print("page | corner | bbox pt x[..] y[..] | h pt | ink RGB | n_px")
    for pr in sorted(INV):
        im = render(pr, dpi)
        g = np.asarray(im.convert("L")).astype(int)
        rgb = np.asarray(im).astype(int)
        H, W = g.shape
        y0, y1 = int(725 * S), int(765 * S)
        for corner, (x0, x1) in (("left", (int(30 * S), int(140 * S))),
                                 ("right", (int(470 * S), int(590 * S)))):
            sub = g[y0:y1, x0:x1]
            m = (sub > 110) if pr == 77 else (sub < 170)
            ys, xs = np.where(m)
            if len(xs) < 40:
                continue
            bb = (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)
            px = rgb[y0:y1, x0:x1][m]
            print(f"  {pr} | {corner:5s} | x[{bb[0]/S:6.1f},{bb[2]/S:6.1f}] "
                  f"y[{bb[1]/S:5.1f},{bb[3]/S:5.1f}] | {(bb[3]-bb[1])/S:4.1f}"
                  f" | ({px[:,0].mean():5.1f},{px[:,1].mean():5.1f},{px[:,2].mean():5.1f}) | {len(px)}")
