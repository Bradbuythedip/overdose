#!/usr/bin/env python3
"""Derive Bitcoin addresses for each candidate phrase and intersect with a
hosted dataset of ~150K funded BTC addresses. Any intersection is reported
as a statistical outlier (random brainwallet has p < 1e-30 of matching).
"""
import sys, os, hashlib, time
from ecdsa import SigningKey, SECP256k1
import base58

DATASET = os.environ.get('DATASET', '/tmp/snapshot.txt')
CAND    = os.environ.get('CAND', os.path.join(os.path.dirname(__file__), 'candidates2.txt'))
OUT     = os.path.join(os.path.dirname(__file__), 'intersect_hits.tsv')
DERIVED = os.path.join(os.path.dirname(__file__), 'derived.tsv')

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
def bech32_polymod(values):
    GEN = [0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3]
    c=1
    for v in values:
        b=c>>25; c=((c&0x1ffffff)<<5)^v
        for i in range(5):
            c ^= GEN[i] if ((b>>i)&1) else 0
    return c
def bech32_create(hrp, data):
    pm = bech32_polymod([ord(x)>>5 for x in hrp]+[0]+[ord(x)&31 for x in hrp]+data+[0]*6)^1
    return [(pm>>5*(5-i))&31 for i in range(6)]
def bech32_encode(hrp,data):
    combo=data+bech32_create(hrp,data)
    return hrp+'1'+''.join(BECH32_CHARSET[d] for d in combo)
def convertbits(data,frombits,tobits,pad=True):
    acc=0;bits=0;ret=[];maxv=(1<<tobits)-1
    for v in data:
        acc=(acc<<frombits)|v; bits+=frombits
        while bits>=tobits: bits-=tobits; ret.append((acc>>bits)&maxv)
    if pad and bits: ret.append((acc<<(tobits-bits))&maxv)
    return ret
def segwit_addr(hrp,witver,witprog):
    return bech32_encode(hrp,[witver]+convertbits(witprog,8,5))

def h160(b): return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()
def b58c(p,pay):
    body=p+pay
    return base58.b58encode(body+hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]).decode()

def addrs_from_priv(priv):
    sk = SigningKey.from_string(priv, curve=SECP256k1)
    pt = sk.verifying_key.pubkey.point
    x=pt.x().to_bytes(32,'big'); y=pt.y().to_bytes(32,'big')
    pub_u = b'\x04'+x+y
    pub_c = (b'\x02' if (pt.y()%2==0) else b'\x03')+x
    hu = h160(pub_u); hc = h160(pub_c)
    return {
        'p2pkh_u': b58c(b'\x00', hu),
        'p2pkh_c': b58c(b'\x00', hc),
        'p2wpkh':  segwit_addr('bc',0,hc),
        # P2SH-P2WPKH
        'p2sh_p2wpkh': b58c(b'\x05', h160(b'\x00\x14'+hc)),
    }

def main():
    sys.stderr.write("loading dataset...\n")
    with open(DATASET) as f:
        snapshot = set(l.strip() for l in f if l.strip())
    sys.stderr.write(f"loaded {len(snapshot)} addresses\n")

    candidates = [l.rstrip('\n') for l in open(CAND) if l.strip()]
    sys.stderr.write(f"checking {len(candidates)} candidates against snapshot\n")

    hit = open(OUT,'w'); hit.write('phrase\thash_kind\taddr_type\taddress\n')
    derived = open(DERIVED,'w'); derived.write('phrase\thash_kind\taddr_type\taddress\n')
    hits = 0
    t0 = time.time()
    for i,phrase in enumerate(candidates,1):
        p = phrase.encode('utf-8')
        for hk, priv in [('sha256', hashlib.sha256(p).digest()),
                         ('sha256d', hashlib.sha256(hashlib.sha256(p).digest()).digest())]:
            addrs = addrs_from_priv(priv)
            for at, a in addrs.items():
                derived.write(f'{phrase}\t{hk}\t{at}\t{a}\n')
                if a in snapshot:
                    line = f'{phrase}\t{hk}\t{at}\t{a}\n'
                    hit.write(line); hit.flush()
                    sys.stderr.write('*** HIT *** ' + line)
                    hits += 1
        if i % 50 == 0:
            sys.stderr.write(f"[{i}/{len(candidates)}] hits={hits} t={time.time()-t0:.1f}s\n")
    hit.close(); derived.close()
    sys.stderr.write(f"done. {hits} hits in {time.time()-t0:.1f}s\n")
    return hits

if __name__ == '__main__':
    sys.exit(0 if main()==0 else 0)
