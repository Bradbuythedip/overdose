#!/usr/bin/env python3
"""Stream every file in Qalander/bitcoin-all-addresses (~800M addresses,
~28GB total) and check each line against the set of addresses derived
from our candidate brainwallet phrases. Any match is a STATISTICAL OUTLIER.
"""
import os, sys, time, subprocess, urllib.request
from itertools import product

SOLVER_DIR = os.path.dirname(os.path.abspath(__file__))
DERIVED = os.path.join(SOLVER_DIR, 'derived.tsv')
HITS    = os.path.join(SOLVER_DIR, 'stream_hits.tsv')
BASE    = 'https://raw.githubusercontent.com/Qalander/bitcoin-all-addresses/master/'

# Enumerate file names: xaa, xab, ..., xzz, then xaaa? Actually the README
# said xaa..xlk = 297 files. So it's xaa..xaz, xba..xbz, ..., xla..xlk.
def fnames():
    names = []
    for a, b in product('abcdefghijklmnopqrstuvwxyz', repeat=2):
        names.append('x' + a + b)
        if len(names) >= 320: break
    return names  # will probe each, stop on 404

def load_derived():
    addrs = {}
    with open(DERIVED) as f:
        next(f)  # header
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) != 4: continue
            phrase, hk, at, addr = parts
            addrs.setdefault(addr, []).append((phrase, hk, at))
    return addrs

def stream_file(url, addrs, hits_out):
    req = urllib.request.Request(url, headers={'User-Agent':'overdose-solver/1.0'})
    try:
        r = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code == 404: return None  # signal end
        sys.stderr.write(f"HTTP {e.code} on {url}\n")
        return 0
    hits = 0
    n = 0
    for raw in r:
        line = raw.decode('utf-8', errors='replace').rstrip('\n')
        if not line: continue
        n += 1
        if line in addrs:
            for phrase, hk, at in addrs[line]:
                out = f'{phrase}\t{hk}\t{at}\t{line}\n'
                hits_out.write(out); hits_out.flush()
                sys.stderr.write('*** HIT *** ' + out)
                hits += 1
    return hits, n

def main():
    sys.stderr.write("loading derived addresses...\n")
    addrs = load_derived()
    sys.stderr.write(f"loaded {len(addrs)} unique target addresses from {DERIVED}\n")
    open(HITS, 'a').close()  # touch
    hits_out = open(HITS, 'a')
    t0 = time.time()
    total_hits = 0; total_lines = 0
    for name in fnames():
        url = BASE + name
        result = stream_file(url, addrs, hits_out)
        if result is None:
            sys.stderr.write(f"reached end ({name} 404)\n")
            break
        hits, n = result
        total_hits += hits; total_lines += n
        sys.stderr.write(f"[{name}] +{n} lines, +{hits} hits "
                         f"(total {total_lines:,} lines, {total_hits} hits, {time.time()-t0:.1f}s)\n")
    sys.stderr.write(f"DONE total_lines={total_lines:,} total_hits={total_hits} time={time.time()-t0:.1f}s\n")

if __name__ == '__main__':
    main()
