#!/usr/bin/env python3
"""Stream the Qalander/bitcoin-all-addresses repo, compute the scripthash
of every address, and emit those whose scripthash is in our 8053-entry
'~20 BTC' set. Output: TSV of (address, balance_sats)."""
import sys, os, mmap, struct, hashlib, urllib.request, time
from itertools import product

# Load target scripthashes -> balance map
def load_targets():
    m = {}
    with open('/tmp/balance_20btc.tsv') as f:
        next(f)
        for line in f:
            sh_hex, sats, _btc = line.rstrip('\n').split('\t')
            m[bytes.fromhex(sh_hex)] = int(sats)
    return m

# Address -> scriptPubKey (subset of balance_lookup.py)
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
B58_ALPHA = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_IDX = {c:i for i,c in enumerate(B58_ALPHA)}

def b58decode(s):
    n = 0
    sb = s.encode()
    for c in sb:
        idx = B58_IDX.get(c, -1)
        if idx < 0: raise ValueError(c)
        n = n*58 + idx
    h = n.to_bytes((n.bit_length()+7)//8, 'big')
    zeros = 0
    for c in sb:
        if c == 0x31: zeros += 1
        else: break
    return b'\x00'*zeros + h

def b58check(s):
    raw = b58decode(s)
    if len(raw) < 5: raise ValueError("short")
    payload, csum = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != csum:
        raise ValueError("checksum")
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
    if pos < 1 or pos+7 > len(addr): raise ValueError("sep")
    hrp = addr[:pos]
    data = []
    for c in addr[pos+1:]:
        idx = BECH32_CHARSET.find(c)
        if idx < 0: raise ValueError("char")
        data.append(idx)
    exp = [ord(c)>>5 for c in hrp] + [0] + [ord(c)&31 for c in hrp]
    pm = bech32_polymod(exp + data)
    if pm != 1 and pm != 0x2bc830a3: raise ValueError("checksum")
    return data[:-6]

def convertbits(data, frombits, tobits, pad=True):
    acc=0; bits=0; ret=[]
    maxv=(1<<tobits)-1
    for v in data:
        acc=(acc<<frombits)|v; bits+=frombits
        while bits>=tobits:
            bits-=tobits; ret.append((acc>>bits)&maxv)
    if pad and bits: ret.append((acc<<(tobits-bits))&maxv)
    return ret

def script_from(addr):
    if addr.startswith(('bc1','tb1')):
        data = bech32_decode(addr)
        witver = data[0]
        witprog = bytes(convertbits(data[1:], 5, 8, False))
        op = 0x00 if witver==0 else (0x50+witver)
        return bytes([op, len(witprog)]) + witprog
    ver, pk = b58check(addr)
    if ver == b'\x00':
        return bytes([0x76,0xA9,0x14]) + pk + bytes([0x88,0xAC])
    if ver == b'\x05':
        return bytes([0xA9,0x14]) + pk + bytes([0x87])
    raise ValueError(f"ver {ver.hex()}")

def main():
    targets = load_targets()
    sys.stderr.write(f"loaded {len(targets)} target scripthashes\n")
    out = open('/tmp/btc_20btc_addrs.tsv','w')
    out.write('address\tbalance_sats\tbalance_btc\n')
    BASE = 'https://raw.githubusercontent.com/Qalander/bitcoin-all-addresses/master/'
    names = []
    for a,b in product('abcdefghijklmnopqrstuvwxyz', repeat=2):
        names.append('x'+a+b)
    t0 = time.time(); total=0; hits=0
    for name in names:
        url = BASE + name
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'overdose/1.0'})
            r = urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                sys.stderr.write(f"end at {name}\n"); break
            raise
        n = 0; h = 0
        for raw in r:
            line = raw.decode('utf-8','replace').rstrip('\n')
            if not line or line == 'recipient': continue
            n += 1
            try:
                sh = hashlib.sha256(script_from(line)).digest()
            except Exception:
                continue
            if sh in targets:
                bal = targets[sh]
                row = f'{line}\t{bal}\t{bal/1e8:.8f}\n'
                out.write(row); out.flush()
                h += 1; hits += 1
        total += n
        sys.stderr.write(f"[{name}] +{n} +{h}h | total {total:,} {hits}h {time.time()-t0:.0f}s\n")
        sys.stderr.flush()
    out.close()
    sys.stderr.write(f"DONE total={total:,} hits={hits} time={time.time()-t0:.0f}s\n")

if __name__ == '__main__':
    main()
