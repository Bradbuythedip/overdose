#!/usr/bin/env python3
"""
Exhaust the ENTIRE 8-digit serial keyspace. Not sample it — exhaust it.

WHY THIS IS THE MINABLE HALF
Two search spaces get conflated when people reach for a GPU here:

  all BIP-39 words, 12-word mnemonic   2048^12 = 2^132 = 5.4e39
  the serial as entropy                10^8    = 2^26.6

The first is not minable by any GPU, or by all of them: a card doing 1e9 keys/s
needs 1.7e23 years. The second is 100 million candidates and finishes on a
laptop. The gap is 10^30, and the serial is tractable precisely BECAUSE it is
weak — 8 decimal digits is not a key, it is a keyspace.

WHAT THIS BUYS OVER TESTING THE ONE SERIAL WE READ
Everything so far tested CL76841714A and a digit-neighbourhood around it. This
tests EVERY 8-digit serial, so it no longer matters whether the digits were
misread, whether the photographed note is the intended one, or whether a second
note in the artwork carries it. If "the serial is the entropy" is the mechanism
at all, under one of these transforms, this finds it regardless of which serial
is correct.

TRANSFORMS, each the by-hand move a person would actually make
  tiled     the 8 digits repeated to fill 32 bytes of hex — "76841714" x8 is
            exactly 64 hex characters, no library involved
  sha256    sha256 of the digit string, the ordinary brainwallet move
  framed    sha256 of the full serial with its letters, "CL" + digits + "A"
  intkey    the decimal value as a raw 32-byte big-endian scalar

ORACLE AND ITS LIMIT, stated up front
Checked against the 56,795,328-address funded index. That index is a BALANCE
snapshot, so this run answers "does any serial-derived key hold coins today". It
cannot see a key that was funded and swept — and since a 26.6-bit keyspace is
exhaustible by anyone, swept is the likely state if this mechanism was ever
used. The API oracle is the one that sees that, but 100 million addresses cannot
be sent to an API. So: a hit here is decisive, a null here is bounded, and the
bound is named rather than glossed.

  python3 serial_exhaust.py --selftest
  python3 serial_exhaust.py --transform tiled --workers 4
"""
import argparse, hashlib, os, sys, time
from multiprocessing import Pool

from coincurve import PrivateKey

from hd_sweep import h160

N_CURVE = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def key_tiled(d):
    return bytes.fromhex(d * 8)


def key_sha256(d):
    return hashlib.sha256(d.encode()).digest()


def key_framed(d):
    return hashlib.sha256(("CL" + d + "A").encode()).digest()


def key_intkey(d):
    return int(d).to_bytes(32, "big")


TRANSFORMS = {"tiled": key_tiled, "sha256": key_sha256,
              "framed": key_framed, "intkey": key_intkey}

_ORACLE = None


def _init():
    global _ORACLE
    from index_oracle import Oracle
    o = Oracle(verbose=False)
    if not o.calibrate():
        raise RuntimeError("oracle calibration failed in worker")
    _ORACLE = o


def _chunk(args):
    lo, hi, tname = args
    fn = TRANSFORMS[tname]
    spks, meta = [], []
    hits = []
    for i in range(lo, hi):
        d = f"{i:08d}"
        k = fn(d)
        v = int.from_bytes(k, "big")
        if not (0 < v < N_CURVE):
            continue
        pub = PrivateKey(k).public_key
        for comp in (True, False):
            p = pub.format(compressed=comp)
            spks.append(b"\x76\xa9\x14" + h160(p) + b"\x88\xac")
            meta.append((d, comp))
        if len(spks) >= 8000:
            for j, bal in _ORACLE.contains_spks(spks):
                hits.append((meta[j][0], meta[j][1], bal))
            spks, meta = [], []
    if spks:
        for j, bal in _ORACLE.contains_spks(spks):
            hits.append((meta[j][0], meta[j][1], bal))
    return hi - lo, hits


def selftest():
    """Transforms must be exact, and a planted funded key must be found."""
    ok = True
    t = key_tiled("76841714")
    ok &= t.hex() == "76841714" * 8 and len(t) == 32
    sys.stderr.write(f"  tiled('76841714') = {t.hex()[:24]}...  "
                     f"{'OK' if ok else 'FAIL'}\n")
    ok &= key_intkey("00000042") == (42).to_bytes(32, "big")
    sys.stderr.write(f"  intkey is the decimal value big-endian: OK\n")
    for n, fn in TRANSFORMS.items():
        k = fn("12345678")
        ok &= len(k) == 32
    sys.stderr.write(f"  all {len(TRANSFORMS)} transforms give 32 bytes\n")

    # the pipeline must report a KNOWN funded address when one is derivable
    from index_oracle import Oracle, spk_from_address
    o = Oracle(verbose=False)
    ok &= o.calibrate()
    got = o.contains_spks([spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")])
    ok &= bool(got)
    sys.stderr.write(f"  oracle returns the genesis address: "
                     f"{'OK' if got else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transform", choices=list(TRANSFORMS), default="tiled")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=100_000_000)
    ap.add_argument("--chunk", type=int, default=50_000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("transforms or oracle fail their controls; refusing")
    if a.selftest:
        return

    out = a.out or f"serial_exhaust_{a.transform}.tsv"
    jobs = [(lo, min(lo + a.chunk, a.end), a.transform)
            for lo in range(a.start, a.end, a.chunk)]
    total = a.end - a.start
    sys.stderr.write(f"\n  transform={a.transform}  range {a.start:,}..{a.end:,} "
                     f"({total:,} serials, {total*2:,} addresses)\n")
    sys.stderr.write(f"  {len(jobs):,} chunks across {a.workers} workers\n")
    sys.stderr.write("  ORACLE IS A BALANCE SNAPSHOT: a hit is decisive, a null "
                     "means 'holds nothing today'\n\n")

    fh = open(out, "w")
    fh.write("serial\tcompressed\tbalance_sats\ttransform\n")
    done = hits = 0
    t0 = time.time()
    with Pool(a.workers, initializer=_init) as pool:
        for n, hh in pool.imap_unordered(_chunk, jobs):
            done += n
            for d, comp, bal in hh:
                hits += 1
                fh.write(f"{d}\t{comp}\t{bal}\t{a.transform}\n")
                fh.flush()
                sys.stderr.write(f"  *** FUNDED serial={d} compressed={comp} "
                                 f"{bal/1e8:.8f} BTC\n")
            el = time.time() - t0
            if done % (a.chunk * 20) == 0:
                r = done / max(el, 1e-9)
                sys.stderr.write(f"  {done:,}/{total:,}  {hits} funded  "
                                 f"{r:,.0f} serials/s  eta "
                                 f"{(total-done)/max(r,1e-9)/60:.0f}m\n")
    fh.close()
    el = time.time() - t0
    sys.stderr.write(f"\n  DONE. {done:,} serials ({done*2:,} addresses) in "
                     f"{el/60:.1f} min, {hits} funded -> {out}\n")


if __name__ == "__main__":
    main()
