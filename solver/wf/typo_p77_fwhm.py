"""Sub-pixel stem width (FWHM of the grayscale profile) for chosen glyphs, page 77.

For a glyph box (line, x0, x1) take rows in the middle of the x-height, normalise the
row profile between line background and foreground, and measure the width of every
segment above 0.5 with linear interpolation at the crossings.  Reports the median of
the widest segment per row (the main stem) and the median of all segments.
Run from solver/.
"""
import sys, numpy as np
sys.path.insert(0, '/home/user/overdose/solver/wf')
from typo_p77_measure import L, rgb, ROWS

def fwhm(i, x0, x1, invert=None, band=(0.42, 0.66)):
    y0, y1 = ROWS[i-1]
    H = y1 - y0
    r0, r1 = y0 + int(H*band[0]), y0 + int(H*band[1])
    sub = L[r0:r1, x0-2:x1+2].astype(float)
    if invert is None:
        invert = np.median(L[y0:y1, x0-2:x1+2]) > 150      # white bar -> dark text
    if invert:
        sub = 255 - sub
    bg = np.percentile(L[y0:y1, x0-2:x1+2] if not invert else 255-L[y0:y1, x0-2:x1+2], 15)
    fg = np.percentile(L[y0:y1, x0-2:x1+2] if not invert else 255-L[y0:y1, x0-2:x1+2], 99)
    widest, allw = [], []
    for row in sub:
        p = np.clip((row - bg) / (fg - bg), 0, 1)
        above = p >= 0.5
        segs = []
        x = 0
        while x < len(p):
            if above[x]:
                s = x
                while x < len(p) and above[x]: x += 1
                e = x - 1
                # sub-pixel crossings
                left = s - (p[s]-0.5)/(p[s]-p[s-1]) if s > 0 and p[s] != p[s-1] else s
                right = e + (p[e]-0.5)/(p[e]-p[e+1]) if e < len(p)-1 and p[e] != p[e+1] else e
                segs.append(right - left + 1 - 1)  # width between half-max crossings
            x += 1
        if segs:
            widest.append(max(segs)); allw.extend(segs)
    return (np.median(widest) if widest else float('nan'), np.median(allw) if allw else float('nan'), len(widest))

