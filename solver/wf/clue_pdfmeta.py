#!/usr/bin/env python3
"""
PDFMETA lens: everything the PDF container itself says about the scan.

    python3 wf/clue_pdfmeta.py            # all sections
    python3 wf/clue_pdfmeta.py A B C      # selected sections

Sections
  A  document-level metadata, trailer, catalog, object census, orphan check
  B  page tree: MediaBox/CropBox/Rotate/Annots/Resources per page
  C  the CANON_PFINF marker stream (TEXTON vs TEXTOFF)
  D  the illegal /Resources /Subtype plain-text OCR streams
  E  OCR text layer: exact char counts per PRINTED page (page-map corrected)
  F  OCR span geometry: per-span Tf size + Tm baseline, un-rotated
  G  declared ink colours: every `g`/`rg` before every `Do`
  H  image object dictionary census (filters, ImageMask, SMask, Decode)
  I  what the OCR layer holds that article_transcript.txt does not
"""
import os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF  = os.path.join(ROOT, "scan", "Scan1.pdf")
TRANS= os.path.join(ROOT, "article_transcript.txt")

# pdf page index -> printed page number (extract_scan.py:38)
PAGE_MAP = {0: 73, 1: 72, 2: 74, 3: 75, 4: 77, 5: 76, 6: 79, 7: 78}
PRINTED  = [PAGE_MAP[i] for i in range(8)]

import pymupdf


def doc():
    return pymupdf.open(PDF)


def raw():
    return open(PDF, "rb").read()


# ---------------------------------------------------------------- A
def sec_A():
    d = doc()
    print("== A. document level ==")
    print("pymupdf", pymupdf.version[0])
    print("file bytes", os.path.getsize(PDF))
    print("metadata", json.dumps(d.metadata))
    print("xref_length", d.xref_length(), "pages", d.page_count)
    print("is_form_pdf", d.is_form_pdf, "embfile_count", d.embfile_count(),
          "encrypted", d.is_encrypted, "has_links", d.has_links(),
          "has_annots", d.has_annots())
    print("xml_metadata(XMP) len", len(d.get_xml_metadata() or ""))
    print("toc entries", len(d.get_toc()))
    print("trailer:", " ".join(d.xref_object(-1).split()))
    b = raw()
    print("header", b[:9])
    print("'%%EOF' count", b.count(b"%%EOF"), " 'startxref' count",
          b.count(b"startxref"), " 'xref' count", b.count(b"\nxref"))
    print("Linearized present:", b"/Linearized" in b)
    for k in (b"/Metadata", b"/Annots", b"/AcroForm", b"/EmbeddedFile",
              b"/JavaScript", b"/OpenAction", b"/Names", b"/OCProperties",
              b"/Rotate", b"/CropBox", b"/SMask", b"/Decode", b"/Mask"):
        print(f"  raw occurrences of {k.decode():<15}", b.count(k))
    # object census + orphan check
    kinds = collections.Counter()
    streams = 0
    for i in range(1, d.xref_length()):
        o = d.xref_object(i, compressed=False)
        if d.xref_is_stream(i):
            streams += 1
        m = re.search(r"/Type\s*/(\w+)", o)
        sub = re.search(r"/Subtype\s*/(\w+)", o)
        if m:
            kinds[m.group(1) + ("/" + sub.group(1) if sub else "")] += 1
        elif o.strip().isdigit():
            kinds["<bare integer>"] += 1
        else:
            kinds["<untyped stream>"] += 1
    print("object census:", dict(kinds), " streams:", streams)
    # reachability from catalog
    seen, stack = set(), [2]
    while stack:
        n = stack.pop()
        if n in seen or not (0 < n < d.xref_length()):
            continue
        seen.add(n)
        o = d.xref_object(n, compressed=False)
        for r in re.findall(r"(\d+)\s+\d+\s+R", o):
            stack.append(int(r))
    allobj = set(range(1, d.xref_length()))
    print("reachable from /Root:", len(seen),
          " unreachable:", sorted(allobj - seen - {1}),
          "(1 = /Info, reached from trailer)")


# ---------------------------------------------------------------- B
def sec_B():
    d = doc()
    print("== B. page tree ==")
    print(f"{'idx':>3} {'printed':>7}  MediaBox  CropBox  Rotate  keys")
    for i in range(8):
        x = d[i].xref
        o = d.xref_object(x, compressed=False)
        keys = re.findall(r"^\s*/(\w+)", o, re.M)
        mb = d[i].mediabox
        cb = d[i].cropbox
        print(f"{i:>3} {PAGE_MAP[i]:>7}  {tuple(mb)} {tuple(cb)} "
              f"rot={d[i].rotation}  {sorted(set(keys))}")
        print("      Contents:", re.search(r"/Contents\s*\[([^\]]*)\]", o).group(1).strip())
        res = re.search(r"/Resources\s*<<(.*?)/ProcSet", o, re.S)
        print("      Resources keys:",
              re.findall(r"/(\w+)\s", res.group(1)) if res else None)


