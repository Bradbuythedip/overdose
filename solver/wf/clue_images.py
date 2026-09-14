#!/usr/bin/env python3
"""
IMAGES lens -- embedded-image inventory and forensics for solver/scan/Scan1.pdf.

Every clue reported from this lens is produced by one of these subcommands.

  python3 wf/clue_images.py inventory   full 35-image table (xref, dims, bpc,
                                        cs, filter, bytes, dpi, ImageMask,
                                        Decode, SMask, Mask, rect)
  python3 wf/clue_images.py objects     xref-table census; orphans; duplicates
  python3 wf/clue_images.py fills       the 27 stencil ink colours, recovered
                                        from the content streams
  python3 wf/clue_images.py orange      colour-layer vs composite orange counts
  python3 wf/clue_images.py empty       painted-sample fraction per stencil
  python3 wf/clue_images.py filters     Flate-over-DCT double filter accounting
  python3 wf/clue_images.py jpeg        DQT / sampling / chroma-resolution
  python3 wf/clue_images.py canon       Canon content-stream markers + OCR layer
  python3 wf/clue_images.py grid        segmenter block grid (8 px x 4 px)
  python3 wf/clue_images.py ctm         placement matrices (flip/rotation test)
  python3 wf/clue_images.py x18         the two disjoint elements inside xref 18
  python3 wf/clue_images.py dump        write every stencil, un-rotated, to
                                        /tmp/imgs for eyeballing
"""
import hashlib, io, os, re, sys, collections
import numpy as np
import pymupdf
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "scan", "Scan1.pdf")
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}


def doc():
    return pymupdf.open(PDF)


def _stencil(d, xref):
    """Decoded stencil as a bool array: True == PAINTED.

    Polarity is verified in `empty()`: the LIGHT class of the extracted PNG is
    the class the /ImageMask paints with the current fill colour.
    """
    a = np.array(Image.open(io.BytesIO(d.extract_image(xref)["image"])).convert("L"))
    return a >= 128


# ---------------------------------------------------------------- inventory
def inventory():
    d = doc()
    print(f"{'pg':<4}{'xref':<6}{'WxH':<12}{'bpc':<5}{'colorspace':<11}"
          f"{'filter':<16}{'bytes':>8}  {'dpi':<12}{'ImgMask':<9}"
          f"{'Decode':<8}{'SMask':<7}{'Mask':<6}{'n':<3}rect")
    n = 0
    for i, pg in enumerate(d):
        for x in pg.get_images(full=True):
            xref, _, w, h, bpc, cs, _, _, filt = x[:9]
            r = pg.get_image_rects(xref)
            rr = r[0] if r else None
            k = lambda key: (d.xref_get_key(xref, key) or (None, "-"))[1]
            print(f"{PAGE_MAP[i]:<4}{xref:<6}{f'{w}x{h}':<12}{bpc:<5}{cs or '-':<11}"
                  f"{filt:<16}{len(d.xref_stream_raw(xref)):>8}  "
                  f"{f'{w/rr.width*72:.0f}x{h/rr.height*72:.0f}':<12}"
                  f"{k('ImageMask'):<9}{k('Decode'):<8}{k('SMask'):<7}"
                  f"{k('Mask'):<6}{len(r):<3}"
                  f"{[round(v,2) for v in (rr.x0,rr.y0,rr.x1,rr.y1)]}")
            n += 1
    print(f"\n{n} image placements")


def objects():
    d = doc()
    imgs = [x for x in range(1, d.xref_length())
            if (d.xref_get_key(x, "Subtype") or (None, None))[1] == "/Image"]
    placed, md5s = collections.Counter(), collections.Counter()
    for pg in d:
        for x in pg.get_images(full=True):
            placed[x[0]] += 1
            md5s[hashlib.md5(d.xref_stream_raw(x[0])).hexdigest()] += 1
    types = collections.Counter()
    for x in range(1, d.xref_length()):
        t = (d.xref_get_key(x, "Type") or (None, None))[1]
        s = (d.xref_get_key(x, "Subtype") or (None, None))[1]
        types[(t, s)] += 1
    print("xref table length          :", d.xref_length())
    print("object census              :", dict(types))
    print("/Image objects in the table:", len(imgs))
    print("placed on some page        :", len(placed))
    print("ORPHANS (never drawn)      :", sorted(set(imgs) - set(placed)))
    print("placed more than once      :", [x for x, c in placed.items() if c > 1])
    print("byte-identical streams     :", [m for m, c in md5s.items() if c > 1],
          f"({len(md5s)} distinct streams)")
    print("images carrying /SMask     :",
          [x for x in imgs if (d.xref_get_key(x, "SMask") or (None, "null"))[1] != "null"])
    print("images carrying /Mask      :",
          [x for x in imgs if (d.xref_get_key(x, "Mask") or (None, "null"))[1] != "null"])
    print("images carrying /Decode    :",
          [x for x in imgs if (d.xref_get_key(x, "Decode") or (None, "null"))[1] != "null"])


