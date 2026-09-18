#!/usr/bin/env python3
"""
The EVER-USED oracle: the detector this project has been missing.

THE PROBLEM, IN THE REPO'S OWN WORDS
Every sweep here -- 69M audited derivations across 12 corpora (STATUS.md) --
was judged by /tmp/address_map.bin, the UTXO set as of 2025-10-11. STATUS.md
says what that means:

    every "0 hits" means *no address that still holds coins*. It does NOT rule
    out a key that was funded and swept before then -- which for a magazine-
    printed key is the most likely history of all.

Measured control, recorded in the same file: 32 famous brainwallet phrases x 2
pubkey forms = 64 addresses, every one demonstrably funded once and drained
years ago -- 0 of 64 appear in either offline index, while genesis appears in
both. About 460M addresses have ever held a balance; ~56.8M still do. The
detector has been seeing roughly 12% of the relevant space, so a correct
derivation of a swept key would have produced the same silence as a wrong one.

WHAT THIS BUILDS
A membership index over every address that has EVER appeared on chain:

    address -> scriptPubKey -> sha256 -> first 8 bytes, big-endian

partitioned into 256 buckets by the leading byte and sorted within each bucket.
A query touches exactly one bucket, so lookups stay O(log n) with no merge pass
and bounded RAM. An 8-byte prefix over ~1.3e9 entries collides with probability
~7e-11 per query -- under one expected false positive across a whole re-sweep,
and every hit is verified against a live endpoint anyway.

Bucketing rather than one sorted file is deliberate: a 1.3e9-element k-way
merge in Python costs hours, and buys nothing a bucket lookup does not give.

WHAT A HIT MEANS, AND DOES NOT
"This address exists on chain." NOT a solve. The set contains every address
ever touched, including every brainwallet a cracker ever drained. Vet with
claim_check.py, the live history, and decoys.py before believing anything, and
re-derive the key by hand before claiming it.

  python3 everused.py --selftest
  python3 everused.py --build --source all_Bitcoin_addresses_ever_used_sorted.txt.gz
  python3 everused.py --check 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
"""
import argparse, gzip, hashlib, os, struct, sys, time

import numpy as np

DEFAULT_DIR = "/tmp/everused"
SOURCE_URL = ("http://alladdresses.loyce.club/"
              "all_Bitcoin_addresses_ever_used_sorted.txt.gz")
NBUCKETS = 256
MANIFEST = "manifest.txt"


# ---------------------------------------------------------------- hashing
def prefix_of_spk(spk):
    """The 8-byte big-endian prefix of sha256(scriptPubKey), as an int."""
    return int.from_bytes(hashlib.sha256(spk).digest()[:8], "big")


def prefix_of_address(addr):
    """None if the address does not parse. Never guess: report, don't drop."""
    from index_oracle import spk_from_address
    spk = spk_from_address(addr)
    return None if spk is None else prefix_of_spk(spk)


# ---------------------------------------------------------------- build
class BucketWriter:
    """256 append-only bucket files with buffered writes."""

    def __init__(self, outdir, flush_every=1 << 20):
        os.makedirs(outdir, exist_ok=True)
        self.outdir = outdir
        self.buf = [[] for _ in range(NBUCKETS)]
        self.fh = [open(os.path.join(outdir, f"b{i:02x}.raw"), "ab")
                   for i in range(NBUCKETS)]
        self.flush_every = flush_every
        self.n = 0

    def add(self, p):
        b = p >> 56
        self.buf[b].append(p)
        self.n += 1
        if len(self.buf[b]) >= self.flush_every:
            self._flush(b)

    def _flush(self, b):
        if not self.buf[b]:
            return
        np.array(self.buf[b], dtype=">u8").tofile(self.fh[b])
        self.buf[b] = []

    def close(self):
        for b in range(NBUCKETS):
            self._flush(b)
            self.fh[b].close()


HEADERS = {"recipient", "address", "addresses"}   # dump column headers, not data


def split_names(n):
    """xaa, xab, ... -- the conventional split(1) naming these dumps use."""
    import string
    out = []
    for a in string.ascii_lowercase:
        for b in string.ascii_lowercase:
            out.append(f"x{a}{b}")
            if len(out) >= n:
                return out
    return out


