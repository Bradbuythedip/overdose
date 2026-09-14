#!/usr/bin/env python3
"""
PAGE 72 IN FULL -- reproducible measurements of the NUMBERS page.

Page 72 is the department page facing the article opener. It was in no
transcript and no corpus until the 8-page scan `scan/Scan1.pdf` was found, and
even then only its display statistics were recorded. This measures the whole
page: the complete text including both columns of source URLs, how the scan's
ink separations carve the page up, the only drawn line-art in the artefact, the
ink colours, and the numeral inventory.

  python3 wf/clue_page72.py --all
  python3 wf/clue_page72.py --transcript   complete printed text
  python3 wf/clue_page72.py --masks        the four embedded images, which text
                                           each 1-bit separation carries, and
                                           what has no separation at all
  python3 wf/clue_page72.py --ocr          what the PDF text layer does and
                                           does not contain, vs the separations
  python3 wf/clue_page72.py --rule         the corner-bracket keyline
  python3 wf/clue_page72.py --colour       per-element ink RGB, and orange
  python3 wf/clue_page72.py --sharp        stencil text vs background-only text
  python3 wf/clue_page72.py --numerals     the numeral inventory
"""
import argparse, io, os, re, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "scan", "Scan1.pdf")
PAGEMAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
IDX72 = 1
DPI = 400
W, H = 3400, 4400                    # 612x792 pt at 400 dpi

# ---- complete transcription, read at 400-900 dpi off the corrected render ---
TRANSCRIPT = [
    ("masthead",  "NUMBERS"),
    ("stat1",     "165"),
    ("stat1",     "WESTERN UNION"),
    ("stat1",     "LOCATIONS IN"),
    ("stat1",     "PALESTINE"),
    ("stat2",     "572"),
    ("stat2",     "WESTERN UNION"),
    ("stat2",     "LOCATIONS IN"),
    ("stat2",     "EL SALVADOR"),
    ("revenue",   "In 2020,"),
    ("revenue",   "WESTERN"),
    ("revenue",   "UNION"),
    ("revenue",   "GENERATED REVENUE"),
    ("revenue",   "OF $4.8 BILLION"),
    ("market",    "The global"),
    ("market",    "REMITTANCE"),
    ("market",    "MARKET SIZE"),
    ("market",    "is projected to reach"),
    ("market",    "$930.44 BILLION BY 2026"),
    ("cagr",      "Based on a compound"),
    ("cagr",      "annual growth rate of 3.9%"),
    ("cagr",      "(taken from historical"),
    ("cagr",      "remittance industry"),
    ("cagr",      "growth data)."),
    ("digital",   "The global"),
    ("digital",   "DIGITAL"),
    ("digital",   "REMITTANCE"),
    ("digital",   "MARKET"),
    ("digital",   "is estimated to reach"),
    ("digital",   "$35.8 BILLION BY 2026"),
    ("digital",   "This is up from"),
    ("digital",   "$14.5 BILLION BY 2019"),
    ("footerL",   "Sources:"),
    ("footerL",   "www.knomad.org/publication/migration-and-development-brief-34"),
    ("footerL",   "www.migrationdataportal.org/themes/remittances"),
    ("footerL",   "www.worldbank.org/en/news/press-release/2021/05/12/defying-"
                  "predictions-remittance-flows-remain-strong-during-covid-19-crisis"),
    ("footerL",   "www.wise.com/documents/Public_Research_and_Survey_-_US_Hidden_Fees"),
    ("footerR",   "www.repository.upenn.edu/sire/75/"),
    ("footerR",   "www.westernunion.com/sv/en/receive-money.html"),
    ("footerR",   "ir.westernunion.com/investor-relations/financial-information/"),
    ("footerR",   "www.alliedmarketresearch.com/remittance-market"),
    ("footerR",   "www.globenewswire.com/news-release/2021/04/12/2208403/"),
    ("sidebar",   "Bitcoin Magazine | El Salvador"),   # rotated 90 CW, right edge
    ("folio",     "72"),
]

