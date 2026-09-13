#!/usr/bin/env python3
"""
Path-exhaustive HD derivation sweep against a SMALL target set.

WHY THIS IS NEW: every earlier brainwallet sweep checked derived addresses
against the full 56.8M-address funded index, but only tried a handful of
derivation paths (mostly seed[:32] direct, plus BIP44/49/84 receive-0). The
multimodal sweep even fell back to seed[:32] because bip_utils would not build.

Now the target set is ~116 addresses instead of 56.8 million, so we can afford
to explode the DERIVATION PATH dimension instead of the phrase dimension:
~72 paths x 5 seed schemes x 5 script types per phrase, versus ~4 before.

Use --direct-only to invert that trade for very large phrase corpora: it skips
HD path expansion (125 phrases/sec vs 6.9) once the path dimension has already
been covered by a deep run on a curated set.

BIP32 implemented directly on hmac-sha512 + coincurve, so there is no
dependency that can silently fail and degrade the search.

  python3 hd_sweep.py --phrases candidates_v2.txt --targets targets_all116.txt
  python3 hd_sweep.py --phrases big_corpus.txt --targets targets_all116.txt --direct-only
  python3 hd_sweep.py --selftest        # no network, must print SELFTEST PASS
"""
import argparse, hashlib, hmac, sys, unicodedata

try:
    from coincurve import PrivateKey, PublicKey
except ImportError:
    sys.exit("need coincurve:  pip install coincurve")

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


# ---------- encodings ----------
def b58check(payload):
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(payload + chk) - len((payload + chk).lstrip(b"\x00"))) + s


def h160(b):
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def _bech32_polymod(values):
    gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if ((top >> i) & 1) else 0
    return chk

def _bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def _convertbits(data, frombits, tobits, pad=True):
    acc = 0; bits = 0; ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    return ret

def bech32_encode(hrp, witver, witprog):
    data = [witver] + _convertbits(list(witprog), 8, 5)
    const = 0x2bc830a3 if witver else 1          # bech32m for v1+, bech32 for v0
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    chk = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(BECH32_CHARSET[d] for d in data + chk)


# ---------- address types ----------
def addr_p2pkh(pub):
    return b58check(b"\x00" + h160(pub))

def addr_p2sh_p2wpkh(pub):
    redeem = b"\x00\x14" + h160(pub)
    return b58check(b"\x05" + h160(redeem))

def addr_p2wpkh(pub):
    return bech32_encode("bc", 0, h160(pub))

def addr_p2tr(pub33):
    # BIP86: Q = lift_x(P) + tagged_hash("TapTweak", xonly(P)) * G
    # The internal key must be lifted to EVEN-Y before tweaking (BIP340/341).
    xonly = pub33[1:]
    tag = hashlib.sha256(b"TapTweak").digest()
    t = int.from_bytes(hashlib.sha256(tag + tag + xonly).digest(), "big")
    if t == 0 or t >= CURVE_N:
        return None
    P_even = PublicKey(b"\x02" + xonly)          # force even-Y internal key
    tweak_pt = PrivateKey(t.to_bytes(32, "big")).public_key
    out = PublicKey.combine_keys([P_even, tweak_pt]).format(compressed=True)
    return bech32_encode("bc", 1, out[1:])


def all_addrs(priv32):
    """Every address type for one private key."""
    try:
        sk = PrivateKey(priv32)
    except Exception:
        return []
    pc = sk.public_key.format(compressed=True)
    pu = sk.public_key.format(compressed=False)
    out = [addr_p2pkh(pc), addr_p2pkh(pu), addr_p2sh_p2wpkh(pc), addr_p2wpkh(pc)]
    try:
        t = addr_p2tr(pc)
        if t: out.append(t)
    except Exception:
        pass
    return out


# ---------- BIP32 ----------
def bip32_master(seed):
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return I[:32], I[32:]

def bip32_ckd(k, c, index):
    if index >= 0x80000000:
        data = b"\x00" + k + index.to_bytes(4, "big")
    else:
        pub = PrivateKey(k).public_key.format(compressed=True)
        data = pub + index.to_bytes(4, "big")
    I = hmac.new(c, data, hashlib.sha512).digest()
    kn = (int.from_bytes(I[:32], "big") + int.from_bytes(k, "big")) % CURVE_N
    if kn == 0:
        raise ValueError("invalid child")
    return kn.to_bytes(32, "big"), I[32:]

def parse_path(p):
    if p in ("m", ""): return []
    out = []
    for part in p.replace("m/", "").split("/"):
        if not part: continue
        if part.endswith("'") or part.endswith("h"):
            out.append(int(part[:-1]) + 0x80000000)
        else:
            out.append(int(part))
    return out

def derive(seed, path):
    k, c = bip32_master(seed)
    for idx in parse_path(path):
        k, c = bip32_ckd(k, c, idx)
    return k


# ---------- the path set ----------
def build_paths():
    paths = ["m"]
    for acct_prefix in ["m/44'/0'/0'", "m/49'/0'/0'", "m/84'/0'/0'", "m/86'/0'/0'"]:
        for change in (0, 1):
            for i in range(6):
                paths.append(f"{acct_prefix}/{change}/{i}")
    # account 1 as well, receive only
    for acct_prefix in ["m/44'/0'/1'", "m/84'/0'/1'"]:
        for i in range(3):
            paths.append(f"{acct_prefix}/0/{i}")
    # Electrum / bitcoin-core / older-wallet shapes
    for p in ["m/0", "m/0/0", "m/0/1", "m/1/0", "m/0'", "m/0'/0", "m/0'/0/0",
              "m/0'/0'", "m/0'/0'/0'", "m/1", "m/2", "m/44'/0'/0'",
              "m/49'/0'/0'", "m/84'/0'/0'", "m/32'", "m/0'/1", "m/1'/0"]:
        paths.append(p)
    return list(dict.fromkeys(paths))


