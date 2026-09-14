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
def shit(pn=77):
    a = page(pn)
    lum = a.mean(2)
    # page ground is dark brown; the graffiti is the bright paint on it
    print(f"\n=== p{pn} white 'SHIT' graffiti ===")
    print(f"  page ground median RGB {list(np.median(a[2000:2400,1500:1900].reshape(-1,3),axis=0).astype(int))}")
    m = lum > 175
    # restrict to the upper-right quadrant where the graffiti sits
    m[2200:, :] = False
    m[:, :1400] = False
    lab, n = label_fast(m)
    res = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if ys.size < 1500:
            continue
        res.append((ys, xs))
    res.sort(key=lambda t: t[1].mean())
    allx = np.concatenate([t[1] for t in res]) if res else np.array([])
    ally = np.concatenate([t[0] for t in res]) if res else np.array([])
    if allx.size:
        print(f"  {len(res)} bright components >=1500 px; combined bbox "
              f"x[{allx.min()},{allx.max()}] y[{ally.min()},{ally.max()}] "
              f"= {allx.max()-allx.min()+1} x {ally.max()-ally.min()+1} px "
              f"({(allx.max()-allx.min()+1)/DPI:.2f} x {(ally.max()-ally.min()+1)/DPI:.2f} in)")
        ang, L, W = pca_axis(ally, allx)
        print(f"  combined long axis {ang:+.2f} deg")
        for k, (ys, xs) in enumerate(res):
            a2, L2, W2 = pca_axis(ys, xs)
            col = np.median(a[ys, xs], axis=0).astype(int)
            print(f"    blob {k+1}: area {ys.size:6d} bbox x[{xs.min()},{xs.max()}] "
                  f"y[{ys.min()},{ys.max()}] h={ys.max()-ys.min()+1} axis {a2:+.1f} "
                  f"RGB {list(col)}")
    return res


# ------------------------------------------------ p79 wire / bitcoin / signature
def p79art():
    pn = 79
    a = page(pn)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    ink = (lum < 150) & (sat < 60)
    lab, n = label_fast(ink)
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if ys.size < 800:
            continue
        comps.append((ys.size, ys, xs))
    comps.sort(reverse=True, key=lambda t: t[0])
    print(f"\n=== p{pn} hand-drawn marks (dark, low-saturation, >=800 px) ===")
    named = []
    for sz, ys, xs in comps[:14]:
        ang, L, W = pca_axis(ys, xs)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
        col = np.median(a[ys, xs], axis=0).astype(int)
        where = "wire(top-left)" if y1 < 900 and x0 < 1200 else \
                ("signature/heart" if y0 > 3000 and 900 < xs.mean() < 2600 else
                 ("bitcoin-glyph" if y0 > 3000 and xs.mean() <= 900 else "?"))
        print(f"  area {sz:6d} bbox x[{x0},{x1}] y[{y0},{y1}] "
              f"({x1-x0+1}x{y1-y0+1}px) axis {ang:+6.2f} L={L:6.0f} W={W:5.0f} "
              f"RGB {list(col)}  {where}")
        named.append((sz, x0, y0, x1, y1, ang, where))
    # barbed wire: count the barbs (local thickness maxima along the wire)
    wire = np.zeros_like(ink)
    for sz, ys, xs in comps:
        if ys.max() < 950 and xs.min() < 1400:
            wire[ys, xs] = True
    wy, wx = np.nonzero(wire)
    if wy.size:
        ang, L, W = pca_axis(wy, wx)
        print(f"\n  barbed wire: {wy.size} ink px, bbox x[{wx.min()},{wx.max()}] "
              f"y[{wy.min()},{wy.max()}], long axis {ang:+.2f} deg, L={L:.0f} W={W:.0f}")
        # thickness profile perpendicular to the run: count ink per column
        cols = wire.sum(0)
        nz = np.flatnonzero(cols)
        prof = cols[nz.min():nz.max() + 1].astype(float)
        k = 25
        sm = np.convolve(prof, np.ones(k) / k, mode="same")
        peaks = [i for i in range(k, sm.size - k)
                 if sm[i] == sm[max(0, i - k):i + k].max() and sm[i] > sm.mean() * 1.25]
        merged = []
        for p in peaks:
            if not merged or p - merged[-1] > 60:
                merged.append(p)
        print(f"  column-thickness peaks (barb clusters): {len(merged)} at x = "
              f"{[int(p+nz.min()+wx.min()*0) for p in merged]}")
    return comps


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
    if o in ("all", "shit"):
        shit(77)
    if o in ("all", "p79art"):
        p79art()


if __name__ == "__main__":
    main()
