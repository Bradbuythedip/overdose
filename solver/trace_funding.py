#!/usr/bin/env python3
"""
FR5 — funding-source attribution for surviving candidates.

For each candidate address, pulls its funding transaction and characterises the
source: who paid it, and does the transaction shape look like an exchange batch
payout, a personal wallet spend, or a coinjoin.

The puzzle wallet was funded by SOMEONE. If that someone is an exchange
withdrawal in the window, or an address Keiser has posted publicly, that is the
identification.

  python3 trace_funding.py --addrs surviving.txt --out funding_trace.tsv

  # or feed it the filtered address_check output directly
  awk -F'\t' '$4>=695000 && $4<=781000 && $10=="YES" {print $1}' \
      window_resolved.tsv > surviving.txt

Stdlib only. Resumable. Set --hops 2 to also walk one level further back.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from collections import Counter

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


def classify(tx):
    """Heuristic shape classification of a funding transaction."""
    vin = tx.get("vin", [])
    vout = tx.get("vout", [])
    n_in, n_out = len(vin), len(vout)
    vals = [v.get("value", 0) for v in vout]

    # exchange batch payout: one/few inputs fanning out to many recipients
    if n_out >= 10:
        return f"BATCH-PAYOUT ({n_in}-in/{n_out}-out) — likely exchange or payment processor"
    # coinjoin: many inputs, many equal-value outputs
    if n_in >= 5 and n_out >= 5:
        c = Counter(vals)
        if c.most_common(1)[0][1] >= 5:
            return f"COINJOIN-LIKE ({n_in}-in/{n_out}-out, {c.most_common(1)[0][1]} equal outputs)"
    # consolidation: many inputs to one output
    if n_in >= 5 and n_out <= 2:
        return f"CONSOLIDATION ({n_in}-in/{n_out}-out)"
    # personal spend: 1-2 in, 2 out (payment + change)
    if n_in <= 2 and n_out == 2:
        return f"PERSONAL-SPEND ({n_in}-in/2-out, payment+change)"
    if n_in <= 2 and n_out == 1:
        return f"SWEEP ({n_in}-in/1-out, no change)"
    return f"OTHER ({n_in}-in/{n_out}-out)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addrs", required=True)
    ap.add_argument("--out", default="funding_trace.tsv")
    ap.add_argument("--api", default=API)
    ap.add_argument("--sleep", type=float, default=0.35)
    ap.add_argument("--hops", type=int, default=1, help="1 = direct funders; 2 = also who funded them")
    a = ap.parse_args()

    addrs = []
    for l in open(a.addrs):
        l = l.strip()
        if not l or l.startswith("#") or l.startswith("address"): continue
        addrs.append(l.split("\t")[0].split(",")[0].strip())

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            done.add(line.split("\t")[0])
        sys.stderr.write(f"resuming: {len(done)} already done\n")
    else:
        with open(a.out, "w") as f:
            f.write("address\tfunding_txid\tshape\tn_inputs\tn_outputs\t"
                    "total_in_btc\tinput_addresses\thop2_sources\n")

    out = open(a.out, "a")
    todo = [x for x in addrs if x not in done]
    sys.stderr.write(f"tracing {len(todo)} addresses (hops={a.hops})\n\n")

    for ad in todo:
        time.sleep(a.sleep)
        txs = get(f"{a.api}/address/{ad}/txs/chain")
        if not txs:
            sys.stderr.write(f"  {ad}: no txs\n"); continue
        tx = txs[-1]                                  # oldest = funding tx
        txid = tx.get("txid", "")
        shape = classify(tx)
        vin = tx.get("vin", [])
        vout = tx.get("vout", [])
        in_addrs = []
        total_in = 0
        for v in vin:
            po = v.get("prevout") or {}
            ia = po.get("scriptpubkey_address")
            total_in += po.get("value", 0)
            if ia and ia not in in_addrs:
                in_addrs.append(ia)

        hop2 = []
        if a.hops >= 2:
            for ia in in_addrs[:3]:                   # cap the fan-out
                time.sleep(a.sleep)
                t2 = get(f"{a.api}/address/{ia}/txs/chain")
                if not t2: continue
                for v2 in (t2[-1].get("vin", []))[:5]:
                    po2 = v2.get("prevout") or {}
                    a2 = po2.get("scriptpubkey_address")
                    if a2 and a2 not in hop2:
                        hop2.append(a2)

        line = (f"{ad}\t{txid}\t{shape}\t{len(vin)}\t{len(vout)}\t"
                f"{total_in/1e8:.8f}\t{','.join(in_addrs[:8])}\t{','.join(hop2[:8])}\n")
        out.write(line); out.flush()

        # human-readable progress
        sys.stderr.write(f"{ad}\n")
        sys.stderr.write(f"   tx     {txid}\n")
        sys.stderr.write(f"   shape  {shape}\n")
        sys.stderr.write(f"   in     {total_in/1e8:.8f} BTC from {len(in_addrs)} distinct address(es)\n")
        for ia in in_addrs[:5]:
            sys.stderr.write(f"            {ia}\n")
        if len(in_addrs) > 5:
            sys.stderr.write(f"            ... +{len(in_addrs)-5} more\n")
        if hop2:
            sys.stderr.write(f"   hop2   {', '.join(hop2[:5])}\n")
        sys.stderr.write("\n")

    out.close()
    sys.stderr.write(f"DONE -> {a.out}\n\n")
    sys.stderr.write("WHAT TO LOOK FOR:\n")
    sys.stderr.write("  * BATCH-PAYOUT shape  -> exchange withdrawal. Paste the input address\n")
    sys.stderr.write("    into an explorer; if it is a labelled exchange hot wallet, the\n")
    sys.stderr.write("    depositor is likely identifiable only via the exchange.\n")
    sys.stderr.write("  * PERSONAL-SPEND      -> someone's own wallet paid it. The input address\n")
    sys.stderr.write("    is a real person's address. Search it publicly.\n")
    sys.stderr.write("  * Two or more candidates sharing an input address -> same funder, and\n")
    sys.stderr.write("    almost certainly not the puzzle (a puzzle wallet is funded once, alone).\n")

if __name__ == "__main__":
    main()
