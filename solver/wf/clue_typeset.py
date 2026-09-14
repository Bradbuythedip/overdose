#!/usr/bin/env python3
"""
TYPESET lens - typesetting forensics on the Overdose scan (solver/scan/Scan1.pdf).

All bilevel masks are natively 400 dpi (verified via get_image_rects), so
1 px = 0.18 pt exactly and every page is directly commensurable.

Stages
  rects    mask xrefs, placement rects, verified dpi
  lines    line bands per page
  vmet     vertical metrics per text line (baseline/x-height/cap/asc/desc)
  pitch    horizontal advance (character pitch) per line, grid-fitted
  faces    display-face metrics: headline, NUMBERS figures, knockout bar text
  spaces   word-space width distribution + every gap wider than one space

Prereq: python3 extract_scan.py --dpi 400 --out /tmp/sc400
"""
import argparse, glob, json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "scan", "Scan1.pdf")
SC = "/tmp/sc400"
OUT = os.path.join(HERE, "typeset")
os.makedirs(OUT, exist_ok=True)

PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
PT_PER_PX = 72.0 / 400.0          # masks are native 400 dpi
PW, PH = 612.0, 792.0             # US Letter, points


# ------------------------------------------------------------------ loading
def mask_index():
    """printed page -> dict(xref, w, h, rect_rot) for the page's main text mask."""
    import pymupdf
    d = pymupdf.open(PDF)
    idx = {}
    for i, pg in enumerate(d):
        printed = PAGE_MAP[i]
        best = None
        for im in pg.get_images(full=True):
            xref = im[0]
            info = d.extract_image(xref)
            if info.get("bpc") != 1:
                continue
            npx = info["width"] * info["height"]
            if npx < 500_000:
                continue
            r = pg.get_image_rects(xref)[0]
            if best is None or npx > best["npx"]:
                best = dict(xref=xref, w=info["width"], h=info["height"], npx=npx,
                            rect=(r.x0, r.y0, r.x1, r.y1),
                            dpi=(info["width"] / (r.width / 72),
                                 info["height"] / (r.height / 72)))
        if best:
            # rotate the placement 180 deg with the page
            x0, y0, x1, y1 = best["rect"]
            best["rect_rot"] = (PW - x1, PH - y1, PW - x0, PH - y0)
            idx[printed] = best
    return idx


def load(printed, mi=None):
    """(ink bool array True=ink, meta). Page content is scanned 180 deg rotated."""
    mi = mi or mask_index()
    m = mi[printed]
    fn = glob.glob(f"{SC}/p{printed}_x{m['xref']}_*.png")
    if not fn:
        raise SystemExit(f"missing render for p{printed}; run extract_scan.py")
    a = np.array(Image.open(fn[0]).convert("L"))
    ink = (a > 127)[::-1, ::-1]          # masks store ink as the LIGHT class
    return ink, m


def pxpt_x(m, px):   # mask px -> page point (x), in the un-rotated reading frame
    return m["rect_rot"][0] + px * PT_PER_PX


def pxpt_y(m, py):
    return m["rect_rot"][1] + py * PT_PER_PX


# ------------------------------------------------------------- segmentation
def line_bands(ink, min_ink=4, min_h=6):
    rows = ink.sum(1)
    on = rows >= min_ink
    segs, s = [], None
    for y, v in enumerate(on):
        if v and s is None:
            s = y
        elif not v and s is not None:
            if y - s >= min_h:
                segs.append((s, y))
            s = None
    if s is not None and len(on) - s >= min_h:
        segs.append((s, len(on)))
    return segs


def comps_of(band, min_area=6):
    lab, n = ndimage.label(band, structure=np.ones((3, 3), bool))
    out = []
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        sy, sx = sl
        a = int((lab[sy, sx] > 0).sum())
        if a < min_area:
            continue
        out.append(dict(x0=sx.start, x1=sx.stop, y0=sy.start, y1=sy.stop, area=a))
    out.sort(key=lambda c: c["x0"])
    return out


# --------------------------------------------------------- vertical metrics
def vmetrics(ink, y0, y1):
    band = ink[y0:y1]
    cs = comps_of(band)
    if len(cs) < 10:
        return None
    hs = np.array([c["y1"] - c["y0"] for c in cs], float)
    med = np.median(hs)
    cs = [c for c in cs if (c["y1"] - c["y0"]) >= 0.30 * med and (c["x1"] - c["x0"]) >= 2]
    if len(cs) < 10:
        return None
    tops = np.array([c["y0"] for c in cs], float)
    bots = np.array([c["y1"] for c in cs], float)
    # baseline = modal bottom edge (1 px bins, widest cluster)
    h, e = np.histogram(bots, bins=np.arange(bots.min(), bots.max() + 2) - 0.5)
    k = int(np.argmax(np.convolve(h, np.ones(3), "same")))
    bcen = e[k] + 0.5
    sel = bots[np.abs(bots - bcen) <= 1.6]
    base = sel.mean()
    # x-line = modal top edge among the SHORT glyphs (tops below the cap band)
    h2, e2 = np.histogram(tops, bins=np.arange(tops.min(), tops.max() + 2) - 0.5)
    k2 = int(np.argmax(np.convolve(h2, np.ones(3), "same")))
    xcen = e2[k2] + 0.5
    sel2 = tops[np.abs(tops - xcen) <= 1.6]
    xline = sel2.mean()
    return dict(
        y0=int(y0), y1=int(y1), n=len(cs),
        base_px=float(base + y0),
        xh=float(base - xline),
        asc=float(base - np.percentile(tops, 2)),
        desc=float(np.percentile(bots, 98) - base),
        frac_base=float(len(sel) / len(cs)),
        frac_x=float(len(sel2) / len(cs)),
    )


# ------------------------------------------------------------------- pitch
def fit_pitch(lefts, plo, phi, step=0.01):
    L = np.asarray(sorted(lefts), float)
    if len(L) < 8:
        return None, None
    best = (None, 9e9)
    for p in np.arange(plo, phi, step):
        k = L / p
        fr = k - np.floor(k)
        ph = np.angle(np.exp(2j * np.pi * fr).mean()) / (2 * np.pi)
        d = np.abs(((k - ph + 0.5) % 1.0) - 0.5)
        s = float(d.mean())
        if s < best[1]:
            best = (float(p), s)
    return best


def line_pitch(ink, y0, y1, plo=18.0, phi=60.0):
    cs = comps_of(ink[y0:y1], min_area=8)
    if len(cs) < 10:
        return None
    lefts = [c["x0"] for c in cs]
    p, s = fit_pitch(lefts, plo, phi)
    if p is None:
        return None
    return dict(pitch=p, resid=s, n=len(cs), x0=cs[0]["x0"], x1=cs[-1]["x1"])


# =========================================================== stages
def stage_rects(a):
    mi = mask_index()
    print("printed xref   px_w  px_h   rect(pt, reading frame)            dpi")
    for p in sorted(mi):
        m = mi[p]
        r = m["rect_rot"]
        print(f"  {p}   x{m['xref']:<4d} {m['w']:5d} {m['h']:5d}  "
              f"({r[0]:6.1f},{r[1]:6.1f})-({r[2]:6.1f},{r[3]:6.1f})  "
              f"{m['dpi'][0]:.1f}x{m['dpi'][1]:.1f}")
    json.dump({str(k): {kk: vv for kk, vv in v.items()} for k, v in mi.items()},
              open(f"{OUT}/rects.json", "w"), indent=1)


def stage_lines(a):
    mi = mask_index()
    for p in sorted(mi):
        ink, m = load(p, mi)
        bands = line_bands(ink)
        print(f"\n== p{p}  mask {m['w']}x{m['h']}  {len(bands)} bands")
        for i, (y0, y1) in enumerate(bands):
            cols = ink[y0:y1].sum(0)
            nz = np.nonzero(cols)[0]
            print(f" {i:3d} y {y0:5d}-{y1:5d} h{y1-y0:4d} "
                  f"x {nz[0]:5d}-{nz[-1]:5d} ink {int(ink[y0:y1].sum()):7d} "
                  f"ypt {pxpt_y(m,y0):6.1f}")


def stage_vmet(a):
    mi = mask_index()
    rows = []
    for p in sorted(mi):
        ink, m = load(p, mi)
        print(f"\n== p{p}")
        for i, (y0, y1) in enumerate(line_bands(ink)):
            v = vmetrics(ink, y0, y1)
            if not v:
                continue
            pt = lambda z: z * PT_PER_PX
            print(f" {i:3d} n={v['n']:3d} xh={v['xh']:6.2f}px/{pt(v['xh']):5.2f}pt "
                  f"asc={v['asc']:6.2f}/{pt(v['asc']):5.2f} "
                  f"desc={v['desc']:5.2f}/{pt(v['desc']):4.2f} "
                  f"fb={v['frac_base']:.2f} fx={v['frac_x']:.2f} "
                  f"h={y1-y0}")
            v["page"] = p; v["idx"] = i
            rows.append(v)
    json.dump(rows, open(f"{OUT}/vmet.json", "w"), indent=1)


def stage_pitch(a):
    mi = mask_index()
    rows = []
    for p in sorted(mi):
        ink, m = load(p, mi)
        print(f"\n== p{p}")
        for i, (y0, y1) in enumerate(line_bands(ink)):
            r = line_pitch(ink, y0, y1)
            if not r:
                continue
            print(f" {i:3d} n={r['n']:3d} pitch={r['pitch']:6.2f}px "
                  f"={r['pitch']*PT_PER_PX:5.2f}pt resid={r['resid']:.3f} "
                  f"w={(r['x1']-r['x0'])*PT_PER_PX:6.1f}pt")
            r["page"] = p; r["idx"] = i; r["y0"] = y0; r["y1"] = y1
            rows.append(r)
    json.dump(rows, open(f"{OUT}/pitch.json", "w"), indent=1)


