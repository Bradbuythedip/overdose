#!/usr/bin/env python3
"""
Both banknote serials COMBINED, every way, and a transform-closure "discovery
mode" that follows each result into the next transform. Against the real index.

WHAT WAS MISSING
`serial2_exhaust.py` lists a framing G -- "paired: both serials combined,
concatenated and arithmetic" -- in its docstring, and never implements it. The
only paired forms ever swept are three plain concatenations in `clue_serial.py`.
Everything below is therefore new coverage, not a re-run:

  1 numeric     a=76841714, b=46279860 (and their hex readings): sum, difference,
                product, xor/or/and, mod, gcd, interleaved digits, digit-wise
                sum/diff/product mod 10, concatenations, x20 (the prize), each
                as a string, as hex, as a raw integer key, as LE/BE bytes
  2 strings     the letters and digits recombined (CL/KB/A/L12, spacing,
                ordering, reversal, mirror), plus what the letters MEAN on a
                Federal Reserve Note: series C=2001, K=2006A; district
                L=12 San Francisco, B=2 New York; the $100 (Franklin)
                -- direct hashes AND 5 seed types x 72 HD paths
  3 entropy     16 ASCII digits = exactly 128 bits = a 12-word mnemonic; packed
                BCD / 32-bit ints / hex readings tiled to 16 and 32 bytes; every
                combined string whose byte length is a legal entropy size; and
                sha256 of each string as 24-word entropy -- each mnemonic x 9
                passphrases (incl. the OTHER serial) x 72 paths
  4 pairing     one serial as key, the other as message/salt: HMAC-SHA512,
                PBKDF2-SHA256/512 (1 and 2048 rounds), scrypt, WarpWallet
                (N=2^18), sha256(a) xor sha256(b), byte-wise xor
  5 text-index  the digits (singles, pairs, triples, quads, cumulative) as
                indices into the article's words / lines / characters and page
                72, 0- and 1-based; 12/24-index readings into the BIP-39 list,
                checksum-validated against chance
  6 discovery   breadth-first closure over ~30 transforms (reverse, rot180,
                mirror, hash-to-hex, hex<->int, base58, concat-with-other,
                concat-with-"El Salvador", digit-wise xor/sum, interleave,
                sort, digit-sum, tile...) from the serial pair, depth-bounded,
                deduplicated, every node tested. --loop widens the depth.
  +  plugins    any combo_*.py in this directory exporting forms() -> [(tag, s)]
                is swept too; "hex:" tags are bytes, and 32-byte ones are
                also tried as raw keys

CONTROLS  the index's genesis-address control; a planted key that MUST be
found by the same code path; a BIP-39 test vector (all-zero entropy ->
1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA) proving entropy->mnemonic->seed->path->
address end to end; WIF validator vectors. Any null is refused without them.

NO PARTIAL CREDIT  a hit is an address in the 56M funded index, a checksum-
valid WIF, or a checksum-valid mnemonic counted against its chance rate.

  python3 serial_combine.py --selftest
  python3 serial_combine.py                 # all families, discovery depth 2
  python3 serial_combine.py --loop          # then depth 3, 4 (capped, logged)
"""
import argparse, glob, hashlib, hmac, importlib, itertools, math, os, sys, time

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
A_L, A_D, A_S, A_DIST = "CL", "76841714", "A", "L12"
B_L, B_D = "KB", "46279860"
A_STR, B_STR = "CL76841714A", "KB46279860"
a, b = int(A_D), int(B_D)
ah, bh = int(A_D, 16), int(B_D, 16)
ENT_SIZES = (16, 20, 24, 28, 32)
PASSPHRASES = ["", "El Salvador", "bitcoin", "OVERDOSE", "Max Keiser",
               A_STR, B_STR, A_D, B_D]
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


# ---------------------------------------------------------------- helpers
def b58enc(bs):
    n = int.from_bytes(bs, "big"); out = ""
    while n: n, r = divmod(n, 58); out = B58[r] + out
    return "1" * (len(bs) - len(bs.lstrip(b"\0"))) + out

def wif_valid(s):
    if not (50 <= len(s) <= 53) or any(c not in B58 for c in s): return False
    n = 0
    for c in s: n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    if len(raw) < 37 or raw[0] != 0x80: return False
    return hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:]

def direct_bytes(bs):
    return {
        "sha256": hashlib.sha256(bs).digest(),
        "dsha256": hashlib.sha256(hashlib.sha256(bs).digest()).digest(),
        "sha512h": hashlib.sha512(bs).digest()[:32],
        "sha512l": hashlib.sha512(bs).digest()[32:],
        "sha3_256": hashlib.sha3_256(bs).digest(),
        "blake2b": hashlib.blake2b(bs, digest_size=32).digest(),
        "keccak_like": hashlib.sha3_256(hashlib.sha256(bs).digest()).digest(),
    }

def interleave(x, y):
    out = []
    for i in range(max(len(x), len(y))):
        if i < len(x): out.append(x[i])
        if i < len(y): out.append(y[i])
    return "".join(out)

def digitwise(x, y, op):
    if len(x) != len(y) or not (x.isdigit() and y.isdigit()): return None
    return "".join(str(op(int(p), int(q)) % 10) for p, q in zip(x, y))


