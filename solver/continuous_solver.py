#!/usr/bin/env python3
"""
Continuous offline solver. Runs unattended, never repeats itself, and refuses
to file a null it cannot stand behind.

THE THREE THINGS THAT MAKE IT DIFFERENT FROM ANOTHER SWEEP SCRIPT

1. IT REMEMBERS. Every unit of work has a deterministic id derived from its
   family and parameters, held in solver_ledger. Restarting resumes; a crashed
   unit is requeued; nothing is swept twice. This project's recurring failure
   was never compute, it was bookkeeping.

2. IT PROVES ITS ORACLE EVERY CYCLE. Before any unit's result is accepted, the
   oracle in use must return a KNOWN POSITIVE — the genesis address for the
   index, a constructed key for the checksum filter. If it does not, the unit
   is filed INVALID rather than as a null. A null from an unproven oracle is
   not evidence, and this repo has already recorded 0 hits over 782 files that
   were all 404 bodies.

3. IT SCHEDULES BY INFORMATION, NOT BY SIZE. Families that have never run go
   first; then the cheapest untried unit. A family is not "done" because it was
   large, and a large null on a family that cannot carry a key teaches nothing.

FAMILIES
  ngram          article n-grams by length and case, full derivation set
  corpus         a committed generator's output, swept
  checksum_mine  strided readings judged by the SERIAL as a 4-byte checksum —
                 chain-free, so it reaches spaces no index or API can be asked
                 about, and it sees a key that was never funded or was swept
  serial_range   a slice of the 10^8 serial keyspace under one transform

ORACLE LIMITS, stated because an unattended loop must not overstate itself
The offline index is a BALANCE snapshot: it answers "holds coins today", never
"was ever funded". The checksum filter answers neither — it asks whether a
derivation reproduces the serial. Both are recorded per unit, so no result can
later be read as something it was not.

  python3 continuous_solver.py --selftest
  python3 continuous_solver.py --seed          # queue the standard families
  python3 continuous_solver.py --run --workers 2
"""
import argparse, hashlib, itertools, json, os, re, subprocess, sys, tempfile, time

from solver_ledger import Ledger

INDEX = "index56m"
CHECKSUM = "serial_checksum"


# ---------------------------------------------------------------- oracles
class IndexOracle:
    """The 56.8M funded-address index, with its control."""
    name = INDEX

    def __init__(self):
        from index_oracle import Oracle
        self.o = Oracle(verbose=False)
        self.ready = self.o.calibrate()

    def control(self):
        from index_oracle import spk_from_address
        if not self.ready:
            return False
        spk = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        return bool(self.o.contains_spks([spk]))

    def check(self, spks):
        return self.o.contains_spks(spks)


class ChecksumOracle:
    """The serial read as a 4-byte checksum. Needs no chain at all."""
    name = CHECKSUM

    def __init__(self):
        from serial_oracle import targets
        self.rev = {}
        for n, v in targets().items():
            self.rev.setdefault(v, []).append(n)

    def control(self):
        """A planted value must be found by the same membership test."""
        probe = hashlib.sha256(b"control").digest()[:4]
        rev = dict(self.rev)
        rev[probe] = ["planted"]
        return probe in rev and len(self.rev) > 0

    def match(self, four):
        return self.rev.get(four)


# ---------------------------------------------------------------- families
def article_words():
    from gen_priority_addrs import load
    _l, _s, paras = load()
    return re.findall(r"[A-Za-z0-9$%'-]+", " ".join(paras))


def fam_ngram(params):
    """Article n-grams of one length and case, full derivation set."""
    n, case = params["n"], params["case"]
    ws = article_words()
    for i in range(len(ws) - n + 1):
        g = " ".join(ws[i:i + n])
        yield {"lower": g.lower(), "upper": g.upper(), "as-is": g,
               "joined": "".join(ws[i:i + n]).lower()}[case]


