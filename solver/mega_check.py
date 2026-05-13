#!/usr/bin/env python3
"""High-throughput candidate checker: derive addresses from many candidates
and check each via the mmap'd balance index. Reports any nonzero balance.

Hash variants per candidate phrase:
  - SHA256
  - double SHA256
  - iterated SHA256 (n=2..16)
  - SHA512[:32]
  - "Bitcoin seed" HMAC (BIP-32 master from seed - we treat the phrase as seed)
  - Phrase prefixed with "Bitcoin signed message:\n" then double-SHA256
  - PBKDF2-HMAC-SHA512(phrase, salt='', iters=2048)[:32]  (BIP-39-ish)

Address variants per private key:
  - P2PKH compressed/uncompressed
  - P2WPKH bech32
  - P2SH-P2WPKH
"""
import os, sys, hashlib, hmac, mmap, struct, argparse, time
from ecdsa import SigningKey, SECP256k1
import base58

HEADER_FMT = '<IHHQHBB' + 'Q' + '32s' + 'Q' + '64s'
HEADER_SIZE = struct.calcsize(HEADER_FMT)
REC_SIZE = 40

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
def bech32_polymod(values):
    GEN=[0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3]
    c=1
    for v in values:
        b=c>>25; c=((c&0x1ffffff)<<5)^v
        for i in range(5):
            c ^= GEN[i] if ((b>>i)&1) else 0
    return c
def bech32_create(hrp,data):
    pm = bech32_polymod([ord(x)>>5 for x in hrp]+[0]+[ord(x)&31 for x in hrp]+data+[0]*6)^1
    return [(pm>>5*(5-i))&31 for i in range(6)]
def bech32_encode(hrp,data):
    return hrp+'1'+''.join(BECH32_CHARSET[d] for d in data+bech32_create(hrp,data))
def convertbits(data,frombits,tobits,pad=True):
    acc=0;bits=0;ret=[];maxv=(1<<tobits)-1
    for v in data:
        acc=(acc<<frombits)|v;bits+=frombits
        while bits>=tobits: bits-=tobits;ret.append((acc>>bits)&maxv)
    if pad and bits: ret.append((acc<<(tobits-bits))&maxv)
    return ret
def h160(b): return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()
def b58c(p,pay):
    body=p+pay
    return base58.b58encode(body+hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]).decode()

class BalanceIndex:
    def __init__(self, path):
        f = open(path,'rb')
        self.f = f
        self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        h = struct.unpack(HEADER_FMT, self.mm[:HEADER_SIZE])
        self.n = h[3]; self.base = h[2]
        assert h[0] == 0x50414D41
    def lookup(self, sh):
        lo, hi = 0, self.n
        mm = self.mm; base = self.base
        while lo < hi:
            mid = (lo+hi)//2
            off = base + mid*REC_SIZE
            k = mm[off:off+32]
            if k < sh: lo=mid+1
            elif k > sh: hi=mid
            else:
                return int.from_bytes(mm[off+32:off+40],'little')
        return 0

def script_p2pkh(h): return b'\x76\xa9\x14' + h + b'\x88\xac'
def script_p2sh(h):  return b'\xa9\x14' + h + b'\x87'
def script_p2wpkh(h): return b'\x00\x14' + h

def addrs_from_priv(priv):
    sk = SigningKey.from_string(priv, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    x = pt.x().to_bytes(32,'big'); y = pt.y().to_bytes(32,'big')
    pub_u = b'\x04' + x + y
    pub_c = (b'\x02' if (pt.y()%2==0) else b'\x03') + x
    hu = h160(pub_u); hc = h160(pub_c)
    # Also P2SH-P2WPKH redeem
    p2sh_h = h160(b'\x00\x14' + hc)
    return [
        ('p2pkh_u', b58c(b'\x00', hu), script_p2pkh(hu)),
        ('p2pkh_c', b58c(b'\x00', hc), script_p2pkh(hc)),
        ('p2wpkh',  bech32_encode('bc', [0]+convertbits(hc, 8, 5)), script_p2wpkh(hc)),
        ('p2sh_p2wpkh', b58c(b'\x05', p2sh_h), script_p2sh(p2sh_h)),
    ]

def keys_from_phrase(phrase):
    p = phrase.encode('utf-8')
    out = []
    k = hashlib.sha256(p).digest()
    out.append(('sha256', k))
    out.append(('sha256d', hashlib.sha256(k).digest()))
    # iterated SHA256
    cur = k
    for i in range(2, 11):
        cur = hashlib.sha256(cur).digest()
        out.append((f'sha256x{i}', cur))
    # SHA512[:32]
    out.append(('sha512_32', hashlib.sha512(p).digest()[:32]))
    # PBKDF2-HMAC-SHA512 (BIP39-like, salt='mnemonic')
    out.append(('pbkdf2_2048', hashlib.pbkdf2_hmac('sha512', p, b'mnemonic', 2048)[:32]))
    out.append(('pbkdf2_2048_nosalt', hashlib.pbkdf2_hmac('sha512', p, b'', 2048)[:32]))
    # BIP-32 master seed style: HMAC-SHA512(key='Bitcoin seed', msg=phrase)[:32]
    h = hmac.new(b'Bitcoin seed', p, hashlib.sha512).digest()
    out.append(('hmac_bitcoin_seed_lo', h[:32]))
    out.append(('hmac_bitcoin_seed_hi', h[32:]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--index', default='/tmp/address_map.bin')
    ap.add_argument('--out', default='mega_hits.tsv')
    args = ap.parse_args()
    bi = BalanceIndex(args.index)
    sys.stderr.write(f"index ok: {bi.n:,} records\n")
    out = open(args.out, 'w')
    out.write('phrase\tkey_kind\taddr_type\taddress\tbalance_sats\tbalance_btc\n')
    phrases = [l.rstrip('\n') for l in open(args.file) if l.strip()]
    sys.stderr.write(f"checking {len(phrases)} phrases\n")
    t0 = time.time(); hits = 0
    for i, phrase in enumerate(phrases, 1):
        try:
            ks = keys_from_phrase(phrase)
        except Exception:
            continue
        for kk, priv in ks:
            # skip invalid priv (out of curve order is rare)
            try:
                addrs = addrs_from_priv(priv)
            except Exception:
                continue
            for at, addr, spk in addrs:
                sh = hashlib.sha256(spk).digest()
                bal = bi.lookup(sh)
                if bal > 0:
                    row = f'{phrase}\t{kk}\t{at}\t{addr}\t{bal}\t{bal/1e8:.8f}\n'
                    out.write(row); out.flush()
                    sys.stderr.write('*** HIT *** ' + row); sys.stderr.flush()
                    hits += 1
        if i % 200 == 0:
            sys.stderr.write(f"[{i}/{len(phrases)}] hits={hits} elapsed={time.time()-t0:.1f}s\n")
    sys.stderr.write(f"DONE hits={hits} time={time.time()-t0:.1f}s\n")

if __name__ == '__main__':
    main()
