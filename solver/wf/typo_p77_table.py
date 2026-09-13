"""Per-run stroke width table for page 77 lines, for letter-level mapping.

For every ink run (column run) on a line prints x-range, run width, and two stroke
metrics: mid = 2*median(DT) over medial-axis pixels within the middle 40% of the line
height (stems only, excludes serifs and baseline joins); max = 2*max(DT) in the run.
Run from solver/:  python3 wf/typo_p77_table.py 3 8 9 ...
"""
import sys, numpy as np
from scipy.ndimage import distance_transform_edt, maximum_filter
sys.path.insert(0, '/home/user/overdose/solver/wf')
from typo_p77_measure import ink_mask, runs_from, ROWS

TEXT = {
 1:"Meanwhile, back in El Salvador, 42% of the country",
 2:"is now hyperbitcoinized (at the time of writing).",
 3:"Jack Mallers' Strike app has gone from 20,000 new sign-ups",
 4:"a day to a mind-bending 100,000 and growing. At this rate, the whole",
 5:"country will be Toxic Bitcoin Maximalists within six months.",
 6:"(Sorry Bhutan, you fell for that snake oil salesmen over",
 7:"at XRP. Get ready to experience shitcoin hell.",
 8:"Has anyone heard from Roger Ver lately?",
 9:"big blockers got their heads ripped off during the Block",
 10:"Size War of 2017 and it's been going downhill ever since.",
 11:"Particularly for Faketoshi and his army of high-priced",
 12:"London legal hacks who harass old women and children",
 13:"(and Peter McCormack) for no other reason than the U.K.'s",
 14:"legal system favors and protects demented shitcoiners,",
 15:"useless Royals, career criminals and banksters.",
 16:"London is a scammer paradise. Full Stop.",
 17:"EVERY SINGLE ONE OF",
 18:"THE BITCOIN WANNABES - BCH, BSV, ETH, XRP,",
 19:"ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT",
 20:"MONEY AND GOLD - IS FACING THE IGNOMINIOUS",
 21:"FATE OF DEMONETIZATION VERSUS BITCOIN.",
 22:"It's a guaranteed, mathematical certainty. Let me explain",
 23:"why, and this might be the first time you're hearing this,",
 24:"bitcoin was designed to be a 51% attack on the world's",
 25:"energy supply. Shitcoins, fiat and gold will",
 26:"starve to death as the result of Bitcoin's",
 27:"insatiable conquest of all available energy.",
 28:"And as bitcoin starves shitcoins, fiat and gold to death,",
 29:"it simultaneously demonetizes war, violence, hatred and",
 30:"the state itself. It does this by monetizing, for the first",
 31:"time in human history, peace, love and understanding",
 32:"(Elvis Costello was right).",
}

def table(i):
    y0, y1 = ROWS[i-1]; y0 -= 6; y1 += 6
    xmin = 240 if i <= 7 else 580; xmax = 1645
    m = ink_mask(y0, y1, xmin, xmax)
    dt = distance_transform_edt(m)
    ridge = (dt >= maximum_filter(dt, size=3)) & (dt >= 1.5)
    H = y1 - y0; r0, r1 = int(H*0.35), int(H*0.68)   # x-height band (line box includes 6px pads)
    runs = runs_from(m)
    out = []
    for a, b in runs:
        sub = dt[:, a:b]; rg = ridge[:, a:b]
        mid = sub[r0:r1][rg[r0:r1]]
        allr = sub[rg]
        if allr.size < 3: continue
        midv = 2*float(np.median(mid)) if mid.size >= 3 else float('nan')
        out.append((xmin+a, xmin+b, b-a, midv, 2*float(allr.max()), 2*float(np.mean(allr))))
    return out

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        i = int(arg); t = table(i)
        print('== LINE %d: %s   (%d runs, %d non-space chars)' % (i, TEXT[i], len(t), len(TEXT[i].replace(' ',''))))
        print('   x0    x1   w   mid   max  mean')
        for x0, x1, w, midv, mx, mn in t:
            flag = ' <<' if (midv == midv and midv >= 5.0) else ''
            print('  %4d %4d %3d  %4.1f  %4.1f  %4.1f%s' % (x0, x1, w, midv, mx, mn, flag))
