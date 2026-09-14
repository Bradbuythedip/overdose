#!/usr/bin/env python3
"""
PAGE GEOMETRY of Scan1.pdf, measured at 400 dpi.

WHAT IT MEASURES
  A. paper/trim edges of the printed magazine leaf inside the letter-size scan
  B. per-page ink raster (bilevel text masks placed in page coordinates; p74/p77
     have no mask so the colour layer is thresholded)
  C. text lines: count, first baseline, leading, left/right edge per line,
     alignment class, and the ragged-right edge as a number sequence

  python3 wf/clue_geometry.py --stage A
  python3 wf/clue_geometry.py --stage C --page 75
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.path.dirname(HERE)
PDF = os.path.join(SOLVER, "scan", "Scan1.pdf")
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
DPI = 400
SCALE = DPI / 72.0
PW, PH = int(612 * SCALE), int(792 * SCALE)          # 3400 x 4400
RENDER = "/tmp/sc400"                                 # from extract_scan.py


def pdf():
    import pymupdf
    return pymupdf.open(PDF)


# ---------------------------------------------------------------- A. paper
def paper_edges(page):
    """Where the magazine leaf stops and the scanner lid starts.

    The scan is letter sized; the leaf is smaller, so a rim of lid shows.
    Scanned on a dark-ish backing the rim is measurably darker than paper.
    Returns the trim rectangle in 400 dpi pixels and in inches.
    """
    im = Image.open(f"{RENDER}/p{page}_400dpi.png").convert("L")
    a = np.asarray(im).astype(np.int16)
    col = a.mean(axis=0)           # length 3400
    row = a.mean(axis=1)           # length 4400
    return a, col, row


# ------------------------------------------------------------- B. ink raster
def ink_raster(page, main_only=True, min_px=400_000):
    """Binary ink at 400 dpi in page coordinates (3400x4400).

    The embedded PNGs are 1-bit masks with INK = WHITE, placed on the page at
    exactly 400 dpi, so they drop in without resampling.
    """
    d = pdf()
    idx = [k for k, v in PAGE_MAP.items() if v == page][0]
    pg = d[idx]
    out = np.zeros((PH, PW), dtype=bool)
    placed = []
    for x in pg.get_images(full=True):
        info = d.extract_image(x[0])
        if info["ext"] != "png":
            continue
        if main_only and info["width"] * info["height"] < min_px:
            continue
        bb = pg.get_image_bbox(x)
        m = np.asarray(Image.open(__import__("io").BytesIO(info["image"])).convert("L")) > 127
        x0, y0 = int(round(bb.x0 * SCALE)), int(round(bb.y0 * SCALE))
        h, w = m.shape
        x1, y1 = min(x0 + w, PW), min(y0 + h, PH)
        out[y0:y1, x0:x1] |= m[: y1 - y0, : x1 - x0]
        placed.append((x[0], w, h, x0, y0))
    if not placed:                        # p74, p77: no mask
        im = Image.open(f"{RENDER}/p{page}_400dpi.png").convert("L")
        a = np.asarray(im).astype(np.int16)
        if a.mean() < 140:                # knockout page: type is the bright ink
            out = a > (a.mean() + 55)
        else:
            out = a < (a.mean() - 55)
    # page is stored rotated 180; the placed masks are in PDF space, so the
    # assembled raster is upside down relative to the un-rotated renders.
    return out, placed


def rot180(a):
    return a[::-1, ::-1]


# ------------------------------------------------------------------ C. lines
def components(mask, min_area=18, max_area=200_000):
    from scipy import ndimage
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), int))
    objs = ndimage.find_objects(lab)
    areas = ndimage.sum(mask, lab, index=np.arange(1, n + 1))
    out = []
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        a = float(areas[i])
        if a < min_area or a > max_area:
            continue
        ys, xs = sl
        out.append(dict(x=int(xs.start), y=int(ys.start),
                        w=int(xs.stop - xs.start), h=int(ys.stop - ys.start),
                        a=int(a), cx=float((xs.start + xs.stop) / 2),
                        cy=float((ys.start + ys.stop) / 2),
                        bot=int(ys.stop), right=int(xs.stop)))
    return out


def chain_lines(boxes, dx_max=170, dy_max=34, min_glyphs=3):
    """Walk left to right along a baseline, tolerating curvature.

    A fixed-y row bucket cannot segment p79, whose lines arc; a loose y
    tolerance merges neighbouring lines instead. Chaining nearest-to-the-right
    follows arbitrary curvature and never jumps rows, because the next row is
    far in y at the same x.
    """
    import bisect
    bs = sorted(boxes, key=lambda b: (b["x"], b["bot"]))
    xs = [b["x"] for b in bs]
    used = [False] * len(bs)
    lines = []
    for i in range(len(bs)):
        if used[i]:
            continue
        chain = [bs[i]]
        used[i] = True
        cx, cy = bs[i]["right"], bs[i]["bot"]
        while True:
            lo = bisect.bisect_left(xs, cx - 12)
            hi = bisect.bisect_right(xs, cx + dx_max)
            bj, bd = -1, 1e18
            for j in range(lo, hi):
                if used[j]:
                    continue
                y = bs[j]["bot"]
                if abs(y - cy) > dy_max:
                    continue
                dd = (bs[j]["x"] - cx) + 3.0 * abs(y - cy)
                if dd < bd:
                    bj, bd = j, dd
            if bj < 0:
                break
            used[bj] = True
            chain.append(bs[bj])
            cx, cy = max(cx, bs[bj]["right"]), bs[bj]["bot"]
        if len(chain) >= min_glyphs:
            lines.append(sorted(chain, key=lambda z: z["x"]))
    lines.sort(key=lambda L: np.median([g["bot"] for g in L]))
    return lines


def line_stats(lines):
    out = []
    for L in lines:
        xs = [g["x"] for g in L]
        rs = [g["right"] for g in L]
        bots = sorted(g["bot"] for g in L)
        out.append(dict(n=len(L), left=min(xs), right=max(rs),
                        base=float(np.median(bots)),
                        top=min(g["y"] for g in L),
                        bot=max(g["bot"] for g in L),
                        ink=sum(g["a"] for g in L)))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="C")
    ap.add_argument("--page", type=int, default=0)
    a = ap.parse_args()
    pages = [a.page] if a.page else [72, 73, 74, 75, 76, 77, 78, 79]
    for p in pages:
        if a.stage == "A":
            arr, col, row = paper_edges(p)
            print(p, arr.shape, "col min/max", int(col.min()), int(col.max()))
        else:
            m, placed = ink_raster(p)
            m = rot180(m)
            print(p, "ink%", round(100 * m.mean(), 3), "masks", len(placed))
