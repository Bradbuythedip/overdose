#!/usr/bin/env python3
"""Structural letter streams interpreted AS key bytes: raw ASCII windows and
a=1..26 / a=0..25 ordinal maps, 32-byte head and tail."""
import sys
from full_sweep import spks_for_key
from spk_extra import spks_extra
import continuous_solver as CS
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
rows = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
def keys(s):
    out = []
    b = s.encode()
    low = s.lower()
    m1 = bytes((ord(c) - 96) % 256 for c in low)
    m0 = bytes((ord(c) - 97) % 256 for c in low)
    for tag, arr in (("ascii", b), ("a1", m1), ("a0", m0)):
        for t2, k in ((tag + "_head", arr[:32]), (tag + "_tail", arr[-32:])):
            if len(k) == 32 and 0 < int.from_bytes(k, "big") < N:
                out.append((t2, k))
    return out
orc = CS.IndexOracle()
if not orc.ready: sys.exit("no oracle: " + orc.why)
if not orc.control(): sys.exit("POSITIVE CONTROL FAILED")
sys.stderr.write("control OK\n")
meta, spks, n, hits = [], [], 0, 0
def flush():
    global meta, spks, hits
    if not spks: return
    for j, bal in orc.check(spks):
        hits += 1
        print(f"HIT\t{bal}\t{meta[j][1]}\t{meta[j][2]}\t{meta[j][0]}")
        sys.stdout.flush()
    meta, spks = [], []
for i, s in enumerate(rows, 1):
    for tag, k in keys(s):
        for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
            meta.append((s[:120], tag, st)); spks.append(spk); n += 1
        if len(spks) >= 40000: flush()
    if i % 500 == 0: sys.stderr.write(f"\r {i}/{len(rows)} {n:,} spks ")
flush()
sys.stderr.write(f"\n{n:,} scriptPubKeys, {hits} hit(s)\n")