# ---------------------------------------------------------------- C
def sec_C():
    d = doc()
    print("== C. CANON_PFINF marker (first content stream of each page) ==")
    for i in range(8):
        o = d.xref_object(d[i].xref, compressed=False)
        refs = [int(t) for t in re.findall(r"(\d+)\s+\d+\s+R",
                 re.search(r"/Contents\s*\[([^\]]*)\]", o).group(1))]
        first = d.xref_stream(refs[0])
        print(f"  idx {i} printed {PAGE_MAP[i]}: contents={refs} "
              f"first={first!r} ({len(first)} bytes)")


# ---------------------------------------------------------------- D
def sec_D():
    d = doc()
    print("== D. /Resources /Subtype -> stream  (illegal key; plain-text OCR) ==")
    tot = 0
    for i in range(8):
        o = d.xref_object(d[i].xref, compressed=False)
        m = re.search(r"/Subtype\s+(\d+)\s+\d+\s+R", o)
        if not m:
            print(f"  idx {i} printed {PAGE_MAP[i]}: NO /Subtype key")
            continue
        x = int(m.group(1))
        lo = d.xref_get_key(x, "Length")
        b = d.xref_stream(x)
        tot += len(b)
        print(f"  idx {i} printed {PAGE_MAP[i]}: /Subtype {x} 0 R  "
              f"/Length {lo}  raw {len(b)} bytes  filter="
              f"{d.xref_get_key(x,'Filter')}")
        print("      head:", repr(b[:110]))
    print("  total plain-text bytes:", tot)
    print("\n  -- does it equal page.get_text()? --")
    for i in range(8):
        o = d.xref_object(d[i].xref, compressed=False)
        m = re.search(r"/Subtype\s+(\d+)\s+\d+\s+R", o)
        sub = d.xref_stream(int(m.group(1))).decode("cp1252") if m else ""
        gt = d[i].get_text()
        print(f"  idx {i} printed {PAGE_MAP[i]}: subtype {len(sub)} chars, "
              f"get_text {len(gt)} chars, identical={sub==gt}, "
              f"same-after-strip={sub.strip()==gt.strip()}, "
              f"set-equal={sorted(sub.split())==sorted(gt.split())}")


# ---------------------------------------------------------------- E
def sec_E():
    d = doc()
    print("== E. OCR text layer, exact counts, PAGE-MAP CORRECTED ==")
    rows = []
    for i in range(8):
        t = d[i].get_text()
        rows.append((PAGE_MAP[i], i, len(t), len(t.replace("\n", "")),
                     t.count("\n"), sum(1 for c in t if ord(c) > 127),
                     sorted({hex(ord(c)) for c in t if ord(c) > 127})))
    print(f"{'printed':>7} {'pdfidx':>6} {'chars':>6} {'nonNL':>6} "
          f"{'lines':>5} {'non-ascii':>9}  codes")
    for p, i, n, nn, nl, na, cs in sorted(rows):
        print(f"{p:>7} {i:>6} {n:>6} {nn:>6} {nl:>5} {na:>9}  {cs}")
    print("\n  naive map (printed = 72 + pdf_index) would report:")
    for i in range(8):
        print(f"      printed {72+i} -> {len(d[i].get_text())} chars "
              f"(TRUE page for that count is {PAGE_MAP[i]})")


# ---------------------------------------------------------------- F
SPAN = re.compile(rb"/F3\s+([\d.]+)\s+Tf|1 0 0 1 ([\d.]+) ([\d.]+) Tm\s*<([0-9A-Fa-f]*)>\s*Tj")


def spans(d, i):
    """(size, x, y, hexpayload) per Tj, in the PDF's own (rotated) frame."""
    o = d.xref_object(d[i].xref, compressed=False)
    refs = [int(t) for t in re.findall(r"(\d+)\s+\d+\s+R",
             re.search(r"/Contents\s*\[([^\]]*)\]", o).group(1))]
    buf = b"".join(d.xref_stream(r) for r in refs)
    out, cur = [], None
    for m in SPAN.finditer(buf):
        if m.group(1):
            cur = float(m.group(1))
        else:
            out.append((cur, float(m.group(2)), float(m.group(3)),
                        bytes.fromhex(m.group(4).decode())))
    return out


