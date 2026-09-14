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


# ---------------------------------------------------------------- driver
PAGES_TEXT = [72, 75, 76, 77, 78, 79]
COLW = {72: (900, 2750), 75: (440, 2790), 76: (505, 2955),
        77: (430, 2990), 78: (525, 2955), 79: (575, 2895)}


def prep(page):
    """Cache the two rasters and the component list for one page."""
    import os, pickle
    os.makedirs("/tmp/geo", exist_ok=True)
    cp = f"/tmp/geo/comps_{page}.pkl"
    if os.path.exists(cp):
        return pickle.load(open(cp, "rb"))
    if page == 77:
        ink = colour_ink(77)
        np.save("/tmp/geo/colourink_77.npy", ink)
        x0, x1 = COLW[77]
        b = components(ink[:, x0:x1], min_area=25, max_area=40000)
        for g in b:
            g["x"] += x0; g["cx"] += x0; g["right"] += x0
    else:
        m, _ = ink_raster(page)
        b = components(rot180(m))
        ci = colour_ink(page)
        np.save(f"/tmp/geo/colourink_{page}.npy", ci)
    pickle.dump(b, open(cp, "wb"))
    return b


def main():
    import math
    for p in PAGES_TEXT:
        b = prep(p)
        L = merge_fragments(chain_lines(b), 96.0, strong_n=3 if p == 72 else 12)
        fits = [f for f in (baseline_fit(Z) for Z in L) if f]
        sl = np.array([f["slope"] for f in fits])
        sg = np.array([abs(f["sag"]) for f in fits])
        print("p%d  chained lines=%d  median slope %+.5f (%+.3f deg)  "
              "median |sagitta| %.1f px  max %.1f px"
              % (p, len(L), np.median(sl),
                 math.degrees(math.atan(np.median(sl))),
                 np.median(sg), sg.max()))


def _run_report():
    main()
    print()
    full_report()
    return 0





# ------------------------------------------- C2. colour-layer ink (complete)
def colour_ink(page, k=81, thr=42):
    """Ink from the 200 dpi colour layer, upsampled 2x by the 400 dpi render.

    WHY NOT THE MASK. The PDF is mixed-raster: a bilevel text mask plus a
    colour plate. The project's notes say the mask holds *all* black-on-white
    text. It does not -- whole printed lines are missing from it (p78 line 10,
    for one), and text sitting on the orange/charcoal highlight rectangles is
    dropped wholesale. Anything counted off the mask undercounts the page.

    Local-mean contrast catches both polarities at once: dark type on paper and
    knockout type on a dark rule or on p77's brown ground.
    """
    from scipy import ndimage
    im = Image.open(f"{RENDER}/p{page}_400dpi.png").convert("L")
    a = np.asarray(im).astype(np.float32)
    bg = ndimage.uniform_filter(a, size=k)
    return np.abs(a - bg) > thr


def bands(mask, x0, x1, min_rows=6, min_ink=400, gap=8):
    """Horizontal ink bands = printed text lines, inside a column [x0,x1)."""
    prof = mask[:, x0:x1].sum(axis=1)
    on = prof > 3
    out, st = [], None
    run_off = 0
    for y in range(len(on)):
        if on[y]:
            if st is None:
                st = y
            run_off = 0
        else:
            if st is not None:
                run_off += 1
                if run_off >= gap:
                    e = y - run_off
                    if e - st + 1 >= min_rows and prof[st:e + 1].sum() >= min_ink:
                        out.append((st, e, int(prof[st:e + 1].sum())))
                    st = None
    if st is not None:
        out.append((st, len(on) - 1, int(prof[st:].sum())))
    return out


# --------------------------------------------------- C3. lines, fragment-safe
def merge_fragments(lines, pitch, strong_n=12):
    """Chaining breaks a line at quotes, apostrophes and tall/short glyphs.

    Rebuild: keep chains with >= strong_n glyphs as the lines, then attach each
    leftover chain to whichever strong line passes closest to it VERTICALLY AT
    THAT x. Interpolating the strong line's own bottom edge keeps this correct
    on p79, whose baselines arc by more than a line's height across the page.
    """
    strong = [L for L in lines if len(L) >= strong_n]
    weak = [L for L in lines if len(L) < strong_n]
    if not strong:
        return lines
    prof = []
    for L in strong:
        xs = np.array([g["cx"] for g in L], float)
        ys = np.array([g["bot"] for g in L], float)
        o = np.argsort(xs)
        prof.append((xs[o], ys[o]))
    for W in weak:
        wx = float(np.median([g["cx"] for g in W]))
        wy = float(np.median([g["bot"] for g in W]))
        best, bd = -1, 1e18
        for i, (xs, ys) in enumerate(prof):
            yi = float(np.interp(wx, xs, ys))
            d = abs(yi - wy)
            if d < bd:
                best, bd = i, d
        if best >= 0 and bd < 0.5 * pitch:
            strong[best] = sorted(strong[best] + W, key=lambda z: z["x"])
    strong.sort(key=lambda L: np.median([g["bot"] for g in L]))
    return strong