# ------------------------------------------------------------------- fills
def page_fills(pg):
    """(/ObjN, colourspace, rgb0-1) for every Do, in draw order."""
    toks = pg.read_contents().decode("latin-1").split()
    fill, space, out = None, None, []
    for j, t in enumerate(toks):
        if t == "rg":
            fill = tuple(float(v) for v in toks[j - 3:j]); space = "DeviceRGB"
        elif t == "g":
            v = float(toks[j - 1]); fill = (v, v, v); space = "DeviceGray"
        elif t == "Do":
            out.append((toks[j - 1], space, fill))
    return out


def fills():
    d = doc()
    print("Every bilevel region is an /ImageMask STENCIL. A stencil carries no")
    print("colour of its own: it is painted in the fill colour standing in the")
    print("content stream. That colour is the scanner's measurement of the ink.\n")
    print(f"{'pg':<4}{'xref':<6}{'space':<12}{'fill 0-1':<22}{'RGB 0-255':<18}R-G")
    rows = []
    for i, pg in enumerate(d):
        for name, space, f in page_fills(pg):
            x = int(re.sub(r"\D", "", name))
            if f is None:
                print(f"{PAGE_MAP[i]:<4}{x:<6}{'(none)':<12}"
                      f"{'-':<22}{'full-page colour layer':<18}")
                continue
            rgb = tuple(round(v * 255) for v in f)
            rows.append((PAGE_MAP[i], x, space, rgb))
            print(f"{PAGE_MAP[i]:<4}{x:<6}{space:<12}"
                  f"{','.join(f'{v:.3f}' for v in f):<22}{str(rgb):<18}"
                  f"{rgb[0]-rgb[1]:+d}")
    print(f"\n{len(rows)} stencils; pure black (0,0,0) used: "
          f"{sum(1 for r in rows if r[3]==(0,0,0))}")
    print("DeviceGray stencils:", [(r[0], r[1], r[3]) for r in rows if r[2] == "DeviceGray"])
    print("\nmain body-text masks (largest stencil on each page):")
    for r in rows:
        if r[1] in (5, 17, 35, 50, 60, 74):
            print(f"   p{r[0]} xref {r[1]:<3} {r[3]}  R-G = {r[3][0]-r[3][1]:+d}")
    print("\nfolio strips:")
    for r in rows:
        if r[1] in (8, 27, 38, 51, 66, 78):
            print(f"   p{r[0]} xref {r[1]:<3} {r[3]}")


# ------------------------------------------------------------------ orange
def _orange(a):
    a = a.astype(int)
    return ((a[:, :, 0] > 150) & (a[:, :, 1] > 40) & (a[:, :, 1] < 175) &
            (a[:, :, 2] < 110) & (a[:, :, 0] - a[:, :, 2] > 70))


def orange():
    d = doc()
    print("The orange-pixel mask of window/thirty_clues.md clue 16, applied to")
    print("BOTH the 200 dpi colour layer alone and the 400 dpi composite.\n")
    print(f"{'pg':<5}{'colour layer':>14}{'composite render':>18}")
    for i, pg in enumerate(d):
        col = np.array(Image.open(io.BytesIO(
            d.extract_image(pg.get_images()[0][0])["image"])).convert("RGB"))
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(400 / 72, 400 / 72))
        ren = np.array(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        m = _orange(ren)
        extra = ""
        if 0 < m.sum() and _orange(col).sum() == 0:
            ys, xs = np.nonzero(m)
            extra = ("   all of it inside "
                     f"[{xs.min()*72/400:.2f}, {ys.min()*72/400:.2f}, "
                     f"{xs.max()*72/400:.2f}, {ys.max()*72/400:.2f}] pt")
        print(f"{PAGE_MAP[i]:<5}{_orange(col).sum():>14}{m.sum():>18}{extra}")


# ------------------------------------------------------------------- empty
def empty():
    d = doc()
    # polarity proof
    pg = d[6]
    r = pymupdf.Rect(161.28, 576.72, 473.76, 607.68)
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(400 / 72, 400 / 72), clip=r)
    b = np.array(Image.frombytes("RGB", (pix.width, pix.height), pix.samples)).astype(int)
    near = lambda c, t: (np.abs(b - np.array(c)).max(axis=2) < t).mean()
    print("POLARITY PROOF, p79 xref 64/65 share rect", list(r))
    print(f"   xref 64 light fraction in extracted PNG : {_stencil(d,64).mean():.4f}")
    print(f"   render fraction within 12 of xref 64's fill (107,90,96): {near((107,90,96),12):.4f}")
    print(f"   render fraction within 20 of xref 65's fill (157,131,92): {near((157,131,92),20):.6f}")
    print("   => the LIGHT class of the extracted PNG is the PAINTED class,")
    print("      and xref 65's fill colour never reaches the page.\n")
    print(f"{'pg':<5}{'xref':<6}{'WxH':<12}{'samples':>10}{'painted':>10}"
          f"{'painted %':>11}{'stream B':>10}")
    for i, p in enumerate(d):
        for x in p.get_images(full=True):
            if x[5] == "DeviceRGB":
                continue
            s = _stencil(d, x[0])
            print(f"{PAGE_MAP[i]:<5}{x[0]:<6}{f'{x[2]}x{x[3]}':<12}{s.size:>10}"
                  f"{int(s.sum()):>10}{100*s.mean():>10.3f}%"
                  f"{len(d.xref_stream_raw(x[0])):>10}")


