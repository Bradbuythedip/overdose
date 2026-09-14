#!/usr/bin/env python3
"""
Page 79's baseline curves. Does each glyph sit exactly ON the curve?

THE IDEA
The body text on p79 is set on an arc — the lines bow across the page. That is
a strange choice for an article's conclusion, and it has a property nothing
else on the spread has: on a curve, every glyph carries a VERTICAL OFFSET.

Fit the arc, and each character's residual from the fitted arc is a channel.
It is invisible to a reader, it survives printing, and it is structurally
impossible to even look at until the curve has been modelled. Which is exactly
why nobody has: `wf/glyphs_p79.tsv` stores ONE y per line —

    line 1: 10 glyphs, y range 2601-2601 (spread 0)

— so the existing corpus has no per-glyph vertical position at all, on any
page. It also recovered 6 of 26 lines here, because a line-finder that groups
glyphs by shared horizontal y cannot group text whose y changes mid-line.

WHAT THIS MEASURES
Per-glyph baseline residual, and whether it carries more than print noise.
The null matters more than the signal: ink spread, paper texture, JPEG
artefacts and the photograph's own perspective all perturb a centroid. So the
test is comparative — p79 (curved) against p75, p76, p78 (flat) — and the
question is whether p79's residuals are structured in a way the flat pages'
are not.

A residual channel that exists only on the curved page is evidence. One that
looks the same everywhere is the camera.

  python3 curve_residual.py --selftest
  python3 curve_residual.py --page 79
"""
import argparse, sys

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("needs opencv")

IMG = {75: "IMG_6246.jpeg", 76: "IMG_6247.jpeg", 77: "IMG_6248.jpeg",
       78: "IMG_6249.jpeg", 79: "IMG_6250.jpeg"}
BASE = "/home/user/overdose/public/images"


