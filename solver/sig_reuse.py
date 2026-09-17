#!/usr/bin/env python3
"""
Recover a private key from ECDSA NONCE REUSE. A key without the cipher.

THE IDEA
"Keep pulling txs until you find something." The something worth finding is a
repeated ECDSA nonce. If one private key d signs two different messages with
the same nonce k:

    s1 = k^-1 (z1 + r d),   s2 = k^-1 (z2 + r d),   same r
    => k = (z1 - z2) / (s1 - s2)
    => d = (s1 k - z1) / r        (all mod n)

No derivation, no brainwallet, no cipher. Just algebra on two signatures. This
was a real key-leak vector for the exact era these wallets are from (the 2013
Android SecureRandom bug; many early wallets had weak RNGs). If the setter's
funding wallet leaked this way, and it is one HD wallet with the prize address,
the prize follows.

WHAT IT DOES
Given raw transaction hexes (or a trace_cache.jsonl of Esplora tx JSON), it
extracts every legacy-input signature as (pubkey, r, s, z), where z is the
BIP-143-free legacy SIGHASH_ALL preimage hash (scriptCode = the input's own
P2PKH script, reconstructable from its address). It groups by pubkey and, for
any pubkey signing twice with the same r and different z, recovers d and
VERIFIES d*G == pubkey before emitting a WIF.

VERIFICATION IS MANDATORY. A recovered d that does not regenerate the pubkey is
arithmetic noise; it is discarded. Needs coincurve for the one point multiply.

  python3 sig_reuse.py --selftest
  python3 sig_reuse.py --tx <rawhex> [--tx <rawhex> ...]
  python3 sig_reuse.py --cache trace_cache.jsonl
"""
import argparse, hashlib, json, sys

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def dsha(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def der_rs(sig):
    """(r, s) from a DER signature (trailing sighash byte already stripped)."""
    assert sig[0] == 0x30
    i = 2
    assert sig[i] == 0x02; rl = sig[i + 1]; i += 2
    r = int.from_bytes(sig[i:i + rl], "big"); i += rl
    assert sig[i] == 0x02; sl = sig[i + 1]; i += 2
    s = int.from_bytes(sig[i:i + sl], "big")
    return r, s


def pushes(script):
    out, i = [], 0
    while i < len(script):
        op = script[i]; i += 1
        if op < 0x4c:
            out.append(script[i:i + op]); i += op
        elif op == 0x4c:
            n = script[i]; i += 1; out.append(script[i:i + n]); i += n
        else:
            break
    return out


def h160(b): return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


def legacy_sighash(raw, vin_index, script_code):
    """SIGHASH_ALL preimage hash for one legacy input.

    Rebuild the tx with every scriptSig empty except this input's, which is set
    to script_code, then dsha(serialized || 0x01000000).
    """
    b = bytes.fromhex(raw) if isinstance(raw, str) else raw
    i = [0]
    def take(n): v = b[i[0]:i[0]+n]; i[0]+=n; return v
    def u32(): return int.from_bytes(take(4), "little")
    def var():
        n = take(1)[0]
        return n if n < 0xfd else int.from_bytes(take({0xfd:2,0xfe:4}.get(n,8)),"little")
    ver = take(4)
    nin = var()
    ins = []
    for _ in range(nin):
        op = take(36); take(var()); seq = take(4)   # drop scriptsig
        ins.append((op, seq))
    nout = var()
    outs = []
    for _ in range(nout):
        val = take(8); spk = take(var()); outs.append((val, spk))
    lock = take(4)
    # reserialize with only vin_index carrying script_code
    from struct import pack
    def vi(n):
        return bytes([n]) if n < 0xfd else b"\xfd"+pack("<H",n)
    out = ver + vi(nin)
    for k,(op,seq) in enumerate(ins):
        sc = script_code if k == vin_index else b""
        out += op + vi(len(sc)) + sc + seq
    out += vi(nout)
    for val,spk in outs:
        out += val + vi(len(spk)) + spk
    out += lock + b"\x01\x00\x00\x00"       # SIGHASH_ALL
    return int.from_bytes(dsha(out), "big")


def sigs_from_tx(raw):
    """[(pubkey_hex, r, s, z)] for every standard legacy P2PKH input."""
    b = bytes.fromhex(raw) if isinstance(raw, str) else raw
    i = [0]
    def take(n): v = b[i[0]:i[0]+n]; i[0]+=n; return v
    def u32(): return int.from_bytes(take(4),"little")
    def var():
        n = take(1)[0]
        return n if n < 0xfd else int.from_bytes(take({0xfd:2,0xfe:4}.get(n,8)),"little")
    take(4)
    nin = var()
    scriptsigs = []
    for _ in range(nin):
        take(36); ss = take(var()); take(4)
        scriptsigs.append(ss)
    out = []
    for idx, ss in enumerate(scriptsigs):
        ps = pushes(ss)
        if len(ps) != 2:
            continue
        sig, pub = ps
        if not sig or sig[0] != 0x30 or len(pub) not in (33, 65):
            continue
        r, s = der_rs(sig[:-1])
        script_code = b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"
        z = legacy_sighash(b, idx, script_code)
        out.append((pub.hex(), r, s, z))
    return out


def recover(r, s1, z1, s2, z2):
    k = ((z1 - z2) * pow((s1 - s2) % N, -1, N)) % N
    d = ((s1 * k - z1) * pow(r, -1, N)) % N
    return d


def verify(d, pub_hex):
    try:
        from coincurve import PrivateKey
        return PrivateKey(d.to_bytes(32, "big")).public_key.format(True).hex() == pub_hex \
            or PrivateKey(d.to_bytes(32, "big")).public_key.format(False).hex() == pub_hex
    except Exception:
        return None            # cannot verify without coincurve


def wif(d, compressed=True):
    payload = b"\x80" + d.to_bytes(32, "big") + (b"\x01" if compressed else b"")
    B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    full = payload + dsha(payload)[:4]
    n = int.from_bytes(full, "big"); out = ""
    while n:
        n, m = divmod(n, 58); out = B58[m] + out
    return out


def scan(sig_records):
    """sig_records: [(pub, r, s, z)]. Return recovered [(pub, d, wif)]."""
    by = {}
    for pub, r, s, z in sig_records:
        by.setdefault((pub, r), []).append((s, z))
    found = []
    for (pub, r), lst in by.items():
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                (s1, z1), (s2, z2) = lst[a], lst[b]
                if z1 == z2 or s1 == s2:
                    continue
                try:
                    d = recover(r, s1, z1, s2, z2)
                except Exception:
                    continue
                if not (0 < d < N):
                    continue
                v = verify(d, pub)
                if v:
                    found.append((pub, d, wif(d)))
    return found


def selftest():
    ok = True
    try:
        from coincurve import PrivateKey
    except Exception:
        sys.stderr.write("  coincurve not importable -- recovery can run but "
                         "cannot self-verify. Install it. SELFTEST INCONCLUSIVE\n")
        return False
    # plant: one key signs two different messages with the SAME nonce
    d_true = int.from_bytes(hashlib.sha256(b"nonce reuse victim").digest(), "big") % N
    pk = PrivateKey(d_true.to_bytes(32, "big"))
    pub = pk.public_key.format(True).hex()
    k = int.from_bytes(hashlib.sha256(b"the reused nonce").digest(), "big") % N
    from coincurve import PublicKey
    # r = x-coord of k*G
    kG = PrivateKey(k.to_bytes(32, "big")).public_key.format(False)
    r = int.from_bytes(kG[1:33], "big") % N
    z1 = int.from_bytes(hashlib.sha256(b"message one").digest(), "big")
    z2 = int.from_bytes(hashlib.sha256(b"message two").digest(), "big")
    s1 = (pow(k, -1, N) * (z1 + r * d_true)) % N
    s2 = (pow(k, -1, N) * (z2 + r * d_true)) % N
    d_rec = recover(r, s1, z1, s2, z2)
    ok &= d_rec == d_true
    sys.stderr.write(f"  a planted reused nonce recovers the exact key: "
                     f"{'OK' if d_rec == d_true else 'FAIL'}\n")
    ok &= verify(d_rec, pub) is True
    sys.stderr.write(f"  the recovered key regenerates its pubkey: "
                     f"{'OK' if verify(d_rec, pub) else 'FAIL'}\n")
    got = scan([(pub, r, s1, z1), (pub, r, s2, z2)])
    ok &= len(got) == 1 and got[0][1] == d_true
    sys.stderr.write(f"  scan() finds it end-to-end and emits a WIF: "
                     f"{'OK' if got and got[0][1]==d_true else 'FAIL'}\n")
    # a NON-reused pair (different r) must yield nothing
    got2 = scan([(pub, r, s1, z1), (pub, (r+1) % N, s2, z2)])
    ok &= not got2
    sys.stderr.write(f"  different nonces yield nothing: "
                     f"{'OK' if not got2 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tx", action="append", default=[], help="raw tx hex")
    ap.add_argument("--cache", help="trace_cache.jsonl of Esplora tx JSON")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("cannot self-verify recovery; refusing to trust a null")
    if a.selftest:
        return

    recs = []
    for raw in a.tx:
        recs += sigs_from_tx(raw)
    if a.cache:
        import os
        if os.path.exists(a.cache):
            for l in open(a.cache):
                try:
                    _k, v = json.loads(l)
                except Exception:
                    continue
                # Esplora tx JSON carries no raw hex; skip unless it's hex
        sys.stderr.write("  (cache mode needs raw tx hex; Esplora JSON lacks "
                         "scriptSig bytes -- feed --tx hexes instead)\n")
    sys.stderr.write(f"\n  {len(recs)} legacy signatures extracted, "
                     f"{len(set((p,r) for p,r,_,_ in recs))} distinct (pubkey, r)\n")
    found = scan(recs)
    if found:
        for pub, d, w in found:
            sys.stderr.write(f"\n  *** KEY RECOVERED (verified) for {pub}\n"
                             f"      WIF {w}\n")
    else:
        sys.stderr.write("  no nonce reuse among these signatures.\n")


if __name__ == "__main__":
    main()
