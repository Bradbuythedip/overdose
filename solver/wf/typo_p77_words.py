"""6x word crops with ridge-based stroke width per ink run, page 77 (IMG_6248).

Stroke width per run = 2 * mean(DT) over medial-axis pixels (local maxima of the
distance transform), which is far less sensitive to serifs and letter joins than the
column-max used in typo_p77_measure.py.  Run from solver/.
"""
from PIL import Image, ImageDraw
import numpy as np, sys
from scipy.ndimage import distance_transform_edt, binary_opening, maximum_filter
sys.path.insert(0, '/home/user/overdose/solver/wf')
from typo_p77_measure import ink_mask, runs_from, im, ROWS

OUT = '/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p77/'

def ridge_width(mask):
    dt = distance_transform_edt(mask)
    ridge = (dt >= maximum_filter(dt, size=3)) & (dt >= 1.5)
    return dt, ridge

def crop_panel(label, line, xa, xb, Z=6):
    y0, y1 = ROWS[line-1]; y0 -= 6; y1 += 6
    m = ink_mask(y0, y1, xa, xb)
    dt, ridge = ridge_width(m)
    runs = runs_from(m)
    c = im.crop((xa, y0, xb, y1)).resize(((xb-xa)*Z, (y1-y0)*Z), Image.LANCZOS)
    panel = Image.new('RGB', (c.width, c.height + 30), (40, 40, 40))
    panel.paste(c, (0, 30)); d = ImageDraw.Draw(panel)
    d.text((2, 2), label, fill=(255, 255, 0))
    for (a, b) in runs:
        r = ridge[:, a:b]; v = dt[:, a:b][r]
        if v.size < 4: continue
        w = 2 * float(np.mean(v))
        col = (255, 90, 90) if w >= 4.9 else ((255, 210, 80) if w >= 4.4 else (140, 210, 255))
        d.text((a*Z + 1, 16), '%.1f' % w, fill=col)
        d.line([(a*Z, 28), (b*Z - 1, 28)], fill=col, width=2)
    return panel

def sheet(name, items, maxw=2000):
    panels = [crop_panel(*it) for it in items]
    W = min(maxw, max(p.width for p in panels)); H = sum(min(p.height, 400) for p in panels) + 10*len(panels)
    s = Image.new('RGB', (W, H), (25, 25, 25)); y = 0
    for p in panels:
        if p.width > W: p = p.resize((W, int(p.height*W/p.width)), Image.LANCZOS)
        s.paste(p, (0, y)); y += p.height + 10
    fn = OUT + name + '.png'; s.save(fn); print(fn, s.size)

if __name__ == '__main__':
    sheet('w_A', [
        ('L3 Jack Mallers Strike', 3, 250, 640),
        ('L8 from Roger Ver lately', 8, 1230, 1626),
        ('L9 the Block', 9, 1420, 1626),
        ('L10 Size War of 2017', 10, 615, 950),
    ])
    sheet('w_B', [
        ('L11 for Faketoshi and', 11, 880, 1200),
        ('L13 (and Peter McCormack)', 13, 605, 1020),
        ('L16 paradise. Full Stop.', 16, 1200, 1622),
        ('L24 be a 51% attack', 24, 1000, 1330),
    ])
    sheet('w_C', [
        ('L25a energy supply. Shitcoins,', 25, 590, 1080),
        ('L25b fiat and gold will', 25, 1060, 1615),
        ('L26a starve to death as', 26, 590, 1080),
        ('L26b the result of Bitcoin s', 26, 1060, 1615),
    ])
    sheet('w_D', [
        ('L27a insatiable conquest', 27, 590, 1060),
        ('L27b of all available energy.', 27, 1040, 1615),
        ('L28 starves shitcoins, fiat', 28, 900, 1300),
        ('L4 REGULAR REF: a day to a mind-bending', 4, 250, 640),
    ])
    sheet('w_E', [
        ('L5 orange bar', 5, 540, 1000),
        ('L5 orange bar (cont)', 5, 980, 1420),
        ('L12 orange bar', 12, 1110, 1626),
        ('L7 white bar REGULAR REF: shitcoin hell.', 7, 1040, 1330),
    ])
    sheet('w_F', [
        ('L14 shitcoiners,', 14, 1370, 1626),
        ('L15 useless Royals, career', 15, 736, 1200),
        ('L30a itself. It does this by', 30, 1000, 1400),
        ('L30b monetizing, for the', 30, 1380, 1615),
    ])
    sheet('w_G', [
        ('L18 THE BITCOIN WANNABES', 18, 625, 1000),
        ('L21 VERSUS BITCOIN.', 21, 1250, 1570),
        ('L7 at XRP. (regular caps ref)', 7, 250, 480),
        ('L6 (Sorry Bhutan, you fell', 6, 250, 700),
        ('L22 It s a guaranteed, (regular ref)', 22, 590, 1000),
    ])
