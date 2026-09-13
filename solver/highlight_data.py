#!/usr/bin/env python3
"""
Treat the highlight overlay as DATA rather than as text.

Every prior pass read the highlighted PHRASES. Nobody has read the highlighting
itself: which runs are orange, which are knocked-out black, and in what order.
That is a symbol sequence the designer chose, independent of the words, and it
is exactly the kind of channel a "hidden in plain sight" cipher uses.

The colour sequence across the piece is 38 symbols long. Read as bits that is
under 5 bytes -- far too short to be a private key -- so this does not test
"is the key here" but "is there a short payload here": an index, an offset, a
page/line pointer, or a passphrase fragment.

Derives and tests:
  the colour sequence as bits, both polarities, per page and whole article
  as bytes / hex / decimal
  run-length encodings of it
  the per-page counts of each colour as a digit string
and screens every product through the funded index and the WIF checksum oracle.

  python3 highlight_data.py --hl highlights_ordered.tsv
"""
import argparse, hashlib, itertools, re, sys


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or "\t" not in line:
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            rows.append((p[0].strip(), p[1].strip(), p[2].strip()))
    return rows


def bits_to_products(bits, tag, out):
    """Every reasonable reading of a bit string."""
    s = "".join(bits)
    if len(s) < 4:
        return
    out.add(s)
    out.add(s[::-1])
    inv = "".join("1" if c == "0" else "0" for c in s)
    out.add(inv)
    out.add(inv[::-1])
    for b in (s, inv):
        # as an integer, decimal and hex
        n = int(b, 2)
        out.add(str(n))
        out.add(hex(n)[2:])
        out.add(hex(n)[2:].upper())
        # as bytes, hex of the packed bytes
        pad = b + "0" * (-len(b) % 8)
        by = bytes(int(pad[i:i + 8], 2) for i in range(0, len(pad), 8))
        out.add(by.hex())
        # run-length encoding
        rle = "".join(str(len(list(g))) for _, g in itertools.groupby(b))
        out.add(rle)
        # as letters, a=0/b=1 and the 5-bit alphabet reading
        out.add("".join("ab"[int(c)] for c in b))
        if len(b) >= 5:
            letters = "".join(
                chr(97 + int(b[i:i + 5], 2) % 26) for i in range(0, len(b) - 4, 5))
            out.add(letters)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hl", default="highlights_ordered.tsv")
    ap.add_argument("--out", default="/tmp/hldata.txt")
    a = ap.parse_args()

    rows = load(a.hl)
    pages = sorted({p for p, _, _ in rows})
    sys.stderr.write(f"{len(rows)} highlight runs across {len(pages)} pages\n\n")

    # orange = 1; black and the page-77 white-on-dark bars are the same device
    # (knocked-out text), so both read as 0
    seq = ["1" if c == "orange" else "0" for _, c, _ in rows]
    sys.stderr.write("  colour sequence, orange=1 / knocked-out=0:\n")
    sys.stderr.write("    " + "".join(seq) + f"   ({len(seq)} symbols)\n")
    for p in pages:
        s = "".join("1" if c == "orange" else "0"
                    for pg, c, _ in rows if pg == p)
        sys.stderr.write(f"    p{p}: {s}  ({len(s)})\n")

    n = int("".join(seq), 2)
    sys.stderr.write(f"\n  as an integer : {n}\n")
    sys.stderr.write(f"  as hex        : {hex(n)[2:]}\n")
    rle = "".join(str(len(list(g))) for _, g in itertools.groupby("".join(seq)))
    sys.stderr.write(f"  run lengths   : {rle}\n")

    # three-state reading, since page 77's bars sit on a dark ground
    tri = {"orange": "0", "black": "1", "white": "2"}
    t = "".join(tri.get(c, "3") for _, c, _ in rows)
    sys.stderr.write(f"  three-state   : {t}\n")

    out = set()
    bits_to_products(seq, "ALL", out)
    for p in pages:
        bits_to_products([b for (pg, c, _), b in zip(rows, seq) if pg == p],
                         f"p{p}", out)
    out.add(t)
    out.add(t[::-1])
    counts = "".join(str(sum(1 for pg, c, _ in rows if pg == p and c == "orange"))
                     for p in pages)
    out.add(counts)
    out.add(counts[::-1])
    sys.stderr.write(f"  orange-per-page counts: {counts}\n")

    out = {x for x in out if 3 <= len(x) <= 200}
    with open(a.out, "w") as f:
        for x in sorted(out):
            f.write(x + "\n")
    sys.stderr.write(f"\n{len(out)} derived products -> {a.out}\n")

    # screen every product: as a passphrase, and as literal hex key material
    from index_oracle import Oracle
    from full_sweep import spks_for_key
    o = Oracle(verbose=False)
    if not o.calibrate():
        sys.exit("oracle calibration failed")

    hits = 0
    for x in sorted(out):
        keys = [hashlib.sha256(x.encode()).digest(),
                hashlib.sha256(hashlib.sha256(x.encode()).digest()).digest()]
        h = re.fullmatch(r"[0-9a-fA-F]+", x)
        if h and len(x) == 64:
            keys.append(bytes.fromhex(x))
        if h and len(x) < 64:
            keys.append(bytes.fromhex(x.rjust(64, "0")))
        for k in keys:
            spks = spks_for_key(k)
            for j, bal in o.contains_spks([s for _, s in spks]):
                hits += 1
                sys.stderr.write(f"\n*** HIT {bal/1e8:.8f} BTC  {spks[j][0]}\n"
                                 f"    product {x!r}\n    priv {k.hex()}\n")
    sys.stderr.write(f"\n{len(out)} products screened against the funded index: "
                     f"{hits} hits\n")


if __name__ == "__main__":
    main()
