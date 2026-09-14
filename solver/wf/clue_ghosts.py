#!/usr/bin/env python3
"""
GHOST / SHOW-THROUGH MAPPING for the Overdose scan (printed pages 72-79).

Physical model
--------------
The eight printed pages sit on five leaves:

    leaf A: 71 recto / 72 verso        (71 NOT in the scan)
    leaf B: 73 recto / 74 verso
    leaf C: 75 recto / 76 verso
    leaf D: 77 recto / 78 verso
    leaf E: 79 recto / 80 verso        (80 NOT in the scan)

Two ghost mechanisms, and BOTH of them mirror horizontally:

  SET-OFF   ink transferred by contact from the FACING page of the opened
            spread: 72<->73, 74<->75, 76<->77, 78<->79.  The two sheets meet
            face to face at the gutter, so source x maps to W - x.
  SHOW-THRU light through the leaf, showing the OTHER SIDE OF THE SAME LEAF:
            71->72, 73->74, 75->76, 77->78, 79->80 (and back).  Flipping a
            leaf about its spine also maps source x to W - x.

Therefore the mirror transform cannot separate the two mechanisms; only the
IDENTITY of the source page can.  That is what this script measures: for every
ghost region it cross-correlates against the mirrored ink of BOTH candidate
sources (facing page = set-off, same-leaf page = show-through) and reports the
peak normalised correlation and the registration offset for each.

A ghost that registers to NEITHER available candidate, on page 72 or 79, is
evidence of printed matter on page 71 or 80 -- outside the scan.

    python3 wf/clue_ghosts.py --render     # rebuild /tmp/sc400 (needs pymupdf)
    python3 wf/clue_ghosts.py --regions    # ghost regions + bounding boxes
    python3 wf/clue_ghosts.py --register   # correlate every ghost to sources
    python3 wf/clue_ghosts.py --crops      # write zoomed crops for eyeballing
"""
import os, sys, argparse
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

SC = "/tmp/sc400"
PAGES = list(range(72, 80))
# facing page across the opened spread -> set-off source
FACING = {72: 73, 73: 72, 74: 75, 75: 74, 76: 77, 77: 76, 78: 79, 79: 78}
# other side of the same physical leaf -> show-through source
LEAF   = {72: 71, 71: 72, 73: 74, 74: 73, 75: 76, 76: 75, 77: 78, 78: 77,
          79: 80, 80: 79}


