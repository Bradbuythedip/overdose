#!/usr/bin/env python3
"""
An April-2023 RICH-LIST index. Read the limitation below before using it.

WHAT IT ACTUALLY ANSWERS
"Did this address hold a large balance in April 2023?" — nothing more.

WHAT IT WAS BUILT TO ANSWER, AND DOES NOT
It was written to close the swept-key blind spot: address_map.bin holds only
CURRENTLY-funded addresses, so a key that was cracked and drained years ago
reports 0 hits even when handed the correct private key. The intended fix was
that an April-2023 snapshot would record addresses "funded at that time,
regardless of what happened since".

That is only half true, and the half that fails is the important one. A rich
list catches an address that held a balance ON the snapshot date and is empty
now. It cannot catch an address funded and swept BEFORE that date, because a
drained address has zero balance and is not on any rich list.

THE CONTROL THAT PROVES IT
The original selftest checked three addresses that were funded at snapshot time
and confirmed they were present. It never checked a known-SWEPT address, so the
limitation was invisible. Running that control: 32 canonical brainwallet
phrases x 2 pubkey forms = 64 addresses, every one demonstrably funded once and
drained by crackers years ago — 0 of 64 are in this index, and 0 of 64 are in
address_map.bin either. The two oracles are two instants, not an interval.

So a null from this index means "not rich in April 2023", and a null from both
means "not holding coins at either of two moments". Neither means "never
funded". Closing that properly needs every output ever created — a full chain
scan or an ever-used-address dump — which is not in this tree.

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
    # COVERAGE CONTROL. Known-swept brainwallets must be reported ABSENT, and
    # that absence is the limitation of this index, not a bug. Asserting it
    # here stops the module from ever being described again as an "ever-funded"
    # oracle: it is a balance snapshot, and these addresses prove it.
    import hashlib as _h
    try:
        from coincurve import PrivateKey as _PK
        from hd_sweep import h160 as _h160
        swept, seen = ["satoshi", "password", "correct horse battery staple"], 0
        spks = []
        for p in swept:
            k = _h.sha256(p.encode()).digest()
            for comp in (False, True):
                pub = _PK(k).public_key.format(compressed=comp)
                spks.append(b"\x76\xa9\x14" + _h160(pub) + b"\x88\xac")
        seen = len(h.contains_spks(spks))
        sys.stderr.write(f"  COVERAGE: {len(spks)} known-SWEPT brainwallet "
                         f"addresses found in this index: {seen} "
                         f"(expected 0 — this index cannot see swept keys)\n")
        ok &= seen == 0
    except Exception as e:            # missing deps must not silently pass
        sys.stderr.write(f"  COVERAGE control could not run: {e}\n")
        ok = False
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
