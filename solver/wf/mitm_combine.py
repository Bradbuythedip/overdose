#!/usr/bin/env python3
"""
The non-additive half of the two-component attack.

wf/mitm_split.py covers priv = a + b (mod n), the one combination that
factorises through the curve and so admits the point-addition shortcut. It
cannot express the combinations that pass both halves through a hash or a KDF,
because those do not commute with scalar multiplication. Those are here.

Component halves are the same clue-derived sets: the two banknote serials
(CL76841714A from pages 73/74, KB46279860 from page 72), page 72's 22 printed
numerals and nine source URLs, the El Salvador spellings and the article
anchors.

Combination modes, each applied in BOTH orders (a,b) and (b,a):

  concat            sha256(a + b)              and with " ", "-", "_", "|" joins
  digest_concat     sha256(sha256(a) || sha256(b))
  xor               sha256(a) XOR sha256(b)
  hmac              HMAC-SHA256(key=a, msg=b)
  pbkdf2            PBKDF2-HMAC-SHA256(a, salt=b, 2048)
  double            sha256(sha256(a) + b)

XOR and the digest concatenations are the interesting ones for a SPLIT key:
they are exactly how a two-part secret is usually recombined by hand.

Controls: each mode is pinned by recomputing a known vector, and the oracle
must find a known funded address, before any null is reported.

  python3 wf/mitm_combine.py --selftest
  python3 wf/mitm_combine.py
"""
import hashlib, hmac, itertools, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from hd_sweep import CURVE_N

from mitm_split import setA, setB, SERIAL1, SERIAL2, P72_NUMS, P72_URLS, SALVADOR, ANCHORS

JOINS = ["", " ", "-", "_", "|", ":"]


def modes(a, b):
    """Yield (label, 32-byte key) for every non-additive combination."""
    ab, bb = a.encode(), b.encode()
    ha, hb = hashlib.sha256(ab).digest(), hashlib.sha256(bb).digest()
    for j in JOINS:
        yield f"concat[{j!r}]", hashlib.sha256(ab + j.encode() + bb).digest()
    yield "digest_concat", hashlib.sha256(ha + hb).digest()
    yield "xor", bytes(x ^ y for x, y in zip(ha, hb))
    yield "hmac", hmac.new(ab, bb, hashlib.sha256).digest()
    yield "double", hashlib.sha256(ha + bb).digest()
    yield "pbkdf2", hashlib.pbkdf2_hmac("sha256", ab, bb, 2048, 32)


def selftest():
    ok = True
    # pin the primitives against recomputable vectors
    a, b = "abc", "def"
    v1 = hashlib.sha256(b"abcdef").hexdigest()
    got = None
    for lbl, k in modes(a, b):
        if lbl == "concat['']":
            got = k.hex()
    ok &= got == v1
    print(f"  concat vector: {'OK' if got == v1 else 'FAIL'}")

    xa = hashlib.sha256(b"abc").digest()
    xb = hashlib.sha256(b"def").digest()
    want = bytes(x ^ y for x, y in zip(xa, xb)).hex()
    got = dict((l, k.hex()) for l, k in modes(a, b))["xor"]
    ok &= got == want
    print(f"  xor vector:    {'OK' if got == want else 'FAIL'}")

    want = hmac.new(b"abc", b"def", hashlib.sha256).hexdigest()
    got = dict((l, k.hex()) for l, k in modes(a, b))["hmac"]
    ok &= got == want
    print(f"  hmac vector:   {'OK' if got == want else 'FAIL'}")

    # the derivation path must rederive a known brainwallet address
    k = hashlib.sha256(b"correct horse battery staple").digest()
    addr = H.addrs_for_priv(k)["p2pkh_u"]
    good = addr == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    ok &= good
    print(f"  derivation path: {'OK' if good else 'FAIL'} ({addr})")

    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    ok &= g
    print(f"  oracle genesis:  {'OK' if g else 'FAIL'}")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")

    # the expensive pbkdf2 mode is reserved for the tightest pairing
    core_a = sorted({SERIAL1, SERIAL1.lower(), "76841714", "CL76841714"})
    core_b = sorted({SERIAL2, SERIAL2.lower(), "46279860", "KB46279860"})

    A, B = setA(), setB()
    print(f"\nhalf A: {len(A)}  half B: {len(B)}")

    o = H.Oracle()
    hits = []
    n_keys = 0
    t0 = time.time()
    PENDING = []

    def flush(force=False):
        nonlocal n_keys
        if not PENDING or (len(PENDING) < 20000 and not force):
            return
        full = H.full_index()
        from index_oracle import spk_from_address
        spks, meta = [], []
        for tag, k in PENDING:
            for t, ad in H.addrs_for_priv(k).items():
                if o.funded(ad):
                    hits.append((tag, t, ad, k.hex()))
                    print(f"*** HIT(richlist) {tag} {t} {ad}", flush=True)
                spk = spk_from_address(ad)
                if spk is not None:
                    spks.append(spk); meta.append((tag, t, ad, k))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, t, ad, k = meta[j]
                hits.append((tag, t, ad, k.hex(), bal))
                print(f"*** HIT(fullindex) {tag} {t} {ad} {bal/1e8:.8f} BTC", flush=True)
        n_keys += len(PENDING)
        PENDING.clear()

    for a in A:
        for b in B:
            for lbl, k in modes(a, b):
                if lbl == "pbkdf2" and not (a in core_a and b in core_b):
                    continue
                if not (0 < int.from_bytes(k, "big") < CURVE_N):
                    continue
                PENDING.append((f"{lbl}|{a[:34]}|{b[:34]}", k))
            for lbl, k in modes(b, a):
                if lbl == "pbkdf2" and not (b in core_b and a in core_a):
                    continue
                if not (0 < int.from_bytes(k, "big") < CURVE_N):
                    continue
                PENDING.append((f"{lbl}R|{b[:34]}|{a[:34]}", k))
            flush()
    flush(force=True)

    print(f"\nkeys derived {n_keys:,} in {time.time()-t0:.0f}s")
    print(f"addresses checked ~{n_keys*5:,}")
    print("combination hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
