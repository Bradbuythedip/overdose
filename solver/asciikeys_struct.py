#!/usr/bin/env python3
"""Every structural read's raw UTF-8 bytes as key material (head/tail 32)."""
import sys
from full_sweep import spks_for_key
from spk_extra import spks_extra
import continuous_solver as CS
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
rows = [l.rstrip("\n") for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
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
    b = s.encode("utf-8")
    for tag, k in (("ascii_head", b[:32]), ("ascii_tail", b[-32:])):
        if len(k) == 32 and 0 < int.from_bytes(k, "big") < N:
            for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                meta.append((s[:120], tag, st)); spks.append(spk); n += 1
    if len(spks) >= 40000: flush()
    if i % 2000 == 0: sys.stderr.write(f"\r {i}/{len(rows)} {n:,} spks ")
flush()
sys.stderr.write(f"\n{n:,} scriptPubKeys, {hits} hit(s)\n")
