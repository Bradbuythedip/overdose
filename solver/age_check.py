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

WHY THERE IS A CAPABILITY PROBE
The first version of this ran against an endpoint that does not serve the
history path, failed on all 64 with HTTP 400, and then printed "none predates
the claim" — a confident negative derived from ZERO profiled addresses. A null
from a test that never ran is the error this project exists to avoid, so the
probe runs first and the verdict is gated on how many addresses actually
resolved.

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
        self.hist_path = None          # discovered by probe()

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

    def probe(self, sample_sh):
        """Find a history path this endpoint actually serves, or None.

        Sixty-four identical HTTP 400s followed by a verdict is worse than one
        clear refusal, so this runs before any real work.
        """
        for tmpl in ("/scripthash/{}/txs", "/scripthash/{}/txs/chain"):
            p = tmpl.format(sample_sh)
            try:
                r = self.get(p)
            except RuntimeError as e:
                sys.stderr.write(f"    {tmpl}  ->  {e}\n")
                continue
            if isinstance(r, list):
                sys.stderr.write(f"    {tmpl}  ->  OK ({len(r)} tx)\n")
                self.hist_path = tmpl
                return tmpl
            sys.stderr.write(f"    {tmpl}  ->  unexpected shape "
                             f"{type(r).__name__}\n")
        return None

    def history(self, sh, cap=40):
        """All confirmed txs for a scripthash, oldest last. Pages backwards."""
        if not self.hist_path:
            raise RuntimeError("no history path; probe() found none")
        out, last = [], None
        while len(out) < cap:
            p = self.hist_path.format(sh)
            if last:
                p = f"/scripthash/{sh}/txs/chain/{last}"
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


def verdict(rows, n_input):
    """The summary. MUST NOT conclude anything from an empty result set."""
    import collections
    tally = collections.Counter(r[0] for r in rows)
    out = []
    if not rows:
        out.append("NO VERDICT — 0 of %d addresses were profiled." % n_input)
        out.append("  The endpoint could not answer the question, so this says")
        out.append("  nothing about whether any address predates the claim.")
        out.append("  An earlier version printed a confident negative here.")
        return "\n".join(out), tally
    hot = tally["PRE-PRINT"] + tally["PRE-ANNOUNCE"]
    if hot:
        out.append(f"{hot} address(es) were funded before Keiser's claim, sat, "
                   f"and were emptied")
        out.append("  in the window no oracle here can see. That is the profile "
                   "of a prize being")
        out.append("  claimed. It is not proof — verify each funding "
                   "transaction by hand.")
    elif len(rows) == n_input:
        out.append("None of the %d predates the claim. Every address emptied in "
                   "the blind" % n_input)
        out.append("  window was funded after 2023-03-04, so none has the "
                   "dormant-prize profile.")
    else:
        out.append(f"PARTIAL — {len(rows)} of {n_input} profiled, and none of "
                   f"THOSE predates the")
        out.append(f"  claim. The other {n_input - len(rows)} are unresolved "
                   f"and this says nothing about them.")
    return "\n".join(out), tally


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
    got, _w = classify(650000, 940000)
    ok &= got == "PRE-PRINT"
    sys.stderr.write(f"  a very old funding reports PRE-PRINT, not "
                     f"PRE-ANNOUNCE: {'OK' if got=='PRE-PRINT' else 'FAIL'}\n")

    # THE REGRESSION THAT MATTERS: an empty result set must NOT produce a
    # negative conclusion. The first version of this file did exactly that.
    msg, _t = verdict([], 64)
    bad = "none predates" in msg.lower() or "every address" in msg.lower()
    ok &= ("NO VERDICT" in msg) and not bad
    sys.stderr.write(f"  0 profiled -> NO VERDICT, not a negative conclusion: "
                     f"{'OK' if ('NO VERDICT' in msg and not bad) else 'FAIL'}\n")
    msg2, _t = verdict([("RECENT", "x", 900000, 940000, 40000, 2, "", "")], 64)
    ok &= "PARTIAL" in msg2
    sys.stderr.write(f"  1 of 64 profiled -> PARTIAL, scoped to what ran: "
                     f"{'OK' if 'PARTIAL' in msg2 else 'FAIL'}\n")
    rows = [("RECENT", str(i), 900000, 940000, 40000, 2, "", "")
            for i in range(64)]
    msg3, _t = verdict(rows, 64)
    ok &= "None of the 64" in msg3
    sys.stderr.write(f"  64 of 64 profiled -> the negative IS allowed: "
                     f"{'OK' if 'None of the 64' in msg3 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="swept_once.txt")
    ap.add_argument("--sweeps", default="chain_tail_hits.jsonl")
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

    api = Esplora(a.rpc)
    sys.stderr.write(f"\n  {len(shs)} scripthash(es) swept once in the "
                     f"index-blind window\n")
    sys.stderr.write("\n  PROBING the endpoint for a usable history path\n")
    if not shs:
        sys.exit("  no scripthashes in the input")
    if not api.probe(shs[0]):
        sys.stderr.write(
            "\n  This endpoint serves /scripthash/{h} — filter_full.py depends\n"
            "  on that — but NOT the transaction-history paths, so it cannot\n"
            "  answer when an address was first funded.\n"
            "\n  NO VERDICT. Nothing has been tested.\n"
            "\n  Two ways forward:\n"
            "    1. Point --rpc at a full Esplora instance (blockstream.info/api\n"
            "       or a self-hosted one) which serves /scripthash/{h}/txs.\n"
            "    2. Avoid history entirely: a SWEEP transaction's input names\n"
            "       the funding txid, and /tx/{txid} gives its block height.\n"
            "       That needs chain_tail_scan to record the spending txid in\n"
            "       its SWEEP records, which it does not yet do.\n")
        sys.exit(2)

    sys.stderr.write(f"\n  using {api.hist_path}\n\n")
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

    msg, tally = verdict(rows, len(shs))
    sys.stderr.write(f"\n\n  {len(rows)} of {len(shs)} profiled -> {a.out}\n")
    for k in ("PRE-PRINT", "PRE-ANNOUNCE", "RECENT", "TRANSIENT", "UNKNOWN"):
        if tally[k]:
            sys.stderr.write(f"    {k:14} {tally[k]:>4}\n")
    sys.stderr.write("\n  " + msg + "\n")


if __name__ == "__main__":
    main()
