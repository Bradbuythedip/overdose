#!/usr/bin/env python3
"""
Is "funded before the claim, then swept" actually unusual? Control for it.

THE FINDING THIS TESTS
age_check dated the 99 exactly-20-BTC addresses swept once in the index-blind
window. 18 were funded before the 2023-03-04 announcement -- 9 of them before
the magazine went to press -- and sat 3.0 to 5.6 years before being emptied.
Written down like that it reads like a prize being claimed.

WHY IT MIGHT READ LIKE THAT ANYWAY
Every address in that set held exactly 20.00000000 BTC at the 2025-10-11
snapshot. An address holding a round 20 BTC that does not move for years is
ordinary cold storage, not a puzzle. So the question is not "are 18 of them
old" -- it is:

    is an exactly-20-BTC address that was SWEPT in this window more likely to
    be old than one that was NOT swept?

If the same ~18% of un-swept exactly-20 addresses are also pre-announcement,
the observation is the base rate and carries no information. This project has
twice reported an effect that survived only because the null was never matched
to the operation, so the null is computed here rather than asserted.

THE CONTROL SET
window/Tnew_exact_20.tsv holds 795 scripthashes that each held exactly
20.00000000 BTC at the snapshot. Remove the ones observed being swept and
sample from the remainder: same balance, same script-type mix, same index,
differing only in whether a sweep was seen.

  python3 base_rate.py --selftest
  python3 base_rate.py --make-control --n 150 --out control.txt
  python3 base_rate.py --compare age_profile.tsv control_profile.tsv
"""
import argparse, collections, json, os, random, sys

PRE = ("PRE-PRINT", "PRE-ANNOUNCE")


def load_795(path="window/Tnew_exact_20.tsv"):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        p = line.split("\t")
        if p and len(p[0]) == 64 and not p[0].startswith("scripthash"):
            out.append(p[0].strip().lower())
    return out


def observed_swept(path="sweep_hits.jsonl"):
    """Every scripthash seen being spent -- excluded from the control."""
    seen = set()
    if not os.path.exists(path):
        return seen
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("type") == "SWEEP" and r.get("scripthash"):
            seen.add(r["scripthash"])
    return seen


def read_profile(path):
    """(n_total, n_pre) from an age_check TSV."""
    if not os.path.exists(path):
        sys.exit(f"no profile at {path}")
    n = pre = 0
    with open(path, encoding="utf-8") as fh:
        head = fh.readline()
        if not head.startswith("class"):
            sys.exit(f"{path} is not an age_check profile")
        for line in fh:
            cls = line.split("\t")[0].strip()
            if not cls:
                continue
            n += 1
            if cls in PRE:
                pre += 1
    return n, pre


def fisher(a, b, c, d):
    """Two-sided Fisher exact p for [[a,b],[c,d]]. Exact, no scipy."""
    from math import comb
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def p_of(x):
        return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)

    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    obs = p_of(a)
    # sum every table at least as extreme, with a tolerance so that floating
    # point does not silently drop the observed table itself
    return min(1.0, sum(p_of(x) for x in range(lo, hi + 1)
                        if p_of(x) <= obs * (1 + 1e-9)))


def selftest():
    ok = True
    # a table with no association must not look significant
    p = fisher(18, 81, 18, 81)
    ok &= p > 0.9
    sys.stderr.write(f"  identical proportions -> p = {p:.3f} (expect ~1.0): "
                     f"{'OK' if p > 0.9 else 'FAIL'}\n")
    # a strong association must
    p2 = fisher(18, 81, 0, 99)
    ok &= p2 < 0.001
    sys.stderr.write(f"  18/99 vs 0/99 -> p = {p2:.2e}: "
                     f"{'OK' if p2 < 0.001 else 'FAIL'}\n")
    # pinned against a textbook value: Fisher's tea-tasting, [[3,1],[1,3]]
    p3 = fisher(3, 1, 1, 3)
    good = abs(p3 - 0.4857) < 0.002
    ok &= good
    sys.stderr.write(f"  tea-tasting [[3,1],[1,3]] -> p = {p3:.4f}, "
                     f"published 0.4857: {'OK' if good else 'FAIL'}\n")
    # symmetry: swapping the groups must not change the p-value
    ok &= abs(fisher(18, 81, 5, 94) - fisher(5, 94, 18, 81)) < 1e-12
    sys.stderr.write(f"  p is symmetric under swapping the two groups: "
                     f"{'OK' if abs(fisher(18,81,5,94)-fisher(5,94,18,81))<1e-12 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-control", action="store_true")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260914)
    ap.add_argument("--sweeps", default="sweep_hits.jsonl")
    ap.add_argument("--out", default="control.txt")
    ap.add_argument("--compare", nargs=2, metavar=("TREATMENT", "CONTROL"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the statistic fails its own checks; refusing")
    if a.selftest:
        return

    if a.make_control:
        all795 = load_795()
        if not all795:
            sys.exit("no window/Tnew_exact_20.tsv")
        swept = observed_swept(a.sweeps)
        pool = [s for s in all795 if s not in swept]
        sys.stderr.write(f"\n  {len(all795)} exactly-20 scripthashes\n"
                         f"  {len(swept)} observed being swept -> excluded\n"
                         f"  {len(pool)} in the control pool\n")
        if len(pool) < a.n:
            sys.stderr.write(f"  pool smaller than --n; using all {len(pool)}\n")
        rng = random.Random(a.seed)
        pick = rng.sample(pool, min(a.n, len(pool)))
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(sorted(pick)) + "\n")
        sys.stderr.write(f"  {len(pick)} sampled (seed {a.seed}) -> {a.out}\n\n"
                         f"  next:\n"
                         f"    age_check.py --in {a.out} --sweeps /dev/null "
                         f"--rpc \"$B\" --out control_profile.tsv\n"
                         f"    base_rate.py --compare age_profile.tsv "
                         f"control_profile.tsv\n")
        return

    if a.compare:
        tn, tp = read_profile(a.compare[0])
        cn, cp = read_profile(a.compare[1])
        if not tn or not cn:
            sys.exit("one of the profiles has no rows; nothing to compare")
        tr, cr = tp / tn, cp / cn
        p = fisher(tp, tn - tp, cp, cn - cp)
        sys.stderr.write(
            f"\n  {'group':<28} {'pre-claim':>10} {'total':>7} {'rate':>8}\n"
            f"  {'swept in the window':<28} {tp:>10} {tn:>7} {tr:>7.1%}\n"
            f"  {'never seen swept':<28} {cp:>10} {cn:>7} {cr:>7.1%}\n"
            f"\n  Fisher exact, two-sided: p = {p:.4f}\n\n")
        if p >= 0.05:
            sys.stderr.write(
                f"  NOT DISTINGUISHABLE FROM THE BASE RATE. An exactly-20-BTC\n"
                f"  address that was swept here is no more likely to predate the\n"
                f"  claim than one that was not. The 'dormant then claimed'\n"
                f"  shape is what these addresses look like anyway, and the\n"
                f"  {tp} hits carry no information about the puzzle.\n")
        else:
            sys.stderr.write(
                f"  SWEPT ADDRESSES ARE OLDER THAN THE BASE RATE (p = {p:.4f}).\n"
                f"  That is a real association. It still does not say WHICH\n"
                f"  address is the prize, or that any of them is -- only that\n"
                f"  this set is not the ordinary population. Verify by hand.\n")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