def sec_F():
    d = doc()
    print("== F. OCR span geometry (Tf size + Tm baseline), un-rotated ==")
    allsz = collections.Counter()
    for i in range(8):
        s = spans(d, i)
        if not s:
            print(f"  printed {PAGE_MAP[i]} (idx {i}): 0 spans")
            continue
        sz = [a for a, *_ in s]
        allsz.update(sz)
        # un-rotate 180deg: x' = 612 - x, y' = 792 - y
        xs = [612 - x for _, x, _, _ in s]
        ys = [792 - y for _, _, y, _ in s]
        print(f"  printed {PAGE_MAP[i]} (idx {i}): {len(s)} spans, "
              f"{sum(len(p) for *_ ,p in s)} glyph bytes, "
              f"Tf {min(sz)}-{max(sz)}pt ({len(set(sz))} distinct), "
              f"x {min(xs):.1f}-{max(xs):.1f}pt  y {min(ys):.1f}-{max(ys):.1f}pt")
    print("  document-wide Tf histogram (pt: spans):")
    print("   ", dict(sorted(allsz.items())))
    steps = sorted(allsz)
    diffs = sorted({round(b - a, 3) for a, b in zip(steps, steps[1:])})
    print("  distinct gaps between adjacent sizes:", diffs)


# ---------------------------------------------------------------- G
DO = re.compile(rb"q\s*\n(?:([\d.]+)\s+g|([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg)?\s*\n?"
                rb"([\d.]+)\s+0\s+0\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+cm\s*\n"
                rb"/Obj(\d+)\s+Do")


def sec_G():
    d = doc()
    print("== G. declared ink colour per placed XObject ==")
    print(f"{'printed':>7} {'xref':>5} {'w x h (px)':>13} {'placed pt':>15} "
          f"{'declared colour':>22}  sRGB")
    for i in range(8):
        o = d.xref_object(d[i].xref, compressed=False)
        refs = [int(t) for t in re.findall(r"(\d+)\s+\d+\s+R",
                 re.search(r"/Contents\s*\[([^\]]*)\]", o).group(1))]
        buf = b"".join(d.xref_stream(r) for r in refs)
        for m in DO.finditer(buf):
            g, r_, g_, b_, w, h, x, y, xr = m.groups()
            xr = int(xr)
            if g:
                v = float(g); col = f"{v:.3f} g"; rgb = tuple([round(v*255)]*3)
            elif r_:
                v = (float(r_), float(g_), float(b_))
                col = f"{v[0]:.3f} {v[1]:.3f} {v[2]:.3f} rg"
                rgb = tuple(round(c*255) for c in v)
            else:
                col = "(inherited)"; rgb = None
            W = d.xref_get_key(xr, "Width")[1]
            H = d.xref_get_key(xr, "Height")[1]
            cls = ""
            if rgb:
                import colorsys
                hh, ll, ss = colorsys.rgb_to_hls(*[c/255 for c in rgb])
                hue, sat = round(hh*360), round(ss, 3)
                cls = ("NEUTRAL" if sat < 0.12 else
                       "ORANGE" if 15 <= hue <= 45 else
                       "PINK/MAGENTA" if (hue >= 300 or hue < 15) else
                       f"OTHER h={hue}")
                cls = f"h={hue:>3} s={sat:<5} {cls}"
            print(f"{PAGE_MAP[i]:>7} {xr:>5} {W+'x'+H:>13} "
                  f"{float(w):>7.2f}x{float(h):<7.2f} {col:>22}  {str(rgb):>16} {cls}")


# ---------------------------------------------------------------- H
def sec_H():
    d = doc()
    print("== H. image object census ==")
    print(f"{'xref':>5} {'printed':>7} {'w':>5} {'h':>5} {'bpc':>3} "
          f"{'colorspace':>10} {'filter':>26} {'mask':>5} {'len':>8}")
    owner = {}
    for i in range(8):
        for x in d[i].get_images(full=True):
            owner.setdefault(x[0], PAGE_MAP[i])
    for xr in sorted(owner):
        g = lambda k: (d.xref_get_key(xr, k) or ("", ""))[1]
        print(f"{xr:>5} {owner[xr]:>7} {g('Width'):>5} {g('Height'):>5} "
              f"{g('BitsPerComponent'):>3} {g('ColorSpace') or '-':>10} "
              f"{g('Filter'):>26} {g('ImageMask') or '-':>5} {g('Length'):>8}")
    filt = collections.Counter((d.xref_get_key(x, "Filter") or ("",""))[1]
                               for x in owner)
    print("  filter histogram:", dict(filt))
    for k in ("SMask", "Decode", "Mask", "Interpolate", "Intent"):
        n = sum(1 for x in owner if (d.xref_get_key(x, k) or ("null",))[0] != "null")
        print(f"  images carrying /{k}: {n}")


# ---------------------------------------------------------------- I
def unrot(s):
    """Reverse the string; OCR read the page upside down."""
    return s[::-1]