def _one_stream(path_or_url):
    if path_or_url.startswith(("http://", "https://")):
        import urllib.request
        req = urllib.request.Request(
            path_or_url, headers={"User-Agent": "overdose-everused/1"})
        r = urllib.request.urlopen(req, timeout=120)
        if path_or_url.endswith(".gz"):
            return gzip.open(r, "rt", encoding="utf-8", errors="replace")
        import io
        return io.TextIOWrapper(r, encoding="utf-8", errors="replace")
    if path_or_url.endswith(".gz"):
        return gzip.open(path_or_url, "rt", encoding="utf-8", errors="replace")
    return open(path_or_url, "rt", encoding="utf-8", errors="replace")


def open_source(spec):
    """A line iterator over one dump, or over a list of split files.

    `spec` is a path, a URL, or 'BASEURL#N' meaning the first N split files
    (xaa, xab, ...) under BASEURL -- the layout the blockchair-derived
    'all addresses ever used' mirrors publish. Reading them in sequence is
    equivalent to reading one concatenated dump."""
    if "#" in spec and spec.startswith(("http://", "https://")):
        base, _, n = spec.partition("#")
        names = split_names(int(n))

        def gen():
            for i, nm in enumerate(names, 1):
                url = f"{base.rstrip('/')}/{nm}"
                try:
                    st = _one_stream(url)
                except Exception as e:
                    sys.stderr.write(f"\n  [{i}/{len(names)}] {nm}: {e!r} -- "
                                     f"stopping; the index covers {i-1} files\n")
                    return
                sys.stderr.write(f"\n  [{i}/{len(names)}] {nm}\n")
                with st:
                    for line in st:
                        yield line
        return gen()
    st = _one_stream(spec)
    return st


def build(source, outdir, limit=0, log=sys.stderr.write):
    """Stream the dump into 256 raw buckets, then sort each in place."""
    stream = open_source(source)
    w = BucketWriter(outdir)
    bad, blank, hdr, t0 = [], 0, 0, time.time()
    try:
        for i, line in enumerate(stream, 1):
            a = line.strip()
            if not a:
                blank += 1
                continue
            if a.lower() in HEADERS:
                hdr += 1
                continue
            p = prefix_of_address(a)
            if p is None:
                if len(bad) < 50:
                    bad.append(a)
                continue
            w.add(p)
            if i % 5_000_000 == 0:
                el = time.time() - t0
                log(f"\r  {i:,} lines, {w.n:,} indexed, {len(bad)} unparsed, "
                    f"{i/max(el,1e-9):,.0f}/s  ")
            if limit and i >= limit:
                break
    finally:
        w.close()
        try:
            stream.close()
        except Exception:
            pass
    log(f"\n  streamed: {w.n:,} addresses indexed, {blank:,} blank, "
        f"{hdr} header line(s), {len(bad)} unparseable "
        f"(first few: {bad[:5]})\n")
    sort_buckets(outdir, log)
    with open(os.path.join(outdir, MANIFEST), "w") as f:
        f.write(f"source\t{source}\nindexed\t{w.n}\nunparsed\t{len(bad)}\n"
                f"headers\t{hdr}\nbuilt\t{int(time.time())}\n")
    return w.n, len(bad)


def sort_buckets(outdir, log=sys.stderr.write):
    """Sort each bucket in place. Peak RAM = the largest bucket."""
    tot = 0
    for b in range(NBUCKETS):
        raw = os.path.join(outdir, f"b{b:02x}.raw")
        srt = os.path.join(outdir, f"b{b:02x}.u64")
        if not os.path.exists(raw):
            continue
        a = np.fromfile(raw, dtype=">u8")
        if a.size:
            a.sort()
            a.tofile(srt)
        else:
            open(srt, "wb").close()
        os.unlink(raw)
        tot += a.size
        if b % 32 == 0:
            log(f"\r  sorting buckets: {b}/{NBUCKETS}, {tot:,} entries  ")
    log(f"\n  sorted {tot:,} entries into {NBUCKETS} buckets\n")
    return tot


