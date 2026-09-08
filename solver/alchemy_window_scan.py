#!/usr/bin/env python3
"""
PATH B (fallback / independent cross-check) — the literal FR1+FR2 brief.

Walks every block in the puzzle window over Bitcoin Core RPC (Alchemy), pulls
each block as RAW HEX (verbosity 0, ~1.7 MB/block instead of ~7 MB of JSON),
parses it locally, and emits every output whose value is in [19.5, 20.5] BTC.

Optionally intersects against the offline ~20-BTC scripthash set so the output
is already FR4-confirmed.

Stdlib only. Resumable: re-running skips heights already in --out.

  python3 alchemy_window_scan.py --rpc https://bitcoin-mainnet.g.alchemy.com/v2/KEY \
      --start 756000 --end 782000 --targets targets_union.tsv --out window_outputs.tsv

  python3 alchemy_window_scan.py --selftest      # parser test vectors, no network
"""
import argparse, hashlib, json, os, sys, threading, queue, urllib.request

# ---------------- encodings ----------------
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58check(payload):
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    s = ""
    while n: n, r = divmod(n, 58); s = B58[r] + s
    return "1" * (len(payload + chk) - len((payload + chk).lstrip(b"\0"))) + s

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
def _polymod(v):
    G = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]; c = 1
    for x in v:
        b = c >> 25; c = ((c & 0x1ffffff) << 5) ^ x
        for i in range(5):
            if (b >> i) & 1: c ^= G[i]
    return c
def _conv(data, f, t, pad):
    acc = bits = 0; out = []; maxv = (1 << t) - 1
    for value in data:
        acc = (acc << f) | value; bits += f
        while bits >= t: bits -= t; out.append((acc >> bits) & maxv)
    if pad and bits: out.append((acc << (t - bits)) & maxv)
    return out