# ------------------------------------------------------------------ deskew
def skew_angle(ink, lo=-1.6, hi=1.6, step=0.05, band=None):
    """
    Estimate page skew by maximising the variance of the row-ink projection
    (sharpest line separation) over shear angles. Returns degrees.
    """
    a = ink if band is None else ink[band[0]:band[1]]
    ys, xs = np.nonzero(a)
    if len(ys) > 400_000:
        k = np.random.RandomState(0).choice(len(ys), 400_000, replace=False)
        ys, xs = ys[k], xs[k]
    xc = xs.mean()
    best = (0.0, -1.0)
    H = a.shape[0]
    for deg in np.arange(lo, hi + 1e-9, step):
        t = math.tan(math.radians(deg))
        yy = np.clip((ys + (xs - xc) * t).astype(np.int32), 0, H - 1)
        prof = np.bincount(yy, minlength=H).astype(float)
        v = float(prof.var())
        if v > best[1]:
            best = (float(deg), v)
    return best


def deskew(ink, deg):
    if abs(deg) < 0.01:
        return ink
    im = Image.fromarray((ink * 255).astype(np.uint8))
    im = im.rotate(-deg, resample=Image.BILINEAR, expand=False, fillcolor=0)
    return np.array(im) > 100


def stage_skew(a):
    mi = mask_index()
    for p in sorted(mi):
        ink, m = load(p, mi)
        d, v = skew_angle(ink)
        ink2 = deskew(ink, d)
        d2, v2 = skew_angle(ink2, -0.4, 0.4, 0.02)
        print(f"p{p}: skew {d:+.2f} deg  varratio {v/ink.sum():.1f} -> residual {d2:+.2f}")



# ------------------------------------------- profile-based vertical metrics
def prof_metrics(ink, y0, y1, thr_x=0.5, thr_e=0.08):
    """
    Vertical metrics from the ROW-INK PROFILE of a line, which is immune to the
    stroke breaks that fragment connected components in this distressed face.
      x-band  = contiguous run where r(y) >= thr_x * max(r)   (baseline..x-line)
      asc/desc = outermost y where r(y) >= thr_e * max(r)
    """
    r = ink[y0:y1].sum(1).astype(float)
    if r.max() < 5:
        return None
    m = r.max()
    ky = int(np.argmax(r))
    hi = r >= thr_x * m
    a = ky
    while a > 0 and hi[a - 1]:
        a -= 1
    b = ky
    while b < len(r) - 1 and hi[b + 1]:
        b += 1
    lo = r >= thr_e * m
    nz = np.nonzero(lo)[0]
    return dict(y0=int(y0), y1=int(y1), xtop=int(a), xbot=int(b),
                xh=float(b - a + 1), asc=float(b - nz[0] + 1),
                desc=float(nz[-1] - b), peak=float(m),
                ink=int(ink[y0:y1].sum()))


def autocorr_pitch(ink, y0, y1, lo=18, hi=60):
    """Character pitch from the autocorrelation of the column-ink profile."""
    c = ink[y0:y1].sum(0).astype(float)
    nz = np.nonzero(c)[0]
    if len(nz) < 50:
        return None
    c = c[nz[0]:nz[-1] + 1]
    c = c - c.mean()
    n = len(c)
    if n < 4 * hi:
        return None
    f = np.fft.rfft(c, 4 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac /= ac[0] if ac[0] else 1
    seg = ac[lo:hi + 1]
    k = int(np.argmax(seg)) + lo
    # parabolic refine
    if lo < k < hi:
        y1_, y2_, y3_ = ac[k - 1], ac[k], ac[k + 1]
        d = (y1_ - y3_) / (2 * (y1_ - 2 * y2_ + y3_)) if (y1_ - 2 * y2_ + y3_) else 0
        kk = k + float(np.clip(d, -1, 1))
    else:
        kk = float(k)
    return dict(pitch=kk, peak=float(ac[k]), width=int(len(c)))


def body_lines(ink, xh_lo=25, xh_hi=40, min_ink=2500):
    out = []
    for (y0, y1) in line_bands(ink):
        pm = prof_metrics(ink, y0, y1)
        if not pm:
            continue
        if xh_lo <= pm["xh"] <= xh_hi and pm["ink"] >= min_ink:
            out.append(pm)
    return out


def stage_body(a):
    mi = mask_index()
    summ = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        rows = []
        print(f"\n== p{p}")
        for (y0, y1) in line_bands(ink):
            pm = prof_metrics(ink, y0, y1)
            if not pm or pm["ink"] < 1500:
                continue
            ac = autocorr_pitch(ink, y0, y1)
            pm["pitch"] = ac["pitch"] if ac else None
            pm["acpeak"] = ac["peak"] if ac else None
            rows.append(pm)
            print(f"  y{y0:5d} h{y1-y0:4d} ink{pm['ink']:7d} xh {pm['xh']:5.1f}px"
                  f"/{pm['xh']*PT_PER_PX:5.2f}pt asc {pm['asc']:5.1f} desc {pm['desc']:5.1f}"
                  f" pitch {pm['pitch'] if pm['pitch'] is None else round(pm['pitch'],2)}"
                  f" acp {pm['acpeak'] if pm['acpeak'] is None else round(pm['acpeak'],3)}")
        summ[p] = rows
    json.dump(summ, open(f"{OUT}/body.json", "w"), indent=1)



# --------------------------------------------------- glyph boxes (merged)
def glyph_boxes(ink, y0, y1, min_area=5, ov=0.45):
    """
    Connected components merged back into glyphs. This face breaks strokes, so
    a single letter can arrive as 2-3 components stacked vertically; merge any
    components whose x-ranges overlap by >= `ov` of the narrower one.
    """
    cs = comps_of(ink[y0:y1], min_area=min_area)
    if not cs:
        return []
    boxes = []
    for c in cs:
        placed = False
        for b in boxes:
            o = min(b["x1"], c["x1"]) - max(b["x0"], c["x0"])
            w = min(b["x1"] - b["x0"], c["x1"] - c["x0"])
            if w > 0 and o >= ov * w:
                b["x0"] = min(b["x0"], c["x0"]); b["x1"] = max(b["x1"], c["x1"])
                b["y0"] = min(b["y0"], c["y0"]); b["y1"] = max(b["y1"], c["y1"])
                b["area"] += c["area"]; b["parts"] += 1
                placed = True
                break
        if not placed:
            boxes.append(dict(c, parts=1))
    boxes.sort(key=lambda b: b["x0"])
    return boxes


def mode1(v, binw=1.0, smooth=3):
    v = np.asarray(v, float)
    if len(v) == 0:
        return None, 0
    e = np.arange(v.min() - binw, v.max() + 2 * binw, binw)
    h, _ = np.histogram(v, bins=e)
    hs = np.convolve(h, np.ones(smooth), "same")
    k = int(np.argmax(hs))
    lo, hi = e[k] - binw, e[k] + 2 * binw
    sel = v[(v >= lo) & (v <= hi)]
    return (float(sel.mean()) if len(sel) else float(e[k])), int(len(sel))


def line_metrics(ink, y0, y1):
    """x-height, cap-height, ascender, descender, baseline - from merged glyphs."""
    bs = glyph_boxes(ink, y0, y1)
    bs = [b for b in bs if (b["x1"] - b["x0"]) >= 3 and b["area"] >= 12]
    if len(bs) < 12:
        return None
    tops = np.array([b["y0"] for b in bs], float)
    bots = np.array([b["y1"] for b in bs], float)
    hts = bots - tops
    base, nb = mode1(bots)
    xh, nx = mode1(hts)                       # most letters are x-height only
    on = np.abs(bots - base) <= 2.0           # glyphs sitting on the baseline
    tall = hts[on & (hts > xh + 3)]
    cap, nc = mode1(tall) if len(tall) >= 4 else (None, 0)
    asc = float(base - np.percentile(tops, 2))
    desc = float(np.percentile(bots, 98) - base)
    return dict(y0=int(y0), y1=int(y1), n=len(bs), nbase=nb, nx=nx, ncap=nc,
                base=float(base + y0), xh=float(xh),
                cap=(float(cap) if cap else None), asc=asc, desc=desc,
                parts=float(np.mean([b["parts"] for b in bs])),
                ink=int(ink[y0:y1].sum()))


def stage_metrics(a):
    mi = mask_index()
    allrows = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        rows = []
        print(f"\n== p{p}")
        for (y0, y1) in line_bands(ink):
            lm = line_metrics(ink, y0, y1)
            if not lm:
                continue
            ac = autocorr_pitch(ink, y0, y1)
            lm["pitch"] = float(ac["pitch"]) if ac else None
            lm["acpeak"] = float(ac["peak"]) if ac else None
            rows.append(lm)
            capf = f"{lm['cap']:5.1f}" if lm["cap"] else "   - "
            pf = f"{lm['pitch']:5.2f}" if lm["pitch"] else "  -  "
            print(f"  y{y0:5d} n{lm['n']:4d} xh{lm['xh']:6.2f}({lm['nx']:3d}) "
                  f"cap{capf}({lm['ncap']:3d}) asc{lm['asc']:6.1f} desc{lm['desc']:5.1f} "
                  f"base{lm['base']:8.1f} pitch{pf} parts{lm['parts']:4.2f}")
        allrows[p] = rows
    json.dump(allrows, open(f"{OUT}/metrics.json", "w"), indent=1)



# ------------------------------------------- robust per-line body metrics
def line_body(ink, y0, y1, min_glyphs=15):
    """
    Body-face metrics for one line, robust to the face's stroke breaks.
      baseline  = mode of merged-glyph bottom edges
      x-height  = 30th pct of heights of BASELINE-SITTING glyphs (x-only
                  letters are ~2/3 of them, so p30 sits inside that class)
      asc/cap   = 90th pct of the same
      descender = how far below baseline the p98 bottom reaches
      pitch     = mode of adjacent glyph-box left-edge differences
    """
    bs = glyph_boxes(ink, y0, y1)
    bs = [b for b in bs if (b["x1"] - b["x0"]) >= 5 and b["area"] >= 25]
    if len(bs) < min_glyphs:
        return None
    bots = np.array([b["y1"] for b in bs], float)
    base, nb = mode1(bots)
    on = [b for b in bs if abs(b["y1"] - base) <= 2.5]
    if len(on) < min_glyphs:
        return None
    h = np.array([b["y1"] - b["y0"] for b in on], float)
    xh = float(np.percentile(h, 30))
    tall = float(np.percentile(h, 90))
    desc = float(np.percentile(bots, 98) - base)
    lefts = np.array([b["x0"] for b in bs], float)
    d = np.diff(lefts)
    d = d[(d >= 8) & (d <= 70)]
    pmode, pn = mode1(d, binw=1.0) if len(d) >= 8 else (None, 0)
    return dict(y0=int(y0), y1=int(y1), n=len(bs), non=len(on),
                base=float(base + y0), xh=xh, tall=tall, desc=desc,
                pitch_mode=pmode, pitch_n=pn,
                x_left=float(bs[0]["x0"]), x_right=float(bs[-1]["x1"]))


def stage_size(a):
    """Per-page body face size: is every page set at the same point size?"""
    mi = mask_index()
    print(f"{'pg':>4} {'lines':>5} {'x-ht px':>9} {'x-ht pt':>8} {'asc/cap':>8} "
          f"{'desc':>6} {'pitch px':>9} {'pitch pt':>8} {'lead px':>8} {'lead pt':>8}")
    tab = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        rows = []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if lb and 20 <= lb["xh"] <= 45:
                rows.append(lb)
        if not rows:
            print(f"{p:>4}   (no body lines)")
            continue
        xh = np.array([r["xh"] for r in rows])
        tl = np.array([r["tall"] for r in rows])
        de = np.array([r["desc"] for r in rows])
        pi = np.array([r["pitch_mode"] for r in rows if r["pitch_mode"]])
        bases = np.array(sorted(r["base"] for r in rows))
        lead = np.diff(bases)
        lead = lead[(lead > 40) & (lead < 200)]
        lm, _ = mode1(lead, binw=2.0) if len(lead) >= 3 else (float("nan"), 0)
        tab[p] = dict(n=len(rows), xh=float(np.median(xh)), xh_sd=float(xh.std()),
                      tall=float(np.median(tl)), desc=float(np.median(de)),
                      pitch=float(np.median(pi)), lead=float(lm))
        print(f"{p:>4} {len(rows):>5} {np.median(xh):9.2f} {np.median(xh)*PT_PER_PX:8.3f} "
              f"{np.median(tl):8.2f} {np.median(de):6.2f} {np.median(pi):9.2f} "
              f"{np.median(pi)*PT_PER_PX:8.3f} {lm:8.2f} {lm*PT_PER_PX:8.3f}")
    json.dump(tab, open(f"{OUT}/size.json", "w"), indent=1)
    return tab



def stage_inventory(a):
    """Every line on every masked page with its x-height -> the size inventory."""
    mi = mask_index()
    out = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        rows = []
        print(f"\n== p{p}")
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1, min_glyphs=8)
            if not lb:
                continue
            rows.append(lb)
            print(f"  y{y0:5d} ypt{pxpt_y(m,y0):6.1f} n{lb['n']:4d} "
                  f"xh{lb['xh']:6.1f}px/{lb['xh']*PT_PER_PX:5.2f}pt "
                  f"tall{lb['tall']:6.1f} desc{lb['desc']:5.1f} "
                  f"pitch{(lb['pitch_mode'] or 0):6.1f} "
                  f"xL{lb['x_left']:6.0f} xR{lb['x_right']:6.0f}")
        out[p] = rows
    json.dump(out, open(f"{OUT}/inventory.json", "w"), indent=1)


