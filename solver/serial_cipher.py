#!/usr/bin/env python3
"""
The serial as CIPHERTEXT, not key material: decodings of CL 76841714 A / L12
and KB 46279860, and the two notes as Key A and Key B of a multisig.

Every prior framing hashes the serial. This one asks what it DECODES to:

  base-N      CL76841714A is a valid base58 string (KB46279860 is not: '0');
              base58 / base36 / base62 decodings of each string, as decimal,
              hex and raw 32-byte keys
  Roman       CL = 150, L = 50 (the L12 seal); with the digits
  El Salvador the 8-digit numbers in Salvadoran formats: +503 mobile numbers
              (76841714 has a valid mobile prefix), wa.me links, DUI with its
              real check digit (both serials check to 5), dotted IPv4
  shifts      digit-wise Caesar (+-1..9, x3, x7 mod 10) and digit-wise
              Vigenere with the clue words as key streams (A1Z26 mod 10 and
              phone-keypad digit maps): El Salvador, OVERDOSE, BITCOIN, KEISER,
              BUKELE, GEORGE SAND, LEONARDO, MIRROR, SATOSHI
  elements    CL -> Cl 17; K 19, B 5 (the pills)
  ordinals    each number as a sat: its ordinal NAME
  multisig    "keyS" plural, suffix A and prefix KB: the two serials as two
              keys -> 1-of-2 and 2-of-2 (P2SH, P2WSH, P2SH-P2WSH; compressed
              and uncompressed; both orders and BIP-67 sorted) across the 7
              hash derivations, and 2-of-3 with an El Salvador / OVERDOSE /
              Max Keiser third key -- queried against the index directly

  python3 serial_cipher.py            # plugin forms() + the multisig family
  python3 serial_cipher.py --selftest
"""
import argparse, hashlib, itertools, sys

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
A_STR, A_D, B_STR, B_D, L12 = "CL76841714A", "76841714", "KB46279860", "46279860", "L12"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CLUE_KEYS = ["El Salvador", "OVERDOSE", "BITCOIN", "KEISER", "MAX KEISER", "BUKELE", "GEORGE SAND",
             "LEONARDO", "MIRROR", "SATOSHI", "SAND", "NAYIB"]
KEYPAD = {c: d for d, letters in {"2": "ABC", "3": "DEF", "4": "GHI", "5": "JKL", "6": "MNO", "7": "PQRS",
                                  "8": "TUV", "9": "WXYZ"}.items() for c in letters}


def decode_base(s, alphabet):
    n = 0
    for c in s:
        if c not in alphabet: return None
        n = n * len(alphabet) + alphabet.index(c)
    return n

def dui_check(d8):
    s = sum(int(c) * w for c, w in zip(d8, range(9, 1, -1)))
    return (10 - s % 10) % 10

def sat_name(sat):
    x = 2099999997690000 - sat
    out = []
    while x > 0:
        out.append("abcdefghijklmnopqrstuvwxyz"[(x - 1) % 26]); x = (x - 1) // 26
    return "".join(reversed(out))

def key_stream(word, mode):
    ds = []
    for c in word.upper():
        if not c.isalpha(): continue
        ds.append(str((ord(c) - 64) % 10) if mode == "a1z26" else KEYPAD.get(c, "0"))
    return "".join(ds)

def shift(digits, stream, op):
    return "".join(str(op(int(d), int(stream[i % len(stream)])) % 10) for i, d in enumerate(digits))


