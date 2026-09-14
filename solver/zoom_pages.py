#!/usr/bin/env python3
"""
Regenerate the page crops behind window/reading_the_pages_myself.md.

The claims in that document -- that p79's baseline curves, that bold appears as
contiguous runs rather than word alternation, that the p77 passage is tracked
out to justify -- are claims about what the pages LOOK like. They are only
checkable if the exact crops are reproducible, so the coordinates live here
rather than in a shell history.

The crops themselves are ~9 MB of derived PNG and are gitignored. The source
images are in the repository; this script is the method.

  python3 zoom_pages.py            # writes zoom/*.png
  python3 zoom_pages.py --list     # just print what would be made
"""
import argparse, os, sys

IMG = "/home/user/overdose/public/images"

# (name, source image, crop box in ORIGINAL pixel coords, scale, what it shows)
CROPS = [
    ("p79_closing", "IMG_6250.jpeg", (430, 1580, 1680, 1830), 3,
     "the closing block: bold runs, not word alternation"),
    ("p79_rabbit", "IMG_6250.jpeg", (430, 1290, 1680, 1480), 3,
     "'Bitcoin rabbit hole' bold, and the 1969 bed-in reference"),
    ("p79_curve_a", "IMG_6250.jpeg", (330, 690, 1700, 960), 2,
     "curved baseline, upper half of the arc"),
    ("p79_curve_b", "IMG_6250.jpeg", (330, 940, 1700, 1180), 2,
     "curved baseline; the bold run ENDS mid-line at 'connect'"),
    ("p78_warmongers", "IMG_6249.jpeg", (300, 1420, 1620, 1500), 3,
     "'The warmongers will start mining bitcoin for sure.' in display size -- "
     "the clearest apparent word-level bold, which is the font"),
    ("p78_genesis", "IMG_6249.jpeg", (300, 1490, 1620, 1650), 3,
     "'right there in the Genesis Block', set as a right-aligned staircase"),
    ("p77_tracked", "IMG_6248.jpeg", (560, 1760, 1680, 1990), 2.6,
     "the letter-tracked passage -- justification, flush to both margins"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="zoom")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for n, src, box, s, why in CROPS:
            print(f"{n:18} {src}  {box}  x{s}\n{'':18} {why}")
        return
    from PIL import Image
    os.makedirs(a.out, exist_ok=True)
    for n, src, box, s, why in CROPS:
        p = os.path.join(IMG, src)
        if not os.path.exists(p):
            sys.stderr.write(f"  {n}: missing {p}\n")
            continue
        im = Image.open(p).crop(box)
        im = im.resize((int(im.width * s), int(im.height * s)),
                       Image.LANCZOS)
        out = os.path.join(a.out, n + ".png")
        im.save(out)
        sys.stderr.write(f"  {out}  {im.size}  {why}\n")


if __name__ == "__main__":
    main()
