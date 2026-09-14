#!/usr/bin/env python3
"""
FR1 (window filter) + FR5 (attribution ranking) -> /tmp/window_candidates.tsv

Two modes:

  --electrum   stage 2 of Path A. Takes electrum_sweep.py's output
               (scripthash, tx_count, funding_txid, height), resolves each
               funding tx to address/value and each height to a timestamp,
               applies the window filter, scores, and emits the TSV.
               Needs Bitcoin network access.

  --from-tsv   offline. Takes already-resolved rows (Path B's output, or
               anything with address/txid/height/time/value columns), applies
               the window filter, scores and emits. Runs anywhere.

Window default: 2022-10-01T00:00Z .. 2023-04-01T00:00Z (Keiser's article issue
through one month after the 4 Mar 2023 tweet).
"""
import argparse, hashlib, json, sys, datetime

WIN_LO = 1664582400   # 2022-10-01T00:00:00Z
WIN_HI = 1680307200   # 2023-04-01T00:00:00Z

# ---- FR5 attribution signals -------------------------------------------------
# Vanity prefixes are checked against the address body (after the version char),
# case-insensitively, since a grinder controls base58 case only loosely.
TOKENS = [
    ("keiser", 60), ("overdose", 60), ("bukele", 50), ("salvador", 50),
    ("volcano", 40), ("saketoshi", 40), ("stacyherbert", 40), ("stacy", 30),
    ("herbert", 30), ("biatch", 35), ("banana", 35), ("republic", 30),
    ("orange", 25), ("toxic", 25), ("maxkeiser", 60), ("maxk", 20),
    ("hyperbitcoin", 25), ("pill", 20), ("xxx", 25), ("mk", 8),
]
TWEET_TS = 1677888000          # 2023-03-04
ARTICLE_TS = 1664582400        # Fall 2022 issue, window open

def score(addr, value_sats, block_time, script_type):
    s = 0; why = []
    body = (addr or "")[1:].lower()
    for tok, w in TOKENS:
        if body.startswith(tok):
            s += w * 3; why.append(f"vanity-prefix:{tok}(+{w*3})")
        elif tok in body and len(tok) >= 5:
            s += w // 2; why.append(f"contains:{tok}(+{w//2})")
    if value_sats == 2_000_000_000:
        s += 40; why.append("exact-20.00000000(+40)")
    elif value_sats % 100_000_000 == 0:
        s += 15; why.append("whole-BTC(+15)")
    elif value_sats % 1_000_000 == 0:
        s += 5; why.append("round-to-0.01(+5)")
    if script_type == "p2pkh":
        s += 10; why.append("legacy-p2pkh(+10)")
    if block_time:
        # tighter than the window: the article issue and the tweet are the two
        # dates Keiser actually anchored the puzzle to
        for label, ts, w in (("article-issue", ARTICLE_TS, 12), ("tweet", TWEET_TS, 18)):
            d = abs(block_time - ts) / 86400.0
            if d <= 45:
                b = int(w * (1 - d / 45)); 
                if b > 0: s += b; why.append(f"near-{label}:{d:.0f}d(+{b})")
    return s, ";".join(why) or "-"

def iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def emit(rows, out_path):
    rows.sort(key=lambda r: (-r["score"], r["block_time"]))
    with open(out_path, "w") as f:
        f.write("address\tfunding_txid\tblock_height\tblock_time\tvalue_sats\t"
                "value_btc\tblock_time_iso\tscript_type\tin_window\tkeiser_score\tsignals\n")
        for r in rows:
            f.write(f"{r['address']}\t{r['funding_txid']}\t{r['block_height']}\t{r['block_time']}\t"
                    f"{r['value_sats']}\t{r['value_sats']/1e8:.8f}\t{iso(r['block_time']) if r['block_time'] else '-'}\t"
                    f"{r['script_type']}\t{r['in_window']}\t{r['score']}\t{r['signals']}\n")
    sys.stderr.write(f"wrote {len(rows)} rows -> {out_path}\n")

def load_tsv(path):
    rows = []
    with open(path) as f:
        hdr = f.readline().rstrip("\n").split("\t")
        ix = {h: i for i, h in enumerate(hdr)}
        need = ("address", "funding_txid", "block_height", "block_time", "value_sats")
        missing = [n for n in need if n not in ix]
        if missing: sys.exit(f"input missing columns: {missing}; got {hdr}")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(hdr): continue
            rows.append({
                "address": p[ix["address"]],
                "funding_txid": p[ix["funding_txid"]],
                "block_height": int(p[ix["block_height"]]),
                "block_time": int(p[ix["block_time"]]),
                "value_sats": int(p[ix["value_sats"]]),
                "script_type": p[ix["script_type"]] if "script_type" in ix else "?",
            })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-tsv", help="already-resolved rows (offline mode)")
    ap.add_argument("--electrum", help="electrum_sweep.py output (needs network)")
    ap.add_argument("--server", default="electrum.blockstream.info:50002")
    ap.add_argument("--out", default="/tmp/window_candidates.tsv")
    ap.add_argument("--all", action="store_true", help="keep out-of-window rows too (marked)")
    a = ap.parse_args()

    if a.from_tsv:
        rows = load_tsv(a.from_tsv)
    elif a.electrum:
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        from electrum_sweep import Electrum
        from alchemy_window_scan import script_to_address
        h, _, p = a.server.partition(":")
        e = Electrum(h, int(p or 50002)); e.connect()
        recs = []
        for line in open(a.electrum):
            line = line.strip()
            if not line or line.startswith("scripthash"): continue
            sh, txc, txid, hgt = line.split("\t")[:4]
            recs.append((sh, txid, int(hgt)))
        sys.stderr.write(f"resolving {len(recs)} funding txs\n")
        rows = []
        hdr_cache = {}
        for i in range(0, len(recs), 25):
            batch = recs[i:i+25]
            txres = e.call_batch([("blockchain.transaction.get", [t, True]) for _, t, _ in batch])
            need = sorted({hg for _, _, hg in batch if hg not in hdr_cache})
            if need:
                hres = e.call_batch([("blockchain.block.header", [hg]) for hg in need])
                for hg, hh in zip(need, hres):
                    hdr_cache[hg] = int.from_bytes(bytes.fromhex(hh)[68:72], "little") if hh else 0
            for (sh, txid, hgt), tx in zip(batch, txres):
                if not tx: continue
                for v in tx.get("vout", []):
                    spk = bytes.fromhex(v["scriptPubKey"]["hex"])
                    if hashlib.sha256(spk).hexdigest() != sh: continue
                    addr, kind = script_to_address(spk)
                    rows.append({"address": addr or v["scriptPubKey"].get("address", "?"),
                                 "funding_txid": txid, "block_height": hgt,
                                 "block_time": hdr_cache.get(hgt, 0),
                                 "value_sats": int(round(v["value"] * 1e8)),
                                 "script_type": kind})
            sys.stderr.write(f"  {min(i+25,len(recs))}/{len(recs)}\n")
    else:
        sys.exit("need --from-tsv or --electrum")

    for r in rows:
        r["in_window"] = "YES" if WIN_LO <= r["block_time"] < WIN_HI else "no"
        r["score"], r["signals"] = score(r["address"], r["value_sats"], r["block_time"], r["script_type"])
    inw = [r for r in rows if r["in_window"] == "YES"]
    sys.stderr.write(f"resolved={len(rows)} in-window={len(inw)}\n")
    emit(rows if a.all else inw, a.out)

if __name__ == "__main__":
    main()