def page(p, div=2):
    """400 dpi render, reading orientation, downsampled by `div` (2 -> 200dpi)."""
    im = Image.open(f"{SC}/p{p}_400dpi.png").convert("RGB")
    if div > 1:
        im = im.resize((im.width // div, im.height // div), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


def luma(a):
    return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114


def paper_level(g):
    """Per-page paper white: the 97th percentile of the interior."""
    h, w = g.shape
    core = g[int(h * .05):int(h * .95), int(w * .05):int(w * .95)]
    return float(np.percentile(core, 97))


def layers(p, div=2):
    """Return (dark ink map, faint ghost map) as non-negative float arrays."""
    g = luma(page(p, div))
    pw = paper_level(g)
    ink = np.clip(pw - g, 0, None)
    dark  = np.where(ink > 55, ink, 0.0)          # real printed ink
    ghost = np.where((ink > 5) & (ink < 38), ink, 0.0)   # faint layer only
    return ink, dark, ghost, pw


# ---------------------------------------------------------------- regions ---
def ghost_regions(p, div=2, min_area=600, close=9):
    """Connected faint-ink blobs, returned as (area, x0,y0,x1,y1, mean_ink)."""
    from scipy import ndimage as ndi
    ink, dark, ghost, pw = layers(p, div)
    m = ghost > 0
    # suppress the halo that always rings real ink
    grow = ndi.binary_dilation(dark > 0, np.ones((7, 7), bool))
    m &= ~grow
    m = ndi.binary_closing(m, np.ones((close, close), bool))
    m = ndi.binary_opening(m, np.ones((3, 3), bool))
    lab, n = ndi.label(m, structure=np.ones((3, 3), int))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        a = int((lab[sl] == i).sum())
        if a < min_area:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        mi = float(ink[sl][lab[sl] == i].mean())
        out.append((a, x0, y0, x1, y1, mi))
    out.sort(reverse=True)
    return out, (ink, dark, ghost, pw)


# ----------------------------------------------------------- registration ---
def ncc_map(patch, field, min_std=1.0):
    """Normalised cross-correlation of `patch` over `field` (scipy fft).

    Windows of `field` whose own standard deviation is below `min_std` grey
    levels are set to -1: a near-blank window otherwise divides by ~0 and
    produces a meaningless spike.  That guard matters here because most of
    every page IS near-blank paper.
    """
    from scipy.signal import fftconvolve
    p = patch - patch.mean()
    pn = np.sqrt((p * p).sum())
    if pn == 0:
        return None
    num = fftconvolve(field, p[::-1, ::-1], mode="valid")
    ones = np.ones_like(p)
    s1 = fftconvolve(field, ones, mode="valid")
    s2 = fftconvolve(field * field, ones, mode="valid")
    n = p.size
    var = np.clip(s2 - s1 * s1 / n, 0, None) / n
    den = np.sqrt(var * n) * pn
    c = np.where(den > 0, num / np.maximum(den, 1e-9), -1.0)
    return np.where(var >= min_std ** 2, c, -1.0)


def register(ghost_patch, src_page, div=2, mirror=True, src_layer="dark"):
    """Best NCC of a ghost patch against a (mirrored) source page's ink."""
    ink, dark, gh, pw = layers(src_page, div)
    f = {"dark": dark, "ink": ink, "ghost": gh}[src_layer]
    if mirror:
        f = f[:, ::-1]
    c = ncc_map(ghost_patch, f)
    if c is None:
        return None
    k = int(np.argmax(c))
    y, x = np.unravel_index(k, c.shape)
    return float(c[y, x]), int(x), int(y), c


def bbox_patch(p, box, div=2, layer="ghost"):
    ink, dark, gh, pw = layers(p, div)
    a = {"dark": dark, "ink": ink, "ghost": gh}[layer]
    x0, y0, x1, y1 = box
    return a[y0:y1, x0:x1]


def mirror_box(box, W):
    """Where a ghost bbox lands on the source page once un-mirrored."""
    x0, y0, x1, y1 = box
    return (W - x1, y0, W - x0, y1)


# ---------------------------------------------------------------- drivers ---
def cmd_regions(div=2, min_area=600):
    for p in PAGES:
        regs, (ink, dark, ghost, pw) = ghost_regions(p, div, min_area)
        cov = 100.0 * (ghost > 0).sum() / ghost.size
        print(f"\n== page {p}  ({ghost.shape[1]}x{ghost.shape[0]} px @ "
              f"{200//(div//2) if div else 0} dpi)  paper={pw:.1f}  "
              f"faint-ink coverage={cov:.2f}%  regions>= {min_area}px: {len(regs)}")
        for a, x0, y0, x1, y1, mi in regs[:14]:
            print(f"   area={a:7d}  bbox=({x0},{y0})-({x1},{y1})  "
                  f"{x1-x0}x{y1-y0}  mean_ink={mi:.1f}")


def cmd_pagewise(div=2):
    """Whole-page NCC of each page's faint layer against every mirrored source."""
    from scipy.signal import fftconvolve
    print("page  source  mirrored  peakNCC   dx    dy")
    for p in PAGES:
        ink, dark, gh, pw = layers(p, div)
        H, W = gh.shape
        # use the page interior to avoid scan edges
        patch = gh[300:H-300, 200:W-200]
        for s in PAGES:
            if s == p:
                continue
            for mir in (True, False):
                r = register(patch, s, div, mir, "dark")
                if r is None:
                    continue
                c, x, y, _ = r
                print(f"{p:5d} {s:7d} {str(mir):>9}  {c:7.4f} "
                      f"{x-200:5d} {y-300:5d}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", action="store_true")
    ap.add_argument("--pagewise", action="store_true")
    ap.add_argument("--div", type=int, default=2)
    ap.add_argument("--min-area", type=int, default=600)
    a = ap.parse_args()
    if a.regions:
        cmd_regions(a.div, a.min_area)
    if a.pagewise:
        cmd_pagewise(a.div)


# ------------------------------------------------- MRC background helpers ---
BG_XREF = {72: 16, 73: 4, 74: 26, 75: 34, 76: 49, 77: 45, 78: 58, 79: 73}
# the 1700x2200 JPEG that the scanner left AFTER pulling the sharp text into
# the bilevel masks: for the light pages this is very nearly a pure ghost layer.
BG_FILE = {72: "p72_x16_1700x2200.jpeg", 73: "p73_x4_1700x2200.jpeg",
           74: "p74_x26_1700x2200.jpeg", 75: "p75_x34_1700x2200.jpeg",
           76: "p76_x49_1700x2200.jpeg", 77: "p77_x45_1700x2200.jpeg",
           78: "p78_x73_1700x2200.jpeg", 79: "p79_x58_1700x2200.jpeg"}


def bg(p):
    """MRC background layer, 1700x2200, rotated into reading orientation."""
    from PIL import Image as I
    return np.asarray(I.open(f"{SC}/{BG_FILE[p]}").convert("RGB")
                      .rotate(180)).astype(np.float32)


def full(p):
    """Composited 400 dpi render downsampled to 1700x2200 (matches bg())."""
    from PIL import Image as I
    im = I.open(f"{SC}/p{p}_400dpi.png").convert("RGB").resize((1700, 2200),
                                                               I.LANCZOS)
    return np.asarray(im).astype(np.float32)


def inkmap(a):
    g = a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
    pw = np.percentile(g[110:2090, 85:1615], 97)
    return np.clip(pw - g, 0, None)


def match(patch, field, mirror):
    f = field[:, ::-1] if mirror else field
    c = ncc_map(patch, f)
    k = int(np.argmax(c)); y, x = np.unravel_index(k, c.shape)
    return float(c[y, x]), int(x), int(y)


# ------------------------------------------------------- fore-edge colour ---
FORE = {72: "L", 73: "R", 74: "L", 75: "R", 76: "L", 77: "R", 78: "L", 79: "R"}


def edge_profile(p, band=200, dpi=400):
    """Redness (R-(G+B)/2) profile of the outer `band` px of both page edges."""
    from PIL import Image as I
    a = np.asarray(I.open(f"{SC}/p{p}_400dpi.png").convert("RGB")).astype(np.float32)
    red = a[..., 0] - (a[..., 1] + a[..., 2]) / 2
    H, W = red.shape
    left = red[:, :band]
    right = red[:, W - band:]
    return left, right


def cmd_edges(band=200):
    print("page fore  mean-red@fore-edge(outer 60px)  mean-red@gutter-edge  "
          "peak99  paper-edge x")
    for p in PAGES:
        L, R = edge_profile(p, band)
        fe, ge = (L, R) if FORE[p] == "L" else (R, L)
        f60 = fe[:, :60] if FORE[p] == "L" else fe[:, -60:]
        g60 = ge[:, :60] if FORE[p] == "R" else ge[:, -60:]
        print(f"{p:4d}  {FORE[p]}    {f60.mean():8.3f}                    "
              f"{g60.mean():8.3f}          {np.percentile(f60,99):6.1f}")


# ------------------------------------------------ paper edge / serration ---
def paper_edge(p, side, thresh=250.0):
    """Column index of the paper boundary for every row, one page side.

    The scan surrounds the sheet with pure white; the sheet itself is never
    pure white.  Walking in from the scan border until the pixel stops being
    white therefore finds the physical edge of the paper.
    """
    from PIL import Image as I
    a = np.asarray(I.open(f"{SC}/p{p}_400dpi.png").convert("L")).astype(np.float32)
    H, W = a.shape
    notwhite = a < thresh
    if side == "L":
        idx = np.argmax(notwhite, axis=1).astype(float)
        idx[~notwhite.any(axis=1)] = np.nan
    else:
        idx = (W - 1 - np.argmax(notwhite[:, ::-1], axis=1)).astype(float)
        idx[~notwhite.any(axis=1)] = np.nan
    return idx


def serration(p, side, y0=400, y1=4000):
    """Roughness of one page edge: robust spread and the dominant tooth pitch."""
    idx = paper_edge(p, side)[y0:y1]
    idx = idx[np.isfinite(idx)]
    if idx.size < 100:
        return None
    med = np.median(idx)
    dev = idx - med
    mad = float(np.median(np.abs(dev)))
    # dominant spatial frequency of the edge, ignoring slow drift
    from scipy import ndimage as ndi
    hp = dev - ndi.uniform_filter1d(dev, 201)
    hp = hp[np.abs(hp) < 200]
    f = np.abs(np.fft.rfft(hp - hp.mean()))
    k = int(np.argmax(f[3:len(f)//2])) + 3
    pitch = len(hp) / k
    return dict(median_x=float(med), mad=mad, p2p=float(np.percentile(dev, 98)
                - np.percentile(dev, 2)), pitch_px=float(pitch),
                pitch_mm=float(pitch / 400 * 25.4), rows=int(idx.size))


# ------------------------------------------------- leaf test from the tear ---
def edge_signal(p, side, band=90, y0=200, y1=4200):
    """Ink profile of the outermost `band` px of one page side, per row.

    If two pages are the two faces of ONE leaf, one page's left-edge signal is
    the other page's right-edge signal at the same row: the same torn paper
    edge seen from both sides.  Facing pages of a spread are two DIFFERENT
    leaves and their outer edges are guillotine-trimmed, so they cannot match.
    """
    from PIL import Image as I
    a = np.asarray(I.open(f"{SC}/p{p}_400dpi.png").convert("RGB")).astype(np.float32)
    strip = a[y0:y1, 12:12 + band] if side == "L" else a[y0:y1, -band:]
    g = strip[..., 0] * .299 + strip[..., 1] * .587 + strip[..., 2] * .114
    ink = np.clip(np.percentile(g, 98) - g, 0, None)
    return ink.mean(axis=1)


def leaf_test(pairs=((72, 73), (74, 75), (76, 77), (78, 79),
                     (73, 74), (75, 76), (77, 78))):
    """Correlate every even page's LEFT edge with its neighbours' RIGHT edge."""
    from scipy import ndimage as ndi
    out = []
    for a, b in pairs:
        sa = edge_signal(a, "L"); sb = edge_signal(b, "R")
        hp = lambda v: v - ndi.uniform_filter1d(v, 301)
        x, y = hp(sa), hp(sb)
        r = float(np.corrcoef(x, y)[0, 1])
        # allow a small vertical registration shift
        best = max(((float(np.corrcoef(x[max(0,d):len(x)+min(0,d)],
                                       y[max(0,-d):len(y)+min(0,-d)])[0, 1]), d)
                    for d in range(-60, 61)))
        out.append((a, b, r, best))
        print(f"p{a} LEFT edge  vs  p{b} RIGHT edge:  r0={r:+.3f}   "
              f"best r={best[0]:+.3f} at dy={best[1]:+d} px")
    return out


# --------------------------------------------- spread-wide ghost solution ---
def fit_transfer(pg, src, Crange=(1500, 1900), dyrange=(-40, 40), step=2):
    """Find the mirror constant C and vertical shift dy of src -> pg transfer.

    The model is  pg_ghost(x, y)  ~  alpha * src_ink(C - x, y + dy).
    Returns (best_r, C, dy, alpha).  Works on the MRC background layer of the
    receiving page, which is the scanner's own ghost/no-ghost separation.
    """
    from scipy import ndimage as ndi
    G = inkmap(bg(pg)); S = inkmap(full(src))
    G4 = ndi.zoom(G, .25, order=1); S4 = ndi.zoom(S, .25, order=1)
    hp = lambda a: a - ndi.uniform_filter(a, 25)
    Gh = hp(G4); H, W = Gh.shape
    best = (-2, None, None, None)
    ys, xs = np.mgrid[0:H, 0:W]
    for C in range(Crange[0] // 4, Crange[1] // 4, step):
        for dy in range(dyrange[0] // 4, dyrange[1] // 4 + 1):
            sy = np.clip(ys + dy, 0, H - 1); sx = np.clip(C - xs, 0, W - 1)
            P = hp(S4[sy, sx])
            m = (P != 0)
            r = float(np.corrcoef(Gh[m], P[m])[0, 1])
            if r > best[0]:
                a = float((G4[m] * S4[sy, sx][m]).sum() /
                          (S4[sy, sx][m] ** 2).sum())
                best = (r, C * 4, dy * 4, a)
    return best


# ============================================================ CLUE DRIVERS ==
def clue_binding_edge():
    """Which page edge is the perfect-bound spine, measured, for all 8 pages."""
    from scipy import ndimage as ndi
    from scipy.signal import find_peaks
    from PIL import Image as I

    def boundary(p, side, band=400):
        a = np.asarray(I.open(f"{SC}/p{p}_400dpi.png").convert("L")).astype(np.float32)
        W = a.shape[1]
        b = a[:, 14:14 + band] if side == "L" else a[:, W - band:]
        sm = ndi.uniform_filter1d(b, 9, axis=1); nw = sm < 251
        if side == "L":
            idx = np.argmax(nw, axis=1).astype(float) + 14
        else:
            idx = (band - 1 - np.argmax(nw[:, ::-1], axis=1)).astype(float) + W - band
        idx[~nw.any(axis=1)] = np.nan
        return idx

    print("page  right-edge boundary sd (px)   notch pitch (mm)   notch depth (mm)")
    prof = {}
    for p in PAGES:
        v = boundary(p, "R")[300:4100]
        med = np.nanmedian(v); v = np.where(np.isfinite(v), v, med)
        d = np.clip(v - med, -120, 120)
        hp = d - ndi.uniform_filter1d(d, 601)
        prof[p] = hp
        pk, _ = find_peaks(-hp, prominence=8, distance=20)
        pitch = np.median(np.diff(pk)) / 400 * 25.4 if len(pk) > 4 else float("nan")
        depth = np.median(np.abs(hp[pk])) / 400 * 25.4 if len(pk) > 4 else float("nan")
        print(f"{p:4d}      {d.std():8.2f}                {pitch:8.2f}          {depth:8.2f}")
    print("\nnotch pattern shared between odd pages (same milling, same heights):")
    for a, b in ((73, 75), (75, 79), (73, 77), (73, 74), (72, 76)):
        r = max((float(np.corrcoef(prof[a][max(0,d):len(prof[a])+min(0,d)],
                                   prof[b][max(0,-d):len(prof[b])+min(0,-d)])[0, 1]), d)
                for d in range(-80, 81))
        print(f"  p{a}R vs p{b}R:  r={r[0]:+.3f} at dy={r[1]:+d} px")


def clue_ghost_transform():
    """The one mirror transform that places every ghost on its source page."""
    jobs = [("p72 <- p73  OVERDOSE masthead", 72, 73, (300, 255, 1600, 410)),
            ("p73 <- p72  In2020/WESTERN UN", 73, 72, (600, 360, 920, 560)),
            ("p74 <- p75  TOXIC AF headline", 74, 75, (840, 225, 1450, 320)),
            ("p79 <- p78  MAX KEISER sig   ", 79, 78, (600, 1830, 830, 2010))]
    print("receiving page            NCC    mirror C   dy   src ink  ghost ink  transfer")
    for name, pg, src, (x0, y0, x1, y1) in jobs:
        G = inkmap(bg(pg)); S = inkmap(full(src))
        patch = G[y0:y1, x0:x1]
        c, xm, ym = match(patch, S, True)
        C = xm + 1699 - x0; dy = ym - y0
        sx = np.clip(C - np.arange(x0, x1), 0, 1699)
        sy = np.clip(np.arange(y0, y1) + dy, 0, 2199)
        sp = S[np.ix_(sy, sx)]; m = sp > 40
        print(f"{name}  {c:.3f}   {C:6d}  {dy:+4d}  {sp[m].mean():7.1f}  "
              f"{patch[m].mean():8.2f}   {100*patch[m].mean()/sp[m].mean():5.2f}%")


def clue_p72_note():
    """The faint banknote on p72 does not lie on p73 under that transform."""
    from scipy import ndimage as ndi
    G = inkmap(bg(72)); S = inkmap(full(73))
    band = lambda a: ndi.gaussian_filter(a, 3) - ndi.gaussian_filter(a, 25)
    Gb, Sb = band(G), band(S)

    def t(box, C=1683, dy0=2, rad=14):
        x0, y0, x1, y1 = box; g = Gb[y0:y1, x0:x1].ravel(); best = -2
        for ddx in range(-rad, rad + 1, 2):
            for ddy in range(-rad, rad + 1, 2):
                sx = np.clip(C + ddx - np.arange(x0, x1), 0, 1699)
                sy = np.clip(np.arange(y0, y1) + dy0 + ddy, 0, 2199)
                s = Sb[np.ix_(sy, sx)].ravel()
                if s.std() < 1e-6:
                    continue
                best = max(best, float(np.corrcoef(g, s)[0, 1]))
        return best
    for n, b in [("VERIFIED p73 ghost: OVERDOSE  ", (300, 255, 1600, 410)),
                 ("VERIFIED p73 ghost: Max Keiser", (1040, 405, 1420, 475)),
                 ("faint note: serial line       ", (500, 470, 980, 560)),
                 ("blank-paper control           ", (1250, 1750, 1600, 1950))]:
        print(f"  {n}  best band-pass r vs p73 = {t(b):+.3f}")


def clue_red_seal():
    """The one chromatically red object on page 72 is the ghost note's seal."""
    from scipy import ndimage as ndi
    from PIL import Image as I
    a = bg(72)
    d = ndi.uniform_filter(a[..., 0] - a[..., 1], 25)
    inner = np.zeros(d.shape, bool); inner[110:2090, 60:1640] = True
    print(f"  p72 background (R-G): median={np.median(d[inner]):+.2f}  "
          f"p99.9={np.percentile(d[inner], 99.9):+.2f}")
    m = np.where(inner, d, -99) > 3.0
    lab, n = ndi.label(ndi.binary_closing(m, np.ones((9, 9), bool)))
    sz = sorted(((int((lab[o] == i + 1).sum()), o)
                 for i, o in enumerate(ndi.find_objects(lab))), reverse=True)[:3]
    for s, o in sz:
        print(f"    R-G>3 blob {s:6d}px  400dpi bbox "
              f"({2*o[1].start},{2*o[0].start})-({2*o[1].stop},{2*o[0].stop})")


def clue_rose_spine():
    """Rose ink on the 78/79 leaf's binding edge, absent from pp.72-79's print."""
    from PIL import Image as I
    FOREEDGE = {72: "L", 73: "R", 74: "L", 75: "R",
                76: "L", 77: "R", 78: "L", 79: "R"}
    for p in PAGES:
        a = np.asarray(I.open(f"{SC}/p{p}_400dpi.png").convert("RGB")).astype(np.float32)
        s = a[:, :80] if FOREEDGE[p] == "L" else a[:, -80:]
        red = (s[..., 0] - (s[..., 1] + s[..., 2]) / 2).max(axis=1)
        print(f"  p{p} outer edge {FOREEDGE[p]}: rows with redness>18 = {int((red>18).sum()):5d}"
              f"   max={red.max():5.1f}")
