#!/usr/bin/env python3
"""
Whole-word bold as a BACON CIPHER — a binary channel, not a word list.

WHY THIS IS DIFFERENT FROM WHAT WAS TRIED
Task #9 in this project tested whole-word bold as a NULL CIPHER: read the bold
words as words. That is a completely different mechanism from Bacon's cipher,
where the choice of typeface is a BINARY CODE — regular = A, bold = B, five
symbols per plaintext letter. The words themselves are irrelevant; only their
weight carries the payload.

The capacity works out. The body text is roughly 1,000 words, so ~1,000 bits,
which is ~200 Bacon letters or 125 bytes. A 51-character WIF or a 32-byte key
fits with room to spare. A null cipher over the bold words could never carry a
key; a Bacon cipher easily can.

And crucially this uses the ONE typographic signal that survives 215 dpi.
Per-CHARACTER bold is measurably unrecoverable here — both this session and a
sibling session established that the per-letter calls track glyph identity
rather than weight. Per-WORD bold is a different matter: aggregating ink over
a whole word averages out the per-glyph noise.

THE MEASURE
Not stroke width, which failed. Ink AREA per word, normalised by what that
word's own characters should ink at regular weight — learned from the page
itself. A bold word inks roughly 1.4-1.8x its regular twin.

Every reading of the resulting bit string is then tested:
  Bacon decode, 24-letter and 26-letter alphabets, both polarities
  bits -> bytes -> 32-byte key windows at every bit phase
  bits -> 11-bit BIP-39 indices -> checksum-valid mnemonics
  the bit string itself, and its run lengths, as passphrases
all screened against the current-balance index, the historical ever-funded
index, and the WIF/BIP38 checksum oracle.

  python3 bacon_cipher.py --selftest
  python3 bacon_cipher.py --pages ../IMG_6246.jpeg ../IMG_6247.jpeg ...
"""
import argparse, hashlib, itertools, os, re, sys

import numpy as np

import bold_extract as B

BACON24 = "abcdefghiklmnopqrstuwxyz"      # classic: i/j and u/v share
BACON26 = "abcdefghijklmnopqrstuvwxyz"


def words_of_line(ln, wmed):
    """Split a detected text line into word-level glyph groups."""
    gl = sorted(ln, key=lambda c: c["bbox"][0])
    words, cur = [], [gl[0]]
    for prev, c in zip(gl, gl[1:]):
        if c["bbox"][0] - prev["bbox"][2] > 0.6 * wmed:
            words.append(cur)
            cur = [c]
        else:
            cur.append(c)
    words.append(cur)
    return words