def sec_I():
    d = doc()
    print("== I. OCR content vs article_transcript.txt ==")
    tr = open(TRANS, encoding="utf-8", errors="replace").read()
    trlow = re.sub(r"[^a-z0-9]+", "", tr.lower())
    for i in range(8):
        t = d[i].get_text()
        if not t.strip():
            print(f"  printed {PAGE_MAP[i]}: EMPTY text layer")
            continue
        rev = unrot(t)
        # tokens of >=4 alnum chars that survive the upside-down read
        toks = [w for w in re.findall(r"[A-Za-z0-9./:_-]{5,}", rev)]
        hits = [w for w in toks
                if re.sub(r"[^a-z0-9]+", "", w.lower()) and
                   re.sub(r"[^a-z0-9]+", "", w.lower()) in trlow]
        print(f"  printed {PAGE_MAP[i]}: {len(t)} chars, {len(toks)} reversed "
              f"tokens>=5, {len(hits)} of them literally present in the "
              f"transcript")
        if hits[:12]:
            print("      e.g.", hits[:12])



# ---------------------------------------------------------------- J
def sec_J():
    """Stream compression census: what is greppable in the raw file."""
    d = doc()
    print("== J. stream storage: plaintext vs compressed ==")
    import collections as _c
    cen = _c.Counter()
    unf, fl = [], []
    for i in range(1, d.xref_length()):
        if not d.xref_is_stream(i):
            continue
        f = (d.xref_get_key(i, "Filter") or ("null", "null"))
        cen[f[1]] += 1
        if f[0] == "null":
            unf.append(i)
        elif f[1] == "/FlateDecode":
            fl.append(i)
    print("  filter census over all streams:", dict(cen))
    print(f"  UNFILTERED (plaintext) streams: {unf}")
    print(f"     total raw bytes: {sum(len(d.xref_stream(i)) for i in unf)}")
    print(f"  FlateDecode-only streams (the per-page graphics streams): {fl}")
    b = raw()
    print("  byte-grep of the raw PDF:")
    for tok in (b"ESOCTtTE", b"rasTex xEn", b" cm", b" rg", b" Do", b"Tj",
                b"0.988 0.533 0.251 rg"):
        print(f"     {tok!r:<26} {b.count(tok)}")
    print("  => OCR text is plaintext and greppable; every placement matrix")
    print("     and every declared ink colour is inside the 8 Flate streams")
    print("     and is invisible to strings/grep.")


# ---------------------------------------------------------------- K
def sec_K():
    """Orange ink: JPEG colour layer alone vs composited page."""
    import numpy as np, io
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    d = doc()
    print("== K. orange ink, colour layer vs composite ==")
    def om(a):
        R = a[:, :, 0].astype(int); G = a[:, :, 1].astype(int)
        B = a[:, :, 2].astype(int)
        return ((R > 150) & (G > 40) & (G < 175) & (B < 110) & (R - B > 70))
    print(f"{'printed':>7} {'colour-layer px':>16} {'composite px':>13} {'delta':>8}")
    for i in range(8):
        xr = [x[0] for x in d[i].get_images(full=True)]
        col = [x for x in xr
               if (d.xref_get_key(x, "ColorSpace") or ("", ""))[1] == "/DeviceRGB"][0]
        a = np.array(Image.open(io.BytesIO(d.extract_image(col)["image"]))
                     .convert("RGB"))
        n1 = int(om(a).sum())
        pix = d[i].get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72))
        b = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n)[:, :, :3]
        n2 = int(om(b).sum())
        print(f"{PAGE_MAP[i]:>7} {n1:>16} {n2:>13} {n2-n1:>8}")


# ---------------------------------------------------------------- L
def sec_L():
    """Scanner's own block segmentation (the /Subtype copy) vs get_text."""
    d = doc()
    print("== L. line/block segmentation, two plaintext copies ==")
    print(f"{'printed':>7} {'/Subtype lines':>15} {'get_text lines':>15} {'Tj spans':>9}")
    for i in range(8):
        o = d.xref_object(d[i].xref, compressed=False)
        m = re.search(r"/Subtype\s+(\d+)\s+\d+\s+R", o)
        sub = d.xref_stream(int(m.group(1))).decode("cp1252") if m else ""
        gt = d[i].get_text()
        print(f"{PAGE_MAP[i]:>7} {sub.count(chr(10)):>15} {gt.count(chr(10)):>15} "
              f"{len(spans(d,i)):>9}")


SECTIONS = dict(A=sec_A, B=sec_B, C=sec_C, D=sec_D, E=sec_E,
                F=sec_F, G=sec_G, H=sec_H, I=sec_I,
                J=sec_J, K=sec_K, L=sec_L)

if __name__ == "__main__":
    want = [a.upper() for a in sys.argv[1:]] or list(SECTIONS)
    for k in want:
        SECTIONS[k]()
        print()