# ----------------------------------------------------------------- filters
def filters():
    d = doc()
    tr = tj = 0
    print(f"{'pg':<5}{'xref':<6}{'/Filter':<28}{'stored':>9}{'inner JPEG':>12}"
          f"{'flate saves':>13}{'%':>8}")
    for i, pg in enumerate(d):
        for x in pg.get_images(full=True):
            if x[5] != "DeviceRGB":
                continue
            raw = d.xref_stream_raw(x[0])
            jpg = d.extract_image(x[0])["image"]
            tr += len(raw); tj += len(jpg)
            print(f"{PAGE_MAP[i]:<5}{x[0]:<6}"
                  f"{d.xref_get_key(x[0],'Filter')[1]:<28}{len(raw):>9}"
                  f"{len(jpg):>12}{len(jpg)-len(raw):>13}"
                  f"{100*(1-len(raw)/len(jpg)):>7.2f}%")
    print(f"{'TOTAL':<39}{tr:>9}{tj:>12}{tj-tr:>13}{100*(1-tr/tj):>7.2f}%")


def jpeg():
    d = doc()
    sigs = set()
    for i, pg in enumerate(d):
        x = pg.get_images()[0][0]
        b = d.extract_image(x)["image"]
        im = Image.open(io.BytesIO(b))
        q = im.quantization
        sigs.add(tuple(tuple(v) for v in q.values()))
        k, samp = 2, None
        while k < len(b) - 1:
            if b[k] != 0xFF:
                k += 1; continue
            m = b[k + 1]
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                k += 2; continue
            if m == 0xC0:
                samp = [(b[k+11+3*c] >> 4, b[k+11+3*c] & 15) for c in range(b[k+9])]
                break
            k += 2 + ((b[k+2] << 8) | b[k+3])
        print(f"p{PAGE_MAP[i]} xref {x:<3} {im.size} DQT sums "
              f"{ {kk: sum(v) for kk, v in q.items()} } sampling HxV {samp}")
    print("\ndistinct quantization-table sets across the eight colour layers:", len(sigs))
    q = Image.open(io.BytesIO(d.extract_image(34)["image"])).quantization
    print("luma  DQT[0][:8] :", list(q[0])[:8], " sum", sum(q[0]))
    print("chroma DQT[1][:8]:", list(q[1])[:8], " sum", sum(q[1]))
    print("chroma coefficients pinned at the 164 ceiling:",
          sum(1 for v in q[1] if v == 164), "of 64")
    y = np.array(Image.open(io.BytesIO(d.extract_image(34)["image"])).convert("YCbCr"))
    h, w, _ = y.shape
    for n, ch in (("Cb", 1), ("Cr", 2), ("Y ", 0)):
        c = y[:, :, ch].astype(int)
        print(f"  {n}: horizontal even/odd pairs equal {np.mean(c[:,0:w:2]==c[:,1:w:2]):.4f}"
              f"   vertical {np.mean(c[0:h:2,:]==c[1:h:2,:]):.4f}")
    print(f"  => chroma is {w//2}x{h} = 100 x 200 dpi; luma is {w}x{h} = 200 x 200 dpi")


