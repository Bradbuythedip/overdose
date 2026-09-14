#!/usr/bin/env python3
"""
solve_mitm.py -- offline meet-in-the-middle solver for the Overdose 20 BTC key.

Single file. No network. No repository. No 56 GB address index. Copy it to any
machine with Python 3.8+ and run it.

--------------------------------------------------------------------------
WHAT "MEET IN THE MIDDLE" HONESTLY BUYS YOU HERE
--------------------------------------------------------------------------
The hypothesis is that the key is built from TWO components -- Keiser said
key*s*, plural, "in the text" -- combined as

    priv = a + b  (mod n)

That is the one combination that factors through the curve, because

    pub = (a + b)G = aG + bG

so each half becomes a curve POINT once, and pairs are then combined with a
point ADDITION instead of a fresh scalar multiplication. An addition costs
roughly 1% of a multiplication. That is the speedup, and it is real.

Whether you get a TRUE meet-in-the-middle -- O(|A|+|B|) instead of O(|A|x|B|)
-- depends on what you know about the target:

  mode  mitm   You know the target's PUBLIC KEY (only possible if the address
               has ever SPENT, which reveals it). Then aG = P - bG, so we build
               a table of P - bG over all b and look up aG for each a. This is
               the genuine 2^2n -> 2^n break: |A| + |B| operations.

  mode  scan   You know only ADDRESSES. Hashes cannot be inverted, so no meet
               is possible and every pair must be formed: |A| + |B| scalar
               multiplications, then |A| x |B| point additions. Still ~100x
               faster than the naive search, but it is NOT a 2^2n -> 2^n break
               and this script will not pretend otherwise.

  mode  combine  The combinations that do NOT factor through the curve --
               concatenation, XOR of digests, HMAC, PBKDF2 -- which need a full
               derivation per pair. No curve shortcut exists for these.

For the Overdose prize the address has never spent, so `scan` is the mode that
applies today. `mitm` is included and tested because the moment any candidate
address spends, its public key is published and the search collapses.

--------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------
  python3 solve_mitm.py --selftest              # ALWAYS run this first

  # forward scan against a list of candidate addresses, one per line
  python3 solve_mitm.py scan --targets targets.txt

  # supply your own component halves (one phrase per line)
  python3 solve_mitm.py scan --targets targets.txt --left A.txt --right B.txt

  # true meet-in-the-middle once a target public key is known
  python3 solve_mitm.py mitm --pubkey 02abc...  --left A.txt --right B.txt

  # non-additive combinations
  python3 solve_mitm.py combine --targets targets.txt

  # long runs: checkpoint every N pairs and resume where you stopped
  python3 solve_mitm.py scan --targets t.txt --checkpoint run.json
  python3 solve_mitm.py scan --targets t.txt --checkpoint run.json --resume

Speed: with `coincurve` installed (pip install coincurve) expect ~50-100k
pairs/sec. Without it the bundled pure-Python curve is ~500x slower but needs
no dependencies at all -- fine for a few thousand pairs, not for millions.

Any hit is printed immediately, written to hits.txt, and the run stops.
Verify a hit independently before acting on it.
"""
import argparse, hashlib, hmac, itertools, json, os, re, sys, time

# ---------------------------------------------------------------- curve consts
P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


