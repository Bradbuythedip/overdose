#!/usr/bin/env python3
"""
EVER-FUNDED oracle over an Esplora endpoint. Closes the blind spot.

WHAT THIS FIXES
Both offline indices in this repo are BALANCE SNAPSHOTS. address_map.bin
answers "holds coins today"; the rich-list index answers "held a large balance
in April 2023". Neither answers "was ever funded" — measured control: 32
canonical brainwallet phrases x 2 pubkey forms = 64 addresses that all
demonstrably held coins once and were drained years ago, 0 of 64 present in
either index. See window/the_oracle_blind_spot.md.

That matters because the most likely history for a magazine-printed key is that
it was weak, was cracked, and was swept long ago — in which case every offline
sweep in this project reports 0 hits even if handed the correct key.

Esplora's address endpoint returns exactly the missing field:

    GET {base}/address/{addr}
    {"chain_stats": {"funded_txo_count": N, "funded_txo_sum": sats,
                     "spent_txo_count": M, "spent_txo_sum": sats, ...}, ...}

funded_txo_count > 0 means the address RECEIVED coins at some point, whatever
the balance is now. That is the oracle this project has been missing.

THE CONTROL IS NOT OPTIONAL
This project's standing rule: a null from a data source means nothing until
that source has produced a known positive in the same run. So before any
candidate is queried, the script asks the endpoint about brainwallets that are
KNOWN to have been funded and drained. If those do not come back with
funded_txo_count > 0, the endpoint is not answering the question we think it is
and the script REFUSES to sweep. A "0 hits" from a misconfigured endpoint is
the exact failure this repo has already suffered once, when a scan reported 0
hits over 782 files that were all 404 bodies.

NOT TESTED AGAINST A LIVE ENDPOINT. Written offline, where all egress is
blocked. The control run is what will tell you it works; do not trust a null
from it until you have seen the control pass.

USAGE
    export ESPLORA=https://bitcoin-mainnet.g.alchemy.com/v2/YOUR_KEY
    python3 everfunded.py --selftest              # offline logic checks
    python3 everfunded.py --control-only          # hit the API, prove it works
    python3 everfunded.py --addresses addrs.txt
    python3 everfunded.py --phrases corpus.txt    # derive, then query

Results are cached to --cache so a re-run costs nothing and an interrupted run
resumes. Rate limited, retried with exponential backoff on 429/5xx.
"""
import argparse, hashlib, json, os, sys, time, urllib.error, urllib.request

# Brainwallets that were unquestionably funded and are unquestionably empty
# now. They are the control: the endpoint must report funded_txo_count > 0.
SWEPT_CONTROLS = ["satoshi", "password", "correct horse battery staple"]
# An address that has certainly received coins, as a second, non-derived check.
GENESIS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"


def derive_addresses(phrase):
    """P2PKH (both pubkey forms) for sha256(phrase). Import kept local so the
    control path works even without coincurve installed."""
    from coincurve import PrivateKey
    from hd_sweep import h160
    k = hashlib.sha256(phrase.encode()).digest()
    out = []
    for comp in (False, True):
        pub = PrivateKey(k).public_key.format(compressed=comp)
        out.append(b58check(b"\x00" + h160(pub)))
    return out


B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check(payload):
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(payload + chk) - len((payload + chk).lstrip(b"\0"))) + s


