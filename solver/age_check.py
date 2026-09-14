#!/usr/bin/env python3
"""
For addresses emptied in the index-blind window: WHEN were they funded?

THE LEAD THIS ANSWERS
`chain_tail_scan --start 918000` walks the region `address_map.bin` cannot see
(it is a 2025-10-11 snapshot; see `window/index_horizon.md`). Across ~31,000
blocks it found 1,449 SWEEP records against the 795 exactly-20-BTC scripthashes
— but only **106 distinct addresses**, and the records are dominated by hot
wallets: one scripthash accounts for 18 of the first 20.

Of those 106, **64 were swept exactly once**. That is the shape a claimed prize
has: funded, dormant, then a single spend.

But "swept once inside this window" is not yet "dormant then claimed". An
address funded last month and spent once looks identical here. The
discriminator is the FUNDING DATE:

    the prize was printed in a Fall 2021 magazine and announced 2023-03-04
    (block ~782,000), so a genuine prize address existed and was funded at or
    before then, and sat untouched for years

So for each address this reports first-funding height, the sweep height, and
the dormancy between them. Long dormancy across the announcement is the signal;
a recent funding is ordinary flow.

WHAT IT DOES NOT DO
It does not filter. An adversarial review of candidate filters for this exact
problem returned `survived: []` — every proposed narrowing criterion either
failed to discriminate or risked discarding the prize. So this ranks and
annotates, and the exclusion is the reader's call with the evidence visible.

  python3 age_check.py --selftest
  python3 age_check.py --in swept_once.txt --rpc "$B"
"""
import argparse, json, os, sys, time

ANNOUNCE_BLOCK = 782000      # 2023-03-04, "it's for 20 BTC"
PRINT_BLOCK = 700000         # ~Sept 2021, the El Salvador issue


class Esplora:
    def __init__(self, base, timeout=30):
        self.base, self.timeout = base.rstrip("/"), timeout

    def get(self, path):
        import urllib.request, urllib.error
        req = urllib.request.Request(
            self.base + path, headers={"User-Agent": "overdose-age/1"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"HTTP {e.code} on {path}") from None
            except urllib.error.URLError as e:
                if attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"unreachable: {e.reason}") from None
        raise RuntimeError(f"gave up on {path}")

    def history(self, sh, cap=40):
        """All confirmed txs for a scripthash, oldest last. Pages backwards.

        Esplora returns the most recent 25 and pages with the last seen txid.
        A dormant address has 2, so this almost always costs one call; the cap
        stops a hot wallet from costing hundreds.
        """
        out, last = [], None
        while len(out) < cap:
            p = f"/scripthash/{sh}/txs/chain"
            if last:
                p += f"/{last}"
            batch = self.get(p)
            if not batch:
                break
            out += batch
            if len(batch) < 25:
                break
            last = batch[-1]["txid"]
        return out


def profile(api, sh):
    """(first_funded_height, last_height, n_tx, note) for one scripthash."""
    txs = api.history(sh)
    if not txs:
        return None, None, 0, "no confirmed history"
    heights = [t.get("status", {}).get("block_height")
               for t in txs if t.get("status", {}).get("confirmed")]
    heights = [h for h in heights if h]
    if not heights:
        return None, None, len(txs), "unconfirmed only"
    note = ""
    if len(txs) >= 40:
        note = "history truncated at the cap; first funding may be older"
    return min(heights), max(heights), len(txs), note


def classify(first, sweep):
    """How interesting is this history?"""
    if first is None:
        return "UNKNOWN", ""
    if first <= PRINT_BLOCK:
        return "PRE-PRINT", "funded before the magazine went to press"
    if first <= ANNOUNCE_BLOCK:
        return "PRE-ANNOUNCE", "funded before the 2023-03-04 claim"
    if sweep and first > sweep - 1000:
        return "TRANSIENT", "funded and spent within ~1 week"
    return "RECENT", "funded after the claim"


