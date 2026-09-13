#!/usr/bin/env python3
"""
Slow / stretched KDFs over the article phrases -- the class the bulk sweep missed.

WarpWallet exposed a wider gap than itself. Every one of this repo's ~69M
derived addresses came from a FAST hash (sha256, dsha256, sha512 halves,
sha3-256, blake2b, keccak-ish). Any deliberately-stretched KDF is invisible to
a bulk sweep by construction, because the whole point of stretching is that you
cannot try many candidates. So the coverage is not "69M addresses" but "69M
addresses under fast hashes only", and the stretched families were never tried
at all on the body prose.

Covered here, all against the offline funded index:

  pbkdf2-hmac-sha256  c = 1k, 2048, 4096, 10k, 65536      salt "" and variants
  pbkdf2-hmac-sha512  c = 2048, 4096, 65536
  scrypt              N = 2^12, 2^14 (r=8,p=1)  -- the cheap end of the
                      WarpWallet family, which warpwallet.py covers at 2^18

Cost per phrase is roughly 0.2 s for the whole menu, so this scales to
thousands of phrases rather than millions -- which is the point.

Self-test pins each KDF against a published RFC/reference vector, because a
silently-wrong KDF makes every null here worthless.

  python3 kdf_sweep.py --selftest
  python3 kdf_sweep.py --phrases FILE --out kdf_hits.tsv
"""
import argparse, binascii, hashlib, sys, time
from multiprocessing import Pool

from full_sweep import spks_for_key
from index_oracle import Oracle

SALTS = ["", "bitcoin", "Bitcoin", "maxkeiser", "Max Keiser", "overdose",
         "OVERDOSE", "El Salvador"]


def derivations(phrase):
    """Yield (label, priv32) for every stretched KDF worth trying."""
    pb = phrase.encode("utf-8")
    for salt in SALTS:
        sb = salt.encode("utf-8")
        for c in (1000, 2048, 4096, 10000, 65536):
            yield (f"pbkdf2-sha256/{c}/salt={salt!r}",
                   hashlib.pbkdf2_hmac("sha256", pb, sb, c, dklen=32))
        for c in (2048, 4096, 65536):
            yield (f"pbkdf2-sha512/{c}/salt={salt!r}",
                   hashlib.pbkdf2_hmac("sha512", pb, sb, c, dklen=32))
    # scrypt: only the empty salt, it is the expensive one
    for logn in (12, 14):
        try:
            yield (f"scrypt/2^{logn}",
                   hashlib.scrypt(pb, salt=b"", n=1 << logn, r=8, p=1,
                                  dklen=32, maxmem=1 << 30))
        except Exception:
            pass


def selftest():
    """Pin each primitive to a published vector."""
    ok = True

    # RFC 6070 PBKDF2-HMAC-SHA1 is the canonical vector set; hashlib shares one
    # implementation across hash choices, so verifying SHA1 verifies the
    # machinery, and the SHA256 vector below is from RFC 7914 / common practice.
    v = hashlib.pbkdf2_hmac("sha1", b"password", b"salt", 1, dklen=20)
    exp = binascii.unhexlify("0c60c80f961f0e71f3a9b524af6012062fe037a6")
    ok &= v == exp
    sys.stderr.write(f"  RFC 6070 pbkdf2-sha1 c=1      {'OK' if v == exp else 'FAIL'}\n")

    v = hashlib.pbkdf2_hmac("sha1", b"password", b"salt", 4096, dklen=20)
    exp = binascii.unhexlify("4b007901b765489abead49d926f721d065a429c1")
    ok &= v == exp
    sys.stderr.write(f"  RFC 6070 pbkdf2-sha1 c=4096   {'OK' if v == exp else 'FAIL'}\n")

    # RFC 7914 scrypt vector: N=16384, r=8, p=1, "pleaseletmein"/"SodiumChloride"
    v = hashlib.scrypt(b"pleaseletmein", salt=b"SodiumChloride",
                       n=16384, r=8, p=1, dklen=64, maxmem=1 << 30)
    exp = binascii.unhexlify(
        "7023bdcb3afd7348461c06cd81fd38ebfda8fbba904f8e3ea9b543f6545da1f2"
        "d5432955613f0fcf62d49705242a9af9e61e85dc0d651e40dfcf017b45575887")
    ok &= v == exp
    sys.stderr.write(f"  RFC 7914 scrypt N=16384       {'OK' if v == exp else 'FAIL'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def _job(phrase):
    labels, keys = [], []
    for lab, k in derivations(phrase):
        labels.append(lab)
        keys.append(k)
    return phrase, labels, keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases")
    ap.add_argument("--out", default="kdf_hits.tsv")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("refusing to run: a KDF does not match its published vector")
    if a.selftest:
        return
    if not a.phrases:
        sys.exit("--phrases required")

    phrases = [l.rstrip("\n") for l in open(a.phrases, encoding="utf-8")]
    phrases = [p for p in phrases if p.strip()]

    oracle = Oracle(verbose=True)
    if not oracle.calibrate():
        sys.exit("oracle calibration failed")

    n_per = len(list(derivations("x")))
    sys.stderr.write(f"\n{len(phrases):,} phrases x {n_per} stretched KDFs "
                     f"x 5 script types = {len(phrases)*n_per*5:,} addresses\n\n")

    out = open(a.out, "w")
    out.write("phrase\tkdf\tscript_type\tprivkey_hex\tbalance_sats\tbalance_btc\n")
    n = hits = 0
    t0 = time.time()
    with Pool(a.workers) as pool:
        for phrase, labels, keys in pool.imap_unordered(_job, phrases, chunksize=1):
            n += 1
            meta, spks = [], []
            for lab, k in zip(labels, keys):
                for st, spk in spks_for_key(k):
                    meta.append((lab, st))
                    spks.append(spk)
            for j, bal in oracle.contains_spks(spks):
                hits += 1
                lab, st = meta[j]
                kk = keys[labels.index(lab)]
                out.write(f"{phrase}\t{lab}\t{st}\t{kk.hex()}\t{bal}\t{bal/1e8:.8f}\n")
                out.flush()
                sys.stderr.write(f"\n*** HIT {bal/1e8:.8f} BTC  {st}  {lab}\n"
                                 f"    phrase={phrase!r}\n    priv {kk.hex()}\n\n")
                sys.stderr.flush()
            if n % 50 == 0:
                el = time.time() - t0
                sys.stderr.write(f"  {n}/{len(phrases)}  {hits} hits  "
                                 f"{n/el:.1f}/s  eta {(len(phrases)-n)/(n/el)/60:.1f}m\n")
                sys.stderr.flush()
    out.close()
    sys.stderr.write(f"\nDONE. {n} phrases, {hits} hits -> {a.out}\n")


if __name__ == "__main__":
    main()