# ---------------------------------------------------------------- family 1
def numeric_values():
    v = {}
    for pre, (x, y) in (("dec", (a, b)), ("hex", (ah, bh))):
        v[f"{pre}:a+b"] = x + y
        v[f"{pre}:|a-b|"] = abs(x - y)
        v[f"{pre}:a*b"] = x * y
        v[f"{pre}:a^b"] = x ^ y
        v[f"{pre}:a|b"] = x | y
        v[f"{pre}:a&b"] = x & y
        v[f"{pre}:a%b"] = x % y
        v[f"{pre}:b%a"] = y % x
        v[f"{pre}:gcd"] = math.gcd(x, y)
        v[f"{pre}:lcm"] = x * y // math.gcd(x, y)
        v[f"{pre}:a//b"] = x // y if x >= y else y // x
        v[f"{pre}:a2+b2"] = x * x + y * y
        v[f"{pre}:(a+b)/2"] = (x + y) // 2
        v[f"{pre}:a<<32|b"] = (x << 32) | y
        v[f"{pre}:b<<32|a"] = (y << 32) | x
        v[f"{pre}:(a+b)*20"] = (x + y) * 20
        v[f"{pre}:a*20+b"] = x * 20 + y
        v[f"{pre}:a+b+20"] = x + y + 20
        v[f"{pre}:a*b*20"] = x * y * 20
        v[f"{pre}:21e6-a-b"] = abs(21000000 - x - y)
        v[f"{pre}:a+b+21e6"] = x + y + 21000000
    v["dec:ab"] = int(A_D + B_D); v["dec:ba"] = int(B_D + A_D)
    v["hex:ab"] = int(A_D + B_D, 16); v["hex:ba"] = int(B_D + A_D, 16)
    v["dec:interleave_ab"] = int(interleave(A_D, B_D))
    v["dec:interleave_ba"] = int(interleave(B_D, A_D))
    v["dec:rev(a)+rev(b)"] = int(A_D[::-1]) + int(B_D[::-1])
    v["dec:rev(ab)"] = int((A_D + B_D)[::-1])
    for nm, op in (("sum", lambda p, q: p + q), ("diff", lambda p, q: p - q),
                   ("prod", lambda p, q: p * q), ("xor", lambda p, q: p ^ q)):
        v[f"dec:digitwise_{nm}"] = int(digitwise(A_D, B_D, op))
    v["dec:digitsum_a"] = sum(map(int, A_D)); v["dec:digitsum_b"] = sum(map(int, B_D))
    v["dec:digitsum_ab"] = v["dec:digitsum_a"] + v["dec:digitsum_b"]
    v["dec:a"] = a; v["dec:b"] = b
    return v

def numeric_forms():
    """(tag, str) material and (tag, key32) raw keys from the numeric values."""
    mats, keys = [], []
    for tag, v in numeric_values().items():
        s = str(v); h = format(v, "x")
        mats += [(f"{tag}/dec", s), (f"{tag}/hex", h), (f"{tag}/hex8", h.zfill(8)),
                 (f"{tag}/hex16", h.zfill(16))]
        if 0 < v < N:
            keys.append((f"{tag}/int", v.to_bytes(32, "big")))
        for nbytes in (4, 8, 16):
            if v < 1 << (8 * nbytes):
                be = v.to_bytes(nbytes, "big"); le = v.to_bytes(nbytes, "little")
                mats += [(f"{tag}/be{nbytes}", be), (f"{tag}/le{nbytes}", le)]
                kl = int.from_bytes(le.ljust(32, b"\0"), "big")
                if 0 < kl < N: keys.append((f"{tag}/le{nbytes}pad", kl.to_bytes(32, "big")))
                kr = int.from_bytes(be.ljust(32, b"\0"), "big")
                if 0 < kr < N: keys.append((f"{tag}/be{nbytes}rpad", kr.to_bytes(32, "big")))
    return mats, keys


