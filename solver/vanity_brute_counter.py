#!/usr/bin/env python3
"""Variant vanity-grind: K_n = SHA256(phrase + ':' + str(n)).

Many "easy" vanity grinders that operate from a seed phrase use this
pattern: append a counter, hash, check the resulting address. We test
both compressed and uncompressed pubkey -> P2PKH against the target
hash160.
"""
import sys, os, hashlib, time, argparse, coincurve

TARGET_H160 = bytes.fromhex("0a959814c7eed2f8903dd74a3e76e3090d6a2b44")

def hash160(b):
    return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phrases', default='/home/user/overdose/solver/candidates_v2.txt')
    ap.add_argument('--iters', type=int, default=200_000)
    ap.add_argument('--limit', type=int, default=3000)
    ap.add_argument('--sep', default=':')
    ap.add_argument('--out', default='/home/user/overdose/solver/vanity_hits2.tsv')
    args = ap.parse_args()
    out = open(args.out, 'a')
    phrases = [l.rstrip('\n') for l in open(args.phrases) if l.strip()][:args.limit]
    print(f"sep={args.sep!r} target {TARGET_H160.hex()} | {len(phrases)} phrases x {args.iters:,}", file=sys.stderr)
    t0 = time.time()
    for i, phrase in enumerate(phrases, 1):
        pb = phrase.encode('utf-8')
        sep = args.sep.encode()
        for n in range(args.iters):
            seed = pb + sep + str(n).encode()
            k = hashlib.sha256(seed).digest()
            try:
                sk = coincurve.PrivateKey(k)
            except Exception:
                continue
            pc = sk.public_key.format(compressed=True)
            pu = sk.public_key.format(compressed=False)
            for ht, lab in [(hash160(pc), 'c'), (hash160(pu), 'u')]:
                if ht[0] == 0x0a and ht[1] == 0x95:
                    if ht == TARGET_H160:
                        line = f"FOUND\t{phrase}\t{lab}\tn={n}\tk={k.hex()}\n"
                        out.write(line); out.flush()
                        sys.stderr.write('*** FOUND *** '+line)
                        return
                    if ht[2] == 0x98:
                        sys.stderr.write(f"  partial 1xxx-0a9598 ({lab} n={n} h160={ht.hex()}) from phrase: {phrase[:60]}\n"); sys.stderr.flush()
        if i % 10 == 0:
            elapsed = time.time() - t0
            rate = i * args.iters / elapsed
            sys.stderr.write(f"[{i}/{len(phrases)}] {rate:,.0f}/s | {elapsed:.0f}s\n"); sys.stderr.flush()
    sys.stderr.write("done; no exact hit\n")

if __name__ == '__main__':
    main()
