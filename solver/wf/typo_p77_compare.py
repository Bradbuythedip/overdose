"""Sub-pixel stroke measure + same-letter comparison sheets for page 77.

width = (grayscale ink area) / (medial-axis length) per ink run, which resolves
sub-pixel weight differences the integer DT metric cannot.  White-bar rows are
restricted to the bar so bar text segments per glyph.  Run from solver/.
"""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, maximum_filter, binary_opening
sys.path.insert(0, '/home/user/overdose/solver/wf')
from typo_p77_measure import im, rgb, L, ROWS, runs_from
from typo_p77_table import TEXT

OUT = '/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p77/'

def masks(y0, y1, x0, x1):
    """Return (binary ink mask, ink-fraction image) with per-column background class."""
    sub = rgb[y0:y1, x0:x1]; l = L[y0:y1, x0:x1]
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    medL = np.median(l, axis=0); medB = np.median(B, axis=0); medR = np.median(R, axis=0)
    mask = np.zeros_like(l, dtype=bool); frac = np.zeros_like(l)
    white = (medL > 190) & (medB > 150)
    orange = (medR > 170) & (medB < 120) & ~white
    dark = ~white & ~orange
    # dark ground: light text
    if dark.any():
        col = l[:, dark]
        bg = np.percentile(col, 20); fg = np.percentile(col, 99)
        mask[:, dark] = col > 150
        frac[:, dark] = np.clip((col - bg) / (fg - bg), 0, 1)
    if white.any():
        col = l[:, white]
        rowmed = np.median(col, axis=1)            # rows inside the bar are bright
        inbar = rowmed > 150
        m = (col < 120) & inbar[:, None]
        bg = np.percentile(col[inbar], 80); fg = np.percentile(col[inbar], 1)
        f = np.clip((bg - col) / (bg - fg), 0, 1) * inbar[:, None]
        mask[:, white] = m; frac[:, white] = f
    if orange.any():
        colB = B[:, orange]
        rowmed = np.median(colB, axis=1)
        inbar = rowmed < 150                       # orange rows have low blue
        m = (colB > 150) & inbar[:, None]
        bg = np.percentile(colB[inbar], 20); fg = np.percentile(colB[inbar], 99)
        f = np.clip((colB - bg) / (fg - bg), 0, 1) * inbar[:, None]
        # outside bar rows text is white-on-dark anyway; keep simple
        mask[:, orange] = m; frac[:, orange] = f
    mask = binary_opening(mask, structure=np.ones((2, 2)))
    frac = frac * (frac > 0.15)
    return mask, frac

def measure(i, xa=None, xb=None):
    y0, y1 = ROWS[i-1]; y0 -= 6; y1 += 6
    xmin = xa if xa else (240 if i <= 7 else 580); xmax = xb if xb else 1645
    m, f = masks(y0, y1, xmin, xmax)
    dt = distance_transform_edt(m)
    ridge = (dt >= maximum_filter(dt, size=3)) & (dt >= 1.0)
    rows = []
    for a, b in runs_from(m):
        rl = int(ridge[:, a:b].sum()); area = float(f[:, a:b].sum()); barea = int(m[:, a:b].sum())
        if rl < 3: continue
        rows.append(dict(x0=xmin+a, x1=xmin+b, w=b-a, area=area, ridge=rl, width=area/rl,
                         dtmax=2*float(dt[:, a:b].max()), bin=barea))
    return rows, (y0, y1)

