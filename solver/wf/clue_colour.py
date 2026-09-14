#!/usr/bin/env python3
"""
COLOUR, MEASURED AT THE NATIVE RESOLUTION OF THE COLOUR LAYER.

Every colour statement in this project so far is a PER-PAGE median over an
orange mask (`window/thirty_clues.md` clues 16-20).  A per-page median cannot
answer the questions that matter:

  * are the 22 highlight bars one ink, or several?
  * is page 73's "lighter orange" a different tint of ink, or not ink at all?
  * what colour is the OVERDOSE running head, and is it the bar ink?
  * what colour is page 77's dark ground, and is it flat?
  * are the knockout bars black, or a build?

This measures each coloured OBJECT separately.

THE ONE THING TO GET RIGHT
The colour layer is a 1700x2200 DeviceRGB JPEG at 200 dpi -- the scanner's MRC
background plane, with the text routed away into a 1-bit mask.  So a highlight
bar arrives as a clean flat wash.  But its EDGE is 2-3 px of JPEG ramp into
white paper, and a small bar is mostly edge.  Measuring a bar without eroding
it makes small bars read lighter than big ones and invents a colour gradient
that is purely a size artefact.  Everything here is measured on an eroded core.

  python3 wf/clue_colour.py --selftest
  python3 wf/clue_colour.py --all
"""
import argparse, glob, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

Image.MAX_IMAGE_PIXELS = None
SRC = os.environ.get("SC400", "/tmp/sc400")
PAGES = list(range(72, 80))


def load(p):
    """The native 200 dpi colour layer, un-rotated into reading orientation."""
    hits = glob.glob(os.path.join(SRC, f"p{p}_x*_1700x2200.jpeg"))
    if not hits:
        sys.exit(f"missing colour layer for p{p} in {SRC}; run\n"
                 f"  python3 extract_scan.py --dpi 400 --out {SRC}")
    return np.asarray(Image.open(hits[0]).convert("RGB").rotate(180)).astype(np.int16)


def chroma(a):
    """max-min across channels: 0 for any neutral, whatever its lightness."""
    return a.max(2) - a.min(2)


def med(a, sel):
    return tuple(int(np.median(a[..., c][sel])) for c in range(3))


def erode(mask, k):
    return nd.binary_erosion(mask, np.ones((k, k), bool))


# ---------------------------------------------------------------- objects
def orange_objects(a, min_px=300, erode_k=9):
    """Every chromatic region, measured on a core eroded by (k-1)/2 px."""
    m = chroma(a) >= 60
    lab, n = nd.label(m)
    objs = nd.find_objects(lab)
    out = []
    for i in range(1, n + 1):
        sel = lab == i
        sz = int(sel.sum())
        if sz < min_px:
            continue
        core = erode(sel, erode_k)
        if core.sum() < 40:
            core = erode(sel, 5)
        if core.sum() < 20:
            core = sel
        sl = objs[i - 1]
        out.append(dict(px=sz, core=int(core.sum()),
                        x0=sl[1].start, x1=sl[1].stop,
                        y0=sl[0].start, y1=sl[0].stop,
                        w=sl[1].stop - sl[1].start, h=sl[0].stop - sl[0].start,
                        rgb=med(a, core), rgb_raw=med(a, sel)))
    out.sort(key=lambda d: (d["y0"], d["x0"]))
    return out


def classify(p, o):
    """bar | display | capsule | head -- by page, size and shape."""
    if p == 73:
        return "capsule"
    if p == 79 and o["y0"] > 1550 and o["w"] < 90:
        return "capsule"
    if p == 77 and o["y0"] < 200:
        return "head"
    if o["h"] >= 40:
        return "display"
    return "bar"


