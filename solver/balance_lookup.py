#!/usr/bin/env python3
"""Look up Bitcoin address balances in address_map.bin (seed-safe/btc-balance).

Binary format:
  Header (132 bytes, LE):
    uint32 magic = 0x50414D41 ("AMAP")
    uint16 version = 1
    uint16 hdr_len
    uint64 n_records
    uint16 rec_size = 40
    uint8  source_kind
    uint8  pad0
    uint64 source_height
    [32]   source_hash
    uint64 created_unix
    [64]   reserved
  Records (40 bytes each, sorted by scripthash):
    [32] scripthash = SHA256(scriptPubKey), Electrum-style (NOT reversed)
    uint64 sum (balance in satoshis)
  Footer: 4-byte CRC32C
"""
import sys, os, struct, hashlib, mmap, bisect, argparse

# ---- Address -> scriptPubKey ----
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
B58_ALPHA = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_IDX = {c:i for i,c in enumerate(B58_ALPHA)}

def b58decode(s):
    n = 0
    for c in s.encode():
        if c not in B58_IDX: raise ValueError("bad b58 char")
        n = n*58 + B58_IDX[c]
    h = n.to_bytes((n.bit_length()+7)//8, 'big')
    # leading 1s -> leading 0 bytes
    zeros = 0
    for c in s.encode():
        if c == 0x31: zeros += 1
        else: break
    return b'\x00'*zeros + h

def b58check_decode(s):
    raw = b58decode(s)
    if len(raw) < 4: raise ValueError("short b58check")
    payload, csum = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != csum:
        raise ValueError("bad b58check checksum")
    return payload[:1], payload[1:]

def bech32_polymod(values):
    GEN = [0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3]
    c = 1
    for v in values:
        b = c >> 25
        c = ((c & 0x1ffffff) << 5) ^ v
        for i in range(5):
            c ^= GEN[i] if ((b>>i)&1) else 0
    return c

def bech32_decode(addr):
    addr = addr.lower()
    pos = addr.rfind('1')
    if pos < 1 or pos+7 > len(addr): raise ValueError("bech32 sep")
    hrp = addr[:pos]
    data = []
    for c in addr[pos+1:]:
        idx = BECH32_CHARSET.find(c)
        if idx < 0: raise ValueError("bech32 char")
        data.append(idx)
    hrp_expand = [ord(c)>>5 for c in hrp] + [0] + [ord(c)&31 for c in hrp]
    pm = bech32_polymod(hrp_expand + data)
    if pm == 1:  spec='bech32'
    elif pm == 0x2bc830a3: spec='bech32m'
    else: raise ValueError("bech32 checksum")
    return hrp, data[:-6], spec

def convertbits(data, frombits, tobits, pad=True):
    acc = 0; bits = 0; ret = []
    maxv = (1<<tobits)-1
    for v in data:
        acc = (acc<<frombits) | v
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc>>bits) & maxv)
    if pad and bits:
        ret.append((acc<<(tobits-bits)) & maxv)
    return ret

def script_from_address(addr):
    if addr.startswith(('bc1','BC1','tb1','TB1')):
        hrp, data, spec = bech32_decode(addr)
        witver = data[0]
        witprog = bytes(convertbits(data[1:], 5, 8, False))
        if witver == 0:
            op = 0x00
        elif witver >= 1 and witver <= 16:
            op = 0x50 + witver  # OP_1..OP_16
        else:
            raise ValueError("bad witver")
        return bytes([op, len(witprog)]) + witprog
    ver, pk = b58check_decode(addr)
    if ver == b'\x00':
        if len(pk) != 20: raise ValueError("p2pkh len")
        return bytes([0x76, 0xA9, 0x14]) + pk + bytes([0x88, 0xAC])
    if ver == b'\x05':
        if len(pk) != 20: raise ValueError("p2sh len")
        return bytes([0xA9, 0x14]) + pk + bytes([0x87])
    raise ValueError(f"unsupported version {ver}")

def address_to_scripthash(addr):
    return hashlib.sha256(script_from_address(addr)).digest()

# ---- Reader ----
HEADER_FMT = '<IHHQHBB' + 'Q' + '32s' + 'Q' + '64s'
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # should be 132
assert HEADER_SIZE == 132, HEADER_SIZE

class BalanceIndex:
    def __init__(self, path):
        self.path = path
        f = open(path, 'rb')
        self.f = f
        st = os.fstat(f.fileno())
        self.size = st.st_size
        self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        hdr = self.mm[:HEADER_SIZE]
        (self.magic, self.version, self.hdr_len, self.n_records,
         self.rec_size, self.source_kind, _pad,
         self.source_hgt, self.source_hash, self.created, _res) = struct.unpack(HEADER_FMT, hdr)
        if self.magic != 0x50414D41:
            raise ValueError(f"bad magic {self.magic:#x}")
        if self.rec_size != 40:
            raise ValueError("bad rec size")
        self.recs_base = self.hdr_len
        # records occupy n_records * 40 bytes
        # the 4-byte CRC32C trailer is after them

    def __getitem__(self, i):
        off = self.recs_base + i * 40
        return self.mm[off:off+32], int.from_bytes(self.mm[off+32:off+40], 'little')

    def lookup(self, scripthash):
        # binary search
        lo, hi = 0, self.n_records
        while lo < hi:
            mid = (lo + hi) // 2
            off = self.recs_base + mid * 40
            k = self.mm[off:off+32]
            if k < scripthash:  lo = mid + 1
            elif k > scripthash: hi = mid
            else:
                return int.from_bytes(self.mm[off+32:off+40], 'little')
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('addresses', nargs='*', help='addresses to look up')
    ap.add_argument('--file', help='TSV with addresses in column 4')
    ap.add_argument('--index', default='/tmp/address_map.bin')
    ap.add_argument('--min-sats', type=int, default=0)
    ap.add_argument('--header', action='store_true')
    args = ap.parse_args()

    bi = BalanceIndex(args.index)
    sys.stderr.write(f"index ok: {bi.n_records:,} records, source_height={bi.source_hgt}\n")

    targets = []
    if args.addresses:
        for a in args.addresses:
            targets.append(('', '', '', a))
    if args.file:
        with open(args.file) as f:
            if args.header: next(f)
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 4: continue
                targets.append(tuple(parts[:4]))

    hits = 0
    print('phrase\thash_kind\taddr_type\taddress\tbalance_sats\tbalance_btc')
    for phrase, hk, at, addr in targets:
        try:
            sh = address_to_scripthash(addr)
        except Exception as e:
            print(f'{phrase}\t{hk}\t{at}\t{addr}\tERR\t{e}', file=sys.stderr)
            continue
        bal = bi.lookup(sh)
        if bal is None or bal < args.min_sats: continue
        hits += 1
        print(f'{phrase}\t{hk}\t{at}\t{addr}\t{bal}\t{bal/1e8:.8f}')
    sys.stderr.write(f"done: {hits} addresses with balance >= {args.min_sats}\n")

if __name__ == '__main__':
    main()
