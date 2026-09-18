#!/usr/bin/env python3
"""
LENS: Bitcoin wallet-format cryptographer. Every wallet-ENCODING convention by
which two short secrets -- the 11-char CL76841714A and the 10-char KB46279860,
or the two 8-digit numbers 76841714 and 46279860 -- get folded into ONE key,
that serial_combine.py's pairing/entropy families do not already perform.

WHAT IT ADDS (family tag prefixes in brackets)
  [e2]    Electrum 2.x seed phrases: Electrum's own mnemonic_encode (integer ->
          little-endian base-2048 words) of each combined integer reading, the
          raw encoding AND Electrum's make_seed convention (entropy + nonce until
          the "Seed version" HMAC prefix is 01/standard or 100/segwit), plus the
          root key / m/0/0 / m/0'/0/0 of each as 32-byte hex: raw keys.
          Version-prefix and BIP-39-checksum status appear in TAGS only; nothing
          is filtered on them.
  [e1]    Electrum 1.x hex seeds (24 and 32 hex from the digits: tiled, zero-
          padded both ends and centred, interleaved, A*2+B*2, ABBA) as hex:
          values, plus the 100,000-round stretch_key secexp and the first
          receive/change keys ((secexp + sha256d("n:c:" + mpk)) mod N).
  [mini]  Casascius mini-key-shaped strings: 'S' + 21 or 29 chars built from
          the serials. SCL76841714AKB46279860 is exactly 22 chars. Material
          only; sha256(string) IS the mini-key rule, and the sweep does that.
  [bw]    bitaddress / brainwallet.org-era typing artefacts: passphrase with
          trailing '\\n', '\\r\\n', space, tab, NUL, leading space/newline, a
          UTF-8 BOM, repeated 2x/3x (bare and space/newline-joined), UTF-16LE
          bytes, and sha256 iterated 3/10/100/1e3/1e4/1e5 times as hex: keys.
  [b39g]  BIP-39 phrases whose 12 words are the 16 digits read as wordlist
          indices under EVERY contiguous grouping into 12 parts of 1-4 digits
          (1,353 groupings per source; sources ab, ba, both reversals, both
          interleavings; base 0 and base 1; out-of-range groupings dropped, no
          mod-2048 wrap), and 24-digit sources (serials + series years) as 24
          singles and 12 pairs. Phrase text only; the sweep checksum-tests
          12/24-word text. Digit-grouping phrases that pass Electrum's prefix
          also get [e2g] root/m/0/0/m/0'/0/0 keys.
  [xprv]  BIP-32 from the digit BYTES (BCD, packed 32-bit ints BE/LE, hex ints)
          as the HMAC "Bitcoin seed" input -> master + 7 first-address paths as
          raw keys; and COMPOSITE extended keys where one serial supplies the
          private key and the other the chain code (sha256 / tiled BCD / ASCII
          readings), children m/0, m/0/0, m/0', m/1/0, m/0'/0/0. The xprv
          base58 strings and 78-byte payloads are emitted too.
  [path]  the digits as BIP-32 child indices: 'path:m/76841714/46279860', the
          4/2/1-digit splits, hex readings, letter values, standard-purpose
          prefixes, hardened variants -- for the orchestrator's path support.
  [raw]   raw-key placements: the two 32-bit values as halves of a 32-byte key
          at every 4-byte-aligned pair of ends/middles, BE and LE, decimal and
          hex readings; the 16 ASCII digit bytes at offsets 0 and 16 (zero- and
          '0'-padded); each 8-byte ASCII serial at every 8-aligned offset pair;
          the two full serial strings zero-padded to 32 bytes.
  [bip38] SPECULATIVE: BIP-38 EC-multiply passfactor, scrypt(passphrase,
          ownersalt=other serial's 8 ASCII digits, N=16384, r=8, p=8).
  [armory] SPECULATIVE, reconstructed from memory of Armory's chained
          derivation (newpriv = priv * (sha256d(pubkey65) XOR chaincode) mod N,
          chaincode = HMAC-SHA256(sha256d(root), 'Derive Chaincode from Root
          Key')); no offline vector confirms it, so treat as low-prior.

DELIBERATELY OMITTED because an existing module covers it
  sha256 / dsha256 / sha512 / sha3 / blake2b of the plain concatenations and
  separators, both orders, cases, reversal, rot180, mirror  -- serial_combine
  string_forms + clue_serial; HMAC / PBKDF2 / scrypt(r=8,p=1) / WarpWallet one
  serial keyed by the other -- serial_combine pairing_forms; BCD/ASCII/int
  readings tiled or padded to 16/32 bytes as BIP-39 ENTROPY and their 9
  passphrases x 72 paths -- serial_combine entropy_forms (single-serial tiles:
  gen_serial_entropy_bip39); the 64-bit a<<32|b and decimal-concat integers as
  raw keys and their LE/BE 4/8/16-byte pads -- serial_combine numeric_forms
  (a few of the [raw] end-placements coincide with those and are kept for
  completeness of the placement grid); ASCII strings as raw BIP-32 seeds and
  the 5 seed types x 72 paths -- serial_combine hd() over string_forms; uniform
  pair/single index readings of ABA/BAB and mod-2048 wraps -- serial_combine
  text_index_forms and serial2_exhaust framing F; RNG-seeded keys --
  serial_entropy; serial-as-checksum -- serial_oracle / serial_bip39_mine (no
  new predicates here); tiled 64-hex literal keys -- serial_combine discovery
  (tile2 twice). Electrum 1.x's 1626-word mnemonic is not reproduced (wordlist
  not in the repo); its hex seed is the wallet's actual secret and is covered.

  python3 combo_walletformats.py
"""
import hashlib, hmac, itertools

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
A_D, B_D = "76841714", "46279860"
A_STR, B_STR = "CL76841714A", "KB46279860"
a, b = int(A_D), int(B_D)
ah, bh = int(A_D, 16), int(B_D, 16)
AB, BA = A_D + B_D, B_D + A_D