def forms():
    out = []
    def add(tag, v):
        if v: out.append((tag, str(v)))
    def num(tag, n):
        if n is None: return
        add(tag + "/dec", n); add(tag + "/hex", format(n, "x"))
        if 0 < n < N: add(tag + "/key", "hex:" + n.to_bytes(32, "big").hex())
    # base-N decodings
    for name, s in (("A", A_STR), ("Ad", A_D), ("B", B_STR), ("Bd", B_D), ("L12", L12), ("AB", A_STR + B_STR),
                    ("A+L12", A_STR + L12), ("AKB", A_STR + "KB"), ("BA", B_STR + A_STR)):
        num(f"b58({name})", decode_base(s, B58))
        num(f"b36({name})", int(s, 36) if all(c.isalnum() for c in s) else None)
        num(f"b62({name})", decode_base(s, B62))
        num(f"b16({name})", int(s, 16) if all(c in "0123456789abcdefABCDEF" for c in s) else None)
    # Roman
    for v in ("150", "CL 150", "150 76841714", "76841714 150", "15076841714", "76841714150", "50 12", "5012",
              "L12 50 12", "150 50 12", "1505012", "150 76841714 50 12", "CL=150", "C=100 L=50", "100 50 76841714",
              "10050768417141", "150 76841714 A", "150768417141"):
        add("roman/" + v, v)
    # El Salvador formats
    for name, d in (("A", A_D), ("B", B_D)):
        for v in (f"+503{d}", f"503{d}", f"+503 {d[:4]} {d[4:]}", f"+503 {d[:4]}-{d[4:]}", f"{d[:4]}-{d[4:]}",
                  f"{d[:4]} {d[4:]}", f"(503) {d[:4]}-{d[4:]}", f"00503{d}", f"https://wa.me/503{d}", f"wa.me/503{d}",
                  f"tel:+503{d}", f"{d}-{dui_check(d)}", f"DUI {d}-{dui_check(d)}", f"{d}{dui_check(d)}",
                  f"{d[:2]}.{d[2:4]}.{d[4:6]}.{d[6:]}", f"{d[:1]}.{d[1:3]}.{d[3:6]}.{d[6:]}",
                  f"http://{d[:2]}.{d[2:4]}.{d[4:6]}.{d[6:]}", f"{d} El Salvador", f"El Salvador +503 {d}"):
            add(f"sv/{name}/" + v, v)
    add("sv/AB/phones", f"+503{A_D} +503{B_D}"); add("sv/AB/dui", f"{A_D}-{dui_check(A_D)} {B_D}-{dui_check(B_D)}")
    add("sv/AB/ipv4", f"{A_D[:2]}.{A_D[2:4]}.{A_D[4:6]}.{A_D[6:]} {B_D[:2]}.{B_D[2:4]}.{B_D[4:6]}.{B_D[6:]}")
    # digit-wise shifts and Vigenere with clue key streams
    for name, d in (("A", A_D), ("B", B_D), ("AB", A_D + B_D), ("BA", B_D + A_D)):
        for k in range(1, 10):
            add(f"caesar/{name}/+{k}", shift(d, str(k), lambda p, q: p + q))
            add(f"caesar/{name}/-{k}", shift(d, str(k), lambda p, q: p - q))
        for m in (3, 7, 9):
            add(f"mul/{name}/x{m}", "".join(str(int(c) * m % 10) for c in d))
        add(f"compl9/{name}", "".join(str(9 - int(c)) for c in d))
        add(f"compl10/{name}", "".join(str((10 - int(c)) % 10) for c in d))
        for kw in CLUE_KEYS:
            for mode in ("a1z26", "keypad"):
                ks = key_stream(kw, mode)
                add(f"vig/{name}/{kw}/{mode}/+", shift(d, ks, lambda p, q: p + q))
                add(f"vig/{name}/{kw}/{mode}/-", shift(d, ks, lambda p, q: p - q))
                add(f"vig/{name}/{kw}/{mode}/rev-", shift(ks[:len(d)].ljust(len(d), "0"), d, lambda p, q: p - q))
    # the other serial as the key stream (digit-wise) -- both directions, all ops
    add("vig/A_by_B/+", shift(A_D, B_D, lambda p, q: p + q)); add("vig/A_by_B/-", shift(A_D, B_D, lambda p, q: p - q))
    add("vig/B_by_A/-", shift(B_D, A_D, lambda p, q: p - q))
    # elements
    for v in ("Cl 17", "17", "17 76841714", "1776841714", "76841714 17", "K 19 B 5", "195", "19 5 46279860",
              "19546279860", "chlorine", "potassium boron", "Cl K B", "17 19 5", "17195", "17 76841714 19 5 46279860"):
        add("element/" + v, v)
    # ordinal sat names
    for name, n in (("A", int(A_D)), ("B", int(B_D)), ("AB", int(A_D + B_D)), ("Ahex", int(A_D, 16)), ("Bhex", int(B_D, 16))):
        if n < 2099999997690000:
            add(f"sat/{name}/name", sat_name(n)); add(f"sat/{name}/nameA", sat_name(n) + " " + A_STR)
    add("sat/AB/names", sat_name(int(A_D)) + " " + sat_name(int(B_D)))
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq


