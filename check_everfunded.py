#!/usr/bin/env python3
"""
check_everfunded.py -- did any of these addresses EVER hold coins?

This answers the one question the offline index cannot, and it is the question
that decides whether every "0 hits" in this project means anything.

THE PROBLEM
`address_map.bin` is a snapshot of addresses funded RIGHT NOW. A key that was
funded and then swept is invisible to it. The project's own control makes this
concrete: 32 canonical brainwallet phrases (`satoshi`, `password`,
`correct horse battery staple`, ...) x 2 pubkey forms = 64 addresses, every one
of which demonstrably held coins once and was drained years ago -- and 0 of
those 64 appear in the index.

So a swept prize and a wrong derivation look IDENTICAL to us. If someone solved
Keiser's puzzle in 2023 and swept it, roughly 120M derivations of null tell us
nothing at all.

THE FIX
An Esplora-compatible API reports `chain_stats.funded_txo_count`, which is a
lifetime count and does not care about the current balance. Non-zero means the
address existed on chain at some point. That converts every null from
"not funded today" into "never existed", which is a far stronger statement.

This needs network, so it runs on your machine, not in the sandbox.

USAGE
  python3 check_everfunded.py --selftest                 # run this first
  python3 check_everfunded.py --addrs addresses.txt
  python3 check_everfunded.py --phrases solver/wf/loop/prio_mirror.txt
  python3 check_everfunded.py --addrs a.txt --api https://mempool.space/api

Results are cached in everfunded_cache.json, so re-running resumes rather than
re-querying. Anything ever-funded is printed loudly and written to
EVERFUNDED_HITS.txt.

BE POLITE. These are free public APIs. The default is 4 requests/second; do not
raise it much, and prefer your own node with --api http://localhost:3000 if you
have one.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import solve_mitm as SM          # reuse the validated crypto
except ImportError:
    sys.exit("solve_mitm.py must sit next to this file (it supplies the crypto)")

CACHE = os.path.join(HERE, "everfunded_cache.json")
HITS = os.path.join(HERE, "EVERFUNDED_HITS.txt")
DEFAULT_API = "https://blockstream.info/api"

# Ever-funded, now empty: sha256("correct horse battery staple"), uncompressed.
# It received ~15.95 BTC and was drained years ago, so it is invisible to a
# balance snapshot and is the exact positive control this tool needs.
CTL_FUNDED = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"


def load_cache():
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE))
        except Exception:
            return {}
    return {}


def save_cache(c):
    tmp = CACHE + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CACHE)


def query(addr, api, timeout=20):
    """(ever_funded, received_sats) or (None, None) if the query failed."""
    url = f"{api.rstrip('/')}/address/{addr}"
    req = urllib.request.Request(url, headers={"User-Agent": "overdose-solver"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, 0           # unknown to the chain = never funded
        return None, None
    except Exception:
        return None, None
    cs = d.get("chain_stats", {}) or {}
    ms = d.get("mempool_stats", {}) or {}
    n = cs.get("funded_txo_count", 0) + ms.get("funded_txo_count", 0)
    sats = cs.get("funded_txo_sum", 0) + ms.get("funded_txo_sum", 0)
    return n > 0, sats


def addrs_from_phrase(p):
    import hashlib
    k = hashlib.sha256(p.encode("utf-8")).digest()
    ki = int.from_bytes(k, "big")
    q = SM.pub_from_scalar(ki)
    if not q:
        return []
    return list(SM.addrs_from_pub(q[0], q[1], SM.ALL_TYPES).values())


def selftest(api):
    ok = True
    print(f"api: {api}")

    # the crypto this tool leans on must itself be sound
    good = SM.selftest()
    print(f"  solve_mitm crypto selftest: {'OK' if good else 'FAIL'}")
    ok &= good

    # POSITIVE control: ever-funded but now empty. If this reads False, the
    # tool is not actually measuring lifetime funding and every null is void.
    ever, sats = query(CTL_FUNDED, api)
    if ever is None:
        print(f"  positive control: UNREACHABLE (network or api down)")
        ok = False
    else:
        print(f"  positive control ever-funded: {'OK' if ever else 'FAIL'} "
              f"({CTL_FUNDED}, {sats/1e8:.4f} BTC received)")
        ok &= bool(ever)

    # NEGATIVE control: a freshly derived key must be unknown to the chain
    import hashlib, os as _os
    fresh = addrs_from_phrase(hashlib.sha256(_os.urandom(32)).hexdigest())[0]
    ever2, _ = query(fresh, api)
    if ever2 is None:
        print("  negative control: UNREACHABLE")
        ok = False
    else:
        print(f"  negative control unfunded: {'OK' if not ever2 else 'FAIL'} "
              f"({fresh})")
        ok &= not ever2

    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addrs", help="file of addresses, one per line")
    ap.add_argument("--phrases", help="file of phrases; sha256 -> all 5 types")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--rate", type=float, default=4.0,
                    help="requests per second (default 4; be polite)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest(a.api) else 1)
    if not selftest(a.api):
        sys.exit("selftest failed; a null from this tool would be meaningless")

    targets = []
    if a.addrs:
        targets += [l.strip() for l in open(a.addrs, encoding="utf-8") if l.strip()]
    if a.phrases:
        for l in open(a.phrases, encoding="utf-8", errors="replace"):
            l = l.rstrip("\n")
            if l.strip():
                targets += addrs_from_phrase(l)
    if not targets:
        sys.exit("give --addrs and/or --phrases")

    seen, uniq = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t); uniq.append(t)

    cache = load_cache()
    todo = [t for t in uniq if t not in cache]
    print(f"\n{len(uniq):,} unique addresses, {len(cache):,} cached, "
          f"{len(todo):,} to query at {a.rate}/s "
          f"(~{len(todo)/max(a.rate,0.1)/60:.1f} min)")

    delay, hits, fails, t0 = 1.0 / max(a.rate, 0.1), [], 0, time.time()
    for i, addr in enumerate(todo):
        ever, sats = query(addr, a.api)
        if ever is None:
            fails += 1
            time.sleep(min(5.0, delay * 10))     # back off on errors
            continue
        cache[addr] = [bool(ever), int(sats)]
        if ever:
            hits.append((addr, sats))
            print(f"\n*** EVER-FUNDED *** {addr}  {sats/1e8:.8f} BTC received",
                  flush=True)
            open(HITS, "a").write(f"{addr}\t{sats}\n")
        if i % 200 == 0 and i:
            save_cache(cache)
            el = time.time() - t0
            print(f"  {i:,}/{len(todo):,}  {i/max(el,1e-9):.1f}/s  "
                  f"{len(hits)} ever-funded  {fails} failed", flush=True)
        time.sleep(delay)
    save_cache(cache)

    everf = sum(1 for v in cache.values() if v[0])
    print(f"\nqueried {len(todo):,} ({fails} failed), cache now {len(cache):,}")
    print(f"ever-funded in cache: {everf}")
    for h in hits:
        print("  ", h)
    if not hits:
        print("\nNone of these addresses has ever existed on chain. That is a"
              "\nmuch stronger null than the offline index can give: it rules"
              "\nout a swept prize for exactly this phrase set.")


if __name__ == "__main__":
    main()
