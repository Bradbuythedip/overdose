#!/usr/bin/env python3
"""Generate candidate BIP39 mnemonics from the BIP39-compatible words found
in the article highlights, derive their first BIP44 P2PKH address (path
m/44'/0'/0'/0/0) plus a few other common derivation paths, and check
each against the balance index."""
import sys, os, hashlib, hmac, mmap, struct, time
from itertools import islice, combinations
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
import base58

# Article's BIP39-word sequence in highlight order
ARTICLE_BIP39_SEQ = [
    'they','all','stock','layer','layer','great','thing','fall','keep','dignity',
    'layer','you','rabbit','hole','this','true','open','heart','off','live',
    'this','way','dumb','post','gun','volcano','heart','six','sorry','you',
    'that','snake','oil','over','ready','old','useless','fix','this','keep',
    'left','worth','game','economy','more','wealth','gold','right','will','all',
    'energy','will','live','own','rabbit','hole'
]

# Unique BIP39 words in article (44 unique)
ARTICLE_BIP39_UNIQ = sorted(set(ARTICLE_BIP39_SEQ))

# ---- BIP32/BIP44 derivation ----
CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def point_mul(k):
    sk = SigningKey.from_string(k.to_bytes(32, 'big'), curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    return pt

def serialize_pub(pt):
    x = pt.x().to_bytes(32,'big')
    return (b'\x02' if (pt.y()%2==0) else b'\x03') + x

def hash160(b):
    return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()

def b58c(p, pay):
    body = p + pay
    return base58.b58encode(body + hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]).decode()

def bip32_master(seed):
    h = hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()
    return int.from_bytes(h[:32],'big'), h[32:]

def ckd_priv(k, c, i):
    if i & 0x80000000:
        data = b'\x00' + k.to_bytes(32,'big') + i.to_bytes(4,'big')
    else:
        pub = serialize_pub(point_mul(k))
        data = pub + i.to_bytes(4,'big')
    h = hmac.new(c, data, hashlib.sha512).digest()
    il = int.from_bytes(h[:32],'big')
    k2 = (il + k) % CURVE_ORDER
    return k2, h[32:]

def derive_path(seed, path):
    k, c = bip32_master(seed)
    for i in path:
        k, c = ckd_priv(k, c, i)
    return k

H = 0x80000000
PATHS = {
    "bip44_btc_0_0":  [44|H, 0|H, 0|H, 0, 0],
    "bip44_btc_0_1":  [44|H, 0|H, 0|H, 0, 1],
    "bip49_btc_0_0":  [49|H, 0|H, 0|H, 0, 0],
    "bip84_btc_0_0":  [84|H, 0|H, 0|H, 0, 0],
    "bip86_btc_0_0":  [86|H, 0|H, 0|H, 0, 0],
    "electrum_0_0":   [0, 0],
    "raw_master":     [],
}

# Address index lookup
HEADER_FMT = '<IHHQHBB' + 'Q' + '32s' + 'Q' + '64s'
HEADER_SIZE = struct.calcsize(HEADER_FMT)
REC_SIZE = 40

class BalanceIndex:
    def __init__(self, path):
        f = open(path,'rb'); self.f = f
        self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        h = struct.unpack(HEADER_FMT, self.mm[:HEADER_SIZE])
        self.n = h[3]; self.base = h[2]
    def lookup(self, sh):
        lo,hi = 0,self.n; mm=self.mm; base=self.base
        while lo<hi:
            mid=(lo+hi)//2
            off=base+mid*REC_SIZE
            k=mm[off:off+32]
            if k<sh: lo=mid+1
            elif k>sh: hi=mid
            else: return int.from_bytes(mm[off+32:off+40],'little')
        return 0

def script_p2pkh(h): return b'\x76\xa9\x14'+h+b'\x88\xac'
def script_p2sh(h): return b'\xa9\x14'+h+b'\x87'
def script_p2wpkh(h): return b'\x00\x14'+h

