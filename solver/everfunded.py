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
import argparse, hashlib, json, os, queue, sys, threading, time
import urllib.error, urllib.request

# Brainwallets that were unquestionably funded and are unquestionably empty
# now. They are the control: the endpoint must report funded_txo_count > 0.
#
# The addresses are PRECOMPUTED so that --control-only and --addresses run on a
# bare Python with no third-party packages and no repo data files. They are not
# recalled constants: each is sha256(phrase) -> P2PKH, derived by this repo's
# own code, and `--verify-controls` re-derives them from the phrases and checks
# they still match, so a typo here cannot silently weaken the control.
SWEPT_CONTROLS = [
    ("satoshi", "1ADJqstUMBB5zFquWg19UqZ7Zc6ePCpzLE",
     "1xm4vFerV3pSgvBFkyzLgT1Ew3HQYrS1V"),
    ("password", "16ga2uqnF1NqpAuQeeg7sTCAdtDUwDyJav",
     "16qVRutZ7rZuPx7NMtapvZorWYjyaME2Ue"),
    ("correct horse battery staple", "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T",
     "1C7zdTfnkzmr13HfA2vNm5SJYRK6nEKyq8"),
]
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


def b58decode_h160(addr):
    """hash160 from a P2PKH address, verifying the checksum. Stdlib only."""
    n = 0
    for ch in addr:
        if ch not in B58:
            return None
        n = n * 58 + B58.index(ch)
    b = n.to_bytes(25, "big")
    if hashlib.sha256(hashlib.sha256(b[:21]).digest()).digest()[:4] != b[21:]:
        return None
    return b[1:21]


class Adaptive:
    """AIMD rate control: ramp up until the endpoint pushes back, then back off.

    Additive increase, multiplicative decrease — the same control law TCP uses,
    for the same reason: it finds the ceiling without knowing it in advance and
    it recovers politely when the ceiling moves. Every success nudges the rate
    up a little; every 429/503 halves it and imposes a cooldown, so a burst of
    throttles collapses the rate fast instead of hammering a limiter.

    A token bucket rather than a sleep-per-request, so N worker threads share
    one global rate instead of each keeping its own.
    """

    def __init__(self, start=8.0, cap=400.0, floor=0.5, step=0.5):
        self.rate, self.cap, self.floor, self.step = start, cap, floor, step
        self.tokens = start
        self.last = time.time()
        self.lock = threading.Lock()
        self.ok_since_change = 0
        self.throttles = 0
        self.peak = start
        self.cooldown_until = 0.0

    def take(self):
        while True:
            with self.lock:
                now = time.time()
                self.tokens = min(self.rate,
                                  self.tokens + (now - self.last) * self.rate)
                self.last = now
                if now >= self.cooldown_until and self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                need = max((1.0 - self.tokens) / max(self.rate, 1e-6),
                           self.cooldown_until - now, 0.005)
            time.sleep(min(need, 0.5))

    def on_ok(self):
        with self.lock:
            self.ok_since_change += 1
            # additive increase, and slower the higher we already are
            if self.ok_since_change >= max(20, int(self.rate)):
                self.rate = min(self.cap, self.rate + self.step)
                self.peak = max(self.peak, self.rate)
                self.ok_since_change = 0

    def on_throttle(self):
        with self.lock:
            self.throttles += 1
            self.rate = max(self.floor, self.rate * 0.5)
            self.ok_since_change = 0
            self.cooldown_until = time.time() + 1.0