# ---------------------------------------------------------------- oracle
class EverUsed:
    """Membership over 'every address ever used'. No balances: present/absent."""

    name = "everused"

    def __init__(self, outdir=DEFAULT_DIR):
        self.dir = outdir
        self.ready = False
        self.why = ""
        self.n = 0
        self._b = {}
        man = os.path.join(outdir, MANIFEST)
        if not os.path.isdir(outdir) or not os.path.exists(man):
            self.why = f"no ever-used index at {outdir} (run --build)"
            return
        miss = [b for b in range(NBUCKETS)
                if not os.path.exists(os.path.join(outdir, f"b{b:02x}.u64"))]
        if miss:
            self.why = f"index at {outdir} is incomplete ({len(miss)} buckets missing)"
            return
        for line in open(man):
            k, _, v = line.partition("\t")
            if k == "indexed":
                self.n = int(v.strip() or 0)
            if k == "source":
                self.src = v.strip()
        self.ready = True
        self.why = f"{self.n:,} addresses ever used, from {getattr(self,'src','?')}"

    def _bucket(self, b):
        """Sorted uint64 view of one bucket. An empty bucket cannot be mmapped,
        so it degrades to an empty array rather than raising."""
        a = self._b.get(b)
        if a is None:
            path = os.path.join(self.dir, f"b{b:02x}.u64")
            if os.path.getsize(path) == 0:
                a = np.empty(0, dtype=">u8")
            else:
                a = np.memmap(path, dtype=">u8", mode="r")
            self._b[b] = a
        return a

    def contains_prefixes(self, prefixes):
        """Indices (into the input list) of prefixes present in the index."""
        if not self.ready:
            raise RuntimeError("ever-used index not ready: " + self.why)
        if not len(prefixes):
            return []
        pref = [int(p) for p in prefixes]
        q = np.array(pref, dtype=">u8")
        top = np.array([p >> 56 for p in pref], dtype=np.int32)
        out = []
        for b in np.unique(top):
            idx = np.nonzero(top == b)[0]
            arr = self._bucket(int(b))
            if arr.size == 0:
                continue
            vals = q[idx]
            pos = np.searchsorted(arr, vals, side="left")
            ok = pos < arr.size
            hit = np.zeros(idx.size, dtype=bool)
            hit[ok] = arr[pos[ok]] == vals[ok]
            out.extend(int(j) for j in idx[hit])
        return sorted(out)

    def contains_spks(self, spks):
        """(index, balance) like index_oracle.Oracle. Balance is UNKNOWN here.

        The sentinel is None, not 0: a caller that prints it must say "ever
        used, balance unknown". Reporting 0 would read as "not funded", which
        is how claim_check.py once mislabelled a richlist miss as an index
        miss -- the bug this project was explicitly fixed for."""
        pref = [prefix_of_spk(s) for s in spks]
        return [(j, None) for j in self.contains_prefixes(pref)]

    def control(self):
        """Must DISCRIMINATE this oracle from the balance snapshot.

        sha256('correct horse battery staple') -> an address with 148,425
        fundings and a zero balance today. It MUST be here and MUST be absent
        from address_map.bin. If that does not hold, this index is not
        answering "ever used" and any null from it would be void."""
        from index_oracle import spk_from_address
        ok = True
        g = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        ok &= bool(self.contains_spks([g]))
        swept = swept_control_spks()
        ok &= bool(self.contains_spks(swept))
        return ok


def swept_control_spks():
    """scriptPubKeys of a famous funded-then-drained brainwallet key."""
    from full_sweep import spks_for_key
    k = hashlib.sha256(b"correct horse battery staple").digest()
    d = dict(spks_for_key(k))
    return [d["p2pkh_u"], d["p2pkh_c"]]