def priv_to_all_scripthashes(k):
    pt = point_mul(k)
    x=pt.x().to_bytes(32,'big')
    pub_c = (b'\x02' if (pt.y()%2==0) else b'\x03') + x
    pub_u = b'\x04' + x + pt.y().to_bytes(32,'big')
    hc = hash160(pub_c); hu = hash160(pub_u)
    p2sh_h = hash160(b'\x00\x14'+hc)
    out = {}
    out['p2pkh_c']   = hashlib.sha256(script_p2pkh(hc)).digest()
    out['p2pkh_u']   = hashlib.sha256(script_p2pkh(hu)).digest()
    out['p2wpkh']    = hashlib.sha256(script_p2wpkh(hc)).digest()
    out['p2sh_p2wpkh'] = hashlib.sha256(script_p2sh(p2sh_h)).digest()
    return out, hc, hu

def check_mnemonic(mn, bi):
    m = Mnemonic('english')
    if not m.check(mn.lower()):
        return None
    seed = m.to_seed(mn.lower(), passphrase="")
    hits = []
    for pn, path in PATHS.items():
        try:
            k = derive_path(seed, path)
            if k == 0 or k >= CURVE_ORDER: continue
            shs, hc, hu = priv_to_all_scripthashes(k)
            for at, sh in shs.items():
                bal = bi.lookup(sh)
                if bal > 0:
                    addr_c = b58c(b'\x00', hash160((b'\x02' if (point_mul(k).y()%2==0) else b'\x03') + point_mul(k).x().to_bytes(32,'big')))
                    hits.append((pn, at, bal))
        except Exception as e:
            pass
    return hits

def main():
    bi = BalanceIndex('/tmp/address_map.bin')
    sys.stderr.write(f"index ok: {bi.n:,} records\n")
    out = open('bip39_hits.tsv','w')
    out.write('mnemonic\tpath\taddr_type\tbalance_sats\n')

    # Strategy 1: first 12 BIP39-words from highlights in order
    seq = ARTICLE_BIP39_SEQ
    print(f"sequence has {len(seq)} BIP39 words; trying windows", file=sys.stderr)
    tried = 0; hits = 0
    # 12-word sliding windows
    for start in range(len(seq) - 11):
        mn = ' '.join(seq[start:start+12])
        result = check_mnemonic(mn, bi)
        tried += 1
        if result is None:
            # invalid checksum — try the next valid permutation
            pass
        elif result:
            for pn, at, bal in result:
                line = f"{mn}\t{pn}\t{at}\t{bal}\n"
                out.write(line); out.flush()
                sys.stderr.write('*** HIT *** '+line); sys.stderr.flush()
                hits += 1
    # 24-word
    for start in range(len(seq) - 23):
        mn = ' '.join(seq[start:start+24])
        result = check_mnemonic(mn, bi)
        tried += 1
        if result:
            for pn, at, bal in result:
                line = f"{mn}\t{pn}\t{at}\t{bal}\n"
                out.write(line); out.flush()
                sys.stderr.write('*** HIT *** '+line); sys.stderr.flush()
                hits += 1
    sys.stderr.write(f"tried {tried} sliding-window mnemonics, hits={hits}\n")

    # Strategy 2: unique BIP39 words in alphabetical order, first 12 / first 24
    uniq = ARTICLE_BIP39_UNIQ
    for n in (12, 15, 18, 21, 24):
        if len(uniq) >= n:
            mn = ' '.join(uniq[:n])
            r = check_mnemonic(mn, bi)
            if r:
                for pn, at, bal in r:
                    line = f"{mn}\t{pn}\t{at}\t{bal}\n"
                    out.write(line); out.flush()
                    sys.stderr.write('*** HIT (uniq) *** '+line); sys.stderr.flush()
                    hits += 1

    sys.stderr.write(f"DONE total_hits={hits}\n")

if __name__ == '__main__':
    main()
