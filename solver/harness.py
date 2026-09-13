#!/usr/bin/env python3
"""
Shared offline harness for the Overdose puzzle (2026-09-13 session).

Oracle
------
/tmp/oracle/addrs_all.txt : 1,720,292 unique addresses pulled from every file
of the Pymmdrza/Rich-Address-Wallet clone (April-2023 rich list down to ~1 BTC,
plus later snapshots).  Positive control: all 870 named exactly-20-BTC
addresses from window/named_exact20_870.txt are present.  Any single address
holding the 20 BTC prize by April 2023 (Keiser said it was unclaimed in
March and December 2023) MUST be in this set, so a derivation that produces a
funded address registers here.  It does NOT see: addresses funded after
Apr-2023 only, sub-1-BTC dust, or a prize split across many small outputs.

Key-format oracles that need no chain data at all
-------------------------------------------------
  wif_check(s)           WIF 51/52 chars, 4-byte dSHA256 checksum (1 in 2^32)
  bip38_check(s)         6P... 58 chars, 4-byte checksum
  mini_check(s)          Casascius mini, 1 byte (weak, ~1/256)
  bip39_valid(words)     BIP-39 checksum (1 in 16 for 12 words, 1/256 for 24)
  electrum_v2_type(text) HMAC-SHA512("Seed version") prefix '01'/'100'/'101'
                         (1 in 256 / 1 in 4096) -- accepts ANY words
  electrum_old_valid(w)  12 words all in the 1626-word old Electrum list

Derivations
-----------
  addrs_for_priv(priv32) -> dict type->address (p2pkh_c, p2pkh_u, p2wpkh,
                            p2sh_p2wpkh, p2tr)
  bip39_addrs(mnemonic, passphrase, paths) -> list of (path, type, addr)
  electrum_v2_addrs(text, passphrase, n) -> standard m/0/i + segwit m/0'/0/i
  electrum_old_addrs(words, n) -> old Electrum stretched-key addresses

Run `python3 harness.py --selftest` before trusting any null from it.
"""
import hashlib, hmac, os, sys, unicodedata, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coincurve import PrivateKey, PublicKey
from hd_sweep import (CURVE_N, h160, derive as hd_derive, build_paths,
                      bech32_encode, addr_p2pkh, addr_p2sh_p2wpkh, addr_p2wpkh,
                      addr_p2tr, b58check)

ORACLE_PATH = "/tmp/oracle/addrs_all.txt"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58SET = set(B58)


# ---------------------------------------------------------------- base58 ----
def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def b58encode(b):
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    pad = len(b) - len(b.lstrip(b"\x00"))
    return "1" * pad + out


