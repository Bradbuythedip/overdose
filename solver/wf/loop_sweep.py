#!/usr/bin/env python3
"""
Sweep everything the strange-loop dissection produced.

Reads every wf/loop/cand_*.txt and wf/loop/prio_*.txt written by the clue
agents, dedupes across them, and sweeps in two tiers so the cheap pass covers
everything before the expensive pass runs on the agents' own best guesses:

  tier 1  ALL candidates x direct digests only        (7 keys  x 5 addrs)
  tier 2  PRIORITY candidates x the deep path set     (367 keys x 5 addrs)

  python3 wf/loop_sweep.py --selftest
  python3 wf/loop_sweep.py
"""
import glob, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

LOOP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loop")


def read(pattern):
    out, seen, per = [], set(), {}
    for fn in sorted(glob.glob(os.path.join(LOOP, pattern))):
        n = 0
        for line in open(fn, encoding="utf-8", errors="replace"):
            s = line.rstrip("\n")
            if not s or s in seen:
                continue
            seen.add(s); out.append(s); n += 1
        per[os.path.basename(fn)] = n
    return out, per


def sweep(phrases, deep, label):
    from index_oracle import spk_from_address
    paths = HD.build_paths() if deep else []
    o = H.Oracle(use_full=False)
    full = H.full_index()
    hits, n_addr, t0, PEND = [], 0, time.time(), []

    def flush(force=False):
        nonlocal n_addr
        if not PEND or (len(PEND) < 60000 and not force):
            return
        spks, meta = [], []
        for tag, ad, kh in PEND:
            if o.funded(ad):
                hits.append((tag, ad, kh))
                print(f"*** HIT(richlist) {tag} {ad} {kh}", flush=True)
            spk = spk_from_address(ad)
            if spk is not None:
                spks.append(spk); meta.append((tag, ad, kh))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, ad, kh = meta[j]
                hits.append((tag, ad, kh, bal))
                print(f"*** HIT(fullindex) {tag} {ad} {bal/1e8:.8f} BTC {kh}",
                      flush=True)
        n_addr += len(PEND); PEND.clear()

    for ph in phrases:
        for tag, k in HD.direct_keys(ph).items():
            for ad in HD.all_addrs(k):
                PEND.append((f"{tag}|{ph[:40]}", ad, k.hex()))
        if deep:
            for sname, seed in HD.seeds_from(ph).items():
                for path in paths:
                    try:
                        k = HD.derive(seed, path)
                    except Exception:
                        continue
                    if k:
                        for ad in HD.all_addrs(k):
                            PEND.append((f"{sname}:{path}|{ph[:40]}", ad, k.hex()))
        flush()
    flush(force=True)
    print(f"[{label}] phrases {len(phrases):,}  addresses {n_addr:,}  "
          f"{time.time()-t0:.0f}s  hits {len(hits)}")
    for h in hits:
        print("   ", h)
    return hits


def selftest():
    ok = True
    c, per = read("cand_*.txt")
    p, _ = read("prio_*.txt")
    print(f"  candidate files: {len(per)}  phrases {len(c):,}")
    for k, v in per.items():
        print(f"     {k}: {v:,}")
    print(f"  priority phrases: {len(p):,}")
    ok &= len(c) > 0
    print(f"  candidates present: {'OK' if len(c) else 'FAIL'}")
    k = HD.direct_keys("correct horse battery staple")["sha256"]
    a = HD.all_addrs(k)
    good = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T" in a
    print(f"  derivation path: {'OK' if good else 'FAIL'}")
    ok &= good
    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis: {'OK' if g else 'FAIL'}")
    ok &= g
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")
    cands, _ = read("cand_*.txt")
    prio, _ = read("prio_*.txt")
    print()
    h1 = sweep(cands, deep=False, label="tier1 shallow, all candidates")
    h2 = sweep(prio, deep=True, label="tier2 deep, priority candidates")
    print("\nTOTAL HITS:", len(h1) + len(h2))
