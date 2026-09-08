#!/usr/bin/env python3
"""Scan all 56.8M records in address_map.bin and emit any with balance in
the range [LOW, HIGH] (default 19–21 BTC). Then we will look those up in
the full address dataset to recover their string form."""
import sys, os, mmap, struct, argparse

HEADER_SIZE = 132
REC_SIZE = 40

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', default='/tmp/address_map.bin')
    ap.add_argument('--low-sats', type=int, default=int(19.0 * 1e8))
    ap.add_argument('--high-sats', type=int, default=int(21.0 * 1e8))
    ap.add_argument('--out', default='/tmp/balance_20btc_scripthashes.bin')
    ap.add_argument('--out-hex', default='/tmp/balance_20btc.tsv')
    args = ap.parse_args()

    f = open(args.index,'rb')
    st = os.fstat(f.fileno()); size = st.st_size
    mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
    hdr_fmt = '<IHHQHBB' + 'Q' + '32s' + 'Q' + '64s'
    magic, version, hdr_len, n, rec_size, *_ = struct.unpack(hdr_fmt, mm[:HEADER_SIZE])
    assert magic == 0x50414D41
    sys.stderr.write(f"index ok: {n:,} records\n")
    base = hdr_len

    out_bin = open(args.out, 'wb')
    out_hex = open(args.out_hex, 'w')
    out_hex.write('scripthash_hex\tbalance_sats\tbalance_btc\n')
    found = 0
    # iterate
    chunk = 1 << 16
    for start in range(0, n, chunk):
        end = min(start+chunk, n)
        block = mm[base + start*REC_SIZE : base + end*REC_SIZE]
        for i in range(end - start):
            off = i * REC_SIZE
            bal = int.from_bytes(block[off+32:off+40], 'little')
            if args.low_sats <= bal <= args.high_sats:
                sh = bytes(block[off:off+32])
                out_bin.write(sh)
                out_hex.write(f"{sh.hex()}\t{bal}\t{bal/1e8:.8f}\n")
                found += 1
        if start % (chunk * 16) == 0:
            sys.stderr.write(f"[{start:,}/{n:,}] found={found}\n")
    out_bin.close(); out_hex.close()
    sys.stderr.write(f"DONE found={found} in range [{args.low_sats},{args.high_sats}] sats\n")

if __name__ == '__main__':
    main()