# glyph boxes on the corrected 3400x4400 render, found by ink-band segmentation
BOXES = {
    "masthead NUMBERS":   (2880, 205, 3180, 255),
    "165 numerals":       (1370, 385, 1526, 458),
    "WESTERN UNION(165)": (991, 482, 1522, 540),
    "LOCATIONS IN(165)":  (1096, 568, 1524, 612),
    "PALESTINE":          (1141, 644, 1525, 695),
    "572 numerals":       (2005, 386, 2176, 459),
    "WESTERN UNION(572)": (2006, 484, 2537, 541),
    "LOCATIONS IN(572)":  (2007, 569, 2435, 614),
    "EL SALVADOR":        (2004, 645, 2450, 697),
    "WESTERN/UNION mark": (1480, 1010, 2060, 1230),
    "GENERATED REVENUE":  (1360, 1270, 2180, 1340),
    "REMITTANCE upper":   (1380, 1670, 2130, 1740),
    "keyline box":        (1330, 2760, 2170, 3050),
    "$35.8 line":         (1290, 3060, 1560, 3170),
    "This is up from":    (1520, 3300, 2050, 3390),
    "$14.5":              (1280, 3425, 1520, 3530),
    "BILLION BY 2019":    (1560, 3425, 2400, 3530),
    "Sources: word":      (480, 3805, 700, 3860),
    "footerL URLs":       (480, 3860, 1740, 4100),
    "footerR URLs":       (1900, 3845, 2960, 4085),
    "sidebar":            (3200, 1850, 3280, 2530),
    "folio 72":           (3180, 4155, 3270, 4230),
}

_cache = {}


def doc():
    import pymupdf
    if "d" not in _cache:
        _cache["d"] = pymupdf.open(PDF)
    return _cache["d"]


def render72(dpi=DPI):
    import pymupdf
    k = f"r{dpi}"
    if k not in _cache:
        pix = doc()[IDX72].get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        _cache[k] = np.asarray(im.rotate(180)).astype(float)   # scan is 180-rot
    return _cache[k]


def stencils():
    """Each 1-bit separation rasterised onto the corrected page canvas."""
    if "st" in _cache:
        return _cache["st"]
    d, pg, out = doc(), doc()[IDX72], {}
    for it in pg.get_image_info(xrefs=True):
        info = d.extract_image(it["xref"])
        if info["bpc"] != 1:
            continue
        m = np.array(Image.open(io.BytesIO(info["image"])).convert("L")) > 127
        b = it["bbox"]
        c = np.zeros((H, W), bool)
        x0, x1 = int(round(b[0] / 612 * W)), int(round(b[2] / 612 * W))
        y0, y1 = int(round(b[1] / 792 * H)), int(round(b[3] / 792 * H))
        c[y0:y1, x0:x1] = np.array(
            Image.fromarray(m.astype(np.uint8) * 255)
            .resize((x1 - x0, y1 - y0), Image.NEAREST)) > 127
        out[it["xref"]] = np.rot90(c, 2)
    _cache["st"] = out
    return out


# --------------------------------------------------------------- transcript --
def cmd_transcript():
    cur = None
    for sec, t in TRANSCRIPT:
        if sec != cur:
            print(f"\n  [{sec}]")
            cur = sec
        print(f"    {t}")
    nch = sum(len(t) for _, t in TRANSCRIPT)
    urls = [t for s, t in TRANSCRIPT if s.startswith("footer") and t != "Sources:"]
    print(f"\n  {len(TRANSCRIPT)} printed lines, {nch} characters")
    print(f"  {len(urls)} source URLs, {sum(len(u) for u in urls)} characters of URL")