# ---------------------------------------------------------------- family 2
def string_forms():
    """Combined string forms: letters+digits recombined, and banknote meaning."""
    import mirror_serial as MS
    S = set()
    partsA = [A_STR, A_D, A_L + A_D, A_D + A_S, "CL 76841714 A", A_DIST + A_D, A_D + A_DIST]
    partsB = [B_STR, B_D, "KB 46279860", B_L]
    seps = ["", " ", "-", "/", "\n", "_", ".", ",", "|", "+"]
    for x in partsA:
        for y in partsB:
            for sep in seps:
                S.add(x + sep + y); S.add(y + sep + x)
    # digit-only recombinations
    S.add(interleave(A_D, B_D)); S.add(interleave(B_D, A_D))
    for nm, op in (("sum", lambda p, q: p + q), ("diff", lambda p, q: p - q),
                   ("prod", lambda p, q: p * q), ("xor", lambda p, q: p ^ q)):
        S.add(digitwise(A_D, B_D, op))
    S.add(A_D + B_D); S.add(B_D + A_D); S.add((A_D + B_D)[::-1]); S.add((B_D + A_D)[::-1])
    S.add(A_D[::-1] + B_D[::-1]); S.add(B_D[::-1] + A_D[::-1])
    S.add(MS.rot180(A_D) + MS.rot180(B_D)); S.add(MS.rot180(A_D + B_D))
    S.add(MS.mirror(A_D + B_D)); S.add(MS.mirror(A_STR + B_STR))
    S.add("".join(sorted(A_D + B_D))); S.add("".join(sorted(A_D + B_D, reverse=True)))
    # letters alone and their meaning
    letters = ["CL", "KB", "CLKB", "KBCL", "CLAKB", "CLA KB", "CKLB", "CL KB", "CL A KB",
               "CLA", "LB", "CK", "L12 B2", "L12B2", "L B", "12 2", "122", "212", "1202", "0212",
               "3 12 1 11 2", "3121112", "03 12 01 11 02", "0312011102", "3-12-1-11-2"]
    series = ["2001", "2006", "2006A", "20012006", "2001 2006", "20062001", "2006 2001",
              "Series 2001", "Series 2006A", "2001 2006A"]
    district = ["San Francisco", "New York", "San Francisco New York", "New York San Francisco",
                "Federal Reserve Bank of San Francisco", "Federal Reserve Bank of New York",
                "L12", "B2", "12", "2", "twelve", "two", "12 2", "L 12 B 2"]
    note = ["100", "$100", "one hundred dollars", "Franklin", "Benjamin Franklin",
            "Federal Reserve Note", "In God We Trust", "United States of America",
            "The United States of America", "Independence Hall", "hundred", "twenty", "20"]
    for grp in (letters, series, district, note):
        for w in grp:
            S.add(w)
            for d in (A_D, B_D, A_D + B_D, A_D + " " + B_D, A_STR + B_STR, A_STR + " " + B_STR):
                S.add(w + " " + d); S.add(d + " " + w); S.add(w + d); S.add(d + w)
    # series/district numbers interleaved with digits
    for combo in ("2001 76841714 2006 46279860", "12 76841714 2 46279860",
                  "C 2001 L 12 76841714 A K 2006 B 2 46279860",
                  "L 76841714 A B 46279860", "CL 76841714 A KB 46279860",
                  "76841714 2001 46279860 2006", "76841714 12 46279860 2",
                  "200176841714200646279860", "12768417142462798 60".replace(" ", ""),
                  "1276841714246279860", "20017684171420062006A46279860",
                  "CL76841714A 2001 L12 KB46279860 2006A B2"):
        S.add(combo)
    # with the named clue
    for d in (A_D + B_D, A_D + " " + B_D, A_STR + B_STR, A_STR + " " + B_STR,
              B_D + A_D, B_STR + A_STR):
        for c in ("El Salvador", "el salvador", "ELSALVADOR", "OVERDOSE", "Overdose",
                  "Max Keiser", "Bukele", "bitcoin", "Bitcoin", "mirror", "George Sand",
                  "20 BTC", "20BTC", "Bitcoin Magazine", "Issue 24", "24", "72", "79", "7279"):
            S.add(d + " " + c); S.add(c + " " + d); S.add(d + c); S.add(c + d)
    out = []
    for s in S:
        if not s: continue
        out.append(s)
        if s != s.lower(): out.append(s.lower())
        if s != s.upper(): out.append(s.upper())
    return sorted(set(out))


# ---------------------------------------------------------------- family 3
def entropy_forms(strings):
    """(tag, entropy_bytes, passphrases) readings of the pair as BIP-39 entropy."""
    E = []
    d16 = [("ab", A_D + B_D), ("ba", B_D + A_D), ("ab_rev", (A_D + B_D)[::-1]),
           ("interleave", interleave(A_D, B_D)), ("interleave_ba", interleave(B_D, A_D))]
    full = PASSPHRASES
    for tag, s in d16:
        asc = s.encode()
        E.append((f"ascii16:{tag}", asc, full))
        E.append((f"ascii32:{tag}x2", asc * 2, full))
        bcd = bytes.fromhex(s)                          # 8 bytes
        E.append((f"bcd16:{tag}x2", bcd * 2, full))
        E.append((f"bcd16:{tag}lpad", bcd.rjust(16, b"\0"), full))
        E.append((f"bcd16:{tag}rpad", bcd.ljust(16, b"\0"), full))
        E.append((f"bcd32:{tag}x4", bcd * 4, full))
        E.append((f"bcd32:{tag}lpad", bcd.rjust(32, b"\0"), full))
    for tag, (x, y) in (("ints_ab", (a, b)), ("ints_ba", (b, a)), ("hex_ab", (ah, bh)), ("hex_ba", (bh, ah))):
        be = x.to_bytes(4, "big") + y.to_bytes(4, "big")
        le = x.to_bytes(4, "little") + y.to_bytes(4, "little")
        for nm, bs in (("be", be), ("le", le)):
            E.append((f"{tag}_{nm}16:x2", bs * 2, full))
            E.append((f"{tag}_{nm}16:lpad", bs.rjust(16, b"\0"), full))
            E.append((f"{tag}_{nm}16:rpad", bs.ljust(16, b"\0"), full))
            E.append((f"{tag}_{nm}32:x4", bs * 4, full))
        E.append((f"{tag}_be8+le8", be + le, full))
    for x, y in ((a, b), (b, a)):
        for nb in (16, 32):
            E.append((f"int{nb}:a<<|b", ((x << 32) | y).to_bytes(nb, "big"), full))
            E.append((f"int{nb}:a+b", (x + y).to_bytes(nb, "big"), full))
            E.append((f"int{nb}:a*b", (x * y).to_bytes(nb, "big"), full))
            E.append((f"int{nb}:a^b", (x ^ y).to_bytes(nb, "big"), full))
    lite = ["", "El Salvador"]
    for s in strings:
        bs = s.encode()
        if len(bs) in ENT_SIZES:
            E.append((f"ascii:{s[:24]!r}", bs, full))
        h = hashlib.sha256(bs).digest()
        E.append((f"sha256:{s[:24]!r}", h, lite))
        E.append((f"sha256_16:{s[:24]!r}", h[:16], lite))
    return E


