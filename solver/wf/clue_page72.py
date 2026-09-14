#!/usr/bin/env python3
"""
PAGE 72 IN FULL -- measurements for the Overdose puzzle.

Page 72 is the NUMBERS department page facing the article opener. It was in no
transcript until the 8-page scan was found. This script measures it.

  python3 wf/clue_page72.py --all
  python3 wf/clue_page72.py --masks      # the four embedded images and what
                                         # text each bilevel separation holds
  python3 wf/clue_page72.py --rule       # the keyline box (drawn rules)
  python3 wf/clue_page72.py --globes     # the two wireframe globe graphics
  python3 wf/clue_page72.py --colour     # ink colour vs the article pages
  python3 wf/clue_page72.py --numerals   # the numeral inventory
"""
import argparse, io, os, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "scan", "Scan1.pdf")
PDFIDX_72 = 1                      # PDF page 1 is printed page 72
DPI = 400
W, H = 3400, 4400                  # 612x792 pt at 400 dpi

# --- the complete transcription, read at 400 dpi off the corrected render ----
# reading order, top to bottom, left to right
TRANSCRIPT = [
    ("masthead",   "NUMBERS"),
    ("stat1",      "165"),
    ("stat1",      "WESTERN UNION"),
    ("stat1",      "LOCATIONS IN"),
    ("stat1",      "PALESTINE"),
    ("stat2",      "572"),
    ("stat2",      "WESTERN UNION"),
    ("stat2",      "LOCATIONS IN"),
    ("stat2",      "EL SALVADOR"),
    ("revenue",    "In 2020,"),
    ("revenue",    "WESTERN"),
    ("revenue",    "UNION"),
    ("revenue",    "GENERATED REVENUE"),
    ("revenue",    "OF $4.8 BILLION"),
    ("market",     "The global"),
    ("market",     "REMITTANCE"),
    ("market",     "MARKET SIZE"),
    ("market",     "is projected to reach"),
    ("market",     "$930.44 BILLION BY 2026"),
    ("cagr",       "Based on a compound"),
    ("cagr",       "annual growth rate of 3.9%"),
    ("cagr",       "(taken from historical"),
    ("cagr",       "remittance industry"),
    ("cagr",       "growth data)."),
    ("digital",    "The global"),
    ("digital",    "DIGITAL"),
    ("digital",    "REMITTANCE"),
    ("digital",    "MARKET"),
    ("digital",    "is estimated to reach"),
    ("digital",    "$35.8 BILLION BY 2026"),
    ("digital",    "This is up from"),
    ("digital",    "$14.5 BILLION BY 2019"),
    ("footer",     "Sources:"),
    ("footerL",    "www.knomad.org/publication/migration-and-development-brief-34"),
    ("footerL",    "www.migrationdataportal.org/themes/remittances"),
    ("footerL",    "www.worldbank.org/en/news/press-release/2021/05/12/defying-"
                   "predictions-remittance-flows-remain-strong-during-covid-19-crisis"),
    ("footerL",    "www.wise.com/documents/Public_Research_and_Survey_-_US_Hidden_Fees"),
    ("footerR",    "www.repository.upenn.edu/sire/75/"),
    ("footerR",    "www.westernunion.com/sv/en/receive-money.html"),
    ("footerR",    "ir.westernunion.com/investor-relations/financial-information/"),
    ("footerR",    "www.alliedmarketresearch.com/remittance-market"),
    ("footerR",    "www.globenewswire.com/news-release/2021/04/12/2208403/"),
    ("sidebar",    "Bitcoin Magazine | El Salvador"),   # rotated 90 deg, right edge
    ("folio",      "72"),
]

# regions on the corrected 3400x4400 render (x0,y0,x1,y1)
BOXES = {
    "masthead":     (2850, 200, 3180, 260),
    "stat1":        (960, 330, 1560, 720),
    "stat2":        (1960, 330, 2600, 720),
    "revenue":      (1400, 900, 2150, 1450),
    "market":       (1150, 1570, 2400, 2170),
    "cagr":         (1400, 2150, 2160, 2500),
    "digital":      (1200, 2600, 2280, 3560),
    "keylinebox":   (1330, 2760, 2170, 3050),
    "footerL":      (470, 3810, 1760, 4100),
    "footerR":      (1900, 3840, 2960, 4090),
    "sidebar":      (3200, 1850, 3280, 2530),
    "folio":        (3140, 4140, 3260, 4210),
}


def render_page(dpi=DPI):
    import pymupdf
    d = pymupdf.open(PDF)
    pg = d[PDFIDX_72]
    m = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = pg.get_pixmap(matrix=m)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return im.rotate(180)          # every page of the scan is 180 deg rotated


def embedded(xref):
    import pymupdf
    d = pymupdf.open(PDF)
    info = d.extract_image(xref)
    im = Image.open(io.BytesIO(info["image"]))
    return im, info


