#!/usr/bin/env python3
"""
PATH A (primary) — FR1+FR2+FR3 in one pass, ~10^4 cheaper than a block scan.

Takes the offline-derived target set of scripthashes that hold ~20 BTC today
and asks an Electrum server for each one's transaction history. A scripthash
with exactly ONE history entry is, by definition, funded once and never spent
(FR3). Its single tx gives the funding height -> window filter (FR1) and the
output value/address (FR2).

Stdlib only. Run on a machine with outbound Bitcoin network access.

  python3 electrum_sweep.py --targets targets_new.tsv --out window_raw.tsv

Electrum note: the wire format for a scripthash is sha256(scriptPubKey) with
the BYTE ORDER REVERSED. The target file stores the un-reversed digest
(address_map.bin convention), so we reverse on the way out and back on input.
"""
import argparse, json, socket, ssl, sys, time

DEFAULT_SERVERS = [
    ("electrum.blockstream.info", 50002),
    ("fulcrum.sethforprivacy.com", 50002),
    ("electrum.emzy.de", 50002),
    ("bitcoin.lu.ke", 50002),
    ("electrum.bitaroo.net", 50002),
]

class Electrum:
    def __init__(self, host, port, timeout=30):
        self.host, self.port, self.timeout = host, port, timeout
        self.sock = None; self.buf = b""; self.rid = 0
    def connect(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE      # public Electrum servers use self-signed certs
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock = ctx.wrap_socket(raw, server_hostname=self.host)
        self.sock.settimeout(self.timeout)
        self.buf = b""
        self.call_batch([("server.version", ["overdose-solver", "1.4"])])
    def close(self):
        try:
            if self.sock: self.sock.close()
        except Exception: pass
        self.sock = None
    def _readline(self):
        while b"\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk: raise ConnectionError("server closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line
    def call_batch(self, calls):
        """calls = [(method, params), ...] -> list of results (None on error)."""
        reqs = []
        for m, p in calls:
            self.rid += 1
            reqs.append({"jsonrpc": "2.0", "id": self.rid, "method": m, "params": p})
        self.sock.sendall((json.dumps(reqs) + "\n").encode())
        resp = json.loads(self._readline())
        if isinstance(resp, dict): resp = [resp]
        by_id = {r.get("id"): r for r in resp}
        out = []
        for r in reqs:
            rr = by_id.get(r["id"])
            out.append(None if (rr is None or "error" in rr) else rr.get("result"))
        return out

def connect_any(servers, timeout):
    for host, port in servers:
        try:
            e = Electrum(host, port, timeout); e.connect()
            sys.stderr.write(f"connected: {host}:{port}\n")
            return e
        except Exception as ex:
            sys.stderr.write(f"  {host}:{port} failed: {ex}\n")
    raise SystemExit("no Electrum server reachable — try Path B (alchemy_window_scan.py)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True, help="TSV, col1 = sha256(scriptPubKey) hex (un-reversed)")
    ap.add_argument("--out", default="window_raw.tsv")
    ap.add_argument("--batch", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=45)
    ap.add_argument("--server", help="host:port to force a specific Electrum server")
    ap.add_argument("--max-history", type=int, default=1,
                    help="keep scripthashes with at most this many txs (FR3: 1)")
    args = ap.parse_args()

    servers = DEFAULT_SERVERS
    if args.server:
        h, _, p = args.server.partition(":")
        servers = [(h, int(p or 50002))]

    targets = []
    with open(args.targets) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("scripthash"): continue
            sh = line.split("\t")[0]
            if len(sh) == 64: targets.append(sh)
    sys.stderr.write(f"targets: {len(targets):,}\n")

    e = connect_any(servers, args.timeout)
    out = open(args.out, "w")
    out.write("scripthash\ttx_count\tfunding_txid\tblock_height\n")
    kept = done = 0
    i = 0
    while i < len(targets):
        chunk = targets[i:i+args.batch]
        calls = [("blockchain.scripthash.get_history",
                  [bytes.fromhex(sh)[::-1].hex()]) for sh in chunk]
        try:
            res = e.call_batch(calls)
        except Exception as ex:
            sys.stderr.write(f"reconnect after: {ex}\n")
            e.close(); time.sleep(3); e = connect_any(servers, args.timeout)
            continue
        for sh, hist in zip(chunk, res):
            done += 1
            if hist is None: continue
            confirmed = [h for h in hist if h.get("height", 0) > 0]
            if 1 <= len(confirmed) <= args.max_history:
                kept += 1
                out.write(f"{sh}\t{len(confirmed)}\t{confirmed[0]['tx_hash']}\t{confirmed[0]['height']}\n")
                out.flush()
        i += len(chunk)
        if done % 500 < args.batch:
            sys.stderr.write(f"  {done:,}/{len(targets):,}  kept={kept}\n"); sys.stderr.flush()
    out.close()
    sys.stderr.write(f"DONE scanned={done:,} funded-once-never-spent={kept}\n")
    sys.stderr.write(f"-> {args.out}\n")

if __name__ == "__main__":
    main()