def pooled_xheight(ink, lines, lo=20, hi=45):
    """Sub-pixel x-height: pool baseline-sitting glyph heights over body lines."""
    H = []
    for (y0, y1) in lines:
        bs = glyph_boxes(ink, y0, y1)
        bs = [b for b in bs if (b["x1"] - b["x0"]) >= 5 and b["area"] >= 25]
        if len(bs) < 15:
            continue
        bots = np.array([b["y1"] for b in bs], float)
        base, _ = mode1(bots)
        for b in bs:
            if abs(b["y1"] - base) <= 2.5:
                H.append(b["y1"] - b["y0"])
    H = np.array(H, float)
    H = H[(H >= lo) & (H <= hi)]
    if len(H) < 50:
        return None
    # lowest mode = x-height class
    e = np.arange(lo - 0.5, hi + 1.5, 1.0)
    h, _ = np.histogram(H, bins=e)
    k = int(np.argmax(h[: int(len(h) * 0.6)]))
    c = e[k] + 0.5
    sel = H[np.abs(H - c) <= 2.0]
    return dict(xh=float(sel.mean()), sd=float(sel.std()), n=int(len(sel)),
                ntot=int(len(H)), sem=float(sel.std() / math.sqrt(len(sel))))


def stage_xheight(a):
    mi = mask_index()
    print(" pg   nlines    x-height px   sd    sem     n      pt      implied pt size")
    for p in sorted(mi):
        ink, m = load(p, mi)
        lines = []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if lb and 27 <= lb["xh"] <= 36:
                lines.append((y0, y1))
        r = pooled_xheight(ink, lines)
        if not r:
            print(f" {p}  (none)")
            continue
        print(f" {p}   {len(lines):4d}    {r['xh']:8.3f}  {r['sd']:5.3f} {r['sem']:6.4f} "
              f"{r['n']:5d}  {r['xh']*PT_PER_PX:6.3f}   x-ht/em~0.46 -> "
              f"{r['xh']*PT_PER_PX/0.46:5.2f}pt")



# ----------------------------------------------------- highlight-bar text
def load_bars(path=None):
    path = path or os.path.join(HERE, "..", "bars.tsv")
    rows = []
    for ln in open(path):
        f = ln.rstrip("\n").split("\t")
        if f[0] == "page":
            continue
        rows.append(dict(page=int(f[0]), colour=f[1], x0=int(f[2]), x1=int(f[3]),
                         y=int(f[4]), w=int(f[5]), h=int(f[6])))
    return rows


def full400_to_mask(m, X, Y):
    """bars.tsv coords are the 3400x4400 full-page 400 dpi render (un-rotated)."""
    return X - m["rect_rot"][0] * 400 / 72.0, Y - m["rect_rot"][1] * 400 / 72.0


def stroke_width(sub):
    """Median horizontal run length of ink = stem width, in px."""
    runs = []
    for row in sub:
        x = 0
        n = len(row)
        while x < n:
            if row[x]:
                j = x
                while j < n and row[j]:
                    j += 1
                if j - x <= 30:
                    runs.append(j - x)
                x = j
            else:
                x += 1
    return (float(np.median(runs)), len(runs)) if runs else (float("nan"), 0)


def block_metrics(ink, y0, y1, x0, x1, tag=""):
    bs = glyph_boxes(ink[:, x0:x1], y0, y1)
    bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 20]
    if len(bs) < 6:
        return None
    bots = np.array([b["y1"] for b in bs], float)
    base, _ = mode1(bots)
    on = [b for b in bs if abs(b["y1"] - base) <= 3.0]
    if len(on) < 5:
        return None
    h = np.array([b["y1"] - b["y0"] for b in on], float)
    w = np.array([b["x1"] - b["x0"] for b in on], float)
    sw, nr = stroke_width(ink[y0:y1, x0:x1])
    lefts = np.array([b["x0"] for b in bs], float)
    d = np.diff(lefts); d = d[(d >= 6) & (d <= 90)]
    pm, pn = mode1(d, binw=1.0) if len(d) >= 5 else (None, 0)
    return dict(tag=tag, n=len(bs), non=len(on),
                xh=float(np.percentile(h, 30)), tall=float(np.percentile(h, 90)),
                wmed=float(np.median(w)), sw=sw,
                pitch=pm, pitch_n=pn, base=float(base + y0))


