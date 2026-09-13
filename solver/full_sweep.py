#!/usr/bin/env python3
"""
Path-exhaustive derivation sweep against the FULL 56.8M funded-address index.

THE COVERAGE HOLE THIS CLOSES
-----------------------------
  earlier brainwallet sweeps : many phrases x ~4 paths   x full 56.8M index
  hd_sweep.py (18.2M addrs)  : many phrases x ~360 paths x only 116 targets
  THIS                       : many phrases x ~360 paths x full 56.8M index

The 116-address target set rests on filter assumptions -- exactly 20.00000000
BTC, never moved, funded at or below block 781000. Each of those could be
wrong. Scoring against the full funded index makes a hit register regardless
of balance, spend history or funding date, so it does not inherit any of them.

Runs entirely offline against /tmp/address_map.bin -- no network, which
matters because this sandbox's egress policy blocks every Bitcoin API host.

  python3 full_sweep.py --selftest
  python3 full_sweep.py --phrases /tmp/all_phrases.txt --out full_sweep_hits.tsv

Derivation primitives are imported from hd_sweep.py rather than reimplemented,
so they stay covered by that module's BIP44/49/84/86 self-test vectors.
"""
import argparse, hashlib, sys, time

from coincurve import PrivateKey, PublicKey

from hd_sweep import (CURVE_N, h160, build_paths, derive, seeds_from,
                      direct_keys, selftest as hd_selftest)
from index_oracle import Oracle


# ---------- pubkey -> scriptPubKey (skip the address-string round trip) ----------
def spks_for_key(priv32):
    """Every standard scriptPubKey for one private key.

    Returns list of (script_type, spk_bytes).
    """
    try:
        sk = PrivateKey(priv32)
    except Exception:
        return []
    pub = sk.public_key
    pc = pub.format(compressed=True)
    pu = pub.format(compressed=False)

    hc, hu = h160(pc), h160(pu)
    out = [
        ("p2pkh_c", b"\x76\xa9\x14" + hc + b"\x88\xac"),
        ("p2pkh_u", b"\x76\xa9\x14" + hu + b"\x88\xac"),
        ("p2wpkh",  b"\x00\x14" + hc),
        ("p2sh_p2wpkh", b"\xa9\x14" + h160(b"\x00\x14" + hc) + b"\x87"),
    ]
    # BIP86 taproot: Q = lift_x(P) + H_TapTweak(xonly(P))*G, internal key even-Y
    try:
        xonly = pc[1:]
        tag = hashlib.sha256(b"TapTweak").digest()
        t = int.from_bytes(hashlib.sha256(tag + tag + xonly).digest(), "big")
        if 0 < t < CURVE_N:
            q = PublicKey.combine_keys(
                [PublicKey(b"\x02" + xonly),
                 PrivateKey(t.to_bytes(32, "big")).public_key]
            ).format(compressed=True)
            out.append(("p2tr", b"\x51\x20" + q[1:]))
    except Exception:
        pass
    return out


def keys_for_phrase(phrase, paths):
    """Yield (label, priv32) for every derivation of one phrase."""
    for name, k in direct_keys(phrase).items():
        yield f"direct:{name}", k
    if not paths:
        return
    for sname, seed in seeds_from(phrase).items():
        for p in paths:
            try:
                yield f"{sname}:{p}", derive(seed, p)
            except Exception:
                continue


