#!/usr/bin/env python3
"""
Test the LOW-ENTROPY KEY-VALUE space directly against the funding-tx addresses.

DIFFERENT FROM EVERY PRIOR SWEEP
Every derivation here hashes text into a key. This tests key VALUES a human
picks by hand -- the way the 1000 BTC puzzle uses small/patterned keys. We have
the addresses' hash160s, so we check key values directly: does privkey = k
produce this address, for k a small integer, a date, a round number, a serial,
or the article's own numbers used raw?

  python3 lowentropy.py --selftest
  python3 lowentropy.py --max-int 3000000
"""
import argparse, hashlib, itertools, sys
from coincurve import PrivateKey

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

TARGETS = {  # h160 -> label
 bytes.fromhex("735f452fed8ca297de0484be1b63200b726077c1"): "1BX2q prize out",
 bytes.fromhex("a94072ffa9dec8ab9762359919fb97aaf87359a0"): "1GRv change out",
}
# input h160s from their pubkeys
def h160(b): return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()
for pub,lab in (("02247fd4365fceb03c66643a40839cdc4ee13cd3ea374824e814a3368c946c6720","1A3RB in0"),
                ("02b2bb89fd735a29dc904a704948761dacf95ff3163b65337e0c7414ab401c82ab","1BCYm in1")):
    TARGETS[h160(bytes.fromhex(pub))] = lab
TSET = set(TARGETS)


def check(k):
    """k int -> label if its p2pkh (either pubkey form) is a target, else None."""
    if not (0 < k < N):
        return None
    kb = k.to_bytes(32, "big")
    pk = PrivateKey(kb)
    for comp in (True, False):
        if h160(pk.public_key.format(comp)) in TSET:
            return TARGETS[h160(pk.public_key.format(comp))]
    return None


def structured():
    """Named low-entropy key values that are not small sequential ints."""
    vals = {}
    # dates
    for y in range(2008, 2024):
        for m in range(1, 13):
            for d in range(1, 32):
                vals[f"date{y:04d}{m:02d}{d:02d}"] = int(f"{y:04d}{m:02d}{d:02d}")
    # round numbers and powers
    for k in range(1, 200):
        vals[f"10^{k}"] = 10 ** k % N
        vals[f"2^{k}"] = 2 ** k
    # repeated / patterned bytes
    for b in range(1, 256):
        vals[f"rep{b}"] = int.from_bytes(bytes([b]) * 32, "big") % N
    vals["0x0..01"] = 1
    for nяб in (1,): pass
    # the article's numbers and the serials/id as raw values
    nums = [2008,1971,2011,2017,1969,42,40,51,85,95,10,20,21000000,
            76841714,46279860,20374262,2000000000,12,165,572]
    for nv in nums:
        vals[f"num{nv}"] = nv
    for a,b in itertools.permutations([76841714,46279860,20374262],2):
        vals[f"{a}{b}"] = int(f"{a}{b}") % N
    # 20 BTC in sats, satoshi-flavoured constants
    for c in (2000000000, 2000000000000, 1299, 74820403884):
        vals[f"const{c}"] = c
    return vals


def selftest():
    ok = True
    # a planted target: put a known small key's address into TSET and find it
    kb = (12345).to_bytes(32, "big")
    planted = h160(PrivateKey(kb).public_key.format(True))
    TSET.add(planted); TARGETS[planted] = "PLANT"
    got = check(12345)
    ok &= got == "PLANT"
    sys.stderr.write(f"  a planted key value 12345 is found by check(): "
                     f"{'OK' if got=='PLANT' else 'FAIL'}\n")
    TSET.discard(planted); TARGETS.pop(planted, None)
    ok &= check(12345) is None
    sys.stderr.write(f"  and not found once removed: "
                     f"{'OK' if check(12345) is None else 'FAIL'}\n")
    ok &= len(TSET) == 4
    sys.stderr.write(f"  {len(TSET)} real target addresses loaded\n")
    s = structured()
    sys.stderr.write(f"  {len(s)} structured low-entropy candidates\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-int", type=int, default=3_000_000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("bad setup")
    if a.selftest:
        return
    hits = []
    # structured first
    for name, v in structured().items():
        r = check(v)
        if r:
            hits.append((name, v, r))
            sys.stderr.write(f"\n  *** HIT {r}: {name} = {v}\n")
    sys.stderr.write(f"  {len(structured())} structured values tested\n")
    # small sequential integers
    import time
    t = time.time()
    for k in range(1, a.max_int + 1):
        r = check(k)
        if r:
            hits.append((f"int{k}", k, r))
            sys.stderr.write(f"\n  *** HIT {r}: private key = {k}\n")
        if k % 250000 == 0:
            sys.stderr.write(f"\r  {k:,}/{a.max_int:,} ints  "
                             f"{k/(time.time()-t):.0f}/s  ")
            sys.stderr.flush()
    sys.stderr.write(f"\n\n  small ints 1..{a.max_int:,} + structured: "
                     f"{len(hits)} hit(s)\n")
    if not hits:
        sys.stderr.write("  no low-entropy key value produces any of the four "
                         "funding-tx addresses.\n")


if __name__ == "__main__":
    main()
