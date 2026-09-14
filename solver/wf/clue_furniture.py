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