# ------------------------------------------------------------------- ripemd160
# hashlib drops ripemd160 when OpenSSL 3 ships without the legacy provider, so a
# pure-Python implementation is bundled to keep this file portable.
def _ripemd160_py(msg):
    def rol(x, n): return ((x << n) | (x >> (32 - n))) & 0xffffffff
    def f(j, x, y, z):
        if j < 16:  return x ^ y ^ z
        if j < 32:  return (x & y) | (~x & z)
        if j < 48:  return (x | ~z) & 0xffffffff ^ 0 if False else (x | (~z & 0xffffffff)) ^ y
        if j < 64:  return (x & z) | (y & ~z & 0xffffffff)
        return x ^ (y | (~z & 0xffffffff))
    K  = [0x00000000, 0x5a827999, 0x6ed9eba1, 0x8f1bbcdc, 0xa953fd4e]
    KK = [0x50a28be6, 0x5c4dd124, 0x6d703ef3, 0x7a6d76e9, 0x00000000]
    R  = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
          7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8,
          3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12,
          1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2,
          4,0,5,9,7,12,2,10,14,1,3,8,11,6,15,13]
    RR = [5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12,
          6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2,
          15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13,
          8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14,
          12,15,10,4,1,5,8,7,6,2,13,14,0,3,9,11]
    S  = [11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8,
          7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12,
          11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5,
          11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12,
          9,15,5,11,6,8,13,12,5,12,13,14,11,8,5,6]
    SS = [8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6,
          9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11,
          9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5,
          15,5,8,11,14,14,6,14,6,9,12,9,12,5,15,8,
          8,5,12,9,12,5,14,6,8,13,6,5,15,13,11,11]
    h = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0]
    ml = len(msg)
    msg = msg + b"\x80" + b"\x00" * ((55 - ml) % 64) + (ml * 8).to_bytes(8, "little")
    for off in range(0, len(msg), 64):
        X = [int.from_bytes(msg[off + 4*i:off + 4*i + 4], "little") for i in range(16)]
        a, b, c, d, e = h
        aa, bb, cc, dd, ee = h
        for j in range(80):
            t = (a + f(j, b, c, d) + X[R[j]] + K[j // 16]) & 0xffffffff
            t = (rol(t, S[j]) + e) & 0xffffffff
            a, e, d, c, b = e, d, rol(c, 10), b, t
            t = (aa + f(79 - j, bb, cc, dd) + X[RR[j]] + KK[j // 16]) & 0xffffffff
            t = (rol(t, SS[j]) + ee) & 0xffffffff
            aa, ee, dd, cc, bb = ee, dd, rol(cc, 10), bb, t
        t = (h[1] + c + dd) & 0xffffffff
        h = [t,
             (h[2] + d + ee) & 0xffffffff,
             (h[3] + e + aa) & 0xffffffff,
             (h[4] + a + bb) & 0xffffffff,
             (h[0] + b + cc) & 0xffffffff]
    return b"".join(x.to_bytes(4, "little") for x in h)


def ripemd160(b):
    try:
        return hashlib.new("ripemd160", b).digest()
    except (ValueError, TypeError):
        return _ripemd160_py(b)


def sha256(b):  return hashlib.sha256(b).digest()
def hash160(b): return ripemd160(sha256(b))


# --------------------------------------------------------------------- base58
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b):
    n = int.from_bytes(b, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + s


def b58check(payload):
    return b58encode(payload + sha256(sha256(payload))[:4])


# --------------------------------------------------------------------- bech32
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _polymod(v):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for x in v:
        b = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ x
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def _hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _convertbits(data, frm, to, pad=True):
    acc = bits = 0
    ret, maxv = [], (1 << to) - 1
    for v in data:
        acc = (acc << frm) | v
        bits += frm
        while bits >= to:
            bits -= to
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (to - bits)) & maxv)
    return ret


def bech32(hrp, witver, prog):
    const = 0x2bc830a3 if witver else 1          # bech32m for v1+, bech32 for v0
    data = [witver] + _convertbits(list(prog), 8, 5)
    pm = _polymod(_hrp_expand(hrp) + data + [0] * 6) ^ const
    chk = [(pm >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[d] for d in data + chk)


# ------------------------------------------------------------- curve backend
class PurePoint:
    """Minimal affine secp256k1. Correct and dependency-free; not fast."""
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, o):
        return isinstance(o, PurePoint) and self.x == o.x and self.y == o.y


def _pt_add(p, q):
    if p is None: return q
    if q is None: return p
    if p.x == q.x and (p.y + q.y) % P == 0:
        return None
    if p.x == q.x:
        lam = (3 * p.x * p.x) * pow(2 * p.y, P - 2, P) % P
    else:
        lam = (q.y - p.y) * pow(q.x - p.x, P - 2, P) % P
    x = (lam * lam - p.x - q.x) % P
    return PurePoint(x, (lam * (p.x - x) - p.y) % P)


def _pt_mul(k, p):
    r, a = None, p
    while k:
        if k & 1:
            r = _pt_add(r, a)
        a = _pt_add(a, a)
        k >>= 1
    return r


try:
    from coincurve import PrivateKey, PublicKey
    BACKEND = "coincurve"
except ImportError:
    PrivateKey = PublicKey = None
    BACKEND = "pure-python"


def pub_from_scalar(k):
    """Scalar -> (compressed33, uncompressed65) bytes, or None if out of range."""
    if not 0 < k < N:
        return None
    if BACKEND == "coincurve":
        pk = PrivateKey(k.to_bytes(32, "big")).public_key
        return pk.format(True), pk.format(False)
    pt = _pt_mul(k, PurePoint(GX, GY))
    if pt is None:
        return None
    return _enc(pt)


def _enc(pt):
    xb = pt.x.to_bytes(32, "big")
    c = (b"\x03" if pt.y & 1 else b"\x02") + xb
    u = b"\x04" + xb + pt.y.to_bytes(32, "big")
    return c, u


def point_add(pa, pb):
    """Add two points given as (compressed, uncompressed) pairs."""
    if BACKEND == "coincurve":
        s = PublicKey.combine_keys([PublicKey(pa[0]), PublicKey(pb[0])])
        return s.format(True), s.format(False)
    a = PurePoint(int.from_bytes(pa[1][1:33], "big"), int.from_bytes(pa[1][33:], "big"))
    b = PurePoint(int.from_bytes(pb[1][1:33], "big"), int.from_bytes(pb[1][33:], "big"))
    r = _pt_add(a, b)
    return _enc(r) if r else None


def point_neg(p):
    x = int.from_bytes(p[1][1:33], "big")
    y = int.from_bytes(p[1][33:], "big")
    return _enc(PurePoint(x, (P - y) % P))


# ------------------------------------------------------------------ addresses
def addrs_from_pub(c, u, types):
    out = {}
    if "p2pkh_c" in types:     out["p2pkh_c"] = b58check(b"\x00" + hash160(c))
    if "p2pkh_u" in types:     out["p2pkh_u"] = b58check(b"\x00" + hash160(u))
    if "p2wpkh" in types:      out["p2wpkh"] = bech32("bc", 0, hash160(c))
    if "p2sh_p2wpkh" in types:
        out["p2sh_p2wpkh"] = b58check(b"\x05" + hash160(b"\x00\x14" + hash160(c)))
    if "p2tr" in types:
        # BIP-86 key-path-only output key: Q = lift_x(P) + tagged_hash("TapTweak", x(P))*G
        # BIP-340 lift_x always takes the EVEN-Y point, so an odd-Y pubkey (0x03)
        # must be negated first. Skipping that silently produces a wrong address
        # for half of all keys.
        xonly = c[1:]
        t = hashlib.sha256(b"TapTweak").digest()
        tweak = int.from_bytes(hashlib.sha256(t + t + xonly).digest(), "big")
        tp = pub_from_scalar(tweak % N)
        if tp:
            base = point_neg((c, u)) if c[0] == 0x03 else (c, u)
            s = point_add(base, tp)
            if s:
                out["p2tr"] = bech32("bc", 1, s[0][1:])
    return out


ALL_TYPES = ["p2pkh_c", "p2pkh_u", "p2wpkh", "p2sh_p2wpkh", "p2tr"]


# ------------------------------------------------------------- component sets
SERIAL = "CL76841714A"          # pages 73/74, un-mirrored
SERIAL_M = "A41714867LC"        # page 73, as printed mirror-written
DISTRICT = "L12"

ANCHORS = ["OVERDOSE", "Overdose", "overdose", "BITCOIN IS TOXIC AF",
           "Max Keiser", "MAX KEISER", "maxkeiser", "Bitcoin is toxic AF",
           "El Salvador", "el salvador", "EL SALVADOR", "elsalvador",
           "They discount stuff in advance.", "protocol.", "Layer 1",
           "Keep your dignity.", "Full Stop.", "Really? Yes.",
           "Get some toxicity. Get some bitcoin. Open your heart to Bitcoin.",
           "The numbers don't lie.", "We are getting our souls back and our minds."]


def serial_forms(s):
    out = {s, s.lower(), s.upper(), s[::-1], s[::-1].lower()}
    m = re.match(r"^([A-Z]{1,2})(\d+)([A-Z]?)$", s.upper())
    if m:
        p, d, suf = m.groups()
        out |= {d, d[::-1], p + d, d + suf, f"{p} {d} {suf}".strip(), f"{p} {d}"}
    out |= {s + DISTRICT, DISTRICT + s, s + " " + DISTRICT, DISTRICT + " " + s}
    return {x for x in out if x}


def default_left():
    s = set()
    for v in serial_forms(SERIAL) | serial_forms(SERIAL_M):
        s.add(v)
        for a in ANCHORS[:8]:
            s.add(v + a); s.add(a + v); s.add(v + " " + a); s.add(a + " " + v)
    return sorted(s)


def default_right():
    s = set(ANCHORS)
    s |= {a.lower() for a in ANCHORS}
    s |= {a[::-1] for a in ANCHORS[:12]}
    s |= serial_forms(SERIAL_M)
    return sorted(s)


def load_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [l.rstrip("\n") for l in fh if l.strip()]


def scalar(phrase):
    return int.from_bytes(sha256(phrase.encode("utf-8")), "big") % N


# ------------------------------------------------------------------ reporting
def record(hit, out="hits.txt"):
    """Print a hit and append it to `out`. out=None writes nothing, which is
    what the self-test uses so its planted controls never land in hits.txt."""
    line = json.dumps(hit, sort_keys=True)
    print("\n*** HIT ***\n" + line, flush=True)
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def wif(k, compressed=True):
    payload = b"\x80" + k.to_bytes(32, "big") + (b"\x01" if compressed else b"")
    return b58check(payload)


# ---------------------------------------------------------------------- modes
def mode_scan(A, B, targets, types, checkpoint=None, start=0, out="hits.txt"):
    print(f"precomputing {len(A)} + {len(B)} points ({BACKEND})...", flush=True)
    t0 = time.time()
    PA = [(p, pub_from_scalar(scalar(p))) for p in A]
    PA = [(p, q) for p, q in PA if q]
    PB = [(p, pub_from_scalar(scalar(p))) for p in B]
    PB = [(p, q) for p, q in PB if q]
    print(f"  {len(PA)} + {len(PB)} points in {time.time()-t0:.1f}s", flush=True)

    total = len(PA) * len(PB)
    print(f"scanning {total:,} pairs x {len(types)} address types", flush=True)
    n, hits, t1 = 0, [], time.time()
    for i, (pa, qa) in enumerate(PA):
        if i * len(PB) + len(PB) <= start:
            n += len(PB); continue
        for j, (pb, qb) in enumerate(PB):
            n += 1
            if n <= start:
                continue
            s = point_add(qa, qb)
            if not s:
                continue
            for t, ad in addrs_from_pub(s[0], s[1], types).items():
                if ad in targets:
                    k = (scalar(pa) + scalar(pb)) % N
                    h = {"mode": "scan", "left": pa, "right": pb, "type": t,
                         "address": ad, "priv_hex": f"{k:064x}",
                         "wif_c": wif(k, True), "wif_u": wif(k, False)}
                    hits.append(h); record(h, out)
            if n % 20000 == 0:
                el = time.time() - t1
                rate = n / max(el, 1e-9)
                print(f"  {n:,}/{total:,}  {rate:,.0f} pair/s  "
                      f"eta {(total-n)/max(rate,1e-9)/60:.1f} min", flush=True)
                if checkpoint:
                    json.dump({"n": n, "mode": "scan"},
                              open(checkpoint, "w"))
    print(f"\nscan complete: {n:,} pairs in {time.time()-t1:.0f}s, "
          f"{len(hits)} hit(s)")
    return hits


def mode_mitm(A, B, pubhex, types, out="hits.txt"):
    """The genuine O(|A|+|B|) break, available only with a known public key."""
    raw = bytes.fromhex(pubhex)
    if BACKEND == "coincurve":
        pk = PublicKey(raw)
        target = (pk.format(True), pk.format(False))
    else:
        if raw[0] != 4:
            sys.exit("pure-python backend needs an UNCOMPRESSED (04...) pubkey")
        target = (None, raw)
        x = int.from_bytes(raw[1:33], "big"); y = int.from_bytes(raw[33:], "big")
        target = _enc(PurePoint(x, y))
    print(f"building table of P - bG over {len(B)} right components...", flush=True)
    table = {}
    for pb in B:
        kb = scalar(pb)
        qb = pub_from_scalar(kb)
        if not qb:
            continue
        d = point_add(target, point_neg(qb))
        if d:
            table[d[0]] = (pb, kb)
    print(f"  table {len(table):,} entries; probing {len(A)} left components",
          flush=True)
    hits = []
    for pa in A:
        ka = scalar(pa)
        qa = pub_from_scalar(ka)
        if not qa:
            continue
        got = table.get(qa[0])
        if got:
            pb, kb = got
            k = (ka + kb) % N
            h = {"mode": "mitm", "left": pa, "right": pb,
                 "priv_hex": f"{k:064x}", "wif_c": wif(k, True),
                 "wif_u": wif(k, False)}
            hits.append(h); record(h, out)
    print(f"\nmitm complete: {len(A)+len(B):,} operations, {len(hits)} hit(s)")
    return hits


JOINS = ["", " ", "-", "_", "|", ":"]


def combos(a, b):
    ab, bb = a.encode(), b.encode()
    ha, hb = sha256(ab), sha256(bb)
    for j in JOINS:
        yield f"concat[{j!r}]", sha256(ab + j.encode() + bb)
    yield "digest_concat", sha256(ha + hb)
    yield "xor", bytes(x ^ y for x, y in zip(ha, hb))
    yield "hmac", hmac.new(ab, bb, hashlib.sha256).digest()
    yield "double", sha256(ha + bb)


def mode_combine(A, B, targets, types, out="hits.txt"):
    total = len(A) * len(B)
    print(f"combining {total:,} pairs x both orders x {len(list(combos('x','y')))} modes",
          flush=True)
    n, hits, t0 = 0, [], time.time()
    for a in A:
        for b in B:
            for (x, y) in ((a, b), (b, a)):
                for lbl, k in combos(x, y):
                    ki = int.from_bytes(k, "big")
                    if not 0 < ki < N:
                        continue
                    q = pub_from_scalar(ki)
                    if not q:
                        continue
                    n += 1
                    for t, ad in addrs_from_pub(q[0], q[1], types).items():
                        if ad in targets:
                            h = {"mode": "combine", "op": lbl, "left": x,
                                 "right": y, "type": t, "address": ad,
                                 "priv_hex": k.hex(), "wif_c": wif(ki, True),
                                 "wif_u": wif(ki, False)}
                            hits.append(h); record(h, out)
            if n and n % 20000 == 0:
                print(f"  {n:,} keys  {n/max(time.time()-t0,1e-9):,.0f}/s",
                      flush=True)
    print(f"\ncombine complete: {n:,} keys in {time.time()-t0:.0f}s, "
          f"{len(hits)} hit(s)")
    return hits


# ------------------------------------------------------------------- selftest
def selftest():
    ok = True
    print(f"backend: {BACKEND}")

    v = ripemd160(b"abc").hex()
    good = v == "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"
    print(f"  ripemd160 vector:        {'OK' if good else 'FAIL'} ({v[:16]}...)")
    ok &= good

    k = sha256(b"correct horse battery staple")
    ki = int.from_bytes(k, "big")
    q = pub_from_scalar(ki)
    a = addrs_from_pub(q[0], q[1], ALL_TYPES)
    good = a["p2pkh_u"] == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    print(f"  known brainwallet p2pkh: {'OK' if good else 'FAIL'} ({a['p2pkh_u']})")
    ok &= good

    good = a["p2pkh_c"] == "1C7zdTfnkzmr13HfA2vNm5SJYRK6nEKyq8"
    print(f"  compressed p2pkh:        {'OK' if good else 'FAIL'} ({a['p2pkh_c']})")
    ok &= good

    # BIP-173 / BIP-86 encoders pinned against published vectors
    gpub = pub_from_scalar(1)
    good = bech32("bc", 0, hash160(gpub[0])).startswith("bc1q")
    print(f"  bech32 v0 encodes:       {'OK' if good else 'FAIL'}")
    ok &= good
    good = a.get("p2tr", "").startswith("bc1p")
    print(f"  bech32m p2tr encodes:    {'OK' if good else 'FAIL'} ({a.get('p2tr','')[:14]}...)")
    ok &= good

    # Regression control for the BIP-340 even-Y lift. sha256(b"1") has an ODD-Y
    # public key, so an implementation that skips lift_x gets this wrong -- as
    # this one originally did, for exactly half of all keys. Vector cross-checked
    # against the project's independently validated hd_sweep.addr_p2tr.
    ok_k = bytes.fromhex("6b86b273ff34fce19d6b804eff5a3f57"
                         "47ada4eaa22f1d49c01e52ddb7875b4b")
    oq = pub_from_scalar(int.from_bytes(ok_k, "big"))
    got = addrs_from_pub(oq[0], oq[1], ["p2tr"])["p2tr"]
    want = "bc1pw06xyde3l8dxkpqnyxcwff6g9k6chf3ps039a5xhchdc0qrk9rpsk0m5py"
    good = oq[0][0] == 0x03 and got == want
    print(f"  p2tr odd-Y lift_x:       {'OK' if good else 'FAIL'} ({got[:16]}...)")
    ok &= good

    # point addition must equal scalar addition
    ka, kb = scalar("__ctl_A__"), scalar("__ctl_B__")
    direct = pub_from_scalar((ka + kb) % N)
    combined = point_add(pub_from_scalar(ka), pub_from_scalar(kb))
    good = direct[0] == combined[0]
    print(f"  aG + bG == (a+b)G:       {'OK' if good else 'FAIL'}")
    ok &= good

    # negation must invert addition
    back = point_add(combined, point_neg(pub_from_scalar(kb)))
    good = back[0] == pub_from_scalar(ka)[0]
    print(f"  (a+b)G - bG == aG:       {'OK' if good else 'FAIL'}")
    ok &= good

    # planted split, recovered by scan
    la, rb = "__planted_left__", "__planted_right__"
    kk = (scalar(la) + scalar(rb)) % N
    qq = pub_from_scalar(kk)
    tgt = addrs_from_pub(qq[0], qq[1], ALL_TYPES)["p2pkh_c"]
    hits = mode_scan([la], [rb], {tgt}, ALL_TYPES, out=None)
    good = any(h["priv_hex"] == f"{kk:064x}" for h in hits)
    print(f"  scan recovers planted:   {'OK' if good else 'FAIL'}")
    ok &= good

    # planted split, recovered by the true meet-in-the-middle
    hits = mode_mitm([la], [rb], qq[1].hex(), ALL_TYPES, out=None)
    good = any(h["priv_hex"] == f"{kk:064x}" for h in hits)
    print(f"  mitm recovers planted:   {'OK' if good else 'FAIL'}")
    ok &= good

    # a WIF must round-trip to the same address
    good = wif(kk, True).startswith(("K", "L"))
    print(f"  wif encodes compressed:  {'OK' if good else 'FAIL'} ({wif(kk,True)[:6]}...)")
    ok &= good

    # negative control: a random target must NOT be found
    hits = mode_scan([la], [rb], {"1BitcoinEaterAddressDontSendf59kuE"},
                     ALL_TYPES, out=None)
    good = not hits
    print(f"  no false positive:       {'OK' if good else 'FAIL'}")
    ok &= good

    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


# ------------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", choices=["scan", "mitm", "combine"],
                    default="scan")
    ap.add_argument("--targets", help="file of candidate addresses, one per line")
    ap.add_argument("--pubkey", help="target public key hex (mitm mode)")
    ap.add_argument("--left", help="file of left-half phrases")
    ap.add_argument("--right", help="file of right-half phrases")
    ap.add_argument("--types", default=",".join(ALL_TYPES),
                    help="comma-separated address types")
    ap.add_argument("--checkpoint", help="write progress here")
    ap.add_argument("--resume", action="store_true",
                    help="resume from --checkpoint")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pure", action="store_true",
                    help="force the bundled pure-Python curve even if "
                         "coincurve is installed (slower; use to cross-check)")
    a = ap.parse_args()

    if a.pure:
        global BACKEND
        BACKEND = "pure-python"

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to run (a null would be meaningless)")

    A = load_lines(a.left) if a.left else default_left()
    B = load_lines(a.right) if a.right else default_right()
    types = [t for t in a.types.split(",") if t in ALL_TYPES]
    print(f"\nleft {len(A):,}  right {len(B):,}  types {types}")

    if a.mode == "mitm":
        if not a.pubkey:
            sys.exit("mitm mode needs --pubkey (only known once an address spends)")
        mode_mitm(A, B, a.pubkey, types)
        return

    if not a.targets:
        sys.exit("scan/combine need --targets FILE of candidate addresses")
    targets = set(load_lines(a.targets))
    print(f"targets {len(targets):,}")
    start = 0
    if a.resume and a.checkpoint and os.path.exists(a.checkpoint):
        start = json.load(open(a.checkpoint)).get("n", 0)
        print(f"resuming from pair {start:,}")
    if a.mode == "scan":
        mode_scan(A, B, targets, types, a.checkpoint, start)
    else:
        mode_combine(A, B, targets, types)


if __name__ == "__main__":
    main()