def selftest(oracle):
    """Prove the pipeline can produce a KNOWN POSITIVE before any null from it
    is treated as meaningful.

    A funded-brainwallet control is NOT usable here: address_map.bin holds only
    currently-funded addresses, and every well-known brainwallet key (sha256(""),
    priv=1, sha256("satoshi") ...) was swept to zero by bots years ago, so all of
    them are legitimately absent. Verified empirically -- 8/8 probed came back
    unfunded.

    So the control is composed instead. The pipeline is
        priv32 --(A)--> scriptPubKey --(B)--> sha256 --> index hit
    and each half is pinned against known-good vectors:

      (A) spks_for_key() must emit byte-identical scriptPubKeys to
          spk_from_address() for BIP44/49/84/86 + uncompressed-brainwallet test
          vectors, covering all five script types this sweep emits.
      (B) oracle.contains_spks() must find genuinely funded addresses when fed
          scriptPubKeys built by spk_from_address.

    (A) and (B) meet at the same scriptPubKey representation, so a pass on both
    closes the chain end to end.
    """
    from index_oracle import spk_from_address

    ok = hd_selftest() == 0            # hd_sweep returns an exit code: 0 == pass
    if not ok:
        sys.stderr.write("hd_sweep selftest FAILED\n")

    mnemonic = ("abandon abandon abandon abandon abandon abandon "
                "abandon abandon abandon abandon abandon about")
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), b"mnemonic", 2048)
    vectors = [
        ("p2pkh_c", derive(seed, "m/44'/0'/0'/0/0"),
         "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"),
        ("p2sh_p2wpkh", derive(seed, "m/49'/0'/0'/0/0"),
         "37VucYSaXLCAsxYyAPfbSi9eh4iEcbShgf"),
        ("p2wpkh", derive(seed, "m/84'/0'/0'/0/0"),
         "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu"),
        ("p2tr", derive(seed, "m/86'/0'/0'/0/0"),
         "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"),
        ("p2pkh_u", hashlib.sha256(b"correct horse battery staple").digest(),
         "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"),
    ]
    sys.stderr.write("  (A) scriptPubKey construction vs known addresses:\n")
    for want_type, priv, addr in vectors:
        built = dict(spks_for_key(priv)).get(want_type)
        expect = spk_from_address(addr)
        good = built is not None and built == expect
        ok &= good
        sys.stderr.write(f"      {want_type:12} {addr[:26]:26} "
                         f"{'OK' if good else 'FAIL'}\n")

    sys.stderr.write("  (B) index lookup on scriptPubKeys of funded addresses:\n")
    known = ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
             "12ib7dApVFvg82TXKycWBNpN8kFyiAN1dr"]
    spks = [spk_from_address(a) for a in known]
    hits = dict(oracle.contains_spks(spks))
    for j, a in enumerate(known):
        good = j in hits
        ok &= good
        sys.stderr.write(f"      {a[:26]:26} "
                         f"{f'{hits[j]/1e8:.4f} BTC OK' if good else 'FAIL'}\n")

    sys.stderr.write("SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases")
    ap.add_argument("--out", default="full_sweep_hits.tsv")
    ap.add_argument("--direct-only", action="store_true")
    ap.add_argument("--batch", type=int, default=20000,
                    help="scriptPubKeys per vectorized index query")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    oracle = Oracle(verbose=True)
    if not oracle.calibrate():
        sys.exit("oracle calibration failed")

    if a.selftest:
        sys.exit(0 if selftest(oracle) else 1)
    if not selftest(oracle):
        sys.exit("refusing to run: a null result would be meaningless")
    if not a.phrases:
        sys.exit("--phrases required")

    paths = [] if a.direct_only else build_paths()
    phrases = [l.rstrip("\n") for l in open(a.phrases, encoding="utf-8", errors="replace")]
    phrases = [p for p in phrases if p.strip()]
    sys.stderr.write(f"\n{len(phrases):,} phrases x {len(paths) or 1} paths "
                     f"-> sweeping against {oracle.n:,} funded addresses\n\n")

    out = open(a.out, "w")
    out.write("phrase\tderivation\tscript_type\tbalance_sats\tbalance_btc\n")

    meta, spks = [], []
    n_addr = n_hit = 0
    t0 = time.time()

    def flush():
        nonlocal meta, spks, n_hit
        if not spks:
            return
        for j, bal in oracle.contains_spks(spks):
            ph, dv, st = meta[j]
            n_hit += 1
            out.write(f"{ph}\t{dv}\t{st}\t{bal}\t{bal/1e8:.8f}\n")
            out.flush()
            sys.stderr.write(f"\n*** HIT  {bal/1e8:.8f} BTC  {st}  "
                             f"{dv}  phrase={ph!r}\n\n")
            sys.stderr.flush()
        meta, spks = [], []

    for i, ph in enumerate(phrases, 1):
        for label, k in keys_for_phrase(ph, paths):
            for st, spk in spks_for_key(k):
                meta.append((ph, label, st))
                spks.append(spk)
                n_addr += 1
            if len(spks) >= a.batch:
                flush()
        if i % 100 == 0:
            el = time.time() - t0
            sys.stderr.write(f"  {i:,}/{len(phrases):,} phrases  "
                             f"{n_addr:,} addrs  {n_hit} hits  "
                             f"{i/el:.1f} ph/s  eta {(len(phrases)-i)/(i/el)/60:.1f}m\n")
            sys.stderr.flush()
    flush()
    out.close()
    sys.stderr.write(f"\nDONE. {len(phrases):,} phrases, {n_addr:,} addresses "
                     f"derived, {n_hit} funded hits -> {a.out}\n")


if __name__ == "__main__":
    main()