def selftest():
    ok = True
    for first, sweep, want in ((690000, 940000, "PRE-PRINT"),
                               (770000, 940000, "PRE-ANNOUNCE"),
                               (939500, 940000, "TRANSIENT"),
                               (900000, 940000, "RECENT"),
                               (None, 940000, "UNKNOWN")):
        got, _w = classify(first, sweep)
        ok &= got == want
        if got != want:
            sys.stderr.write(f"  classify({first},{sweep}) = {got} "
                             f"want {want}  FAIL\n")
    sys.stderr.write(f"  classification over pre-print / pre-announce / "
                     f"transient / recent / unknown: {'OK' if ok else 'FAIL'}\n")
    sys.stderr.write(f"  announcement block {ANNOUNCE_BLOCK:,} (2023-03-04), "
                     f"print block {PRINT_BLOCK:,} (~Sept 2021)\n")
    # the ordering must be strict: a pre-print address is also pre-announce,
    # and must be reported as the STRONGER label
    got, _w = classify(650000, 940000)
    ok &= got == "PRE-PRINT"
    sys.stderr.write(f"  a very old funding reports PRE-PRINT, not "
                     f"PRE-ANNOUNCE: {'OK' if got=='PRE-PRINT' else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="swept_once.txt",
                    help="one scripthash per line")
    ap.add_argument("--sweeps", default="chain_tail_hits.jsonl",
                    help="the scan output, to recover each sweep's block")
    ap.add_argument("--rpc", default=os.environ.get("B", ""))
    ap.add_argument("--out", default="age_profile.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("classification is wrong; refusing")
    if a.selftest:
        return
    if not os.path.exists(a.inp):
        sys.exit(f"no input at {a.inp}")
    if not a.rpc:
        sys.exit("need --rpc (or $B)")

    shs = [l.strip().lower() for l in open(a.inp) if len(l.strip()) == 64]
    sweep_block = {}
    if os.path.exists(a.sweeps):
        for line in open(a.sweeps, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") == "SWEEP":
                sweep_block.setdefault(r["scripthash"], r["block"])

    sys.stderr.write(f"\n  {len(shs)} scripthash(es) swept once in the "
                     f"index-blind window\n")
    sys.stderr.write(f"  asking the chain when each was FIRST funded\n\n")

    api = Esplora(a.rpc)
    rows = []
    for i, sh in enumerate(shs, 1):
        try:
            first, last, n, note = profile(api, sh)
        except RuntimeError as e:
            sys.stderr.write(f"  {sh[:16]}…: {e}\n")
            continue
        swp = sweep_block.get(sh)
        tag, why = classify(first, swp)
        dorm = (swp - first) if (first and swp) else None
        rows.append((tag, sh, first, swp, dorm, n, why, note))
        if tag in ("PRE-PRINT", "PRE-ANNOUNCE"):
            sys.stderr.write(
                f"\n  *** {tag}  {sh[:40]}…\n"
                f"      funded block {first:,}, swept {swp:,}, "
                f"dormant {dorm:,} blocks (~{dorm/144/365:.1f} yr), "
                f"{n} tx\n      {why}\n")
        if sys.stderr.isatty():
            sys.stderr.write(f"\r  {i}/{len(shs)}  ")
            sys.stderr.flush()

    order = {"PRE-PRINT": 0, "PRE-ANNOUNCE": 1, "RECENT": 2,
             "TRANSIENT": 3, "UNKNOWN": 4}
    rows.sort(key=lambda r: (order.get(r[0], 9), r[2] or 10 ** 9))
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("class\tscripthash\tfirst_funded\tswept\tdormant_blocks\t"
                 "tx_count\twhy\tnote\n")
        for r in rows:
            fh.write("\t".join("" if x is None else str(x) for x in r) + "\n")

    import collections
    tally = collections.Counter(r[0] for r in rows)
    sys.stderr.write(f"\n\n  {len(rows)} profiled -> {a.out}\n")
    for k in ("PRE-PRINT", "PRE-ANNOUNCE", "RECENT", "TRANSIENT", "UNKNOWN"):
        if tally[k]:
            sys.stderr.write(f"    {k:14} {tally[k]:>4}\n")
    hot = tally["PRE-PRINT"] + tally["PRE-ANNOUNCE"]
    if hot:
        sys.stderr.write(
            f"\n  {hot} address(es) were funded before Keiser's claim, sat, and "
            f"were emptied\n  in the window no oracle here can see. That is the "
            f"profile of a prize being\n  claimed. It is not proof — verify each "
            f"funding transaction by hand.\n")
    else:
        sys.stderr.write(
            "\n  none predates the claim. Every address emptied in the blind "
            "window was\n  funded after 2023-03-04, so none has the "
            "dormant-prize profile.\n")


if __name__ == "__main__":
    main()
