#!/usr/bin/env python3
"""
Derivation schemes the prior sweeps never ran.

Everything so far treated a hash of the passphrase as the private key directly.
Real wallets don't do that: they turn the passphrase into a SEED and then walk a
BIP32 path. This adds:

  1. BIP32/BIP44/49/84/86 path derivation from a BIP39-style seed
     (PBKDF2-HMAC-SHA512(phrase, "mnemonic"+extra, 2048) -> m -> paths)
  2. scrypt-derived keys at common parameter sets
  3. WarpWallet (scrypt XOR pbkdf2), the real construction, with several salts

Each derived key is also tested at its secp256k1 mirror (n-k), and across
P2PKH(c/u), P2WPKH and P2SH-P2WPKH. Verified offline against address_map.bin.
"""
import argparse, hashlib, hmac, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_check import Index, sha, h160
import coincurve

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 2**256 - 2**32 - 977

# ---------- BIP32 ----------
def master_from_seed(seed, key=b"Bitcoin seed"):
    I = hmac.new(key, seed, hashlib.sha512).digest()
    return I[:32], I[32:]

def ckd_priv(k, c, index):
    if index >= 0x80000000:
        data = b'\x00' + k + index.to_bytes(4, 'big')
    else:
        pub = coincurve.PublicKey.from_valid_secret(k).format(compressed=True)
        data = pub + index.to_bytes(4, 'big')
    I = hmac.new(c, data, hashlib.sha512).digest()
    ki = (int.from_bytes(I[:32], 'big') + int.from_bytes(k, 'big')) % N
    if ki == 0: raise ValueError("invalid child")
    return ki.to_bytes(32, 'big'), I[32:]

def derive_path(seed, path):
    k, c = master_from_seed(seed)
    for el in path:
        k, c = ckd_priv(k, c, el)
    return k

H = 0x80000000
PATHS = {
    'm':                 [],
    "m/0":               [0],
    "m/0/0":             [0, 0],
    "m/0'":              [H],
    "m/0'/0'/0'":        [H, H, H],
    "m/0'/0/0":          [H, 0, 0],
    "m/44'/0'/0'/0/0":   [44+H, H, H, 0, 0],
    "m/44'/0'/0'/0/1":   [44+H, H, H, 0, 1],
    "m/49'/0'/0'/0/0":   [49+H, H, H, 0, 0],
    "m/84'/0'/0'/0/0":   [84+H, H, H, 0, 0],
    "m/86'/0'/0'/0/0":   [86+H, H, H, 0, 0],
}

def scripts_for(pc, pu):
    hc = h160(pc); hu = h160(pu); ph = h160(b'\x00\x14' + hc)
    return (b'\x76\xa9\x14'+hc+b'\x88\xac', b'\x76\xa9\x14'+hu+b'\x88\xac',
            b'\x00\x14'+hc, b'\xa9\x14'+ph+b'\x87')

def check(idx, kb, label, out):
    ki = int.from_bytes(kb, 'big')
    if not (0 < ki < N): return 0
    try:
        xy = coincurve.PublicKey.from_valid_secret(kb).format(compressed=False)
    except Exception:
        return 0
    x, y = xy[1:33], xy[33:65]; yi = int.from_bytes(y, 'big'); ev = yi % 2 == 0
    n = 0
    for mi, (pc, pu) in enumerate((((b'\x02' if ev else b'\x03')+x, b'\x04'+x+y),
                                   ((b'\x03' if ev else b'\x02')+x,
                                    b'\x04'+x+((P-yi) % P).to_bytes(32, 'big')))):
        for spk in scripts_for(pc, pu):
            bal = idx.lookup(sha(spk))
            if bal:
                out.write(f"HIT\t{label}\tmirror={mi}\t{sha(spk).hex()}\t{bal}\n"); out.flush()
                sys.stderr.write(f"*** HIT *** {label} bal={bal}\n"); n += 1
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phrases', nargs='+', required=True)
    ap.add_argument('--index', default='/tmp/od/address_map.bin')
    ap.add_argument('--out', default='hd_hits.tsv')
    ap.add_argument('--warp', action='store_true', help='also run WarpWallet (slow)')
    ap.add_argument('--warp-limit', type=int, default=250)
    a = ap.parse_args()

    phrases, seen = [], set()
    for p in a.phrases:
        if not os.path.exists(p): continue
        for line in open(p, encoding='utf-8', errors='replace'):
            s = line.rstrip('\n')
            if s and s not in seen: seen.add(s); phrases.append(s)
    sys.stderr.write(f"phrases: {len(phrases):,}\n")

    idx = Index(a.index)
    out = open(a.out, 'w'); out.write("result\tlabel\tmirror\tscripthash\tbalance\n")
    t0 = time.time(); nk = 0; hits = 0

    SALTS = [b'', b'mnemonic', b'mnemonicoverdose', b'mnemonicbitcoin', b'mnemonicMax Keiser']
    for i, ph in enumerate(phrases):
        pb = ph.encode('utf-8')
        # 1. BIP39-style seed -> BIP32 paths
        for salt in SALTS:
            seed = hashlib.pbkdf2_hmac('sha512', pb, salt, 2048)
            for pname, path in PATHS.items():
                try: k = derive_path(seed, path)
                except Exception: continue
                nk += 1; hits += check(idx, k, f"{ph!r}|bip32{pname}|salt={salt.decode() or '-'}", out)
        # 2. scrypt at common parameter sets
        for (Nn, r, p_) in ((16384, 8, 1), (1024, 8, 1), (32768, 8, 2)):
            try:
                k = hashlib.scrypt(pb, salt=b'', n=Nn, r=r, p=p_, dklen=32, maxmem=1 << 30)
            except Exception: continue
            nk += 1; hits += check(idx, k, f"{ph!r}|scrypt{Nn}", out)
        if (i + 1) % 100 == 0:
            sys.stderr.write(f"  {i+1:,}/{len(phrases):,}  keys={nk:,} hits={hits} {time.time()-t0:.0f}s\n")
            sys.stderr.flush()

    if a.warp:
        sys.stderr.write("WarpWallet pass (slow)...\n")
        for i, ph in enumerate(phrases[:a.warp_limit]):
            pb = ph.encode('utf-8')
            for salt in (b'', b'overdose', b'maxkeiser@gmail.com', b'bitcoinmagazine'):
                try:
                    s1 = hashlib.scrypt(pb + b'\x01', salt=salt + b'\x01', n=1 << 18, r=8, p=1,
                                        dklen=32, maxmem=1 << 31)
                    s2 = hashlib.pbkdf2_hmac('sha256', pb + b'\x02', salt + b'\x02', 1 << 16, 32)
                    k = bytes(x ^ y for x, y in zip(s1, s2))
                except Exception: continue
                nk += 1; hits += check(idx, k, f"{ph!r}|warp|salt={salt.decode() or '-'}", out)
            if (i + 1) % 25 == 0:
                sys.stderr.write(f"  warp {i+1}/{min(a.warp_limit,len(phrases))} {time.time()-t0:.0f}s\n")
    out.close()
    sys.stderr.write(f"DONE phrases={len(phrases):,} keys={nk:,} HITS={hits} time={time.time()-t0:.0f}s\n")

if __name__ == '__main__':
    main()