def est_pitch(lines):
    b = sorted(float(np.median([g["bot"] for g in L])) for L in lines)
    d = np.diff(b)
    d = d[(d > 30) & (d < 400)]
    if len(d) == 0:
        return 96.0
    # modal pitch: smallest cluster centre that most gaps are integer multiples of
    cand = np.arange(60.0, 160.0, 0.05)
    best, bs = 96.0, -1
    for c in cand:
        k = np.round(d / c)
        k[k < 1] = 1
        err = np.abs(d - k * c)
        s = float(np.sum(err < 4.0))
        if s > bs:
            best, bs = float(c), s
    return best


# ------------------------------------------------- C4. baseline grid + slots
def fit_grid(bases, pitch):
    """Best phase for a constant-pitch grid through the measured baselines."""
    b = np.asarray(sorted(bases), float)
    ph = np.arange(0, pitch, 0.05)
    err = [np.sum(np.abs(((b - p + pitch / 2) % pitch) - pitch / 2)) for p in ph]
    return float(ph[int(np.argmin(err))])


def slot_table(page, lines, pitch, x0, x1, ytop=None, ybot=None):
    """Every baseline-grid slot in the text block, with mask ink and colour ink.

    The point of the table: a slot with colour ink but no mask ink is a printed
    line the bilevel layer dropped.
    """
    mk, _ = ink_raster(page)
    mk = rot180(mk)
    ci = np.load(f"/tmp/geo/colourink_{page}.npy")
    bases = [float(np.median([g["bot"] for g in L])) for L in lines]
    ph = fit_grid(bases, pitch)
    lo = (ytop if ytop is not None else min(bases)) - 0.2 * pitch
    hi = (ybot if ybot is not None else max(bases)) + 0.4 * pitch
    k0 = int(np.ceil((lo - ph) / pitch))
    k1 = int(np.floor((hi - ph) / pitch))
    rows = []
    for k in range(k0, k1 + 1):
        base = ph + k * pitch
        a, b = int(base - 0.80 * pitch), int(base + 0.18 * pitch)
        if a < 0 or b >= mk.shape[0]:
            continue
        m = int(mk[a:b, x0:x1].sum())
        c = int(ci[a:b, x0:x1].sum())
        near = min((abs(base - z) for z in bases), default=999)
        rows.append(dict(k=k, base=round(base, 1), mask=m, colour=c,
                         matched=near < 0.35 * pitch))
    return rows


# ------------------------------------------------- C5. leading by regression
def leading(bases):
    """Line pitch by least squares over integer line indices.

    A modal gap is too coarse: paragraph gaps are 2x the pitch and the blocks
    on a page need not share a phase. Assign each baseline an integer index by
    rounding its gap to the running median, then regress y on index.
    """
    b = np.asarray(sorted(bases), float)
    d = np.diff(b)
    m = float(np.median(d[d < np.percentile(d, 75) * 1.3])) if len(d) else 96.0
    for _ in range(4):
        idx = np.concatenate([[0], np.cumsum(np.round(d / m))])
        A = np.vstack([idx, np.ones_like(idx)]).T
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        m = float(sol[0])
    resid = b - (sol[0] * idx + sol[1])
    return float(sol[0]), float(sol[1]), idx.astype(int), resid


def mode_baseline(L, bw=4.0):
    """Baseline = modal bottom edge, not the median.

    The median moves with how many descenders a line happens to contain; the
    mode sits on the run of x-height and cap-height glyphs that all share one
    bottom, which is the baseline.
    """
    b = np.array([g["bot"] for g in L], float)
    if len(b) < 3:
        return float(np.median(b))
    grid = np.arange(b.min() - 1, b.max() + 1, 0.5)
    cnt = [np.sum(np.abs(b - g) <= bw) for g in grid]
    return float(grid[int(np.argmax(cnt))])