# ------------------------------------------------------------------- masks ---
def cmd_masks():
    d = doc()
    print("  embedded images per page (get_images(full=True), NO size filter --")
    print("  note extract_scan.py's masks() drops anything under 500,000 px):")
    for i, pg in enumerate(d):
        print(f"    pdf idx {i}  printed {PAGEMAP[i]}  {len(pg.get_images(full=True))} images")
    print("\n  page 72, every embedded image, placement in pt on a 612x792 page,")
    print("  with the fill colour the content stream sets before each Do:")
    c = b"".join(d.xref_stream(x) for x in d[IDX72].get_contents())
    pat = re.compile(rb"q\s+((?:[\d.]+ ){1,4}(?:rg|g)\s+)?([\d.]+) 0 0 ([\d.]+) "
                     rb"([\d.]+) ([\d.]+) cm\s+/(\w+) Do\s+Q")
    fills = {}
    for m in pat.finditer(c):
        col = (m.group(1) or b"").decode().strip()
        fills[m.group(6).decode()] = col
    for it in d[IDX72].get_image_info(xrefs=True):
        info = d.extract_image(it["xref"])
        b = it["bbox"]
        a = np.array(Image.open(io.BytesIO(info["image"])).convert("L"))
        ink = f"{(a > 127).mean():.4f}" if info["bpc"] == 1 else "   -  "
        col = fills.get(f"Obj{it['xref']}", "")
        rgb = ""
        if col.endswith("rg"):
            rgb = str(tuple(round(float(t) * 255) for t in col.split()[:3]))
        elif col.endswith("g"):
            rgb = str((round(float(col.split()[0]) * 255),) * 3)
        print(f"    x{it['xref']:<3} {info['width']:>5}x{info['height']:<5} "
              f"bpc={info['bpc']}  bbox=({b[0]:6.2f},{b[1]:6.2f},{b[2]:6.2f},"
              f"{b[3]:6.2f})  ink={ink}  fill={col:<22}{rgb}")

    st = stencils()
    ks = sorted(st)
    print("\n  ink coverage of each printed element in each 1-bit separation:")
    print(f"    {'element':<20} " + "  ".join(f"  x{k}" for k in ks) + "     ANY")
    orphan = []
    for n, (x0, y0, x1, y1) in BOXES.items():
        vs = [st[k][y0:y1, x0:x1].mean() * 100 for k in ks]
        anyv = np.any([st[k][y0:y1, x0:x1] for k in ks], axis=0).mean() * 100
        if anyv == 0:
            orphan.append(n)
        print(f"    {n:<20} " + "  ".join(f"{v:5.2f}%" for v in vs) + f"  {anyv:6.2f}%")
    print(f"\n  elements with NO 1-bit separation at all ({len(orphan)}): {orphan}")
    print("  those survive only in the 200 dpi lossy background layer x16.")
    # prove the background is inpainted where a stencil exists
    bg = np.rot90(np.asarray(Image.open(io.BytesIO(
        doc().extract_image(16)["image"])).convert("L")).astype(float), 2)
    bgH, bgW = bg.shape
    def bgmean(box, mask=None):
        x0, y0, x1, y1 = [int(round(v / (W if i % 2 == 0 else H)
                                    * (bgW if i % 2 == 0 else bgH)))
                          for i, v in enumerate(box)]
        return bg[y0:y1, x0:x1]
    print("\n  background layer x16 luminance (0=black, 255=white):")
    for n in ("165 numerals", "572 numerals", "footerL URLs", "folio 72", "$14.5"):
        s = bgmean(BOXES[n])
        print(f"    {n:<16} min={s.min():5.1f} p5={np.percentile(s,5):6.1f} "
              f"mean={s.mean():6.1f}")
    print("  -> where a stencil exists the background is inpainted blank paper;")
    print("     where none exists the glyphs are still there, at 200 dpi.")
    return orphan


# --------------------------------------------------------------------- ocr ---
def cmd_ocr():
    """The PDF text layer is OCR of the page ROTATED 180. Test its coverage
    GEOMETRICALLY: map each printed region into the rotated page's coordinates
    and count OCR words whose bbox falls inside it."""
    pg = doc()[IDX72]
    words = pg.get_text("words")
    t = pg.get_text()
    print(f"  p72 text layer: {len(t)} chars, {len(t.splitlines())} lines, "
          f"{len(words)} OCR words")

    def torot(x0, y0, x1, y1):
        return (612 - x1 / W * 612, 792 - y1 / H * 792,
                612 - x0 / W * 612, 792 - y0 / H * 792)

    tests = {
        "footerR URLs   (stencil x17)": (1890, 3830, 2970, 4095),
        "footerL URLs   (NO stencil)":  (470, 3795, 1780, 4115),
        "folio 72       (NO stencil)":  (3170, 4145, 3280, 4240),
        "$14.5          (NO stencil)":  (1270, 3415, 1530, 3540),
        "572 block      (stencil x18)": (1990, 330, 2560, 710),
        "165 block      (stencil x17)": (960, 330, 1560, 710),
    }
    for n, box in tests.items():
        a, b, c, e = torot(*box)
        hit = [w for w in words
               if w[0] >= a - 2 and w[2] <= c + 2 and w[1] >= b - 2 and w[3] <= e + 2]
        print(f"    {n:<30} OCR words inside = {len(hit):3d}  "
              f"{[w[4] for w in hit[:4]]}")
    print("  -> the text layer's coverage is exactly the stencil coverage:")
    print("     every element with a 1-bit separation was OCR'd, and the four")
    print("     that have none produced zero OCR words. That is why no machine")
    print("     transcript has ever contained the left-hand source column.")
    return words


# -------------------------------------------------------------------- rule ---
def _runs(mask):
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(mask) - 1))
    return out


