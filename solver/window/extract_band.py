#!/usr/bin/env python3
"""FR4 target-set extraction from address_map.bin.
NOTE: dtype MUST be 'V32' (void), not 'S32' — numpy's bytes dtype strips
trailing NUL bytes, which silently truncates any scripthash ending in 0x00."""
import numpy as np, struct, sys

IDX = '/tmp/od/address_map.bin'
f = open(IDX, 'rb')
magic, ver, hdr_len, n, rec, *_ = struct.unpack('<IHHQHBB'+'Q'+'32s'+'Q'+'64s', f.read(132))
assert magic == 0x50414D41 and rec == 40, "bad index"
sys.stderr.write(f"index: {n:,} records\n")

dt = np.dtype([('sh', 'V32'), ('bal', '<u8')])
mm = np.memmap(IDX, dtype=dt, mode='r', offset=hdr_len, shape=(n,))

S = 100_000_000
BANDS = {
    'b1_19.5_20.5' : (int(19.5*S), int(20.5*S)),
    'b1_19.0_21.0' : (int(19.0*S), int(21.0*S)),
    'b2_39.0_41.0' : (int(39.0*S), int(41.0*S)),
    'b3_58.5_61.5' : (int(58.5*S), int(61.5*S)),
    'exact_20'     : (20*S, 20*S),
}
counts = {k: 0 for k in BANDS}
outs = {k: open(f'/tmp/od/band_{k}.tsv', 'w') for k in BANDS}
for fh in outs.values():
    fh.write('scripthash_hex\tbalance_sats\tbalance_btc\n')

CH = 2_000_000
for start in range(0, n, CH):
    blk = mm[start:min(start+CH, n)]
    bal = blk['bal']
    for k, (lo, hi) in BANDS.items():
        m = (bal >= lo) & (bal <= hi)
        c = int(m.sum())
        if not c: continue
        counts[k] += c
        sh = blk['sh'][m]; bb = bal[m]
        w = outs[k].write
        for i in range(c):
            v = int(bb[i])
            w(f"{sh[i].tobytes().hex()}\t{v}\t{v/1e8:.8f}\n")

for fh in outs.values(): fh.close()
sys.stderr.write("FINAL COUNTS\n")
for k, (lo, hi) in BANDS.items():
    sys.stderr.write(f"  {k:16s} [{lo/1e8:>8.2f},{hi/1e8:>8.2f}] BTC -> {counts[k]:,}\n")