def stage_bars(a):
    """Is the text on the orange bars the same face and size as the body?"""
    mi = mask_index()
    bars = load_bars()
    print(" pg  bar          xh_px  tall  stroke  pitch  n   | body xh  body stroke")
    bodyref = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        lines = [(y0, y1) for (y0, y1) in line_bands(ink)
                 if (lb := line_body(ink, y0, y1)) and 27 <= lb["xh"] <= 36]
        H, SW = [], []
        for (y0, y1) in lines:
            bm = block_metrics(ink, y0, y1, 0, ink.shape[1])
            if bm:
                H.append(bm["xh"]); SW.append(bm["sw"])
        bodyref[p] = (float(np.median(H)) if H else float("nan"),
                      float(np.median(SW)) if SW else float("nan"))
    for p in sorted(mi):
        if p not in (75, 76, 78, 79):
            continue
        ink, m = load(p, mi)
        for b in [b for b in bars if b["page"] == p]:
            mx0, my0 = full400_to_mask(m, b["x0"], b["y"])
            mx1, my1 = full400_to_mask(m, b["x1"], b["y"] + b["h"])
            x0, x1 = int(max(0, mx0)), int(min(ink.shape[1], mx1))
            y0, y1 = int(max(0, my0)), int(min(ink.shape[0], my1))
            if x1 - x0 < 40 or y1 - y0 < 20:
                continue
            bm = block_metrics(ink, y0, y1, x0, x1, tag=f"{b['x0']},{b['y']}")
            if not bm:
                print(f" {p}  {b['x0']:5d},{b['y']:5d}  (no glyphs)")
                continue
            print(f" {p}  {b['x0']:5d},{b['y']:5d} {bm['xh']:7.1f} {bm['tall']:5.1f} "
                  f"{bm['sw']:6.1f} {(bm['pitch'] or 0):6.1f} {bm['n']:3d}  | "
                  f"{bodyref[p][0]:7.1f} {bodyref[p][1]:6.1f}")



def find_bars(printed):
    """Orange highlight bars from the 200 dpi colour layer, rotated to reading
    order, returned in MASK pixel coordinates."""
    fn = glob.glob(f"{SC}/p{printed}_x*_1700x2200.jpeg")[0]
    c = np.array(Image.open(fn).convert("RGB"))[::-1, ::-1]
    R, G, B = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
    orange = (R > 150) & (G > 40) & (G < 185) & (B < 120) & (R - B > 70)
    lab, n = ndimage.label(orange)
    out = []
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        sy, sx = sl
        h, w = sy.stop - sy.start, sx.stop - sx.start
        if w < 60 or h < 12 or h > 60 or w / h < 3:
            continue
        out.append(dict(cx0=sx.start, cx1=sx.stop, cy0=sy.start, cy1=sy.stop))
    out.sort(key=lambda b: (b["cy0"], b["cx0"]))
    return out


def stage_bars2(a):
    """Bar text vs body text: same face, same size?"""
    mi = mask_index()
    print(" pg  bar(colour px)      glyphs  xh_px   tall  stroke  sw/xh   pitch")
    agg = {}
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        rx0 = m["rect_rot"][0] * 400 / 72.0
        ry0 = m["rect_rot"][1] * 400 / 72.0
        body = []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if lb and 27 <= lb["xh"] <= 36:
                bm = block_metrics(ink, y0, y1, 0, ink.shape[1])
                if bm:
                    body.append(bm)
        bxh = float(np.median([b["xh"] for b in body]))
        bsw = float(np.median([b["sw"] for b in body]))
        bp = float(np.median([b["pitch"] for b in body if b["pitch"]]))
        print(f" p{p} BODY ({len(body)} lines)        {bxh:7.2f} "
              f"{np.median([b['tall'] for b in body]):6.2f} {bsw:6.2f} "
              f"{bsw/bxh:6.3f} {bp:7.2f}")
        rows = []
        for b in find_bars(p):
            x0 = int(b["cx0"] * 2 - rx0); x1 = int(b["cx1"] * 2 - rx0)
            y0 = int(b["cy0"] * 2 - ry0); y1 = int(b["cy1"] * 2 - ry0)
            x0, x1 = max(0, x0), min(ink.shape[1], x1)
            y0, y1 = max(0, y0 - 6), min(ink.shape[0], y1 + 6)
            if x1 - x0 < 60 or y1 - y0 < 20:
                continue
            bm = block_metrics(ink, y0, y1, x0, x1)
            if not bm:
                continue
            rows.append(bm)
            print(f"      ({b['cx0']:4d},{b['cy0']:4d})-({b['cx1']:4d},{b['cy1']:4d})"
                  f" {bm['n']:4d} {bm['xh']:7.2f} {bm['tall']:6.2f} {bm['sw']:6.2f} "
                  f"{bm['sw']/bm['xh']:6.3f} {(bm['pitch'] or 0):7.2f}")
        if rows:
            agg[p] = dict(body_xh=bxh, body_sw=bsw, body_pitch=bp,
                          bar_xh=float(np.median([r["xh"] for r in rows])),
                          bar_sw=float(np.median([r["sw"] for r in rows])),
                          bar_pitch=float(np.median([r["pitch"] for r in rows if r["pitch"]])),
                          nbars=len(rows))
    print("\nSUMMARY  page  bars  body_xh  bar_xh   body_sw  bar_sw  sw_ratio  "
          "body_pitch bar_pitch")
    for p, v in agg.items():
        print(f"         {p}    {v['nbars']:3d}  {v['body_xh']:7.2f} {v['bar_xh']:7.2f}  "
              f"{v['body_sw']:7.2f} {v['bar_sw']:7.2f}  {v['bar_sw']/v['body_sw']:8.3f}  "
              f"{v['body_pitch']:9.2f} {v['bar_pitch']:8.2f}")
    json.dump(agg, open(f"{OUT}/bars.json", "w"), indent=1)



def grid_fit(lefts, plo=28.0, phi=40.0, step=0.005):
    """Fine grid fit of a fixed pitch to merged-glyph left edges."""
    L = np.asarray(sorted(lefts), float)
    if len(L) < 12:
        return None
    L = L - L[0]
    best = (None, 9e9, None)
    for pp in np.arange(plo, phi, step):
        k = L / pp
        fr = k - np.floor(k)
        ph = np.angle(np.exp(2j * np.pi * fr).mean()) / (2 * np.pi)
        d = np.abs(((k - ph + 0.5) % 1.0) - 0.5)
        sc = float(np.median(d))
        if sc < best[1]:
            best = (float(pp), sc, float(ph))
    return dict(pitch=best[0], resid=best[1], phase=best[2], n=len(L),
                span=float(L[-1]))


def stage_pitchfine(a):
    """Character pitch per page, fine grid fit on merged glyph left edges."""
    mi = mask_index()
    print(" pg  lines  pitch_px   sd     pitch_pt   resid   cells/in   span_med")
    tab = {}
    for p in sorted(mi):
        ink, m = load(p, mi)
        vals, res, spans = [], [], []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if not (lb and 27 <= lb["xh"] <= 36):
                continue
            bs = glyph_boxes(ink, y0, y1)
            bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 18]
            g = grid_fit([b["x0"] for b in bs])
            if g and g["span"] > 1200:
                vals.append(g["pitch"]); res.append(g["resid"]); spans.append(g["span"])
        if len(vals) < 3:
            print(f" {p}   (too few lines: {len(vals)})")
            continue
        v = np.array(vals)
        tab[p] = dict(n=len(v), pitch=float(np.median(v)), sd=float(v.std()),
                      resid=float(np.median(res)))
        print(f" {p}   {len(v):4d}  {np.median(v):8.3f} {v.std():6.3f}  "
              f"{np.median(v)*PT_PER_PX:8.4f}  {np.median(res):6.3f}  "
              f"{400/np.median(v):8.3f}  {np.median(spans):8.0f}")
    json.dump(tab, open(f"{OUT}/pitchfine.json", "w"), indent=1)



def joint_pitch(linelefts, plo=26.0, phi=42.0, step=0.002):
    """
    One pitch for the whole page: every line shares the pitch but has its own
    phase. Score = mean over lines of the median |distance to nearest cell|.
    """
    grid = np.arange(plo, phi, step)
    sc = np.zeros(len(grid))
    for L in linelefts:
        L = np.asarray(sorted(L), float)
        L = L - L[0]
        col = np.empty(len(grid))
        for j, pp in enumerate(grid):
            k = L / pp
            fr = k - np.floor(k)
            ph = np.angle(np.exp(2j * np.pi * fr).mean()) / (2 * np.pi)
            d = np.abs(((k - ph + 0.5) % 1.0) - 0.5)
            col[j] = np.median(d)
        sc += col
    sc /= max(1, len(linelefts))
    k = int(np.argmin(sc))
    return dict(pitch=float(grid[k]), score=float(sc[k]),
                curve=(grid, sc), nlines=len(linelefts))


def page_linelefts(ink, xh_lo=27, xh_hi=36, min_glyphs=25):
    out = []
    for (y0, y1) in line_bands(ink):
        lb = line_body(ink, y0, y1)
        if not (lb and xh_lo <= lb["xh"] <= xh_hi):
            continue
        bs = glyph_boxes(ink, y0, y1)
        bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 18]
        if len(bs) >= min_glyphs:
            out.append([b["x0"] for b in bs])
    return out


def stage_pitchjoint(a):
    mi = mask_index()
    print(" pg  lines   pitch_px   pitch_pt   cpi     score   2nd-best")
    tab = {}
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        LL = page_linelefts(ink)
        if len(LL) < 3:
            print(f" {p}  too few lines"); continue
        r = joint_pitch(LL)
        g, sc = r["curve"]
        # second-best local minimum, at least 1.5 px away
        mask = np.abs(g - r["pitch"]) > 1.5
        k2 = int(np.argmin(np.where(mask, sc, 9e9)))
        tab[p] = dict(pitch=r["pitch"], score=r["score"], nlines=r["nlines"])
        print(f" {p}   {r['nlines']:4d}  {r['pitch']:9.3f}  {r['pitch']*PT_PER_PX:8.4f}  "
              f"{400/r['pitch']:6.3f}  {r['score']:.4f}  {g[k2]:.3f}@{sc[k2]:.4f}")
        np.save(f"{OUT}/pitchcurve_{p}.npy", np.vstack([g, sc]))
    json.dump(tab, open(f"{OUT}/pitchjoint.json", "w"), indent=1)



