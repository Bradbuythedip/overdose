#!/usr/bin/env python3
"""
Turn ~30,000 twenty-BTC outputs into a shortlist by asking what became of them.

THE BASE RATE, MEASURED NOT ASSUMED
chain_tail_scan found 225 outputs of exactly 20.00000000 BTC in 1,037 blocks —
0.217 per block, extrapolating to ~29,707 across the 136,917 unscanned blocks,
and ~88,725 including the 19.9-20.1 band. One scripthash was paid exactly 20 BTC
47 times.

So an output of exactly 20 BTC is COMMON. Twenty is a round number people move:
exchange withdrawals, consolidations, OTC settlement. As a filter it selects
tens of thousands of things and is not a shortlist. The scan's FULL detector
finds every such output ever CREATED in the window, and most were spent within
hours.

WHAT ACTUALLY DISCRIMINATES
A prize nobody has claimed is still sitting there. So the question is not "was
20 BTC paid here" but "is 20 BTC STILL HERE". That needs current chain state,
one query per distinct scripthash, which the scan cannot know from a block
alone.

WHAT THIS DELIBERATELY DOES NOT DO
It does not silently drop anything. Address reuse, extra deposits and later dust
are all reported as ANNOTATIONS rather than used as exclusions, because each is
a plausible thing to happen to a real prize address: a duster sends it 546 sats,
Keiser tops it up, it is funded from an exchange batch. A filter that removes
99% of noise but has any real chance of removing the answer is the wrong trade
for a one-shot search. Narrowing is the caller's decision, made with the
annotations visible.

  python3 filter_full.py --selftest
  python3 filter_full.py --in chain_tail_hits.jsonl --rpc "$B"
"""
import argparse, collections, hashlib, json, os, sys, time

PRIZE_SATS = 2_000_000_000
BAND_LO, BAND_HI = 1_990_000_000, 2_010_000_000


class Esplora:
    def __init__(self, base, timeout=30):
        self.base, self.timeout = base.rstrip("/"), timeout

    def get(self, path):
        import urllib.request, urllib.error
        req = urllib.request.Request(
            self.base + path, headers={"User-Agent": "overdose-filter/1"})
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
                raise RuntimeError(f"cannot reach {self.base}: {e.reason}") from None
        raise RuntimeError(f"gave up on {path}")

    def state(self, scripthash):
        """(balance_sats, tx_count, funded_sum, spent_sum) for a scripthash."""
        d = self.get(f"/scripthash/{scripthash}")
        cs = d.get("chain_stats") or {}
        f, s = cs.get("funded_txo_sum", 0), cs.get("spent_txo_sum", 0)
        return f - s, cs.get("tx_count", 0), f, s


def load(path):
    recs = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def candidates(recs, known_795):
    """Distinct scripthashes from FULL records, with their provenance."""
    by = collections.OrderedDict()
    for r in recs:
        if r.get("type") != "FULL":
            continue
        sh = r["scripthash"]
        c = by.setdefault(sh, {
            "scripthash": sh, "spk": r.get("spk", ""), "hits": 0,
            "blocks": [], "tags": set(), "in_795": sh in known_795})
        c["hits"] += 1
        c["blocks"].append(r["block"])
        c["tags"].add(r.get("tag", ""))
    for c in by.values():
        c["tags"] = sorted(c["tags"])
        c["first_block"] = min(c["blocks"])
        c["last_block"] = max(c["blocks"])
        # annotations, never exclusions
        notes = []
        if c["hits"] > 3:
            notes.append(f"paid ~20 BTC {c['hits']}x — exchange-like reuse")
        if "EXACT_20" not in c["tags"]:
            notes.append("never an exact 20.00000000 payment")
        c["notes"] = notes
        del c["blocks"]
    return list(by.values())


def classify_state(bal, txc):
    """What the current chain state says about this scripthash."""
    if bal == 0:
        return "EMPTY", "everything that arrived here has been spent"
    if bal == PRIZE_SATS:
        return ("HOLDS_EXACT_20",
                "holds exactly 20.00000000 BTC right now"
                + (" in a single transaction" if txc == 1 else
                   f" across {txc} transactions"))
    if BAND_LO <= bal <= BAND_HI:
        return "HOLDS_NEAR_20", f"holds {bal/1e8:.8f} BTC"
    return "OTHER", f"holds {bal/1e8:.8f} BTC"


def load_795(path="window/Tnew_exact_20.tsv"):
    if not os.path.exists(path):
        return set()
    out = set()
    for line in open(path):
        p = line.split("\t")
        if p and len(p[0]) == 64 and not p[0].startswith("scripthash"):
            out.add(p[0].strip().lower())
    return out