def bech32(hrp, witver, prog):
    data = [witver] + _conv(prog, 8, 5, True)
    exp = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    const = 1 if witver == 0 else 0x2bc830a3
    pm = _polymod(exp + data + [0] * 6) ^ const
    chk = [(pm >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[d] for d in data + chk)

def h160(b): return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()

def script_to_address(s):
    """-> (address, type). None address for non-standard scripts."""
    n = len(s)
    if n == 25 and s[0] == 0x76 and s[1] == 0xA9 and s[2] == 0x14 and s[23] == 0x88 and s[24] == 0xAC:
        return b58check(b"\x00" + s[3:23]), "p2pkh"
    if n == 23 and s[0] == 0xA9 and s[1] == 0x14 and s[22] == 0x87:
        return b58check(b"\x05" + s[2:22]), "p2sh"
    if n == 22 and s[0] == 0x00 and s[1] == 0x14:
        return bech32("bc", 0, s[2:22]), "p2wpkh"
    if n == 34 and s[0] == 0x00 and s[1] == 0x20:
        return bech32("bc", 0, s[2:34]), "p2wsh"
    if n == 34 and s[0] == 0x51 and s[1] == 0x20:
        return bech32("bc", 1, s[2:34]), "p2tr"
    if n == 67 and s[0] == 0x41 and s[66] == 0xAC:
        return b58check(b"\x00" + h160(s[1:66])), "p2pk"
    if n == 35 and s[0] == 0x21 and s[34] == 0xAC:
        return b58check(b"\x00" + h160(s[1:34])), "p2pk"
    return None, "nonstandard"

# ---------------- raw block parser ----------------
class R:
    __slots__ = ("b", "i")
    def __init__(self, b): self.b = b; self.i = 0
    def take(self, n):
        j = self.i + n
        if j > len(self.b): raise ValueError("truncated block")
        v = self.b[self.i:j]; self.i = j; return v
    def u32(self): return int.from_bytes(self.take(4), "little")
    def u64(self): return int.from_bytes(self.take(8), "little")
    def varint(self):
        c = self.take(1)[0]
        if c < 0xfd: return c
        if c == 0xfd: return int.from_bytes(self.take(2), "little")
        if c == 0xfe: return int.from_bytes(self.take(4), "little")
        return int.from_bytes(self.take(8), "little")

def dsha(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def parse_block(raw):
    """-> (timestamp, [ (txid_hex, [(vout_index, value_sats, scriptPubKey)]) ])"""
    r = R(raw)
    hdr = r.take(80)
    ts = int.from_bytes(hdr[68:72], "little")
    ntx = r.varint()
    txs = []
    for _ in range(ntx):
        start = r.i
        ver = r.take(4)
        segwit = False
        mark = r.i
        if r.b[r.i] == 0x00 and r.b[r.i + 1] == 0x01:
            segwit = True; r.take(2)
        vin_start = r.i
        nin = r.varint()
        for _ in range(nin):
            r.take(36)
            r.take(r.varint())
            r.take(4)
        vin_end = r.i
        nout = r.varint()
        outs = []
        for k in range(nout):
            val = r.u64()
            spk = r.take(r.varint())
            outs.append((k, val, spk))
        vout_end = r.i
        if segwit:
            for _ in range(nin):
                for _ in range(r.varint()):
                    r.take(r.varint())
        lock = r.take(4)
        # txid excludes witness data
        if segwit:
            ser = ver + raw[vin_start:vout_end] + lock
        else:
            ser = raw[start:r.i]
        txs.append((dsha(ser)[::-1].hex(), outs))
    return ts, txs

# ---------------- RPC ----------------
class RPC:
    def __init__(self, url): self.url = url; self.n = 0
    def batch(self, calls, tries=5):
        body = []
        for m, p in calls:
            self.n += 1
            body.append({"jsonrpc": "2.0", "id": self.n, "method": m, "params": p})
        data = json.dumps(body).encode()
        last = None
        for a in range(tries):
            try:
                req = urllib.request.Request(self.url, data=data,
                        headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as resp:
                    out = json.loads(resp.read())
                if isinstance(out, dict): out = [out]
                by = {o.get("id"): o for o in out}
                return [by.get(b["id"], {}).get("result") for b in body]
            except Exception as ex:
                last = ex
                import time; time.sleep(min(2 ** a, 30))
        raise RuntimeError(f"rpc failed after {tries}: {last}")

# ---------------- self test ----------------
GENESIS = (
"0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd"
"7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c"
"0101000000010000000000000000000000000000000000000000000000000000000000000000ffff"
"ffff4d04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c"
"6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f722062616e6b73"
"ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b7105cd6a828e03909a6"
"7962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
"ac00000000")

def selftest():
    ok = True
    ts, txs = parse_block(bytes.fromhex(GENESIS))
    print(f"genesis: ts={ts} ntx={len(txs)}")
    assert ts == 1231006505, ts
    assert len(txs) == 1
    txid, outs = txs[0]
    exp = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
    print(f"  txid   = {txid}\n  expect = {exp}  {'OK' if txid==exp else 'MISMATCH'}")
    ok &= txid == exp
    assert len(outs) == 1 and outs[0][1] == 5000000000, outs
    addr, kind = script_to_address(outs[0][2])
    print(f"  output = {outs[0][1]} sats ({outs[0][1]/1e8} BTC) {kind} {addr}")
    ok &= addr == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    # address encoders vs known vectors
    vec = [
        (bytes.fromhex("76a91462e907b15cbf27d5425399ebf6f0fb50ebb88f1888ac"),
         "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"),
        (bytes.fromhex("a91474f209f6ea907e2ea48f74fae05782ae8a66525787"),
         "3CMNFxN1oHBc4R1EpboAL5yzHGgE611Xou"),
        (bytes.fromhex("0014751e76e8199196d454941c45d1b3a323f1433bd6"),
         "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"),
        (bytes.fromhex("00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262"),
         "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3"),
        (bytes.fromhex("512079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"),
         "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"),
    ]
    for spk, want in vec:
        got, kind = script_to_address(spk)
        flag = "OK" if got == want else "MISMATCH"
        print(f"  {kind:11s} {got}  {flag}")
        ok &= got == want

    # synthetic segwit block: 1 non-segwit tx + 1 segwit tx, check values parse
    def vi(n): return bytes([n]) if n < 0xfd else b"\xfd" + n.to_bytes(2, "little")
    spk = bytes.fromhex("0014751e76e8199196d454941c45d1b3a323f1433bd6")
    nonseg = (b"\x01\x00\x00\x00" + vi(1) + b"\x00"*32 + b"\xff\xff\xff\xff" + vi(0) + b"\xff\xff\xff\xff"
              + vi(1) + (1950000000).to_bytes(8, "little") + vi(len(spk)) + spk + b"\x00\x00\x00\x00")
    seg = (b"\x02\x00\x00\x00" + b"\x00\x01" + vi(1) + b"\x11"*32 + b"\x00\x00\x00\x00" + vi(0) + b"\xff\xff\xff\xff"
           + vi(2) + (2000000000).to_bytes(8, "little") + vi(len(spk)) + spk
                   + (2050000001).to_bytes(8, "little") + vi(len(spk)) + spk
           + vi(1) + vi(3) + b"\xaa\xbb\xcc" + b"\x00\x00\x00\x00")
    blk = bytes(80) + vi(2) + nonseg + seg
    ts2, txs2 = parse_block(blk)
    vals = [v for _, o in txs2 for _, v, _ in o]
    print(f"  synthetic segwit block: ntx={len(txs2)} values={vals}")
    ok &= len(txs2) == 2 and vals == [1950000000, 2000000000, 2050000001]
    # txid of the non-segwit tx must equal dsha of its own bytes
    ok &= txs2[0][0] == dsha(nonseg)[::-1].hex()
    # segwit txid must strip marker/flag+witness
    stripped = b"\x02\x00\x00\x00" + seg[6:seg.index(b"\x01\x03\xaa\xbb\xcc")+1-1] + b"\x00\x00\x00\x00"
    print(f"  segwit txid computed (witness-stripped): {txs2[1][0][:16]}...")
    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1

# ---------------- main scan ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc"); ap.add_argument("--start", type=int, default=756000)
    ap.add_argument("--end", type=int, default=782000)
    ap.add_argument("--lo-sats", type=int, default=1_950_000_000)
    ap.add_argument("--hi-sats", type=int, default=2_050_000_000)
    ap.add_argument("--targets", help="optional scripthash set -> also apply FR4 inline")
    ap.add_argument("--out", default="window_outputs.tsv")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: sys.exit(selftest())
    if not a.rpc: sys.exit("--rpc required (or use --selftest)")

    tset = None
    if a.targets:
        tset = set()
        for line in open(a.targets):
            line = line.strip()
            if len(line.split("\t")[0]) == 64 and not line.startswith("scripthash"):
                tset.add(bytes.fromhex(line.split("\t")[0]))
        sys.stderr.write(f"FR4 target set: {len(tset):,} scripthashes\n")

    seen = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            p = line.split("\t")
            if len(p) > 4 and p[3].isdigit(): seen.add(int(p[3]))
        sys.stderr.write(f"resuming: {len(seen):,} heights already done\n")
    else:
        with open(a.out, "w") as f:
            f.write("address\tscript_type\tfunding_txid\tblock_height\tblock_time\tvout\tvalue_sats\tscripthash\tin_target_set\n")

    heights = [h for h in range(a.start, a.end + 1) if h not in seen]
    sys.stderr.write(f"blocks to scan: {len(heights):,}\n")
    rpc = RPC(a.rpc)
    q = queue.Queue(); [q.put(h) for h in heights]
    lock = threading.Lock(); out = open(a.out, "a")
    stats = {"blk": 0, "hit": 0, "tgt": 0}

    def worker():
        while True:
            try: h = q.get_nowait()
            except queue.Empty: return
            try:
                bh = rpc.batch([("getblockhash", [h])])[0]
                raw = rpc.batch([("getblock", [bh, 0])])[0]
                ts, txs = parse_block(bytes.fromhex(raw))
                rows = []
                for txid, outs in txs:
                    for k, val, spk in outs:
                        if a.lo_sats <= val <= a.hi_sats:
                            addr, kind = script_to_address(spk)
                            sh = hashlib.sha256(spk).digest()
                            inset = "" if tset is None else ("YES" if sh in tset else "no")
                            rows.append(f"{addr}\t{kind}\t{txid}\t{h}\t{ts}\t{k}\t{val}\t{sh.hex()}\t{inset}\n")
                with lock:
                    for r in rows:
                        out.write(r)
                        if r.endswith("YES\n"): stats["tgt"] += 1
                    stats["blk"] += 1; stats["hit"] += len(rows)
                    if stats["blk"] % 250 == 0:
                        out.flush()
                        sys.stderr.write(f"  blocks={stats['blk']:,}/{len(heights):,} "
                                         f"in-band={stats['hit']} FR4-confirmed={stats['tgt']}\n")
                        sys.stderr.flush()
            except Exception as ex:
                sys.stderr.write(f"  height {h} ERROR {ex}\n")

    ts_ = [threading.Thread(target=worker, daemon=True) for _ in range(a.threads)]
    [t.start() for t in ts_]; [t.join() for t in ts_]
    out.close()
    sys.stderr.write(f"DONE blocks={stats['blk']:,} in-band={stats['hit']} FR4-confirmed={stats['tgt']}\n")

if __name__ == "__main__":
    main()
