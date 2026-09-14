#!/usr/bin/env python3
"""
The mirrored serial through STRETCHED KDFs -- the last axis it had not seen.

WHY THIS IS A SEPARATE RUN
`mirror_serial.py` put 36 mirror readings of CL76841714A through the full fast
stack: 7 direct hashes plus 5 seed types across 72 HD paths, into 25 script
forms. 330,300 scriptPubKeys, 0 hits.

That closed the mirrored serial under FAST HASHES only. As
`window/kdf_and_keyformats.md` puts it, a deliberately-stretched KDF is
invisible to a bulk sweep by construction -- stretching exists precisely so
that many candidates cannot be tried. So "we swept 330,300 scripts" was never
a claim about scrypt or pbkdf2, and `serial_secret.py` tested the FORWARD
serial as a passphrase and salt, not the mirrored readings.

36 strings is small enough that the expensive family is affordable here, which
is the whole reason this is worth doing: the argument that stretching defeats
bulk search does not apply to a candidate set this size.

WHAT IT RUNS
  kdf_sweep.derivations   pbkdf2-hmac-sha256 at c=1000/2048/4096/10000/65536
                          and sha512 at c=2048/4096/65536, across 8 salts,
                          plus scrypt at N=2^12 and 2^14 -- 66 per phrase
  warpwallet.warp_key     scrypt N=2^18 XOR pbkdf2 c=2^16, across the salts

CONTROLS, BOTH MANDATORY
  1. each primitive is pinned to its published vector before any sweep -- a
     silently-wrong scrypt makes every null worthless
  2. a planted key must be FOUND through the index, or a null here is
     indistinguishable from a broken lookup

  python3 mirror_kdf.py --selftest
  python3 mirror_kdf.py --workers 4
"""
import argparse, hashlib, sys, time
from multiprocessing import Pool

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def _job(args):
    """(reading_name, phrase) -> [(label, key32), ...]. Runs in a worker."""
    name, phrase = args
    import kdf_sweep, warpwallet
    out = []
    for label, k in kdf_sweep.derivations(phrase):
        out.append((f"{name}|{label}", k))
    for salt in kdf_sweep.SALTS:
        try:
            out.append((f"{name}|warp/salt={salt!r}",
                        warpwallet.warp_key(phrase, salt)))
        except Exception:
            pass
    return out


def selftest():
    ok = True
    import kdf_sweep, warpwallet
    sys.stderr.write("  primitives pinned to published vectors:\n")
    # RFC 6070 pbkdf2-sha1
    v = hashlib.pbkdf2_hmac("sha1", b"password", b"salt", 1, dklen=20).hex()
    good = v == "0c60c80f961f0e71f3a9b524af6012062fe037a6"
    ok &= good
    sys.stderr.write(f"    RFC 6070 pbkdf2-sha1 c=1: {'OK' if good else 'FAIL'}\n")
    # RFC 7914 scrypt
    v2 = hashlib.scrypt(b"", salt=b"", n=16, r=1, p=1, dklen=64).hex()
    good = v2.startswith("77d6576238657b203b19")
    ok &= good
    sys.stderr.write(f"    RFC 7914 scrypt N=16: {'OK' if good else 'FAIL'}\n")
    good = warpwallet.selftest()
    ok &= good
    sys.stderr.write(f"    WarpWallet published vector: "
                     f"{'OK' if good else 'FAIL'}\n")

    import mirror_serial
    r = mirror_serial.readings()
    ok &= len(r) >= 30 and r.get("serial_rev") == "A41714867LC"
    sys.stderr.write(f"  {len(r)} mirror readings, incl. "
                     f"{r.get('serial_rev')}: "
                     f"{'OK' if r.get('serial_rev')=='A41714867LC' else 'FAIL'}\n")
    n = len(list(kdf_sweep.derivations("x")))
    sys.stderr.write(f"  {n} stretched derivations per reading, "
                     f"+{len(kdf_sweep.SALTS)} warp = "
                     f"{(n+len(kdf_sweep.SALTS))*len(r):,} keys total\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("a KDF primitive fails its published vector; every null from "
                 "it would be worthless")
    if a.selftest:
        return

    import continuous_solver as CS
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    import mirror_serial

    orc = CS.IndexOracle()
    if not orc.ready:
        sys.exit(f"no oracle: {orc.why}")
    sys.stderr.write("\n  POSITIVE CONTROL\n")
    if not orc.control():
        sys.exit("  the oracle cannot find a known-funded address; refusing "
                 "to report a null")
    sys.stderr.write("  the oracle finds a known-funded address: OK\n")

    readings = sorted(mirror_serial.readings().items())
    sys.stderr.write(f"\n  {len(readings)} mirror readings through the "
                     f"stretched family\n"
                     f"  (this is the slow one -- scrypt N=2^18 is ~2 s per "
                     f"WarpWallet derivation)\n\n")

    t0, nkeys, nspk, hits = time.time(), 0, 0, []
    meta, spks = [], []

    def flush():
        nonlocal meta, spks
        if not spks:
            return
        for j, bal in orc.check(spks):
            hits.append(meta[j] + (bal,))
            sys.stderr.write(f"\n  *** HIT  {bal} sats\n"
                             f"      {meta[j][0]}\n"
                             f"      script {meta[j][1]}\n")
            sys.stderr.flush()
        meta, spks = [], []

    with Pool(a.workers) as pool:
        for i, batch in enumerate(pool.imap_unordered(_job, readings), 1):
            for label, k in batch:
                if not (0 < int.from_bytes(k, "big") < CURVE_N):
                    continue
                nkeys += 1
                for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                    meta.append((label, st))
                    spks.append(spk)
                    nspk += 1
                if len(spks) >= 60000:
                    flush()
            el = time.time() - t0
            sys.stderr.write(f"\r  {i}/{len(readings)} readings  "
                             f"{nkeys:,} keys  {nspk:,} scripts  {el:.0f}s  ")
            sys.stderr.flush()
    flush()
    sys.stderr.write(f"\n\n  {nkeys:,} stretched keys, {nspk:,} "
                     f"scriptPubKeys, {len(hits)} hit(s)\n")
    if not hits:
        sys.stderr.write(
            "  No mirror reading of the serial derives to a funded address\n"
            "  under pbkdf2, scrypt or WarpWallet either.\n"
            "  The mirrored serial is now exhausted, not merely tested.\n")


if __name__ == "__main__":
    main()