def selftest():
    ok = True
    recs = [
        {"type": "FULL", "block": 830100, "tag": "EXACT_20",
         "scripthash": "a" * 64, "spk": "0014" + "11" * 20, "known": False},
        {"type": "FULL", "block": 830500, "tag": "EXACT_20",
         "scripthash": "a" * 64, "spk": "0014" + "11" * 20, "known": False},
        {"type": "FULL", "block": 830700, "tag": "NEAR_20",
         "scripthash": "b" * 64, "spk": "0014" + "22" * 20, "known": False},
        {"type": "PUBLISHER", "block": 830776, "matched": ["x"], "text": "y"},
    ]
    c = candidates(recs, {"b" * 64})
    ok &= len(c) == 2
    sys.stderr.write(f"  4 records -> {len(c)} distinct scripthashes "
                     f"(PUBLISHER ignored): {'OK' if len(c)==2 else 'FAIL'}\n")
    a = [x for x in c if x["scripthash"].startswith("a")][0]
    ok &= a["hits"] == 2 and a["first_block"] == 830100
    sys.stderr.write(f"  repeat payments collapsed, provenance kept "
                     f"({a['hits']} hits, blocks {a['first_block']}-"
                     f"{a['last_block']}): {'OK' if a['hits']==2 else 'FAIL'}\n")
    b = [x for x in c if x["scripthash"].startswith("b")][0]
    ok &= b["in_795"] and "never an exact" in " ".join(b["notes"])
    sys.stderr.write(f"  membership in the 795 recorded, NEAR-only annotated: "
                     f"{'OK' if b['in_795'] else 'FAIL'}\n")

    for bal, txc, want in ((0, 3, "EMPTY"), (PRIZE_SATS, 1, "HOLDS_EXACT_20"),
                           (PRIZE_SATS, 4, "HOLDS_EXACT_20"),
                           (1_995_000_000, 1, "HOLDS_NEAR_20"),
                           (500, 1, "OTHER")):
        got, _w = classify_state(bal, txc)
        ok &= got == want
        if got != want:
            sys.stderr.write(f"  classify_state({bal},{txc}) = {got} "
                             f"want {want}  FAIL\n")
    sys.stderr.write(f"  state classification over empty / exact / near / "
                     f"other: {'OK' if ok else 'FAIL'}\n")

    # a prize topped up or dusted must NOT be classed as uninteresting
    got, _w = classify_state(PRIZE_SATS + 546, 2)
    ok &= got == "HOLDS_NEAR_20"
    sys.stderr.write(f"  20 BTC plus a 546-sat dust payment still reads as "
                     f"near-20 rather than 'other': "
                     f"{'OK' if got=='HOLDS_NEAR_20' else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="chain_tail_hits.jsonl")
    ap.add_argument("--rpc", default=os.environ.get("B", ""),
                    help="Esplora base URL")
    ap.add_argument("--out", default="shortlist.jsonl")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("filter logic fails its own checks; refusing")
    if a.selftest:
        return
    if not os.path.exists(a.inp):
        sys.exit(f"no input at {a.inp}")

    recs = load(a.inp)
    known = load_795()
    cand = candidates(recs, known)
    blocks = [r["block"] for r in recs if "block" in r]
    sys.stderr.write(
        f"\n  {len(recs):,} records over blocks {min(blocks):,}-{max(blocks):,}\n"
        f"  {len(cand):,} distinct scripthashes were paid ~20 BTC\n"
        f"    {sum(1 for c in cand if c['in_795'])} already in the 795 snapshot, "
        f"{sum(1 for c in cand if not c['in_795'])} new to it\n")
    if not a.rpc:
        sys.exit("\n  need --rpc (or $B) to ask what became of them")

    api = Esplora(a.rpc)
    out = open(a.out, "w", encoding="utf-8")
    tally = collections.Counter()
    t0 = time.time()
    for i, c in enumerate(cand, 1):
        try:
            bal, txc, funded, spent = api.state(c["scripthash"])
        except RuntimeError as e:
            sys.stderr.write(f"\n  {c['scripthash'][:16]}…: {e}\n")
            continue
        state, why = classify_state(bal, txc)
        tally[state] += 1
        c.update({"balance": bal, "btc": bal / 1e8, "tx_count": txc,
                  "funded_sum": funded, "spent_sum": spent,
                  "state": state, "why": why})
        out.write(json.dumps(c, ensure_ascii=False) + "\n")
        out.flush()
        if state.startswith("HOLDS"):
            flag = "" if c["in_795"] else "  *** NOT IN THE 795 ***"
            sys.stderr.write(f"\n  {state}  {c['btc']:.8f} BTC  "
                             f"tx_count {txc}  {c['scripthash'][:32]}…{flag}\n")
            for n in c["notes"]:
                sys.stderr.write(f"      note: {n}\n")
        if sys.stderr.isatty():
            el = time.time() - t0
            sys.stderr.write(f"\r  {i}/{len(cand)}  {i/max(el,1e-9):.1f}/s   ")
            sys.stderr.flush()
    out.close()

    sys.stderr.write(f"\n\n  RESULT over {len(cand):,} scripthashes\n")
    for k, v in tally.most_common():
        sys.stderr.write(f"    {k:16} {v:>6,}\n")
    live = tally["HOLDS_EXACT_20"] + tally["HOLDS_NEAR_20"]
    sys.stderr.write(
        f"\n  {live:,} still hold ~20 BTC. Those are the candidates; the rest\n"
        f"  were ordinary flows that have since moved on. -> {a.out}\n")


if __name__ == "__main__":
    main()