# ------------------------------------------------- transcript alignment
def transcript_pages(path=None):
    path = path or os.path.join(HERE, "..", "article_transcript.txt")
    pages, cur = {}, None
    for ln in open(path):
        ln = ln.rstrip("\n")
        if ln.startswith("#"):
            continue
        if ln.startswith("=== PAGE"):
            cur = int(ln.split()[2]); pages[cur] = []
            continue
        if cur and ln.strip():
            pages[cur].append(ln)
    return pages


def mask_text_lines(ink, xh_lo=27, xh_hi=36):
    rows = []
    for (y0, y1) in line_bands(ink):
        lb = line_body(ink, y0, y1)
        if not (lb and xh_lo <= lb["xh"] <= xh_hi):
            continue
        bs = glyph_boxes(ink, y0, y1)
        bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 18]
        if len(bs) < 12:
            continue
        rows.append(dict(y0=y0, y1=y1, n=len(bs),
                         left=bs[0]["x0"], right=bs[-1]["x1"],
                         lastleft=bs[-1]["x0"],
                         lefts=[b["x0"] for b in bs],
                         rights=[b["x1"] for b in bs]))
    return rows


def align(mrows, tlines):
    """Monotonic DP: each mask line -> one transcript line, order preserved,
    transcript lines may be skipped (highlighted lines are absent from the mask)."""
    M, T = len(mrows), len(tlines)
    ns = [len(t.strip().replace(" ", "")) for t in tlines]
    INF = 1e9
    dp = np.full((M + 1, T + 1), INF)
    bk = np.zeros((M + 1, T + 1), int)
    dp[0, :] = 0
    for a in range(1, M + 1):
        for b in range(1, T + 1):
            skip = dp[a, b - 1]
            take = dp[a - 1, b - 1] + abs(mrows[a - 1]["n"] - ns[b - 1])
            if take <= skip:
                dp[a, b] = take; bk[a, b] = 1
            else:
                dp[a, b] = skip; bk[a, b] = 0
    a, b = M, T
    pairs = []
    while a > 0 and b > 0:
        if bk[a, b] == 1:
            pairs.append((a - 1, b - 1)); a -= 1; b -= 1
        else:
            b -= 1
    pairs.reverse()
    return pairs, float(dp[M, T])


def stage_align(a):
    """Is the body face monospaced? Regress printed line width on cell count."""
    mi = mask_index()
    tp = transcript_pages()
    allpts = []
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        mr = mask_text_lines(ink)
        tl = tp[p]
        pairs, cost = align(mr, tl)
        good = [(i, j) for i, j in pairs if abs(mr[i]["n"] - len(tl[j].strip().replace(" ", ""))) <= 2]
        print(f"\n== p{p}  mask lines {len(mr)}  transcript lines {len(tl)}  "
              f"matched {len(pairs)}  within2 {len(good)}  cost {cost:.0f}")
        for i, j in pairs:
            t = tl[j]
            st = t.strip()
            cells = len(st) - 1           # first char left -> last char left
            span = mr[i]["lastleft"] - mr[i]["left"]
            pit = span / cells if cells > 0 else float("nan")
            flag = "*" if abs(mr[i]["n"] - len(st.replace(" ", ""))) <= 2 else " "
            print(f" {flag} y{mr[i]['y0']:5d} nglyph{mr[i]['n']:4d} nchar{len(st.replace(' ','')):4d} "
                  f"cells{cells:4d} span{span:6.0f} pitch{pit:7.3f}  {st[:44]}")
            if flag == "*" and cells > 25:
                allpts.append((cells, span, p))
    if allpts:
        C = np.array([x[0] for x in allpts], float)
        S = np.array([x[1] for x in allpts], float)
        A = np.vstack([C, np.ones(len(C))]).T
        sol, res, *_ = np.linalg.lstsq(A, S, rcond=None)
        pred = A @ sol
        r2 = 1 - ((S - pred) ** 2).sum() / ((S - S.mean()) ** 2).sum()
        print(f"\nREGRESSION over {len(C)} confidently-matched lines")
        print(f"  span = {sol[0]:.4f} * cells + {sol[1]:.2f}   R2 = {r2:.5f}")
        print(f"  pitch = {sol[0]:.4f} px = {sol[0]*PT_PER_PX:.4f} pt = {400/sol[0]:.4f} cpi")
        print(f"  residual sd = {(S-pred).std():.2f} px = {(S-pred).std()*PT_PER_PX:.3f} pt")
        for p in (75, 76, 78, 79):
            k = [i for i, x in enumerate(allpts) if x[2] == p]
            if len(k) >= 4:
                c, sv = C[k], S[k]
                a2 = np.vstack([c, np.ones(len(c))]).T
                so, *_ = np.linalg.lstsq(a2, sv, rcond=None)
                print(f"  p{p}: pitch {so[0]:.4f} px ({so[0]*PT_PER_PX:.4f} pt) "
                      f"from {len(k)} lines")



# --------------------------------------- exact glyph <-> character mapping
def exact_lines(p, mi=None, slack=0):
    """
    Mask lines whose merged-glyph count EXACTLY equals the transcript line's
    non-space character count. Those give an unambiguous glyph->character map.
    """
    mi = mi or mask_index()
    ink, m = load(p, mi)
    mr = mask_text_lines(ink)
    tl = transcript_pages()[p]
    pairs, _ = align(mr, tl)
    out = []
    for i, j in pairs:
        st = tl[j].strip()
        ns = st.replace(" ", "")
        if abs(mr[i]["n"] - len(ns)) <= slack and len(ns) >= 20:
            out.append((mr[i], st, ns))
    return ink, m, out


def stage_words(a):
    """
    Per-word character pitch and inter-word gaps, in exact cell counts,
    from lines where glyph count == transcript non-space character count.
    """
    mi = mask_index()
    allpitch, gaps = [], []
    for p in (75, 76, 78, 79):
        ink, m, rows = exact_lines(p, mi)
        print(f"\n== p{p}: {len(rows)} exactly-matched lines")
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            # index of each non-space char in the stripped line
            idx = [k for k, c in enumerate(st) if c != " "]
            # adjacent pairs INSIDE a word (no space between) -> pitch samples
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10:
                continue
            pit = float(np.median(ins))
            allpitch.append((p, mr["y0"], pit, len(ins)))
            # gaps: cells between consecutive non-space chars
            for t in range(len(idx) - 1):
                cells = idx[t + 1] - idx[t]
                if cells == 1:
                    continue
                meas = (L[t + 1] - L[t]) / pit
                if cells >= 2:
                    gaps.append(dict(page=p, y=int(mr["y0"]), cells=cells,
                                     meas=float(meas), pitch=pit,
                                     ctx=st[max(0, idx[t] - 14):idx[t + 1] + 8]))
            print(f"   y{mr['y0']:5d} pitch {pit:6.3f}px/{pit*PT_PER_PX:5.3f}pt "
                  f"n{len(ins):3d} sd{np.std(ins):5.2f}  {st[:48]}")
    P = np.array([x[2] for x in allpitch])
    print(f"\nPITCH over {len(P)} lines: median {np.median(P):.4f} px "
          f"= {np.median(P)*PT_PER_PX:.4f} pt = {400/np.median(P):.3f} cpi, "
          f"sd {P.std():.3f} px")
    for p in (75, 76, 78, 79):
        v = np.array([x[2] for x in allpitch if x[0] == p])
        if len(v):
            print(f"   p{p}: n={len(v)} median {np.median(v):.4f} px "
                  f"({np.median(v)*PT_PER_PX:.4f} pt) sd {v.std():.3f}")
    print("\nGAPS wider than one cell (cells = transcript, meas = measured/pitch)")
    print(f"{'pg':>3} {'y':>6} {'cells':>6} {'meas':>7}  context")
    for g in sorted(gaps, key=lambda g: (g["page"], g["y"])):
        print(f"{g['page']:>3} {g['y']:>6} {g['cells']:>6} {g['meas']:>7.2f}  "
              f"{g['ctx']!r}")
    json.dump(dict(pitch=[dict(page=x[0], y=x[1], pitch=x[2], n=x[3]) for x in allpitch],
                   gaps=gaps), open(f"{OUT}/words.json", "w"), indent=1)



def word_samples(pages=(75, 76, 78, 79), sd_max=8.0, mi=None):
    """Per-line pitch and word-space ratios from cleanly mapped lines only."""
    mi = mi or mask_index()
    lines = []
    for p in pages:
        ink, m, rows = exact_lines(p, mi)
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            idx = [k for k, c in enumerate(st) if c != " "]
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10 or np.std(ins) > sd_max:
                continue
            pit = float(np.median(ins))
            sp = [((L[t + 1] - L[t]) / pit, idx[t + 1] - idx[t], t)
                  for t in range(len(idx) - 1) if idx[t + 1] - idx[t] >= 2]
            lines.append(dict(page=p, y=int(mr["y0"]), pitch=pit,
                              sd=float(np.std(ins)), nin=len(ins),
                              text=st, spaces=sp,
                              left=int(mr["left"]), right=int(mr["right"])))
    return lines


