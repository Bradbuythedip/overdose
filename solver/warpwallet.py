#!/usr/bin/env python3
"""
WarpWallet key derivation, and a sweep of the article's phrases through it.

WHY THIS IS A REAL GAP
Every derivation in this repo's 69M-address sweep used a FAST hash: sha256,
double-sha256, sha512 halves, sha3-256, blake2b, keccak-ish. An old session's
notes claim "WarpWallet scrypt" was covered, but it is not in any current
tool -- full_sweep.direct_keys() has no scrypt and no pbkdf2 -- and it was
certainly never applied to the article's body prose, which was missing from
every corpus until today.

WarpWallet (keybase.io/warp, 2015) is the deliberately-slow brainwallet of
exactly the era a 2023 puzzle-setter reminiscing about early Bitcoin might
reach for:

    s1 = scrypt (passphrase||0x01, salt||0x01, N=2^18, r=8, p=1, dkLen=32)
    s2 = pbkdf2 (passphrase||0x02, salt||0x02, c=2^16, sha256, dkLen=32)
    privkey = s1 XOR s2

The cost is the point: ~1-3 s and 256 MB per derivation, so this can only ever
be run over hundreds or thousands of curated phrases, never millions. That is
also why it is worth running -- a slow KDF is invisible to every bulk sweep.

The published test vector is checked FIRST and the module refuses to sweep if
it fails, because a silently-wrong scrypt would make every null here worthless.

  python3 warpwallet.py --selftest
  python3 warpwallet.py --phrases FILE --salts FILE --out warp_hits.tsv
"""
import argparse, hashlib, itertools, os, sys, time
from multiprocessing import Pool

from full_sweep import spks_for_key
from index_oracle import Oracle, spk_from_address

N = 1 << 18
R = 8
P = 1
MAXMEM = 1 << 30

# keybase.io/warp published test vector
TV_PASS = "ER8FT+HFjk0"
TV_SALT = "7DpniYifN6c"
TV_ADDR = "1J32CmwScqhwnNQ77cKv9q41JGwoZe2JYQ"


def warp_key(passphrase, salt=""):
    pb = passphrase.encode("utf-8")
    sb = salt.encode("utf-8")
    s1 = hashlib.scrypt(pb + b"\x01", salt=sb + b"\x01",
                        n=N, r=R, p=P, dklen=32, maxmem=MAXMEM)
    s2 = hashlib.pbkdf2_hmac("sha256", pb + b"\x02", sb + b"\x02",
                             1 << 16, dklen=32)
    return bytes(a ^ b for a, b in zip(s1, s2))


def selftest():
    t0 = time.time()
    k = warp_key(TV_PASS, TV_SALT)
    dt = time.time() - t0
    spks = dict(spks_for_key(k))
    want = spk_from_address(TV_ADDR)
    # WarpWallet's own page shows the UNCOMPRESSED address for this vector
    ok_u = spks.get("p2pkh_u") == want
    ok_c = spks.get("p2pkh_c") == want
    sys.stderr.write(f"  test vector pass={TV_PASS!r} salt={TV_SALT!r}\n")
    sys.stderr.write(f"    privkey  {k.hex()}\n")
    sys.stderr.write(f"    expected {TV_ADDR}\n")
    sys.stderr.write(f"    uncompressed match: {ok_u}   compressed match: {ok_c}\n")
    sys.stderr.write(f"    {dt:.2f}s per derivation\n")
    ok = ok_u or ok_c
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def _job(args):
    ph, salt = args
    try:
        return ph, salt, warp_key(ph, salt)
    except Exception:
        return ph, salt, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases")
    ap.add_argument("--salts", help="file of salts, one per line; blank line = empty salt")
    ap.add_argument("--out", default="warp_hits.tsv")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("refusing to sweep: WarpWallet implementation does not match "
                 "the published test vector, so any null would be meaningless")
    if a.selftest:
        return
    if not a.phrases:
        sys.exit("--phrases required")

    phrases = [l.rstrip("\n") for l in open(a.phrases, encoding="utf-8")]
    phrases = [p for p in phrases if p.strip()]
    if a.salts:
        salts = [l.rstrip("\n") for l in open(a.salts, encoding="utf-8")]
    else:
        salts = [""]
    salts = list(dict.fromkeys(salts))

    oracle = Oracle(verbose=True)
    if not oracle.calibrate():
        sys.exit("oracle calibration failed")

    jobs = [(p, s) for p in phrases for s in salts]
    sys.stderr.write(f"\n{len(phrases):,} phrases x {len(salts)} salts = "
                     f"{len(jobs):,} WarpWallet derivations "
                     f"(~{len(jobs)*1.2/max(a.workers,1)/60:.0f} min at "
                     f"{a.workers} workers)\n\n")

    out = open(a.out, "w")
    out.write("phrase\tsalt\tscript_type\tprivkey_hex\tbalance_sats\tbalance_btc\n")
    n = hits = 0
    t0 = time.time()
    with Pool(a.workers) as pool:
        for ph, salt, k in pool.imap_unordered(_job, jobs, chunksize=1):
            n += 1
            if k is None:
                continue
            spks = spks_for_key(k)
            for j, bal in oracle.contains_spks([s for _, s in spks]):
                hits += 1
                st = spks[j][0]
                out.write(f"{ph}\t{salt}\t{st}\t{k.hex()}\t{bal}\t{bal/1e8:.8f}\n")
                out.flush()
                sys.stderr.write(f"\n*** HIT {bal/1e8:.8f} BTC  {st}  "
                                 f"salt={salt!r}  phrase={ph!r}\n"
                                 f"    priv {k.hex()}\n\n")
                sys.stderr.flush()
            if n % 25 == 0:
                el = time.time() - t0
                sys.stderr.write(f"  {n}/{len(jobs)}  {hits} hits  "
                                 f"{n/el:.2f}/s  eta {(len(jobs)-n)/(n/el)/60:.1f}m\n")
                sys.stderr.flush()
    out.close()
    sys.stderr.write(f"\nDONE. {n} derivations, {hits} hits -> {a.out}\n")


if __name__ == "__main__":
    main()