def cmd_rule():
    g = render72().mean(2)
    x0, y0, x1, y1 = BOXES["keyline box"]
    dark = g[y0:y1, x0:x1] < 150
    wpx = x1 - x0
    print(f"  discriminator: a drawn rule is a long CONTIGUOUS run of ink in one")
    print(f"  row (the test window/no_rules_on_the_pages.md ran on pages 73-79).")
    print(f"  window {BOXES['keyline box']}  {wpx}x{y1-y0}px at {DPI} dpi")
    hits = [(y0 + i, max((b - a + 1) for a, b in _runs(dark[i])) if dark[i].any() else 0)
            for i in range(y1 - y0)]
    long = [(y, r) for y, r in hits if r >= 0.12 * wpx]
    print(f"  rows whose longest run >= 12% of window width: {len(long)}  "
          f"y={long[0][0]}..{long[-1][0]}")
    for y in (2806, 3022):
        segs = [(x0 + a, x0 + b, b - a + 1) for a, b in _runs(g[y, x0:x1] < 150)
                if b - a + 1 >= 6]
        print(f"    y={y}: {len(segs)} segments {segs}  gap between them = "
              f"{segs[1][0]-segs[0][1]-1}px")
    for x in (1384, 2140):
        segs = [(y0 + a, y0 + b, b - a + 1) for a, b in _runs(g[y0:y1, x] < 150)
                if b - a + 1 >= 6]
        print(f"    x={x}: {len(segs)} segments {segs}")
    print("  -> two corner brackets, not a closed box.")
    print(f"  overall 1382..2142 x 2803..3026 = 761x224 px = "
          f"{761/DPI*72:.1f}x{224/DPI*72:.1f} pt; stroke 5-6px = "
          f"{5.5/DPI*72:.2f} pt")
    # and nothing else on the page
    full = render72().mean(2) < 150
    band = [(y, max((b - a + 1) for a, b in _runs(full[y])) if full[y].any() else 0)
            for y in range(H)]
    print(f"  same test over the whole page at >=400px (11.8% of page width): "
          f"{sum(1 for _, r in band if r >= 400)} rows")
    return long


# ------------------------------------------------------------------ colour ---
def cmd_colour():
    a = render72()
    print("  per-element ink colour on the composited 400 dpi render")
    print("  (darkest quartile of each glyph box):")
    for n in ("165 numerals", "WESTERN UNION(165)", "LOCATIONS IN(165)",
              "PALESTINE", "572 numerals", "WESTERN UNION(572)",
              "LOCATIONS IN(572)", "EL SALVADOR", "WESTERN/UNION mark",
              "GENERATED REVENUE", "REMITTANCE upper", "footerL URLs",
              "footerR URLs", "folio 72"):
        x0, y0, x1, y1 = BOXES[n]
        s = a[y0:y1, x0:x1].reshape(-1, 3)
        L = s.mean(1)
        core = s[L <= np.percentile(L, 25)]
        paper = np.percentile(L, 95)
        print(f"    {n:<20} RGB=({core[:,0].mean():5.1f},{core[:,1].mean():5.1f},"
              f"{core[:,2].mean():5.1f})  inkL={core.mean():6.1f} "
              f"paperL={paper:6.1f}  dL={paper-core.mean():6.1f}")
    # orange, every page, composited
    import pymupdf
    print("\n  saturated-orange pixels per page, composited render at 200 dpi")
    print("  (HSV hue 10-45 deg, S>0.45, V>0.45):")
    for i in range(8):
        pix = doc()[i].get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72))
        q = (np.frombuffer(pix.samples, np.uint8)
             .reshape(pix.height, pix.width, 3).astype(np.float32) / 255)
        mx, mn = q.max(2), q.min(2)
        s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        r, gg, b = q[..., 0], q[..., 1], q[..., 2]
        dd = mx - mn + 1e-6
        h = np.where(mx == r, ((gg - b) / dd) % 6,
                     np.where(mx == gg, (b - r) / dd + 2, (r - gg) / dd + 4)) * 60
        m = (h >= 10) & (h <= 45) & (s > 0.45) & (mx > 0.45)
        print(f"    p{PAGEMAP[i]}  {int(m.sum()):8,d} px")


# ------------------------------------------------------------------- sharp ---
def cmd_sharp():
    g = render72().mean(2)
    print("  soft-edge (midtone) pixels per ink pixel -- a bilevel stencil gives")
    print("  ~0, a 200 dpi lossy background gives a large ratio:")
    for n in ("footerR URLs", "$35.8 line", "BILLION BY 2019",
              "footerL URLs", "Sources: word", "folio 72", "$14.5"):
        x0, y0, x1, y1 = BOXES[n]
        s = g[y0:y1, x0:x1]
        lo, hi = np.percentile(s, 3), np.percentile(s, 97)
        ink = (s < lo + (hi - lo) * 0.25).mean()
        mid = ((s > lo + (hi - lo) * 0.25) & (s < lo + (hi - lo) * 0.75)).mean()
        print(f"    {n:<18} ink={ink:.3f}  midtone={mid:.3f}  "
              f"midtone/ink={mid/max(ink,1e-9):6.2f}")