def stage_space(a):
    """Word-space width relative to the character advance, and every wide gap."""
    lines = word_samples()
    print(f"clean lines: {len(lines)}")
    P = np.array([l["pitch"] for l in lines])
    print(f"\nCHARACTER ADVANCE  median {np.median(P):.3f} px = "
          f"{np.median(P)*PT_PER_PX:.4f} pt = {400/np.median(P):.3f} cpi  "
          f"(sd across lines {P.std():.3f} px)")
    for p in (75, 76, 78, 79):
        v = np.array([l["pitch"] for l in lines if l["page"] == p])
        if len(v):
            print(f"   p{p}: n={len(v):2d} median {np.median(v):7.3f} px "
                  f"({np.median(v)*PT_PER_PX:6.4f} pt)  min {v.min():.1f} max {v.max():.1f}")
    one = [(l, r) for l in lines for (r, c, t) in l["spaces"] if c == 2]
    R = np.array([r for (_, r) in one])
    print(f"\nSINGLE WORD SPACE: n={len(R)} advance/pitch median {np.median(R):.4f} "
          f"mean {R.mean():.4f} sd {R.std():.4f}")
    print(f"   -> space glyph width = {np.median(R)-1:.4f} character cells "
          f"= {(np.median(R)-1)*np.median(P):.2f} px = "
          f"{(np.median(R)-1)*np.median(P)*PT_PER_PX:.3f} pt")
    for p in (75, 76, 78, 79):
        v = np.array([r for (l, r) in one if l["page"] == p])
        if len(v):
            print(f"   p{p}: n={len(v):3d} median {np.median(v):.4f} sd {v.std():.4f}")
    # per-line word-space medians -> which lines are stretched or squeezed
    print("\nPER-LINE word-space ratio (median over that line's single spaces)")
    out = []
    for l in lines:
        v = [r for (r, c, t) in l["spaces"] if c == 2]
        if len(v) < 3:
            continue
        out.append((float(np.median(v)), l))
    out.sort(key=lambda z: z[0])
    for v, l in out:
        flag = "  <<< SQUEEZED" if v < 1.30 else ("  <<< STRETCHED" if v > 1.80 else "")
        print(f"  p{l['page']} y{l['y']:5d} ratio {v:5.3f} pitch {l['pitch']:5.1f} "
              f"L{l['left']:5d} R{l['right']:5d}  {l['text'][:42]}{flag}")
    print("\nGAPS OF MORE THAN ONE SPACE, measured in cells")
    for l in lines:
        for (r, c, t) in l["spaces"]:
            if c > 2:
                print(f"  p{l['page']} y{l['y']}: transcript {c-1} spaces, "
                      f"measured {r:.2f} cells (pitch {l['pitch']:.1f} px) "
                      f"in {l['text'][:60]!r}")



def stage_mono(a):
    """
    Decisive monospace test: does the character ADVANCE depend on which letter
    it is? In a monospaced face it cannot.
    """
    mi = mask_index()
    per = {}
    widths = {}
    for p in (75, 76, 78, 79):
        ink, m, rows = exact_lines(p, mi)
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            R = np.array(mr["rights"], float)
            idx = [k for k, c in enumerate(st) if c != " "]
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10 or np.std(ins) > 8.0:
                continue
            pit = float(np.median(ins))
            for t in range(len(idx) - 1):
                if idx[t + 1] - idx[t] != 1:
                    continue
                ch = st[idx[t]]
                per.setdefault(ch, []).append((L[t + 1] - L[t]) / pit)
            for t in range(len(idx)):
                widths.setdefault(st[idx[t]], []).append((R[t] - L[t]) / pit)
    print("char   n   advance/pitch   ink width/pitch")
    rows = []
    for ch in sorted(per, key=lambda c: -len(per[c])):
        v = np.array(per[ch]); w = np.array(widths.get(ch, [np.nan]))
        if len(v) < 12:
            continue
        rows.append((ch, len(v), float(np.median(v)), float(v.std()),
                     float(np.median(w))))
        print(f"  {ch!r:>4} {len(v):4d}   {np.median(v):6.3f} +-{v.std():5.3f}   "
              f"{np.median(w):6.3f}")
    A = np.array([r[2] for r in rows])
    W = np.array([r[4] for r in rows])
    print(f"\nADVANCE across {len(rows)} letter identities: "
          f"min {A.min():.3f} ({rows[int(np.argmin(A))][0]!r}) "
          f"max {A.max():.3f} ({rows[int(np.argmax(A))][0]!r}) "
          f"spread {A.max()-A.min():.3f}  sd {A.std():.4f}")
    print(f"INK WIDTH across the same: min {W.min():.3f} max {W.max():.3f} "
          f"spread {W.max()-W.min():.3f}  sd {W.std():.4f}")
    print(f"ratio of between-letter sd, advance vs ink width: "
          f"{A.std()/W.std():.3f}")
    # one-way ANOVA-ish F on advance by letter
    groups = [np.array(per[r[0]]) for r in rows]
    allv = np.concatenate(groups)
    gm = allv.mean()
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in groups)
    ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    dfb, dfw = len(groups) - 1, len(allv) - len(groups)
    print(f"F(advance ~ letter) = {(ssb/dfb)/(ssw/dfw):.3f} on {dfb},{dfw} df")
    groups = [np.array(widths[r[0]]) for r in rows]
    allv = np.concatenate(groups); gm = allv.mean()
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in groups)
    ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    print(f"F(ink width ~ letter) = {(ssb/(len(groups)-1))/(ssw/(len(allv)-len(groups))):.3f}"
          f" on {len(groups)-1},{len(allv)-len(groups)} df")



def stage_alpha(a):
    """
    Decisive monospace test that side bearings cannot fake.

    For a run of n consecutive cells with no space, let r = (x[t+n]-x[t])/n.
      MONOSPACE:    x[t+n]-x[t] = n*pitch + (lsb[t+n]-lsb[t])   -> sd(r) ~ 1/n
      PROPORTIONAL: x[t+n]-x[t] = sum of n letter widths        -> sd(r) ~ 1/sqrt(n)
    Fit sd(r) = C * n^-alpha. alpha near 1.0 = monospace, near 0.5 = proportional.
    """
    mi = mask_index()
    samples = {}
    for p in (75, 76, 78, 79):
        ink, m, rows = exact_lines(p, mi)
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            idx = [k for k, c in enumerate(st) if c != " "]
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10 or np.std(ins) > 8.0:
                continue
            pit = float(np.median(ins))
            for t in range(len(idx)):
                for n in range(1, 15):
                    if t + n >= len(idx):
                        break
                    if idx[t + n] - idx[t] != n:      # a space inside the run
                        break
                    samples.setdefault(n, []).append((L[t + n] - L[t]) / n / pit)
    print("  n   count    mean      sd     sd*n    sd*sqrt(n)")
    ns, sds = [], []
    for n in sorted(samples):
        v = np.array(samples[n])
        if len(v) < 40:
            continue
        v = v[(v > 0.4) & (v < 2.5)]
        ns.append(n); sds.append(v.std())
        print(f" {n:3d} {len(v):6d}  {v.mean():7.4f} {v.std():7.4f} "
              f"{v.std()*n:8.4f} {v.std()*math.sqrt(n):10.4f}")
    ns = np.array(ns, float); sds = np.array(sds)
    A = np.vstack([np.log(ns), np.ones(len(ns))]).T
    sol, *_ = np.linalg.lstsq(A, np.log(sds), rcond=None)
    pred = A @ sol
    r2 = 1 - ((np.log(sds) - pred) ** 2).sum() / ((np.log(sds) - np.log(sds).mean()) ** 2).sum()
    print(f"\n  sd(r) = {math.exp(sol[1]):.4f} * n^({sol[0]:+.4f})   R2={r2:.4f}")
    print(f"  alpha = {-sol[0]:.4f}   (1.0 = monospace, 0.5 = proportional)")



def alpha_from(samples, nmax=8, nmin_count=40):
    ns, sds, cnt = [], [], []
    for n in sorted(samples):
        if n > nmax:
            break
        v = np.array(samples[n])
        v = v[(v > 0.4) & (v < 2.5)]
        if len(v) < nmin_count:
            continue
        ns.append(n); sds.append(v.std()); cnt.append(len(v))
    ns = np.array(ns, float); sds = np.array(sds)
    A = np.vstack([np.log(ns), np.ones(len(ns))]).T
    sol, *_ = np.linalg.lstsq(A, np.log(sds), rcond=None)
    # variance decomposition:  sd^2 * n = A + B/n
    y = sds ** 2 * ns
    M = np.vstack([np.ones(len(ns)), 1.0 / ns]).T
    ab, *_ = np.linalg.lstsq(M, y, rcond=None)
    return dict(alpha=float(-sol[0]), ns=ns, sds=sds, cnt=cnt,
                A=float(ab[0]), B=float(ab[1]))


def synth_samples(kind, nlines=32, ncells=55, seed=0, pitch=35.0, noise=1.6):
    """Positive controls for the alpha estimator."""
    rs = np.random.RandomState(seed)
    widths = dict(zip("abcdefghijklmnopqrstuvwxyz",
                      rs.uniform(0.80, 1.30, 26)))
    lsb = dict(zip("abcdefghijklmnopqrstuvwxyz", rs.uniform(0.0, 0.25, 26)))
    samples = {}
    for _ in range(nlines):
        letters = rs.choice(list("abcdefghijklmnopqrstuvwxyz"), ncells)
        x = np.zeros(ncells)
        for k in range(1, ncells):
            if kind == "mono":
                x[k] = x[k - 1] + pitch
            else:
                x[k] = x[k - 1] + pitch * widths[letters[k - 1]]
        if kind == "mono":
            x = x + np.array([lsb[c] for c in letters]) * pitch
        x = x + rs.normal(0, noise, ncells)
        ins = np.diff(x)
        pit = float(np.median(ins))
        for t in range(ncells):
            for n in range(1, 15):
                if t + n >= ncells:
                    break
                samples.setdefault(n, []).append((x[t + n] - x[t]) / n / pit)
    return samples


