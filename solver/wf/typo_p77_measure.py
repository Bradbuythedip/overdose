"""Per-glyph stroke-width measurement for page 77 (IMG_6248) of Keiser's OVERDOSE.

Produces annotated 4x line crops with a stroke-width value over every ink run so that
letter-level bold can be judged against the image.  Run from solver/.
"""
from PIL import Image, ImageDraw
import numpy as np, math, json, sys
from scipy.ndimage import distance_transform_edt, binary_opening

PAGE = '/home/user/overdose/IMG_6248.jpeg'
OUT = '/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p77/'
ROWS = [(287,318),(342,373),(395,429),(451,483),(504,542),(558,596),(612,650),(709,740),(761,794),
        (816,841),(868,903),(919,955),(973,997),(1025,1060),(1076,1110),(1123,1162),(1270,1299),
        (1323,1358),(1377,1409),(1430,1462),(1483,1515),(1629,1659),(1683,1716),(1735,1765),
        (1788,1818),(1842,1870),(1893,1925),(1948,1980),(2001,2033),(2055,2094),(2110,2141),(2164,2190)]

im = Image.open(PAGE).convert('RGB')
rgb = np.asarray(im).astype(float)
L = np.asarray(im.convert('L')).astype(float)

def ink_mask(y0, y1, x0, x1):
    """Ink mask for a line crop, classifying background per column."""
    sub = rgb[y0:y1, x0:x1]
    l = L[y0:y1, x0:x1]
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    medL = np.median(l, axis=0)
    medB = np.median(B, axis=0)
    medR = np.median(R, axis=0)
    mask = np.zeros_like(l, dtype=bool)
    for x in range(l.shape[1]):
        if medL[x] > 190 and medB[x] > 150:          # white bar: dark text
            mask[:, x] = l[:, x] < 120
        elif medR[x] > 170 and medB[x] < 120:        # orange bar: white text
            mask[:, x] = B[:, x] > 150
        else:                                        # dark ground: light text
            mask[:, x] = l[:, x] > 150
    mask = binary_opening(mask, structure=np.ones((2, 2)))
    return mask

def runs_from(mask, min_gap=1):
    cols = mask.sum(axis=0) > 0
    runs = []; inrun = False
    for x, v in enumerate(cols):
        if v and not inrun: s = x; inrun = True
        elif not v and inrun: inrun = False; runs.append((s, x))
    if inrun: runs.append((s, len(cols)))
    return runs

def measure_line(i):
    y0, y1 = ROWS[i-1]
    xmin = 240 if i <= 7 else 580
    xmax = 1645
    y0 -= 6; y1 += 6
    m = ink_mask(y0, y1, xmin, xmax)
    cols = np.where(m.sum(axis=0) > 0)[0]
    x0 = max(xmin, xmin + int(cols.min()) - 6); x1 = min(xmax, xmin + int(cols.max()) + 6)
    m = ink_mask(y0, y1, x0, x1)
    dt = distance_transform_edt(m)
    colmax = dt.max(axis=0)            # half stroke width of the thickest stroke in each column
    runs = runs_from(m)
    vals = []
    for (a, b) in runs:
        seg = colmax[a:b]
        seg = seg[seg > 0]
        if len(seg) == 0: continue
        w = 2 * np.percentile(seg, 85)  # near-max full stroke width in the glyph
        vals.append((a + x0, b + x0, float(w), int(m[:, a:b].sum())))
    return (y0, y1, x0, x1), runs, vals, colmax

def render_pair(a, b, Z=4, SEGW=440, OV=24):
    panels = []
    for i in (a, b):
        (y0, y1, x0, x1), runs, vals, colmax = measure_line(i)
        w = x1 - x0; n = max(1, math.ceil(w / SEGW)); sw = math.ceil(w / n)
        segs = []
        for k in range(n):
            sx0 = max(x0, x0 + k * sw - OV); sx1 = min(x1, x0 + (k + 1) * sw + OV)
            c = im.crop((sx0, y0, sx1, y1)).resize(((sx1 - sx0) * Z, (y1 - y0) * Z), Image.LANCZOS)
            canvas = Image.new('RGB', (c.width, c.height + 34), (40, 40, 40))
            canvas.paste(c, (0, 34))
            d = ImageDraw.Draw(canvas)
            # curve of stroke width (full width, px at 1x) in the header band
            for xx in range(sx0, sx1):
                v = colmax[xx - x0] * 2
                if v > 0:
                    h = int(min(30, v * 4))
                    col = (255, 80, 80) if v >= 4.6 else ((255, 200, 60) if v >= 4.0 else (120, 200, 255))
                    d.line([((xx - sx0) * Z, 32), ((xx - sx0) * Z, 32 - h)], fill=col, width=Z)
            for (ra, rb, wv, area) in vals:
                if ra >= sx0 and rb <= sx1 + 1:
                    d.text(((ra - sx0) * Z + 1, 0), '%.1f' % wv, fill=(255, 255, 255))
            segs.append(canvas)
        W = max(s.width for s in segs) + 16; H = sum(s.height for s in segs) + 8 * len(segs) + 30
        p = Image.new('RGB', (W, H), (60, 60, 60)); d = ImageDraw.Draw(p)
        d.text((8, 8), 'LINE %d (page y %d-%d x %d-%d)  values = full stroke width px @1x; bars: blue<4.0 yellow<4.6 red>=4.6' % (i, y0, y1, x0, x1), fill=(255, 255, 0))
        y = 30
        for s in segs:
            p.paste(s, (8, y)); y += s.height + 8
        panels.append(p)
    W = max(p.width for p in panels); H = sum(p.height for p in panels) + 20
    c = Image.new('RGB', (W, H), (30, 30, 30)); c.paste(panels[0], (0, 0)); c.paste(panels[1], (0, panels[0].height + 20))
    fn = OUT + 'sw_%02d_%02d.png' % (a, b); c.save(fn); return fn

if __name__ == '__main__':
    pairs = [(1,2),(3,4),(5,6),(7,8),(9,10),(11,12),(13,14),(15,16),(17,18),(19,20),(21,22),(23,24),(25,26),(27,28),(29,30),(31,32)]
    for a, b in pairs:
        print(render_pair(a, b))
    # dump raw run values for reference
    allv = {}
    for i in range(1, 33):
        (y0, y1, x0, x1), runs, vals, colmax = measure_line(i)
        allv[i] = [(int(a), int(b), round(w, 2), area) for a, b, w, area in vals]
    json.dump(allv, open(OUT + 'sw_runs.json', 'w'), indent=0)
