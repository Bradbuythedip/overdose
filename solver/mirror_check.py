#!/usr/bin/env python3
"""
The secp256k1 mirror: for every candidate private key k, also test n - k.

Prior work mirrored the *text* (reversed strings, atbash, ROT13, ...) and then
hashed. It never mirrored the *key*. That leaves an untested half of the search
space, and it is nearly free: k and n-k share a public-key x-coordinate and have
flipped y, so for a compressed key the mirror is literally the prefix byte
02 <-> 03. No extra elliptic-curve multiplication.

Also tests four key-level involutions that a "mirror writing" hint could mean
literally: byte reversal, bit reversal, hex-nibble reversal, bitwise complement.

Everything is checked against address_map.bin, so this needs NO network.

  python3 mirror_check.py --phrases candidates_v2.txt --index /tmp/od/address_map.bin
"""
import argparse, hashlib, hmac, mmap, os, struct, sys, time
import coincurve

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 2**256 - 2**32 - 977

def h160(b): return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()
def sha(b):  return hashlib.sha256(b).digest()

class Index:
    def __init__(self, path):
        f = open(path, 'rb'); self.f = f
        hdr = f.read(132)
        magic, ver, hlen, n, rec, *_ = struct.unpack('<IHHQHBB'+'Q'+'32s'+'Q'+'64s', hdr)
        assert magic == 0x50414D41 and rec == 40
        self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.n = n; self.base = hlen
    def lookup(self, sh):
        lo, hi, mm, base = 0, self.n, self.mm, self.base
        while lo < hi:
            mid = (lo + hi) >> 1
            off = base + mid * 40
            k = mm[off:off+32]
            if k < sh: lo = mid + 1
            elif k > sh: hi = mid
            else: return int.from_bytes(mm[off+32:off+40], 'little')
        return 0

def keys_from_phrase(phrase):
    p = phrase.encode('utf-8'); out = []
    k = sha(p); out.append(('sha256', k))
    out.append(('sha256d', sha(k)))
    cur = k
    for i in range(2, 11):
        cur = sha(cur); out.append((f'sha256x{i}', cur))
    out.append(('sha512_32', hashlib.sha512(p).digest()[:32]))
    out.append(('pbkdf2_2048', hashlib.pbkdf2_hmac('sha512', p, b'mnemonic', 2048)[:32]))
    out.append(('pbkdf2_nosalt', hashlib.pbkdf2_hmac('sha512', p, b'', 2048)[:32]))
    h = hmac.new(b'Bitcoin seed', p, hashlib.sha512).digest()
    out.append(('hmac_seed_lo', h[:32])); out.append(('hmac_seed_hi', h[32:]))
    return out

_REV = bytes.maketrans(bytes(range(256)),
        bytes(int(f'{i:08b}'[::-1], 2) for i in range(256)))
def key_forms(k):
    """Involutions a 'mirror' hint could literally mean."""
    yield 'base', k
    yield 'revbytes', k[::-1]                       # endianness mirror
    yield 'complement', bytes(255 - b for b in k)   # bitwise mirror
    yield 'bitrev', k.translate(_REV)[::-1]         # full 256-bit reversal
    hx = k.hex(); yield 'nibrev', bytes.fromhex(hx[::-1])   # hex-string mirror

def scripts_for(pub_c, pub_u):
    hc = h160(pub_c); hu = h160(pub_u)
    ph = h160(b'\x00\x14' + hc)
    return (('p2pkh_c',     b'\x76\xa9\x14' + hc + b'\x88\xac'),
            ('p2pkh_u',     b'\x76\xa9\x14' + hu + b'\x88\xac'),
            ('p2wpkh',      b'\x00\x14' + hc),
            ('p2sh_p2wpkh', b'\xa9\x14' + ph + b'\x87'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phrases', nargs='+', required=True)
    ap.add_argument('--index', default='/tmp/od/address_map.bin')
    ap.add_argument('--out', default='mirror_hits.tsv')
    a = ap.parse_args()

    phrases = []
    seen = set()
    for path in a.phrases:
        if not os.path.exists(path): continue
        for line in open(path, encoding='utf-8', errors='replace'):
            s = line.rstrip('\n')
            if s and s not in seen: seen.add(s); phrases.append(s)
    sys.stderr.write(f"phrases: {len(phrases):,}\n")

    idx = Index(a.index)
    sys.stderr.write(f"index: {idx.n:,} funded scripthashes\n")
    out = open(a.out, 'w')
    out.write("phrase\thash_kind\tkey_form\tmirror\taddr_type\tscripthash\tbalance_sats\n")

    t0 = time.time(); nkey = 0; naddr = 0; hits = 0
    for pi, phrase in enumerate(phrases):
        for kind, k in keys_from_phrase(phrase):
            for form, kk in key_forms(k):
                ki = int.from_bytes(kk, 'big')
                if not (0 < ki < N): continue
                try:
                    xy = coincurve.PublicKey.from_valid_secret(kk).format(compressed=False)
                except Exception:
                    continue
                nkey += 1
                x = xy[1:33]; y = xy[33:65]; yi = int.from_bytes(y, 'big')
                even = (yi % 2 == 0)
                pc  = (b'\x02' if even else b'\x03') + x
                pu  = b'\x04' + x + y
                # --- the secp256k1 mirror: k -> N-k, same x, y -> P-y ---
                pc2 = (b'\x03' if even else b'\x02') + x
                pu2 = b'\x04' + x + ((P - yi) % P).to_bytes(32, 'big')
                for mirror, (a_c, a_u) in (('', (pc, pu)), ('MIRROR', (pc2, pu2))):
                    for atype, spk in scripts_for(a_c, a_u):
                        naddr += 1
                        bal = idx.lookup(sha(spk))
                        if bal:
                            hits += 1
                            row = (f"{phrase}\t{kind}\t{form}\t{mirror or 'normal'}\t"
                                   f"{atype}\t{sha(spk).hex()}\t{bal}\n")
                            out.write(row); out.flush()
                            sys.stderr.write("*** HIT *** " + row)
        if (pi + 1) % 500 == 0:
            el = time.time() - t0
            sys.stderr.write(f"  {pi+1:,}/{len(phrases):,} phrases | {nkey:,} keys | "
                             f"{naddr:,} addrs | {hits} hits | {el:.0f}s\n"); sys.stderr.flush()
    out.close()
    sys.stderr.write(f"DONE phrases={len(phrases):,} keys={nkey:,} addresses={naddr:,} "
                     f"hits={hits} time={time.time()-t0:.0f}s\n")

if __name__ == '__main__':
    main()
