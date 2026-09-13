#!/usr/bin/env python3
"""
Per-LETTER weight (bold / regular) recovery from the page scans, by comparing
each glyph with other instances of the SAME letter.

Why the earlier verdict ("unrecoverable at this resolution") was wrong
---------------------------------------------------------------------
window/bold_cipher_resolved.md measured "George" as G=4.6 e=6.4 o=3.6 r=3.7
g=3.3 e=6.4 and called the intra-word spread noise. But the vision agents had
independently reported that only "Gee" of "George" is bold. The measurement
and the eyes agree: bold is applied PER LETTER, and a per-letter comparison
(this 'e' vs every other 'e' on the page) separates the two weights, whereas a
per-line threshold mixing letter identities cannot.

Method (profile based, no connected-component segmentation of glyphs)
--------------------------------------------------------------------
1. binarize (Otsu), restrict to the main text column
2. text lines = runs of the row ink profile
3. per line: fit the typewriter grid (pitch, phase) by minimising ink on the
   cell boundaries; ink per cell; occupied cells -> runs -> words
4. DP-align run lengths with the transcript line's word lengths, assign chars
5. per glyph cell: ink area, EDT mean stroke width
6. per letter identity: reference = 35th percentile over the page;
   area_ratio = area / reference

Outputs solver/wf/glyphs_p{page}.tsv (one row per glyph cell) and prints the
transcript with bold letters UPPERCASED for eyeballing.

  python3 glyph_weight.py --page 75 [--debug-line 6]
"""
import argparse, os, re, sys

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bold_extract as B