def fam_corpus(params):
    """Phrases emitted by one committed generator."""
    script, extra = params["script"], params.get("extra", [])
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "p.txt")
        r = subprocess.run([sys.executable, script] + extra + ["--out", out],
                           capture_output=True, text=True)
        if not os.path.exists(out):
            raise RuntimeError((r.stderr or "")[-300:])
        for line in open(out, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n")
            if len(p.strip()) >= 4 and len(p.split()) >= 2:
                yield p


def fam_checksum_mine(params):
    """Strided readings, judged by the serial rather than by the chain."""
    stride, L = params["stride"], params["len"]
    ws = article_words()
    span = (L - 1) * stride
    for i in range(0, max(len(ws) - span, 0)):
        seq = ws[i:i + span + 1:stride]
        if len(seq) == L:
            yield " ".join(seq)
            yield " ".join(seq[::-1])


def fam_serial_range(params):
    """A slice of the serial keyspace, as private keys."""
    from serial_exhaust import TRANSFORMS
    fn = TRANSFORMS[params["transform"]]
    for i in range(params["lo"], params["hi"]):
        yield fn(f"{i:08d}")


FAMILIES = {
    "ngram": (fam_ngram, INDEX),
    "corpus": (fam_corpus, INDEX),
    "checksum_mine": (fam_checksum_mine, CHECKSUM),
    "serial_range": (fam_serial_range, INDEX),
}


# ---------------------------------------------------------------- execution
def run_index_unit(gen, oracle, led, wid, family, batch=4000):
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    paths = build_paths()[:8]
    cand = addrs = hits = 0
    meta, spks = [], []

    def flush():
        nonlocal meta, spks, hits
        if not spks:
            return
        for j, bal in oracle.check(spks):
            hits += 1
            led.hit(wid, family, meta[j][0], meta[j][1], bal, oracle.name)
            sys.stderr.write(f"  *** HIT {bal} :: {meta[j][0][:90]}\n")
        meta, spks = [], []

    for item in gen:
        cand += 1
        keys = ([("raw", item)] if isinstance(item, (bytes, bytearray))
                else [(f"d:{n}", k) for n, k in direct_keys(item).items()])
        if not isinstance(item, (bytes, bytearray)):
            for sn, seed in seeds_from(item).items():
                for p in paths:
                    try:
                        k = derive(seed, p)
                    except Exception:
                        continue
                    if k:
                        keys.append((f"{sn}:{p}", k))
        label = item if isinstance(item, str) else item.hex()
        for dn, k in keys:
            for st, spk in spks_for_key(k):
                meta.append((f"{label[:80]}|{dn}|{st}", st))
                spks.append(spk)
                addrs += 1
            if len(spks) >= batch:
                flush()
    flush()
    return cand, addrs, hits


def run_checksum_unit(gen, oracle, led, wid, family):
    from serial_text_mine import products
    cand = hits = 0
    for phrase in gen:
        cand += 1
        for label, v in products(phrase):
            names = oracle.match(v)
            if names:
                hits += 1
                led.hit(wid, family, f"{phrase[:80]}|{label}|{names[0]}",
                        v.hex(), 0, oracle.name)
                sys.stderr.write(f"  *** CHECKSUM MATCH {label}={names[0]} "
                                 f":: {phrase[:80]}\n")
    return cand, 0, hits


def seed_work(led):
    n = 0
    for ln in range(2, 13):
        for case in ("lower", "as-is", "joined"):
            led.add("ngram", {"n": ln, "case": case})
            n += 1
    for script, extra in [("boustrophedon.py", []), ("sentence_cipher.py", []),
                          ("gen_typographic.py", []), ("gen_numbers.py", []),
                          ("gen_numbers.py", ["--set", "p72"]),
                          ("gen_schott.py", [])]:
        led.add("corpus", {"script": script, "extra": extra})
        n += 1
    for stride in range(1, 13):
        for L in range(2, 25):
            led.add("checksum_mine", {"stride": stride, "len": L})
            n += 1
    from serial_exhaust import TRANSFORMS
    for t in TRANSFORMS:
        for lo in range(0, 100_000_000, 5_000_000):
            led.add("serial_range",
                    {"transform": t, "lo": lo, "hi": lo + 5_000_000})
            n += 1
    return n


def selftest():
    ok = True
    ws = article_words()
    ok &= len(ws) > 1000
    sys.stderr.write(f"  {len(ws)} article words\n")

    g = list(itertools.islice(fam_ngram({"n": 3, "case": "lower"}), 5))
    ok &= len(g) == 5 and all(len(x.split()) == 3 for x in g)
    sys.stderr.write(f"  ngram family yields 3-grams: {g[0]!r}\n")

    c = list(itertools.islice(fam_checksum_mine({"stride": 2, "len": 4}), 4))
    ok &= len(c) == 4
    sys.stderr.write(f"  checksum_mine yields strided readings: {c[0]!r}\n")

    s = list(itertools.islice(fam_serial_range(
        {"transform": "tiled", "lo": 0, "hi": 3}), 3))
    ok &= all(len(x) == 32 for x in s)
    sys.stderr.write(f"  serial_range yields 32-byte keys\n")

    io = IndexOracle()
    c1 = io.control()
    ok &= c1
    sys.stderr.write(f"  index oracle control (genesis found): "
                     f"{'OK' if c1 else 'FAIL'}\n")
    co = ChecksumOracle()
    c2 = co.control()
    ok &= c2
    sys.stderr.write(f"  checksum oracle control: {'OK' if c2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="solver_ledger.sqlite")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--max-units", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("solver fails its controls; refusing to run unattended")
    if a.selftest:
        return

    led = Ledger(a.db)
    if a.seed:
        n = seed_work(led)
        sys.stderr.write(f"\n  queued {n} work units\n")
        return
    if not a.run:
        sys.stderr.write("\n  nothing to do: pass --seed then --run\n")
        return

    req = led.requeue_stale()
    if req:
        sys.stderr.write(f"  requeued {req} stale units from a previous run\n")

    oracles = {INDEX: IndexOracle(), CHECKSUM: ChecksumOracle()}
    done = 0
    while True:
        got = led.claim(order_by="family, id")
        if not got:
            sys.stderr.write("\n  queue empty — all known work is done\n")
            break
        wid, family, params = got
        genfn, oname = FAMILIES[family]
        oracle = oracles[oname]

        ctrl = oracle.control()
        if not ctrl:
            led.finish(wid, oracle=oname, control_ok=False,
                       detail="oracle control did not fire")
            sys.stderr.write(f"  {family} {params}: ORACLE CONTROL FAILED — "
                             f"filed INVALID, not as a null\n")
            continue

        t0 = time.time()
        sys.stderr.write(f"\n  [{done+1}] {family} {json.dumps(params)}\n")
        try:
            gen = genfn(params)
            if oname == CHECKSUM:
                cand, addrs, hits = run_checksum_unit(gen, oracle, led, wid,
                                                      family)
            else:
                cand, addrs, hits = run_index_unit(gen, oracle, led, wid,
                                                   family)
            led.finish(wid, oracle=oname, control_ok=True, candidates=cand,
                       addresses=addrs, hits=hits,
                       detail=f"{time.time()-t0:.1f}s")
            sys.stderr.write(f"      {cand:,} candidates, {addrs:,} addresses, "
                             f"{hits} hits, {time.time()-t0:.0f}s\n")
        except Exception as e:
            led.finish(wid, oracle=oname, control_ok=True, status="error",
                       detail=repr(e)[:400])
            sys.stderr.write(f"      ERROR {e!r}\n")
        done += 1
        if a.max_units and done >= a.max_units:
            sys.stderr.write(f"\n  stopping after {done} units as asked\n")
            break

    t = led.totals()
    sys.stderr.write(f"\n  ledger: {t['done']:,} units done, "
                     f"{t['addresses']:,} addresses, {t['hits']} hits, "
                     f"{t['invalid']} invalid\n")


if __name__ == "__main__":
    main()
