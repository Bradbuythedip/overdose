#!/usr/bin/env python3
"""
Two analyses unlocked by the April-2023 P2PKH snapshot
(ghcr.io/shlima/fortune : addresses/Bitcoin/2023/04/p2pkh_Rich_Max_100.txt).

Run on a machine that can pull the image; see sibling branch's RUNBOOK_window.md.
Needs only that file plus address_map.bin -- no blockchain API.

  python3 apr2023_analysis.py --apr2023 apr2023/p2pkh_Rich_Max_100.txt \
      --index /tmp/address_map.bin --corpus-hits window/resolved_b1_19.5_20.5.tsv

ANALYSIS 1 -- date the candidates.
  A tier-1 candidate holds ~20 BTC now and is absent from the corpus ending
  2021-01-17. If it ALSO appears in April 2023 it was funded before then, i.e.
  inside the corrected Sept-2021..Mar-2023 window. Absent => funded after the
  announcement => excluded.

ANALYSIS 2 -- was the puzzle already solved and swept?
  Every search so far assumes the wallet is UNSPENT. Keiser said in March 2023
  that nobody had solved it; if someone solved it afterwards the wallet is spent
  and invisible to the whole approach. This finds addresses that held a balance
  in April 2023 but hold NOTHING today -- swept in between. Restricted to
  addresses absent from the pre-2021 corpus, those are "funded in the puzzle
  window, later emptied": exactly the shape a silently-solved puzzle wallet has.

Ported from sibling branch claude/keiser-overdose-puzzle-itkf6t solver/apr2023_analysis.py
"""
import argparse, hashlib, struct, mmap, sys, os

def h160(b): return hashlib.new('ripemd160', hashlib.sha256(b).digest()).digest()
B58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
IDX = {c: i for i, c in enumerate(B58)}
def b58dec(s):
    n = 0
    for c in s.encode():
        if c not in IDX: raise ValueError
        n = n * 58 + IDX[c]
    h = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    z = len(s) - len(s.lstrip('1'))
    return b'\x00' * z + h
def spk_of(a):
    raw = b58dec(a)
    if len(raw) < 25: raise ValueError
    ver, pk = raw[0:1], raw[1:21]
    if ver == b'\x00': return b'\x76\xa9\x14' + pk + b'\x88\xac'
    if ver == b'\x05': return b'\xa9\x14' + pk + b'\x87'
    raise ValueError

class Index:
    def __init__(self, path):
        f = open(path, 'rb')
        magic, ver, hl, n, rec, *_ = struct.unpack('<IHHQHBB'+'Q'+'32s'+'Q'+'64s', f.read(132))
        assert magic == 0x50414D41
        self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ); self.n = n; self.base = hl
    def lookup(self, sh):
        lo, hi, mm, b = 0, self.n, self.mm, self.base
        while lo < hi:
            mid = (lo + hi) >> 1; off = b + mid * 40; k = mm[off:off+32]
            if k < sh: lo = mid + 1
            elif k > sh: hi = mid
            else: return int.from_bytes(mm[off+32:off+40], 'little')
        return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apr2023', required=True)
    ap.add_argument('--index', default='/tmp/address_map.bin')
    ap.add_argument('--tier1', default='window/candidates_p2pkh_exact20.txt')
    ap.add_argument('--all-cands', default='window/candidates_all.txt')
    ap.add_argument('--corpus-hits', default='window/resolved_b1_19.5_20.5.tsv',
                    help='addresses recovered from the pre-2021 corpus (to exclude)')
    ap.add_argument('--swept-out', default='swept_candidates.tsv')
    a = ap.parse_args()

    apr = set()
    for line in open(a.apr2023, encoding='utf-8', errors='replace'):
        s = line.strip()
        if s: apr.add(s)
    sys.stderr.write(f"April-2023 snapshot: {len(apr):,} addresses\n")
    idx = Index(a.index)

    # ---- ANALYSIS 1 ----
    for name, path in (('tier-1 (exact 20, P2PKH)', a.tier1), ('all candidates', a.all_cands)):
        if not os.path.exists(path): continue
        cands = [l.strip() for l in open(path) if l.strip()]
        inw = [c for c in cands if c in apr]
        out = [c for c in cands if c not in apr]
        sys.stderr.write(f"\n{name}: {len(cands)}\n"
                         f"   funded BEFORE Apr-2023 (IN WINDOW): {len(inw)}\n"
                         f"   funded after  Apr-2023 (excluded) : {len(out)}\n")
        if path == a.tier1:
            with open('tier1_in_window.txt','w') as f:
                for c in inw: f.write(c+"\n")
            sys.stderr.write("   -> tier1_in_window.txt\n")
            for c in inw[:40]: sys.stderr.write(f"      {c}\n")

    # ---- ANALYSIS 2 ----
    old = set()
    if os.path.exists(a.corpus_hits):
        for line in open(a.corpus_hits):
            p = line.split('\t')
            if p and p[0] != 'address': old.add(p[0])
    sys.stderr.write(f"\npre-2021 corpus addresses to exclude: {len(old):,}\n")
    swept = 0
    with open(a.swept_out,'w') as f:
        f.write("address\tapr2023\tbalance_now_sats\tnote\n")
        for adr in apr:
            if adr in old: continue                 # existed before 2021 -> not window-funded
            try: sh = hashlib.sha256(spk_of(adr)).digest()
            except Exception: continue
            if idx.lookup(sh) == 0:                 # had balance Apr-2023, empty now
                swept += 1
                f.write(f"{adr}\tYES\t0\tfunded post-2021, held Apr-2023, EMPTY now\n")
    sys.stderr.write(f"SWEPT candidates (post-2021 funded, emptied since Apr-2023): {swept:,}\n")
    sys.stderr.write(f" -> {a.swept_out}\n"
                     " Check these with blockstream: any whose single funding tx was ~20 BTC\n"
                     " is a puzzle wallet that was SOLVED and swept -- which would explain\n"
                     " every negative result so far.\n")

if __name__ == '__main__':
    main()
