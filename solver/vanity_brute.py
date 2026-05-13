#!/usr/bin/env python3
"""Vanitygen-style brute force toward target hash160.

For each seed phrase, compute K0 = SHA256(phrase), then iterate:
  K_n = (K0 + n) mod CURVE_ORDER
  compute pubkey -> hash160 (compressed AND uncompressed)
  check if either equals the target hash160.

This replicates the common vanity-grinding pattern where a tool starts
with a seed and increments the private key by 1 until the desired
prefix is found.

Throughput: ~50,000 keys/sec using ecdsa+coincurve combo (or ~5,000/sec
with pure ecdsa). At 5K/sec, 1M iters per phrase = ~3min per phrase.
"""
import sys, os, hashlib, time, argparse
try:
    import coincurve
    USE_COINCURVE = True
except ImportError:
    USE_COINCURVE = False
    from ecdsa import SigningKey, SECP256k1

TARGET_H160 = bytes.fromhex("0a959814c7eed2f8903dd74a3e76e3090d6a2b44")
TARGET_PREFIX = TARGET_H160[:1]  # first byte for fast filter

CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def hash160(b):
    return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()

if USE_COINCURVE:
    def pubkeys(priv_bytes):
        sk = coincurve.PrivateKey(priv_bytes)
        return sk.public_key.format(compressed=True), sk.public_key.format(compressed=False)
else:
    def pubkeys(priv_bytes):
        sk = SigningKey.from_string(priv_bytes, curve=SECP256k1)
        pt = sk.verifying_key.pubkey.point
        x = pt.x().to_bytes(32,'big')
        y = pt.y().to_bytes(32,'big')
        pub_u = b'\x04' + x + y
        pub_c = (b'\x02' if (pt.y()%2==0) else b'\x03') + x
        return pub_c, pub_u

def search(phrase, max_iters):
    p = phrase.encode('utf-8')
    k0 = int.from_bytes(hashlib.sha256(p).digest(), 'big')
    found_any_1xxx = []
    for n in range(max_iters):
        k = (k0 + n) % CURVE_ORDER
        if k == 0: continue
        try:
            pc, pu = pubkeys(k.to_bytes(32,'big'))
        except Exception:
            continue
        hc = hash160(pc)
        hu = hash160(pu)
        # Fast filter: first byte 0x0a
        for ht, label in [(hc, 'c'), (hu, 'u')]:
            if ht[0] == 0x0a:
                # check second byte to narrow further (0x95)
                if ht[1] == 0x95:
                    # full compare
                    if ht == TARGET_H160:
                        return True, phrase, label, n, k
                    found_any_1xxx.append((label, n, ht.hex()))
    return False, phrase, None, max_iters, None, found_any_1xxx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phrases', default='/home/user/overdose/solver/candidates_v2.txt')
    ap.add_argument('--iters', type=int, default=200_000, help='iters per phrase')
    ap.add_argument('--limit', type=int, default=200, help='max phrases to try')
    ap.add_argument('--out', default='/home/user/overdose/solver/vanity_hits.tsv')
    args = ap.parse_args()
    print(f"target hash160: {TARGET_H160.hex()}", file=sys.stderr)
    print(f"using {'coincurve' if USE_COINCURVE else 'ecdsa'}", file=sys.stderr)
    out = open(args.out, 'a')
    phrases = [l.rstrip('\n') for l in open(args.phrases) if l.strip()][:args.limit]
    print(f"trying {len(phrases)} phrases x {args.iters:,} iters", file=sys.stderr)
    t0 = time.time()
    found = 0
    for i, phrase in enumerate(phrases, 1):
        r = search(phrase, args.iters)
        if r[0]:
            _, ph, lab, n, k = r[:5]
            line = f"FOUND\t{ph}\t{lab}\t{n}\t{k:064x}\n"
            out.write(line); out.flush()
            print('*** FOUND ***', line, file=sys.stderr)
            found += 1
            return
        # report any 1xxx prefix matches even if not exact
        _, ph, _, _, _, partials = r[:6] if len(r) > 5 else (*r, [])
        if partials:
            for lab, n, h in partials[:3]:
                print(f"  partial 1xxx (label={lab} n={n} h160={h}) from phrase: {ph[:50]}", file=sys.stderr)
        if i % 10 == 0:
            elapsed = time.time() - t0
            rate = i * args.iters / elapsed
            print(f"[{i}/{len(phrases)}] {rate:,.0f} keys/sec | elapsed {elapsed:.0f}s", file=sys.stderr)
    print(f"done; total found {found}", file=sys.stderr)

if __name__ == '__main__':
    main()