def report_objects():
    rows = []
    for p in PAGES:
        a = load(p)
        for o in orange_objects(a):
            o["page"], o["kind"] = p, classify(p, o)
            rows.append(o)
    print("\n== every chromatic object, eroded core (page 72, 74 have none) ==")
    print("page kind     px     core  x0   y0    w   h   coreRGB        rawRGB")
    for o in rows:
        print(f"{o['page']} {o['kind']:8s}{o['px']:7d} {o['core']:7d} "
              f"{o['x0']:5d}{o['y0']:5d} {o['w']:5d}{o['h']:4d}  "
              f"{str(o['rgb']):16s}{o['rgb_raw']}")
    for kind in ("bar", "display", "capsule", "head"):
        s = [o for o in rows if o["kind"] == kind]
        if not s:
            continue
        arr = np.array([o["rgb"] for o in s])
        print(f"\n  {kind}: n={len(s)}  median={tuple(int(x) for x in np.median(arr,0))}"
              f"  min={tuple(int(x) for x in arr.min(0))}"
              f"  max={tuple(int(x) for x in arr.max(0))}")
        for c, nm in enumerate("RGB"):
            print(f"     {nm}: {arr[:,c].min()}..{arr[:,c].max()} "
                  f"sd={arr[:,c].std():.2f}")
    # per page, bars only
    print("\n  bars per page (core medians):")
    for p in PAGES:
        s = [o for o in rows if o["kind"] in ("bar", "display") and o["page"] == p]
        if not s:
            continue
        arr = np.array([o["rgb"] for o in s])
        print(f"   p{p}: n={len(s):2d} median={tuple(int(x) for x in np.median(arr,0))} "
              f"B range {arr[:,2].min()}..{arr[:,2].max()}")
    return rows


# ---------------------------------------------------------------- ground
def report_ground():
    print("\n== page 77 dark ground, and every page's paper base ==")
    for p in PAGES:
        a = load(p)
        c = chroma(a)
        L = a.mean(2)
        if p == 77:
            g = (L > 60) & (L < 140) & (c < 40)
        else:
            g = (L > 200) & (c < 30)
        print(f" p{p}: base n={int(g.sum()):8d} median={med(a,g)} "
              f"chroma_med={int(np.median(c[g]))} chroma_max={int(c.max())}")


def report_ground_flatness():
    """Is the ground/paper flat, or does the scanner light it unevenly?"""
    print("\n== illumination: base value by horizontal fifth (reading order) ==")
    for p in PAGES:
        a = load(p)
        c = chroma(a)
        L = a.mean(2)
        g = (L > 60) & (L < 140) & (c < 40) if p == 77 else (L > 200) & (c < 30)
        cols = []
        for i in range(5):
            x0, x1 = i * 340, (i + 1) * 340
            sub = g[:, x0:x1]
            cols.append(int(np.median(L[:, x0:x1][sub])) if sub.sum() > 500 else -1)
        print(f" p{p}: {cols}  spread={max(cols)-min(cols)}")


# ---------------------------------------------------------------- blacks
def report_blacks():
    """The knockout bars and the darkest type: neutral, or a colour build?"""
    print("\n== dark ink: is it neutral? (chroma of the darkest pixels) ==")
    for p in PAGES:
        a = load(p)
        L = a.mean(2)
        c = chroma(a)
        for name, sel in (("darkest1%", L <= np.percentile(L, 1)),
                          ("L<60", L < 60)):
            if sel.sum() < 200:
                print(f" p{p} {name:10s} n={int(sel.sum()):7d}  (too few)")
                continue
            print(f" p{p} {name:10s} n={int(sel.sum()):7d} median={med(a,sel)} "
                  f"chroma_med={int(np.median(c[sel]))} "
                  f"R-B={int(np.median(a[...,0][sel]-a[...,2][sel]))}")


# ---------------------------------------------------------------- head ghost
GHOST = {75: (120, 100, 280, 150), 76: (120, 100, 280, 150),
         78: (120, 100, 280, 150), 79: (120, 100, 280, 150),
         73: (120, 100, 280, 150), 72: (120, 100, 280, 150),
         74: (120, 100, 280, 150)}


