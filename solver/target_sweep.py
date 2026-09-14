#!/usr/bin/env python3
"""
Re-run the whole derivation corpus against a SMALL target set.

WHY THIS EXISTS
`window/index_horizon.md` established that address_map.bin is a 2025-10-11
snapshot, so its horizon is ~block 918,388 and the most recent ~48,500 blocks
are invisible to it. IndexOracle is the oracle behind every one of the
~150,000,000 derivations in this project, which means an address funded after
that date would be missed **even holding the correct key**.

`chain_tail_scan.py --start 918000` walks that blind region and reports every
output of ~20 BTC. Those hits are ADDRESSES, not keys — finding one does not
solve anything on its own. What it gives you is a target set no oracle here has
ever been able to see.

This closes the loop: take those scripthashes and re-derive the corpus against
them specifically. Cheap, because the cost of a sweep is the secp256k1 point
multiplication, not the lookup — swapping a 56M-entry index for a 50-entry set
changes almost nothing about the runtime, and the whole corpus re-runs in
minutes.

WHAT IT SWEEPS
Every family this project has: article phrases and n-grams, the highlight
sequence readings, the Keiser persona corpus, basic-crypto constructions, and
the complete single-edit neighbourhood of unverified characters — each through
7 direct hashes plus 5 seed types over 8 HD paths, into 25 script forms.

  python3 target_sweep.py --selftest
  python3 target_sweep.py --from-scan chain_tail_hits.jsonl --min-block 918000
  python3 target_sweep.py --targets a_scripthash,another
"""
import argparse, hashlib, itertools, json, os, sys, time

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def targets_from_scan(path, min_block=0, include_known=False):
    """Scripthashes of ~20 BTC outputs the scan found, past the index horizon."""
    out = {}
    if not os.path.exists(path):
        sys.exit(f"no scan output at {path}")
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("type") != "FULL" or r.get("block", 0) < min_block:
            continue
        if r.get("known") and not include_known:
            continue          # already in the 795, so already swept
        out[r["scripthash"]] = r
    return out


def corpus(scope="all"):
    """Every candidate string this project generates, deduplicated."""
    seen, out = set(), []

    def add(it):
        for s in it:
            s = (s or "").strip()
            if s and s not in seen and len(s) < 4000:
                seen.add(s)
                out.append(s)

    import article
    lines, sents, paras = article.load()
    add(list(sents) + list(paras) + list(lines))
    words = " ".join(paras).split()
    for n in range(2, 9):
        add(" ".join(words[i:i + n]) for i in range(len(words) - n + 1))
    try:
        import highlight_sequence as H
        add(H.readings(H.load()))
    except Exception as e:
        sys.stderr.write(f"    (highlight readings unavailable: {e})\n")
    try:
        import keiser_persona as K
        add(K.corpus())
    except Exception as e:
        sys.stderr.write(f"    (persona corpus unavailable: {e})\n")
    if scope == "all":
        try:
            import mega_solve as M
            add(itertools.islice(M.fam_edit1_unverified(), 500000))
        except Exception as e:
            sys.stderr.write(f"    (edit1_unverified unavailable: {e})\n")
    return out