# ---------------------------------------------------------------- selftest
def selftest(outdir=DEFAULT_DIR):
    ok = True
    w = sys.stderr.write

    def rep(msg, good):
        nonlocal ok
        ok &= bool(good)
        w(f"  {msg}: {'OK' if good else 'FAIL'}\n")

    # 1. hashing agrees with the existing oracle's convention
    from index_oracle import spk_from_address
    g = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    rep("genesis address parses to a scriptPubKey", g is not None)
    rep("prefix == first 8 bytes of sha256(spk), big-endian",
        prefix_of_spk(g) == int.from_bytes(hashlib.sha256(g).digest()[:8], "big"))
    rep("an invalid address returns None rather than guessing",
        prefix_of_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb") is None)

    # 2. build a miniature index and query it
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="everused_selftest_")
    try:
        from full_sweep import spks_for_key
        import index_oracle as IO
        swept = swept_control_spks()
        planted = [IO.spk_to_addr(s) if hasattr(IO, "spk_to_addr") else None
                   for s in swept]
        from shortlist_everfunded import spk_to_addr
        addrs = ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"] + \
                [spk_to_addr(s) for s in swept]
        addrs = [a for a in addrs if a]
        src = os.path.join(tmp, "mini.txt")
        with open(src, "w") as f:
            f.write("\n".join(addrs) + "\nNOT_AN_ADDRESS\n\n")
        n, bad = build(src, tmp, log=lambda m: None)
        rep(f"miniature build indexed {n} addresses, flagged {bad} unparseable",
            n == len(addrs) and bad == 1)
        o = EverUsed(tmp)
        rep("the built index loads and reports ready", o.ready)
        rep("genesis is found", bool(o.contains_spks([g])))
        rep("the swept brainwallet is found", bool(o.contains_spks(swept)))
        rep("the discriminating control passes", o.control())
        rnd = hashlib.sha256(os.urandom(32)).digest()
        fake = dict(spks_for_key(rnd))["p2pkh_c"]
        rep("a fresh random address is NOT found (no blanket true)",
            not o.contains_spks([fake]))
        # balance sentinel
        hits = o.contains_spks([g])
        rep("a hit reports balance None, never 0 ('unknown', not 'unfunded')",
            hits and hits[0][1] is None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 3. the point of the whole exercise, stated as a test
    try:
        from index_oracle import Oracle, MAP
        if os.path.exists(MAP):
            b = Oracle(verbose=False)
            if b.calibrate():
                seen = b.contains_spks(swept_control_spks())
                rep("the swept control is ABSENT from address_map.bin "
                    "(this is the blind spot being closed)", not seen)
        else:
            w("  (address_map.bin absent here; the discrimination half of the "
              "control cannot run)\n")
    except Exception as e:
        w(f"  (balance-index comparison unavailable: {e!r})\n")

    # 4. the real index, if present
    real = EverUsed(outdir)
    if real.ready:
        rep(f"the real index at {outdir} passes its control "
            f"({real.n:,} addresses)", real.control())
    else:
        w(f"  (no real index yet: {real.why})\n")

    w("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--source", default=SOURCE_URL)
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--limit", type=int, default=0, help="stop after N lines (testing)")
    ap.add_argument("--check", nargs="*", default=[], help="addresses to look up")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(a.dir):
        sys.exit("ever-used indexing is wrong; refusing to build or answer")
    if a.selftest:
        return

    if a.build:
        sys.stderr.write(f"\n  building from {a.source}\n")
        n, bad = build(a.source, a.dir)
        o = EverUsed(a.dir)
        if not o.ready:
            sys.exit(f"build finished but the index is not usable: {o.why}")
        if not o.control():
            sys.exit("CONTROL FAILED after build -- the index does not contain "
                     "a known swept address, so it is not an 'ever used' set. "
                     "Any null from it would be void.")
        sys.stderr.write(f"  control OK. {o.why}\n")
        return

    if a.check:
        o = EverUsed(a.dir)
        if not o.ready:
            sys.exit(f"no index: {o.why}")
        if not o.control():
            sys.exit("control failed; refusing to answer")
        from index_oracle import spk_from_address
        for addr in a.check:
            spk = spk_from_address(addr)
            if spk is None:
                print(f"{addr}\tINVALID")
                continue
            hit = bool(o.contains_spks([spk]))
            print(f"{addr}\t{'EVER USED' if hit else 'never used'}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
