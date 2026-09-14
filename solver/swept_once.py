#!/usr/bin/env python3
"""
Which exactly-20-BTC addresses were emptied EXACTLY ONCE in the blind window?

WHY THE MULTIPLICITY FILTER IS THE WHOLE POINT
`chain_tail_scan` writes a SWEEP record every time a spend reveals a pubkey
whose script forms match one of the 795 exactly-20-BTC scripthashes. Those
records are dominated by hot wallets: in an earlier scan a single scripthash
accounted for 18 of the first 20 records. An exchange spends the same address
hundreds of times.

An address spent ONCE is the other thing entirely -- funded, dormant, then a
single spend. That is the shape a claimed prize has, and it is why the cut is
at one rather than at some tuned threshold.

WHAT THIS IS NOT
It is not evidence. "Swept once inside this window" says nothing yet about WHEN
the address was funded, and a coin funded last month and spent once looks
identical here. Dating is `age_check.py`'s job, and this only prepares its
input -- including each address's prev_txid, the outpoint its spend consumed,
which is what makes dating possible without a transaction-history endpoint.

  python3 swept_once.py --selftest
  python3 swept_once.py --in sweep_hits.jsonl --out swept_once.txt
"""
import argparse, collections, json, os, sys


def tally(path):
    """(counts, prev_txid, prev_vout, blocks, n_records) over SWEEP records."""
    counts = collections.Counter()
    prev, pvout, blocks = {}, {}, {}
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("type") != "SWEEP":
                continue
            sh = r.get("scripthash")
            if not sh:
                continue
            n += 1
            counts[sh] += 1
            # keep the FIRST sighting: for a singly-swept address there is only
            # one, and for a reused one the earliest spend is the least
            # misleading thing to carry forward
            prev.setdefault(sh, r.get("prev_txid"))
            pvout.setdefault(sh, r.get("prev_vout"))
            blocks.setdefault(sh, r.get("block"))
    return counts, prev, pvout, blocks, n


def select(counts, lo, hi):
    return sorted(sh for sh, c in counts.items() if lo <= c <= hi)


def funnel(counts, n_records, lo, hi, out=sys.stderr):
    """Show what was discarded, not just what survived."""
    dist = collections.Counter(counts.values())
    out.write(f"\n  {n_records:,} SWEEP records\n")
    out.write(f"  {len(counts):,} distinct scripthashes\n")
    if not counts:
        return
    out.write("\n  spends per address:\n")
    shown = 0
    for c in sorted(dist):
        mark = "  <- kept" if lo <= c <= hi else ""
        out.write(f"    {c:>6} spend(s): {dist[c]:>6} address(es){mark}\n")
        shown += 1
        if shown >= 12 and len(dist) > 14:
            rest = sum(v for k, v in dist.items() if k > c)
            out.write(f"    {'more':>6}          : {rest:>6} address(es) "
                      f"(hot wallets)\n")
            break