class Esplora:
    def __init__(self, base, cache=None, qps=4.0, timeout=20, retries=5):
        self.base = base.rstrip("/")
        self.min_gap = 1.0 / max(qps, 0.01)
        self.timeout, self.retries = timeout, retries
        self.last = 0.0
        self.cache_path = cache
        self.cache = {}
        if cache and os.path.exists(cache):
            with open(cache) as fh:
                for line in fh:
                    try:
                        d = json.loads(line)
                        self.cache[d["a"]] = d["s"]
                    except Exception:
                        pass
        self.cache_fh = open(cache, "a") if cache else None
        self.calls = 0

    def _get(self, path):
        gap = self.min_gap - (time.time() - self.last)
        if gap > 0:
            time.sleep(gap)
        url = f"{self.base}{path}"
        delay = 1.0
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "overdose-everfunded/1"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    self.last = time.time()
                    self.calls += 1
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
            except Exception:
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        raise RuntimeError(f"giving up on {url}")

    def stats(self, addr):
        """(funded_txo_count, funded_sum_sats, current_balance_sats) or None."""
        if addr in self.cache:
            return tuple(self.cache[addr])
        d = self._get(f"/address/{addr}")
        cs = d.get("chain_stats") or {}
        ms = d.get("mempool_stats") or {}
        fc = int(cs.get("funded_txo_count", 0)) + int(ms.get("funded_txo_count", 0))
        fs = int(cs.get("funded_txo_sum", 0)) + int(ms.get("funded_txo_sum", 0))
        bal = fs - int(cs.get("spent_txo_sum", 0)) - int(ms.get("spent_txo_sum", 0))
        v = (fc, fs, bal)
        self.cache[addr] = list(v)
        if self.cache_fh:
            self.cache_fh.write(json.dumps({"a": addr, "s": list(v)}) + "\n")
            self.cache_fh.flush()
        return v


def run_control(api):
    """The endpoint must report known-SWEPT addresses as ever-funded."""
    sys.stderr.write("\n  CONTROL — these must all come back funded_txo_count > 0.\n")
    sys.stderr.write("  If any says 0, the endpoint is not answering "
                     "'was it ever funded' and this script will refuse.\n\n")
    ok = True
    try:
        fc, fs, bal = api.stats(GENESIS)
        good = fc > 0
        sys.stderr.write(f"    {'genesis coinbase addr':34} funded_txo_count="
                         f"{fc:<6} received={fs/1e8:.4f} BTC  balance="
                         f"{bal/1e8:.4f}  {'OK' if good else 'FAIL'}\n")
        ok &= good
    except Exception as e:
        sys.stderr.write(f"    genesis lookup FAILED: {e}\n")
        return False
    for p in SWEPT_CONTROLS:
        try:
            addrs = derive_addresses(p)
        except Exception as e:
            sys.stderr.write(f"    cannot derive (need coincurve): {e}\n")
            return False
        best = (0, 0, 0)
        for a in addrs:
            try:
                s = api.stats(a)
            except Exception as e:
                sys.stderr.write(f"    {p!r} lookup FAILED: {e}\n")
                return False
            if s[0] > best[0]:
                best = s
        good = best[0] > 0
        ok &= good
        sys.stderr.write(f"    sha256({p!r})".ljust(36)
                         + f" funded_txo_count={best[0]:<6} "
                           f"received={best[1]/1e8:.4f} BTC  balance="
                           f"{best[2]/1e8:.4f}  {'OK' if good else 'FAIL'}\n")
    sys.stderr.write(f"\n  CONTROL {'PASSED' if ok else 'FAILED'} "
                     f"({api.calls} API calls)\n")
    if not ok:
        sys.stderr.write("  A swept brainwallet reporting 0 means this "
                         "endpoint returns balances, not history. Do not "
                         "trust any null from it.\n")
    return ok