# ---------------------------------------------------------------- family 4
def pairing_forms(heavy=True):
    """(tag, key32) keys and (tag, seed) HD seeds from one serial keyed by the other."""
    keys, seeds = [], []
    X = [("Astr", A_STR), ("Ad", A_D), ("Bstr", B_STR), ("Bd", B_D)]
    for (nx, x), (ny, y) in itertools.permutations(X, 2):
        if nx[0] == ny[0]: continue
        xb, yb = x.encode(), y.encode()
        m = hmac.new(xb, yb, hashlib.sha512).digest()
        keys += [(f"hmac512({nx},{ny})[:32]", m[:32]), (f"hmac512({nx},{ny})[32:]", m[32:])]
        seeds.append((f"hmac512({nx},{ny})", m))
        m2 = hmac.new(xb, yb, hashlib.sha256).digest()
        keys.append((f"hmac256({nx},{ny})", m2))
        for it in (1, 2048):
            s5 = hashlib.pbkdf2_hmac("sha512", xb, yb, it)
            keys.append((f"pbkdf2_512({nx},{ny},{it})[:32]", s5[:32]))
            seeds.append((f"pbkdf2_512({nx},{ny},{it})", s5))
            s2 = hashlib.pbkdf2_hmac("sha256", xb, yb, it)
            keys.append((f"pbkdf2_256({nx},{ny},{it})", s2))
        keys.append((f"pbkdf2_512({nx},'mnemonic'+{ny})[:32]",
                     hashlib.pbkdf2_hmac("sha512", xb, b"mnemonic" + yb, 2048)[:32]))
        seeds.append((f"pbkdf2_512({nx},'mnemonic'+{ny})",
                      hashlib.pbkdf2_hmac("sha512", xb, b"mnemonic" + yb, 2048)))
        keys.append((f"scrypt14({nx},{ny})", hashlib.scrypt(xb, salt=yb, n=2 ** 14, r=8, p=1, dklen=32)))
        hx, hy = hashlib.sha256(xb).digest(), hashlib.sha256(yb).digest()
        keys.append((f"sha256({nx})^sha256({ny})", bytes(p ^ q for p, q in zip(hx, hy))))
        keys.append((f"sha256(sha256({nx})+sha256({ny}))", hashlib.sha256(hx + hy).digest()))
        if len(xb) == len(yb):
            keys.append((f"sha256({nx} xor {ny})", hashlib.sha256(bytes(p ^ q for p, q in zip(xb, yb))).digest()))
        if heavy:
            s1 = hashlib.scrypt(xb + b"\x01", salt=yb + b"\x01", n=2 ** 18, r=8, p=1, dklen=32, maxmem=2 ** 30)
            s2 = hashlib.pbkdf2_hmac("sha256", xb + b"\x02", yb + b"\x02", 2 ** 16, 32)
            keys.append((f"warpwallet({nx},{ny})", bytes(p ^ q for p, q in zip(s1, s2))))
    return keys, seeds


# ---------------------------------------------------------------- family 5
def index_sequences():
    def chunks(s, k):
        return [int(s[i:i + k]) for i in range(0, len(s), k)]
    ab, ba = A_D + B_D, B_D + A_D
    seqs = {}
    for nm, s in (("A", A_D), ("B", B_D), ("AB", ab), ("BA", ba), ("ABA", ab + A_D),
                  ("BAB", ba + B_D), ("ABAB", ab + ab), ("revAB", ab[::-1])):
        seqs[f"{nm}.d1"] = [int(c) for c in s]
        for k in (2, 3, 4):
            seqs[f"{nm}.d{k}"] = chunks(s, k)
    seqs["A.int"] = [a]; seqs["B.int"] = [b]; seqs["AB.ints"] = [a, b]
    seqs["letters+A"] = [3, 12] + [int(c) for c in A_D] + [1]
    seqs["letters+AB"] = [3, 12] + [int(c) for c in A_D] + [1, 11, 2] + [int(c) for c in B_D]
    for k in list(seqs):
        seqs[k + ".cum"] = list(itertools.accumulate(seqs[k]))
    return seqs

def text_index_forms():
    """(tag, str) readings of the digits as indices into the article and page 72,
    and (tag, words) mnemonic-shaped readings into the BIP-39 list."""
    import article
    lines, sents, paras = article.load()
    words = " ".join(paras).split()
    flat = " ".join(paras)
    nlines = [l for l in lines if l.strip()]
    p72 = []
    try:
        p72 = open("p72.txt", encoding="utf-8").read().split()
    except OSError:
        pass
    targets = [("words", words), ("lines", nlines), ("p72", p72)]
    out, mn = [], []
    for sname, seq in index_sequences().items():
        for base in (0, 1):
            idx = [i - base for i in seq]
            for tname, tgt in targets:
                if not tgt: continue
                mod = [i % len(tgt) for i in idx]
                sel = [tgt[i] for i in mod]
                out.append((f"{sname}/b{base}/{tname}", " ".join(sel)))
                out.append((f"{sname}/b{base}/{tname}/initials", "".join(w[0] for w in sel if w)))
                if all(0 <= i < len(tgt) for i in idx) and mod != idx:
                    pass
            chars = "".join(flat[i % len(flat)] for i in idx)
            out.append((f"{sname}/b{base}/chars", chars))
            # (line, col) pairs
            if len(idx) >= 2:
                pc = []
                for i in range(0, len(idx) - 1, 2):
                    l = nlines[idx[i] % len(nlines)]
                    pc.append(l[idx[i + 1] % max(len(l), 1)] if l else "")
                out.append((f"{sname}/b{base}/linecol", "".join(pc)))
        if len(seq) in (12, 15, 18, 21, 24):
            try:
                import bip39_index as BI
                for base in (0, 1):
                    ws = BI.to_words(seq, base, True)
                    if ws: mn.append((f"{sname}/b{base}/bip39", ws))
            except Exception:
                pass
    return out, mn