def stage_alpha2(a):
    mi = mask_index()
    samples = {}
    for p in (75, 76, 78, 79):
        ink, m, rows = exact_lines(p, mi)
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            idx = [k for k, c in enumerate(st) if c != " "]
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10 or np.std(ins) > 8.0:
                continue
            pit = float(np.median(ins))
            for t in range(len(idx)):
                for n in range(1, 15):
                    if t + n >= len(idx):
                        break
                    if idx[t + n] - idx[t] != n:
                        break
                    samples.setdefault(n, []).append((L[t + n] - L[t]) / n / pit)
    r = alpha_from(samples)
    print("OVERDOSE body face (p75/76/78/79, 32 cleanly-mapped lines)")
    print(f"   alpha = {r['alpha']:.4f}")
    print(f"   sd^2*n = A + B/n   ->  A = {r['A']:.5f}  (sqrt = {math.sqrt(max(r['A'],0)):.4f} "
          f"cells of per-letter advance variation)")
    print(f"                          B = {r['B']:.5f}  (sqrt = {math.sqrt(max(r['B'],0)):.4f} "
          f"cells of endpoint measurement noise)")
    for kind in ("mono", "prop"):
        c = synth_samples(kind, noise=1.6)
        rc = alpha_from(c)
        print(f"CONTROL {kind:5s}: alpha = {rc['alpha']:.4f}   A = {rc['A']:.5f}  "
              f"B = {rc['B']:.5f}")
    c = synth_samples("mono", noise=3.2)
    rc = alpha_from(c)
    print(f"CONTROL mono (2x noise): alpha = {rc['alpha']:.4f}   A = {rc['A']:.5f}  "
          f"B = {rc['B']:.5f}")



def colour_page(printed):
    fn = glob.glob(f"{SC}/p{printed}_x*_1700x2200.jpeg")[0]
    return np.array(Image.open(fn).convert("RGB"))[::-1, ::-1]


def stage_barface(a):
    """
    Bar text vs body text, both measured on the SAME 200 dpi colour layer
    (the bars are absent from the 400 dpi mask, so this is the only place
    both can be compared on equal terms).
    """
    mi = mask_index()
    print(" page  where         glyphs  x-height  asc/cap  advance  stroke  sw/xh")
    summ = {}
    for p in (75, 76, 78, 79):
        c = colour_page(p)
        lum = c.mean(2)
        R, G, B = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
        orange = (R > 150) & (G > 40) & (G < 185) & (B < 120) & (R - B > 70)
        barmask = ndimage.binary_closing(orange, np.ones((5, 25)))
        barmask = ndimage.binary_fill_holes(barmask)
        lab, n = ndimage.label(barmask)
        bars = []
        for sl in ndimage.find_objects(lab):
            sy, sx = sl
            w, h = sx.stop - sx.start, sy.stop - sy.start
            if w < 60 or h < 12 or h > 60 or w / h < 3:
                continue
            bars.append((sy, sx))
        for tag, regions in (("BAR", bars),):
            hs, ads, sws = [], [], []
            ng = 0
            for sy, sx in regions:
                sub = lum[sy.start + 2:sy.stop - 2, sx.start:sx.stop]
                ink = sub < 120                      # dark type on orange
                bs = glyph_boxes(ink, 0, ink.shape[0], min_area=3, ov=0.45)
                bs = [b for b in bs if (b["x1"] - b["x0"]) >= 2 and b["area"] >= 8]
                if len(bs) < 8:
                    continue
                bots = np.array([b["y1"] for b in bs], float)
                base, _ = mode1(bots)
                on = [b for b in bs if abs(b["y1"] - base) <= 2.0]
                if len(on) < 6:
                    continue
                hh = np.array([b["y1"] - b["y0"] for b in on], float)
                hs.append(float(np.percentile(hh, 30)))
                ads += list(np.diff([b["x0"] for b in bs]))
                sw, _ = stroke_width(ink)
                sws.append(sw)
                ng += len(bs)
            ad = np.array([x for x in ads if 8 <= x <= 40])
            adm, _ = mode1(ad, binw=1.0) if len(ad) > 20 else (float("nan"), 0)
            xh = float(np.median(hs)) if hs else float("nan")
            print(f"  {p}   {tag} ({len(regions):2d})      {ng:5d}  {xh:8.2f}  "
                  f"{'':7s}  {adm:7.2f}  {np.median(sws):6.2f}  {np.median(sws)/xh:5.3f}")
            summ[(p, tag)] = (xh, adm, float(np.median(sws)))
        # body text on the same colour layer: dark ink on white paper, bars masked out
        body = (lum < 120) & (~ndimage.binary_dilation(barmask, np.ones((9, 9))))
        hs, ads, sws = [], [], []
        ng = 0
        for (y0, y1) in line_bands(body, min_ink=3, min_h=8):
            if y1 - y0 < 14 or y1 - y0 > 45:
                continue
            bs = glyph_boxes(body, y0, y1, min_area=3, ov=0.45)
            bs = [b for b in bs if (b["x1"] - b["x0"]) >= 2 and b["area"] >= 8]
            if len(bs) < 15:
                continue
            bots = np.array([b["y1"] for b in bs], float)
            base, _ = mode1(bots)
            on = [b for b in bs if abs(b["y1"] - base) <= 2.0]
            if len(on) < 10:
                continue
            hh = np.array([b["y1"] - b["y0"] for b in on], float)
            v = float(np.percentile(hh, 30))
            if not (10 <= v <= 22):
                continue
            hs.append(v)
            ads += list(np.diff([b["x0"] for b in bs]))
            sw, _ = stroke_width(body[y0:y1])
            sws.append(sw)
            ng += len(bs)
        ad = np.array([x for x in ads if 8 <= x <= 40])
        adm, _ = mode1(ad, binw=1.0) if len(ad) > 20 else (float("nan"), 0)
        xh = float(np.median(hs)) if hs else float("nan")
        print(f"  {p}   BODY ({len(hs):2d} lines) {ng:5d}  {xh:8.2f}  "
              f"{'':7s}  {adm:7.2f}  {np.median(sws):6.2f}  {np.median(sws)/xh:5.3f}")
        summ[(p, "BODY")] = (xh, adm, float(np.median(sws)))
    print("\nRATIO bar/body per page:  x-height   advance   stroke")
    for p in (75, 76, 78, 79):
        b = summ.get((p, "BAR")); y = summ.get((p, "BODY"))
        if b and y:
            print(f"   p{p}:  {b[0]/y[0]:8.3f}  {b[1]/y[1]:8.3f}  {b[2]/y[2]:8.3f}")



def stage_leading(a):
    """Baseline-to-baseline leading, fitted as a lattice over each page's body."""
    mi = mask_index()
    print(" pg  lines   leading_px  leading_pt  rms_px   offsets")
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        bl = []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if lb and 27 <= lb["xh"] <= 36:
                bl.append(lb["base"])
        bl = np.array(sorted(bl))
        if len(bl) < 5:
            print(f" {p}  too few"); continue
        best = (None, 9e9, None)
        for L in np.arange(80.0, 115.0, 0.01):
            k = np.round((bl - bl[0]) / L)
            if len(set(k)) < len(k):          # two lines on one lattice row
                continue
            A = np.vstack([k, np.ones(len(k))]).T
            sol, *_ = np.linalg.lstsq(A, bl, rcond=None)
            r = float(np.sqrt((((A @ sol) - bl) ** 2).mean()))
            if r < best[1]:
                best = (float(sol[0]), r, k)
        print(f" {p}   {len(bl):4d}   {best[0]:9.3f}  {best[0]*PT_PER_PX:9.4f} "
              f"{best[1]:7.2f}   {sorted(set(int(x) for x in best[2]))[:14]}")


def stage_display(a):
    """
    Display faces: cap-height and stroke weight for every text block,
    against the body face measured the same way.
    """
    mi = mask_index()
    # body reference
    ref = {}
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        caps, sws, xhs = [], [], []
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if not (lb and 27 <= lb["xh"] <= 36):
                continue
            bm = block_metrics(ink, y0, y1, 0, ink.shape[1])
            if bm:
                caps.append(bm["tall"]); sws.append(bm["sw"]); xhs.append(bm["xh"])
        ref[p] = (float(np.median(xhs)), float(np.median(caps)), float(np.median(sws)))
    bx = float(np.median([v[0] for v in ref.values()]))
    bc = float(np.median([v[1] for v in ref.values()]))
    bs = float(np.median([v[2] for v in ref.values()]))
    print(f"BODY FACE (p75/76/78/79): x-height {bx:.2f} px  asc/cap band {bc:.2f} px  "
          f"stroke {bs:.2f} px  stroke/cap {bs/bc:.4f}  x/cap {bx/bc:.4f}")
    print()
    print(" page  y_px  ypt   glyphs  xh_px   cap_px   stroke  sw/cap   x/cap   width_px")
    for p, xlo, xhi in ((73, 100, 2912), (72, 950, 3140)):
        ink, m = load(p, mi)
        for (y0, y1) in line_bands(ink):
            bm = block_metrics(ink, y0, y1, xlo, min(xhi, ink.shape[1]))
            if not bm or bm["n"] < 5:
                continue
            cols = ink[y0:y1, xlo:xhi].sum(0)
            nz = np.nonzero(cols)[0]
            print(f"  {p}  {y0:5d} {pxpt_y(m,y0):6.1f} {bm['n']:6d} {bm['xh']:7.2f} "
                  f"{bm['tall']:8.2f} {bm['sw']:7.2f} {bm['sw']/bm['tall']:7.4f} "
                  f"{bm['xh']/bm['tall']:7.4f} {nz[-1]-nz[0]:8d}")