# ---------------------------------------------------------------- multisig
def multisig_spks():
    """(tag, spk) for the two serials as two keys of a multisig, plus 2-of-3."""
    from coincurve import PrivateKey
    from hd_sweep import direct_keys
    from spk_extra import sc_multisig, p2sh, p2wsh
    def pubs(k):
        pk = PrivateKey(k).public_key
        return pk.format(compressed=True), pk.format(compressed=False)
    def keyset(s):
        return {h: k for h, k in direct_keys(s).items() if 0 < int.from_bytes(k, "big") < N}
    A = {("Astr", h): k for h, k in keyset(A_STR).items()}; A.update({("Ad", h): k for h, k in keyset(A_D).items()})
    B = {("Bstr", h): k for h, k in keyset(B_STR).items()}; B.update({("Bd", h): k for h, k in keyset(B_D).items()})
    third = {w: keyset(w)["sha256"] for w in ("El Salvador", "OVERDOSE", "Max Keiser", "bitcoin")}
    out = []
    def emit(tag, m, plist):
        script = sc_multisig(m, plist)
        out.append((f"{tag}|p2sh", p2sh(script)))
        out.append((f"{tag}|p2wsh", p2wsh(script)))
        out.append((f"{tag}|p2sh-p2wsh", p2sh(p2wsh(script))))
    for (an, ah), ak in A.items():
        for (bn, bh), bk in B.items():
            if ah != bh and not (ah == "sha256" or bh == "sha256"): continue   # same hash, or sha256 x any
            for ci, fmt in ((0, "c"), (1, "u")):
                pa, pb = pubs(ak)[ci], pubs(bk)[ci]
                for m in (1, 2):
                    emit(f"{m}of2:{an}/{ah}+{bn}/{bh}:{fmt}:AB", m, [pa, pb])
                    emit(f"{m}of2:{an}/{ah}+{bn}/{bh}:{fmt}:BA", m, [pb, pa])
                    emit(f"{m}of2:{an}/{ah}+{bn}/{bh}:{fmt}:sorted", m, sorted([pa, pb]))
                if fmt == "c" and ah == bh:
                    for w, tk in third.items():
                        pt = pubs(tk)[0]
                        emit(f"2of3:{an}/{ah}+{bn}+{w}:ABT", 2, [pa, pb, pt])
                        emit(f"2of3:{an}/{ah}+{bn}+{w}:sorted", 2, sorted([pa, pb, pt]))
                        emit(f"1of3:{an}/{ah}+{bn}+{w}:sorted", 1, sorted([pa, pb, pt]))
    return out


def selftest():
    ok = True
    ok &= decode_base("CL76841714A", B58) is not None and decode_base("KB46279860", B58) is None
    ok &= dui_check("76841714") == 5 and dui_check("46279860") == 5
    ok &= sat_name(0) == "nvtdijuwxlp" and sat_name(2099999997689999) == "a"
    ok &= shift("76841714", "1", lambda p, q: p + q) == "87952825"
    ok &= key_stream("El Salvador", "a1z26") == "5291221458"
    F = forms(); tags = [t for t, _ in F]
    ok &= len(set(tags)) == len(tags) and all(v for _, v in F) and len(F) > 300
    ms = multisig_spks()
    ok &= len(ms) > 1000 and all(isinstance(s, (bytes, bytearray)) and s[:1] in (b"\xa9", b"\x00") for _, s in ms)
    print(f"  {len(F)} decoding forms; {len(ms):,} multisig scripts; base58(CL76841714A) = {decode_base(A_STR, B58)}")
    return bool(ok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not selftest(): sys.exit("selftest FAIL")
    if a.selftest: return
    import continuous_solver as CS
    orc = CS.IndexOracle()
    if not orc.ready: sys.exit(f"no oracle: {orc.why}")
    if not orc.control(): sys.exit("positive control failed")
    ms = multisig_spks()
    # planted control: a multisig of the genesis-key form cannot be planted, so plant the genesis spk itself
    from index_oracle import spk_from_address
    g = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    hits = orc.check([s for _, s in ms] + [g])
    tags = [t for t, _ in ms] + ["PLANT"]
    real = [(tags[j], bal) for j, bal in hits if tags[j] != "PLANT"]
    plant_ok = any(tags[j] == "PLANT" for j, _ in hits)
    print(f"  multisig: {len(ms):,} scripts vs {orc.name}: {len(real)} hit(s); planted control "
          f"{'found' if plant_ok else 'MISSING -- null void'}")
    for t, bal in real: print(f"  *** INDEX HIT {bal} sats :: {t}")


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest()) if "--selftest" in sys.argv else main()