def selftest():
    """Offline checks: address encoding and stats parsing."""
    ok = True
    # The encoder is checked by ROUND TRIP against this repo's independent
    # decoder, not against an address recalled from memory. An earlier version
    # of this selftest asserted a remembered "published" brainwallet address
    # and failed, because the remembered value was wrong — asserting recalled
    # constants as ground truth is precisely the failure mode this project
    # refuses to accept anywhere else.
    try:
        from index_oracle import spk_from_address
        spk = spk_from_address(GENESIS)          # 0x76 a9 14 <h160> 88 ac
        h160_of_genesis = spk[3:23]
        again = b58check(b"\x00" + h160_of_genesis)
        ok &= again == GENESIS
        sys.stderr.write(f"  round trip: {GENESIS} -> hash160 -> {again}  "
                         f"{'OK' if again == GENESIS else 'FAIL'}\n")
    except Exception as e:
        sys.stderr.write(f"  round-trip control unavailable: {e}\n")
        ok = False
    try:
        a = derive_addresses("satoshi")
        sys.stderr.write(f"  sha256('satoshi') -> {a[0]} uncompressed, "
                         f"{a[1]} compressed\n")
        from index_oracle import spk_from_address as _s
        ok &= all(_s(x) is not None for x in a)
        sys.stderr.write(f"  both derived addresses decode as valid "
                         f"Base58Check: {'OK' if ok else 'FAIL'}\n")
    except Exception as e:
        sys.stderr.write(f"  derivation unavailable (need coincurve): {e}\n")
        ok = False

    class Fake(Esplora):
        def __init__(self):
            self.cache, self.cache_fh, self.calls = {}, None, 0

        def _get(self, path):
            return {"chain_stats": {"funded_txo_count": 3,
                                    "funded_txo_sum": 500000000,
                                    "spent_txo_count": 3,
                                    "spent_txo_sum": 500000000},
                    "mempool_stats": {"funded_txo_count": 0,
                                      "funded_txo_sum": 0,
                                      "spent_txo_count": 0,
                                      "spent_txo_sum": 0}}
    f = Fake()
    fc, fs, bal = f.stats("x")
    good = fc == 3 and fs == 500000000 and bal == 0
    sys.stderr.write(f"  a fully-SWEPT address parses as funded_txo_count=3, "
                     f"balance=0: {'OK' if good else 'FAIL'}\n")
    sys.stderr.write("  ^ this is the whole point: balance 0, but it WAS "
                     "funded, and the offline indices cannot see it\n")
    ok &= good
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("ESPLORA", ""),
                    help="Esplora base URL, or set $ESPLORA")
    ap.add_argument("--addresses")
    ap.add_argument("--phrases")
    ap.add_argument("--cache", default="everfunded_cache.jsonl")
    ap.add_argument("--qps", type=float, default=4.0)
    ap.add_argument("--out", default="everfunded_hits.tsv")
    ap.add_argument("--control-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("offline logic checks failed; refusing to query anything")
    if a.selftest:
        return
    if not a.base:
        sys.exit("no endpoint: pass --base or set $ESPLORA")

    api = Esplora(a.base, cache=a.cache, qps=a.qps)
    if not run_control(api):
        sys.exit("control failed — refusing to sweep, a null here would be "
                 "meaningless")
    if a.control_only:
        return

    items = []
    if a.addresses:
        items = [("-", l.strip()) for l in open(a.addresses) if l.strip()]
    elif a.phrases:
        for l in open(a.phrases, encoding="utf-8"):
            p = l.rstrip("\n")
            if p:
                for ad in derive_addresses(p):
                    items.append((p[:60], ad))
    else:
        sys.exit("give --addresses or --phrases")

    sys.stderr.write(f"\n  querying {len(items):,} addresses at {a.qps}/s "
                     f"(~{len(items)/max(a.qps,0.01)/60:.0f} min)\n")
    fh = open(a.out, "w")
    fh.write("phrase\taddress\tfunded_txo_count\treceived_btc\tbalance_btc\n")
    hits = 0
    for i, (src, ad) in enumerate(items, 1):
        try:
            fc, fs, bal = api.stats(ad)
        except Exception as e:
            sys.stderr.write(f"  [{i}] {ad} error: {e}\n")
            continue
        if fc > 0:
            hits += 1
            fh.write(f"{src}\t{ad}\t{fc}\t{fs/1e8:.8f}\t{bal/1e8:.8f}\n")
            fh.flush()
            sys.stderr.write(f"  *** EVER-FUNDED {ad}  received "
                             f"{fs/1e8:.8f} BTC, balance {bal/1e8:.8f} "
                             f":: {src}\n")
        if i % 200 == 0:
            sys.stderr.write(f"  {i:,}/{len(items):,}  {hits} ever-funded\n")
    fh.close()
    sys.stderr.write(f"\n  DONE. {len(items):,} addresses, {hits} EVER-FUNDED "
                     f"-> {a.out}\n")
    sys.stderr.write("  Note: 'ever-funded' includes dust and unrelated "
                     "collisions. Check received amount and date before "
                     "concluding anything.\n")


if __name__ == "__main__":
    main()