def bar_regions(printed, kind="orange"):
    """Highlight rectangles from the 200 dpi colour layer, in colour-layer px."""
    c = colour_page(printed)
    R, G, B = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
    lum = c.mean(2)
    if kind == "orange":
        msk = (R > 150) & (G > 40) & (G < 185) & (B < 120) & (R - B > 70)
    else:
        msk = (lum < 90) & (abs(R - B) < 60)
    mm = ndimage.binary_fill_holes(ndimage.binary_closing(msk, np.ones((5, 25))))
    lab, n = ndimage.label(mm)
    out = []
    for sl in ndimage.find_objects(lab):
        sy, sx = sl
        w, h = sx.stop - sx.start, sy.stop - sy.start
        if w < 80 or h < 12 or h > 60 or w / h < 3:
            continue
        out.append((sy, sx))
    return out


def stage_holes(a):
    """
    Every highlight rectangle is a HOLE in the 400 dpi bilevel text mask:
    the scanner assigned the highlighted type to the 200 dpi colour layer.
    """
    mi = mask_index()
    tot = {"orange": [0, 0, 0], "black": [0, 0, 0]}
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        rx0 = m["rect_rot"][0] * 400 / 72.0
        ry0 = m["rect_rot"][1] * 400 / 72.0
        for kind in ("orange", "black"):
            for sy, sx in bar_regions(p, kind):
                x0 = int(max(0, sx.start * 2 - rx0)); x1 = int(min(ink.shape[1], sx.stop * 2 - rx0))
                y0 = int(max(0, sy.start * 2 - ry0)); y1 = int(min(ink.shape[0], sy.stop * 2 - ry0))
                if x1 - x0 < 40 or y1 - y0 < 15:
                    continue
                sub = ink[y0:y1, x0:x1]
                tot[kind][0] += 1
                tot[kind][1] += int(sub.sum())
                tot[kind][2] += sub.size
    for k, v in tot.items():
        print(f"{k:6s} bars overlapping a mask: {v[0]:3d}   "
              f"mask ink inside them: {v[1]} px of {v[2]} "
              f"({100*v[1]/max(v[2],1):.5f}%)")
    # the worked example
    ink, m = load(75, mi)
    y0, y1 = 1705, 1779
    bs = glyph_boxes(ink, y0, y1)
    bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 18 and b["x0"] > 300]
    L = np.array([b["x0"] for b in bs], float)
    d = np.diff(L)
    pit = float(np.median(d[d < 60]))
    print(f"\nWORKED EXAMPLE  p75 mask band at page y {pxpt_y(m,y0):.1f} pt")
    print(f'  printed line: "Look, toxicity is Layer 1 of the protocol."')
    print(f"  mask holds {len(bs)} glyphs; character advance {pit:.2f} px")
    for k, x in enumerate(d):
        if x > 2.2 * pit:
            print(f"  void of {x:.0f} px = {x/pit:.2f} character advances at page x "
                  f"{pxpt_x(m,bs[k]['x1']):.1f}-{pxpt_x(m,bs[k+1]['x0']):.1f} pt")
    print('  "Layer 1 o" (9 chars + 2 spaces) predicts '
          f'{9 + 2*0.529:.2f} advances')


def stroke_lim(sub, cap):
    runs, lim = [], max(6, int(0.7 * cap))
    for row in sub:
        x, n = 0, len(row)
        while x < n:
            if row[x]:
                j = x
                while j < n and row[j]:
                    j += 1
                if j - x <= lim:
                    runs.append(j - x)
                x = j
            else:
                x += 1
    return float(np.median(runs)) if runs else float("nan")


def stage_faces(a):
    """Display faces: masthead, page-72 figures, against the body face."""
    mi = mask_index()
    # body reference
    xs, cs, ss = [], [], []
    for p in (75, 76, 78, 79):
        ink, m = load(p, mi)
        for (y0, y1) in line_bands(ink):
            lb = line_body(ink, y0, y1)
            if not (lb and 27 <= lb["xh"] <= 36):
                continue
            bm = block_metrics(ink, y0, y1, 0, ink.shape[1])
            if bm:
                xs.append(bm["xh"]); cs.append(bm["tall"])
                ss.append(stroke_lim(ink[y0:y1], bm["tall"]))
    bx, bc, bs_ = np.median(xs), np.median(cs), np.median(ss)
    print(f"BODY  x-height {bx:.2f} px  asc/cap {bc:.2f} px  stroke {bs_:.2f} px  "
          f"stroke/cap {bs_/bc:.4f}  ({len(xs)} lines)")
    # masthead
    ink, m = load(73, mi)
    d, _ = skew_angle(ink, -2.2, 0.6, 0.02)
    ink2 = deskew(ink, d)
    for (y0, y1) in line_bands(ink2):
        bx2 = glyph_boxes(ink2, y0, y1, min_area=200, ov=0.3)
        bx2 = [b for b in bx2 if (b["x1"] - b["x0"]) >= 20]
        if len(bx2) < 3:
            continue
        cap = float(np.median([b["y1"] - b["y0"] for b in bx2]))
        sw = stroke_lim(ink2[y0:y1], cap)
        adv = np.diff([b["x0"] for b in bx2])
        print(f"MASTHEAD p73 (deskew {d:+.2f} deg): {len(bx2)} letters  "
              f"cap {cap:.1f} px = {cap*PT_PER_PX:.2f} pt = {cap/400:.4f} in  "
              f"stroke {sw:.1f}  stroke/cap {sw/cap:.4f}  "
              f"advances {[int(x) for x in adv]}  CV {adv.std()/adv.mean():.4f}")
    # page 72
    ink, m = load(72, mi)
    vals = []
    print("\np72 blocks: ypt  glyphs  x-ht  cap  stroke  sw/cap  x/cap")
    for (y0, y1) in line_bands(ink):
        bm = block_metrics(ink, y0, y1, 950, 3140)
        if not bm or bm["n"] < 5:
            continue
        sw = stroke_lim(ink[y0:y1, 950:3140], bm["tall"])
        vals.append(sw / bm["tall"])
        print(f"   {pxpt_y(m,y0):6.1f} {bm['n']:6d} {bm['xh']:6.1f} {bm['tall']:6.1f} "
              f"{sw:6.1f} {sw/bm['tall']:7.4f} {bm['xh']/bm['tall']:6.4f}")
    v = np.array(sorted(x for x in vals if x > 0.05))
    print(f"\np72 stroke/cap sorted: {np.round(v,4).tolist()}")
    print(f"   light class {v[v<=0.15].min():.4f}-{v[v<=0.15].max():.4f} (n={int((v<=0.15).sum())});  "
          f"heavy class {v[v>=0.22].min():.4f}-{v[v>=0.22].max():.4f} (n={int((v>=0.22).sum())})")
    print(f"   body face sits at {bs_/bc:.4f}, inside the empty band")



def stage_vclass(a):
    """
    Full vertical metric set, using the exact glyph->character map so each
    glyph's letter identity is known: x-height, cap-height, ascender,
    descender, measured per letter class rather than by percentile.
    """
    import collections
    mi = mask_index()
    H = collections.defaultdict(list)
    D = collections.defaultdict(list)
    for p in (75, 76, 78, 79):
        ink, m, rows = exact_lines(p, mi)
        for mr, st, ns in rows:
            L = np.array(mr["lefts"], float)
            bs = glyph_boxes(ink, mr["y0"], mr["y1"])
            bs = [b for b in bs if (b["x1"] - b["x0"]) >= 4 and b["area"] >= 18]
            idx = [k for k, c in enumerate(st) if c != " "]
            ins = [L[t + 1] - L[t] for t in range(len(idx) - 1)
                   if idx[t + 1] - idx[t] == 1]
            if len(ins) < 10 or np.std(ins) > 8.0:
                continue
            bots = np.array([b["y1"] for b in bs], float)
            base, _ = mode1(bots)
            for t, k in enumerate(idx):
                if t >= len(bs):
                    break
                H[st[k]].append(bs[t]["y1"] - bs[t]["y0"])
                D[st[k]].append(bs[t]["y1"] - base)
    classes = dict(x="acemnorsuvwxz", ascender="bdfhkl",
                   capital="ABCDEFGHIJKLMNOPQRSTUVWXYZ", descender="gjpqy")
    print(" class       n   height_px  height_pt   below_baseline_px")
    res = {}
    for cl, letters in classes.items():
        h = [v for ch in letters for v in H.get(ch, [])]
        d = [v for ch in letters for v in D.get(ch, [])]
        if len(h) < 20:
            print(f" {cl:10s} {len(h):4d}  (too few)")
            continue
        h = np.array(h, float); d = np.array(d, float)
        res[cl] = float(np.median(h))
        print(f" {cl:10s} {len(h):4d}   {np.median(h):8.2f}   {np.median(h)*PT_PER_PX:8.3f}"
              f"   {np.median(d):12.2f}")
    if "x" in res and "capital" in res:
        print(f"\n x-height/cap-height = {res['x']/res['capital']:.4f}")
    json.dump(res, open(f"{OUT}/vclass.json", "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="rects")
    ap.add_argument("--page", type=int, default=0)
    a = ap.parse_args()
    fn = globals().get("stage_" + a.stage)
    if fn is None:
        print("stages:", sorted(k[6:] for k in globals() if k.startswith("stage_")))
        sys.exit(1)
    fn(a)
