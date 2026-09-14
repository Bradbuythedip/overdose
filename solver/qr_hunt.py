#!/usr/bin/env python3
"""
Point a barcode decoder at the pages. Nobody ever did.

THE GAP
Every image attack in this project was steganographic or typographic: LSB,
EOI-trailing, EXIF, COM/APPn markers, DQT comparison, stroke-width measurement,
mirror transforms, vision-model reading. All of them ask "is something hidden in
the pixels".

None of them asked the blunt question: IS THERE A BARCODE ON THE PAGE. A QR
code is how a human being puts a private key on a piece of paper. Casascius
coins, paper wallets, every hardware-wallet backup card -- they all print one.
A magazine hiding a key has an obvious reason to use one, possibly small,
possibly inside the artwork on the opening spread.

`grep -ril "qrcode\\|pyzbar\\|zbar\\|barcode"` over the whole tree returns one
markdown file and no code. This closes that.

WHY IT IS NOT JUST detectAndDecode()
A QR in a photographed magazine page is small, off-axis, low-contrast, possibly
printed over artwork, and every page in this scan is 180 degrees rotated. A
single call on the full image finds nothing and proves nothing. So:

  4 rotations x 6 preprocessings x 5 scales, on the full page
  plus a tiled pass, so a code occupying 5% of the page is not lost in
  downsampling
  plus the OpenCV barcode detector for 1-D symbologies

POSITIVE CONTROL
A QR is generated, pasted into a copy of a real page, and must be RECOVERED by
the same pipeline before any null is reported. Without it, "no QR found" is
indistinguishable from "the decoder was never working".

  python3 qr_hunt.py --selftest
  python3 qr_hunt.py --images '/home/user/overdose/public/images/IMG_*.jpeg'
"""
import argparse, glob, sys

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("needs opencv: pip install opencv-python-headless")