try:
    from bip39_index import WL
except Exception:                       # pragma: no cover
    from mnemonic import Mnemonic
    WL = Mnemonic("english").wordlist
try:
    from mnemonic import Mnemonic as _M
    _MNE = _M("english")
except Exception:                       # pragma: no cover
    _MNE = None
try:
    from hd_sweep import PrivateKey, bip32_master, bip32_ckd, derive, b58check
    _EC = True
except Exception:                       # pragma: no cover
    _EC = False


# ---------------------------------------------------------------- helpers
def sha256d(x):
    return hashlib.sha256(hashlib.sha256(x).digest()).digest()

def interleave(x, y):
    return "".join(p + q for p, q in zip(x, y)) + x[len(y):] + y[len(x):]

def tile(s, n):
    return (s * (n // len(s) + 1))[:n]

def hx(bs):
    return "hex:" + bs.hex()

def electrum_encode(i):
    """Electrum's Mnemonic.mnemonic_encode: little-endian base-2048 words."""
    words = []
    while i:
        i, x = divmod(i, 2048)
        words.append(WL[x])
    return " ".join(words)

def electrum_prefix(phrase):
    """Electrum seed_type: which version prefix the 'Seed version' HMAC has."""
    h = hmac.new(b"Seed version", phrase.encode(), hashlib.sha512).hexdigest()
    for p in ("01", "100", "101", "102"):
        if h.startswith(p):
            return p
    return None

def electrum_make_seed(i, prefix, limit=8192):
    """Electrum make_seed: mnemonic_encode(entropy + nonce), first nonce whose
    seed carries the wanted prefix. Returns (nonce, phrase) or None."""
    for nonce in range(1, limit):
        ph = electrum_encode(i + nonce)
        if ph and electrum_prefix(ph) == prefix:
            return nonce, ph
    return None

def electrum_root(phrase, passphrase=""):
    return hashlib.pbkdf2_hmac("sha512", phrase.encode(), b"electrum" + passphrase.encode(), 2048)

def bip39_ok(phrase):
    if _MNE is None or len(phrase.split()) not in (12, 15, 18, 21, 24):
        return False
    try:
        return bool(_MNE.check(phrase))
    except Exception:
        return False

def flags(phrase):
    f = []
    p = electrum_prefix(phrase)
    if p: f.append("e2v=" + p)
    if bip39_ok(phrase): f.append("b39ok")
    return ("[" + ",".join(f) + "]") if f else ""

def stretch1x(hexseed):
    """Electrum 1.x stretch_key: 100,000 x sha256(seed || original), seed as
    the ASCII hex string; returns the integer exponent."""
    s = hexseed.encode(); o = s
    for _ in range(100000):
        s = hashlib.sha256(s + o).digest()
    return int.from_bytes(s, "big")

def e1x_address_key(secexp, n, for_change):
    mpk = PrivateKey(secexp.to_bytes(32, "big")).public_key.format(compressed=False)[1:]
    seq = int.from_bytes(sha256d(f"{n}:{for_change}:".encode() + mpk), "big")
    return (secexp + seq) % N

def compositions(total, parts, mx=4):
    if parts == 1:
        if 1 <= total <= mx:
            yield (total,)
        return
    for f in range(1, min(mx, total - (parts - 1)) + 1):
        for r in compositions(total - f, parts - 1, mx):
            yield (f,) + r

def group_words(digits, comp, base):
    out, i = [], 0
    for L in comp:
        v = int(digits[i:i + L]) - base; i += L
        if not (0 <= v < 2048):
            return None
        out.append(WL[v])
    return " ".join(out)

def key_ok(k):
    return 0 < int.from_bytes(k, "big") < N

def xprv_payload(k, c, depth=0, fp=b"\0\0\0\0", child=0):
    return bytes.fromhex("0488ade4") + bytes([depth]) + fp + child.to_bytes(4, "big") + c + b"\0" + k

def ckd_path(k, c, path):
    for part in path.split("/")[1:]:
        idx = int(part.rstrip("'")) + (0x80000000 if part.endswith("'") else 0)
        k, c = bip32_ckd(k, c, idx)
    return k

def armory_next(priv32):
    cc = hmac.new(sha256d(priv32), b"Derive Chaincode from Root Key", hashlib.sha256).digest()
    pub = PrivateKey(priv32).public_key.format(compressed=False)
    mult = int.from_bytes(bytes(p ^ q for p, q in zip(sha256d(pub), cc)), "big")
    return ((int.from_bytes(priv32, "big") * mult) % N).to_bytes(32, "big")


# ---------------------------------------------------------------- families
def _int_readings():
    asc = lambda s: int.from_bytes(s.encode(), "big")
    bcd = lambda s: int(s, 16)
    return [
        ("ab", int(AB)), ("ba", int(BA)), ("rev_ab", int(AB[::-1])), ("rev_ba", int(BA[::-1])),
        ("il_ab", int(interleave(A_D, B_D))), ("il_ba", int(interleave(B_D, A_D))),
        ("a<<32|b", (a << 32) | b), ("b<<32|a", (b << 32) | a),
        ("ah<<32|bh", (ah << 32) | bh), ("bh<<32|ah", (bh << 32) | ah),
        ("ascii16_ab", asc(AB)), ("ascii16_ba", asc(BA)),
        ("bcd_ab", bcd(AB)), ("bcd_ba", bcd(BA)),
        ("bcd_abx2", bcd(AB * 2)), ("bcd_bax2", bcd(BA * 2)),
        ("a+b", a + b), ("a*b", a * b), ("a^b", a ^ b), ("|a-b|", abs(a - b)),
    ]

def fam_electrum2(add):
    def emit_keys(tag, ph, pw=""):
        if not _EC: return
        root = electrum_root(ph, pw)
        k, c = bip32_master(root)
        add(f"{tag}/root", hx(k))
        add(f"{tag}/m0.0", hx(ckd_path(k, c, "m/0/0")))
        add(f"{tag}/m0.1", hx(ckd_path(k, c, "m/0/1")))
        add(f"{tag}/m1.0", hx(ckd_path(k, c, "m/1/0")))
        add(f"{tag}/m0h.0.0", hx(ckd_path(k, c, "m/0'/0/0")))
    for nm, i in _int_readings():
        ph = electrum_encode(i)
        if not ph: continue
        add(f"e2:enc:{nm}{flags(ph)}", ph)
        emit_keys(f"e2:enc:{nm}", ph)
        for pfx, pname in (("01", "std"), ("100", "sw")):
            r = electrum_make_seed(i, pfx)
            if r:
                nonce, ph2 = r
                add(f"e2:mk_{pname}:{nm}+{nonce}", ph2)
                emit_keys(f"e2:mk_{pname}:{nm}+{nonce}", ph2)
    # single-serial encodings joined, and each with the OTHER serial as the
    # Electrum passphrase (the "seed extension")
    wa, wb = electrum_encode(a), electrum_encode(b)
    add(f"e2:enc:a|b{flags(wa + ' ' + wb)}", wa + " " + wb)
    add(f"e2:enc:b|a{flags(wb + ' ' + wa)}", wb + " " + wa)
    emit_keys("e2:enc:a|b", wa + " " + wb); emit_keys("e2:enc:b|a", wb + " " + wa)
    for tag, ph, pw in (("a_pwB", wa, B_STR), ("a_pwBd", wa, B_D),
                        ("b_pwA", wb, A_STR), ("b_pwAd", wb, A_D)):
        emit_keys(f"e2:enc:{tag}", ph, pw)

def fam_electrum1(add):
    z = "0"
    seeds32 = {
        "ab_x2": AB * 2, "ba_x2": BA * 2, "ab_rpad": AB + z * 16, "ab_lpad": z * 16 + AB,
        "ba_rpad": BA + z * 16, "ba_lpad": z * 16 + BA, "ab_centre": z * 8 + AB + z * 8,
        "a2b2": A_D * 2 + B_D * 2, "b2a2": B_D * 2 + A_D * 2, "abba": A_D + B_D + B_D + A_D,
        "baab": B_D + A_D + A_D + B_D, "il_ab_x2": interleave(A_D, B_D) * 2,
        "il_ba_x2": interleave(B_D, A_D) * 2, "a_x4": A_D * 4, "b_x4": B_D * 4,
        "rev_ab_x2": AB[::-1] * 2,
    }
    seeds24 = {
        "aba": A_D + B_D + A_D, "bab": B_D + A_D + B_D, "ab_rpad": AB + z * 8,
        "ab_lpad": z * 8 + AB, "ba_rpad": BA + z * 8, "ba_lpad": z * 8 + BA,
        "a_x3": A_D * 3, "b_x3": B_D * 3, "il_ab_rpad": interleave(A_D, B_D) + z * 8,
    }
    for size, seeds in ((32, seeds32), (24, seeds24)):
        for nm, hs in seeds.items():
            assert len(hs) == size, (nm, hs)
            add(f"e1:seed{size}:{nm}", "hex:" + hs)
            sec = stretch1x(hs)
            if not (0 < sec < N): continue
            add(f"e1:secexp{size}:{nm}", hx(sec.to_bytes(32, "big")))
            if _EC:
                for n_, fc in ((0, 0), (1, 0), (0, 1)):
                    add(f"e1:addr{size}:{nm}/{fc}:{n_}", hx(e1x_address_key(sec, n_, fc).to_bytes(32, "big")))

def fam_minikey(add):
    ilab = interleave(A_D, B_D)
    cands = {
        "full_ab": "S" + A_STR + B_STR, "full_ba": "S" + B_STR + A_STR,
        "full_ab+a": "S" + A_STR + B_STR + A_D, "full_ab+b": "S" + A_STR + B_STR + B_D,
        "full_ba+b": "S" + B_STR + A_STR + B_D, "full_ba+a": "S" + B_STR + A_STR + A_D,
        "tile21_ab": "S" + tile(AB, 21), "tile21_ba": "S" + tile(BA, 21),
        "tile29_ab": "S" + tile(AB, 29), "tile29_ba": "S" + tile(BA, 29),
        "tile21_il": "S" + tile(ilab, 21), "tile29_il": "S" + tile(ilab, 29),
        "ab+1x5": "S" + AB + "1" * 5, "1x5+ab": "S" + "1" * 5 + AB,
        "ba+1x5": "S" + BA + "1" * 5, "1x5+ba": "S" + "1" * 5 + BA,
        "ab+1x13": "S" + AB + "1" * 13, "1x13+ab": "S" + "1" * 13 + AB,
        "ba+1x13": "S" + BA + "1" * 13, "1x13+ba": "S" + "1" * 13 + BA,
        "letters_ab": "S" + "CLAKB" + AB, "letters_ba": "S" + "KBCLA" + BA,
        "sp_ab": "S" + A_STR + " " + B_STR, "lower_ab": "S" + (A_STR + B_STR).lower(),
        "el_ab": "S" + "ElSalvador" + A_D[:3] + B_D[:3] + A_D[3:] + B_D[3:],
    }
    for nm, s in cands.items():
        add(f"mini:{nm}(len{len(s)})", s)

def fam_brainwallet(add):
    bases = {
        "d_ab": AB, "d_ba": BA, "d_ab_sp": A_D + " " + B_D, "d_ba_sp": B_D + " " + A_D,
        "s_ab": A_STR + B_STR, "s_ba": B_STR + A_STR, "s_ab_sp": A_STR + " " + B_STR,
        "s_ba_sp": B_STR + " " + A_STR, "s_ab_fullsp": "CL 76841714 A KB 46279860",
        "s_ba_fullsp": "KB 46279860 CL 76841714 A", "d_ab_dash": A_D + "-" + B_D,
        "d_ab_nl": A_D + "\n" + B_D, "s_ab_nl": A_STR + "\n" + B_STR,
        "s_ab_lower": (A_STR + B_STR).lower(), "s_ab_sp_lower": (A_STR + " " + B_STR).lower(),
        "d_ab_slash": A_D + "/" + B_D,
    }
    variants = [("nl", "{p}\n"), ("crlf", "{p}\r\n"), ("sp", "{p} "), ("tab", "{p}\t"),
                ("nul", "{p}\0"), ("_sp", " {p}"), ("_nl", "\n{p}"), ("bom", "﻿{p}"),
                ("x2", "{p}{p}"), ("x3", "{p}{p}{p}"), ("x2sp", "{p} {p}"), ("x2nl", "{p}\n{p}"),
                ("x3sp", "{p} {p} {p}"), ("nlnl", "{p}\n\n"), ("quoted", '"{p}"'),
                ("x2nl_tail", "{p}\n{p}\n")]
    for bn, p in bases.items():
        for vn, fmt in variants:
            add(f"bw:{bn}/{vn}", fmt.replace("{p}", p))
        add(f"bw:{bn}/utf16le", hx(p.encode("utf-16-le")))
        add(f"bw:{bn}/utf16be", hx(p.encode("utf-16-be")))
    iter_bases = ["d_ab", "d_ba", "s_ab", "s_ba", "d_ab_sp", "s_ab_sp", "s_ab_fullsp", "s_ab_lower"]
    for bn in iter_bases:
        p = bases[bn].encode(); h = hashlib.sha256(p).digest(); k = 1
        for target in (3, 10, 100, 1000, 10000, 100000):
            while k < target:
                h = hashlib.sha256(h).digest(); k += 1
            add(f"bw:{bn}/sha256^{target}", hx(h))

def fam_bip39_groupings(add):
    sources16 = {"ab": AB, "ba": BA, "rev_ab": AB[::-1], "rev_ba": BA[::-1],
                 "il_ab": interleave(A_D, B_D), "il_ba": interleave(B_D, A_D)}
    comps = list(compositions(16, 12))
    e2g = []
    for sn, digits in sources16.items():
        for comp in comps:
            ctag = ".".join(map(str, comp))
            for base in (0, 1):
                ph = group_words(digits, comp, base)
                if ph is None: continue
                fl = flags(ph)
                add(f"b39g:{sn}/b{base}/{ctag}{fl}", ph)
                if "e2v=" in fl: e2g.append((f"e2g:{sn}/b{base}/{ctag}", ph))
    # 24-digit sources: the serials with the series years they carry
    sources24 = {"ab2001_2006": AB + "20012006", "ab2006_2001": AB + "20062001",
                 "2001a2006b": "2001" + A_D + "2006" + B_D, "a2001b2006": A_D + "2001" + B_D + "2006",
                 "ba2006_2001": BA + "20062001", "2006b2001a": "2006" + B_D + "2001" + A_D}
    for sn, digits in sources24.items():
        assert len(digits) == 24, sn
        for cn, comp in (("1x24", (1,) * 24), ("2x12", (2,) * 12)):
            for base in (0, 1):
                ph = group_words(digits, comp, base)
                if ph is None: continue
                fl = flags(ph)
                add(f"b39g:{sn}/b{base}/{cn}{fl}", ph)
                if "e2v=" in fl: e2g.append((f"e2g:{sn}/b{base}/{cn}", ph))
    if _EC:
        for tag, ph in e2g:
            k, c = bip32_master(electrum_root(ph))
            add(f"{tag}/root", hx(k))
            add(f"{tag}/m0.0", hx(ckd_path(k, c, "m/0/0")))
            add(f"{tag}/m0h.0.0", hx(ckd_path(k, c, "m/0'/0/0")))

def fam_xprv(add):
    if not _EC: return
    seeds = {
        "bcd_ab": bytes.fromhex(AB), "bcd_ba": bytes.fromhex(BA),
        "bcd_abx2": bytes.fromhex(AB * 2), "bcd_bax2": bytes.fromhex(BA * 2),
        "ints_ab_be": a.to_bytes(4, "big") + b.to_bytes(4, "big"),
        "ints_ba_be": b.to_bytes(4, "big") + a.to_bytes(4, "big"),
        "ints_ab_le": a.to_bytes(4, "little") + b.to_bytes(4, "little"),
        "ints_ba_le": b.to_bytes(4, "little") + a.to_bytes(4, "little"),
        "u64_ab_be": ((a << 32) | b).to_bytes(8, "big"), "u64_ab_le": ((a << 32) | b).to_bytes(8, "little"),
        "bcd_il": bytes.fromhex(interleave(A_D, B_D)),
        "bcd_ab_x4": bytes.fromhex(AB * 4),
    }
    paths = ["m/0/0", "m/0'/0/0", "m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0",
             "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0", "m/0", "m/1/0"]
    for nm, sd in seeds.items():
        k, c = bip32_master(sd)
        add(f"xprv:seed:{nm}/m", hx(k))
        add(f"xprv:seed:{nm}/xprv", b58check(xprv_payload(k, c)))
        for p in paths:
            try: add(f"xprv:seed:{nm}/{p}", hx(derive(sd, p)))
            except Exception: pass
    # composite: one serial is the private key, the other the chain code
    readings = {
        "sha256": {"A": hashlib.sha256(A_STR.encode()).digest(), "B": hashlib.sha256(B_STR.encode()).digest()},
        "sha256d": {"A": hashlib.sha256(A_D.encode()).digest(), "B": hashlib.sha256(B_D.encode()).digest()},
        "tiled": {"A": bytes.fromhex(A_D * 8), "B": bytes.fromhex(B_D * 8)},
        "ascii_rpad": {"A": A_STR.encode().ljust(32, b"\0"), "B": B_STR.encode().ljust(32, b"\0")},
        "int": {"A": a.to_bytes(32, "big"), "B": b.to_bytes(32, "big")},
    }
    children = ["m/0", "m/0/0", "m/0'", "m/1/0", "m/0'/0/0", "m/44'/0'/0'/0/0"]
    for rn, r in readings.items():
        for kn, cn in (("A", "B"), ("B", "A")):
            k, c = r[kn], r[cn]
            if not key_ok(k): continue
            add(f"xprv:comp:{rn}:key{kn}_cc{cn}/xprv", b58check(xprv_payload(k, c)))
            add(f"xprv:comp:{rn}:key{kn}_cc{cn}/payload", hx(xprv_payload(k, c)))
            for p in children:
                try: add(f"xprv:comp:{rn}:key{kn}_cc{cn}/{p}", hx(ckd_path(k, c, p)))
                except Exception: pass

def fam_paths(add):
    def H(p):  # harden every component
        return "m/" + "/".join(x + "'" for x in p[2:].split("/"))
    P = []
    P += [f"m/{a}/{b}", f"m/{b}/{a}", f"m/{a}'/{b}", f"m/{a}/{b}'", f"m/{b}'/{a}", f"m/{b}/{a}'",
          f"m/{a}", f"m/{b}", f"m/{a}/0", f"m/{b}/0", f"m/{a}/{b}/0", f"m/{a}'/{b}'/0/0", f"m/{a}/{b}/0/0",
          f"m/{ah}/{bh}", f"m/{bh}/{ah}",
          "m/7684/1714/4627/9860", "m/4627/9860/7684/1714",
          "m/76/84/17/14/46/27/98/60", "m/46/27/98/60/76/84/17/14",
          "m/7/6/8/4/1/7/1/4/4/6/2/7/9/8/6/0", "m/4/6/2/7/9/8/6/0/7/6/8/4/1/7/1/4",
          "m/768/417/144/627/986/0", "m/7684171/4462798/60",
          f"m/3/12/{a}/1/11/2/{b}", f"m/12/{a}/2/{b}", f"m/2001/{a}/2006/{b}", f"m/12/2/{a}/{b}",
          f"m/44'/0'/0'/0/{a}", f"m/44'/0'/0'/0/{b}", f"m/44'/0'/0'/{a}/{b}", f"m/44'/0'/{a}'/0/{b}",
          f"m/44'/0'/{a}'/0/0", f"m/44'/0'/{b}'/0/0", f"m/84'/0'/0'/0/{a}", f"m/84'/0'/0'/0/{b}",
          f"m/49'/0'/0'/0/{a}", f"m/86'/0'/0'/0/{a}", f"m/0/{a}", f"m/0/{b}", f"m/0'/{a}/{b}",
          f"m/0/{a}/{b}", f"m/{a}'/0/0", f"m/{b}'/0/0", f"m/44'/{a}'/{b}'/0/0",
          f"m/{a + b}", f"m/{a ^ b}", f"m/{abs(a - b)}", f"m/{a + b}/0", f"m/{ah ^ bh}"]
    for p in [f"m/{a}/{b}", f"m/{b}/{a}", f"m/{ah}/{bh}", "m/7684/1714/4627/9860",
              "m/4627/9860/7684/1714", "m/76/84/17/14/46/27/98/60",
              "m/7/6/8/4/1/7/1/4/4/6/2/7/9/8/6/0", f"m/3/12/{a}/1/11/2/{b}", f"m/12/{a}/2/{b}",
              f"m/2001/{a}/2006/{b}", f"m/{a + b}"]:
        P.append(H(p))
    for p in dict.fromkeys(P):
        if all(int(x.rstrip("'")) < 0x80000000 for x in p[2:].split("/")):
            add(f"path:{p}", "path:" + p)

def fam_raw(add):
    def place(parts):
        k = bytearray(32)
        for off, bs in parts: k[off:off + len(bs)] = bs
        return bytes(k)
    pairs = [(0, 4), (4, 0), (0, 28), (28, 0), (24, 28), (28, 24), (0, 16), (16, 0),
             (12, 16), (16, 12), (12, 28), (28, 12), (4, 28), (28, 4)]
    for rn, (x, y) in (("dec", (a, b)), ("hex", (ah, bh))):
        for en in ("big", "little"):
            for pa, pb in pairs:
                k = place([(pa, x.to_bytes(4, en)), (pb, y.to_bytes(4, en))])
                if key_ok(k): add(f"raw:u32x2:{rn}/{en[:2]}/a@{pa}b@{pb}", hx(k))
            for pa, pb in ((0, 8), (16, 24), (0, 24), (8, 16)):
                k = place([(pa, x.to_bytes(8, en)), (pb, y.to_bytes(8, en))])
                if key_ok(k): add(f"raw:u64x2:{rn}/{en[:2]}/a@{pa}b@{pb}", hx(k))
    for sn, s in (("ab", AB), ("ba", BA), ("il_ab", interleave(A_D, B_D)), ("il_ba", interleave(B_D, A_D))):
        for off in (0, 16):
            add(f"raw:ascii16:{sn}@{off}", hx(place([(off, s.encode())])))
        add(f"raw:ascii32:{sn}_rpad0", hx(s.ljust(32, "0").encode()))
        add(f"raw:ascii32:{sn}_lpad0", hx(s.rjust(32, "0").encode()))
        add(f"raw:ascii32:{sn}_x2", hx((s * 2).encode()))
    for (xn, x), (yn, y) in itertools.permutations((("a", A_D), ("b", B_D)), 2):
        for px, py in ((0, 16), (0, 24), (8, 16), (8, 24), (16, 24), (24, 0), (16, 0), (24, 8)):
            add(f"raw:ascii8x2:{xn}@{px}{yn}@{py}", hx(place([(px, x.encode()), (py, y.encode())])))
    for sn, s in (("s_ab", A_STR + B_STR), ("s_ba", B_STR + A_STR),
                  ("s_ab_sp", A_STR + " " + B_STR), ("s_ba_sp", B_STR + " " + A_STR)):
        add(f"raw:asciifull:{sn}_rpad", hx(s.encode().ljust(32, b"\0")))
        add(f"raw:asciifull:{sn}_lpad", hx(s.encode().rjust(32, b"\0")))
        add(f"raw:asciifull:{sn}_rpad0", hx(s.ljust(32, "0").encode()))

def fam_bip38(add):
    for pn, pw, sn, salt in (("Astr", A_STR, "Bd", B_D), ("Bstr", B_STR, "Ad", A_D),
                             ("Ad", A_D, "Bd", B_D), ("Bd", B_D, "Ad", A_D)):
        k = hashlib.scrypt(pw.encode(), salt=salt.encode(), n=16384, r=8, p=8, dklen=32)
        if key_ok(k): add(f"bip38:passfactor({pn},salt={sn})", hx(k))

def fam_armory(add):
    if not _EC: return
    roots = {"tiled_ab": bytes.fromhex(AB * 4), "tiled_ba": bytes.fromhex(BA * 4),
             "sha256_dab": hashlib.sha256(AB.encode()).digest(),
             "sha256_sab": hashlib.sha256((A_STR + B_STR).encode()).digest()}
    for nm, r in roots.items():
        if not key_ok(r): continue
        k = r
        for step in (1, 2):
            k = armory_next(k)
            add(f"armory:{nm}/chain{step}", hx(k))


# ---------------------------------------------------------------- API
_CACHE = None

def forms():
    global _CACHE
    if _CACHE is not None:
        return list(_CACHE)
    out, seen = [], set()
    def add(tag, val):
        if not val or tag in seen:
            raise ValueError(f"bad form {tag!r}")
        seen.add(tag); out.append((tag, val))
    for fam in (fam_electrum2, fam_electrum1, fam_minikey, fam_brainwallet,
                fam_bip39_groupings, fam_xprv, fam_paths, fam_raw, fam_bip38, fam_armory):
        fam(add)
    _CACHE = out
    return list(out)


def selftest():
    ok = True
    F = forms(); D = dict(F)
    def rep(msg, good):
        nonlocal ok; ok &= bool(good); print(f"  {msg}: {'OK' if good else 'FAIL'}")
    rep(f"{len(F)} forms, <= 20000", 0 < len(F) <= 20000)
    rep("tags unique", len(D) == len(F))
    rep("no empty values", all(v for _, v in F))
    rep("hex: values are valid even-length hex",
        all(len(v[4:]) % 2 == 0 and bytes.fromhex(v[4:]) is not None for _, v in F if v.startswith("hex:")))
    # Electrum 2.x encoding is little-endian base 2048
    rep("electrum_encode(1) == 'ability'", electrum_encode(1) == "ability")
    rep("electrum_encode(2048) == 'abandon ability'", electrum_encode(2048) == "abandon ability")
    rep("electrum_encode(2047) == 'zoo'", electrum_encode(2047) == "zoo")
    mk = [t for t in D if t.startswith("e2:mk_std:") and "/" not in t]
    rep(f"{len(mk)} Electrum make_seed phrases, all carry prefix 01",
        mk and all(electrum_prefix(D[t]) == "01" for t in mk))
    # Electrum 1.x seeds and stretch
    rep("e1 32-hex tiled seed is ab repeated twice",
        D.get("e1:seed32:ab_x2") == "hex:76841714462798607684171446279860")
    s = b"00" * 16; o = s
    for _ in range(100000): s = hashlib.sha256(s + o).digest()
    rep("stretch1x matches an independent 100k loop", stretch1x("00" * 16) == int.from_bytes(s, "big"))
    # mini keys
    rep("SCL76841714AKB46279860 is a 22-char mini-key shape",
        D.get("mini:full_ab(len22)") == "SCL76841714AKB46279860" and len("SCL76841714AKB46279860") == 22)
    rep("30-char shape present", D.get("mini:full_ab+a(len30)") == "SCL76841714AKB4627986076841714")
    # brainwallet artefacts
    rep("trailing-newline variant", D.get("bw:d_ab/nl") == "7684171446279860\n")
    rep("x3 variant", D.get("bw:s_ab/x3") == "CL76841714AKB46279860" * 3)
    h = hashlib.sha256(b"7684171446279860").digest()
    for _ in range(2): h = hashlib.sha256(h).digest()
    rep("sha256^3 equals three explicit rounds", D.get("bw:d_ab/sha256^3") == hx(h))
    # groupings: count and one hand-built phrase
    rep("1,353 groupings of 16 digits into 12 parts of 1-4", len(list(compositions(16, 12))) == 1353)
    want = " ".join(WL[i] for i in (76, 84, 17, 14, 4, 6, 2, 7, 9, 8, 6, 0))
    got = [v for t, v in F if t.startswith("b39g:ab/b0/2.2.2.2.1.1.1.1.1.1.1.1")]
    rep("ab grouped 2.2.2.2.1x8, base 0 -> 'another appear acquire achieve ...'",
        got == [want] and want.startswith("another appear acquire achieve above absorb able"))
    rep("base-1 grouping ending in a lone '0' is dropped",
        not any(t.startswith("b39g:ab/b1/2.2.2.2.1.1.1.1.1.1.1.1") for t in D))
    n12 = sum(1 for t, v in F if t.startswith("b39g:") and len(v.split()) == 12)
    n24 = sum(1 for t, v in F if t.startswith("b39g:") and len(v.split()) == 24)
    rep(f"{n12} twelve-word and {n24} 24-word grouping phrases", n12 > 5000 and n24 >= 6)
    # raw placements
    asc = "7684171446279860".encode().hex()
    rep("16 ASCII digits at offset 0", D.get("raw:ascii16:ab@0") == "hex:" + asc + "00" * 16)
    rep("16 ASCII digits at offset 16", D.get("raw:ascii16:ab@16") == "hex:" + "00" * 16 + asc)
    k = bytearray(32); k[0:4] = a.to_bytes(4, "big"); k[28:32] = b.to_bytes(4, "big")
    rep("a BE at 0, b BE at 28", D.get("raw:u32x2:dec/bi/a@0b@28") == hx(bytes(k)))
    rep("path form present", D.get("path:m/76841714/46279860") == "path:m/76841714/46279860")
    rep("hardened path form present", D.get("path:m/76841714'/46279860'") == "path:m/76841714'/46279860'")
    if _EC:
        rep("Electrum-1 address keys derived (EC available)", any(t.startswith("e1:addr32:ab_x2/0:0") for t in D))
        rep("composite xprv children derived", "xprv:comp:sha256:keyA_ccB/m/0/0" in D)
        rep("xprv strings start with 'xprv'", all(v.startswith("xprv") for t, v in F if t.endswith("/xprv")))
    print("  SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    import time
    t0 = time.time()
    n = len(forms())
    print(n, "forms; selftest", selftest(), f"({time.time() - t0:.1f}s)")