# ------------------------------------------------------------------- canon
def canon():
    d = doc()
    sizes = collections.Counter()
    print(f"{'pg':<5}{'marker':<30}{'stream B':>9}{'Tj':>6}{'Tf':>6}{'Tr':>5}"
          f"  font-size range")
    for i, pg in enumerate(d):
        c = pg.read_contents().decode("latin-1")
        tf = [float(s) for _, s in re.findall(r"/F(\w+)\s+([\d.]+)\s+Tf", c)]
        sizes.update(tf)
        tr = sorted(set(re.findall(r"(\d+)\s+Tr", c)))
        print(f"{PAGE_MAP[i]:<5}{c.splitlines()[0].strip():<30}{len(c):>9}"
              f"{len(re.findall('Tj', c)):>6}{len(tf):>6}{','.join(tr) or '-':>5}"
              f"  {min(tf) if tf else '-'}-{max(tf) if tf else '-'}")
    print("\nfont resource:", d.xref_object(10).replace("\n", " "))
    print("total Tj word-shows:", sum(
        len(re.findall("Tj", pg.read_contents().decode("latin-1"))) for pg in d))
    print("distinct Tf sizes:", len(sizes), "min", min(sizes), "max", max(sizes))
    steps = sorted({round(b - a, 2) for a, b in zip(sorted(sizes), sorted(sizes)[1:])})
    print("gaps between consecutive sizes:", steps)
    print("histogram:", dict(sorted(sizes.items())))


# -------------------------------------------------------------------- grid
def grid():
    d = doc()
    ws, hs, cm = [], [], []
    for pg in d:
        for x in pg.get_images(full=True):
            if x[5] == "DeviceRGB":
                continue
            ws.append(x[2]); hs.append(x[3])
        toks = pg.read_contents().decode("latin-1").split()
        for j, t in enumerate(toks):
            if t == "cm":
                cm += [float(v) for v in toks[j - 6:j]]
    cm = [v for v in cm if v]
    print("bilevel widths :", sorted(set(ws)))
    print("   every width  a multiple of 8 px:", all(w % 8 == 0 for w in ws),
          "  of 16:", all(w % 16 == 0 for w in ws))
    print("bilevel heights:", sorted(set(hs)))
    print("   every height a multiple of 4 px:", all(h % 4 == 0 for h in hs),
          "  of 8:", all(h % 8 == 0 for h in hs))
    print(f"{len(cm)} non-zero CTM values; all multiples of 0.72 pt (1/100 in "
          f"= 4 px at 400 dpi):",
          all(abs(round(v / 0.72) - v / 0.72) < 1e-9 for v in cm))
    print("   smallest |CTM value|:", min(abs(v) for v in cm), "pt")


def ctm():
    d = doc()
    for i, pg in enumerate(d):
        toks = pg.read_contents().decode("latin-1").split()
        cur = None
        print(f"--- printed page {PAGE_MAP[i]} ---")
        for j, t in enumerate(toks):
            if t == "cm":
                cur = [float(v) for v in toks[j - 6:j]]
            if t == "Do":
                a, b, c, dd = cur[:4]
                det = a * dd - b * c
                print(f"   {toks[j-1]:<8} cm={cur} det={det:+.2f} "
                      f"skew={'yes' if (b or c) else 'no'} "
                      f"{'FLIPPED' if det < 0 else ''}")


def x18():
    d = doc()
    p = _stencil(d, 18)[::-1, ::-1]     # un-rotate to reading orientation
    rows = p.sum(axis=1)
    bands, s, gap = [], None, 0
    for i, v in enumerate(rows):
        if v:
            s = i if s is None else s; gap = 0
        elif s is not None:
            gap += 1
            if gap > 40:
                bands.append((s, i - gap)); s = None
    if s is not None:
        bands.append((s, len(rows) - 1))
    print("xref 18, 1080x868, painted %.2f%% -- in READING orientation:" % (100 * p.mean()))
    for a0, a1 in bands:
        sub = p[a0:a1 + 1]
        c = np.nonzero(sub.sum(axis=0))[0]
        print(f"   rows {a0:4d}-{a1:4d}  cols {c.min():4d}-{c.max():4d}  "
              f"painted {int(sub.sum()):6d} px")
    if len(bands) > 1:
        g = max(bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1))
        print(f"   largest blank gap between bands: {g} rows = {g/400:.3f} in at 400 dpi")


def dump(out="/tmp/imgs"):
    d = doc()
    os.makedirs(out, exist_ok=True)
    for i, pg in enumerate(d):
        for x in pg.get_images(full=True):
            if x[5] == "DeviceRGB":
                continue
            a = Image.open(io.BytesIO(d.extract_image(x[0])["image"])).convert("L").rotate(180)
            w, h = a.size
            while max(a.size) > 1600:
                a = a.resize((a.size[0] // 2, a.size[1] // 2))
            fn = f"{out}/p{PAGE_MAP[i]}_x{x[0]}_{w}x{h}.png"
            a.save(fn); print(fn)


if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    globals()[fn]()