def blocks_of(bases, pitch, factor=1.55):
    out, cur = [], [0]
    for i in range(1, len(bases)):
        if bases[i] - bases[i - 1] > factor * pitch:
            out.append(cur)
            cur = []
        cur.append(i)
    out.append(cur)
    return out


def baseline_fit(L, nbin=6, bw=4.0):
    """Per-line baseline: modal glyph bottom inside x-bins, then a fit.

    Returns (slope px/px, intercept, sagitta, rms_line, rms_quad, pts).
    Sagitta is the quadratic's largest departure from its own chord: it
    separates a genuine arc from a straight line that is merely tilted.
    """
    xs = np.array([g["cx"] for g in L], float)
    ys = np.array([g["bot"] for g in L], float)
    if len(xs) < 12:
        return None
    qs = np.quantile(xs, np.linspace(0, 1, nbin + 1))
    px, py = [], []
    for j in range(nbin):
        s = (xs >= qs[j]) & (xs <= qs[j + 1])
        if s.sum() < 3:
            continue
        b = ys[s]
        grid = np.arange(b.min() - 1, b.max() + 1, 0.5)
        cnt = [np.sum(np.abs(b - g) <= bw) for g in grid]
        px.append(float(np.mean(xs[s])))
        py.append(float(grid[int(np.argmax(cnt))]))
    px, py = np.array(px), np.array(py)
    if len(px) < 4:
        return None
    c1 = np.polyfit(px, py, 1)
    r1 = py - np.polyval(c1, px)
    c2 = np.polyfit(px, py, 2)
    r2 = py - np.polyval(c2, px)
    xa, xb = px.min(), px.max()
    xx = np.linspace(xa, xb, 200)
    yy = np.polyval(c2, xx)
    ch = np.interp(xx, [xa, xb], [np.polyval(c2, xa), np.polyval(c2, xb)])
    sag = float((yy - ch)[np.argmax(np.abs(yy - ch))])
    return dict(slope=float(c1[0]), b=float(c1[1]), sag=sag,
                rms1=float(np.sqrt((r1 ** 2).mean())),
                rms2=float(np.sqrt((r2 ** 2).mean())),
                x0=float(xa), x1=float(xb), n=len(L))


def line_extent(ink, base, slope, xref, pitch, x0, x1, up=0.80, dn=0.18,
                min_col=2):
    """Left and right ink edge of one line, following its own tilted baseline.

    A horizontal band cannot measure p79's opening block, which is rotated
    ~2.7 deg: over its 1,600 px measure the band would slide a third of a line.
    So the window is sheared to sit on the fitted baseline.
    """
    H = ink.shape[0]
    xs = np.arange(x0, x1)
    yb = base + slope * (xs - xref)
    lo = np.clip((yb - up * pitch).astype(int), 0, H - 1)
    hi = np.clip((yb + dn * pitch).astype(int), 1, H)
    cnt = np.array([ink[lo[i]:hi[i], xs[i]].sum() for i in range(len(xs))])
    hit = np.where(cnt >= min_col)[0]
    if len(hit) == 0:
        return None
    return int(xs[hit[0]]), int(xs[hit[-1]]), int(cnt.sum())


def fill_gaps(rows, ci, pitch, x0, x1, thresh=1500):
    """Every baseline slot between two detected lines, tested for colour ink.

    Chaining only sees lines the bilevel mask kept. A gap of n pitches hides
    n-1 slots; each is either a blank (paragraph space) or a printed line the
    mask dropped. The colour plate settles which.
    """
    out = []
    for i, r in enumerate(rows):
        out.append(dict(kind="mask", base=r[1], slope=r[2], ext=r[3]))
        if i + 1 < len(rows):
            b0, b1 = r[1], rows[i + 1][1]
            n = int(round((b1 - b0) / pitch))
            for j in range(1, max(n, 1)):
                bb = b0 + (b1 - b0) * j / n
                sl = (r[2] + rows[i + 1][2]) / 2
                e = line_extent(ci, bb, sl, 1700, pitch, x0, x1)
                ink = e[2] if e else 0
                out.append(dict(kind="colour" if ink >= thresh else "blank",
                                base=bb, slope=sl, ext=e, ink=ink))
    return out


