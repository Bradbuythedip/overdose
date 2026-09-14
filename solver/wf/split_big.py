#!/usr/bin/env python3
"""
The additive split over the LARGE clue halves, scored against the FULL index.

WHY THIS IS STRONGER THAN THE STANDALONE TOOL
solve_mitm.py scores pairs against targets_20btc.txt -- 158 candidate addresses
inferred from the ~20 BTC in-window analysis. If the prize is not one of those
158, that run cannot see it. This scores the same pairs against
address_map.bin: every currently-funded address on Bitcoin, 56,795,328 of them.
Given the user's intelligence that the prize is UNSWEPT, its address is in that
set by construction, so a correct split fires here and cannot be missed.

    priv = a + b (mod n)   =>   pub = aG + bG

so both halves become points once (|A| + |B| scalar multiplications) and each
pair costs one point ADDITION instead of a multiplication.

SPEED
Addresses are never encoded. hash160 is turned straight into a scriptPubKey and
handed to the index's vectorized lookup, which skips base58 and bech32 entirely.
A control asserts the hand-built scriptPubKeys equal what the project's own
address parser produces, so the shortcut cannot silently diverge.

p2tr is omitted deliberately: Taproot activated in November 2021, after this
issue went to press, so a 2021 prize key in a Taproot output is implausible.
Stated rather than hidden -- it is a real, if small, gap in this sweep.

  python3 wf/split_big.py --selftest
  python3 wf/split_big.py [--limit N] [--workers K]
"""
import hashlib, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from coincurve import PrivateKey, PublicKey
from hd_sweep import CURVE_N

SOLVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SOLVER)          # halves/ lives at the REPO root
LEFT = os.path.join(ROOT, "halves", "left_serial.txt")
RIGHT = os.path.join(ROOT, "halves", "right_column.txt")
BATCH = 2_000_000


def h160(b):
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


def spks_for(pc, pu):
    """scriptPubKeys straight from the pubkeys -- no address encoding."""
    hc, hu = h160(pc), h160(pu)
    return (b"\x76\xa9\x14" + hc + b"\x88\xac",          # p2pkh compressed
            b"\x76\xa9\x14" + hu + b"\x88\xac",          # p2pkh uncompressed
            b"\x00\x14" + hc,                            # p2wpkh
            b"\xa9\x14" + h160(b"\x00\x14" + hc) + b"\x87")   # p2sh-p2wpkh


def scalar(p):
    return int.from_bytes(hashlib.sha256(p.encode("utf-8")).digest(), "big") % CURVE_N


def load(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [l.rstrip("\n") for l in fh if l.strip()]


def selftest():
    ok = True
    for p in (LEFT, RIGHT):
        good = os.path.exists(p)
        print(f"  {os.path.basename(p)}: {'OK' if good else 'FAIL'}")
        ok &= good
    if not ok:
        print("SELFTEST FAIL"); return False

    # the scriptPubKey shortcut must agree with the project's address parser
    from index_oracle import spk_from_address
    from hd_sweep import addr_p2pkh, addr_p2wpkh, addr_p2sh_p2wpkh
    k = hashlib.sha256(b"control").digest()
    pk = PrivateKey(k).public_key
    pc, pu = pk.format(True), pk.format(False)
    mine = spks_for(pc, pu)
    theirs = (spk_from_address(addr_p2pkh(pc)), spk_from_address(addr_p2pkh(pu)),
              spk_from_address(addr_p2wpkh(pc)),
              spk_from_address(addr_p2sh_p2wpkh(pc)))
    good = mine == theirs
    print(f"  spk shortcut == address parser: {'OK' if good else 'FAIL'}")
    ok &= good

    # point addition must equal scalar addition
    ka, kb = scalar("__a__"), scalar("__b__")
    direct = PrivateKey(((ka + kb) % CURVE_N).to_bytes(32, "big")).public_key
    comb = PublicKey.combine_keys([
        PrivateKey(ka.to_bytes(32, "big")).public_key,
        PrivateKey(kb.to_bytes(32, "big")).public_key])
    good = direct.format() == comb.format()
    print(f"  aG + bG == (a+b)G: {'OK' if good else 'FAIL'}")
    ok &= good

    # the index must see a known funded scriptPubKey (genesis coinbase)
    full = H.full_index()
    good = full is not None
    if good:
        gspk = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        good = len(full.contains_spks([gspk])) == 1
    print(f"  full index sees genesis: {'OK' if good else 'FAIL'}")
    ok &= good

    # and must NOT see an unfunded one. NOT a burn address -- 1BitcoinEater...
    # actually holds a balance, because people really do burn coins to it. A
    # freshly derived key is unfunded with overwhelming probability.
    if full is not None:
        fresh = PrivateKey(hashlib.sha256(os.urandom(32)).digest()).public_key
        fspk = spks_for(fresh.format(True), fresh.format(False))[0]
        good = len(full.contains_spks([fspk])) == 0
        print(f"  index rejects a fresh key: {'OK' if good else 'FAIL'}")
        ok &= good

    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")

    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    A, B = load(LEFT), load(RIGHT)
    if limit:
        A = A[:limit]
    print(f"\nleft {len(A):,}  right {len(B):,}  pairs {len(A)*len(B):,}")

    t0 = time.time()
    ka = [scalar(p) for p in A]
    kb = [scalar(p) for p in B]
    PA = [PrivateKey(k.to_bytes(32, "big")).public_key for k in ka]
    PB = [PrivateKey(k.to_bytes(32, "big")).public_key for k in kb]
    print(f"precomputed {len(PA):,} + {len(PB):,} points in {time.time()-t0:.1f}s",
          flush=True)

    full = H.full_index()
    hits, n_pairs, n_spk, t1 = [], 0, 0, time.time()
    spks, meta = [], []

    def flush():
        nonlocal n_spk, spks, meta
        if not spks:
            return
        for j, bal in full.contains_spks(spks):
            i, jj, t = meta[j]
            priv = (ka[i] + kb[jj]) % CURVE_N
            h = (A[i], B[jj], t, f"{priv:064x}", bal)
            hits.append(h)
            print(f"\n*** HIT *** {A[i]!r} + {B[jj]!r} -> {t} "
                  f"{bal/1e8:.8f} BTC  priv {priv:064x}", flush=True)
            open(os.path.join(SOLVER, "SPLIT_HITS.txt"), "a").write(repr(h) + "\n")
        n_spk += len(spks)
        spks, meta = [], []

    TYPES = ("p2pkh_c", "p2pkh_u", "p2wpkh", "p2sh_p2wpkh")
    for i, pa in enumerate(PA):
        for j, pb in enumerate(PB):
            try:
                s = PublicKey.combine_keys([pa, pb])
            except Exception:
                continue
            n_pairs += 1
            for t, spk in zip(TYPES, spks_for(s.format(True), s.format(False))):
                spks.append(spk); meta.append((i, j, t))
            if len(spks) >= BATCH:
                flush()
        if i % 50 == 0 and i:
            el = time.time() - t1
            rate = n_pairs / max(el, 1e-9)
            tot = len(PA) * len(PB)
            print(f"  {i}/{len(PA)} left  {n_pairs:,}/{tot:,} pairs  "
                  f"{rate:,.0f} pair/s  eta {(tot-n_pairs)/max(rate,1e-9)/60:.0f} min",
                  flush=True)
    flush()

    print(f"\npairs {n_pairs:,}  scriptPubKeys {n_spk:,}  "
          f"in {time.time()-t1:.0f}s")
    print("split-big hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
