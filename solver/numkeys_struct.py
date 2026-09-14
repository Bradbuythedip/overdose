#!/usr/bin/env python3
"""Structural number sequences interpreted AS the key material itself:
decimal integer, hex digits, and per-number byte arrays. Not a passphrase
hash -- the position counts are the key."""
import re, sys
sys.path.insert(0, "/home/user/overdose/solver")
from full_sweep import spks_for_key
from spk_extra import spks_extra
import continuous_solver as CS

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
src = sys.argv[1]
rows = [l.rstrip("\n") for l in open(src, encoding="utf-8") if l.strip()]

def keyints(s):
    out = []
    digits = re.sub(r"\D", "", s)
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if digits:
        v = int(digits)
        if 0 < v < N:
            out.append(("dec", v.to_bytes(32, "big")))
        out.append(("dec_modn", (v % N).to_bytes(32, "big")))
        rv = int(digits[::-1])
        out.append(("decrev_modn", (rv % N).to_bytes(32, "big")))
        # digits as hex
        h = digits
        for tag, hh in (("hex_head", h[:64]), ("hex_tail", h[-64:]),
                        ("hex_pad", h.rjust(64, "0")[-64:])):
            if len(hh) == 64:
                try:
                    b = bytes.fromhex(hh)
                    if 0 < int.from_bytes(b, "big") < N:
                        out.append((tag, b))
                except ValueError:
                    pass
    if len(nums) >= 8:
        for tag, seq in (("bytes", nums), ("bytesrev", nums[::-1])):
            b = bytes(x % 256 for x in seq)
            for t2, bb in ((tag + "_head", b[:32]), (tag + "_tail", b[-32:]),
                           (tag + "_pad", b.rjust(32, b"\0")[-32:])):
                if len(bb) == 32 and 0 < int.from_bytes(bb, "big") < N:
                    out.append((t2, bb))
    return out

orc = CS.IndexOracle()
if not orc.ready:
    sys.exit("no oracle: " + orc.why)
if not orc.control():
    sys.exit("POSITIVE CONTROL FAILED")
sys.stderr.write("control OK\n")

meta, spks, n, hits = [], [], 0, 0
def flush():
    global meta, spks, hits
    if not spks:
        return
    for j, bal in orc.check(spks):
        hits += 1
        print(f"HIT\t{bal}\t{meta[j][1]}\t{meta[j][2]}\t{meta[j][0]}")
        sys.stdout.flush()
    meta, spks = [], []

for i, s in enumerate(rows, 1):
    for tag, k in keyints(s):
        for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
            meta.append((s[:120], tag, st)); spks.append(spk); n += 1
        if len(spks) >= 40000:
            flush()
    if i % 100 == 0:
        sys.stderr.write(f"\r {i}/{len(rows)}  {n:,} spks ")
flush()
sys.stderr.write(f"\n{n:,} scriptPubKeys, {hits} hit(s)\n")