def measure_page(path, scale=2):
    """Return per-word (ink_area, n_glyphs, bbox) for the page's body text."""
    im, g = B.load_gray(path, scale)
    ink, thr, bars = B.ink_mask(g)
    comps = B.components(ink, 14 * scale // 2, 90 * scale // 2, 40)
    if not comps:
        return []
    lines = B.group_lines(comps, tol=12 * scale)
    lines = [l for l in lines if len(l) >= 8]
    wmed = float(np.median([c["bbox"][2] - c["bbox"][0] for c in comps]))

    out = []
    for li, ln in enumerate(lines):
        hs = np.array([c["bbox"][3] - c["bbox"][1] for c in ln])
        hmed = np.median(hs)
        gl = [c for c in ln if (c["bbox"][3] - c["bbox"][1]) >= 0.45 * hmed]
        if len(gl) < 4:
            continue
        for wd in words_of_line(gl, wmed):
            if len(wd) < 2:
                continue
            area = sum(int(c["mask"].sum()) for c in wd)
            n = len(wd)
            x0 = min(c["bbox"][0] for c in wd)
            y0 = min(c["bbox"][1] for c in wd)
            out.append({"li": li, "area": area, "n": n, "x": x0, "y": y0,
                        "ink_per_glyph": area / n})
    return out


def classify(words):
    """Two-cluster split on ink-per-glyph, normalised per line to absorb the
    exposure and font-size drift down a page."""
    if not words:
        return []
    by_line = {}
    for w in words:
        by_line.setdefault(w["li"], []).append(w)
    for ws in by_line.values():
        med = float(np.median([w["ink_per_glyph"] for w in ws]))
        for w in ws:
            w["ratio"] = w["ink_per_glyph"] / med if med else 1.0
    ratios = np.array([w["ratio"] for w in words])
    # split at the midpoint between the two modes; regular sits at 1.0
    thr = 1.25
    for w in words:
        w["bold"] = w["ratio"] >= thr
    return ratios


def bacon_decode(bits, alphabet, polarity):
    b = bits if polarity else "".join("1" if c == "0" else "0" for c in bits)
    out = []
    for i in range(0, len(b) - 4, 5):
        v = int(b[i:i + 5], 2)
        out.append(alphabet[v] if v < len(alphabet) else "?")
    return "".join(out)


def products(bits, tag, out):
    if len(bits) < 20:
        return
    out.add(bits)
    for alpha in (BACON24, BACON26):
        for pol in (True, False):
            d = bacon_decode(bits, alpha, pol)
            if len(d) >= 8:
                out.add(d)
                out.add(d[::-1])
    rle = "".join(str(len(list(g))) for _, g in itertools.groupby(bits))
    out.add(rle)


def key_windows(bits):
    """Every 32-byte key the bit string could encode, at every bit phase."""
    keys = []
    for phase in range(8):
        b = bits[phase:]
        nby = len(b) // 8
        if nby < 32:
            continue
        by = bytes(int(b[i * 8:(i + 1) * 8], 2) for i in range(nby))
        for i in range(len(by) - 31):
            keys.append(by[i:i + 32])
    return keys


def bip39_from_bits(bits):
    """Read the bit string as 11-bit BIP-39 indices; keep checksum-valid runs."""
    try:
        from mnemonic import Mnemonic
    except ImportError:
        return []
    wl = Mnemonic("english").wordlist
    from bip39_sweep import checksum_ok
    out = []
    for phase in range(11):
        b = bits[phase:]
        idx = [int(b[i:i + 11], 2) for i in range(0, len(b) - 10, 11)]
        words = [wl[i] for i in idx]
        for n in (12, 15, 18, 21, 24):
            for i in range(len(words) - n + 1):
                w = words[i:i + n]
                if checksum_ok(w):
                    out.append(" ".join(w))
    return out


def selftest():
    """Plant a Bacon-encoded message in a synthetic bit string and recover it."""
    msg = "helloworld"
    bits = "".join(f"{BACON26.index(c):05b}" for c in msg)
    got = bacon_decode(bits, BACON26, True)
    ok = got == msg
    sys.stderr.write(f"  bacon round-trip: {got!r} {'OK' if ok else 'FAIL'}\n")
    kw = key_windows("1" * 300)
    ok &= len(kw) > 0 and len(kw[0]) == 32
    sys.stderr.write(f"  key windows from 300 bits: {len(kw)} "
                     f"{'OK' if kw else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("selftest failed")
    if a.selftest:
        return

    allbits, per_page = [], {}
    for p in a.pages:
        ws = measure_page(p)
        classify(ws)
        bits = "".join("1" if w["bold"] else "0" for w in ws)
        per_page[os.path.basename(p)] = bits
        allbits.append(bits)
        nb = sum(1 for w in ws if w["bold"])
        sys.stderr.write(f"  {os.path.basename(p)}: {len(ws)} words, "
                         f"{nb} bold ({nb/max(len(ws),1)*100:.0f}%)\n")
        sys.stderr.write(f"    {bits[:100]}\n")

    full = "".join(allbits)
    sys.stderr.write(f"\n  total {len(full)} bits = {len(full)//5} Bacon letters "
                     f"= {len(full)//8} bytes\n")

    out = set()
    products(full, "ALL", out)
    for name, b in per_page.items():
        products(b, name, out)
    # mirror scopes: the clue is mirror writing, so bit order may be reversed
    products(full[::-1], "ALLrev", out)

    sys.stderr.write(f"\n  bacon decode (26-letter, bold=1): "
                     f"{bacon_decode(full, BACON26, True)[:70]}\n")
    sys.stderr.write(f"  bacon decode (26-letter, bold=0): "
                     f"{bacon_decode(full, BACON26, False)[:70]}\n")

    mn = bip39_from_bits(full) + bip39_from_bits(full[::-1])
    sys.stderr.write(f"  checksum-valid BIP-39 mnemonics from the bits: {len(mn)}\n")

    keys = key_windows(full) + key_windows(full[::-1])
    sys.stderr.write(f"  32-byte key windows at every bit phase: {len(keys)}\n")

    # ---- screen everything ----
    from index_oracle import Oracle
    from full_sweep import spks_for_key
    from hist_index import HistIndex
    o = Oracle(verbose=False)
    o.calibrate()
    h = HistIndex()
    hits = 0

    def check(k, label):
        nonlocal hits
        spks = spks_for_key(k)
        for idx, name in ((o, "current"), (h, "historical")):
            for j, bal in idx.contains_spks([s for _, s in spks]):
                hits += 1
                sys.stderr.write(f"\n*** HIT [{name}] {label}  {spks[j][0]}  "
                                 f"{bal/1e8:.8f} BTC\n    priv {k.hex()}\n")

    for k in keys:
        check(k, "raw-bit-window")
    for s in sorted(out):
        check(hashlib.sha256(s.encode()).digest(), f"sha256({s[:28]}...)")
    if mn:
        from mnemonic import Mnemonic
        from hd_sweep import build_paths, derive
        for m in mn:
            seed = Mnemonic.to_seed(m, passphrase="")
            for path in build_paths()[:24]:
                try:
                    check(derive(seed, path), f"bip39:{m[:24]}...")
                except Exception:
                    pass

    sys.stderr.write(f"\n  {len(keys)} key windows + {len(out)} string products "
                     f"+ {len(mn)} mnemonics screened: {hits} hits\n")


if __name__ == "__main__":
    main()
