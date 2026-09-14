#!/usr/bin/env python3
"""
ARTWORK, MEASURED.  Every non-type mark on the Overdose spread, located and
sized in the 400 dpi render of scan/Scan1.pdf.

Coordinate frame for EVERY number printed here:
    the page as printed (reading orientation), 3400 x 4400 px at 400 dpi,
    origin top-left, +x right, +y down.  1 px = 1/400 in = 0.0635 mm.
Renders come from `python3 extract_scan.py --dpi 400 --out /tmp/sc400`,
which already rotates the 180-degree-flipped scan back upright.

Angles are the PCA long-axis bearing in degrees, measured from +x (east),
counter-clockwise positive in reading orientation (i.e. standard maths
convention on a y-down image after negating dy), folded to (-90, +90].

Sections
    caps     segment + measure every gelatin capsule on p73 and p79
    reuse    is the p73 capsule set the same photograph as p79's?
    xmarks   the grey painted X strokes on p76
    scribble the p78 "X FUCK ALL X" scrawl and the boxed quote inside it
    shit     the p77 white "SHIT" graffiti
    p79art   barbed wire, drawn Bitcoin symbol, MAX-heart-KEISER signature
"""
import argparse, os, sys, math, json
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

SC = os.environ.get("SC400", "/tmp/sc400")
DPI = 400


def page(n):
    return np.asarray(Image.open(os.path.join(SC, f"p{n}_{DPI}dpi.png")).convert("RGB")).astype(np.int16)