def selftest():
    ok = True
    import tempfile
    recs = [
        {"type": "FULL", "block": 918500, "scripthash": "a" * 64,
         "known": False, "btc": 20.0},
        {"type": "FULL", "block": 830100, "scripthash": "b" * 64,
         "known": False, "btc": 20.0},          # before the horizon
        {"type": "FULL", "block": 920000, "scripthash": "c" * 64,
         "known": True, "btc": 20.0},           # already in the 795
        {"type": "TEXT", "block": 919000, "text": "x"},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
        p = f.name
    t = targets_from_scan(p, min_block=918000)
    ok &= set(t) == {"a" * 64}
    sys.stderr.write(f"  4 records -> {len(t)} target(s): pre-horizon dropped, "
                     f"already-known dropped, TEXT ignored: "
                     f"{'OK' if set(t)=={'a'*64} else 'FAIL'}\n")
    t2 = targets_from_scan(p, min_block=0, include_known=True)
    ok &= len(t2) == 3
    sys.stderr.write(f"  with both filters off: {len(t2)} targets "
                     f"{'OK' if len(t2)==3 else 'FAIL'}\n")
    os.unlink(p)

    # a scripthash must be sha256 of the scriptPubKey, forward order — the same
    # convention everything else here uses. Getting this backwards returns a
    # silent empty set, which is indistinguishable from a real null.
    from full_sweep import spks_for_key
    k = hashlib.sha256(b"target selftest").digest()
    spk = dict(spks_for_key(k))["p2pkh_c"]
    sh = hashlib.sha256(spk).hexdigest()
    found = sweep(corpus_override=["target selftest"], targets={sh: {}},
                  quiet=True)
    ok &= len(found) == 1
    sys.stderr.write(f"  a planted key is FOUND against its own scripthash: "
                     f"{'OK' if len(found)==1 else 'FAIL — the sweep is blind'}\n")
    found2 = sweep(corpus_override=["target selftest"],
                   targets={"f" * 64: {}}, quiet=True)
    ok &= not found2
    sys.stderr.write(f"  and NOT found against an unrelated scripthash: "
                     f"{'OK' if not found2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def sweep(targets, corpus_override=None, scope="all", quiet=False):
    """Derive the corpus and report anything landing on a target scripthash."""
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    paths = build_paths()[:8]
    phrases = corpus_override if corpus_override is not None else corpus(scope)
    hits, n, t0 = [], 0, time.time()
    for i, p in enumerate(phrases, 1):
        keys = [(f"d:{h}", k) for h, k in direct_keys(p).items()]
        for sn, seed in seeds_from(p).items():
            for path in paths:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    keys.append((f"{sn}:{path}", k))
        for dn, k in keys:
            if not (0 < int.from_bytes(k, "big") < CURVE_N):
                continue
            for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                n += 1
                sh = hashlib.sha256(spk).hexdigest()
                if sh in targets:
                    hits.append((p, dn, st, sh))
                    if not quiet:
                        sys.stderr.write(
                            f"\n  *** HIT  scripthash {sh}\n"
                            f"      phrase     {p[:90]!r}\n"
                            f"      derivation {dn}\n"
                            f"      script     {st}\n")
        if not quiet and i % 2000 == 0:
            el = time.time() - t0
            sys.stderr.write(f"\r  {i:,}/{len(phrases):,} phrases  {n:,} "
                             f"scripts  {n/max(el,1e-9):,.0f}/s  ")
            sys.stderr.flush()
    if not quiet:
        sys.stderr.write(f"\n  {n:,} scriptPubKeys tested\n")
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-scan", default="chain_tail_hits.jsonl")
    ap.add_argument("--min-block", type=int, default=918000,
                    help="the index horizon; below it the index already "
                         "covered the address and the corpus already failed")
    ap.add_argument("--include-known", action="store_true")
    ap.add_argument("--targets", help="comma-separated scripthashes instead")
    ap.add_argument("--scope", choices=("core", "all"), default="all")
    ap.add_argument("--out", default="target_hits.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the sweep cannot find a planted key; a null would be "
                 "meaningless")
    if a.selftest:
        return

    if a.targets:
        tg = {s.strip().lower(): {} for s in a.targets.split(",") if s.strip()}
    else:
        tg = targets_from_scan(a.from_scan, a.min_block, a.include_known)
    if not tg:
        sys.stderr.write(
            f"\n  no targets past block {a.min_block:,} in {a.from_scan}.\n"
            f"  Either the blind region has not been scanned yet, or it holds\n"
            f"  no ~20 BTC output absent from the 795 — which is itself the\n"
            f"  result: the index-staleness blind spot would be empty.\n")
        return
    sys.stderr.write(f"\n  {len(tg)} target scripthash(es) past block "
                     f"{a.min_block:,}\n")
    for sh, r in list(tg.items())[:10]:
        sys.stderr.write(f"    {sh[:40]}…  block {r.get('block','?')}  "
                         f"{r.get('btc','?')} BTC\n")

    hits = sweep(tg, scope=a.scope)
    if hits:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("phrase\tderivation\tscript\tscripthash\n")
            for p, dn, st, sh in hits:
                fh.write(f"{p}\t{dn}\t{st}\t{sh}\n")
        sys.stderr.write(f"\n  {len(hits)} HIT(S) -> {a.out}\n"
                         f"  Verify before trusting: derive the key yourself "
                         f"and confirm the address holds what the scan said.\n")
    else:
        sys.stderr.write("\n  no phrase in the corpus derives to any of these "
                         "addresses\n")


if __name__ == "__main__":
    main()