GLYPHS = [
 # label, line, x0, x1
 ('l  Mallers l1', 3, 396, 414), ('l  Mallers l2', 3, 415, 433),
 ('l  downhill l1 REF', 10, 1367, 1382), ('l  downhill l2 REF', 10, 1383, 1400), ('l  downhill l3 REF', 10, 1401, 1419),
 ('l  whole REF', 4, 1427, 1444), ('l  legal(14) REF', 14, 671, 691),
 ('l  will(25) l1', 25, 1566, 1585), ('l  will(25) l2', 25, 1589, 1608),
 ('l  gold(25)', 25, 1431, 1450), ('l  gold(28) REF', 28, 1397, 1413),
 ('l  all(27) l1', 27, 1151, 1169), ('l  all(27) l2', 27, 1174, 1192),
 ('l  available l1', 27, 1314, 1332), ('l  available l2', 27, 1384, 1402),
 ('l  result(26)', 26, 1269, 1287), ('l  Block', 9, 1543, 1563), ('l  blockers REF', 9, 691, 712),
 ('l  Full l1 (large)', 16, 1406, 1433), ('l  Full l2 (large)', 16, 1434, 1461),
 ('i  Size', 10, 649, 666), ('i  since REF', 10, 1535, 1550), ('i  this(23) REF', 23, 0, 0),
 ('i  Shitcoins i1', 25, 951, 967), ('i  Shitcoins i2', 25, 1034, 1051), ('i  fiat(25)', 25, 1176, 1193),
 ('i  will(25)', 25, 1544, 1562), ('i  fiat(28) REF', 28, 1303, 1312),
 ('i  shitcoins(28) i2', 28, 1126, 1142), ('i  Bitcoins(26) i1', 26, 1445, 1462), ('i  Bitcoins(26) i2', 26, 1530, 1546),
 ('i  insatiable i1', 27, 599, 616), ('i  insatiable i2', 27, 711, 728), ('i  available i', 27, 1293, 1309),
 ('i  Strike REF', 3, 569, 582), ('i  Mallers? no: sign REF', 3, 1172, 1186),
 ('h  Shitcoins(25)', 25, 923, 946), ('h  shitcoins(28) REF', 28, 1033, 1056), ('h  the(26)', 26, 1092, 1114),
 ('h  death(26)', 26, 941, 957), ('h  death(28) REF', 28, 1536, 1571), ('h  whole REF', 4, 1409, 1427),
 ('d  and(25)', 25, 1325, 1346), ('d  gold(25)', 25, 1453, 1474), ('d  death(26)', 26, 867, 885),
 ('d  and(28) REF', 28, 1325, 1343), ('d  gold(28) REF', 28, 1413, 1432), ('d  death(28) REF', 28, 1497, 1516),
 ('B  Block', 9, 1519, 1543), ('B  Bitcoins(26)', 26, 1417, 1441), ('B  Bitcoin(5 orange)', 5, 686, 712),
 ('S  Size', 10, 629, 647), ('S  Strike REF', 3, 511, 530), ('S  Shitcoins(25)', 25, 899, 917), ('S  Stop(16 large)', 16, 1480, 1511),
 ('P  Peter', 13, 700, 721), ('P  Particularly REF', 11, 624, 644),
 ('g  Roger', 8, 1354, 1373), ('g  got(9) REF', 9, 853, 873), ('g  gold(25)', 25, 1386, 1406), ('g  gold(28) REF', 28, 1359, 1378), ('g  energy(27)', 27, 1548, 1567),
 ('m  McCormack', 13, 908, 932), ('m  scammer m1 REF', 16, 1074, 1097), ('m  scammer m2 REF', 16, 1098, 1115),
 ('a  McCormack', 13, 933, 953), ('a  scammer REF', 16, 1057, 1072), ('a  fiat(25)', 25, 1198, 1217), ('a  and(25)', 25, 1276, 1296),
 ('a  all(27)', 27, 1126, 1145), ('a  fiat(28) REF', 28, 1314, 1343),
 ('f  fiat(25)', 25, 1152, 1173), ('f  fiat(28) REF', 28, 1282, 1302), ('f  of(27)', 27, 1078, 1098), ('f  of(26) REF', 26, 1371, 1383),
 ('o  gold(25)', 25, 1410, 1427), ('o  gold(28) REF', 28, 1379, 1396), ('o  to(26)', 26, 790, 807),
 ('n  and(25) n', 25, 1301, 1320), ('n  and(28) REF', 28, 1303, 1323),
 ('t  fiat(25)', 25, 1220, 1236), ('t  fiat(28) REF', 28, 1325, 1343), ('t  Shitcoins(25)', 25, 970, 985), ('t  result(26)', 26, 1296, 1305),
 ('s  Shitcoins(25) s', 25, 1081, 1097), ('s  starve s', 26, 600, 617), ('s  as(26)', 26, 1018, 1034), ('s  conquest s', 27, 990, 1007), ('s  Bitcoins s', 26, 1589, 1606), ('s  result s', 26, 1099, 1114),
 ('c  Shitcoins c', 25, 990, 1006), ('c  conquest c', 27, 848, 864), ('c  Bitcoins c', 26, 1485, 1501),
 ('W  War', 10, 716, 742), ('F  Full (large)', 16, 1334, 1360), ('u  Full (large)', 16, 1381, 1404), ('t  Stop (large)', 16, 1514, 1538), ('o  Stop (large)', 16, 1540, 1565), ('p  Stop (large)', 16, 1565, 1596),
 ('d  paradise REF', 16, 1204, 1224), ('s  paradise REF', 16, 1246, 1260),
]

if __name__ == '__main__':
    # locate a regular 'i' in "this" line 23 quickly: use runs from table module
    from typo_p77_table import table
    t23 = table(23)
    # 'this' is the 3rd word: w h y , a n d t h i s ... pick run with width ~7-13 after 'th'
    for label, i, x0, x1 in GLYPHS:
        if x0 == 0: continue
        stem, allm, n = fwhm(i, x0, x1)
        print('%-26s  stem %.2f  all %.2f  (rows %d)' % (label, stem, allm, n))

def line_runs(i):
    """FWHM per ink run for a whole line (runs from typo_p77_table.table)."""
    from typo_p77_table import table
    out = []
    for x0, x1, w, midv, mx, mn in table(i):
        stem, allm, n = fwhm(i, x0, x1)
        out.append((x0, x1, w, stem, allm, midv, mx))
    return out

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'lines':
    import numpy as np
    from typo_p77_table import TEXT
    for arg in sys.argv[2:]:
        i = int(arg)
        rows = line_runs(i)
        print('== LINE %d: %s' % (i, TEXT[i]))
        print('    x0   x1  w   stem  all   mid  max')
        for x0, x1, w, stem, allm, midv, mx in rows:
            flag = ' <<' if (allm == allm and allm >= 4.2) or (stem == stem and stem >= 4.4 and w <= 12) else ''
            print('  %4d %4d %2d   %4.2f %4.2f  %4.1f %4.1f%s' % (x0, x1, w, stem, allm, midv, mx, flag))
        vals = [a for *_, s, a, m, x in rows if a == a]
        print('   all-median distribution: p50 %.2f p90 %.2f max %.2f' % (np.percentile(vals, 50), np.percentile(vals, 90), max(vals)))