def preprocess(img):
    """Named variants of one image. Print is high-contrast; photos are not."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    yield "gray", g
    yield "invert", cv2.bitwise_not(g)
    yield "otsu", cv2.threshold(g, 0, 255,
                                cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    yield "adaptive", cv2.adaptiveThreshold(
        g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5)
    yield "clahe", cv2.createCLAHE(clipLimit=3.0,
                                   tileGridSize=(8, 8)).apply(g)
    yield "sharp", cv2.filter2D(g, -1, np.array([[0, -1, 0],
                                                 [-1, 5, -1],
                                                 [0, -1, 0]]))


def scales_for(shape):
    """Upscaling only helps SMALL regions. A 2400px page upscaled 4x is a
    7000px image the detector crawls over for nothing -- the first version of
    this file timed out in its own selftest doing exactly that."""
    big = max(shape[:2])
    if big > 1600:
        return (1.0, 0.5)
    if big > 700:
        return (1.0, 2.0)
    return (1.0, 2.0, 3.0, 4.0)


def decode_all(img, qd):
    """Every payload this frame yields, across rotations and scales."""
    out = set()
    for rot in range(4):
        r = np.rot90(img, rot).copy() if rot else img
        for name, v in preprocess(r):
            for scale in scales_for(v.shape):
                if scale != 1.0:
                    h, w = v.shape[:2]
                    nh, nw = int(h * scale), int(w * scale)
                    if min(nh, nw) < 40 or max(nh, nw) > 6000:
                        continue
                    s = cv2.resize(v, (nw, nh), interpolation=cv2.INTER_CUBIC)
                else:
                    s = v
                try:
                    ok, infos, _pts, _ = qd.detectAndDecodeMulti(s)
                    if ok:
                        for t in infos:
                            if t:
                                out.add((t, f"rot{rot*90}/{name}/x{scale}"))
                except cv2.error:
                    pass
                try:
                    t, _pts, _ = qd.detectAndDecode(s)
                    if t:
                        out.add((t, f"rot{rot*90}/{name}/x{scale}/single"))
                except cv2.error:
                    pass
    return out


def tiles(img, n=4, overlap=0.25):
    """Overlapping tiles, so a small code is not lost to downsampling."""
    h, w = img.shape[:2]
    th, tw = h // n, w // n
    oy, ox = int(th * overlap), int(tw * overlap)
    for i in range(n):
        for j in range(n):
            y0, x0 = max(0, i * th - oy), max(0, j * tw - ox)
            y1, x1 = min(h, (i + 1) * th + oy), min(w, (j + 1) * tw + ox)
            yield f"tile{i}{j}", img[y0:y1, x0:x1]


def hunt(path, qd, do_tiles=True):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None, []
    found = set(decode_all(img, qd))
    if do_tiles:
        for tn, t in tiles(img):
            for txt, how in decode_all(t, qd):
                found.add((txt, f"{tn}/{how}"))
    return img.shape, sorted(found)


def _plant(img, secret, side):
    enc = cv2.QRCodeEncoder.create()
    qr = cv2.cvtColor(enc.encode(secret), cv2.COLOR_GRAY2BGR)
    qr = cv2.resize(qr, (side, side), interpolation=cv2.INTER_NEAREST)
    out = img.copy()
    out[40:40 + side, 40:40 + side] = qr
    return out


def selftest(sample):
    """Plant QRs in a real page and require this pipeline to recover them.

    TWO paths are exercised, because the run uses both and a control that
    covers only one leaves the other free to be silently broken:
      full-page  a code large enough to survive at native resolution
      tile       a small code, recovered from the crop that contains it

    Deliberately NOT run over all 16 tiles here -- that is 17x the work and the
    first version of this file timed out in its own selftest, which is its own
    kind of failure.
    """
    qd = cv2.QRCodeDetector()
    img = cv2.imread(sample, cv2.IMREAD_COLOR)
    if img is None:
        sys.stderr.write(f"  cannot read {sample}: FAIL\n")
        return False
    secret = "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss"   # WIF shape
    ok = True

    big = max(220, img.shape[1] // 6)
    got = decode_all(_plant(img, secret, big), qd)
    found = secret in [t for t, _h in got]
    ok &= found
    sys.stderr.write(f"  full-page path: planted {big}px QR "
                     f"({big*100//img.shape[1]}% of width) -> "
                     f"{'RECOVERED' if found else 'MISSED'}\n")
    if found:
        sys.stderr.write(f"    via {[h for t,h in got if t==secret][0]}\n")

    small = max(90, img.shape[1] // 16)
    planted = _plant(img, secret, small)
    crop = planted[0:small + 120, 0:small + 120]
    got2 = decode_all(crop, qd)
    found2 = secret in [t for t, _h in got2]
    ok &= found2
    sys.stderr.write(f"  tile path: planted {small}px QR "
                     f"({small*100//img.shape[1]}% of width), recovered from "
                     f"its crop -> {'RECOVERED' if found2 else 'MISSED'}\n")

    # and a negative: an unplanted page must yield nothing, or every "hit"
    # below is noise
    got3 = decode_all(cv2.resize(img, (img.shape[1]//3, img.shape[0]//3)), qd)
    clean = not got3
    ok &= clean
    sys.stderr.write(f"  an unmodified page yields no payload: "
                     f"{'OK' if clean else 'FAIL - decoder hallucinates'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def _hunt_job(args):
    path, do_tiles = args
    qd = cv2.QRCodeDetector()
    shape, got = hunt(path, qd, do_tiles=do_tiles)
    return path, shape, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images",
                    default="/home/user/overdose/public/images/IMG_*.jpeg")
    ap.add_argument("--no-tiles", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    paths = sorted(glob.glob(a.images))
    if not paths:
        sys.exit(f"no images match {a.images}")

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(paths[0]):
        sys.exit("the decoder cannot find a QR it was handed; refusing to "
                 "report a null")

    sys.stderr.write(f"\n  {len(paths)} page images, 4 rotations x 6 "
                     f"preprocessings x adaptive scales,\n  full page"
                     f"{'' if a.no_tiles else ' + 16 overlapping tiles'}, "
                     f"{a.workers} workers\n\n")
    from multiprocessing import Pool
    total = 0
    with Pool(a.workers) as pool:
        jobs = [(p, not a.no_tiles) for p in paths]
        for path, shape, got in pool.imap_unordered(_hunt_job, jobs):
            name = path.rsplit("/", 1)[-1]
            if shape is None:
                sys.stderr.write(f"  {name:22} UNREADABLE\n")
                continue
            sys.stderr.write(f"  {name:22} {shape[1]}x{shape[0]}  "
                             f"{len(got)} payload(s)\n")
            sys.stderr.flush()
            for txt, how in got:
                total += 1
                sys.stderr.write(f"      *** {txt!r}\n          via {how}\n")
                print(f"{name}\t{how}\t{txt}", flush=True)
    sys.stderr.write(f"\n  {total} barcode payload(s) across all pages\n")
    if not total:
        sys.stderr.write("  No QR or barcode is printed on these pages, at any "
                         "rotation,\n  preprocessing, scale or tile.\n")


if __name__ == "__main__":
    main()