# ---------------------------------------------------------------- masks -----
def cmd_masks():
    """Which of page 72's printed text each bilevel ink separation holds."""
    import pymupdf
    d = pymupdf.open(PDF)
    PAGEMAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
    print("  embedded images per page (get_images, no size filter):")
    for i, pg in enumerate(d):
        n = len(pg.get_images(full=True))
        print(f"    pdf idx {i}  printed {PAGEMAP[i]}  {n} images")

    pg = d[PDFIDX_72]
    print("\n  page 72, every embedded image with its placement (pt, 612x792):")
    placed = {}
    for it in pg.get_image_info(xrefs=True):
        b = it["bbox"]
        placed[it["xref"]] = b
        im, info = embedded(it["xref"])
        a = np.array(im.convert("L"))
        ink = float((a > 127).mean()) if info["bpc"] == 1 else float("nan")
        print(f"    x{it['xref']:<3} {info['width']}x{info['height']} "
              f"bpc={info['bpc']} bbox=({b[0]:.1f},{b[1]:.1f},{b[2]:.1f},{b[3]:.1f}) "
              f"ink_frac={ink:.4f}")

    # composite the bilevel separations onto one corrected page canvas
    canvas = {}
    for xref, b in placed.items():
        im, info = embedded(xref)
        if info["bpc"] != 1:
            continue
        m = np.array(im.convert("L")) > 127            # True = ink
        lay = np.zeros((H, W), bool)
        x0 = int(round(b[0] / 612 * W)); x1 = int(round(b[2] / 612 * W))
        y0 = int(round(b[1] / 792 * H)); y1 = int(round(b[3] / 792 * H))
        r = np.array(Image.fromarray(m.astype(np.uint8) * 255)
                     .resize((x1 - x0, y1 - y0), Image.NEAREST)) > 127
        lay[y0:y1, x0:x1] = r
        canvas[xref] = np.rot90(lay, 2)                # un-rotate the page
    print("\n  ink present in each separation, per printed region:")
    print(f"    {'region':<12} " + "  ".join(f"x{k}" for k in sorted(canvas)))
    for name, (bx0, by0, bx1, by1) in BOXES.items():
        row = []
        for k in sorted(canvas):
            f = canvas[k][by0:by1, bx0:bx1].mean()
            row.append(f"{f*100:5.2f}%")
        print(f"    {name:<12} " + "  ".join(row))
    return canvas


# ------------------------------------------------------------- keyline -------
def longest_run(row):
    best = cur = 0
    for v in row:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def cmd_rule(thresh_frac=0.12):
    """A drawn rule = a long CONTIGUOUS run of ink in one row/column.
    Same discriminator window/no_rules_on_the_pages.md used on pages 73-79."""
    im = render_page()
    a = np.array(im.convert("L"))
    x0, y0, x1, y1 = BOXES["keylinebox"]
    sub = a[y0:y1, x0:x1]
    dark = sub < 150
    wpx = x1 - x0
    hpx = y1 - y0
    print(f"  region {BOXES['keylinebox']}  {wpx}x{hpx}px at {DPI} dpi")
    print(f"  threshold: a run >= {int(thresh_frac*wpx)}px (12% of width) is a rule")
    rows = [(y0 + i, longest_run(dark[i])) for i in range(hpx)]
    hits = [r for r in rows if r[1] >= thresh_frac * wpx]
    print(f"  ROWS with a long run: {len(hits)}")
    for y, r in hits:
        xs = np.where(dark[y - y0])[0]
        print(f"    y={y}  longest_run={r}px  ink spans x={x0+xs.min()}..{x0+xs.max()}")
    cols = [(x0 + j, longest_run(dark[:, j])) for j in range(wpx)]
    chits = [c for c in cols if c[1] >= thresh_frac * hpx]
    print(f"  COLUMNS with a long run: {len(chits)}")
    for x, r in chits:
        ys = np.where(dark[:, x - x0])[0]
        print(f"    x={x}  longest_run={r}px  ink spans y={y0+ys.min()}..{y0+ys.max()}")
    # the same test over the whole of page 72 outside this box
    full = np.array(render_page().convert("L")) < 150
    print("\n  same test, whole page 72, run >= 400px (11.8% of page width):")
    band = []
    for y in range(H):
        r = longest_run(full[y])
        if r >= 400:
            band.append((y, r))
    if not band:
        print("    none")
    else:
        # collapse into bands
        out, s, p, mx = [], band[0][0], band[0][0], band[0][1]
        for y, r in band[1:]:
            if y - p <= 2:
                p, mx = y, max(mx, r)
            else:
                out.append((s, p, mx)); s, p, mx = y, y, r
        out.append((s, p, mx))
        for s, e, mx in out:
            print(f"    y={s}..{e} ({e-s+1}px tall)  longest run {mx}px")
    return hits, chits