def sheet(name, items, Z=8):
    """items: (label, line, xa, xb). Renders crops at Z with width labels per run."""
    panels = []
    for label, i, xa, xb in items:
        rows, (y0, y1) = measure(i, xa, xb)
        c = im.crop((xa, y0, xb, y1)).resize(((xb-xa)*Z, (y1-y0)*Z), Image.LANCZOS)
        p = Image.new('RGB', (c.width, c.height + 34), (35, 35, 35)); p.paste(c, (0, 34))
        d = ImageDraw.Draw(p); d.text((2, 2), label, fill=(255, 255, 0))
        for r in rows:
            wv = r['width']
            col = (255, 90, 90) if wv >= 5.4 else ((255, 210, 80) if wv >= 4.9 else (140, 210, 255))
            d.text(((r['x0']-xa)*Z + 1, 18), '%.1f' % wv, fill=col)
            d.line([((r['x0']-xa)*Z, 32), ((r['x1']-xa)*Z - 1, 32)], fill=col, width=2)
        panels.append(p)
    W = min(2000, max(p.width for p in panels)); H = sum(p.height for p in panels) + 8*len(panels)
    s = Image.new('RGB', (W, H), (20, 20, 20)); y = 0
    for p in panels:
        if p.width > W: p = p.resize((W, int(p.height*W/p.width)), Image.LANCZOS)
        s.paste(p, (0, y)); y += p.height + 8
    fn = OUT + name + '.png'; s.save(fn); print(fn, s.size)

if __name__ == '__main__':
    if sys.argv[1:] and sys.argv[1] == 'table':
        for arg in sys.argv[2:]:
            i = int(arg); rows, _ = measure(i)
            print('== LINE %d: %s  (%d runs / %d chars)' % (i, TEXT[i], len(rows), len(TEXT[i].replace(' ', ''))))
            print('    x0   x1  w   width  area ridge dtmax')
            for r in rows:
                flag = ' <<' if r['width'] >= 5.4 else (' <' if r['width'] >= 4.9 else '')
                print('  %4d %4d %2d   %4.2f  %5.0f %4d  %4.1f%s' % (r['x0'], r['x1'], r['w'], r['width'], r['area'], r['ridge'], r['dtmax'], flag))
        sys.exit()
    sheet('c_1', [
        ('L3 Mallers', 3, 340, 520), ('L10 downhill (ref)', 10, 1250, 1425), ('L4 whole (ref)', 4, 1360, 1465),
        ('L8 Roger Ver', 8, 1300, 1495), ('L6 over? no: L10 ever since (ref)', 10, 1425, 1610),
        ('L9 Block', 9, 1440, 1626), ('L9 blockers (ref)', 9, 685, 910),
    ])
    sheet('c_2', [
        ('L10 Size War', 10, 620, 790), ('L3 Strike (ref)', 3, 505, 630), ('L10 since. (ref)', 10, 1510, 1612),
        ('L13 Peter McCormack', 13, 695, 1005), ('L11 Particularly (ref)', 11, 618, 850), ('L16 scammer (ref)', 16, 1140, 1300),
    ])
    sheet('c_3', [
        ('L16 paradise. Full Stop.', 16, 1200, 1622),
        ('L11 Faketoshi', 11, 900, 1130), ('L14 shitcoiners,', 14, 1370, 1626), ('L15 useless Royals,', 15, 736, 1060),
        ('L7 shitcoin hell. (ref)', 7, 1050, 1330), ('L6 Sorry Bhutan (ref)', 6, 250, 620),
    ])
    sheet('c_4', [
        ('L25 Shitcoins, fiat', 25, 890, 1240), ('L28 shitcoins, fiat (ref)', 28, 1010, 1290),
        ('L25 and gold will', 25, 1270, 1612), ('L28 and gold to death (ref)', 28, 1275, 1612),
        ('L26 starve to death as', 26, 595, 1040),
    ])
    sheet('c_5', [
        ('L26 the result of Bitcoins', 26, 1060, 1612),
        ('L27 insatiable conquest', 27, 595, 1035), ('L27 of all available energy.', 27, 1050, 1612),
        ('L22 mathematical (ref)', 22, 1000, 1330), ('L25 energy supply. (ref)', 25, 595, 870),
    ])
    sheet('c_6', [
        ('L5 Toxic Bitcoin Maximalists', 5, 540, 1060), ('L5 within six months.', 5, 1050, 1420),
        ('L12 harass old women and children', 12, 1115, 1626),
        ('L30 It does this by monetizing,', 30, 1140, 1500),
        ('L18 THE BITCOIN WANNABES', 18, 625, 1000), ('L7 at XRP. (ref)', 7, 255, 480),
    ])