# ---------------------------------------------------------------- C6. report
BLOCKS = {                      # printed-line index ranges per typographic block
    75: [(0, 2), (2, 3), (3, 12), (12, 32)],
    76: [(0, 6), (6, 17), (17, 31)],
    78: [(0, 5), (5, 14), (14, 18), (18, 22)],
    79: [(0, 16), (16, 19), (19, 21), (21, 25)],
}


def alignment(lines, theta=0.0, base0=0.0):
    """Flush or ragged, per edge, as numbers.

    On p79 the block is rotated, so the edges are de-rotated before the spread
    is taken: a rotated flush-right block has a right edge that walks left by
    tan(theta) x leading per line, which reads as 'ragged' if ignored.
    """
    L = np.array([z[2] for z in lines], float)
    R = np.array([z[3] for z in lines], float)
    B = np.array([z[0] for z in lines], float)
    L = L + theta * (B - base0)
    R = R + theta * (B - base0)
    return dict(n=len(lines),
                left_min=float(L.min()), left_max=float(L.max()),
                left_sd=float(L.std()), right_min=float(R.min()),
                right_max=float(R.max()), right_sd=float(R.std()),
                lefts=[round(v, 1) for v in L], rights=[round(v, 1) for v in R])




# ------------------------------------------------- one-command full report
LINEFIX = {                     # measured by hand-check against the renders
    76: dict(prepend=[(596.0, "colour", 1041, 2908)]),
    79: dict(drop=[2756.3, 2853.6, 2950.9],
             insert=(19, [(2789.0, "colour", 836, 2705),
                          (2886.0, "colour", 836, 2301)])),
}
PAGE_SLOPE = {75: 0.0036, 76: -0.0017, 78: -0.0008, 79: 0.047}


def page_lines(p):
    """Every printed typeset line on p, from the mask plus the colour plate."""
    b = prep(p)
    L = merge_fragments(chain_lines(b), 96.0)
    fits = [f for f in (baseline_fit(Z) for Z in L) if f]
    rows = [(i + 1, f["slope"] * 1700 + f["b"], f["slope"], None, None)
            for i, f in enumerate(fits)]
    bs = sorted(r[1] for r in rows)
    d = np.diff(bs)
    pit = float(np.median(d[d < 1.5 * np.median(d)]))
    ci = np.load(f"/tmp/geo/colourink_{p}.npy")
    x0, x1 = COLW[p]
    filled = fill_gaps(rows, ci, pit, x0, x1, thresh=10000)
    out = []
    for z in [q for q in filled if q["kind"] != "blank"]:
        e = line_extent(ci, z["base"], z["slope"], 1700, pit, x0, x1,
                        up=0.60, dn=0.10, min_col=4)
        out.append((round(z["base"], 1), z["kind"],
                    e[0] if e else None, e[1] if e else None))
    fx = LINEFIX.get(p, {})
    out = fx.get("prepend", []) + out
    out = [z for z in out if z[0] not in fx.get("drop", [])]
    if "insert" in fx:
        i, items = fx["insert"]
        out = out[:i] + items + out[i:]
    return out, pit