# ---------------------------------------------------------------- numerals ---
def cmd_numerals():
    import collections
    text = " ".join(t for _, t in TRANSCRIPT)
    nums = re.findall(r"\d[\d.]*\d|\d", text)
    dig = "".join(c for c in text if c.isdigit())
    c = collections.Counter(dig)
    print(f"  numeral tokens on page 72: {len(nums)}")
    print("   ", " ".join(nums))
    print(f"  digit glyphs: {len(dig)}")
    print("  frequency: " + "  ".join(f"{k}:{c.get(str(k),0)}" for k in range(10)))
    print(f"  distinct digits: {len(c)}/10 "
          f"(missing {sorted(set('0123456789')-set(c)) or 'none'})")
    stats = [t for s, t in TRANSCRIPT
             if s in ("stat1", "stat2", "revenue", "market", "cagr", "digital")]
    sn = re.findall(r"\d[\d.]*\d|\d", " ".join(stats))
    print(f"  statistics blocks only ({len(sn)}): {' '.join(sn)}")
    ft = [t for s, t in TRANSCRIPT if s.startswith("footer") or s == "folio"]
    fn = re.findall(r"\d[\d.]*\d|\d", " ".join(ft))
    print(f"  footer + folio add ({len(fn)}): {' '.join(fn)}")



# ---------------------------------------------------------------- geometry ---
def _bands(g, x0, y0, x1, y1, th=170, minink=3, minh=10, mask_cols=()):
    s = (g[y0:y1, x0:x1] < th).copy()
    for a, b in mask_cols:
        s[:, max(0, a - x0):max(0, b - x0)] = False
    rs = s.sum(1)
    out, st = [], None
    for i, v in enumerate(rs):
        if v >= minink and st is None:
            st = i
        elif v < minink and st is not None:
            out.append((y0 + st, y0 + i - 1)); st = None
    if st is not None:
        out.append((y0 + st, y0 + len(rs) - 1))
    return [(a, b, b - a + 1) for a, b in out if b - a + 1 >= minh]


def cmd_geometry():
    g = render72().mean(2)
    print("  the two statistic blocks, line by line (ink-band segmentation):")
    for tag, (a, b) in (("165/PALESTINE", (900, 1650)),
                        ("572/EL SALVADOR", (1900, 2650))):
        for (y0, y1, h) in _bands(g, a, 300, b, 760):
            nz = np.where((g[y0:y1 + 1, a:b] < 170).sum(0) > 0)[0]
            print(f"    {tag:<16} y{y0}-{y1} h={h:2d}px  x {a+nz.min()}..{a+nz.max()}")
    print("    -> identical line heights (within 1px); block 1 is flush RIGHT at")
    print("       x~1523, block 2 flush LEFT at x~2005. Mirrored, not repeated.")

    print("\n  the DIGITAL block against the corner brackets (y2803..3026):")
    for (y0, y1, h) in _bands(g, 1350, 2600, 2200, 3400,
                              mask_cols=((1380, 1390), (2136, 2145))):
        inside = "INSIDE " if y0 >= 2803 and y1 <= 3026 else "outside"
        print(f"    y{y0}-{y1} h={h:2d}px  {inside} the brackets")

    print("\n  what page 72's tall thin separation x19 actually holds:")
    st = stencils()
    ys, xs = np.where(st[19])
    print(f"    x19 ink pixels on the corrected page: {len(xs)}  "
          f"x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}  "
          f"(printed LEFT trim margin)")
    x0, y0, x1, y1 = BOXES["sidebar"]
    print(f"    'Bitcoin Magazine | El Salvador' sidebar box {BOXES['sidebar']} "
          f"(printed RIGHT margin):")
    for k in sorted(st):
        print(f"      x{k}: {st[k][y0:y1, x0:x1].mean()*100:5.2f}% ink")
    print("    -> x19 is the torn trim edge, not the sidebar; the sidebar type")
    print("       belongs to the page mask x17.")


def main():
    ap = argparse.ArgumentParser()
    names = ["transcript", "masks", "ocr", "rule", "geometry", "colour",
             "sharp", "numerals"]
    for f in names + ["all"]:
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    run = [k for k in names if getattr(a, k) or a.all] or ["transcript"]
    for k in run:
        print(f"\n=== {k.upper()} ===")
        globals()["cmd_" + k]()


if __name__ == "__main__":
    main()
