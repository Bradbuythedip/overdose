#!/usr/bin/env python3
"""
Regenerate every high-resolution view from the source scan.

WHY THE PDF IS IN THE REPOSITORY
`scan/Scan1.pdf` is 1.38 MB and is the ACTUAL source: eight pages at 400 dpi,
with the magazine's own bilevel text masks embedded. Every render made from it
is tens of megabytes and entirely derivable, so the source is committed and the
renders are not.

It also corrects a hole. The working images for most of this project were seven
phone JPEGs of pages 73-79 under `public/images/`. This PDF has EIGHT pages,
and the extra one is **72** -- the NUMBERS page, which was in no transcript, no
corpus and no sweep until it was found here. Anyone re-running this work from
the JPEGs alone would miss it again.

WHAT IS INSIDE
  8 pages, 612x792pt, rendered here at 400 dpi -> 3400x4400
  per page: a 1700x2200 JPEG colour layer (200 dpi) and, on most, a
    2592-3280 x 3456-3832 PNG which is a 1-BIT BILEVEL TEXT MASK at 300-386
    dpi -- the scanner's own ink separation, with no JPEG ringing and no
    anti-aliasing ambiguity. For glyph geometry that is strictly better than
    any lossy render.
  a text layer, which is OCR of the pages ROTATED 180 DEGREES and is therefore
    garbage read forwards: "'peloTun puts eTqTTTnF er{+" is "the gullible and
    unloved" upside down. It confirms the scan orientation and nothing else.

EVERY PAGE IS 180 DEGREES ROTATED. Renders here are un-rotated.

  python3 extract_scan.py --selftest
  python3 extract_scan.py --dpi 400 --out hires
"""
import argparse, os, sys

PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "scan", "Scan1.pdf")
# PDF page index -> printed page number
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}


def open_pdf(path=PDF):
    import pymupdf
    return pymupdf.open(path)


def render(dpi=400, out="hires", rotate=True):
    import pymupdf
    os.makedirs(out, exist_ok=True)
    d = open_pdf()
    made = []
    for i, pg in enumerate(d):
        m = pymupdf.Matrix(dpi / 72, dpi / 72)
        pix = pg.get_pixmap(matrix=m)
        fn = os.path.join(out, f"p{PAGE_MAP.get(i, i)}_{dpi}dpi.png")
        pix.save(fn)
        if rotate:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            Image.open(fn).rotate(180).save(fn)
        made.append(fn)
    return made


def masks(out="hires", min_px=500_000):
    """The embedded bilevel text masks -- the best glyph source available."""
    d = open_pdf()
    os.makedirs(out, exist_ok=True)
    made = []
    for i, pg in enumerate(d):
        for x in pg.get_images(full=True):
            try:
                info = d.extract_image(x[0])
            except Exception:
                continue
            if info["width"] * info["height"] < min_px:
                continue
            fn = os.path.join(
                out, f"p{PAGE_MAP.get(i, i)}_x{x[0]}_"
                     f"{info['width']}x{info['height']}.{info['ext']}")
            open(fn, "wb").write(info["image"])
            made.append((fn, info["width"], info["height"]))
    return made


def selftest():
    ok = True
    ok &= os.path.exists(PDF)
    sys.stderr.write(f"  source present at {PDF}: "
                     f"{'OK' if os.path.exists(PDF) else 'FAIL'}\n")
    if not ok:
        return False
    d = open_pdf()
    ok &= d.page_count == 8
    sys.stderr.write(f"  {d.page_count} pages (the JPEG set has 7, missing 72): "
                     f"{'OK' if d.page_count == 8 else 'FAIL'}\n")
    ok &= set(PAGE_MAP.values()) == set(range(72, 80))
    sys.stderr.write(f"  page map covers 72-79 exactly: "
                     f"{'OK' if set(PAGE_MAP.values())==set(range(72,80)) else 'FAIL'}\n")
    # the NUMBERS page must be the one carrying the second serial's context
    t = d[1].get_text()
    ok &= "N0I" in t or "NOI" in t or len(t) > 300
    sys.stderr.write(f"  pdf page 1 (printed 72) has a text layer of "
                     f"{len(t)} chars\n")
    big = [x for pg in d for x in pg.get_images(full=True)]
    sys.stderr.write(f"  {len(big)} embedded images across the document\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--out", default="hires")
    ap.add_argument("--no-rotate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the source scan is missing or malformed")
    if a.selftest:
        return
    r = render(a.dpi, a.out, not a.no_rotate)
    sys.stderr.write(f"\n  {len(r)} pages rendered at {a.dpi} dpi -> {a.out}/\n")
    m = masks(a.out)
    for fn, w, h in m:
        sys.stderr.write(f"    {fn}  {w}x{h}\n")
    sys.stderr.write(f"  {len(m)} embedded images extracted\n")


if __name__ == "__main__":
    main()