# -------------------------------------------------------------- globes ------
def cmd_globes():
    """The two wireframe globe graphics behind the remittance blocks."""
    im = render_page()
    a = np.array(im.convert("RGB")).astype(int)
    # the globes are a pale warm line on the paper; isolate by R-B separation
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    for tag, (x0, y0, x1, y1) in (("upper globe", (1050, 1600, 2500, 2200)),
                                  ("lower globe", (1050, 2650, 2500, 3150))):
        sub = a[y0:y1, x0:x1]
        R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
        # globe line is warmer (R>B) than the paper and darker than the paper
        L = sub.mean(2)
        paper = np.percentile(L, 80)
        m = (L < paper - 6) & (R - B > 4)
        print(f"  {tag}: bbox=({x0},{y0},{x1},{y1}) "
              f"paper L80={paper:.1f} line pixels={int(m.sum()):,} "
              f"({m.mean()*100:.2f}% of region)")
        ys, xs = np.where(m)
        if len(xs):
            print(f"    ink extent x={x0+xs.min()}..{x0+xs.max()} "
                  f"({xs.max()-xs.min()+1}px wide), "
                  f"y={y0+ys.min()}..{y0+ys.max()} ({ys.max()-ys.min()+1}px tall)")
            print(f"    aspect (w/h) = {(xs.max()-xs.min()+1)/(ys.max()-ys.min()+1):.3f}")
    return True


# -------------------------------------------------------------- colour ------
def cmd_colour():
    """Ink colour of page 72's display type vs the article's body ink."""
    import pymupdf
    d = pymupdf.open(PDF)
    PAGEMAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
    for idx, regions in ((1, {"165 display": (990, 330, 1310, 420),
                              "572 display": (1985, 330, 2305, 420),
                              "PALESTINE": (1010, 610, 1520, 700),
                              "$930.44 line": (1180, 2010, 2360, 2110),
                              "footer URLs": (480, 3860, 1740, 4090)}),):
        pg = d[idx]
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).rotate(180)
        a = np.array(im).astype(int)
        print(f"  printed page {PAGEMAP[idx]}")
        for name, (x0, y0, x1, y1) in regions.items():
            s = a[y0:y1, x0:x1]
            L = s.mean(2)
            dark = L < np.percentile(L, 5)
            if dark.sum() < 50:
                dark = L < L.min() + 30
            px = s[dark]
            print(f"    {name:<14} n={len(px):6d}  "
                  f"mean RGB=({px[:,0].mean():.0f},{px[:,1].mean():.0f},"
                  f"{px[:,2].mean():.0f})  "
                  f"median=({np.median(px[:,0]):.0f},{np.median(px[:,1]):.0f},"
                  f"{np.median(px[:,2]):.0f})")
    # article page 76 body ink for comparison
    pg = d[5]
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72))
    a = np.array(Image.frombytes("RGB", (pix.width, pix.height),
                                 pix.samples).rotate(180)).astype(int)
    s = a[1600:2200, 700:1600]
    L = s.mean(2); px = s[L < np.percentile(L, 3)]
    print(f"  printed page 76 body ink  n={len(px)}  "
          f"mean RGB=({px[:,0].mean():.0f},{px[:,1].mean():.0f},{px[:,2].mean():.0f})")
    return True


# ------------------------------------------------------------ numerals ------
def cmd_numerals():
    import re, collections
    text = " ".join(t for _, t in TRANSCRIPT)
    nums = re.findall(r"\d[\d.,]*\d|\d", text)
    print(f"  every numeral token printed on page 72 ({len(nums)}):")
    print("   ", " ".join(nums))
    digits = "".join(c for c in text if c.isdigit())
    print(f"  total digit glyphs: {len(digits)}")
    c = collections.Counter(digits)
    print("  digit frequency: " + "  ".join(
        f"{k}:{c.get(str(k),0)}" for k in range(10)))
    print(f"  distinct digit glyphs used: {len(c)} of 10 "
          f"(missing: {sorted(set('0123456789')-set(c)) or 'none'})")
    # the statistics only, not the URLs / folio
    stats = [t for sec, t in TRANSCRIPT if sec in
             ("stat1", "stat2", "revenue", "market", "cagr", "digital")]
    snum = re.findall(r"\d[\d.,]*\d|\d", " ".join(stats))
    print(f"  numerals in the statistics blocks only ({len(snum)}): "
          f"{' '.join(snum)}")
    print(f"  their sum (as floats): {sum(float(x) for x in snum):,.2f}")
    return nums


def cmd_transcript():
    cur = None
    for sec, t in TRANSCRIPT:
        if sec != cur:
            print(f"\n  [{sec}]")
            cur = sec
        print(f"    {t}")
    n = sum(len(t) for _, t in TRANSCRIPT)
    print(f"\n  {len(TRANSCRIPT)} lines, {n} characters")


def main():
    ap = argparse.ArgumentParser()
    for f in ("all", "masks", "rule", "globes", "colour", "numerals",
              "transcript"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    run = [k for k in ("transcript", "masks", "rule", "globes", "colour",
                       "numerals") if getattr(a, k) or a.all]
    if not run:
        run = ["transcript"]
    for k in run:
        print(f"\n=== {k.upper()} ===")
        globals()["cmd_" + k]()


if __name__ == "__main__":
    main()