# ---------------------------------------------------------------- family 6
def transforms():
    import mirror_serial as MS
    def hexint(s):
        return str(int(s, 16)) if s and all(c in "0123456789abcdefABCDEF" for c in s) and len(s) <= 64 else None
    def inthex(s):
        return format(int(s), "x") if s.isdigit() and len(s) <= 80 else None
    def b58(s):
        try:
            bs = bytes.fromhex(s) if len(s) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in s) else s.encode()
            return b58enc(bs) if len(bs) <= 64 else None
        except ValueError:
            return None
    def dw(op):
        return lambda s: digitwise(s, (B_D if s == A_D else A_D)[:len(s)].ljust(len(s), "0"), op) if s.isdigit() and len(s) == 8 else None
    T = [
        ("rev", lambda s: s[::-1]),
        ("rot180", lambda s: MS.rot180(s)),
        ("mirror", lambda s: MS.mirror(s)),
        ("upper", lambda s: s.upper() if s != s.upper() else None),
        ("lower", lambda s: s.lower() if s != s.lower() else None),
        ("sha256hex", lambda s: hashlib.sha256(s.encode()).hexdigest()),
        ("dsha256hex", lambda s: hashlib.sha256(hashlib.sha256(s.encode()).digest()).hexdigest()),
        ("sha256hex16", lambda s: hashlib.sha256(s.encode()).hexdigest()[:32]),
        ("hex->int", hexint), ("int->hex", inthex), ("base58", b58),
        ("+A", lambda s: s + A_D if not s.endswith(A_D) else None),
        ("+B", lambda s: s + B_D if not s.endswith(B_D) else None),
        ("A+", lambda s: A_D + s if not s.startswith(A_D) else None),
        ("B+", lambda s: B_D + s if not s.startswith(B_D) else None),
        ("+ A", lambda s: s + " " + A_STR), ("+ B", lambda s: s + " " + B_STR),
        ("+ElSalvador", lambda s: s + "El Salvador"), ("ElSalvador+", lambda s: "El Salvador" + s),
        ("+ El Salvador", lambda s: s + " El Salvador"),
        ("+OVERDOSE", lambda s: s + "OVERDOSE"), ("+bitcoin", lambda s: s + "bitcoin"),
        ("dw_sum", dw(lambda p, q: p + q)), ("dw_xor", dw(lambda p, q: p ^ q)),
        ("dw_diff", dw(lambda p, q: p - q)),
        ("interleave_A", lambda s: interleave(s, A_D) if s != A_D and len(s) <= 32 else None),
        ("interleave_B", lambda s: interleave(s, B_D) if s != B_D and len(s) <= 32 else None),
        ("sort", lambda s: "".join(sorted(s)) if s != "".join(sorted(s)) else None),
        ("digitsum", lambda s: str(sum(int(c) for c in s if c.isdigit())) if any(c.isdigit() for c in s) else None),
        ("tile2", lambda s: s * 2 if len(s) <= 40 else None),
        ("digits", lambda s: "".join(c for c in s if c.isdigit()) if not s.isdigit() and any(c.isdigit() for c in s) else None),
        ("alpha", lambda s: "".join(c for c in s if c.isalpha()) if not s.isalpha() and any(c.isalpha() for c in s) else None),
        ("strip0", lambda s: s.lstrip("0") if s.startswith("0") else None),
        ("even", lambda s: s[0::2] if len(s) >= 4 else None), ("odd", lambda s: s[1::2] if len(s) >= 4 else None),
        ("half1", lambda s: s[:len(s) // 2] if len(s) >= 8 else None), ("half2", lambda s: s[len(s) // 2:] if len(s) >= 8 else None),
        ("swaphalves", lambda s: s[len(s) // 2:] + s[:len(s) // 2] if len(s) >= 4 else None),
    ]
    return T

def bfs_forms(depth, cap, log=None):
    """Closure of the transform set over the serial pair; returns (tag, str) nodes,
    and whether the cap truncated the frontier (never silently)."""
    T = transforms()
    seeds = [A_D, B_D, A_STR, B_STR, A_D + B_D, B_D + A_D, A_STR + B_STR, A_D + " " + B_D]
    seen = {s: "seed" for s in seeds}
    frontier = list(seeds)
    truncated = False
    for d in range(1, depth + 1):
        nxt = []
        for s in frontier:
            for name, fn in T:
                try:
                    t = fn(s)
                except Exception:
                    t = None
                if not t or t == s or len(t) > 200 or t in seen: continue
                seen[t] = f"{seen[s]}>{name}"
                nxt.append(t)
                if len(seen) >= cap:
                    truncated = True; break
            if truncated: break
        if log: log(f"  discovery depth {d}: {len(nxt):,} new nodes ({len(seen):,} total)"
                    f"{'  [CAP HIT -- frontier truncated]' if truncated else ''}\n")
        frontier = nxt
        if truncated: break
    return [(v, k) for k, v in seen.items()], truncated


# ---------------------------------------------------------------- plugins
def plugin_forms(log=None, pattern="combo_*.py"):
    out = []
    for path in sorted(glob.glob(pattern)):
        mod = os.path.splitext(os.path.basename(path))[0]
        try:
            m = importlib.import_module(mod)
            forms = list(m.forms())
            out += [(f"{mod}:{t}", s) for t, s in forms]
            if log: log(f"  plugin {mod}: {len(forms):,} forms\n")
        except Exception as e:
            if log: log(f"  plugin {mod}: FAILED to load ({e!r}) -- its forms are NOT covered\n")
    return out


def _path_seeds():
    """Seeds a plugin-supplied BIP-32 path is applied to: the 5 seed types of the
    serial strings and clue words, plus the structural entropies' mnemonics."""
    from hd_sweep import seeds_from
    out = []
    for s in (A_STR, B_STR, A_D, B_D, A_D + B_D, B_D + A_D, A_STR + B_STR,
              "El Salvador", "OVERDOSE", "Max Keiser", "bitcoin"):
        for nm, seed in seeds_from(s).items():
            out.append((f"{s[:20]}/{nm}", seed))
    try:
        from mnemonic import Mnemonic
        M = Mnemonic("english")
        for tag, e, _ in entropy_forms([]):
            out.append((f"ent:{tag}", Mnemonic.to_seed(M.to_mnemonic(e), "")))
    except Exception:
        pass
    return out

def _apply_path(sw, tag, path, seeds):
    from hd_sweep import derive
    for nm, seed in seeds:
        try: sw.key(f"{tag}|{nm}|{path}", derive(seed, path))
        except Exception: continue


# ---------------------------------------------------------------- the sweep
class Sweep:
    def __init__(self, orc, paths, log):
        from full_sweep import spks_for_key
        from spk_extra import spks_extra
        self.spks_for_key, self.spks_extra = spks_for_key, spks_extra
        self.orc, self.paths, self.log = orc, paths, log
        self.meta, self.spks, self.hits = [], [], []
        self.n = self.nkeys = self.certif = self.bip = self.bipn12 = self.bipn24 = 0
        self.t0 = time.time()
        self.MN = {}
        try:
            from mnemonic import Mnemonic
            for lang in ("english", "spanish", "french", "italian", "portuguese", "czech"):
                try: self.MN[lang] = Mnemonic(lang)
                except Exception: pass
        except Exception:
            pass
        self.MNE = self.MN.get("english")
        self.bipn = {}          # (lang, nwords) -> candidates tested

    def flush(self):
        if not self.spks: return
        for j, bal in self.orc.check(self.spks):
            self.hits.append((self.meta[j], bal))
            self.log(f"\n  *** INDEX HIT {bal} sats :: {self.meta[j]}\n")
        self.meta, self.spks = [], []

    def key(self, tag, k):
        if not (0 < int.from_bytes(k, "big") < N): return
        self.nkeys += 1
        for st, spk in list(self.spks_for_key(k)) + list(self.spks_extra(k)):
            self.meta.append(f"{tag}|{st}"); self.spks.append(spk); self.n += 1
        if len(self.spks) >= 50000: self.flush()

    def material(self, tag, s):
        checked = False
        if isinstance(s, str) and s.startswith("mn:"):
            try:
                _, lang, phrase = s.split(":", 2)
            except ValueError:
                return
            self.mnemonic_words(tag, phrase.split(), lang)
            s, checked = phrase, True
        if isinstance(s, str):
            flat = s.replace(" ", "")
            if wif_valid(flat):
                self.certif += 1; self.log(f"\n  *** WIF-VALID STRING :: {tag} :: {flat}\n")
            ws = s.lower().split()
            if not checked and len(ws) in (12, 15, 18, 21, 24):
                for lang, M in self.MN.items():
                    if all(w in M.wordlist for w in ws):
                        self.mnemonic_words(tag, ws, lang); break
            hs = s.strip()
            if len(hs) == 64:
                try: self.key(f"{tag}|literal_hex", bytes.fromhex(hs))
                except ValueError: pass
            bs = s.encode()
        else:
            bs = s
            if len(bs) == 32: self.key(f"{tag}|raw32", bs)
        for hn, k in direct_bytes(bs).items():
            self.key(f"{tag}|{hn}", k)

    def hd(self, tag, s):
        from hd_sweep import seeds_from, derive
        for sname, seed in seeds_from(s).items():
            for p in self.paths:
                try: self.key(f"{tag}|{sname}:{p}", derive(seed, p))
                except Exception: continue

    def seed(self, tag, seed):
        from hd_sweep import derive
        for p in self.paths:
            try: self.key(f"{tag}|seed:{p}", derive(seed, p))
            except Exception: continue

    def entropy(self, tag, e, passphrases):
        if not self.MNE or len(e) not in ENT_SIZES: return
        from mnemonic import Mnemonic
        mn = self.MNE.to_mnemonic(e)
        for pw in passphrases:
            self.seed(f"{tag}|mn|pw={pw!r}", Mnemonic.to_seed(mn, pw))
        self.material(f"{tag}|mnemonic_as_text", mn)

    def mnemonic_words(self, tag, ws, lang="english"):
        M = self.MN.get(lang)
        if not M or len(ws) not in (12, 15, 18, 21, 24): return
        self.bipn[(lang, len(ws))] = self.bipn.get((lang, len(ws)), 0) + 1
        mn = " ".join(ws)
        try:
            valid = M.check(mn)
        except Exception:
            valid = False
        if valid:
            self.bip += 1; self.log(f"\n  *** CHECKSUM-VALID {lang.upper()} MNEMONIC :: {tag} :: {mn}\n")
            from mnemonic import Mnemonic
            for pw in PASSPHRASES:
                self.seed(f"{tag}|valid_mn[{lang}]|pw={pw!r}", Mnemonic.to_seed(mn, pw))

    def chance(self):
        """Expected checksum-valid count if every tested mnemonic were random."""
        return sum(n / (2 ** (k // 3)) for (_l, k), n in self.bipn.items())

    def tested_summary(self):
        by = {}
        for (l, k), n in self.bipn.items(): by[l] = by.get(l, 0) + n
        return ", ".join(f"{l} {n:,}" for l, n in sorted(by.items())) or "none"

    def progress(self, what):
        self.log(f"\r  {what}: {self.n:,} scripts, {self.nkeys:,} keys, "
                 f"{self.n / max(time.time() - self.t0, 1e-9):,.0f}/s   ")


# ---------------------------------------------------------------- selftest
class _Fake:
    def __init__(self, spk): self.spk = spk
    def check(self, spks): return [(j, 1) for j, s in enumerate(spks) if s == self.spk]

def selftest():
    ok = True
    def rep(msg, good):
        nonlocal ok; ok &= bool(good); sys.stderr.write(f"  {msg}: {'OK' if good else 'FAIL'}\n")
    rep("WIF validator accepts a real WIF", wif_valid("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ"))
    rep("WIF validator rejects a corrupted WIF", not wif_valid("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTX"))
    rep("a+b = 123121574", numeric_values()["dec:a+b"] == 123121574)
    rep("interleave(a,b) = 7466824719781640", interleave(A_D, B_D) == "7466824719781640")
    rep("digitwise sum mod 10 = 12010574", digitwise(A_D, B_D, lambda p, q: p + q) == "12010574")
    # BIP-39 end-to-end vector
    try:
        from mnemonic import Mnemonic
        from hd_sweep import derive, addr_p2pkh
        from coincurve import PrivateKey
        mn = Mnemonic("english").to_mnemonic(b"\0" * 16)
        good = mn.split()[-1] == "about"
        k = derive(Mnemonic.to_seed(mn, ""), "m/44'/0'/0'/0/0")
        addr = addr_p2pkh(PrivateKey(k).public_key.format(compressed=True))
        rep("BIP-39 zero-entropy vector -> 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA",
            good and addr == "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA")
    except Exception as e:
        rep(f"BIP-39 vector (exception {e!r})", False)
    # planted key must be found through the same code path
    from full_sweep import spks_for_key
    kp = hashlib.sha256(b"serial_combine plant").digest()
    spk = dict(spks_for_key(kp))["p2pkh_c"]
    sw = Sweep(_Fake(spk), [], lambda m: None)
    sw.material("plant", "serial_combine plant"); sw.flush()
    rep("planted brainwallet found by the sweep path", any("plant|sha256|p2pkh_c" in h[0] for h in sw.hits))
    sw2 = Sweep(_Fake(spk), [], lambda m: None)
    sw2.material("other", "not the plant"); sw2.flush()
    rep("an unrelated phrase is NOT a hit", not sw2.hits)
    try:
        from mnemonic import Mnemonic
        ms = Mnemonic("spanish"); mf = Mnemonic("french")
        good = ms.check(ms.to_mnemonic(b"\x01" * 16)) and mf.check(mf.to_mnemonic(b"\x02" * 16)) \
               and not ms.check(mf.to_mnemonic(b"\x02" * 16))
        rep("Spanish/French wordlists checksum-validate their own mnemonics and reject each other's", good)
        sw3 = Sweep(_Fake(b"\x00"), [], lambda m: None)
        sw3.material("t", "mn:spanish:" + ms.to_mnemonic(b"\x03" * 16))
        rep("an mn:<lang>: value is checksum-tested in that language", sw3.bip == 1 and ("spanish", 12) in sw3.bipn)
    except Exception as e:
        rep(f"multi-language mnemonics (exception {e!r})", False)
    S = string_forms(); rep(f"{len(S):,} combined string forms", len(S) > 1500)
    m, k = numeric_forms(); rep(f"{len(m):,} numeric materials, {len(k):,} raw integer keys", len(k) > 100)
    ti, mnw = text_index_forms(); rep(f"{len(ti):,} text-index readings, {len(mnw)} mnemonic-shaped", len(ti) > 300)
    nodes, tr = bfs_forms(1, 10 ** 6); rep(f"discovery depth 1: {len(nodes):,} nodes", len(nodes) > 100 and not tr)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="numeric,strings,entropy,pairing,textindex,discovery,plugins")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--cap", type=int, default=60000, help="max discovery nodes per round")
    ap.add_argument("--loop", action="store_true", help="widen discovery depth to 4")
    ap.add_argument("--no-heavy", action="store_true", help="skip WarpWallet scrypt 2^18")
    ap.add_argument("--plugin-glob", default="combo_*.py", help="which plugin modules to sweep")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    log = lambda m: (sys.stderr.write(m), sys.stderr.flush())
    log("\n  SELFTEST\n")
    if not selftest(): sys.exit("setup wrong; refusing to sweep")
    if a.selftest: return
    import continuous_solver as CS
    from hd_sweep import build_paths
    orc = CS.IndexOracle()
    if not orc.ready: sys.exit(f"no oracle: {orc.why}")
    if not orc.control(): sys.exit("positive control failed; a null would be void")
    log(f"  oracle control OK ({orc.name})\n")
    paths = build_paths()
    sw = Sweep(orc, paths, log)
    fams = set(a.families.split(","))
    strings = string_forms()
    if "numeric" in fams:
        mats, keys = numeric_forms()
        for t, s in mats: sw.material("num:" + t, s)
        for t, k in keys: sw.key("num:" + t, k)
        sw.flush(); sw.progress("numeric"); log("\n")
    if "strings" in fams:
        for i, s in enumerate(strings, 1):
            sw.material("str:" + s[:40], s); sw.hd("str:" + s[:40], s)
            if i % 100 == 0: sw.progress(f"strings {i:,}/{len(strings):,}")
        sw.flush(); sw.progress("strings"); log("\n")
    if "entropy" in fams:
        E = entropy_forms(strings)
        for i, (t, e, pws) in enumerate(E, 1):
            sw.entropy("ent:" + t, e, pws)
            if i % 50 == 0: sw.progress(f"entropy {i:,}/{len(E):,}")
        sw.flush(); sw.progress("entropy"); log("\n")
    if "pairing" in fams:
        keys, seeds = pairing_forms(heavy=not a.no_heavy)
        for t, k in keys: sw.key("pair:" + t, k)
        for t, s in seeds: sw.seed("pair:" + t, s)
        sw.flush(); sw.progress("pairing"); log("\n")
    if "textindex" in fams:
        ti, mnw = text_index_forms()
        for t, s in ti: sw.material("idx:" + t, s); sw.hd("idx:" + t, s)
        for t, ws in mnw: sw.mnemonic_words("idx:" + t, ws)
        sw.flush(); sw.progress("textindex"); log("\n")
    if "plugins" in fams:
        P = plugin_forms(log, a.plugin_glob)
        n_plain = sum(1 for _t, v in P if not (isinstance(v, str) and v.startswith(("mn:", "hex:", "path:"))))
        do_hd = n_plain <= 8000
        log(f"  plugins: {len(P):,} forms ({n_plain:,} plain text); HD seeds x 72 paths on plain text "
            f"{'ON' if do_hd else 'OFF (>8000 plain forms; direct hashes only)'}\n")
        path_seeds = None
        for i, (t, s) in enumerate(P, 1):
            if isinstance(s, str) and s.startswith("hex:"):
                try: s = bytes.fromhex(s[4:])
                except ValueError: continue
                sw.material("plug:" + t, s)
                if len(s) in ENT_SIZES: sw.entropy("plug:" + t, s, ["", "El Salvador"])
            elif isinstance(s, str) and s.startswith("path:"):
                if path_seeds is None: path_seeds = _path_seeds()
                _apply_path(sw, "plug:" + t, s[5:].strip(), path_seeds)
            else:
                sw.material("plug:" + t, s)
                if do_hd: sw.hd("plug:" + t, s)
            if i % 500 == 0: sw.progress(f"plugins {i:,}/{len(P):,}")
        sw.flush(); sw.progress("plugins"); log("\n")
    depth = a.depth
    while "discovery" in fams:
        nodes, truncated = bfs_forms(depth, a.cap, log)
        for i, (t, s) in enumerate(nodes, 1):
            sw.material("disc:" + t, s)
            if i % 2000 == 0: sw.progress(f"discovery d{depth} {i:,}/{len(nodes):,}")
        sw.flush(); sw.progress(f"discovery d{depth}"); log("\n")
        if truncated: log(f"  NOTE: depth {depth} was capped at {a.cap:,} nodes; coverage of that depth is PARTIAL\n")
        if not a.loop or depth >= 4: break
        depth += 1; a.cap *= 4
        log(f"\n  --loop: widening discovery to depth {depth} (cap {a.cap:,})\n")
    sw.flush()
    exp = sw.chance()
    log(f"\n  {sw.n:,} scripts from {sw.nkeys:,} keys vs {orc.name}: {len(sw.hits)} index hit(s); "
        f"{sw.certif} checksum-valid WIF; {sw.bip} checksum-valid mnemonic(s) "
        f"(chance expectation {exp:.2f}; mnemonic candidates tested: {sw.tested_summary()})\n")
    if sw.hits:
        with open("serial_combine_hits.tsv", "w") as f:
            for t, bal in sw.hits: f.write(f"{bal}\t{t}\n")
        log("  hits -> serial_combine_hits.tsv  (re-derive by hand before believing any of them)\n")
    elif not sw.certif and sw.bip <= exp + 1 + 2 * (exp ** 0.5):
        log("  no combination of the two serials reaches a funded address or a self-certifying key.\n")


if __name__ == "__main__":
    main()
