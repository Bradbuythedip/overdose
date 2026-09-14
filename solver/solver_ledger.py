#!/usr/bin/env python3
"""
Durable work ledger. The part that makes an unattended solver honest.

WHY A LEDGER AND NOT A SCRIPT
This project has accumulated dozens of one-shot sweeps, and the recurring
failure has not been compute — it has been BOOKKEEPING. Work was repeated
because nobody remembered it had run; nulls were trusted because nobody
recorded which oracle produced them; a corpus was swept against a balance index
and later described as if it had been checked against chain history. An
unattended loop multiplies all three.

So every unit of work gets a deterministic id from its family and parameters,
and the ledger records what ran, against WHICH ORACLE, whether that oracle
produced a known positive in the same run, and what came out. A unit whose
control did not fire is recorded as INVALID, not as a null — that distinction
is the whole point, and it is the one this project has had to relearn most
often.

  python3 solver_ledger.py --selftest
  python3 solver_ledger.py --stats
"""
import argparse, hashlib, json, os, sqlite3, sys, time

DB = os.environ.get("OVERDOSE_LEDGER", "solver_ledger.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS work (
  id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  params TEXT NOT NULL,
  status TEXT NOT NULL,            -- pending | running | done | invalid | error
  oracle TEXT,                     -- which oracle judged it
  control_ok INTEGER,              -- did that oracle produce a known positive
  candidates INTEGER DEFAULT 0,
  addresses INTEGER DEFAULT 0,
  hits INTEGER DEFAULT 0,
  detail TEXT,
  started REAL, finished REAL
);
CREATE INDEX IF NOT EXISTS ix_status ON work(status);
CREATE INDEX IF NOT EXISTS ix_family ON work(family);
CREATE TABLE IF NOT EXISTS hits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id TEXT, family TEXT, label TEXT, address TEXT,
  value INTEGER, oracle TEXT, found REAL
);
"""


def work_id(family, params):
    """Deterministic id, so the same work is never queued twice."""
    blob = json.dumps([family, params], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


class Ledger:
    def __init__(self, path=DB):
        self.db = sqlite3.connect(path, timeout=30)
        self.db.executescript(SCHEMA)
        self.db.commit()

    def add(self, family, params):
        """Queue a unit. Returns its id; silently ignores a duplicate."""
        wid = work_id(family, params)
        self.db.execute(
            "INSERT OR IGNORE INTO work(id,family,params,status) VALUES(?,?,?,?)",
            (wid, family, json.dumps(params, sort_keys=True), "pending"))
        self.db.commit()
        return wid

    def claim(self, order_by="family"):
        """Take the next pending unit and mark it running."""
        cur = self.db.execute(
            f"SELECT id,family,params FROM work WHERE status='pending' "
            f"ORDER BY {order_by} LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
        wid, family, params = row
        self.db.execute("UPDATE work SET status='running',started=? WHERE id=?",
                        (time.time(), wid))
        self.db.commit()
        return wid, family, json.loads(params)

    def finish(self, wid, *, oracle, control_ok, candidates=0, addresses=0,
               hits=0, detail="", status=None):
        """Record an outcome. A unit whose control did not fire is INVALID.

        Not 'done with zero hits' — invalid. A null from an oracle that never
        proved it can see a positive is not evidence, and letting it be filed
        as a null is exactly how this project once recorded 0 hits over 782
        files that were all 404 bodies.
        """
        st = status or ("done" if control_ok else "invalid")
        self.db.execute(
            "UPDATE work SET status=?,oracle=?,control_ok=?,candidates=?,"
            "addresses=?,hits=?,detail=?,finished=? WHERE id=?",
            (st, oracle, 1 if control_ok else 0, candidates, addresses, hits,
             detail[:2000], time.time(), wid))
        self.db.commit()

    def hit(self, wid, family, label, address, value, oracle):
        self.db.execute(
            "INSERT INTO hits(work_id,family,label,address,value,oracle,found) "
            "VALUES(?,?,?,?,?,?,?)",
            (wid, family, label[:300], address, int(value), oracle, time.time()))
        self.db.commit()

    def requeue_stale(self, older_than=3600):
        """A unit left 'running' by a crash goes back to pending."""
        n = self.db.execute(
            "UPDATE work SET status='pending' WHERE status='running' AND "
            "started < ?", (time.time() - older_than,)).rowcount
        self.db.commit()
        return n

    def stats(self):
        q = ("SELECT family,status,COUNT(*),SUM(addresses),SUM(hits) FROM work "
             "GROUP BY family,status ORDER BY family,status")
        return list(self.db.execute(q))

    def totals(self):
        r = self.db.execute(
            "SELECT COUNT(*),SUM(addresses),SUM(hits) FROM work "
            "WHERE status='done'").fetchone()
        inv = self.db.execute(
            "SELECT COUNT(*) FROM work WHERE status='invalid'").fetchone()[0]
        return {"done": r[0] or 0, "addresses": r[1] or 0, "hits": r[2] or 0,
                "invalid": inv}


def selftest():
    import tempfile
    ok = True
    p = os.path.join(tempfile.mkdtemp(), "t.sqlite")
    L = Ledger(p)

    a = L.add("fam", {"x": 1})
    b = L.add("fam", {"x": 1})
    ok &= a == b
    sys.stderr.write(f"  same params give the same id, queued once: "
                     f"{'OK' if a == b else 'FAIL'}\n")
    c = L.add("fam", {"x": 2})
    ok &= c != a
    sys.stderr.write(f"  different params give a different id: "
                     f"{'OK' if c != a else 'FAIL'}\n")

    got = L.claim()
    ok &= got is not None and got[0] in (a, c)
    L.finish(got[0], oracle="test", control_ok=True, addresses=10)
    L.finish(c if got[0] == a else a, oracle="test", control_ok=False,
             addresses=10)
    t = L.totals()
    ok &= t["done"] == 1 and t["invalid"] == 1
    sys.stderr.write(f"  control_ok=False files as INVALID not done: "
                     f"{'OK' if t['invalid'] == 1 else 'FAIL'}\n")
    sys.stderr.write(f"  totals {t}\n")

    # a crashed unit must come back
    L.add("fam", {"x": 3})
    w = L.claim()
    L.db.execute("UPDATE work SET started=? WHERE id=?", (0, w[0]))
    L.db.commit()
    n = L.requeue_stale(1)
    ok &= n == 1
    sys.stderr.write(f"  stale 'running' unit requeued: "
                     f"{'OK' if n == 1 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    L = Ledger(a.db)
    if a.stats:
        t = L.totals()
        sys.stderr.write(f"\n  done {t['done']:,} units, {t['addresses']:,} "
                         f"addresses, {t['hits']} hits, "
                         f"{t['invalid']} INVALID (control did not fire)\n\n")
        for fam, st, n, addrs, hits in L.stats():
            sys.stderr.write(f"    {fam:34} {st:8} {n:5} units  "
                             f"{(addrs or 0):>12,} addrs  {hits or 0} hits\n")


if __name__ == "__main__":
    main()
