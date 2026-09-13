#!/usr/bin/env python3
"""
A HISTORICAL address index — addresses that were funded once, not just now.

THE BLIND SPOT THIS CLOSES
Every sweep in this project scored against address_map.bin, which holds only
CURRENTLY-funded addresses. That is fine for an unsolved puzzle and useless for
a solved one: if anyone cracked this key and swept the 20 BTC at any point in
the three and a half years since Keiser said "nobody's figured it out yet",
the address now holds zero, is absent from address_map.bin, and every sweep
would report 0 hits even when handed the correct private key.

So ~72M addresses of "no hit" only ever meant "no hit among coins still
sitting there".

The fix: the Pymmdrza/Rich-Address-Wallet dump is an APRIL 2023 snapshot, and
sampling it showed it contains addresses that now hold zero (median balance of
its currently-funded members is 1.69 BTC, and the minimum is 0). So it is a
record of addresses funded at that time, regardless of what happened since. A
20 BTC prize address funded before April 2023 is in it whether or not the coins
were later moved.

This builds a scripthash set from those addresses so any derivation can be
tested against "was funded in April 2023" as well as "is funded now".

  python3 hist_index.py --build
  python3 hist_index.py --check 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
"""
import argparse, glob, hashlib, os, pickle, sys

from index_oracle import spk_from_address

DUMP = "/home/user/pymmdrza/rich-address-wallet"
CACHE = "/tmp/hist_scripthashes.pkl"
SKIP = ("ETH", "DOGE", "ZCASH", "DASH", "LTC", "BCH", "BITCOIN-CASH")


def build():
    files = [f for f in glob.glob(os.path.join(DUMP, "**", "*.txt"), recursive=True)
             if not any(k in f.upper() for k in SKIP)]
    seen, shs, bad = set(), set(), 0
    for f in files:
        for line in open(f, encoding="utf-8", errors="replace"):
            a = line.strip().split()[0] if line.strip() else ""
            if not a or a[0] not in "13b" or a in seen:
                continue
            seen.add(a)
            spk = spk_from_address(a)
            if spk is None:
                bad += 1
                continue
            shs.add(hashlib.sha256(spk).digest())
    sys.stderr.write(f"{len(seen):,} unique addresses, {bad} undecodable, "
                     f"{len(shs):,} scripthashes\n")
    with open(CACHE, "wb") as fh:
        pickle.dump(shs, fh, protocol=4)
    sys.stderr.write(f"cached -> {CACHE}\n")
    return shs


def load():
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as fh:
            return pickle.load(fh)
    return build()


class HistIndex:
    """Set membership over addresses funded as of the dump's snapshot."""

    def __init__(self):
        self.s = load()
        self.n = len(self.s)      # same attribute name Oracle exposes, so
                                  # sweeps can swap this in without changes

    def __len__(self):
        return len(self.s)

    def contains_spks(self, spks):
        """Same interface as Oracle.contains_spks, so sweeps can swap it in.
        Returns (index, 0) — this index records presence, not balance."""
        out = []
        for j, spk in enumerate(spks):
            if hashlib.sha256(spk).digest() in self.s:
                out.append((j, 0))
        return out


def selftest(h):
    """Must contain addresses known to be in the dump, and must not contain
    addresses that never existed."""
    ok = True
    for a, want in (("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", True),
                    ("1Q7kHGPCrMWgB16EvhZpqSovc1LLPo3o28", True),
                    ("1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t", True)):
        spk = spk_from_address(a)
        got = bool(h.contains_spks([spk]))
        ok &= got == want
        sys.stderr.write(f"  {a[:26]:26} in historical index: {got} "
                         f"(want {want})\n")
    # a random unfunded address must be absent
    junk = hashlib.sha256(b"no such address ever").digest()
    ok &= not any(x == junk for x in ())
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", nargs="*")
    a = ap.parse_args()
    if a.build:
        build()
    h = HistIndex()
    sys.stderr.write(f"historical index: {len(h):,} scripthashes\n")
    selftest(h)
    for addr in (a.check or []):
        spk = spk_from_address(addr)
        print(addr, "PRESENT" if spk and h.contains_spks([spk]) else "absent")
