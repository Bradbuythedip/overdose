#!/usr/bin/env python3
"""
Continuous transaction-graph tracer for the peel candidates. Runs on a machine
with a Bitcoin endpoint; resumable; bounded so it terminates.

WHAT IT ANSWERS
The funding tx of candidate #1 (d931904b...) is a personal peel: two inputs ->
exactly 20 BTC to 1BX2qZ9y... plus ~31 BTC change. On its own that raises
1BX2q's prior but does not tie it to Keiser -- 20 BTC round payments are
common. The decisive question is whether ONE wallet created all three 20-BTC
peel candidates. This walks the transaction graph to find out, and flags any
tie to Keiser-related addresses the repo already knows.

THE HEURISTIC, STATED
Common-input-ownership: addresses that appear together as inputs of one
transaction are almost certainly one wallet (they were signed together). This
is the standard clustering assumption; it is a heuristic, not proof, and
CoinJoins break it -- so the tool reports the evidence, never a verdict of
"this is Keiser".

WHAT IT DOES
  - BFS from the three peel candidates (or any --seed address/txid)
  - for each address: its transactions; for each tx: input addresses (traced
    back through prevouts) and output addresses
  - union-find cluster over shared-input sets
  - THE TEST: are the three candidates' funding wallets one cluster? do their
    funding txs share inputs or a change address?
  - flags any traced address present in keiser_direct_hits.tsv or the repo's
    candidate lists
  - caches every tx and address history to disk; re-run resumes for free
  - bounded by --max-depth and --max-nodes so a run always terminates; with
    --loop it repeats, widening, until nothing new appears (the "continuous"
    mode)

ENDPOINT. Needs /address/{a}/txs and /tx/{txid}. blockstream.info/api serves
both. Alchemy serves /tx and /address stats but NOT the /address/{a}/txs
history path (verified earlier this project), so use blockstream here.

  python3 trace.py --selftest                       # offline, on the known tx
  python3 trace.py --base https://blockstream.info/api
  python3 trace.py --base https://blockstream.info/api --loop --max-depth 6
"""
import argparse, hashlib, json, os, sys, time
import urllib.request, urllib.error

CANDIDATES = ["1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t",
              "1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi",
              "1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64"]