def selftest():
    import tempfile
    ok = True
    recs = [
        {"type": "SWEEP", "scripthash": "a" * 64, "block": 920000,
         "prev_txid": "f" * 64, "prev_vout": 0},
        {"type": "SWEEP", "scripthash": "b" * 64, "block": 920001,
         "prev_txid": "e" * 64, "prev_vout": 1},
        {"type": "SWEEP", "scripthash": "b" * 64, "block": 920002,
         "prev_txid": "d" * 64, "prev_vout": 2},
        {"type": "SWEEP", "scripthash": "b" * 64, "block": 920003,
         "prev_txid": "c" * 64, "prev_vout": 3},
        {"type": "FULL", "scripthash": "c" * 64, "block": 920004},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
        f.write("not json at all\n")          # must be skipped, not fatal
        p = f.name
    counts, prev, pvout, blocks, n = tally(p)

    good = n == 4 and set(counts) == {"a" * 64, "b" * 64}
    ok &= good
    sys.stderr.write(f"  4 SWEEP records over 2 addresses, FULL ignored and a "
                     f"malformed line skipped: {'OK' if good else 'FAIL'}\n")

    once = select(counts, 1, 1)
    good = once == ["a" * 64]
    ok &= good
    sys.stderr.write(f"  the 1x address survives, the 3x does not: "
                     f"{'OK' if good else 'FAIL'}\n")

    good = prev["a" * 64] == "f" * 64 and pvout["a" * 64] == 0
    ok &= good
    sys.stderr.write(f"  its prev_txid and prev_vout travel with it: "
                     f"{'OK' if good else 'FAIL'}\n")

    # for a reused address the EARLIEST spend is kept, not the last one seen
    good = prev["b" * 64] == "e" * 64 and blocks["b" * 64] == 920001
    ok &= good
    sys.stderr.write(f"  a reused address keeps its earliest sighting: "
                     f"{'OK' if good else 'FAIL'}\n")

    # prev_vout 0 is falsy -- it must survive, not be dropped by a truth test
    good = pvout["a" * 64] == 0 and pvout["a" * 64] is not None
    ok &= good
    sys.stderr.write(f"  prev_vout of 0 is preserved (falsy but valid): "
                     f"{'OK' if good else 'FAIL'}\n")
    os.unlink(p)

    # an empty input must report empty, never fail silently into a null result
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        p2 = f.name
    c2, _p, _v, _b, n2 = tally(p2)
    good = n2 == 0 and select(c2, 1, 1) == []
    ok &= good
    sys.stderr.write(f"  an empty scan yields an empty list and says so: "
                     f"{'OK' if good else 'FAIL'}\n")
    os.unlink(p2)

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="sweep_hits.jsonl")
    ap.add_argument("--out", default="swept_once.txt")
    ap.add_argument("--tsv", default="",
                    help="companion table with prev_txid (default: <out>.tsv)")
    ap.add_argument("--min-count", type=int, default=1)
    ap.add_argument("--max-count", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the multiplicity filter fails its own checks; refusing")
    if a.selftest:
        return
    if not os.path.exists(a.inp):
        sys.exit(f"no scan output at {a.inp}")

    counts, prev, pvout, blocks, n = tally(a.inp)
    funnel(counts, n, a.min_count, a.max_count)
    keep = select(counts, a.min_count, a.max_count)

    if not keep:
        sys.stderr.write(
            f"\n  NOTHING SELECTED. {len(counts):,} addresses were swept, none "
            f"between {a.min_count} and {a.max_count} times.\n"
            f"  That is a result about the filter, not about the chain.\n")

    # never clobber: the existing file may be the only copy of an earlier run
    if os.path.exists(a.out):
        os.replace(a.out, a.out + ".prev")
        sys.stderr.write(f"\n  existing {a.out} moved to {a.out}.prev\n")
    with open(a.out, "w", encoding="utf-8") as fh:
        for sh in keep:
            fh.write(sh + "\n")

    tsv = a.tsv or (a.out + ".tsv")
    with open(tsv, "w", encoding="utf-8") as fh:
        fh.write("scripthash\tspends\tfirst_sweep_block\tprev_txid\tprev_vout\n")
        for sh in keep:
            fh.write(f"{sh}\t{counts[sh]}\t{blocks.get(sh,'')}\t"
                     f"{prev.get(sh) or ''}\t"
                     f"{'' if pvout.get(sh) is None else pvout[sh]}\n")

    have = sum(1 for sh in keep if prev.get(sh))
    sys.stderr.write(f"\n  {len(keep):,} address(es) swept between "
                     f"{a.min_count} and {a.max_count} time(s) -> {a.out}\n"
                     f"  {have:,} of them carry a prev_txid -> {tsv}\n")
    if keep and not have:
        sys.stderr.write(
            "\n  WARNING: no prev_txid on any record. This scan predates the\n"
            "  change that captures it; re-run chain_tail_scan or age_check\n"
            "  will have nothing to date with.\n")
    else:
        sys.stderr.write(f"\n  next: age_check.py --in {a.out} "
                         f"--sweeps {a.inp} --rpc \"$B\"\n")


if __name__ == "__main__":
    main()
