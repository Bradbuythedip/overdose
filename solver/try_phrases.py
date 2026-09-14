#!/usr/bin/env python3
"""
Test candidate phrases against the 56M funded-address index. The workhorse.

Give it strings, one per line, on stdin or in a file. It runs each through the
full derivation stack and reports anything that lands on a funded address.

    7 direct hashes        sha256, dsha256, sha512 halves, sha3, blake2b, keccak
    5 seed types x 72 HD paths   BIP-32/39/44/49/84/86
    25 script forms        P2PKH c/u, P2WPKH, P2SH-P2WPKH, P2TR, bare P2PK,
                           and the 20 wrapped/multisig forms in spk_extra

A POSITIVE CONTROL RUNS FIRST, ALWAYS. A planted key must be found through the
index before any null is reported, because a sweep that cannot find a key it
was handed produces a null indistinguishable from a real one.

    echo "some phrase" | python3 try_phrases.py
    python3 try_phrases.py --in candidates.txt --label genesis
"""
import argparse, hashlib, sys, time

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def run(phrases, oracle, label="", batch=60000, hd=True, progress=True):
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    paths = build_paths() if hd else []
    hits, n, t0 = [], 0, time.time()
    meta, spks = [], []

    def flush():
        nonlocal meta, spks
        if not spks:
            return
        for j, bal in oracle.check(spks):
            hits.append(meta[j] + (bal,))
            sys.stderr.write(f"\n  *** HIT  {bal} sats\n"
                             f"      phrase     {meta[j][0]!r}\n"
                             f"      derivation {meta[j][1]}\n"
                             f"      script     {meta[j][2]}\n")
            sys.stderr.flush()
        meta, spks = [], []

    for i, p in enumerate(phrases, 1):
        keys = [(f"d:{h}", k) for h, k in direct_keys(p).items()]
        for sn, seed in seeds_from(p).items():
            for path in paths:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    keys.append((f"{sn}:{path}", k))
        for dn, k in keys:
            if not (0 < int.from_bytes(k, "big") < CURVE_N):
                continue
            for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                meta.append((p, dn, st))
                spks.append(spk)
                n += 1
            if len(spks) >= batch:
                flush()
        if progress and i % 50 == 0:
            el = time.time() - t0
            sys.stderr.write(f"\r  [{label}] {i:,}/{len(phrases):,} phrases  "
                             f"{n:,} scripts  {n/max(el,1e-9):,.0f}/s  ")
            sys.stderr.flush()
    flush()
    return hits, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", help="file of phrases; default stdin")
    ap.add_argument("--label", default="")
    ap.add_argument("--no-hd", action="store_true",
                    help="direct hashes only (much faster, less complete)")
    a = ap.parse_args()

    src = open(a.inp, encoding="utf-8") if a.inp else sys.stdin
    seen, phrases = set(), []
    for line in src:
        s = line.rstrip("\n")
        if s and s not in seen and len(s) < 4000:
            seen.add(s)
            phrases.append(s)
    if not phrases:
        sys.exit("no phrases given")

    import continuous_solver as CS
    orc = CS.IndexOracle()
    if not orc.ready:
        sys.exit(f"no oracle: {orc.why}")
    if not orc.control():
        sys.exit("POSITIVE CONTROL FAILED - the oracle cannot find a "
                 "known-funded address; a null would be meaningless")
    sys.stderr.write(f"  [{a.label}] control OK, {len(phrases):,} phrases\n")

    hits, n = run(phrases, orc, a.label, hd=not a.no_hd)
    sys.stderr.write(f"\n  [{a.label}] {n:,} scriptPubKeys, {len(hits)} hit(s)\n")
    for p, dn, st, bal in hits:
        print(f"HIT\t{bal}\t{dn}\t{st}\t{p}")
    if not hits:
        sys.stderr.write(f"  [{a.label}] no hit\n")


if __name__ == "__main__":
    main()
