#!/usr/bin/env python3
"""
Sweep the WRAPPED script types that full_sweep.py never derived.

full_sweep covers five address-shaped single-key forms. spk_extra adds twenty
more per key — P2SH and P2WSH wrappings of P2PK, P2PKH and 1-of-1 multisig,
plus the pairings a setter could build from one key's own compressed and
uncompressed encodings. All of those land in the index (P2SH and P2WSH
scriptPubKeys are present in it); bare P2PK does not, and spk_extra's selftest
demonstrates that rather than assuming it.

Same derivation front end as full_sweep, so the comparison is like for like:
7 direct key hashes plus 5 seed derivations across the full HD path set.

  python3 sweep_extra.py --selftest
  python3 sweep_extra.py --phrases /tmp/allphrases.txt
"""
import argparse, sys, time

from hd_sweep import build_paths, derive, direct_keys, seeds_from
from spk_extra import spks_extra, selftest as extra_selftest
from index_oracle import Oracle, spk_from_address


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases", required=True)
    ap.add_argument("--out", default="/tmp/extra_hits.tsv")
    ap.add_argument("--hist", action="store_true")
    ap.add_argument("--batch", type=int, default=4000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not extra_selftest():
        sys.exit("script construction fails its controls; refusing to sweep")
    if a.selftest:
        return

    if a.hist:
        from hist_index import HistIndex
        idx = HistIndex()
        sys.stderr.write(f"\n  HISTORICAL ever-funded index ({idx.n:,})\n")
    else:
        idx = Oracle(verbose=False)
        if not idx.calibrate():
            sys.exit("oracle calibration failed")
        sys.stderr.write("\n  current-balance index (56,795,328)\n")

    # Canary: a known-funded scriptPubKey pushed through the SAME batched path
    # the sweep uses. Without it a null cannot be told from a dead pipeline.
    canary = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    if not idx.contains_spks([canary]):
        sys.exit("index does not report a known-funded address; refusing")
    sys.stderr.write("  CONTROL: known-funded spk reported by index\n")

    paths = build_paths()
    phrases = [l.rstrip("\n") for l in open(a.phrases, encoding="utf-8")
               if l.strip()]
    sys.stderr.write(f"  {len(phrases):,} phrases x (7 direct + 5 seeds x "
                     f"{len(paths)} paths) x 20 wrapped script types\n\n")

    fh = open(a.out, "w")
    fh.write("phrase\tderivation\tscript\tbalance\n")
    meta, spks = [], []
    n_addr = n_hit = 0
    t0 = time.time()

    def flush():
        nonlocal meta, spks, n_hit
        if not spks:
            return
        for j, bal in idx.contains_spks(spks):
            p, d, st = meta[j]
            n_hit += 1
            fh.write(f"{p}\t{d}\t{st}\t{bal}\n")
            fh.flush()
            sys.stderr.write(f"  *** HIT {bal} :: {st} :: {d}\n      {p}\n")
        meta, spks = [], []

    for i, p in enumerate(phrases, 1):
        keys = [(f"direct:{n}", k) for n, k in direct_keys(p).items()]
        for sn, seed in seeds_from(p).items():
            for dp in paths:
                try:
                    k = derive(seed, dp)
                except Exception:
                    continue
                if k:
                    keys.append((f"{sn}:{dp}", k))
        for dname, k in keys:
            for st, spk in spks_extra(k):
                meta.append((p[:60], dname, st))
                spks.append(spk)
                n_addr += 1
            if len(spks) >= a.batch:
                flush()
        if i % 200 == 0:
            el = time.time() - t0
            sys.stderr.write(f"  {i:,}/{len(phrases):,} phrases  "
                             f"{n_addr:,} addrs  {n_hit} hits  "
                             f"{i/max(el,1e-9):.1f} ph/s\n")
    flush()
    fh.close()
    sys.stderr.write(f"\nDONE. {len(phrases):,} phrases, {n_addr:,} wrapped "
                     f"scriptPubKeys derived, {n_hit} hits -> {a.out}\n")


if __name__ == "__main__":
    main()