PAGES = {75: "IMG_6246.jpeg", 76: "IMG_6247.jpeg", 77: "IMG_6248.jpeg",
         78: "IMG_6249.jpeg", 79: "IMG_6250.jpeg"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def transcript_lines(page):
    txt = open(os.path.join(ROOT, "solver", "article_transcript.txt")).read()
    sec = txt.split(f"=== PAGE {page} ")[1].split("=== PAGE")[0]
    lines = sec.split("\n")[1:]
    return [l for l in lines if l.strip()]


def page_ink(page, scale=2):
    im, g = B.load_gray(os.path.join(ROOT, PAGES[page]), scale)
    if page == 77:
        g = 255 - g
    ink, thr, bars = B.ink_mask(g)
    return im, g, ink


def text_column(ink, scale):
    """x-range of the main text column from character-like components."""
    comps = B.components(ink, 14 * scale // 2, 90 * scale // 2, 40)
    xs = np.array([c["bbox"][0] for c in comps])
    lo, hi = np.percentile(xs, [4, 97])
    xe = np.array([c["bbox"][2] for c in comps])
    return int(lo - 6 * scale), int(min(ink.shape[1], np.percentile(xe, 99) + 6 * scale))


def find_lines(ink, x0, x1, scale):
    band = ink[:, x0:x1]
    prof = band.sum(axis=1)
    thr = max(3, 0.004 * (x1 - x0))
    on = prof > thr
    lines, y = [], 0
    H = len(on)
    while y < H:
        if on[y]:
            s = y
            while y < H and on[y]:
                y += 1
            if y - s >= 10 * scale:
                lines.append((s, y))
        else:
            y += 1
    # merge lines separated by a tiny gap (dots of i, accents)
    merged = []
    for s, e in lines:
        if merged and s - merged[-1][1] <= 3 * scale and (e - merged[-1][0]) <= 40 * scale:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def fit_grid(prof, scale):
    """Return (pitch, phase, occupancy score) fitting a monospace grid to a
    column ink profile. Boundaries should carry little ink."""
    n = len(prof)
    p = prof.astype(float)
    # coarse pitch by autocorrelation
    lags = np.arange(int(12 * scale), int(45 * scale))
    pm = p - p.mean()
    ac = np.array([np.dot(pm[:-l], pm[l:]) for l in lags])
    pitch0 = float(lags[int(np.argmax(ac))])
    best = None
    xs = np.arange(n)
    for pitch in np.arange(pitch0 - 2.0, pitch0 + 2.0, 0.05):
        for phase in np.arange(0, pitch, 0.5):
            b = np.arange(phase, n, pitch)
            bi = np.round(b).astype(int)
            bi = bi[(bi >= 1) & (bi < n - 1)]
            if len(bi) < 4:
                continue
            cost = (p[bi - 1] + p[bi] + p[bi + 1]).sum() / len(bi)
            if best is None or cost < best[2]:
                best = (pitch, phase, cost)
    return best


def dp_align(runs, words):
    """Align observed runs (list of lists of cell idx) with transcript words.
    Returns list of (run_indices, word_index) matches."""
    R, W = len(runs), len(words)
    rl = [len(r) for r in runs]
    wl = [len(w) for w in words]
    INF = 10 ** 9
    cost = [[INF] * (W + 1) for _ in range(R + 1)]
    back = [[None] * (W + 1) for _ in range(R + 1)]
    cost[0][0] = 0
    for i in range(R + 1):
        for j in range(W + 1):
            c = cost[i][j]
            if c >= INF:
                continue
            if i < R and j < W:   # match one run to one word
                nc = c + abs(rl[i] - wl[j])
                if nc < cost[i + 1][j + 1]:
                    cost[i + 1][j + 1] = nc; back[i + 1][j + 1] = ("m", 1)
            if i + 1 < R and j < W:   # merge two runs into one word
                nc = c + abs(rl[i] + rl[i + 1] + 1 - wl[j]) + 2
                if nc < cost[i + 2][j + 1]:
                    cost[i + 2][j + 1] = nc; back[i + 2][j + 1] = ("m", 2)
            if i + 2 < R and j < W:   # merge three runs
                nc = c + abs(rl[i] + rl[i + 1] + rl[i + 2] + 2 - wl[j]) + 4
                if nc < cost[i + 3][j + 1]:
                    cost[i + 3][j + 1] = nc; back[i + 3][j + 1] = ("m", 3)
            if i < R and j + 1 < W:   # one run spans two words (missed gap)
                nc = c + abs(rl[i] - (wl[j] + wl[j + 1] + 1)) + 2
                if nc < cost[i + 1][j + 2]:
                    cost[i + 1][j + 2] = nc; back[i + 1][j + 2] = ("s", 2)
            if i < R:   # spurious run
                nc = c + rl[i] + 3
                if nc < cost[i + 1][j]:
                    cost[i + 1][j] = nc; back[i + 1][j] = ("x", 0)
            if j < W:   # missed word
                nc = c + wl[j] + 3
                if nc < cost[i][j + 1]:
                    cost[i][j + 1] = nc; back[i][j + 1] = ("w", 0)
    # backtrack
    i, j = R, W
    matches = []
    while i > 0 or j > 0:
        b = back[i][j]
        if b is None:
            break
        kind, k = b
        if kind == "m":
            matches.append((list(range(i - k, i)), [j - 1]))
            i -= k; j -= 1
        elif kind == "s":
            matches.append(([i - 1], [j - 2, j - 1]))
            i -= 1; j -= 2
        elif kind == "x":
            i -= 1
        else:
            j -= 1
    matches.reverse()
    return matches, cost[R][W]


def assign_chars(runs, words, matches):
    """Return dict cell -> char for aligned cells."""
    out = {}
    for ris, wis in matches:
        cells = []
        for a, ri in enumerate(ris):
            if a > 0:
                cells.append(None)   # a merged gap counts as a space cell
            cells += runs[ri]
        text = " ".join(words[wi] for wi in wis)
        chars = list(text)
        if len(cells) == len(chars):
            for c, ch in zip(cells, chars):
                if c is not None and ch != " ":
                    out[c] = ch
        else:
            # proportional map, but keep spaces out
            real = [c for c in cells if c is not None]
            letters = [ch for ch in chars if ch != " "]
            n, m = len(real), len(letters)
            for k, c in enumerate(real):
                out[c] = letters[min(m - 1, int(round(k * (m - 1) / max(n - 1, 1))))]
    return out


def line_runs(prof, gap_thr):
    """Runs of ink columns; gaps shorter than gap_thr are bridged (within word)."""
    on = prof > 0
    n = len(on)
    runs, x = [], 0
    while x < n:
        if on[x]:
            s = x
            while x < n and on[x]:
                x += 1
            runs.append([s, x])
        else:
            x += 1
    # merge runs separated by small gaps into words
    words, cur = [], None
    for s, e in runs:
        if cur is not None and s - cur[1] < gap_thr:
            cur[1] = e
        else:
            if cur is not None:
                words.append(cur)
            cur = [s, e]
    if cur is not None:
        words.append(cur)
    return words


def split_word(prof, ws, we, text, wexp, alpha=1.0, beta=0.02):
    """Place len(text)-1 cuts inside [ws, we) minimising ink at cuts plus a
    width prior per letter. Candidates: local minima of the profile."""
    n = len(text)
    if n == 1:
        return [ws, we]
    seg = prof[ws:we].astype(float)
    L = len(seg)
    p30 = np.percentile(seg, 30)
    cands = [x for x in range(3, L - 3)
             if (seg[x] <= seg[x - 1] and seg[x] <= seg[x + 1] and seg[x] <= np.percentile(seg, 60))
             or seg[x] <= p30]
    # thin out consecutive equal-valued candidates
    thinned = []
    for x in cands:
        if not thinned or x - thinned[-1] > 2:
            thinned.append(x)
    cands = thinned
    if len(cands) < n - 1:
        # fall back to proportional cuts
        acc = np.cumsum([wexp.get(ch, wexp["_"]) for ch in text])
        cuts = [ws] + [ws + int(round(L * a / acc[-1])) for a in acc[:-1]] + [we]
        return cuts
    INF = 1e18
    # dp[i][c] = best cost placing cut for letter boundary i at candidate c
    exp_w = [wexp.get(ch, wexp["_"]) for ch in text]
    prev = {0: (0.0, None)}   # position -> (cost, back) ; position 0 = ws
    layers = [prev]
    for i in range(1, n):
        cur = {}
        for c in cands:
            best = (INF, None)
            for pos, (cost, _) in layers[-1].items():
                if c <= pos + 4:
                    continue
                w = c - pos
                nc = cost + alpha * seg[c] + beta * (w - exp_w[i - 1]) ** 2
                if nc < best[0]:
                    best = (nc, pos)
            if best[1] is not None:
                cur[c] = best
        if not cur:
            acc = np.cumsum(exp_w)
            return [ws] + [ws + int(round(L * a / acc[-1])) for a in acc[:-1]] + [we]
        layers.append(cur)
    # close with the last letter to the word end
    best = (INF, None)
    for pos, (cost, _) in layers[-1].items():
        w = L - pos
        nc = cost + beta * (w - exp_w[-1]) ** 2
        if nc < best[0]:
            best = (nc, pos)
    if best[1] is None:
        acc = np.cumsum(exp_w)
        return [ws] + [ws + int(round(L * a / acc[-1])) for a in acc[:-1]] + [we]
    cuts = [L]
    pos = best[1]
    for i in range(n - 1, 0, -1):
        cuts.append(pos)
        pos = layers[i][pos][1]
    cuts.append(0)
    cuts.reverse()
    return [ws + c for c in cuts]


def measure_page(page, scale=2, verbose=True, debug_line=None, wexp=None):
    im, g, ink = page_ink(page, scale)
    x0, x1 = text_column(ink, scale)
    lines = find_lines(ink, x0, x1, scale)
    tl = transcript_lines(page)
    if verbose:
        sys.stderr.write(f"page {page}: column x={x0}..{x1}, {len(lines)} image lines, {len(tl)} transcript lines\n")
    wexp = dict(wexp or {})
    wexp.setdefault("_", 16.5 * scale)
    w_avg = wexp["_"]
    rows, line_info = [], []
    ti = 0
    gap_thr = 7 * scale
    for li, (ys, ye) in enumerate(lines):
        if ti >= len(tl):
            break
        band = ink[ys:ye, x0:x1]
        prof = band.sum(axis=0)
        edt = ndimage.distance_transform_edt(np.pad(band, 1))[1:-1, 1:-1]
        words_px = line_runs(prof, gap_thr)
        words_px = [w for w in words_px if w[1] - w[0] >= 4 * scale]
        if not words_px:
            continue
        runs = [list(range(int(round((e - s) / w_avg)) or 1)) for s, e in words_px]
        best = None
        for look in range(0, 3):
            if ti + look >= len(tl):
                break
            words = tl[ti + look].split()
            m, c = dp_align(runs, words)
            norm = c / max(1, sum(len(w) for w in words))
            if best is None or norm < best[2] - 0.15:
                best = (look, m, norm, words)
            if norm < 0.12:
                break
        look, matches, norm, words = best
        if norm > 0.6:
            line_info.append((li, ti, f"REJECT norm={norm:.2f} runs={[len(r) for r in runs]} words={[len(w) for w in words]}"))
            continue
        ti += look
        nseg = 0
        dbg = None
        if debug_line == ti + 1:
            dbg = im.convert("RGB").crop((x0, ys - 5, x1, ye + 5))
            d = ImageDraw.Draw(dbg)
        for ris, wis in matches:
            if len(ris) != 1 or len(wis) != 1:
                continue      # only clean one-run-one-word matches are measured
            ws, we = words_px[ris[0]]
            text = words[wis[0]]
            cuts = split_word(prof, ws, we, text, wexp)
            for k, ch in enumerate(text):
                a, b = cuts[k], cuts[k + 1]
                if b <= a:
                    continue
                cell = band[:, a:b]
                area = int(cell.sum())
                if area == 0:
                    continue
                ev = edt[:, a:b][cell]
                sw = float(2.0 * ev.mean())
                sw90 = float(2.0 * np.percentile(ev, 90))
                emax = float(2.0 * ev.max())
                rows.append(dict(page=page, line=ti + 1, cell=a, char=ch, area=area, sw=sw,
                                 sw90=sw90, emax=emax, width=b - a, x=x0 + a, y=ys, wlen=len(text)))
                nseg += 1
                if dbg is not None:
                    d.line([(a, 0), (a, dbg.height)], fill=(255, 0, 0), width=1)
                    d.text((a + 2, dbg.height - 12), ch, fill=(0, 0, 255))
        if dbg is not None:
            dbg.save(f"/tmp/dbg_p{page}_l{ti+1}.png")
            sys.stderr.write(f"debug image /tmp/dbg_p{page}_l{ti+1}.png\n")
        line_info.append((li, ti, f"ok norm={norm:.2f} glyphs={nseg}/{sum(len(w) for w in words)}"))
        ti += 1
    if verbose:
        for li, t, s in line_info:
            sys.stderr.write(f"  img {li:3d} -> tr {t+1:3d}: {s}\n")
    return rows, tl


def learn_widths(rows):
    by = {}
    for r in rows:
        by.setdefault(r["char"], []).append(r["width"])
    return {ch: float(np.median(v)) for ch, v in by.items() if len(v) >= 3}


def two_cluster(v):
    """1-D 2-means on log values; returns (lo_centre, hi_centre, labels)."""
    x = np.log(np.maximum(v, 1e-6))
    lo, hi = np.percentile(x, 20), np.percentile(x, 80)
    if hi - lo < 1e-6:
        return float(np.exp(lo)), float(np.exp(hi)), np.zeros(len(x), int)
    for _ in range(25):
        lab = (np.abs(x - hi) < np.abs(x - lo)).astype(int)
        if lab.sum() == 0 or lab.sum() == len(x):
            break
        lo, hi = x[lab == 0].mean(), x[lab == 1].mean()
    return float(np.exp(lo)), float(np.exp(hi)), lab


def score(rows):
    by = {}
    for r in rows:
        by.setdefault(r["char"], []).append(r)
    for ch, rs in by.items():
        areas = np.array([r["area"] for r in rs], dtype=float)
        sws = np.array([r["sw90"] for r in rs], dtype=float)
        if len(rs) >= 6:
            a_lo, a_hi, _ = two_cluster(areas)
            s_lo, s_hi, _ = two_cluster(sws)
        else:
            a_lo = a_hi = np.median(areas); s_lo = s_hi = np.median(sws)
        for r in rs:
            r["area_ratio"] = r["area"] / a_lo if a_lo > 0 else 1.0
            r["sw_ratio"] = r["sw90"] / s_lo if s_lo > 0 else 1.0
            r["n_same"] = len(rs)
            r["a_sep"] = a_hi / a_lo if a_lo > 0 else 1.0
            r["s_sep"] = s_hi / s_lo if s_lo > 0 else 1.0
            # nearest-cluster call on stroke width (log space); fall back to a
            # fixed ratio when the letter has no real second cluster
            if len(rs) >= 6 and s_hi / s_lo >= 1.12:
                d_lo = abs(np.log(r["sw90"]) - np.log(s_lo))
                d_hi = abs(np.log(r["sw90"]) - np.log(s_hi))
                r["bold"] = int(d_hi < d_lo)
            else:
                r["bold"] = int(r["sw_ratio"] >= 1.25)
    return rows


def markup(rows, tl, cutoff, key="area_ratio"):
    out = []
    for i, line in enumerate(tl, start=1):
        rs = {r["cell"]: r for r in rows if r["line"] == i}
        if not rs:
            out.append("(no glyphs) " + line)
            continue
        ks = sorted(rs)
        txt, prev = [], None
        for k in ks:
            r = rs[k]
            if prev is not None and k - prev > 1.6 * prev_w:
                txt.append(" ")
            b = (r["bold"] == 1) if key == "bold" else (r[key] >= cutoff)
            txt.append(r["char"].upper() if b else r["char"].lower())
            prev, prev_w = k, r["width"]
        out.append("".join(txt))
    return out


def write_rows(rows, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("page\tline\tcell\tchar\tarea\tsw\tsw90\temax\twidth\tarea_ratio\tsw_ratio\tbold\tn_same\tx\ty\n")
        for r in sorted(rows, key=lambda r: (r["line"], r["cell"])):
            f.write(f"{r['page']}\t{r['line']}\t{r['cell']}\t{r['char']}\t{r['area']}\t{r['sw']:.2f}\t{r['sw90']:.2f}\t{r['emax']:.2f}\t{r['width']}\t{r['area_ratio']:.3f}\t{r['sw_ratio']:.3f}\t{r['bold']}\t{r['n_same']}\t{r['x']}\t{r['y']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--cutoff", type=float, default=1.3)
    ap.add_argument("--sw-cutoff", type=float, default=1.25)
    ap.add_argument("--debug-line", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows, tl = measure_page(a.page, a.scale, verbose=False)
    wexp = learn_widths(rows)
    wexp["_"] = float(np.median([r["width"] for r in rows]))
    rows, tl = measure_page(a.page, a.scale, debug_line=a.debug_line, wexp=wexp)
    rows = score(rows)
    out = a.out or os.path.join(ROOT, "solver", "wf", f"glyphs_p{a.page}.tsv")
    write_rows(rows, out)
    sys.stderr.write(f"wrote {len(rows)} glyph rows to {out}\n")
    ratios = np.array([r["area_ratio"] for r in rows if r["char"].isalpha()])
    h, e = np.histogram(ratios, bins=np.arange(0.5, 2.55, 0.1))
    sys.stderr.write("area_ratio histogram (letters):\n")
    for k in range(len(h)):
        sys.stderr.write(f"  {e[k]:.1f}-{e[k+1]:.1f} {'#' * int(60 * h[k] / max(h.max(), 1))} {h[k]}\n")
    print("--- area_ratio markup ---")
    for line in markup(rows, tl, a.cutoff):
        print(line)
    print("--- cluster call markup ---")
    for line in markup(rows, tl, 0, key="bold"):
        print(line)


if __name__ == "__main__":
    main()