class Esplora:
    def __init__(self, base, cache=None, qps=4.0, timeout=20, retries=5,
                 adaptive=None):
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
        self.adaptive = adaptive
        self._iolock = threading.Lock()

    def _get(self, path):
        if self.adaptive is not None:
            self.adaptive.take()
        else:
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
                    with self._iolock:
                        self.calls += 1
                    if self.adaptive is not None:
                        self.adaptive.on_ok()
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504):
                    if self.adaptive is not None:
                        self.adaptive.on_throttle()
                    if attempt < self.retries - 1:
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
        with self._iolock:
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
    for p, a_unc, a_comp in SWEPT_CONTROLS:
        addrs = [a_unc, a_comp]
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
    # Round trip using only this file: decode -> re-encode -> must match. An
    # earlier version asserted a REMEMBERED "published" brainwallet address as
    # ground truth and failed, because the remembered value was wrong.
    # Asserting recalled constants is the failure mode this project refuses
    # everywhere else, so nothing here is asserted from memory.
    again = b58check(b"\x00" + b58decode_h160(GENESIS))
    ok &= again == GENESIS
    sys.stderr.write(f"  round trip: {GENESIS} -> hash160 -> {again}  "
                     f"{'OK' if again == GENESIS else 'FAIL'}\n")

    bad = 0
    for _p, u, c in SWEPT_CONTROLS:
        for ad in (u, c):
            if b58decode_h160(ad) is None:
                bad += 1
    ok &= bad == 0
    sys.stderr.write(f"  {2*len(SWEPT_CONTROLS)} embedded control addresses "
                     f"are valid Base58Check: {'OK' if not bad else 'FAIL'}\n")

    class Fake(Esplora):
        def __init__(self):
            self.cache, self.cache_fh, self.calls = {}, None, 0
            self.adaptive = None
            self._iolock = threading.Lock()

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
    ap.add_argument("--qps", type=float, default=4.0,
                    help="fixed rate; ignored when --auto is used")
    ap.add_argument("--auto", action="store_true",
                    help="ramp the rate up until the endpoint throttles, then "
                         "back off and keep probing (AIMD)")
    ap.add_argument("--workers", type=int, default=32,
                    help="concurrent requests, with --auto")
    ap.add_argument("--start-qps", type=float, default=8.0)
    ap.add_argument("--cap-qps", type=float, default=400.0)
    ap.add_argument("--out", default="everfunded_hits.tsv")
    ap.add_argument("--control-only", action="store_true")
    ap.add_argument("--verify-controls", action="store_true",
                    help="re-derive the embedded control addresses from their "
                         "phrases (needs coincurve) and confirm they match")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("offline logic checks failed; refusing to query anything")
    if a.verify_controls:
        bad = 0
        for p, u, c in SWEPT_CONTROLS:
            got = derive_addresses(p)
            good = got == [u, c]
            bad += 0 if good else 1
            sys.stderr.write(f"  {p!r:34} embedded {u} / {c}\n"
                             f"  {'':34} derived  {got[0]} / {got[1]}  "
                             f"{'OK' if good else 'MISMATCH'}\n")
        sys.exit(0 if not bad else "embedded control addresses do not match "
                                   "their phrases")
    if a.selftest:
        return
    if not a.base:
        sys.exit("no endpoint: pass --base or set $ESPLORA")

    ad = Adaptive(start=a.start_qps, cap=a.cap_qps) if a.auto else None
    api = Esplora(a.base, cache=a.cache, qps=a.qps, adaptive=ad)
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

    # CACHED ENTRIES ARE STILL REPORTED. An earlier version filtered them out
    # of the work list and then only recorded hits found in that list, so a
    # fully-cached re-run printed "0 EVER-FUNDED" while the cache itself held
    # known hits — a silent FALSE NEGATIVE, and the worst kind, because it
    # looked like a clean completed sweep. The cache decides what needs an API
    # CALL; it never decides what gets reported.
    cached = [(s_, x) for s_, x in items if x in api.cache]
    todo = [(s_, x) for s_, x in items if x not in api.cache]
    sys.stderr.write(f"\n  {len(items):,} addresses, {len(cached):,} "
                     f"already cached (reported from cache, no API call), "
                     f"{len(todo):,} to fetch\n")
    if ad:
        sys.stderr.write(f"  ADAPTIVE: starting {a.start_qps}/s, {a.workers} "
                         f"workers, ramping until the endpoint throttles then "
                         f"halving. Ctrl-C is safe, progress is cached.\n")
    else:
        sys.stderr.write(f"  fixed {a.qps}/s "
                         f"(~{len(todo)/max(a.qps,0.01)/60:.0f} min)\n")

    fh = open(a.out, "w")
    fh.write("phrase\taddress\tfunded_txo_count\treceived_btc\tbalance_btc\n")
    state = {"done": 0, "hits": 0, "err": 0, "fetched": 0}
    lock = threading.Lock()
    t0 = time.time()

    def record(src, addr, fc, fs, bal):
        with lock:
            state["done"] += 1
            if fc > 0:
                state["hits"] += 1
                fh.write(f"{src}\t{addr}\t{fc}\t{fs/1e8:.8f}\t{bal/1e8:.8f}\n")
                fh.flush()
                sys.stderr.write(f"  *** EVER-FUNDED {addr}  received "
                                 f"{fs/1e8:.8f} BTC, balance {bal/1e8:.8f} "
                                 f":: {src}\n")
            n = state["done"]
            if n % 250 == 0:
                el = max(time.time() - t0, 1e-9)
                # progress is against everything being EVALUATED; rate and eta
                # only make sense for the part actually being FETCHED, so they
                # are suppressed when the run is served from cache
                total = len(cached) + len(todo)
                if state["fetched"]:
                    r = state["fetched"] / el
                    eta = (len(todo) - state["fetched"]) / max(r, 1e-9) / 60
                    extra = (f"  {r:5.1f}/s  eta {eta:4.0f}m" +
                             (f"  rate {ad.rate:6.1f}/s peak {ad.peak:.0f} "
                              f"throttled {ad.throttles}" if ad else ""))
                else:
                    extra = "  (from cache)"
                sys.stderr.write(f"  {n:,}/{total:,}  {state['hits']} "
                                 f"ever-funded{extra}\n")

    # replay the cache first, so a resumed or fully-cached run reports every
    # hit it already knows about
    for src, addr in cached:
        try:
            fc, fs, bal = api.stats(addr)
            record(src, addr, fc, fs, bal)
        except Exception:
            pass

    if not ad or a.workers <= 1:
        for src, addr in todo:
            try:
                fc, fs, bal = api.stats(addr)
                state["fetched"] += 1
                record(src, addr, fc, fs, bal)
            except Exception as e:
                state["err"] += 1
                sys.stderr.write(f"  {addr} error: {e}\n")
    else:
        q = queue.Queue()
        for it in todo:
            q.put(it)

        def worker():
            while True:
                try:
                    src, addr = q.get_nowait()
                except queue.Empty:
                    return
                try:
                    fc, fs, bal = api.stats(addr)
                    with lock:
                        state["fetched"] += 1
                    record(src, addr, fc, fs, bal)
                except Exception as e:
                    with lock:
                        state["err"] += 1
                        if state["err"] <= 10:
                            sys.stderr.write(f"  {addr} error: {e}\n")
                finally:
                    q.task_done()

        ts = [threading.Thread(target=worker, daemon=True)
              for _ in range(a.workers)]
        for t in ts:
            t.start()
        try:
            for t in ts:
                t.join()
        except KeyboardInterrupt:
            sys.stderr.write("\n  interrupted — everything fetched so far is "
                             "in the cache; re-run to resume\n")
    fh.close()
    el = max(time.time() - t0, 1e-9)
    sys.stderr.write(f"\n  {state['done']:,} evaluated "
                     f"({state['fetched']:,} fetched) in {el/60:.1f} min "
                     f"({state['fetched']/el:.1f}/s fetch rate"
                     + (f", peak rate {ad.peak:.0f}/s, {ad.throttles} throttles"
                        if ad else "") + f"), {state['err']} errors\n")
    hits = state["hits"]
    sys.stderr.write(f"\n  DONE. {len(items):,} addresses, {hits} EVER-FUNDED "
                     f"-> {a.out}\n")
    sys.stderr.write("  Note: 'ever-funded' includes dust and unrelated "
                     "collisions. Check received amount and date before "
                     "concluding anything.\n")


if __name__ == "__main__":
    main()