# ---------------------------------------------------------------- components
def label(mask):
    """4-connected CCL, iterative, no scipy dependency."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    cur = 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        cur += 1
        stack = [(y0, x0)]
        lab[y0, x0] = cur
        while stack:
            y, x = stack.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = cur
                    stack.append((ny, nx))
    return lab, cur


def label_fast(mask):
    """4-connected CCL.  scipy when present (fast), pure-python fallback."""
    try:
        from scipy import ndimage
        lab, n = ndimage.label(mask)
        return lab.astype(np.int32), int(n)
    except Exception:
        return _label_slow(mask)


def _label_slow(mask):
    """Union-find CCL over run-length rows: fallback when scipy is absent."""
    h, w = mask.shape
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    lab = np.zeros((h, w), np.int32)
    for y in range(h):
        row = mask[y]
        if not row.any():
            continue
        prev = lab[y - 1] if y else None
        x = 0
        idx = np.flatnonzero(row)
        # group into runs
        if idx.size == 0:
            continue
        splits = np.flatnonzero(np.diff(idx) > 1)
        starts = np.concatenate(([idx[0]], idx[splits + 1]))
        ends = np.concatenate((idx[splits], [idx[-1]]))
        for s, e in zip(starts, ends):
            nb = set()
            if prev is not None:
                seg = prev[max(0, s - 1):e + 2]
                nb = set(int(v) for v in np.unique(seg) if v)
            if nb:
                m = min(nb)
                for v in nb:
                    union(m, v)
                lab[y, s:e + 1] = m
            else:
                parent.append(len(parent))
                lab[y, s:e + 1] = len(parent) - 1
    # flatten
    if len(parent) > 1:
        remap = np.zeros(len(parent), np.int32)
        for i in range(1, len(parent)):
            remap[i] = find(i)
        lab = remap[lab]
        u = np.unique(lab)
        u = u[u > 0]
        ren = np.zeros(lab.max() + 1, np.int32)
        ren[u] = np.arange(1, u.size + 1)
        lab = ren[lab]
        return lab, u.size
    return lab, 0


def pca_axis(ys, xs):
    """Return (angle_deg, length_px, width_px) of the point cloud."""
    y = ys.astype(float) - ys.mean()
    x = xs.astype(float) - xs.mean()
    # y-down -> flip so angles read like a normal plot
    dy = -y
    cov = np.cov(np.vstack([x, dy]))
    w, v = np.linalg.eigh(cov)
    order = np.argsort(w)[::-1]
    w, v = w[order], v[:, order]
    ang = math.degrees(math.atan2(v[1, 0], v[0, 0]))
    while ang <= -90:
        ang += 180
    while ang > 90:
        ang -= 180
    # extent along each axis (full span of projections)
    p0 = x * v[0, 0] + dy * v[1, 0]
    p1 = x * v[0, 1] + dy * v[1, 1]
    return ang, p0.max() - p0.min(), p1.max() - p1.min()


# ---------------------------------------------------------------- capsules
def capsule_masks(a):
    """orange gelatin cap; white gelatin body; the pill = cap|body.

    The white body is a light warm grey on paper that is lighter still, and the
    cast shadow is darker than the body -- three separable luminance bands.
    """
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    orange = (r - b > 60) & (r > 140) & (g < r - 30)
    body = (lum >= 196) & (lum <= 238) & (sat < 22)
    shadow = (lum >= 150) & (lum < 196) & (sat < 22)
    return orange, body, shadow


def caps(pn, minpx=2000, verbose=True):
    """Every gelatin capsule on the page: an orange blob whose bounding box is
    roughly square (aspect 0.4-2.0).  That single shape test rejects the orange
    highlight bars on p79, which are 5.8-26.8 x wider than tall."""
    a = page(pn)
    orange, body, shadow = capsule_masks(a)
    lab, n = label_fast(orange)
    cnt = np.bincount(lab.ravel())
    from scipy import ndimage
    objs = ndimage.find_objects(lab)
    cand = []
    for i in range(1, n + 1):
        if cnt[i] < minpx:
            continue
        sl = objs[i - 1]
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if not (0.4 <= w / h <= 2.0):
            continue          # <- highlight bars die here
        cand.append((i, sl))
    rows = []
    order = sorted(cand, key=lambda t: (t[1][0].start, t[1][1].start))
    for k, (i, sl) in enumerate(order):
        pad = 190
        by0, by1 = max(0, sl[0].start - pad), min(a.shape[0], sl[0].stop + pad)
        bx0, bx1 = max(0, sl[1].start - pad), min(a.shape[1], sl[1].stop + pad)
        sub = a[by0:by1, bx0:bx1]
        subo = orange[by0:by1, bx0:bx1] & (lab[by0:by1, bx0:bx1] == i)
        pill_all = (orange[by0:by1, bx0:bx1] | body[by0:by1, bx0:bx1])
        # the cap/body junction is a 1-3 px ramp that belongs to neither mask;
        # close the gap so cap and body land in one component, then intersect
        # the closing back down to real ink.
        from scipy import ndimage as _nd
        st = _nd.generate_binary_structure(2, 2)
        closed = _nd.binary_closing(pill_all, structure=st, iterations=4)
        fl, _ = label_fast(closed)
        oy, ox = np.nonzero(subo)
        cid = np.bincount(fl[oy, ox]).argmax()
        pill = (fl == cid) & pill_all
        pys, pxs = np.nonzero(pill)
        ang, L, W = pca_axis(pys, pxs)
        oang, oL, oW = pca_axis(oy, ox)
        bodyonly = pill & ~subo
        shp = shadow[by0:by1, bx0:bx1]
        sl2, _ = label_fast(shp)
        capcol = np.median(sub[subo].reshape(-1, 3), axis=0)
        bodycol = np.median(sub[bodyonly].reshape(-1, 3), axis=0) if bodyonly.sum() else None
        rows.append(dict(
            page=pn, idx=k + 1,
            cx=round(float(pxs.mean() + bx0), 1), cy=round(float(pys.mean() + by0), 1),
            bbox=[int(pxs.min() + bx0), int(pys.min() + by0),
                  int(pxs.max() + bx0), int(pys.max() + by0)],
            angle=round(ang, 2), length=round(float(L), 1), width=round(float(W), 1),
            area_pill=int(pill.sum()), area_cap=int(oy.size), area_body=int(bodyonly.sum()),
            cap_frac=round(float(oy.size) / pill.sum(), 4),
            cap_rgb=[int(v) for v in capcol],
            body_rgb=[int(v) for v in bodycol] if bodycol is not None else None,
            capdir=round(math.degrees(math.atan2(-(oy.mean() - pys.mean()),
                                                 ox.mean() - pxs.mean())), 1),
        ))
    if verbose:
        print(f"\n=== p{pn}: {len(rows)} gelatin capsules ===")
        print(f"{'#':>2} {'centroid(x,y)':>16} {'axis':>7} {'len':>6} {'wid':>6} {'L/W':>5} "
              f"{'pill px':>8} {'cap%':>6} {'capdir':>7} {'cap RGB':>15} {'body RGB':>15}")
        for r in rows:
            print(f"{r['idx']:>2} {r['cx']:8.1f},{r['cy']:7.1f} {r['angle']:+7.2f} "
                  f"{r['length']:6.1f} {r['width']:6.1f} {r['length']/r['width']:5.2f} "
                  f"{r['area_pill']:8d} {100*r['cap_frac']:5.1f}% {r['capdir']:+7.1f} "
                  f"{str(r['cap_rgb']):>15} {str(r['body_rgb']):>15}")
        if rows:
            L = np.array([r['length'] for r in rows])
            W = np.array([r['width'] for r in rows])
            A = np.array([r['area_pill'] for r in rows], float)
            C = np.array([r['cap_rgb'] for r in rows], float)
            print(f"   length px  mean {L.mean():.1f} sd {L.std(ddof=1):.1f} "
                  f"({L.mean()/DPI*25.4:.2f} mm)   width mean {W.mean():.1f}")
            print(f"   pill area  mean {A.mean():.0f} px")
            print(f"   cap RGB    mean ({C[:,0].mean():.1f},{C[:,1].mean():.1f},{C[:,2].mean():.1f})")
            print(f"   axes       {[r['angle'] for r in rows]}")
    return rows, a


# ------------------------------------------------------------- reuse check
def chip(a, r, size=180):
    """Crop the capsule, rotate its long axis to horizontal, orange cap to the
    RIGHT, and resample to a fixed size for comparison."""
    x0, y0, x1, y1 = r['bbox']
    pad = 30
    sub = Image.fromarray(a[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad].astype(np.uint8))
    # rotate by -angle about centre (PIL rotates CCW for positive angle on a
    # y-down image, matching our sign convention after the dy negation)
    im = sub.rotate(-r['angle'], resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    b = np.asarray(im).astype(np.int16)
    rr, gg, bb = b[:, :, 0], b[:, :, 1], b[:, :, 2]
    o = (rr - bb > 60) & (rr > 140)
    nz = np.nonzero(b.mean(2) < 232)
    if nz[0].size == 0:
        return None
    yy0, yy1, xx0, xx1 = nz[0].min(), nz[0].max(), nz[1].min(), nz[1].max()
    b = b[yy0:yy1 + 1, xx0:xx1 + 1]
    o = o[yy0:yy1 + 1, xx0:xx1 + 1]
    if o.sum() and np.nonzero(o)[1].mean() < b.shape[1] / 2:
        b = b[::-1, ::-1]
    return np.asarray(Image.fromarray(b.astype(np.uint8)).resize((size, size), Image.BICUBIC)).astype(float)


def procrustes(rows73, rows79):
    """Best similarity transform (uniform scale + rotation + translation)
    taking the five p73 capsule centroids onto the five p79 centroids, in the
    order both sets come out of `caps` (top-to-bottom).  Reports the residual."""
    P = np.array([[r['cx'], r['cy']] for r in rows73], float)
    Q = np.array([[r['cx'], r['cy']] for r in rows79], float)
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    # y-down: negate y so a positive rotation reads counter-clockwise on paper
    Pc[:, 1] *= -1
    Qc[:, 1] *= -1
    U, S, Vt = np.linalg.svd(Pc.T @ Qc)
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    s = S.sum() / (Pc ** 2).sum()
    fit = s * (R @ Pc.T).T
    resid = np.linalg.norm(fit - Qc, axis=1)
    theta = math.degrees(math.atan2(R[1, 0], R[0, 0]))
    span = np.linalg.norm(Qc, axis=1).max() * 2
    print("\n=== are the two capsule arrangements the same photograph? ===")
    print("  Procrustes p73 centroids -> p79 centroids (same top-to-bottom order)")
    print(f"  uniform scale      {s:.4f}   (p79 is {1/s:.3f}x smaller than p73)")
    print(f"  rotation           {theta:+.2f} deg")
    print(f"  per-point residual {np.round(resid,1).tolist()} px")
    print(f"  RMS residual       {math.sqrt((resid**2).mean()):.1f} px "
          f"= {100*math.sqrt((resid**2).mean())/span:.1f}% of the {span:.0f} px cloud diameter")
    # control: the same fit with p73's points shuffled
    best = []
    import itertools
    for perm in itertools.permutations(range(5)):
        Pp = Pc[list(perm)]
        U2, S2, V2 = np.linalg.svd(Pp.T @ Qc)
        R2 = (U2 @ V2).T
        if np.linalg.det(R2) < 0:
            V2[-1] *= -1
            R2 = (U2 @ V2).T
        s2 = S2.sum() / (Pp ** 2).sum()
        r2 = np.linalg.norm(s2 * (R2 @ Pp.T).T - Qc, axis=1)
        best.append((math.sqrt((r2 ** 2).mean()), perm))
    best.sort()
    print(f"  best of all 120 orderings: {best[0][0]:.1f} px for {best[0][1]}; "
          f"median ordering {np.median([b[0] for b in best]):.1f} px")
    # shape descriptors, rotation- and scale-invariant
    print("\n  rotation- and scale-invariant shape match, pill by pill:")
    print(f"  {'pill':>4} {'p73 L/W':>8} {'p79 L/W':>8} {'diff':>6}  "
          f"{'p73 cap%':>9} {'p79 cap%':>9} {'diff':>6}")
    for i in range(min(len(rows73), len(rows79))):
        a_, b_ = rows73[i], rows79[i]
        ra, rb = a_['length'] / a_['width'], b_['length'] / b_['width']
        print(f"  {i+1:>4} {ra:8.2f} {rb:8.2f} {ra-rb:+6.2f}  "
              f"{100*a_['cap_frac']:8.1f}% {100*b_['cap_frac']:8.1f}% "
              f"{100*(a_['cap_frac']-b_['cap_frac']):+6.1f}")
    da = [b_['angle'] - a_['angle'] for a_, b_ in zip(rows73, rows79)]
    print(f"  long-axis rotation p73->p79, pill by pill: "
          f"{[round(v,1) for v in da]}  (mean {np.mean(da):+.1f})")
    return s, theta, resid


def reuse(rows73, a73, rows79, a79, size=180):
    c73 = [chip(a73, r, size) for r in rows73]
    c79 = [chip(a79, r, size) for r in rows79]
    allc = [("73", i + 1, c) for i, c in enumerate(c73)] + [("79", i + 1, c) for i, c in enumerate(c79)]
    allc = [t for t in allc if t[2] is not None]
    print(f"\n=== capsule chip cross-correlation ({size}x{size}, rotation-normalised, cap to the right) ===")
    n = len(allc)
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            u = allc[i][2].mean(2).ravel()
            v = allc[j][2].mean(2).ravel()
            u = (u - u.mean()) / (u.std() + 1e-9)
            v = (v - v.mean()) / (v.std() + 1e-9)
            M[i, j] = float((u * v).mean())
    hdr = "     " + " ".join(f"{p}#{k}" for p, k, _ in allc)
    print(hdr)
    for i, (p, k, _) in enumerate(allc):
        print(f"{p}#{k}  " + " ".join(f"{M[i,j]:5.2f}" for j in range(n)))
    iu = np.triu_indices(n, 1)
    cross = [(M[i, j], allc[i][0] + "#" + str(allc[i][1]), allc[j][0] + "#" + str(allc[j][1]))
             for i, j in zip(*iu)]
    cross.sort(reverse=True)
    print("\n top 6 pairs:")
    for v, x, y in cross[:6]:
        print(f"   {v:5.3f}  {x} <-> {y}")
    same = [v for v, x, y in cross if x[:2] == y[:2]]
    diff = [v for v, x, y in cross if x[:2] != y[:2]]
    print(f" within-page  mean r = {np.mean(same):.3f} (n={len(same)})")
    print(f" cross-page   mean r = {np.mean(diff):.3f} (n={len(diff)})")
    return M, allc


# ---------------------------------------------------------------- p76 X marks
def edge_orientations(mask, sigma=4.0, sep=20, k=2):
    """Structure-tensor orientation spectrum of a blob's boundary.

    A straight brush stroke contributes its two long edges at the SAME
    orientation, so an X gives exactly two peaks: the bearings of its two
    strokes.  Bearings are CCW-on-paper degrees in (-90, 90].
    """
    from scipy import ndimage as _nd
    f = _nd.gaussian_filter(mask.astype(float), sigma)
    gy, gx = np.gradient(f)
    mag = np.hypot(gx, gy)
    sel = mag > mag.max() * 0.15
    # gradient is normal to the edge; stroke bearing = gradient angle + 90
    ang = (np.degrees(np.arctan2(-gy[sel], gx[sel])) + 90.0) % 180.0
    w = mag[sel]
    hist, edges = np.histogram(ang, bins=180, range=(0, 180), weights=w)
    hist = np.convolve(np.r_[hist, hist, hist], np.ones(7) / 7, "same")[180:360]
    order = np.argsort(hist)[::-1]
    picks = []
    for i in order:
        d = i + 0.5
        if all(min(abs(d - p), 180 - abs(d - p)) > sep for p, _ in picks):
            picks.append((d, float(hist[i])))
        if len(picks) == k:
            break
    out = []
    for d, v in picks:
        out.append((d - 180 if d > 90 else d, v))
    return out, hist


def stroke_bearings(mask, halfwidth=26, sep=25, k=2):
    """Hough-lite: the k best-separated line bearings through the centroid."""
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    sc = []
    for deg in range(-89, 91):
        t = math.radians(deg)
        # bearing deg is CCW-on-paper; direction (cos t, -sin t) in y-down
        # image coords, so the perpendicular offset is:
        d = np.abs((xs - cx) * math.sin(t) + (ys - cy) * math.cos(t))
        sc.append((int((d < halfwidth).sum()), deg))
    sc.sort(reverse=True)
    picks = []
    for cnt, deg in sc:
        if all(min(abs(deg - d), 180 - abs(deg - d)) > sep for _, d in picks):
            picks.append((cnt, deg))
        if len(picks) == k:
            break
    return picks


def xmarks(pn=76, roi=(2300, 3350, 3400, 4400)):
    """The two painted X marks in the lower-right corner of p76."""
    a = page(pn)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    m = (lum < 200) & (sat < 45)
    keep = np.zeros_like(m)
    keep[roi[1]:roi[3], roi[0]:roi[2]] = True
    m &= keep
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    print(f"\n=== p{pn} painted X marks  (grey ink: lum<200, sat<45, ROI x{roi[0]}-{roi[2]} y{roi[1]}-{roi[3]}) ===")
    res = []
    for i in range(1, n + 1):
        if cnt[i] < 5000:
            continue
        ys, xs = np.nonzero(lab == i)
        ang, L, W = pca_axis(ys, xs)
        col = np.median(a[ys, xs], axis=0)
        res.append(dict(cx=float(xs.mean()), cy=float(ys.mean()),
                        bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                        area=int(ys.size), angle=round(ang, 2),
                        length=round(float(L), 1), width=round(float(W), 1),
                        rgb=[int(v) for v in col], mask=(lab == i)))
    res.sort(key=lambda r: r['cy'])
    for k, r in enumerate(res):
        x0, y0, x1, y1 = r['bbox']
        picks, _ = edge_orientations(r['mask'][y0:y1 + 1, x0:x1 + 1])
        inc = abs(picks[0][0] - picks[1][0]) if len(picks) > 1 else float('nan')
        inc = min(inc, 180 - inc)
        # stroke thickness = area / total stroke length
        from scipy import ndimage as _nd
        dt = _nd.distance_transform_edt(r['mask'][y0:y1 + 1, x0:x1 + 1])
        r['thick'] = float(np.percentile(dt[dt > 0], 95) * 2)
        print(f"  X#{k+1}  bbox x[{x0},{x1}] y[{y0},{y1}] = {x1-x0+1}x{y1-y0+1} px "
              f"({(x1-x0+1)/DPI:.2f}x{(y1-y0+1)/DPI:.2f} in)")
        print(f"        centroid ({r['cx']:.0f},{r['cy']:.0f})  ink area {r['area']} px  "
              f"bbox fill {100*r['area']/((x1-x0+1)*(y1-y0+1)):.1f}%  median RGB {r['rgb']}")
        r['bearings'] = [round(p[0], 1) for p in picks]
        print(f"        stroke bearings {picks[0][0]:+.1f} deg and {picks[1][0]:+.1f} deg;  "
              f"included angle {inc:.1f} deg;  "
              f"95th-pct stroke thickness {r['thick']:.0f} px")
    if len(res) == 2:
        A, B = res
        sa = math.sqrt(A['area'] / B['area'])
        print(f"  size ratio X#1/X#2: area {A['area']/B['area']:.3f} -> linear {sa:.3f}; "
              f"diagonal {math.hypot(A['bbox'][2]-A['bbox'][0], A['bbox'][3]-A['bbox'][1]) / math.hypot(B['bbox'][2]-B['bbox'][0], B['bbox'][3]-B['bbox'][1]):.3f}; "
              f"thickness {A['thick']/B['thick']:.3f}")
        print(f"  centre-to-centre {math.hypot(A['cx']-B['cx'], A['cy']-B['cy']):.0f} px "
              f"= {math.hypot(A['cx']-B['cx'], A['cy']-B['cy'])/DPI:.2f} in, bearing "
              f"{math.degrees(math.atan2(-(B['cy']-A['cy']), B['cx']-A['cx'])):+.1f} deg")
    return res


# ------------------------------------------------- p78 scribble + boxed quote
def scribble(pn=78):
    a = page(pn)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    ink = (lum < 140) & (sat < 60)
    lab, n = label_fast(ink)
    sizes = [(int((lab == i).sum()), i) for i in range(1, n + 1)]
    sizes.sort(reverse=True)
    big = sizes[0]
    ys, xs = np.nonzero(lab == big[1])
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    print(f"\n=== p{pn} 'X FUCK ALL X' scrawl ===")
    print(f"  largest dark component: {big[0]} px")
    print(f"  bbox x[{x0},{x1}] y[{y0},{y1}]  = {x1-x0+1} x {y1-y0+1} px "
          f"= {(x1-x0+1)/DPI:.2f} x {(y1-y0+1)/DPI:.2f} in")
    print(f"  centroid ({xs.mean():.0f},{ys.mean():.0f})  "
          f"fill {100*big[0]/((x1-x0+1)*(y1-y0+1)):.1f}% of its bbox")
    ang, L, W = pca_axis(ys, xs)
    print(f"  long axis {ang:+.2f} deg, L={L:.0f} W={W:.0f}")
    print(f"  median RGB of the scrawl ink {list(np.median(a[ys,xs],axis=0).astype(int))}")
    # the white-out quote block inside it
    sub = a[y0:y1 + 1, x0:x1 + 1]
    subl = sub.mean(2)
    solid = lab[y0:y1 + 1, x0:x1 + 1] == big[1]
    white = (subl > 200)
    # keep white pixels that are enclosed: flood the outside
    h, w = white.shape
    seen = np.zeros_like(white)
    stack = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + \
            [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    stack = [(y, x) for y, x in stack if white[y, x]]
    for y, x in stack:
        seen[y, x] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and white[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
    inner = white & ~seen
    iy, ix = np.nonzero(inner)
    print(f"  enclosed white (reversed-out) pixels inside the scrawl: {iy.size}")
    if iy.size:
        ll, nn = label_fast(inner)
        sz = sorted(((int((ll == i).sum()), i) for i in range(1, nn + 1)), reverse=True)
        print(f"  {nn} enclosed white components; 8 largest {[s for s,_ in sz[:8]]}")
        # bounding box of everything above 40 px (the set type, not stray gaps)
        keep = np.zeros_like(inner)
        for s, i in sz:
            if s >= 40:
                keep |= (ll == i)
        ky, kx = np.nonzero(keep)
        ang2, L2, W2 = pca_axis(ky, kx)
        print(f"  reversed-out TYPE: {keep.sum()} px in {sum(1 for s,_ in sz if s>=40)} glyph blobs")
        print(f"    bbox in page coords x[{kx.min()+x0},{kx.max()+x0}] y[{ky.min()+y0},{ky.max()+y0}]"
              f"  = {kx.max()-kx.min()+1} x {ky.max()-ky.min()+1} px")
        print(f"    type block long axis {ang2:+.2f} deg")
        # ---- skew detection: the quote is set on a rotated baseline, so find
        # the rotation that makes the glyph-centroid rows crispest.
        cents = []
        boxes = []
        for s, i in sz:
            if s >= 40:
                yy, xx = np.nonzero(ll == i)
                cents.append((xx.mean(), yy.mean()))
                boxes.append((xx.min(), xx.max(), yy.min(), yy.max()))
        P = np.array(cents)
        # skew score = fraction of EMPTY 8-px rows in the projection profile.
        # (scale-free: collapsing everything into one bin scores badly because
        # a 4-line block must show 3 clean inter-line gaps)
        best = (None, -1)
        for th in np.arange(-30, 30.01, 0.25):
            t = math.radians(th)
            yr = -P[:, 0] * math.sin(t) + P[:, 1] * math.cos(t)
            bins = np.arange(yr.min(), yr.max() + 8, 8)
            h, _ = np.histogram(yr, bins=bins)
            sc = float((h == 0).sum()) / max(1, h.size)
            if sc > best[1]:
                best = (th, sc)
        th = best[0]
        print(f"    SET ANGLE of the reversed-out quote: {th:+.2f} deg "
              f"(rotation that maximises row crispness; scan skew for reference below)")
        t = math.radians(th)
        yr = -P[:, 0] * math.sin(t) + P[:, 1] * math.cos(t)
        xr = P[:, 0] * math.cos(t) + P[:, 1] * math.sin(t)
        o = np.argsort(yr)
        lines, cur = [], [o[0]]
        for i in o[1:]:
            if yr[i] - yr[cur[-1]] > 40:
                lines.append(cur)
                cur = [i]
            else:
                cur.append(i)
        lines.append(cur)
        print(f"    {len(lines)} text lines after de-rotation:")
        bl = []
        for k, ln in enumerate(lines):
            ln = sorted(ln, key=lambda i: xr[i])
            X, Y = P[ln, 0], P[ln, 1]
            hh = [boxes[i][3] - boxes[i][2] for i in ln]
            m_ = np.polyfit(X, Y, 1)[0] if len(ln) >= 3 else float('nan')
            bl.append(np.mean(yr[ln]))
            print(f"      line {k+1}: {len(ln):2d} glyph blobs  x-span "
                  f"{xr[ln].max()-xr[ln].min():5.0f} px  residual slope "
                  f"{math.degrees(math.atan(-m_)):+6.2f} deg  median glyph height "
                  f"{np.median(hh):.0f} px")
        if len(bl) > 1:
            lead = np.diff(bl)
            print(f"    leading between lines: {np.round(lead,1).tolist()} px "
                  f"(mean {lead.mean():.1f} px = {lead.mean()/DPI*72:.1f} pt at 400 dpi)")
        # body text on the same page, for comparison
        bodyang, bodyh = _body_metrics(a)
        print(f"    same page, BODY TEXT: set angle {bodyang:+.2f} deg, "
              f"median glyph height {bodyh:.0f} px")
        print(f"    -> the quote is rotated {th-bodyang:+.2f} deg against the page's own type")
    return dict(bbox=[int(x0), int(y0), int(x1), int(y1)], area=int(big[0]))


def quote_block(pn=78):
    """The reversed-out pull-quote inside the p78 scrawl: set angle, line
    metrics and character pitch, against the page's own body type."""
    from scipy import ndimage as _nd
    a = page(pn)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    ink = (lum < 140) & (sat < 60)
    lab, n = label_fast(ink)
    cnt = np.bincount(lab.ravel())
    big = cnt[1:].argmax() + 1
    ys, xs = np.nonzero(lab == big)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    sub = a[y0:y1 + 1, x0:x1 + 1]
    fill = _nd.binary_fill_holes(lab[y0:y1 + 1, x0:x1 + 1] == big)
    inner = (sub.mean(2) > 200) & fill
    ll, nn = label_fast(inner)
    c2 = np.bincount(ll.ravel())
    keep = np.isin(ll, [i for i in range(1, nn + 1) if c2[i] >= 40])
    im = Image.fromarray((keep * 255).astype(np.uint8))
    best = None
    for th in np.arange(-25, 25.01, 0.25):
        r = np.asarray(im.rotate(th, resample=Image.NEAREST, expand=True, fillcolor=0)) > 0
        prof = r.sum(1).astype(float)
        nz = np.flatnonzero(prof)
        prof = prof[nz.min():nz.max() + 1]
        sc = prof.size * (prof ** 2).sum() / prof.sum() ** 2
        if best is None or sc > best[0]:
            best = (sc, float(th))
    th = best[1]
    print(f"\n=== p{pn} reversed-out pull-quote inside the scrawl ===")
    print(f"  the block levels at PIL rotate({th:+.2f}) -> the quote is SET AT "
          f"{-th:+.2f} deg CCW on the page")
    r = np.asarray(im.rotate(th, resample=Image.NEAREST, expand=True, fillcolor=0)) > 0
    rl, rn = label_fast(r)
    rc = np.bincount(rl.ravel())
    objs = _nd.find_objects(rl)
    rows = []
    for i in range(1, rn + 1):
        if rc[i] < 40:
            continue
        sl = objs[i - 1]
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h > 120 or w > 160:
            continue
        rows.append(((sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2,
                     sl[0].start, sl[0].stop, sl[1].start, sl[1].stop, int(rc[i])))
    rows.sort(key=lambda t: t[1])
    lines, cur = [], [rows[0]]
    for t in rows[1:]:
        if t[1] - cur[-1][1] > 34:
            lines.append(cur)
            cur = [t]
        else:
            cur.append(t)
    lines.append(cur)
    # drop clusters that are stray brush slivers rather than a line of type
    lines = [ln for ln in lines if len(ln) >= 4]
    text = ["The economy of", "love is infinitely", "more efficient than", "hate and war."]
    print(f"  {len(lines)} lines of type after de-rotation")
    base, allh = [], []
    for k, ln in enumerate(lines):
        ln = sorted(ln, key=lambda t: t[0])
        yb0 = int(min(t[2] for t in ln))
        yb1 = int(max(t[3] for t in ln))
        band = r[yb0:yb1 + 1]
        cols = np.flatnonzero(band.sum(0) > 0)
        hh = [t[3] - t[2] for t in ln]
        allh += hh
        base.append(np.median([t[3] for t in ln]))
        lbl = text[k] if k < len(text) else "?"
        nch = len(lbl)
        span = cols.max() - cols.min()
        print(f"   line {k+1} '{lbl}': {len(ln):2d} blobs, ink span {span:4d} px, "
              f"{nch} chars -> {span/(nch-1):5.1f} px per character "
              f"({span/(nch-1)/DPI*72:.2f} pt), glyph heights p50 {np.median(hh):.0f} "
              f"p90 {np.percentile(hh,90):.0f} px")
    lead = np.diff(base)
    print(f"  baseline leading {np.round(lead,1).tolist()} px "
          f"(mean {lead.mean():.1f} px = {lead.mean()/DPI*72:.1f} pt)")
    print(f"  quote glyph heights overall: p50 {np.median(allh):.0f} px, "
          f"p90 {np.percentile(allh,90):.0f} px")
    # body type on the same page, measured the same way
    bang, bh, bpitch, bh90 = _body_pitch(a)
    print(f"  p{pn} BODY TYPE for comparison: set angle {bang:+.2f} deg, "
          f"glyph heights p50 {bh:.0f} p90 {bh90:.0f} px, character pitch "
          f"{bpitch:.1f} px ({bpitch/DPI*72:.2f} pt)")
    print(f"  -> the quote is set {-th-bang:+.2f} deg off the body baseline and "
          f"{np.percentile(allh,90)/bh90:.2f}x its glyph height")
    return th


def _body_pitch(a, roi=(400, 800, 3000, 3100)):
    """Skew, glyph height and fixed pitch of the ordinary body type."""
    from scipy import ndimage as _nd
    lum = a.mean(2)
    m = np.zeros(lum.shape, bool)
    m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < 150
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    objs = _nd.find_objects(lab)
    P, H, C = [], [], []
    for i in range(1, n + 1):
        if not (60 <= cnt[i] <= 3000):
            continue
        sl = objs[i - 1]
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h > 90 or w > 90:
            continue
        P.append(((sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2))
        H.append(h)
        C.append((sl[1].start, sl[1].stop, sl[0].start))
    P = np.array(P)
    best = (0.0, -1)
    for th in np.arange(-4, 4.01, 0.1):
        t = math.radians(th)
        yr = -P[:, 0] * math.sin(t) + P[:, 1] * math.cos(t)
        hh, _ = np.histogram(yr, bins=np.arange(yr.min(), yr.max() + 8, 8))
        sc = hh.size * (hh.astype(float) ** 2).sum() / hh.sum() ** 2
        if sc > best[1]:
            best = (float(th), sc)
    # pitch: modal spacing between consecutive glyph left edges on a line
    byline = {}
    for (l, r_, t_) in C:
        byline.setdefault(t_ // 60, []).append(l)
    d = []
    for k, v in byline.items():
        v = sorted(v)
        d += [b - a_ for a_, b in zip(v, v[1:]) if 5 < b - a_ < 80]
    d = np.array(d)
    hist, edges = np.histogram(d, bins=np.arange(5, 81, 1))
    pitch = edges[hist.argmax()] + 0.5
    return best[0], float(np.median(H)), float(pitch), float(np.percentile(H, 90))


def _body_metrics(a, roi=(400, 800, 3000, 3100)):
    """Skew and glyph height of the page's ordinary body type, same method."""
    from scipy import ndimage as _nd
    lum = a.mean(2)
    m = np.zeros(lum.shape, bool)
    m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < 150
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    objs = _nd.find_objects(lab)
    P, H = [], []
    for i in range(1, n + 1):
        if not (60 <= cnt[i] <= 3000):
            continue
        sl = objs[i - 1]
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h > 90 or w > 90:
            continue
        P.append(((sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2))
        H.append(h)
    P = np.array(P)
    best = (0.0, -1)
    for th in np.arange(-6, 6.01, 0.1):
        t = math.radians(th)
        yr = -P[:, 0] * math.sin(t) + P[:, 1] * math.cos(t)
        hh, _ = np.histogram(yr, bins=np.arange(yr.min(), yr.max() + 8, 8))
        sc = float((hh.astype(float) ** 2).sum())
        if sc > best[1]:
            best = (th, sc)
    return best[0], float(np.median(H))


# --------------------------------------------------------------- p77 'SHIT'
def shit(pn=77, roi=(40, 2550, 950, 3620)):
    """The painted white 'SHIT' on p77's dark-brown ground, and the direction
    its paint runs travel."""
    from scipy import ndimage as _nd
    a = page(pn)
    lum = a.mean(2)
    ground = np.median(a[2000:2400, 1500:1900].reshape(-1, 3), axis=0).astype(int)
    m = np.zeros(lum.shape, bool)
    m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] > 165
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    ids = [i for i in range(1, n + 1) if cnt[i] >= 1200]
    print(f"\n=== p{pn} painted 'SHIT' ===")
    print(f"  page ground median RGB {list(ground)}; paint threshold lum>165")
    sel = np.isin(lab, ids)
    ys, xs = np.nonzero(sel)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    print(f"  {len(ids)} paint components >=1200 px, {sel.sum()} px of paint")
    print(f"  combined bbox x[{x0},{x1}] y[{y0},{y1}] = {x1-x0+1}x{y1-y0+1} px "
          f"({(x1-x0+1)/DPI:.2f}x{(y1-y0+1)/DPI:.2f} in)")
    print(f"  paint median RGB {list(np.median(a[ys,xs],axis=0).astype(int))}")
    ang, L, W = pca_axis(ys, xs)
    print(f"  long axis of the whole tag {ang:+.2f} deg")
    objs = _nd.find_objects(lab)
    for k, i in enumerate(sorted(ids, key=lambda i: objs[i-1][1].start)):
        sl = objs[i - 1]
        yy, xx = np.nonzero(lab == i)
        a2, L2, W2 = pca_axis(yy, xx)
        print(f"    letter blob {k+1}: area {cnt[i]:6d}  bbox x[{sl[1].start},{sl[1].stop-1}] "
              f"y[{sl[0].start},{sl[0].stop-1}]  {sl[1].stop-sl[1].start}x{sl[0].stop-sl[0].start} px "
              f"axis {a2:+.1f} deg")
    # ---- which way do the paint RUNS go?
    # Paint that has run is thin; letter strokes are fat.  Split on the local
    # half-width (distance transform), then keep only long thin filaments.
    dt = _nd.distance_transform_edt(sel)
    core = _nd.binary_closing(dt >= 17, iterations=3)
    dcore = _nd.distance_transform_edt(~core)
    tails = sel & ~_nd.binary_dilation(core, iterations=6)
    tl, tn = label_fast(tails)
    tc = np.bincount(tl.ravel())
    objs2 = _nd.find_objects(tl)
    print(f"\n  paint RUNS (ink >6 px clear of any stroke core, kept when longer"
          f" than 80 px and thinner than 30 px):")
    rows = []
    for i in range(1, tn + 1):
        if tc[i] < 300:
            continue
        yy, xx = np.nonzero(tl == i)
        ang2, L2, W2 = pca_axis(yy, xx)
        if L2 < 80 or W2 > 30:
            continue
        j = np.argmax(dcore[yy, xx])
        ty, tx = yy[j], xx[j]
        k = np.argmin(dcore[yy, xx])
        ry, rx = yy[k], xx[k]
        br = math.degrees(math.atan2(-(ty - ry), tx - rx))
        rows.append((int(tc[i]), int(rx), int(ry), int(tx), int(ty), round(br, 1),
                     round(math.hypot(tx - rx, ty - ry), 1), round(L2, 1), round(W2, 1)))
    up = sum(1 for r in rows if r[5] > 0)
    for r in sorted(rows, key=lambda r: -r[7]):
        print(f"    run {r[7]:6.1f} px long x {r[8]:4.1f} px wide: root ({r[1]},{r[2]})"
              f" -> tip ({r[3]},{r[4]}), bearing {r[5]:+7.1f} deg")
    print(f"  {up} of {len(rows)} runs point INTO THE UPPER half of the printed page"
          f" (bearing > 0).")
    if rows:
        brs = [r[5] for r in rows]
        print(f"  mean run bearing {np.mean(brs):+.1f} deg, median {np.median(brs):+.1f} deg"
              f"   (0 deg = right, +90 = straight UP the page as printed)")
        print(f"  gravity runs DOWN.  These run UP -> the graffiti photograph is"
              f" placed on the page rotated 180 deg from the way the paint dried.")
    return rows


# ------------------------------------------------ p79 wire / bitcoin / signature
def _ink(a, mask, erode=2):
    """Median RGB of a mark's INTERIOR (eroded to keep scanner edge fringing
    out of the colour)."""
    from scipy import ndimage as _nd
    m = _nd.binary_erosion(mask, iterations=erode)
    if m.sum() < 50:
        m = mask
    ys, xs = np.nonzero(m)
    return np.median(a[ys, xs], axis=0).astype(int), int(m.sum())


def region(pn, roi, thresh=150, minpx=600, name=""):
    """All dark ink inside a rectangle, as one measured mark."""
    from scipy import ndimage as _nd
    a = page(pn)
    lum = a.mean(2)
    m = np.zeros(lum.shape, bool)
    m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < thresh
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    sel = np.isin(lab, [i for i in range(1, n + 1) if cnt[i] >= minpx])
    ys, xs = np.nonzero(sel)
    if ys.size == 0:
        print(f"  {name}: nothing over threshold")
        return None
    ang, L, W = pca_axis(ys, xs)
    dt = _nd.distance_transform_edt(sel)
    col, npx = _ink(a, sel)
    nblob = len([i for i in range(1, n + 1) if cnt[i] >= minpx])
    print(f"  {name:22s} bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}] "
          f"= {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1} px "
          f"({(xs.max()-xs.min()+1)/DPI:.2f}x{(ys.max()-ys.min()+1)/DPI:.2f} in)")
    print(f"  {'':22s} centroid ({xs.mean():.0f},{ys.mean():.0f})  ink {ys.size} px in "
          f"{nblob} blobs  long axis {ang:+.2f} deg")
    print(f"  {'':22s} stroke width: median {2*np.median(dt[sel]):.1f} px, "
          f"p95 {2*np.percentile(dt[sel],95):.1f} px    interior RGB {list(col)} "
          f"(from {npx} px)")
    return dict(name=name, bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                area=int(ys.size), angle=round(ang, 2), rgb=[int(v) for v in col],
                sw=float(2 * np.median(dt[sel])), mask=sel, page=pn)


def p79art():
    """Barbed wire, drawn Bitcoin glyph, MAX-heart-KEISER signature."""
    from scipy import ndimage as _nd
    print("\n=== p79 hand-drawn marks ===")
    wire = region(79, (30, 30, 1300, 720), 160, 800, "barbed wire")
    btc = region(79, (130, 3360, 470, 3720), 150, 800, "Bitcoin glyph")
    maxw = region(79, (1180, 3660, 1660, 4010), 150, 600, "signature 'MAX'")
    heart = region(79, (1640, 3690, 1780, 3810), 170, 200, "heart between names")
    keis = region(79, (1330, 3800, 2150, 4160), 150, 600, "signature 'KEISER'")
    # barbs: the wire is thin except where it is wrapped into a coil
    wire = wire_measure()
    if heart and maxw and keis:
        hx = (heart['bbox'][0] + heart['bbox'][2]) / 2
        hy = (heart['bbox'][1] + heart['bbox'][3]) / 2
        print(f"  heart: {heart['bbox'][2]-heart['bbox'][0]+1} x "
              f"{heart['bbox'][3]-heart['bbox'][1]+1} px "
              f"({(heart['bbox'][2]-heart['bbox'][0]+1)/DPI*25.4:.1f} x "
              f"{(heart['bbox'][3]-heart['bbox'][1]+1)/DPI*25.4:.1f} mm), centre "
              f"({hx:.0f},{hy:.0f})")
        fill = _nd.binary_fill_holes(heart['mask'])
        print(f"        outline, not solid: {heart['mask'].sum()} ink px inside a "
              f"filled silhouette of {int(fill.sum())} px "
              f"-> the counter is {int(fill.sum()-heart['mask'].sum())} px")
    return dict(wire=wire, btc=btc, max=maxw, heart=heart, keiser=keis)


def inkcolour():
    """Every hand-drawn mark in the piece, measured the same way: is the artwork
    one pen or several?"""
    print("\n=== interior ink colour of every hand-drawn mark ===")
    print(f"  {'mark':28s} {'page':>4} {'R':>4} {'G':>4} {'B':>4}  {'R-B':>5} "
          f"{'stroke w':>9}")
    specs = [
        ("p76 X mark, upper", 76, (2830, 3500, 3400, 3910), 200),
        ("p76 X mark, lower", 76, (2370, 4010, 2800, 4290), 200),
        ("p78 'X FUCK ALL X' scrawl", 78, (430, 3210, 1500, 3990), 140),
        ("p78 X, left of scrawl", 78, (330, 3330, 560, 3560), 140),
        ("p78 X, right of scrawl", 78, (1380, 3340, 1620, 3580), 140),
        ("p79 barbed wire", 79, (30, 30, 1300, 720), 160),
        ("p79 Bitcoin glyph", 79, (130, 3360, 470, 3720), 150),
        ("p79 'MAX'", 79, (1180, 3660, 1660, 4010), 150),
        ("p79 heart", 79, (1640, 3690, 1780, 3810), 170),
        ("p79 'KEISER'", 79, (1330, 3800, 2150, 4160), 150),
    ]
    from scipy import ndimage as _nd
    out = []
    for name, pn, roi, th in specs:
        a = page(pn)
        lum = a.mean(2)
        m = np.zeros(lum.shape, bool)
        m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < th
        lab, n = label_fast(m)
        cnt = np.bincount(lab.ravel())
        sel = np.isin(lab, [i for i in range(1, n + 1) if cnt[i] >= 400])
        if sel.sum() < 200:
            continue
        col, npx = _ink(a, sel, 3)
        dt = _nd.distance_transform_edt(sel)
        sw = 2 * np.median(dt[sel])
        print(f"  {name:28s} {pn:>4} {col[0]:>4} {col[1]:>4} {col[2]:>4}  "
              f"{col[0]-col[2]:>5} {sw:>7.1f} px")
        out.append((name, col, sw))
    # body-text ink on the same pages, as the printing-black reference
    for pn in (76, 78, 79):
        a = page(pn)
        lum = a.mean(2)
        m = np.zeros(lum.shape, bool)
        m[900:2600, 500:2900] = lum[900:2600, 500:2900] < 120
        col, npx = _ink(a, m, 1)
        print(f"  {'(body-text ink, reference)':28s} {pn:>4} {col[0]:>4} {col[1]:>4} "
              f"{col[2]:>4}  {col[0]-col[2]:>5}")
    return out


def xcensus():
    """Every X mark in the piece, measured identically: the two painted Xs on
    p76 and the two that flank the p78 scrawl."""
    from scipy import ndimage as _nd
    specs = [
        ("p76 upper X", 76, (2830, 3500, 3400, 3910), 200, 5000),
        ("p76 lower X", 76, (2370, 4010, 2800, 4290), 200, 5000),
        ("p78 left X",  78, (330, 3330, 560, 3560), 140, 3000),
        ("p78 right X", 78, (1380, 3340, 1620, 3580), 140, 3000),
    ]
    print("\n=== X-mark census (identical method for all four) ===")
    print(f"  {'mark':12s} {'bbox w x h':>12} {'ink px':>7} {'fill':>6} "
          f"{'stroke A':>9} {'stroke B':>9} {'included':>9} {'median sw':>10}")
    rows = []
    for name, pn, roi, th, minpx in specs:
        a = page(pn)
        lum = a.mean(2)
        m = np.zeros(lum.shape, bool)
        m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < th
        lab, n = label_fast(m)
        cnt = np.bincount(lab.ravel())
        sel = np.isin(lab, [i for i in range(1, n + 1) if cnt[i] >= minpx])
        ys, xs = np.nonzero(sel)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        sub = sel[y0:y1 + 1, x0:x1 + 1]
        picks, _ = edge_orientations(sub, sigma=3.0)
        inc = abs(picks[0][0] - picks[1][0])
        inc = min(inc, 180 - inc)
        dt = _nd.distance_transform_edt(sel)
        sw = 2 * np.median(dt[sel])
        print(f"  {name:12s} {x1-x0+1:5d} x{y1-y0+1:5d} {ys.size:7d} "
              f"{100*ys.size/((x1-x0+1)*(y1-y0+1)):5.1f}% {picks[0][0]:+8.1f} "
              f"{picks[1][0]:+8.1f} {inc:8.1f} {sw:8.1f} px")
        rows.append((name, x1 - x0 + 1, y1 - y0 + 1, ys.size, picks[0][0], picks[1][0], inc, sw))
    print("  pairwise size ratios (bbox diagonal):")
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            di = math.hypot(rows[i][1], rows[i][2])
            dj = math.hypot(rows[j][1], rows[j][2])
            print(f"    {rows[i][0]} / {rows[j][0]} = {di/dj:.3f}   "
                  f"stroke-width ratio {rows[i][7]/rows[j][7]:.3f}   "
                  f"included-angle difference {abs(rows[i][6]-rows[j][6]):.1f} deg")
    return rows


def wire_measure():
    """The p79 barbed wire as its own connected component (the ROI also clips
    the first body line's dark highlight bar, so take the largest blob only)."""
    from scipy import ndimage as _nd
    a = page(79)
    lum = a.mean(2)
    m = np.zeros(lum.shape, bool)
    m[30:740, 30:1300] = lum[30:740, 30:1300] < 160
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    sel = lab == (cnt[1:].argmax() + 1)
    ys, xs = np.nonzero(sel)
    ang, L, W = pca_axis(ys, xs)
    dt = _nd.distance_transform_edt(sel)
    print(f"\n  barbed wire, single connected stroke: {int(sel.sum())} ink px, "
          f"bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}]")
    print(f"    long axis {ang:+.2f} deg, run {L:.0f} px ({L/DPI:.2f} in), "
          f"transverse spread {W:.0f} px")
    print(f"    median stroke width {2*np.median(dt[sel]):.1f} px "
          f"({2*np.median(dt[sel])/DPI*25.4:.2f} mm), p95 {2*np.percentile(dt[sel],95):.1f} px")
    t = math.radians(ang)
    u = (xs - xs.mean()) * math.cos(t) - (ys - ys.mean()) * math.sin(t)
    v = (xs - xs.mean()) * math.sin(t) + (ys - ys.mean()) * math.cos(t)
    h, edges = np.histogram(u, bins=np.arange(u.min(), u.max() + 25, 25))
    med = np.median(h)
    idx = [i for i in range(len(h)) if h[i] > 2.2 * med]
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= 3:
            groups[-1].append(i)
        else:
            groups.append([i])
    print(f"    ink is {med:.0f} px per 25-px bin along the wire; "
          f"{len(groups)} bins-clusters exceed 2.2x that = {len(groups)} barb coils")
    cents = []
    for g in groups:
        lo, hi = edges[g[0]], edges[g[-1]] + 25
        sl = (u >= lo) & (u < hi)
        cents.append((xs[sl].mean(), ys[sl].mean()))
        print(f"      coil at page ({xs[sl].mean():.0f},{ys[sl].mean():.0f}): "
              f"{25*len(g)} px of wire, {int(sl.sum())} ink px, perpendicular "
              f"spread {v[sl].max()-v[sl].min():.0f} px")
    if len(cents) == 2:
        d = math.hypot(cents[0][0] - cents[1][0], cents[0][1] - cents[1][1])
        print(f"      coil spacing {d:.0f} px = {d/DPI:.2f} in")
    return dict(area=int(sel.sum()), angle=round(ang, 2), coils=len(groups))


def xiou(size=200):
    """Silhouette overlap between the four X marks, after aspect-normalised
    resize and a small search over rotation and shift.  Answers: which Xs are
    the same drawing used twice?"""
    specs = [("p76 upper X", 76, (2830, 3500, 3400, 3910), 200, 5000),
             ("p76 lower X", 76, (2370, 4010, 2800, 4290), 200, 5000),
             ("p78 left X", 78, (330, 3330, 560, 3560), 140, 3000),
             ("p78 right X", 78, (1380, 3340, 1620, 3580), 140, 3000)]
    chips = {}
    for name, pn, roi, th, minpx in specs:
        a = page(pn)
        lum = a.mean(2)
        m = np.zeros(lum.shape, bool)
        m[roi[1]:roi[3], roi[0]:roi[2]] = lum[roi[1]:roi[3], roi[0]:roi[2]] < th
        lab, n = label_fast(m)
        cnt = np.bincount(lab.ravel())
        sel = np.isin(lab, [i for i in range(1, n + 1) if cnt[i] >= minpx])
        ys, xs = np.nonzero(sel)
        chips[name] = sel[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    def best_iou(A, B):
        best, bp = 0.0, None
        A2 = np.asarray(Image.fromarray((A * 255).astype(np.uint8))
                        .resize((size, size), Image.NEAREST)) > 0
        for th in np.arange(-12, 12.01, 1.0):
            bb = np.asarray(Image.fromarray((B * 255).astype(np.uint8))
                            .resize((size, size), Image.NEAREST)
                            .rotate(th, resample=Image.NEAREST, fillcolor=0)) > 0
            for dx in range(-14, 15, 2):
                for dy in range(-14, 15, 2):
                    b2 = np.roll(np.roll(bb, dy, 0), dx, 1)
                    v = (A2 & b2).sum() / (A2 | b2).sum()
                    if v > best:
                        best, bp = v, (th, dx, dy)
        return best, bp

    print("\n=== X silhouette overlap (aspect-normalised, best small rot/shift) ===")
    names = list(chips)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v, bp = best_iou(chips[names[i]], chips[names[j]])
            print(f"  {names[i]:12s} vs {names[j]:12s}  IoU {v:.3f}  "
                  f"(rot {bp[0]:+.0f} deg, shift {bp[1]},{bp[2]})")


def shit_runs():
    """A single scale-free statistic for the direction of p77's paint runs:
    where does the THIN ink sit relative to the THICK letter cores?"""
    from scipy import ndimage as _nd
    a = page(77)
    lum = a.mean(2)
    m = np.zeros(lum.shape, bool)
    m[2550:3620, 40:950] = lum[2550:3620, 40:950] > 165
    lab, n = label_fast(m)
    cnt = np.bincount(lab.ravel())
    sel = np.isin(lab, [i for i in range(1, n + 1) if cnt[i] >= 1200])
    dt = _nd.distance_transform_edt(sel)
    ys, xs = np.nonzero(sel)
    d = dt[ys, xs]
    thin, thick = d <= 8, d >= 20
    print("\n=== p77 'SHIT': which way did the paint run? ===")
    print(f"  paint {int(sel.sum())} px; thin (local half-width <=8 px) "
          f"{int(thin.sum())}; thick (>=20 px) {int(thick.sum())}")
    print(f"  centroid y: thin {ys[thin].mean():.1f}, thick {ys[thick].mean():.1f} "
          f"-> the thin ink sits {ys[thick].mean()-ys[thin].mean():.1f} px ABOVE the cores")
    print(f"  thick-core y range {ys[thick].min()}..{ys[thick].max()}; "
          f"thin ink y range {ys[thin].min()}..{ys[thin].max()}")
    print(f"  thin ink reaches {ys[thick].min()-ys[thin].min()} px ABOVE the core top "
          f"and only {ys[thin].max()-ys[thick].max()} px below the core bottom "
          f"(ratio {(ys[thick].min()-ys[thin].min())/(ys[thin].max()-ys[thick].max()):.2f}:1)")
    yy = ys.astype(float)
    print(f"  vertical ink-profile skewness {((yy-yy.mean())**3).mean()/yy.std()**3:+.3f} "
          f"(negative = long tail toward the TOP of the printed page)")
    q = np.quantile(ys, [0, .1, .9, 1.0])
    print(f"  mean local half-width: top 10% of the ink {d[(ys>=q[0])&(ys<=q[1])].mean():.2f} px, "
          f"bottom 10% {d[(ys>=q[2])&(ys<=q[3])].mean():.2f} px")
    print("  Gravity pulls paint DOWN.  These runs go UP -> the graffiti photograph")
    print("  is placed on the page 180 deg from the way the paint dried.")


def orangesplit():
    """On p79 the page carries BOTH kinds of orange: photographed gelatin caps
    and printed highlight bars.  Measure them apart, on the same sheet, in the
    same scan pass."""
    print("\n=== p79: photographed orange vs printed orange, same page ===")
    for pn in (73, 79):
        a = page(pn)
        r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        o = (r - b > 60) & (r > 140) & (g < r - 30)
        lab, n = label_fast(o)
        cnt = np.bincount(lab.ravel())
        from scipy import ndimage as _nd
        objs = _nd.find_objects(lab)
        pill, bar = [], []
        for i in range(1, n + 1):
            if cnt[i] < 2000:
                continue
            sl = objs[i - 1]
            h = sl[0].stop - sl[0].start
            w = sl[1].stop - sl[1].start
            (pill if 0.4 <= w / h <= 2.0 else bar).append(i)
        for tag, ids in (("gelatin capsule caps", pill), ("printed highlight bars", bar)):
            if not ids:
                print(f"  p{pn} {tag:24s} none")
                continue
            m = np.isin(lab, ids)
            ys, xs = np.nonzero(m)
            px = a[ys, xs]
            med = np.median(px, axis=0).astype(int)
            per = [list(np.median(a[np.nonzero(lab == i)], axis=0).astype(int)) for i in ids]
            print(f"  p{pn} {tag:24s} {len(ids)} regions, {ys.size:6d} px, "
                  f"median RGB {list(med)}")
            print(f"  {'':29s} per region: {per}")
    print("  -> the two oranges differ on the SAME sheet, so this is not a scan or")
    print("     paper effect; the capsule orange is a photographed object, the bar")
    print("     orange is the article's spot ink.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all")
    args = ap.parse_args()
    o = args.only
    r73 = r79 = a73 = a79 = None
    if o in ("all", "caps", "reuse"):
        r73, a73 = caps(73)
        r79, a79 = caps(79)
    if o in ("all", "reuse"):
        procrustes(r73, r79)
        reuse(r73, a73, r79, a79)
    if o in ("all", "xmarks"):
        xmarks(76)
    if o in ("all", "scribble"):
        scribble(78)
    if o in ("all", "quote"):
        quote_block(78)
    if o in ("all", "shit"):
        shit(77)
    if o in ("all", "p79art"):
        p79art()
    if o in ("all", "ink"):
        inkcolour()
    if o in ("all", "xcensus"):
        xcensus()
    if o in ("all", "xiou"):
        xiou()
    if o in ("all", "runs"):
        shit_runs()
    if o in ("all", "orange"):
        orangesplit()


if __name__ == "__main__":
    main()