def report_head_ghost():
    """Where the running head was lifted into the 1-bit mask, what is left?"""
    print("\n== residue where the OVERDOSE running head was knocked out ==")
    for p in PAGES:
        a = load(p)
        x0, y0, x1, y1 = GHOST[p] if p in GHOST else (0, 0, 1, 1)
        sub = a[y0:y1, x0:x1]
        c = chroma(sub)
        sel = c >= 8
        paper = med(a, (a.mean(2) > 200) & (chroma(a) < 30))
        print(f" p{p}: box x[{x0},{x1}) y[{y0},{y1}) chroma>=8 n={int(sel.sum()):5d} "
              f"median={med(sub,sel) if sel.sum() else '-'} "
              f"max_chroma={int(c.max())} paper={paper}")


# ---------------------------------------------------------------- selftest
def selftest():
    ok = True
    a = load(75)
    ok &= a.shape == (2200, 1700, 3)
    print(f"  p75 colour layer {a.shape}: {'OK' if a.shape==(2200,1700,3) else 'FAIL'}")
    for p in (72, 74):
        mx = int(chroma(load(p)).max())
        good = mx < 40
        ok &= good
        print(f"  p{p} max chroma {mx} (<40 = no chromatic ink): "
              f"{'OK' if good else 'FAIL'}")
    objs = orange_objects(load(73))
    good = len(objs) == 5
    ok &= good
    print(f"  p73 chromatic objects = {len(objs)} (the 5 capsules): "
          f"{'OK' if good else 'FAIL'}")
    # erosion must actually change a small bar's reading
    a = load(76)
    o = [x for x in orange_objects(a) if x["px"] < 5000]
    if o:
        d = o[0]["rgb_raw"][2] - o[0]["rgb"][2]
        print(f"  erosion moves a small bar's B by {d} (edge ramp is real): "
              f"{'OK' if d != 0 else 'FAIL'}")
        ok &= d != 0
    print("  SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


# ------------------------------------------------- the PDF's own colour table
# The scan is a Canon MRC file. Every piece of text it lifted off a page is a
# 1-bit /ImageMask stencil, and the content stream paints each one with an
# EXPLICIT DeviceRGB or DeviceGray fill that the scanner computed from the ink
# it found there. 27 stencils across the 8 pages = 27 exact colours, stored as
# numbers in the file. No pixel measurement, no JPEG, no thresholds. Nothing in
# this project has ever read them.
import re
CM = re.compile(
    r'q\s+(?:([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg|([\d.]+)\s+g)?\s*'
    r'([\d.]+)\s+0\s+0\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+cm\s*/(\w+)\s+Do\s+Q')


def stencils():
    """(page, obj, xref, space, rgb, reading-orientation box in pt).

    Geometry: the sheets were fed 180 degrees round, so a PDF box (x,y,w,h)
    with y measured from the page bottom lands, once the render is turned back
    the right way up, at reading-orientation top-left (612-(x+w), y).
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import extract_scan as E
    d = E.open_pdf()
    rows = []
    for i, pg in enumerate(d):
        pn = E.PAGE_MAP[i]
        t = b"".join(d.xref_stream(x) for x in pg.get_contents()).decode("latin-1")
        mark = "TEXTON" if "TEXTON" in t else ("TEXTOFF" if "TEXTOFF" in t else "?")
        names = {x[7]: x[0] for x in pg.get_images(full=True)}
        for m in CM.finditer(t):
            r, g, b, gr, w, h, x, y, obj = m.groups()
            if r is not None:
                rgb, sp = (round(float(r) * 255), round(float(g) * 255),
                           round(float(b) * 255)), "rg"
            elif gr is not None:
                rgb, sp = (round(float(gr) * 255),) * 3, "g"
            else:
                rgb, sp = None, "-"
            w, h, x, y = float(w), float(h), float(x), float(y)
            rows.append(dict(page=pn, mark=mark, obj=obj, xref=names.get(obj),
                             space=sp, rgb=rgb, w=w, h=h,
                             rx=612 - (x + w), ry=y, ctext=len(t)))
    return rows


def report_stencils():
    rows = stencils()
    print("\n== the 27 stencil fills the Canon MRC encoder wrote into the PDF ==")
    print("page mark    obj   xref sp rgb                  wxh pt        read x,y pt")
    for r in rows:
        if r["space"] == "-":
            continue
        print(f"{r['page']}  {r['mark']:7s} {r['obj']:6s}{str(r['xref']):5s} "
              f"{r['space']:2s} {str(r['rgb']):18s} "
              f"{r['w']:7.2f}x{r['h']:6.2f}  {r['rx']:7.2f},{r['ry']:7.2f}")
    print("\n  -- the OVERDOSE running head (232x32-ish stencil at the page top) --")
    heads = [r for r in rows if r["space"] == "rg" and r["h"] < 8 and r["ry"] < 60]
    for r in heads:
        print(f"   p{r['page']} {r['obj']} {r['rgb']}  "
              f"x={r['rx']:.2f} ({'left' if r['rx'] < 306 else 'right'})")
    arr = np.array([r["rgb"] for r in heads])
    print(f"   n={len(heads)} R {arr[:,0].min()}..{arr[:,0].max()} "
          f"G {arr[:,1].min()}..{arr[:,1].max()} B {arr[:,2].min()}..{arr[:,2].max()}")
    print("\n  -- the full-page body-text stencil, one per page --")
    for r in rows:
        if r["space"] != "-" and r["w"] > 400 and r["h"] > 400:
            R, G, B = r["rgb"]
            print(f"   p{r['page']} {r['obj']} {r['rgb']}  R-G={R-G:+4d}  G-B={G-B:+4d}")
    print("\n  -- pages with no text separation at all --")
    for pn in PAGES:
        s = [r for r in rows if r["page"] == pn]
        n = len([r for r in s if r["space"] != "-"])
        print(f"   p{pn}: {s[0]['mark']:7s} content={s[0]['ctext']:6d}B  stencils={n}")


def report_clipping(rows):
    """How much of the orange is even measurable? R is pinned at the white point."""
    bars = [o for o in rows if o["kind"] in ("bar", "display")]
    arr = np.array([o["rgb"] for o in bars])
    n255 = int((arr[:, 0] == 255).sum())
    print(f"\n== channel clipping ==\n  bars with core R = 255 (clipped): "
          f"{n255}/{len(bars)}; G and B are the only live channels")
    ys = np.array([o["y0"] for o in bars], float)
    for c, nm in ((1, "G"), (2, "B")):
        v = arr[:, c].astype(float)
        r = float(np.corrcoef(ys, v)[0, 1])
        print(f"  corr(bar y on page, {nm}) = {r:+.3f}")
    # within page, to remove any page-level offset
    rs = []
    for p in PAGES:
        s = [o for o in bars if o["page"] == p]
        if len(s) < 4:
            continue
        y = np.array([o["y0"] for o in s], float)
        b = np.array([o["rgb"][2] for o in s], float)
        rr = float(np.corrcoef(y, b)[0, 1])
        rs.append((p, len(s), rr))
        print(f"  p{p}: n={len(s)} corr(y, B) = {rr:+.3f}")
    return rs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stencils", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--objects", action="store_true")
    ap.add_argument("--ground", action="store_true")
    ap.add_argument("--blacks", action="store_true")
    ap.add_argument("--ghost", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.all or a.stencils:
        report_stencils()
    if a.all or a.objects:
        report_clipping(report_objects())
    if a.all or a.ground:
        report_ground()
        report_ground_flatness()
    if a.all or a.blacks:
        report_blacks()
    if a.all or a.ghost:
        report_head_ghost()


if __name__ == "__main__":
    main()
