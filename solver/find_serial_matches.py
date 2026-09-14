#!/usr/bin/env python3
"""
Every 8-digit value whose digest reproduces the serial. The complete list.

WHY COMPUTE IT RATHER THAN READ IT OFF A LOG
The continuous solver reported checksum hits to stderr, where a closed terminal
loses them. This derives the full set independently and exhaustively, so the
answer does not depend on which units happened to run on which machine, and so
any hit anyone reports can be checked against the whole population rather than
taken on its own.

It is also the honest way to read the base rate. 10^8 serials x 2 forms x 14
products x 8 targets / 2^32 gives about 5.2 expected matches across the whole
space. Knowing the real count tells us whether the observed hits are the
population or an excess — and an excess is the only thing that would be
interesting.

  python3 find_serial_matches.py --selftest
  python3 find_serial_matches.py --end 100000000
"""
import argparse, hashlib, sys, time

from serial_oracle import targets, wif_checksums


def products(b):
    out = []
    for fn in (hashlib.sha256, lambda x: hashlib.sha256(hashlib.sha256(x).digest()),
               hashlib.sha3_256, lambda x: hashlib.blake2b(x, digest_size=32)):
        d = fn(b).digest() if hasattr(fn(b), "digest") else fn(b)
        out.append(d[:4]); out.append(d[-4:])
    d = hashlib.sha512(b).digest()
    out.append(d[:4]); out.append(d[28:32]); out.append(d[32:36]); out.append(d[-4:])
    u, c = wif_checksums(hashlib.sha256(b).digest())
    out.append(u); out.append(c)
    return out


def selftest():
    ok = True
    tg = targets()
    want = tg["hex_reversed_byteswap"]
    got = hashlib.sha256(b"68352982").digest()[:4]
    ok &= got == want
    sys.stderr.write(f"  known hit 68352982 reproduces "
                     f"hex_reversed_byteswap: {'OK' if ok else 'FAIL'}\n")
    ok &= want in products(b"68352982")
    sys.stderr.write(f"  and the product list contains it: "
                     f"{'OK' if want in products(b'68352982') else 'FAIL'}\n")
    n = len(products(b"x"))
    exp = 1e8 * 2 * n * len(set(tg.values())) / 2 ** 32
    sys.stderr.write(f"  {n} products/phrase; expected matches over the full "
                     f"10^8 space: {exp:.1f}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=100_000_000)
    ap.add_argument("--out", default="serial_matches.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not selftest():
        sys.exit("controls failed")
    if a.selftest:
        return
    tg = targets()
    rev = {}
    for k, v in tg.items():
        rev.setdefault(v, []).append(k)
    fh = open(a.out, "w")
    fh.write("serial\tform\ttarget\tvalue\n")
    n = hits = 0
    t0 = time.time()
    for i in range(a.start, a.end):
        d = f"{i:08d}"
        for form, b in (("digits", d.encode()),
                        ("framed", ("CL" + d + "A").encode())):
            n += 1
            for v in products(b):
                if v in rev:
                    hits += 1
                    fh.write(f"{d}\t{form}\t{rev[v][0]}\t{v.hex()}\n")
                    fh.flush()
                    sys.stderr.write(f"  MATCH {d} {form} {rev[v][0]} "
                                     f"{v.hex()}\n")
        if i % 2_000_000 == 0 and i:
            el = time.time() - t0
            sys.stderr.write(f"  {i:,}  {hits} matches  "
                             f"{i/el:,.0f}/s  eta {(a.end-i)/(i/el)/60:.0f}m\n")
    fh.close()
    sys.stderr.write(f"\n  DONE. {n:,} phrases, {hits} matches -> {a.out}\n")


if __name__ == "__main__":
    main()