def glyph_boxes(path, invert=False, min_area=12, max_area=4000):
    """Connected components that look like glyphs: (cx, baseline_y, w, h)."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, []
    g = cv2.GaussianBlur(img, (3, 3), 0)
    th = cv2.threshold(g, 0, 255,
                       cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if invert:
        th = cv2.bitwise_not(th)
    n, _lab, stats, cent = cv2.connectedComponentsWithStats(th, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if not (min_area <= a <= max_area):
            continue
        if not (3 <= w <= 80 and 4 <= h <= 90):
            continue
        if h > 6 * w or w > 8 * h:
            continue
        out.append((float(cent[i][0]), float(y + h), w, h))   # baseline = box bottom
    return img.shape, out


def group_lines(boxes, dx_max=60, dy_max=14, min_len=8):
    """Chain glyphs into lines by walking LEFT TO RIGHT along the baseline.

    WHY NOT A y-BUCKET. A fixed-y bucket cannot group a curved line. But the
    obvious fix -- a loose tolerance on a drifting y -- is worse: on a curved
    page adjacent lines approach each other vertically, and a loose walker
    merges them. The first version of this file did exactly that, put 1,083
    p79 glyphs into 7 lines at 155 glyphs per line against 56-67 on the flat
    pages, and reported a 6.47x residual spread that was line spacing being
    fitted as curve.

    So: start at the leftmost unassigned glyph and repeatedly attach the
    nearest glyph to its RIGHT within a small dx and dy window. The dy window
    is per-step, so the chain follows arbitrary curvature while never jumping
    to a neighbouring line, because a neighbouring line is far in y at the
    same x.
    """
    remaining = sorted(boxes, key=lambda b: (b[0], b[1]))
    used = [False] * len(remaining)
    lines = []
    for i in range(len(remaining)):
        if used[i]:
            continue
        chain = [remaining[i]]
        used[i] = True
        cx, cy = remaining[i][0], remaining[i][1]
        while True:
            best, bj, bd = None, -1, 1e18
            for j in range(len(remaining)):
                if used[j]:
                    continue
                x, y = remaining[j][0], remaining[j][1]
                if x <= cx or x - cx > dx_max:
                    continue
                if abs(y - cy) > dy_max:
                    continue
                d = (x - cx) + 3.0 * abs(y - cy)
                if d < bd:
                    best, bj, bd = remaining[j], j, d
            if best is None:
                break
            used[bj] = True
            chain.append(best)
            cx, cy = best[0], best[1]
        if len(chain) >= min_len:
            lines.append(sorted(chain, key=lambda z: z[0]))
    return lines


def residuals(line, deg=2):
    """Fit a polynomial baseline and return per-glyph residuals in pixels."""
    if len(line) < deg + 2:
        return None, None
    x = np.array([b[0] for b in line], float)
    y = np.array([b[1] for b in line], float)
    c = np.polyfit(x, y, deg)
    return y - np.polyval(c, x), c


def curvature(line):
    """The quadratic term of the fitted baseline: how bowed is this line."""
    _r, c = residuals(line)
    return None if c is None else float(c[0])


def profile(page, deg=2):
    shape, boxes = glyph_boxes(f"{BASE}/{IMG[page]}",
                               invert=(page == 77))
    if shape is None:
        return None
    lines = group_lines(boxes)
    allres, curves = [], []
    for ln in lines:
        r, _c = residuals(ln, deg)
        if r is not None:
            allres.append(r)
            k = curvature(ln)
            if k is not None:
                curves.append(k)
    flat = np.concatenate(allres) if allres else np.array([])
    return {"page": page, "glyphs": len(boxes), "lines": len(lines),
            "resid": flat, "curv": np.array(curves)}


def selftest():
    ok = True
    # a PLANTED offset must be recovered. Build a synthetic curved line of
    # glyph boxes, push every third glyph down by 3px, and require the fit to
    # show it. Without this, "residuals look like noise" is unfalsifiable.
    x = np.arange(40) * 30.0 + 100
    true_y = 1000 + 0.0004 * (x - 700) ** 2
    planted = true_y.copy()
    planted[::3] += 3.0
    line = [(float(a), float(b), 10, 12) for a, b in zip(x, planted)]
    r, _c = residuals(line, 2)
    hi = r[::3].mean()
    lo = np.delete(r, np.arange(0, len(r), 3)).mean()
    good = (hi - lo) > 2.0
    ok &= good
    sys.stderr.write(f"  a planted 3px offset on every 3rd glyph is recovered: "
                     f"separation {hi-lo:.2f}px "
                     f"{'OK' if good else 'FAIL - the fit absorbs the signal'}\n")

    clean = [(float(a), float(b), 10, 12) for a, b in zip(x, true_y)]
    r2, _c = residuals(clean, 2)
    good = float(np.abs(r2).max()) < 0.01
    ok &= good
    sys.stderr.write(f"  an unperturbed curve fits to "
                     f"{float(np.abs(r2).max()):.4f}px: "
                     f"{'OK' if good else 'FAIL'}\n")

    # the grouper must follow a curve a fixed-y bucket would split...
    boxes = [(float(a), float(b), 10, 12) for a, b in zip(x, true_y)]
    gl = group_lines(boxes)
    drop = true_y.max() - true_y.min()
    good = len(gl) == 1
    ok &= good
    sys.stderr.write(f"  a line drifting {drop:.0f}px is grouped as "
                     f"{len(gl)} line(s): "
                     f"{'OK' if good else 'FAIL - grouper splits curves'}\n")

    # ...and must NOT merge two curved lines that come close. This is the
    # regression: the first version merged them and reported the line spacing
    # as a 6.47x residual signal.
    two = boxes + [(float(a), float(b) + 40, 10, 12)
                   for a, b in zip(x, true_y)]
    g2 = group_lines(two)
    good = len(g2) == 2 and all(35 <= len(c) <= 45 for c in g2)
    ok &= good
    sys.stderr.write(f"  two curved lines 40px apart stay separate: "
                     f"{len(g2)} lines of {[len(c) for c in g2]} "
                     f"{'OK' if good else 'FAIL - merges lines'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="75,76,78,79")
    ap.add_argument("--deg", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the fit cannot recover a planted offset; refusing")
    if a.selftest:
        return

    pages = [int(p) for p in a.pages.split(",")]
    sys.stderr.write(f"\n  per-glyph baseline residuals, degree-{a.deg} fit\n\n")
    sys.stderr.write(f"  {'page':>5} {'glyphs':>7} {'lines':>6} {'g/line':>7} "
                     f"{'|curv|':>10} {'resid sd':>9} {'resid IQR':>10}\n")
    profs = {}
    for p in pages:
        pr = profile(p, a.deg)
        if pr is None or not len(pr["resid"]):
            sys.stderr.write(f"  {p:>5}  unreadable\n")
            continue
        profs[p] = pr
        gpl = pr["glyphs"] / max(pr["lines"], 1)
        pr["gpl"] = gpl
        k = float(np.abs(pr["curv"]).mean()) if len(pr["curv"]) else 0.0
        r = pr["resid"]
        sys.stderr.write(f"  {p:>5} {pr['glyphs']:>7} {pr['lines']:>6} "
                         f"{pr['gpl']:>7.0f} {k:>10.2e} {r.std():>9.3f} "
                         f"{np.subtract(*np.percentile(r, [75, 25])):>10.3f}\n")

    if 79 in profs and len(profs) > 1:
        flat = np.concatenate([profs[p]["curv"] for p in profs if p != 79
                               and len(profs[p]["curv"])])
        c79 = profs[79]["curv"]
        sys.stderr.write(f"\n  IS P79 ACTUALLY CURVED?\n")
        if len(flat) and len(c79):
            sys.stderr.write(
                f"    p79 mean |quadratic term| {np.abs(c79).mean():.3e}\n"
                f"    flat pages               {np.abs(flat).mean():.3e}\n"
                f"    ratio                    "
                f"{np.abs(c79).mean()/max(np.abs(flat).mean(),1e-12):.2f}x\n")
        rs = {p: profs[p]["resid"].std() for p in profs}
        sys.stderr.write(f"\n  RESIDUAL SPREAD BY PAGE (px): "
                         f"{ {p: round(v,3) for p, v in rs.items()} }\n")
        # GATE: if p79's glyphs-per-line is far from the flat pages', the
        # grouping is wrong and the residual comparison is meaningless.
        g79 = profs[79]["gpl"]
        gflat = [profs[p]["gpl"] for p in profs if p != 79]
        if gflat and (g79 > 1.6 * (sum(gflat) / len(gflat))):
            sys.stderr.write(
                f"\n  REFUSING TO COMPARE. p79 has {g79:.0f} glyphs per line "
                f"against {sum(gflat)/len(gflat):.0f} on the flat pages, so "
                f"lines are\n  being merged and any residual is line spacing, "
                f"not a channel.\n")
            return
        others = [v for p, v in rs.items() if p != 79]
        if others:
            ratio = rs[79] / (sum(others) / len(others))
            sys.stderr.write(f"    p79 / flat-page mean = {ratio:.2f}x\n")
            if ratio < 1.3:
                sys.stderr.write(
                    "\n  p79's glyphs sit on its curve no less tightly than the\n"
                    "  flat pages' glyphs sit on theirs. There is no extra\n"
                    "  vertical channel here -- the curve is a design flourish,\n"
                    "  and the residual that remains is the camera and the ink.\n")
            else:
                sys.stderr.write(
                    f"\n  p79 residuals are {ratio:.2f}x the flat-page spread.\n"
                    f"  That is worth pursuing: quantise and read them out.\n")


if __name__ == "__main__":
    main()