def full_report():
    import math
    print("### leading, per typographic block (least squares on baselines)")
    for p in (75, 76, 78, 79):
        rows, pit = page_lines(p)
        bases = [z[0] for z in rows]
        for B in blocks_of(bases, pit):
            bb = np.array([bases[i] for i in B])
            if len(bb) < 3:
                continue
            A = np.vstack([np.arange(len(bb)), np.ones(len(bb))]).T
            sol, *_ = np.linalg.lstsq(A, bb, rcond=None)
            print("  p%d block n=%2d first_base=%7.1f leading=%.3f px = %.3f pt"
                  % (p, len(bb), bb[0], sol[0], sol[0] * 72 / 400))
    print()
    print("### printed typeset line counts, and lines missing from the masks")
    for p in (75, 76, 78, 79):
        rows, pit = page_lines(p)
        mk, _ = ink_raster(p)
        mk = rot180(mk)
        ci = np.load(f"/tmp/geo/colourink_{p}.npy")
        x0, x1 = COLW[p]
        drop = part = 0
        for (bb, kind, l, r) in rows:
            sl = PAGE_SLOPE[p] if (p != 79 or bb < 2100) else -0.003
            em = line_extent(mk, bb, sl, 1700, pit, x0, x1, 0.62, 0.12, 1)
            ec = line_extent(ci, bb, sl, 1700, pit, x0, x1, 0.62, 0.12, 1)
            ratio = (em[2] if em else 0) / max(ec[2] if ec else 1, 1)
            if ratio < 0.05:
                drop += 1
                print("  p%d base=%7.1f  mask=%6d colour=%6d  WHOLE LINE MISSING"
                      % (p, bb, em[2] if em else 0, ec[2] if ec else 0))
            elif ratio < 0.45:
                part += 1
        print("  p%d: %d printed typeset lines, %d wholly absent from the mask,"
              " %d more under 45%% present" % (p, len(rows), drop, part))
    print()
    print("### alignment per block (edges in 400 dpi px)")
    for p in (75, 76, 78, 79):
        rows, pit = page_lines(p)
        for (a, b) in BLOCKS[p]:
            seg = rows[a:b]
            th = 0.0468 if (p == 79 and a == 0) else 0.0
            A = alignment(seg, th, seg[0][0])
            print("  p%d lines %2d-%2d  LEFT %4.0f-%4.0f sd=%5.1f   "
                  "RIGHT %4.0f-%4.0f sd=%5.1f"
                  % (p, a + 1, b, A["left_min"], A["left_max"], A["left_sd"],
                     A["right_min"], A["right_max"], A["right_sd"]))
    print()
    print("### two more whole-line dropouts the per-line pass cannot reach")
    mk = rot180(ink_raster(75)[0])
    ci = np.load("/tmp/geo/colourink_75.npy")
    print("  p75 headline 'BITCOIN IS TOXIC AF' y460-650 x440-1800: "
          "mask=%d colour=%d" % (mk[460:650, 440:1800].sum(),
                                 ci[460:650, 440:1800].sum()))
    mk = rot180(ink_raster(72)[0])
    ci = np.load("/tmp/geo/colourink_72.npy")
    print("  p72 left source column y3800-4120 x400-1400: mask=%d colour=%d"
          % (mk[3800:4120, 400:1400].sum(), ci[3800:4120, 400:1400].sum()))
    for nm, (a, b) in (("left", (420, 1450)), ("right", (1900, 2990))):
        prof = ci[3800:4110, a:b].sum(axis=1)
        on = prof > 25
        tops, st = [], None
        for i, v in enumerate(on):
            if v and st is None:
                st = i
            elif not v and st is not None:
                if i - st >= 10:
                    tops.append(3800 + st)
                st = None
        d = np.diff(tops)
        print("  p72 %-5s source column: %d lines, leading %.2f px = %.3f pt"
              % (nm, len(tops), d.mean(), d.mean() * 72 / 400))
    print()
    print("### p77 centred display block vs the justified column below it")
    ci = np.load("/tmp/geo/colourink_77.npy")
    cs = []
    for base in (2369.2, 2465.3, 2562.5, 2657.9, 2755.9):
        e = line_extent(ci, base, 0.0015, 1700, 96.5, 1000, 2990, 0.62, 0.12, 3)
        cs.append((e[0] + e[1]) / 2)
        print("  display  base=%7.1f L=%4d R=%4d centre=%7.1f"
              % (base, e[0], e[1], cs[-1]))
    ls, rs = [], []
    for base in (3012.3, 3116.2, 3208.3, 3302.7, 3401.0, 3498.3, 3594.3,
                 3691.2, 3788.2, 3883.0):
        e = line_extent(ci, base, 0.0, 1700, 96.5, 1000, 2990, 0.62, 0.12, 3)
        ls.append(e[0]); rs.append(e[1])
    print("  display centre mean %.1f range %.1f px | justified column "
          "L %d-%d R %d-%d centre %.1f"
          % (np.mean(cs), max(cs) - min(cs), min(ls), max(ls), min(rs),
             max(rs), (np.mean(ls) + np.mean(rs)) / 2))



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="C")
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        raise SystemExit(_run_report())
    pages = [a.page] if a.page else [72, 73, 74, 75, 76, 77, 78, 79]
    for p in pages:
        if a.stage == "A":
            arr, col, row = paper_edges(p)
            print(p, arr.shape, "col min/max", int(col.min()), int(col.max()))
        else:
            m, placed = ink_raster(p)
            m = rot180(m)
            print(p, "ink%", round(100 * m.mean(), 3), "masks", len(placed))