def sha256d(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def to_wif(priv32, compressed=True):
    body = b"\x80" + priv32 + (b"\x01" if compressed else b"")
    return b58encode(body + sha256d(body)[:4])


# ----------------------------------------------------- key-format oracles ----
def wif_check(s):
    if len(s) not in (51, 52) or any(c not in B58SET for c in s):
        return None
    raw = b58decode(s)
    if len(raw) not in (37, 38) or raw[0] != 0x80:
        return None
    if sha256d(raw[:-4])[:4] != raw[-4:]:
        return None
    if len(raw) == 38 and raw[33] != 0x01:
        return None
    return ("wif_c" if len(raw) == 38 else "wif_u", raw[1:33])


def bip38_check(s):
    if len(s) != 58 or not s.startswith("6P") or any(c not in B58SET for c in s):
        return None
    raw = b58decode(s)
    if len(raw) != 43 or sha256d(raw[:-4])[:4] != raw[-4:]:
        return None
    return ("bip38", raw)


def mini_check(s):
    if len(s) not in (22, 26, 30) or not s.startswith("S"):
        return None
    if any(c not in B58SET for c in s):
        return None
    if hashlib.sha256((s + "?").encode()).digest()[0] != 0:
        return None
    return ("mini", hashlib.sha256(s.encode()).digest())


# ------------------------------------------------------------- wordlists ----
def _load_bip39():
    p = "/tmp/wl/bip39_english.txt"
    if os.path.exists(p):
        return [w.strip() for w in open(p) if w.strip()]
    from mnemonic import Mnemonic
    return Mnemonic("english").wordlist


BIP39 = _load_bip39()
BIP39_SET = set(BIP39)
BIP39_IDX = {w: i for i, w in enumerate(BIP39)}


def _load_electrum_old():
    p = "/tmp/wl/electrum_old.py"
    words = []
    if os.path.exists(p):
        src = open(p).read()
        m = re.search(r"_words = \((.*?)\)\n", src, re.S)
        words = re.findall(r'"([a-z]+)"', m.group(1))
    return words


ELECTRUM_OLD = _load_electrum_old()
ELECTRUM_OLD_SET = set(ELECTRUM_OLD)
ELECTRUM_OLD_IDX = {w: i for i, w in enumerate(ELECTRUM_OLD)}


def bip39_valid(words):
    """words: list of lowercase words. True iff all in list and checksum ok."""
    if len(words) not in (12, 15, 18, 21, 24):
        return False
    if any(w not in BIP39_IDX for w in words):
        return False
    bits = "".join(format(BIP39_IDX[w], "011b") for w in words)
    cs = len(bits) // 33
    ent, chk = bits[:-cs], bits[-cs:]
    entb = int(ent, 2).to_bytes(len(ent) // 8, "big")
    h = hashlib.sha256(entb).digest()
    hb = "".join(format(x, "08b") for x in h)
    return hb[:cs] == chk


def bip39_seed(mnemonic, passphrase=""):
    m = unicodedata.normalize("NFKD", mnemonic).encode()
    p = unicodedata.normalize("NFKD", passphrase).encode()
    return hashlib.pbkdf2_hmac("sha512", m, b"mnemonic" + p, 2048)


def electrum_normalize(text):
    x = unicodedata.normalize("NFKD", text)
    x = x.lower()
    x = "".join(c for c in x if not unicodedata.combining(c))
    x = " ".join(x.split())
    return x


def electrum_v2_type(text):
    """'standard' ('01'), 'segwit' ('100'), '2fa' ('101'), '2fa_segwit' ('102') or None."""
    x = electrum_normalize(text)
    s = hmac.new(b"Seed version", x.encode("utf8"), hashlib.sha512).hexdigest()
    if s.startswith("01"):
        return "standard"
    if s.startswith("100"):
        return "segwit"
    if s.startswith("101"):
        return "2fa"
    if s.startswith("102"):
        return "2fa_segwit"
    return None


def electrum_v2_seed(text, passphrase=""):
    x = electrum_normalize(text).encode("utf8")
    p = electrum_normalize(passphrase).encode("utf8")
    return hashlib.pbkdf2_hmac("sha512", x, b"electrum" + p, 2048)


def electrum_old_valid(words):
    return len(words) % 3 == 0 and len(words) >= 12 and all(w in ELECTRUM_OLD_IDX for w in words)


def electrum_old_decode(words):
    n = len(ELECTRUM_OLD)
    out = ""
    for i in range(len(words) // 3):
        w1 = ELECTRUM_OLD_IDX[words[3 * i]]
        w2 = ELECTRUM_OLD_IDX[words[3 * i + 1]] % n
        w3 = ELECTRUM_OLD_IDX[words[3 * i + 2]] % n
        x = w1 + n * ((w2 - w1) % n) + n * n * ((w3 - w2) % n)
        out += "%08x" % x
    return out


def electrum_old_encode(hexseed):
    n = len(ELECTRUM_OLD)
    out = []
    for i in range(len(hexseed) // 8):
        x = int(hexseed[8 * i:8 * i + 8], 16)
        w1 = x % n
        w2 = ((x // n) + w1) % n
        w3 = ((x // n // n) + w2) % n
        out += [ELECTRUM_OLD[w1], ELECTRUM_OLD[w2], ELECTRUM_OLD[w3]]
    return out


def electrum_old_stretch(hexseed):
    seed = hexseed.encode("ascii")
    x = seed
    for _ in range(100000):
        x = hashlib.sha256(x + seed).digest()
    return int.from_bytes(x, "big")


def electrum_old_addrs(words_or_hex, n_addrs=5, change=False):
    """Old (pre-2.0) Electrum standard wallet: uncompressed P2PKH receive addrs."""
    if isinstance(words_or_hex, str) and re.fullmatch(r"[0-9a-f]{32}", words_or_hex):
        hexseed = words_or_hex
    else:
        hexseed = electrum_old_decode(words_or_hex)
    secexp = electrum_old_stretch(hexseed)
    if not 0 < secexp < CURVE_N:
        return []
    mpk = PrivateKey(secexp.to_bytes(32, "big")).public_key.format(compressed=False)[1:]
    out = []
    for i in range(n_addrs):
        for_change = 1 if change else 0
        z = int.from_bytes(sha256d(("%d:%d:" % (i, for_change)).encode("ascii") + mpk), "big")
        k = (secexp + z) % CURVE_N
        priv = k.to_bytes(32, "big")
        pub_u = PrivateKey(priv).public_key.format(compressed=False)
        out.append(("old/%d/%d" % (for_change, i), "p2pkh_u", addr_p2pkh(pub_u), priv))
    return out


# ------------------------------------------------------------ derivations ----
def addrs_for_priv(priv32):
    """All five standard address types for one 32-byte private key."""
    try:
        sk = PrivateKey(priv32)
    except Exception:
        return {}
    pub = sk.public_key
    pc = pub.format(compressed=True)
    pu = pub.format(compressed=False)
    out = {
        "p2pkh_c": addr_p2pkh(pc),
        "p2pkh_u": addr_p2pkh(pu),
        "p2wpkh": addr_p2wpkh(pc),
        "p2sh_p2wpkh": addr_p2sh_p2wpkh(pc),
    }
    try:
        out["p2tr"] = addr_p2tr(pc)
    except Exception:
        pass
    return out


def hd_addrs(seed, paths):
    out = []
    for p in paths:
        try:
            priv = hd_derive(seed, p)
        except Exception:
            continue
        for t, a in addrs_for_priv(priv).items():
            out.append((p, t, a, priv))
    return out


DEFAULT_PATHS = None


def default_paths():
    global DEFAULT_PATHS
    if DEFAULT_PATHS is None:
        DEFAULT_PATHS = build_paths()
    return DEFAULT_PATHS


def quick_paths(n=5):
    """Cheap first-pass path set: first n receive + first change of the big 4."""
    ps = []
    for purpose in ("44'", "49'", "84'", "86'"):
        for i in range(n):
            ps.append(f"m/{purpose}/0'/0'/0/{i}")
        ps.append(f"m/{purpose}/0'/0'/1/0")
    for i in range(n):
        ps.append(f"m/0/{i}")          # electrum standard / bip32 plain
        ps.append(f"m/0'/0/{i}")       # electrum segwit
        ps.append(f"m/{i}")
    ps.append("m")
    return ps


def bip39_addrs(mnemonic, passphrase="", paths=None):
    seed = bip39_seed(mnemonic, passphrase)
    return hd_addrs(seed, paths or quick_paths())


def electrum_v2_addrs(text, passphrase="", n=5):
    seed = electrum_v2_seed(text, passphrase)
    ps = [f"m/0/{i}" for i in range(n)] + [f"m/1/{i}" for i in range(2)]
    ps += [f"m/0'/0/{i}" for i in range(n)] + [f"m/0'/1/{i}" for i in range(2)]
    return hd_addrs(seed, ps)


# --------------------------------------------------------------- oracle ----
_FULL = None
_FULL_TRIED = False


def full_index(verbose=False):
    """Return a calibrated index_oracle.Oracle over the full 56.8M funded index
    if /tmp/address_map.bin exists, else None. Cached."""
    global _FULL, _FULL_TRIED
    if _FULL_TRIED:
        return _FULL
    _FULL_TRIED = True
    try:
        import index_oracle
        if not os.path.exists(index_oracle.MAP):
            return None
        o = index_oracle.Oracle(verbose=verbose)
        if o.calibrate():
            _FULL = o
    except Exception as e:
        sys.stderr.write(f"full_index unavailable: {e}\n")
    return _FULL


class Oracle:
    def __init__(self, path=ORACLE_PATH, use_full=True):
        self.addrs = set()
        with open(path) as f:
            for line in f:
                a = line.strip()
                if a:
                    self.addrs.add(a)
        # positive controls: genesis coinbase, a named exact-20 candidate
        for a in ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                  "123msjGU1bGfvBSc8dok2GBbKbWmc2pYTF"):
            if a not in self.addrs:
                raise RuntimeError(f"oracle positive control missing: {a}")
        self.full = full_index() if use_full else None
        if self.full is not None:
            sys.stderr.write("Oracle: full 56.8M index ACTIVE (checks both sets)\n")

    def __contains__(self, a):
        return self.funded(a)

    def funded(self, a):
        if a in self.addrs:
            return True
        if self.full is not None:
            try:
                return self.full.balance(a) is not None
            except Exception:
                return False
        return False

    def check_priv(self, priv32):
        """Return [(type, addr)] of funded addresses for this private key."""
        return [(t, a) for t, a in addrs_for_priv(priv32).items() if a in self.addrs]

    def check_phrase_direct(self, phrase):
        """Brainwallet-style: 7 fast hashes x 5 address types."""
        from hd_sweep import direct_keys
        hits = []
        for name, k in direct_keys(phrase).items():
            for t, a in self.check_priv(k):
                hits.append((name, t, a, k.hex()))
        return hits


# ------------------------------------------------------------- englishness --
def englishness_z(s, shuffles=40, seed=1):
    from englishness import zscore
    import random
    return zscore(s, shuffles, random.Random(seed))


# --------------------------------------------------------------- selftest ---
def selftest():
    ok = True

    def chk(name, got, exp):
        nonlocal ok
        good = got == exp
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {name}: {got}{'' if good else '  expected ' + str(exp)}")

    # WIF round trip + known vector (bitcoin wiki)
    priv = bytes.fromhex("0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D")
    chk("wif_u", to_wif(priv, False), "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ")
    chk("wif_c", to_wif(priv, True), "KwdMAjGmerYanjeui5SHS7JkmpZvVipYvB2LJGU1ZxJwYvP98617")
    chk("wif_check_u", wif_check("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ")[1], priv)
    chk("wif_check_bad", wif_check("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTK"), None)
    # brainwallet vector
    k = hashlib.sha256(b"correct horse battery staple").digest()
    chk("brainwallet p2pkh_u", addrs_for_priv(k)["p2pkh_u"], "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T")
    # BIP39 checksum + vector
    m = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    chk("bip39_valid", bip39_valid(m.split()), True)
    chk("bip39_invalid", bip39_valid(("abandon " * 12).split()), False)
    got = dict(((p, t), a) for p, t, a, _ in bip39_addrs(m, "", ["m/44'/0'/0'/0/0", "m/84'/0'/0'/0/0"]))
    chk("bip44 addr", got[("m/44'/0'/0'/0/0", "p2pkh_c")], "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA")
    chk("bip84 addr", got[("m/84'/0'/0'/0/0", "p2wpkh")], "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu")
    # Electrum v2 seed version (electrum test suite seeds)
    chk("electrum v2 standard", electrum_v2_type("cycle rocket west magnet parrot shuffle foot correct salt library feed song"), "standard")
    chk("electrum v2 segwit", electrum_v2_type("bitter grass shiver impose acquire brush forget axis eager alone wine silver"), "segwit")
    # Electrum old: wordlist size, encode/decode round trip, and the test-suite vector
    chk("electrum old wordlist", len(ELECTRUM_OLD), 1626)
    hx = "431a62f1c86555d3c45e5c1e9ab77c8c"
    chk("electrum old roundtrip", electrum_old_decode(electrum_old_encode(hx)), hx)
    w = "powerful random nobody notice nothing important anyway look away hidden message over".split()
    chk("electrum old words valid", electrum_old_valid(w), True)
    a = electrum_old_addrs(w, 1)
    chk("electrum old addr0", a[0][2] if a else None, "1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo")
    # oracle
    o = Oracle()
    chk("oracle size>1.7M", len(o.addrs) > 1_700_000, True)
    chk("oracle genesis", o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"), True)
    chk("oracle brainwallet swept", o.funded("1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"), False)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