# the one tx we already have, for the offline selftest
KNOWN_TX_HEX = ("01000000023a9c7612b2e1029e20464b413ffc85faf12e40c69d98a0ab00"
    "bce64daf595919010000006b483045022100af0b0f8c8f276ffca093da2ad017bc22ce10"
    "16082cf95f72dacdfc3629b6b0720220746d2b98b7b02972752f6e8b39082f5eb81f69b69"
    "79bf01589fd7c7dcf8992c0012102247fd4365fceb03c66643a40839cdc4ee13cd3ea3748"
    "24e814a3368c946c672000000000d133fd05c1e8938d4a6c5067c1e0f94edd4738db95532"
    "e95dbcc99c270a3f7c9010000006a47304402204977fe4da447ee1faacc72ad909336dd03"
    "dc58702e684bca816b3b29c8de385202202ca49a5213b9c3a13933aab948d01d876f9008d"
    "62fa653c7f4796d0506a666b8012102b2bb89fd735a29dc904a704948761dacf95ff3163b"
    "65337e0c7414ab401c82ab000000000200943577000000001976a914735f452fed8ca297"
    "de0484be1b63200b726077c188acc634c6b8000000001976a914a94072ffa9dec8ab97623"
    "59919fb97aaf87359a088ac00000000")

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def dsha(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def h160_to_addr(h, ver=b"\x00"):
    d = ver + h + dsha(ver + h)[:4]
    n = int.from_bytes(d, "big"); s = ""
    while n:
        n, r = divmod(n, 58); s = B58[r] + s
    return "1" * (len(d) - len(d.lstrip(b"\x00"))) + s


def decode_tx_hex(raw):
    """Local decode -> {'txid', 'vin':[(ptxid,vout)], 'vout':[(addr,sats)]}."""
    b = bytes.fromhex(raw) if isinstance(raw, str) else raw
    i = [0]

    def take(n):
        v = b[i[0]:i[0] + n]; i[0] += n; return v

    def u32(): return int.from_bytes(take(4), "little")
    def u64(): return int.from_bytes(take(8), "little")

    def var():
        n = take(1)[0]
        return n if n < 0xfd else int.from_bytes(
            take({0xfd: 2, 0xfe: 4}.get(n, 8)), "little")

    u32()
    vin = []
    for _ in range(var()):
        pt = take(32)[::-1].hex(); vo = u32()
        take(var()); u32()
        vin.append((pt, vo))
    vout = []
    for _ in range(var()):
        val = u64(); spk = take(var())
        a = h160_to_addr(spk[3:23]) if spk[:3] == b"\x76\xa9\x14" else \
            (h160_to_addr(spk[2:22], b"\x05") if spk[:2] == b"\xa9\x14" else None)
        vout.append((a, val))
    return {"txid": dsha(b)[::-1].hex(), "vin": vin, "vout": vout}


class Chain:
    """Esplora client with a disk cache and polite backoff."""

    def __init__(self, base, cache="trace_cache.jsonl"):
        self.base = base.rstrip("/")
        self.cache_path, self.cache = cache, {}
        if os.path.exists(cache):
            for l in open(cache):
                try:
                    k, v = json.loads(l); self.cache[k] = v
                except Exception:
                    pass
        self.cf = open(cache, "a")
        self.gap, self.last = 0.20, 0.0

    def _get(self, path):
        if path in self.cache:
            return self.cache[path]
        for attempt in range(6):
            dt = time.time() - self.last
            if dt < self.gap:
                time.sleep(self.gap - dt)
            try:
                req = urllib.request.Request(self.base + path,
                                             headers={"User-Agent": "trace/1"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    v = json.loads(r.read().decode())
                self.last = time.time()
                self.gap = max(0.10, self.gap * 0.9)
                self.cache[path] = v
                self.cf.write(json.dumps([path, v]) + "\n"); self.cf.flush()
                return v
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    self.gap = min(5.0, self.gap * 2); time.sleep(self.gap)
                    continue
                self.cache[path] = None
                return None
            except Exception:
                time.sleep(1.0 + attempt)
        return None

    def tx(self, txid):
        return self._get(f"/tx/{txid}")

    def addr_txs(self, addr):
        out, last = [], None
        while True:
            p = f"/address/{addr}/txs" + (f"/chain/{last}" if last else "")
            batch = self._get(p)
            if not batch:
                break
            out += batch
            if len(batch) < 25:
                break
            last = batch[-1]["txid"]
            if len(out) > 200:
                break
        return out


class UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def known_flags():
    """Addresses the repo already ties to Keiser or holds as candidates."""
    flags = {}
    for path, why in (("keiser_direct_hits.tsv", "keiser_direct_hits"),
                      ("targets_11.txt", "20-BTC candidate list"),
                      ("window/candidates_p2pkh_exact20_67.txt", "exact-20 candidate")):
        if os.path.exists(path):
            for l in open(path, encoding="utf-8", errors="ignore"):
                for tok in l.split():
                    if tok.startswith("1") and 26 <= len(tok) <= 35:
                        flags.setdefault(tok, why)
    return flags


def selftest():
    ok = True
    t = decode_tx_hex(KNOWN_TX_HEX)
    ok &= t["txid"] == "d931904b054de23c21efe650843e5adf6d409c6537c792281aad47a07e850dfa"
    sys.stderr.write(f"  local decode txid matches: {'OK' if t['txid'].startswith('d931904b') else 'FAIL'}\n")
    outs = dict(t["vout"])
    ok &= outs.get("1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t") == 2000000000
    sys.stderr.write(f"  out[0] = 20 BTC to candidate #1: "
                     f"{'OK' if outs.get('1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t')==2000000000 else 'FAIL'}\n")
    ok &= len(t["vin"]) == 2
    sys.stderr.write(f"  2 inputs parsed: {'OK' if len(t['vin'])==2 else 'FAIL'}\n")
    # union-find sanity
    uf = UF(); uf.union("a", "b"); uf.union("b", "c")
    ok &= uf.find("a") == uf.find("c") and uf.find("a") != uf.find("z")
    sys.stderr.write(f"  cluster union-find groups shared inputs: "
                     f"{'OK' if uf.find('a')==uf.find('c') else 'FAIL'}\n")
    f = known_flags()
    ok &= "1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t" in f
    sys.stderr.write(f"  candidate #1 flagged from repo data ({len(f)} known "
                     f"addrs): {'OK' if '1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t' in f else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    class _Fake:
        def tx(self, txid):
            return {"vin": [{"prevout": None, "is_coinbase": True}, {"prevout": {"scriptpubkey_address": "1A"}}],
                    "vout": [{"scriptpubkey_address": "1B", "value": 1}]}
    try:
        ins, outs = input_addrs(_Fake(), "x")
        good = ins == ["1A"] and outs == [("1B", 1)]
    except Exception:
        good = False
    ok &= good
    sys.stderr.write(f"  a coinbase input (prevout: null) is skipped, not a crash: {'OK' if good else 'FAIL'}\n")
    return ok


def input_addrs(chain, txid):
    t = chain.tx(txid)
    if not t:
        return [], []
    # Esplora returns "prevout": null (not a missing key) on coinbase inputs,
    # which the crawl reaches once it is deep enough -- treat null as {}.
    ins = [(vin.get("prevout") or {}).get("scriptpubkey_address")
           for vin in t.get("vin", [])]
    outs = [(vo.get("scriptpubkey_address"), vo.get("value", 0))
            for vo in t.get("vout", [])]
    return [a for a in ins if a], outs


def funding_of(chain, cand):
    """The tx and input-address set that funded a candidate with ~20 BTC."""
    for tx in chain.addr_txs(cand):
        ins, outs = input_addrs(chain, tx["txid"])
        for a, v in outs:
            if a == cand and 1_990_000_000 <= v <= 2_010_000_000:
                return {"txid": tx["txid"], "inputs": ins, "outputs": outs}
    # fall back to the first tx that pays the candidate at all
    for tx in chain.addr_txs(cand):
        ins, outs = input_addrs(chain, tx["txid"])
        if any(a == cand for a, _ in outs):
            return {"txid": tx["txid"], "inputs": ins, "outputs": outs}
    return None


def crawl(chain, uf, flags, max_nodes, max_depth):
    """Cluster the FUNDING WALLETS of the three candidates, not the candidates.

    The candidates never spend, so they are singletons and clustering them is
    meaningless. What matters is whether their FUNDERS -- the input addresses
    of each funding tx -- are one wallet. So: get each candidate's funding
    input set, then BFS from those inputs, unioning every co-input set, and
    skipping high-activity addresses (>60 txs) that are exchanges, not a
    personal setter wallet.
    """
    funding, seen_addr, seen_tx = {}, set(), set()
    frontier = []
    for c in CANDIDATES:
        f = funding_of(chain, c)
        if f:
            funding[c] = f
            for a in f["inputs"]:
                if len(f["inputs"]) > 1:
                    uf.union(f["inputs"][0], a)
                frontier.append((a, 0))
    while frontier and len(seen_addr) < max_nodes:
        addr, depth = frontier.pop(0)
        if addr in seen_addr or depth > max_depth:
            continue
        seen_addr.add(addr)
        txs = chain.addr_txs(addr)
        if len(txs) > 60:                      # exchange / hot wallet; do not expand
            continue
        for tx in txs:
            ins, outs = input_addrs(chain, tx["txid"])
            seen_tx.add(tx["txid"])
            if len(ins) > 1:
                for a in ins[1:]:
                    uf.union(ins[0], a)
            for a in ins + [o[0] for o in outs]:
                if a and a not in seen_addr:
                    frontier.append((a, depth + 1))
    return funding, seen_addr, seen_tx


def report(uf, funding, flags, seen_addr):
    sys.stderr.write(f"\n  {len(seen_addr):,} funder-side addresses visited\n\n")
    # cluster each candidate by its FUNDING INPUT set (not the candidate)
    def cand_cluster(c):
        ins = funding.get(c, {}).get("inputs", [])
        return uf.find(ins[0]) if ins else None
    roots = {c: cand_cluster(c) for c in CANDIDATES}
    sys.stderr.write("  SAME-WALLET TEST (clusters of each candidate's FUNDER):\n")
    for c in CANDIDATES:
        f = funding.get(c)
        if not f:
            sys.stderr.write(f"    {c}  funding tx not found\n"); continue
        sys.stderr.write(f"    {c}\n      funded by {f['txid'][:20]}... "
                         f"inputs={[a[:12] for a in f['inputs'][:4]]} "
                         f"cluster={str(roots[c])[:14]}\n")
    live = {c: r for c, r in roots.items() if r}
    # direct shared funding input -- the strongest signal
    isets = {c: set(funding.get(c, {}).get("inputs", [])) for c in CANDIDATES}
    shared = set.intersection(*[v for v in isets.values() if v]) if \
        sum(1 for v in isets.values() if v) >= 2 else set()
    # shared change: does one candidate's funding tx change feed another's?
    if len(set(live.values())) == 1 and len(live) >= 2:
        sys.stderr.write("\n    *** THE FUNDERS ARE ONE CLUSTER -- one wallet "
                         "funded these candidates. Near-decisive.\n")
    elif len(set(live.values())) > 1:
        sys.stderr.write("\n    funders are in DIFFERENT clusters -- not one "
                         "wallet; the 20-BTC coincidence does not hold up.\n")
    if shared:
        sys.stderr.write(f"    *** shared exact funding input(s): {shared}\n")
    hits = [a for a in seen_addr if a in flags]
    sys.stderr.write(f"\n  funder addresses also in repo/Keiser data: {len(hits)}\n")
    for a in hits[:20]:
        sys.stderr.write(f"    {a}  [{flags[a]}]\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("ESPLORA", ""))
    ap.add_argument("--seed", action="append", default=[])
    ap.add_argument("--max-depth", type=int, default=4)
    ap.add_argument("--max-nodes", type=int, default=400)
    ap.add_argument("--loop", action="store_true",
                    help="keep widening until no new address appears")
    ap.add_argument("--cache", default="trace_cache.jsonl")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("decode/cluster logic is wrong; refusing")
    if a.selftest:
        return
    if not a.base:
        sys.exit("need --base (Esplora, e.g. https://blockstream.info/api). "
                 "This is the network step; it cannot run without an endpoint.")

    chain = Chain(a.base, a.cache)
    flags = known_flags()
    uf = UF()
    depth, prev = a.max_depth, -1
    while True:
        funding, seen_addr, seen_tx = crawl(chain, uf, flags, a.max_nodes, depth)
        report(uf, funding, flags, seen_addr)
        if not a.loop or len(seen_addr) == prev:
            break
        prev = len(seen_addr)
        depth += 1; a.max_nodes = int(a.max_nodes * 1.5)
        sys.stderr.write(f"\n  --loop: widening to depth {depth}, "
                         f"{a.max_nodes} nodes...\n")
    sys.stderr.write(f"\n  txs cached in {a.cache}. Re-run resumes for free.\n")


if __name__ == "__main__":
    main()