# ---------- seed derivations from a phrase ----------
def seeds_from(phrase):
    b = phrase.encode("utf-8")
    nf = unicodedata.normalize("NFKD", phrase).encode("utf-8")
    return {
        "bip39":        hashlib.pbkdf2_hmac("sha512", nf, b"mnemonic", 2048),
        "bip39_pw_btc": hashlib.pbkdf2_hmac("sha512", nf, b"mnemonic" + b"bitcoin", 2048),
        "electrum":     hashlib.pbkdf2_hmac("sha512", nf, b"electrum", 2048),
        "raw":          b,
        "sha512":       hashlib.sha512(b).digest(),
    }

def direct_keys(phrase):
    b = phrase.encode("utf-8")
    d = {
        "sha256":   hashlib.sha256(b).digest(),
        "dsha256":  hashlib.sha256(hashlib.sha256(b).digest()).digest(),
        "sha512h":  hashlib.sha512(b).digest()[:32],
        "sha512l":  hashlib.sha512(b).digest()[32:],
        "sha3_256": hashlib.sha3_256(b).digest(),
        "blake2b":  hashlib.blake2b(b, digest_size=32).digest(),
        "keccak_like": hashlib.sha3_256(hashlib.sha256(b).digest()).digest(),
    }
    s = phrase.strip()
    if len(s) == 64:
        try: d["literal_hex"] = bytes.fromhex(s)
        except ValueError: pass
    return d


def selftest():
    ok = True
    # BIP39 canonical vector -> BIP44 m/44'/0'/0'/0/0
    m = ("abandon abandon abandon abandon abandon abandon "
         "abandon abandon abandon abandon abandon about")
    seed = hashlib.pbkdf2_hmac("sha512", m.encode(), b"mnemonic", 2048)
    got = addr_p2pkh(PrivateKey(derive(seed, "m/44'/0'/0'/0/0")).public_key.format(True))
    exp = "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"
    print(f"  BIP44 m/44'/0'/0'/0/0  {got}  {'OK' if got==exp else 'FAIL exp '+exp}")
    ok &= got == exp

    got = addr_p2wpkh(PrivateKey(derive(seed, "m/84'/0'/0'/0/0")).public_key.format(True))
    exp = "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu"
    print(f"  BIP84 m/84'/0'/0'/0/0  {got}  {'OK' if got==exp else 'FAIL exp '+exp}")
    ok &= got == exp

    got = addr_p2sh_p2wpkh(PrivateKey(derive(seed, "m/49'/0'/0'/0/0")).public_key.format(True))
    exp = "37VucYSaXLCAsxYyAPfbSi9eh4iEcbShgf"
    print(f"  BIP49 m/49'/0'/0'/0/0  {got}  {'OK' if got==exp else 'FAIL exp '+exp}")
    ok &= got == exp

    got = addr_p2tr(PrivateKey(derive(seed, "m/86'/0'/0'/0/0")).public_key.format(True))
    exp = "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"
    print(f"  BIP86 m/86'/0'/0'/0/0  {got}  {'OK' if got==exp else 'FAIL exp '+exp}")
    ok &= got == exp

    # brainwallet control
    got = addr_p2pkh(PrivateKey(hashlib.sha256(b"correct horse battery staple").digest())
                     .public_key.format(False))
    exp = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    print(f"  brainwallet uncompressed  {got}  {'OK' if got==exp else 'FAIL exp '+exp}")
    ok &= got == exp

    print("SELFTEST PASS" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases")
    ap.add_argument("--targets")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="hd_sweep_hits.txt")
    ap.add_argument("--direct-only", action="store_true",
                    help="skip HD path expansion; direct hashes only (~45x faster). "
                         "Use for very large phrase corpora where the path dimension "
                         "is already covered by a deep run on a curated set.")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.phrases or not a.targets:
        sys.exit("need --phrases and --targets (or --selftest)")

    targets = set()
    for l in open(a.targets):
        l = l.strip().split(",")[0].split("\t")[0]
        if l and not l.startswith("#") and l != "address":
            targets.add(l)
    phrases = [l.rstrip("\n") for l in open(a.phrases) if l.strip()]
    paths = [] if a.direct_only else build_paths()

    per = len(paths) * len(seeds_from("x")) + len(direct_keys("x"))
    sys.stderr.write(f"targets: {len(targets)}\nphrases: {len(phrases):,}\n"
                     f"paths:   {len(paths)}{' (DIRECT-ONLY MODE)' if a.direct_only else ''}\n")
    sys.stderr.write(f"~{len(phrases) * per * 5:,} address checks\n\n")

    hits = open(a.out, "w")
    n = 0
    for pi, phrase in enumerate(phrases, 1):
        cands = []
        for label, k in direct_keys(phrase).items():
            cands.append((f"direct:{label}", k))
        for sname, seed in seeds_from(phrase).items():
            for p in paths:
                try:
                    cands.append((f"{sname}:{p}", derive(seed, p)))
                except Exception:
                    pass
        for label, k in cands:
            for ad in all_addrs(k):
                n += 1
                if ad in targets:
                    line = f"*** HIT *** {ad}  phrase={phrase!r}  derivation={label}  priv={k.hex()}\n"
                    sys.stdout.write(line); sys.stdout.flush()
                    hits.write(line); hits.flush()
        if pi % 25 == 0:
            sys.stderr.write(f"  {pi}/{len(phrases)} phrases, {n:,} addresses checked\n")
            sys.stderr.flush()
    hits.close()
    sys.stderr.write(f"\nDONE. {n:,} addresses checked against {len(targets)} targets -> {a.out}\n")


if __name__ == "__main__":
    main()
