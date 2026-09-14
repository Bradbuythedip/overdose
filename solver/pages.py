#!/usr/bin/env python3
"""
The single source of page images: scan/Scan1.pdf. No phone photos.

WHY THE PHOTOS ARE GONE
The seven IMG_6244..6250.jpeg files were camera photographs of pages 73-79:
sequential IMG_ filenames, per-page varying widths (1792-1870 px, which a
flatbed cannot produce), nominal 72 dpi, identical quantization tables, camera
make and model stripped. Effective resolution about 215 dpi.

The scan strictly dominates them on every axis:

  photos                          scan/Scan1.pdf
  ------                          --------------
  7 pages (73-79)                 8 pages (72-79) -- page 72 exists ONLY here
  ~215 dpi, lossy, JPEG ringing   400.0 dpi bilevel ink separation, CCITT G4,
                                    lossless; plus a 200 dpi colour wash layer
  camera perspective + uneven     flatbed, even illumination, no keystone
    lighting + focus variation
  text and wash mixed             text and wash SEPARATED by the scanner

Measured consequence: per-word bold ratios are 1.00/1.01/1.03/0.98 at 400 dpi
against 1.10/1.20/1.21/1.08 on the photos. The higher resolution makes the null
flatter, i.e. the residual clustering the photos showed was an artifact of the
source. Anything measured on the photos is measured on noise the scan does not
have.

USE
    import pages
    p = pages.page_path(76)              # 400 dpi PNG, rendered and cached
    p = pages.page_path(76, dpi=600)
    m = pages.mask_path(76)              # 400 dpi 1-bit ink separation, or None
    for n, p in pages.all_pages().items(): ...

Rendered pages are cached under /tmp/overdose_pages and regenerate on demand,
so nothing large is committed.

NOTE ON POLARITY: the bilevel masks store ink as the LIGHT class (about 6% of
pixels). Code that assumes `pixel < 128 == ink` inverts them.

  python3 pages.py --selftest
"""
import os, sys

SOLVER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SOLVER)
PDF = os.path.join(SOLVER, "scan", "Scan1.pdf")
CACHE = os.environ.get("OVERDOSE_PAGE_CACHE", "/tmp/overdose_pages")

# pdf page index -> printed page number. The scan is NOT in printed order:
# the sheets were fed in swapped pairs.
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
PRINTED = {v: k for k, v in PAGE_MAP.items()}

# printed page -> xref of its full-page 1-bit ink separation, where one exists.
# 74 and 77 have none: 74 is the full-bleed photograph, 77 is printed white on
# dark brown so there was no black-on-white layer to separate.
MASK_XREF = {72: 17, 73: 5, 75: 35, 76: 50, 78: 74, 79: 60}


def _doc():
    import pymupdf
    if not os.path.exists(PDF):
        raise FileNotFoundError(
            f"{PDF} missing. It is the only page source; the phone photos were "
            "removed deliberately (see this module's docstring).")
    return pymupdf.open(PDF)


def page_path(printed, dpi=400, force=False):
    """Path to a rendered, un-rotated PNG of the given printed page."""
    if printed not in PRINTED:
        raise KeyError(f"page {printed} is not in the scan; it covers "
                       f"{min(PRINTED)}-{max(PRINTED)}")
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"p{printed}_{dpi}dpi.png")
    if os.path.exists(out) and not force:
        return out
    d = _doc()
    pg = d[PRINTED[printed]]
    pix = pg.get_pixmap(dpi=dpi)
    from PIL import Image
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im = im.rotate(180)          # the scan is 180 degrees rotated
    im.save(out)
    return out


def mask_path(printed, force=False):
    """Path to the 400 dpi 1-bit ink separation, or None if the page has none."""
    if printed not in MASK_XREF:
        return None
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"p{printed}_mask.png")
    if os.path.exists(out) and not force:
        return out
    import io
    from PIL import Image
    d = _doc()
    info = d.extract_image(MASK_XREF[printed])
    im = Image.open(io.BytesIO(info["image"])).convert("L").rotate(180)
    im.save(out)
    return out


def all_pages(dpi=400):
    return {n: page_path(n, dpi) for n in sorted(PRINTED)}


def selftest():
    ok = True
    d = _doc()
    good = d.page_count == 8
    print(f"  pdf has 8 pages: {'OK' if good else 'FAIL'} ({d.page_count})")
    ok &= good
    good = set(PAGE_MAP.values()) == set(range(72, 80))
    print(f"  map covers 72-79: {'OK' if good else 'FAIL'}")
    ok &= good
    good = not any(f.startswith("IMG_62") for f in os.listdir(ROOT))
    print(f"  no phone photos at repo root: {'OK' if good else 'FAIL'}")
    ok &= good
    p = page_path(72, dpi=150)
    from PIL import Image
    im = Image.open(p)
    good = im.width > 1000 and im.height > 1200
    print(f"  page 72 renders: {'OK' if good else 'FAIL'} ({im.size})")
    ok &= good
    m = mask_path(75)
    good = m is not None and os.path.exists(m)
    print(f"  page 75 mask extracts: {'OK' if good else 'FAIL'}")
    ok &= good
    good = mask_path(77) is None
    print(f"  page 77 correctly has no mask: {'OK' if good else 'FAIL'}")
    ok &= good
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    for n, p in all_pages().items():
        print(n, p)
