#!/usr/bin/env python3
"""
All 45 highlight rectangles as a symbol sequence -- the half never swept.

WHAT WAS MISSING
`bar_geometry.py` measured the 22 ORANGE bars and `bargeom.txt` rendered their
widths as digits/hex/RLE (1,835,000 scripts, null). `highlight_color.py` swept
the colour stream. But the knockout bars are not colour-separable by the method
bar_geometry.py used (it says so at :93-107), so the geometry of the other 23
was never captured, and no file on disk held all 45 -- the scavenger measured
them, reported prose, and left `bars_final.tsv` in a scratch directory.

`bars45.tsv` is that measurement, imported: 26 orange, 13 black knockout, 6
white-on-brown, with rotated width/height/angle and ink fill per rectangle.

WHAT THIS SWEEPS
The 45-symbol sequence in print order, which is the reading `gen_candidates3.py`
H2 proposed ("highlights read as Morse via length") applied to the whole set
rather than the orange half: colour as a 3-symbol and 2-symbol stream (Bacon
both polarities, binary, Morse), widths and heights quantised and rendered as
digits/hex/RLE, the width sequence as BIP-39 indices, gaps between consecutive
bars, and the per-page groupings.

CAPACITY, STATED HONESTLY
45 symbols over a 3-letter alphabet is ~71 bits, and over 2 letters 45 bits --
both far below the 128 a key needs (window/channel_capacity.md). So this cannot
CARRY a key. It is swept because it could carry a pointer or a short passphrase,
and because leaving the measured half of a channel untested is how a project
convinces itself something is closed when it is not.
"""
import os, re

TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bars45.tsv")
A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def bars():
    """(page, colour, w, h, ang, fill) in print order."""
    out = []
    with open(TSV, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(hdr):
                continue
            out.append((int(p[ix["page"]]), p[ix["colour"]],
                        float(p[ix["rot_w"]]), float(p[ix["rot_h"]]),
                        float(p[ix["rot_ang"]]), float(p[ix["fill"]]),
                        float(p[ix["x0"]]), float(p[ix["y0"]])))
    out.sort(key=lambda b: (b[0], b[7], b[6]))
    return out


def _quant(vals, k):
    """Quantise to k levels by rank, so absolute px never matter."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    lab = [0] * len(vals)
    for rank, i in enumerate(order):
        lab[i] = min(k - 1, rank * k // len(vals))
    return lab


def forms():
    B = bars()
    out = []

    def add(t, v):
        v = (v or "").strip()
        if v:
            out.append((t, v))

    def variants(t, v):
        add(t, v)
        if v != v.lower():
            add(t + "/lower", v.lower())

    col = [b[1] for b in B]
    ws = [b[2] for b in B]
    hs = [b[3] for b in B]

    # colour as symbol streams
    m3 = {"orange": "0", "black": "1", "white": "2"}
    variants("colour/base3", "".join(m3[c] for c in col))
    variants("colour/letters", "".join({"orange": "O", "black": "B", "white": "W"}[c] for c in col))
    for name, one in (("orange", "orange"), ("black", "black"), ("white", "white")):
        bits = "".join("1" if c == one else "0" for c in col)
        variants(f"colour/bin_{name}", bits)
        add(f"colour/bin_{name}/inv", bits.translate(str.maketrans("01", "10")))
        # Bacon, both polarities
        for pol, tr in (("A", str.maketrans("01", "AB")), ("B", str.maketrans("01", "BA"))):
            s = bits.translate(tr)
            letters = []
            for i in range(0, len(s) - 4, 5):
                v = int(s[i:i + 5].replace("A", "0").replace("B", "1"), 2)
                letters.append(A[v] if v < 26 else "?")
            add(f"colour/bacon_{name}_{pol}", "".join(letters))
        # Morse: dot/dash with page breaks as separators
        mo = "".join("." if c == one else "-" for c in col)
        add(f"colour/morse_{name}", mo)

    # widths and heights, quantised
    for nm, seq in (("w", ws), ("h", hs)):
        for k in (2, 3, 4, 10):
            q = _quant(seq, k)
            variants(f"{nm}/q{k}", "".join(str(x) for x in q))
            if k == 2:
                bits = "".join(str(x) for x in q)
                letters = []
                for i in range(0, len(bits) - 4, 5):
                    v = int(bits[i:i + 5], 2)
                    letters.append(A[v] if v < 26 else "?")
                add(f"{nm}/q2/bacon", "".join(letters))
        add(f"{nm}/px", " ".join(str(int(round(x))) for x in seq))
        add(f"{nm}/px_nospace", "".join(str(int(round(x))) for x in seq))
        # run-length of the quantised binary
        q = "".join(str(x) for x in _quant(seq, 2))
        rle = [str(len(r)) for r in re.findall(r"0+|1+", q)]
        add(f"{nm}/rle", "".join(rle))
        add(f"{nm}/rle_sp", " ".join(rle))

    # width sequence as wordlist indices
    try:
        from mnemonic import Mnemonic
        for lang in ("english", "spanish", "french", "italian"):
            wl = Mnemonic(lang).wordlist
            for base in (0, 1):
                seq = [wl[(int(round(x)) - base) % 2048] for x in ws]
                for k in (12, 15, 18, 21, 24):
                    for i in range(0, len(seq) - k + 1):
                        add(f"w/{lang}/b{base}/w{k}@{i}", f"mn:{lang}:" + " ".join(seq[i:i + k]))
    except Exception:
        pass

    # gaps between consecutive bars on a page, and per-page groupings
    per = {}
    for b in B:
        per.setdefault(b[0], []).append(b)
    for pg, bs in sorted(per.items()):
        add(f"page{pg}/colour", "".join(m3[b[1]] for b in bs))
        add(f"page{pg}/count", str(len(bs)))
        gaps = [int(round(bs[i + 1][7] - bs[i][7])) for i in range(len(bs) - 1)]
        if gaps:
            add(f"page{pg}/gaps", "".join(str(g % 10) for g in gaps))
            add(f"page{pg}/gaps_sp", " ".join(str(g) for g in gaps))
    add("pages/counts", "".join(str(len(bs)) for _, bs in sorted(per.items())))
    add("total/count", str(len(B)))

    seen, uniq = set(), []
    for t, v in out:
        if v not in seen:
            seen.add(v)
            uniq.append((t, v))
    return uniq


def selftest():
    B = bars()
    got = {}
    for b in B:
        got[b[1]] = got.get(b[1], 0) + 1
    ok = len(B) == 45 and got.get("orange") == 26 and got.get("black") == 13 and got.get("white") == 6
    F = forms()
    tags = [t for t, _ in F]
    ok &= len(set(tags)) == len(tags) and all(v for _, v in F)
    ok &= len(dict(F)["colour/base3"]) == 45
    print(f"  {len(B)} bars ({got}), {len(F)} forms")
    print(f"  colour stream: {dict(F)['colour/base3']}")
    return bool(ok)


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
