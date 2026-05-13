#!/usr/bin/env python3
"""Brainwallet candidate checker for the Keiser Overdose puzzle.

For each candidate phrase read from argv[1] (or stdin), derives:
  - SHA256(phrase) -> priv key
  - double SHA256(phrase) -> priv key
For each priv key, computes compressed P2PKH, uncompressed P2PKH, and
compressed P2WPKH (bech32). Queries blockstream.info esplora for each
address and prints only hits (funded > 0). Hits also appended to hits.tsv.

Rate-limited and resumable via seen.txt.
"""
import sys, os, time, hashlib, json, argparse
from ecdsa import SigningKey, SECP256k1
import base58
import urllib.request, urllib.error

SOLVER_DIR = os.path.dirname(os.path.abspath(__file__))
HITS_PATH = os.path.join(SOLVER_DIR, "hits.tsv")
SEEN_PATH = os.path.join(SOLVER_DIR, "seen.txt")

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk

def bech32_hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]

def bech32_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

def bech32_encode(hrp, data):
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join(BECH32_CHARSET[d] for d in combined)

def convertbits(data, frombits, tobits, pad=True):
    acc = 0; bits = 0; ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        if value < 0 or value >> frombits: return None
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits: ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret

def segwit_addr_encode(hrp, witver, witprog):
    return bech32_encode(hrp, [witver] + convertbits(witprog, 8, 5))

def hash160(b):
    return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()

def b58check(prefix, payload):
    body = prefix + payload
    chk = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    return base58.b58encode(body + chk).decode()

def priv_to_addrs(priv32):
    sk = SigningKey.from_string(priv32, curve=SECP256k1)
    vk = sk.verifying_key
    pt = vk.pubkey.point
    x = pt.x().to_bytes(32, 'big'); y = pt.y().to_bytes(32, 'big')
    pub_unc = b'\x04' + x + y
    pub_c   = (b'\x02' if (pt.y() % 2 == 0) else b'\x03') + x
    h_unc = hash160(pub_unc)
    h_c   = hash160(pub_c)
    p2pkh_unc = b58check(b'\x00', h_unc)
    p2pkh_c   = b58check(b'\x00', h_c)
    p2wpkh    = segwit_addr_encode('bc', 0, h_c)
    return [('p2pkh_unc', p2pkh_unc), ('p2pkh_c', p2pkh_c), ('p2wpkh', p2wpkh)]

def phrase_to_keys(phrase):
    p = phrase.encode('utf-8')
    k1 = hashlib.sha256(p).digest()
    k2 = hashlib.sha256(k1).digest()
    return [('sha256', k1), ('sha256d', k2)]

LAST_REQ = [0.0]
def esplora_get(addr, retries=2):
    url = f"https://blockstream.info/api/address/{addr}"
    for attempt in range(retries + 1):
        # rate-limit to ~5/sec
        dt = time.time() - LAST_REQ[0]
        if dt < 0.22: time.sleep(0.22 - dt)
        LAST_REQ[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'overdose-solver/1.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(2 ** attempt)
                continue
            sys.stderr.write(f"HTTP {e.code} on {addr}\n")
            time.sleep(2 ** attempt)
        except Exception as e:
            sys.stderr.write(f"err {addr}: {e}\n")
            time.sleep(2 ** attempt)
    return None

def load_seen():
    if not os.path.exists(SEEN_PATH): return set()
    return set(open(SEEN_PATH).read().splitlines())

def mark_seen(phrase):
    with open(SEEN_PATH, 'a') as f: f.write(phrase + '\n')

def record_hit(row):
    with open(HITS_PATH, 'a') as f:
        f.write('\t'.join(str(x) for x in row) + '\n')

def check_phrase(phrase, seen):
    if phrase in seen: return 0
    hits = 0
    for hash_kind, priv in phrase_to_keys(phrase):
        for atype, addr in priv_to_addrs(priv):
            data = esplora_get(addr)
            if data is None: continue
            cs = data.get('chain_stats', {})
            funded = cs.get('funded_txo_sum', 0)
            spent  = cs.get('spent_txo_sum', 0)
            txcount = cs.get('tx_count', 0)
            if funded > 0:
                row = (phrase, hash_kind, atype, addr, funded, spent, txcount)
                print('\t'.join(str(x) for x in row), flush=True)
                record_hit(row)
                hits += 1
    mark_seen(phrase)
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?')
    ap.add_argument('--test', action='store_true', help='run test vector')
    args = ap.parse_args()
    if args.test:
        # correct horse battery staple
        priv = hashlib.sha256(b"correct horse battery staple").digest()
        for atype, addr in priv_to_addrs(priv):
            print(atype, addr)
        return
    seen = load_seen()
    if args.file:
        phrases = [l.rstrip('\n') for l in open(args.file) if l.strip()]
    else:
        phrases = [l.rstrip('\n') for l in sys.stdin if l.strip()]
    total = len(phrases)
    hits = 0
    for i, phrase in enumerate(phrases, 1):
        h = check_phrase(phrase, seen)
        hits += h
        if i % 25 == 0 or i == total:
            sys.stderr.write(f"[{i}/{total}] hits={hits}\n")
            sys.stderr.flush()

if __name__ == '__main__':
    main()
