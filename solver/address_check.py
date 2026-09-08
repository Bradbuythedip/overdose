#!/usr/bin/env python3
"""
FINAL STEP — FR1 + FR3 confirmation, now that candidates are plaintext addresses.

Supersedes the scripthash/Electrum route: we have addresses, so blockstream's
plain address endpoint does everything. For each address it fetches chain_stats
(FR3: tx_count == 1 and spent_txo_sum == 0) and the funding transaction
(FR1: block height + timestamp -> window filter; FR2: value).

Stdlib only. Resumable: re-running skips addresses already in --out.
Polite by default (--sleep); raise --workers only against your own esplora.

  python3 address_check.py --addrs window/candidates_p2pkh_exact20.txt \
                           --out window_resolved.tsv
  python3 resolve_and_rank.py --from-tsv window_resolved.tsv \
                           --out /tmp/window_candidates.tsv
"""
import argparse, json, os, sys, threading, queue, time, urllib.request, urllib.error

API = "https://blockstream.info/api"

def get(url, tries=4, timeout=30):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "overdose-solver/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if e.code in (429, 502, 503): time.sleep(min(2 ** a, 20)); continue
            raise
        except Exception:
            time.sleep(min(2 ** a, 20))
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addrs", required=True, help="one address per line")
    ap.add_argument("--out", default="window_resolved.tsv")
    ap.add_argument("--api", default=API)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=0.25)
    a = ap.parse_args()

    addrs = [l.strip() for l in open(a.addrs) if l.strip() and not l.startswith("#")]
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            done.add(line.split("\t")[0])
        sys.stderr.write(f"resuming: {len(done)} already done\n")
    else:
        with open(a.out, "w") as f:
            f.write("address\tscript_type\tfunding_txid\tblock_height\tblock_time\t"
                    "value_sats\ttx_count\tfunded_sats\tspent_sats\tfr3_pass\n")
    todo = [x for x in addrs if x not in done]
    sys.stderr.write(f"checking {len(todo)} addresses\n")

    q = queue.Queue(); [q.put(x) for x in todo]
    lock = threading.Lock(); out = open(a.out, "a"); n = [0]

    def kind(ad):
        if ad.startswith("bc1p"): return "p2tr"
        if ad.startswith("bc1") and len(ad) > 44: return "p2wsh"
        if ad.startswith("bc1"): return "p2wpkh"
        if ad.startswith("3"): return "p2sh"
        return "p2pkh"

    def worker():
        while True:
            try: ad = q.get_nowait()
            except queue.Empty: return
            time.sleep(a.sleep)
            st = get(f"{a.api}/address/{ad}")
            if st is None:
                with lock: sys.stderr.write(f"  {ad}: no data\n")
                continue
            cs = st.get("chain_stats", {})
            txc = cs.get("tx_count", -1)
            funded = cs.get("funded_txo_sum", 0); spent = cs.get("spent_txo_sum", -1)
            fr3 = "YES" if (txc == 1 and spent == 0) else "no"
            txid = ""; hgt = 0; ts = 0; val = 0
            txs = get(f"{a.api}/address/{ad}/txs/chain")
            if txs:
                t0 = txs[-1]                      # oldest = funding tx
                txid = t0.get("txid", "")
                stx = t0.get("status", {})
                hgt = stx.get("block_height", 0) or 0
                ts = stx.get("block_time", 0) or 0
                for v in t0.get("vout", []):
                    if v.get("scriptpubkey_address") == ad:
                        val = max(val, int(v.get("value", 0)))
            with lock:
                out.write(f"{ad}\t{kind(ad)}\t{txid}\t{hgt}\t{ts}\t{val}\t{txc}\t{funded}\t{spent}\t{fr3}\n")
                out.flush(); n[0] += 1
                if n[0] % 20 == 0:
                    sys.stderr.write(f"  {n[0]}/{len(todo)}\n"); sys.stderr.flush()

    ths = [threading.Thread(target=worker, daemon=True) for _ in range(a.workers)]
    [t.start() for t in ths]; [t.join() for t in ths]
    out.close()
    sys.stderr.write(f"DONE -> {a.out}\n")

if __name__ == "__main__":
    main()
