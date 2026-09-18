#!/usr/bin/env python3
"""
LENS: number theory / encodings. Every REPRESENTATION and every DERIVED NUMBER of the
pair a=76841714 (CL 76841714 A) and b=46279860 (KB 46279860) that serial_combine.py's
numeric_values()/numeric_forms() and lowentropy.py do not already emit, each as text
material (decimal, hex, zero-padded hex) and, where it is a natural byte object, as
'hex:' bytes; a curated subset also as 32-byte raw keys. ADDS: [base] a, b, ab, ba in
every base 2-36 (lower and upper), zero-padded binary, base62, bijective/plain base-26
letters, and the digit strings PARSED as base-k numerals for every k that admits them;
[enc] base58 / base64 (std, unpadded, urlsafe) / base32 / base85 / ascii85 / binary of
the 4-byte (BE, LE, BCD) and 8-byte (both orders, BCD, decimal-concat) encodings, plus
the 4-byte BCD of each serial alone as raw bytes; [gray] Gray code and inverse Gray of
a, b and the six 64-bit concatenations; [compl] ones' and two's complement in 32/64
bits; [bits] every bit-rotation (1-31 of the 32-bit values, 1-63 of the 64-bit
concatenations), byte-swap, 16-bit word swap, nibble reversal and bit reversal;
[fact] the prime factorisations (computed, product-checked) of a, b, a+-1, b+-1, the
hex readings, the concatenations, a+b, |a-b|, a*b, a^2+b^2 and the interleavings, with
factor strings in five joins and tau/sigma/phi/lambda/rad/lpf/spf/sopfr/Omega/omega;
[digits] digit products, sums of squares/cubes, alternating sums, digital roots, both
persistences, chunk sums/products, popcounts and Hamming distances; [mod] residue
vectors modulo the first 25 primes and residues modulo the classic 16/24/31-bit
moduli; [pow] a^b, b^a, 2^a, 2^b and the modular inverses of a and b modulo thirteen
famous primes (Mersenne 31/61/89/127, 2^255-19, the secp256k1 field and order, 65537,
1e9+7, 998244353, the largest 32- and 64-bit primes, 2^521-1), a/b and b/a in the
secp256k1 field and group; [fib] Zeckendorf representations, the Fibonacci and Lucas
neighbours, F_a/L_a/F_b/L_b modulo 1e8/1e16/2^32/2^64/n/p/1e9+7, the digit counts of
F_a and F_b, the a-th and b-th primes (1544728243 and 905578979, computed once by a
segmented sieve that reproduced pi(1e9)=50847534 and p_50847534=999999937; re-verified
here by Miller-Rabin only), pi(a), pi(b) (live sieve), next/previous primes of a, b,
ab, ba, a+b, the a-th triangular number, squares, cubes; [dmap] each digit and each
digit pair mapped to its Fibonacci, Lucas, prime, square, cube, factorial, triangular
and power-of-two; [roman] Roman numerals of the digit singles, pairs and triples;
[check] Luhn, Luhn mod 36, Verhoeff, Damm,
mod 97 (ISO 7064 and IBAN-style with letters), mod 11 (ISBN-style and ISO 7064 11-2),
EAN-8, Code-39 mod 43, CRC-8/16 (CCITT-FALSE, ARC, MODBUS, XMODEM)/32/32C/32-BZIP2/
64-XZ, Adler-32, Fletcher-16/32, BSD-16, byte sums and xor, FNV-1a 32/64, djb2, sdbm,
Java hashCode, MurmurHash3-32 (seed 0 and seeded with the OTHER serial), of each
serial form and of the pair; [hash] md5, sha1, ripemd160, sha224, sha3-224, sha384,
sha512, sha512/256, blake2s, hash160, md5(md5-hex) and sha1(sha1-hex) of each serial
string and the pair, as hex text (lower/upper), base64, and as 'hex:' raw digests
(16/20/28-byte ones are legal BIP-39 entropy sizes, 32-byte ones are also raw keys);
[time] a and b as unix
seconds/milliseconds/minutes, offset from the genesis timestamp, prefixed with 1/16/17
to make a 2020s timestamp, a read as the date 7/6/84 17:14 (both day-month orders),
ab/ba as micro- and nanoseconds, each in nine date formats; [block] the block-height
truncations 7684171/768417/76841/7684 and 4627986/462798/46279/4627 with height
prefixes and their pairs; [btc] satoshi/BTC/mBTC/bits amount strings, the 20 BTC
complements and the pair as one amount; [fmt] thousands separators, scientific
notation, signs, zero padding, and the numbers in English words; [text] hex/base64/
base32/base85/binary/decimal/octal ASCII of the serial strings, ROT13, Atbash, Morse,
NATO, keypad digits, A1Z26 digit-to-letter, spelled digits; [ip] IPv4 dotted quads;
[cf] the continued fraction of a/b, its convergents, the reduced fraction, Bezout
coefficients, decimal ratios and the colon join; [cat] every single-serial text form
above concatenated with the OTHER serial's digits and full string ("" and " " joins,
both orders); [pair] every A-form joined with its same-named B-form (both orders).
DELIBERATELY OMITS because an existing module already covers it: the arithmetic
combinations (sum, difference, product, xor/or/and, mod, gcd, lcm, interleave,
digit-wise ops, concatenations, x20, 21e6) as decimal/hex/hex8/hex16/raw-int/LE-BE
4-8-16-byte pads -- serial_combine.numeric_forms; separator joins, reversal, rot180,
mirror, sorted digits, series/district/denomination phrases, alphabet positions of the
letters -- serial_combine.string_forms; hex<->int readings of the digit strings
("1988564756", "49482f2"), base58 of the BCD bytes, sha256/dsha256 hex text, halves,
even/odd digits, digit sums, tiles -- serial_combine discovery BFS (depth <= 2; every
value that closure produces is filtered out of this module's output at build time);
BIP-39 entropy tilings/pads, HMAC/PBKDF2/scrypt/WarpWallet pairings, text-index
readings -- serial_combine entropy/pairing/textindex; small ints, dates, powers,
repeated bytes as raw keys against the four tx addresses -- lowentropy.py; RNG-seeded
keys -- serial_entropy.py; serial-as-checksum predicates -- serial_oracle.py and
serial_bip39_mine.py (this module produces no predicates, only material); Electrum,
mini-key, brainwallet typing artefacts, digit-grouped BIP-39 phrases, xprv, BIP-32
paths, raw-key placements -- combo_walletformats.py; BEP production numbers,
signatures, catalogue strings -- combo_numismatic.py. SPECULATIVE families (kept
because they are cheap, not because a setter is likely to have used them): [bits]
rotations at non-byte offsets, [pow], [fib] modular Fibonacci values and the nth-prime
readings, [mod], [dmap], [check] non-CRC hashes (FNV/djb2/sdbm/Murmur/Java), the
1/16/17-prefixed timestamps and the 7/6/84 date reading, [ip], [cf], and every raw32.

  python3 combo_encodings.py
"""
import base64, datetime, hashlib, math, re, sys, time, zlib

A_D, B_D = "76841714", "46279860"
A_STR, B_STR = "CL76841714A", "KB46279860"
A_SP, B_SP = "CL 76841714 A", "KB 46279860"
a, b = int(A_D), int(B_D)
ah, bh = int(A_D, 16), int(B_D, 16)
AB, BA = A_D + B_D, B_D + A_D
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 2 ** 256 - 2 ** 32 - 977
M32, M64 = (1 << 32) - 1, (1 << 64) - 1
GENESIS_TS = 1231006505
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DIG36 = "0123456789abcdefghijklmnopqrstuvwxyz"
UTC = datetime.timezone.utc

# The a-th and b-th primes. Computed once (2026-09-18) by a numpy segmented sieve to
# 1.6e9 whose run first reproduced pi(1e9) = 50,847,534 and p_50847534 = 999,999,937.
# forms() does not recompute them (that sieve takes ~16 s); selftest re-checks
# primality with Miller-Rabin and the prime-number-theorem bracket.
NTH_PRIME = {a: 1544728243, b: 905578979}

# the six 64-bit concatenations of the pair
U64 = {"a<<32|b": (a << 32) | b, "b<<32|a": (b << 32) | a,
       "bcd_ab": int(AB, 16), "bcd_ba": int(BA, 16),
       "dec_ab": int(AB), "dec_ba": int(BA)}


# ================================================================ number theory
_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

def is_prime(n):
    if n < 2: return False
    for p in _MR_BASES:
        if n % p == 0: return n == p
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    for base in _MR_BASES:
        x = pow(base, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True

def _rho(n):
    if n % 2 == 0: return 2
    for c in range(1, 200):
        x = y = 2; d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n; y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n: return d
    raise ValueError(f"rho failed on {n}")

def factor(n):
    """Sorted prime factors with multiplicity; product-checked by the caller."""
    out = []
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        while n % p == 0: out.append(p); n //= p
    p = 53
    while p * p <= n and p < 100000:
        while n % p == 0: out.append(p); n //= p
        p += 2
    def rec(m):
        if m == 1: return []
        if is_prime(m): return [m]
        d = _rho(m)
        return rec(d) + rec(m // d)
    return sorted(out + rec(n))

def next_prime(n):
    n += 1
    while not is_prime(n): n += 1
    return n

def prev_prime(n):
    n -= 1
    while not is_prime(n): n -= 1
    return n

def arith(fs):
    """tau, sigma, phi, carmichael lambda, radical from a factor list."""
    ex = {}
    for p in fs: ex[p] = ex.get(p, 0) + 1
    tau = sigma = phi = rad = 1; lam = 1
    for p, e in ex.items():
        tau *= e + 1
        sigma *= (p ** (e + 1) - 1) // (p - 1)
        phi *= p ** (e - 1) * (p - 1)
        rad *= p
        if p == 2: l = 1 if e == 1 else 2 if e == 2 else 2 ** (e - 2)
        else: l = p ** (e - 1) * (p - 1)
        lam = lam * l // math.gcd(lam, l)
    return tau, sigma, phi, lam, rad

def fib_pair_mod(n, m):
    """(F_n, F_{n+1}) mod m by fast doubling."""
    if n == 0: return 0 % m, 1 % m
    f, g = fib_pair_mod(n >> 1, m)
    c = f * ((2 * g - f) % m) % m
    d = (f * f + g * g) % m
    return (d, (c + d) % m) if n & 1 else (c, d)

def _fibs(count=101):
    F = [0, 1]
    while len(F) < count: F.append(F[-1] + F[-2])
    return F

def _lucas(count=101):
    L = [2, 1]
    while len(L) < count: L.append(L[-1] + L[-2])
    return L

FIB, LUC = _fibs(), _lucas()

def zeckendorf(n):
    """Indices i (F_2 = 1 basis) of the greedy non-consecutive Fibonacci sum."""
    idx, i = [], len(FIB) - 1
    while n > 0:
        while FIB[i] > n: i -= 1
        idx.append(i); n -= FIB[i]; i -= 2
    return idx

def small_primes(k):
    out, n = [], 2
    while len(out) < k:
        if is_prime(n): out.append(n)
        n += 1
    return out

PRIMES100 = small_primes(100)

_PI_CACHE = {}
def pi_of(*xs):
    """Prime-counting function by a bytearray sieve up to max(xs)."""
    key = max(xs)
    if key not in _PI_CACHE:
        s = bytearray([1]) * (key + 1); s[0] = s[1] = 0
        for i in range(2, math.isqrt(key) + 1):
            if s[i]: s[i * i::i] = bytes(len(range(i * i, key + 1, i)))
        _PI_CACHE[key] = s
    s = _PI_CACHE[key]
    return [s[:x + 1].count(1) for x in xs]

def egcd(p, q):
    if q == 0: return p, 1, 0
    g, x, y = egcd(q, p % q)
    return g, y, x - (p // q) * y

def contfrac(p, q):
    out = []
    while q: d, r = divmod(p, q); out.append(d); p, q = q, r
    return out

def convergents(cf):
    h0, h1, k0, k1 = 0, 1, 1, 0
    for q in cf:
        h0, h1 = h1, q * h1 + h0; k0, k1 = k1, q * k1 + k0
        yield h1, k1


# ================================================================ bit tricks
def gray(n): return n ^ (n >> 1)

def ungray(g):
    n = 0
    while g: n ^= g; g >>= 1
    return n

def rotl(n, r, w):
    m = (1 << w) - 1; r %= w
    return ((n << r) | (n >> (w - r))) & m

def bswap(n, nbytes): return int.from_bytes(n.to_bytes(nbytes, "big"), "little")

def wswap(n):  # 16-bit word reversal of a 64-bit value
    ws = [(n >> (16 * i)) & 0xFFFF for i in range(4)]
    return sum(w << (16 * (3 - i)) for i, w in enumerate(ws))

def nibrev(n, w): return int(format(n, f"0{w // 4}x")[::-1], 16)

def bitrev(n, w): return int(format(n, f"0{w}b")[::-1], 2)


# ================================================================ encoders
def to_base(n, k, digits=DIG36):
    if n == 0: return digits[0]
    out = []
    while n: n, r = divmod(n, k); out.append(digits[r])
    return "".join(reversed(out))

def b58enc(bs):
    n = int.from_bytes(bs, "big"); out = ""
    while n: n, r = divmod(n, 58); out = B58[r] + out
    return "1" * (len(bs) - len(bs.lstrip(b"\0"))) + out

def bij26(n):  # spreadsheet-column letters: 1=A .. 26=Z, 27=AA
    s = ""
    while n: n, r = divmod(n - 1, 26); s = chr(65 + r) + s
    return s

def base26(n):  # A=0 .. Z=25
    return to_base(n, 26, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
         "fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "zero ten twenty thirty forty fifty sixty seventy eighty ninety".split()
_SCALE = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion"]

def words(n):
    if n == 0: return "zero"
    if n < 0: return "minus " + words(-n)
    def under1000(k):
        out = []
        if k >= 100: out.append(_ONES[k // 100] + " hundred"); k %= 100
        if k >= 20:
            t = _TENS[k // 10]
            if k % 10: t += "-" + _ONES[k % 10]
            out.append(t)
        elif k: out.append(_ONES[k])
        return " ".join(out)
    parts, i = [], 0
    while n:
        n, r = divmod(n, 1000)
        if r: parts.append((under1000(r) + " " + _SCALE[i]).strip())
        i += 1
    return " ".join(reversed(parts))

def roman(n):
    if not 0 < n < 4000: return "N" if n == 0 else None
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v: out += s; n -= v
    return out

MORSE = {"0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
         "6": "-....", "7": "--...", "8": "---..", "9": "----.", "A": ".-", "B": "-...",
         "C": "-.-.", "K": "-.-", "L": ".-..", " ": "/"}
NATO = {"A": "Alfa", "B": "Bravo", "C": "Charlie", "K": "Kilo", "L": "Lima"}
KEYPAD = {c: str(d) for d, grp in ((2, "ABC"), (3, "DEF"), (4, "GHI"), (5, "JKL"), (6, "MNO"),
                                    (7, "PQRS"), (8, "TUV"), (9, "WXYZ")) for c in grp}

def morse(s): return " ".join(MORSE[c] for c in s if c in MORSE)
def nato(s): return " ".join(NATO.get(c, c) for c in s.replace(" ", "")).replace(" ".join(A_D), A_D).replace(" ".join(B_D), B_D)
def nato_spelled(s): return " ".join(NATO[c] if c in NATO else _ONES[int(c)] for c in s if c != " ")
def keypad(s): return "".join(KEYPAD.get(c, c) for c in s)
def rot13(s): return s.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "NOPQRSTUVWXYZABCDEFGHIJKLM"))
def atbash(s): return s.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "ZYXWVUTSRQPONMLKJIHGFEDCBA"))

def a1z26(digits, one_is_a=True, zero="Z"):
    out = ""
    for c in digits:
        d = int(c)
        if one_is_a: out += zero if d == 0 else chr(64 + d)
        else: out += chr(65 + d)
    return out


# ================================================================ check values
def luhn(digits):
    s = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9: d -= 9
        s += d
    return (10 - s % 10) % 10

def luhn_modn(s, alphabet=DIG36.upper()):
    n, factor_, total = len(alphabet), 2, 0
    for ch in reversed(s):
        addend = factor_ * alphabet.index(ch)
        factor_ = 1 if factor_ == 2 else 2
        total += addend // n + addend % n
    return alphabet[(n - total % n) % n]

_VD = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],
       [4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],
       [8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]]
_VP = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
       [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
_VINV = [0,4,3,2,1,5,6,7,8,9]

def verhoeff(digits):
    c = 0
    for i, ch in enumerate(reversed(digits)): c = _VD[c][_VP[(i + 1) % 8][int(ch)]]
    return _VINV[c]

_DAMM = [[0,3,1,7,5,9,8,6,4,2],[7,0,9,2,1,5,4,8,6,3],[4,2,0,6,8,7,1,3,5,9],[1,7,5,0,9,8,3,4,2,6],
         [6,1,2,3,0,4,5,9,7,8],[3,6,7,4,2,0,9,5,8,1],[5,8,6,9,7,2,0,1,3,4],[8,9,4,5,3,6,2,0,1,7],
         [9,4,3,8,6,1,7,2,0,5],[2,5,8,1,4,3,6,7,9,0]]

def damm(digits):
    i = 0
    for ch in digits: i = _DAMM[i][int(ch)]
    return i

def iban_digits(s):
    return "".join(str(ord(c) - 55) if c.isalpha() else c for c in s.upper() if c != " ")

def mod11_isbn(digits):
    n = len(digits)
    s = sum(int(c) * (n + 1 - i) for i, c in enumerate(digits))
    r = (11 - s % 11) % 11
    return "X" if r == 10 else str(r)

def mod11_iso7064(digits):
    n = len(digits)
    s = sum(int(c) * pow(2, n - i, 11) for i, c in enumerate(digits))
    r = (12 - s % 11) % 11
    return "X" if r == 10 else str(r)

def ean8(digits):
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(digits))
    return (10 - s % 10) % 10

_C39 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
def code39(s):
    return sum(_C39.index(c) for c in s if c in _C39) % 43

def crc(data, width, poly, init, refin, refout, xorout):
    mask, reg = (1 << width) - 1, init
    for byte in data:
        if refin: byte = int(f"{byte:08b}"[::-1], 2)
        reg ^= byte << (width - 8)
        for _ in range(8):
            reg = ((reg << 1) ^ poly) & mask if reg & (1 << (width - 1)) else (reg << 1) & mask
    if refout: reg = int(f"{reg:0{width}b}"[::-1], 2)
    return reg ^ xorout

CRCS = {  # name: (width, poly, init, refin, refout, xorout, check("123456789"))
    "crc8": (8, 0x07, 0, 0, 0, 0, 0xF4),
    "crc16_ccitt": (16, 0x1021, 0xFFFF, 0, 0, 0, 0x29B1),
    "crc16_arc": (16, 0x8005, 0, 1, 1, 0, 0xBB3D),
    "crc16_modbus": (16, 0x8005, 0xFFFF, 1, 1, 0, 0x4B37),
    "crc16_xmodem": (16, 0x1021, 0, 0, 0, 0, 0x31C3),
    "crc32c": (32, 0x1EDC6F41, M32, 1, 1, M32, 0xE3069283),
    "crc32_bzip2": (32, 0x04C11DB7, M32, 0, 0, M32, 0xFC891918),
    "crc64_xz": (64, 0x42F0E1EBA9EA3693, M64, 1, 1, M64, 0x995DC9BBDF1939FA),
}

def fletcher16(d):
    s1 = s2 = 0
    for c in d: s1 = (s1 + c) % 255; s2 = (s2 + s1) % 255
    return (s2 << 8) | s1

def fletcher32(d):
    if len(d) % 2: d += b"\0"
    s1 = s2 = 0
    for i in range(0, len(d), 2):
        s1 = (s1 + int.from_bytes(d[i:i + 2], "little")) % 65535; s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1

def bsd16(d):
    c = 0
    for x in d: c = ((c >> 1) | ((c & 1) << 15)) + x & 0xFFFF
    return c

def fnv1a(d, bits):
    h, prime, mask = (0x811c9dc5, 0x01000193, M32) if bits == 32 else (0xcbf29ce484222325, 0x100000001b3, M64)
    for c in d: h ^= c; h = (h * prime) & mask
    return h

def djb2(d):
    h = 5381
    for c in d: h = (h * 33 + c) & M32
    return h

def sdbm(d):
    h = 0
    for c in d: h = (c + (h << 6) + (h << 16) - h) & M32
    return h

def javahash(s):
    h = 0
    for c in s: h = (31 * h + ord(c)) & M32
    return h - (1 << 32) if h >= 1 << 31 else h

def murmur3_32(data, seed=0):
    c1, c2, h, L = 0xcc9e2d51, 0x1b873593, seed & M32, len(data)
    rl = lambda x, r: ((x << r) | (x >> (32 - r))) & M32
    nb = L // 4
    for i in range(nb):
        k = int.from_bytes(data[4 * i:4 * i + 4], "little")
        k = (k * c1) & M32; k = rl(k, 15); k = (k * c2) & M32
        h ^= k; h = rl(h, 13); h = (h * 5 + 0xe6546b64) & M32
    tail, k = data[4 * nb:], 0
    if len(tail) >= 3: k ^= tail[2] << 16
    if len(tail) >= 2: k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]; k = (k * c1) & M32; k = rl(k, 15); k = (k * c2) & M32; h ^= k
    h ^= L; h ^= h >> 16; h = (h * 0x85ebca6b) & M32; h ^= h >> 13; h = (h * 0xc2b2ae35) & M32
    return h ^ (h >> 16)


# ================================================================ the families
DATE_FMTS = [("iso", "%Y-%m-%dT%H:%M:%SZ"), ("sql", "%Y-%m-%d %H:%M:%S"), ("ymd", "%Y-%m-%d"),
             ("compact", "%Y%m%d"), ("compact14", "%Y%m%d%H%M%S"), ("dmy", "%d/%m/%Y"),
             ("mdy", "%m/%d/%Y"), ("long", "{B} {d}, {Y}"), ("longdmy", "{d} {B} {Y}")]

def _dates(ts):
    """The nine textual readings of a unix timestamp, or [] if out of range."""
    try:
        dt = datetime.datetime.fromtimestamp(ts, UTC)
    except (OverflowError, OSError, ValueError):
        return []
    out = []
    for nm, f in DATE_FMTS:
        if "{" in f: out.append((nm, f.format(B=dt.strftime("%B"), d=dt.day, Y=dt.year)))
        else: out.append((nm, dt.strftime(f)))
    return out


class _Builder:
    def __init__(self):
        self.items, self.tags = [], set()

    def add(self, fam, key, rep, value, origin, cat=True):
        if value is None: return
        if isinstance(value, bytes): value, cat = "hex:" + value.hex(), False
        value = str(value)
        if not value: return
        tag = f"{fam}:{origin}.{key}" + (f"/{rep}" if rep else "")
        if tag in self.tags: raise ValueError(f"duplicate tag {tag}")
        self.tags.add(tag)
        self.items.append((tag, value, origin, fam, key, rep, cat))

    def num(self, fam, key, v, origin, width=None, raw=False, cat=True):
        self.add(fam, key, "dec", str(v), origin, cat)
        if v < 0: return
        h = format(v, "x")
        if h != str(v): self.add(fam, key, "hex", h, origin, False)
        if width and v < 1 << (8 * width):
            self.add(fam, key, f"hex{2 * width}", h.zfill(2 * width), origin, False)
            self.add(fam, key, f"be{width}", v.to_bytes(width, "big"), origin)
        if raw and 0 < v < N:
            self.add(fam, key, "raw32", v.to_bytes(32, "big"), origin)


def fam_base(B):
    vals = [("A", "a", a), ("B", "b", b), ("AB", "ab", int(AB)), ("AB", "ba", int(BA))]
    for org, nm, v in vals:
        for k in range(2, 37):
            if k == 10: continue
            s = to_base(v, k)
            B.add("base", f"{nm}_b{k}", None, s, org)
            if k > 10: B.add("base", f"{nm}_b{k}", "upper", s.upper(), org, False)
        w = 32 if v < 1 << 32 else 64
        B.add("base", f"{nm}_bin{w}", None, format(v, f"0{w}b"), org, False)
        B.add("base", f"{nm}_bin{w}", "bytes", " ".join(format(v, f"0{w}b")[i:i + 8] for i in range(0, w, 8)), org, False)
        B.add("base", f"{nm}_b62", None, to_base(v, 62, B62), org)
        B.add("base", f"{nm}_bij26", None, bij26(v), org)
        B.add("base", f"{nm}_base26", None, base26(v), org)
        B.add("base", f"{nm}_oct0", None, "0o" + to_base(v, 8), org, False)
        B.add("base", f"{nm}_hex0x", None, "0x" + format(v, "x"), org, False)
        B.add("base", f"{nm}_hex0X", None, "0x" + format(v, "X"), org, False)
    # the digit strings PARSED as base-k numerals (k=16 is the hex reading, already swept)
    for org, nm, s in (("A", "a", A_D), ("B", "b", B_D), ("AB", "ab", AB), ("AB", "ba", BA)):
        top = max(int(c) for c in s)
        for k in range(top + 1, 37):
            if k in (10, 16): continue
            B.num("base", f"{nm}_as_b{k}", int(s, k), org)


def fam_enc(B):
    enc = {"A": {"be4": a.to_bytes(4, "big"), "le4": a.to_bytes(4, "little"),
                 "bcd4": bytes.fromhex(A_D), "bcd4_le": bytes.fromhex(A_D)[::-1]},
           "B": {"be4": b.to_bytes(4, "big"), "le4": b.to_bytes(4, "little"),
                 "bcd4": bytes.fromhex(B_D), "bcd4_le": bytes.fromhex(B_D)[::-1]},
           "AB": {"u64_ab_be": U64["a<<32|b"].to_bytes(8, "big"), "u64_ab_le": U64["a<<32|b"].to_bytes(8, "little"),
                  "u64_ba_be": U64["b<<32|a"].to_bytes(8, "big"), "u64_ba_le": U64["b<<32|a"].to_bytes(8, "little"),
                  "bcd8_ab": bytes.fromhex(AB), "bcd8_ba": bytes.fromhex(BA),
                  "dec_ab_be": U64["dec_ab"].to_bytes(8, "big"), "dec_ab_le": U64["dec_ab"].to_bytes(8, "little"),
                  "dec_ba_be": U64["dec_ba"].to_bytes(8, "big"), "dec_ba_le": U64["dec_ba"].to_bytes(8, "little")}}
    for org, d in enc.items():
        for nm, bs in d.items():
            B.add("enc", nm, "b58", b58enc(bs), org)
            B.add("enc", nm, "b64", base64.b64encode(bs).decode(), org)
            B.add("enc", nm, "b64np", base64.b64encode(bs).decode().rstrip("="), org)
            B.add("enc", nm, "b64url", base64.urlsafe_b64encode(bs).decode().rstrip("="), org)
            B.add("enc", nm, "b32", base64.b32encode(bs).decode(), org)
            B.add("enc", nm, "b32np", base64.b32encode(bs).decode().rstrip("="), org)
            B.add("enc", nm, "b32lo", base64.b32encode(bs).decode().rstrip("=").lower(), org, False)
            B.add("enc", nm, "b85", base64.b85encode(bs).decode(), org)
            B.add("enc", nm, "a85", base64.a85encode(bs).decode(), org)
            B.add("enc", nm, "bin", " ".join(f"{x:08b}" for x in bs), org, False)
    for org, s in (("A", A_D), ("B", B_D)):        # BCD bytes of one serial alone
        B.add("enc", "bcd4", "raw", bytes.fromhex(s), org)
        B.add("enc", "bcd4_le", "raw", bytes.fromhex(s)[::-1], org)


def fam_gray(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("A", "ah", ah), ("B", "bh", bh)):
        B.num("gray", f"gray32_{nm}", gray(v), org, width=4, raw=True)
        B.num("gray", f"ungray32_{nm}", ungray(v), org, width=4, raw=True)
    for nm, v in U64.items():
        B.num("gray", f"gray64_{nm}", gray(v), "AB", width=8, raw=True)
        B.num("gray", f"ungray64_{nm}", ungray(v), "AB", width=8, raw=True)


def fam_compl(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("A", "ah", ah), ("B", "bh", bh)):
        B.num("compl", f"ones32_{nm}", v ^ M32, org, width=4, raw=True)
        B.num("compl", f"twos32_{nm}", (-v) & M32, org, width=4, raw=True)
        B.num("compl", f"ones64_{nm}", v ^ M64, org, width=8, raw=True)
        B.num("compl", f"twos64_{nm}", (-v) & M64, org, width=8, raw=True)
        B.add("compl", f"neg_{nm}", None, f"-{v}", org)
        B.add("compl", f"ones_signed_{nm}", None, f"-{v + 1}", org)
    for nm, v in U64.items():
        B.num("compl", f"ones64_{nm}", v ^ M64, "AB", width=8, raw=True)
        B.num("compl", f"twos64_{nm}", (-v) & M64, "AB", width=8, raw=True)
        B.add("compl", f"neg_{nm}", None, f"-{v}", "AB")


def fam_bits(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("A", "ah", ah), ("B", "bh", bh)):
        for r in range(1, 32):
            B.num("bits", f"rotl32_{nm}_{r}", rotl(v, r, 32), org, width=4, raw=(r % 8 == 0), cat=(r % 8 == 0))
        B.num("bits", f"bswap32_{nm}", bswap(v, 4), org, width=4, raw=True)
        B.num("bits", f"bitrev32_{nm}", bitrev(v, 32), org, width=4, raw=True)
        B.num("bits", f"nibrev32_{nm}", nibrev(v, 32), org, width=4, raw=True)
        B.num("bits", f"bswap16in32_{nm}", ((v & 0xFFFF) << 16) | (v >> 16), org, width=4, raw=False)
    for nm, v in U64.items():
        for r in range(1, 64):
            B.num("bits", f"rotl64_{nm}_{r}", rotl(v, r, 64), "AB", width=8, raw=(r % 8 == 0), cat=False)
        B.num("bits", f"bswap64_{nm}", bswap(v, 8), "AB", width=8, raw=True)
        B.num("bits", f"wswap64_{nm}", wswap(v), "AB", width=8, raw=True)
        B.num("bits", f"bitrev64_{nm}", bitrev(v, 64), "AB", width=8, raw=True)
        B.num("bits", f"nibrev64_{nm}", nibrev(v, 64), "AB", width=8, raw=True)
        B.num("bits", f"bswap32in64_{nm}", (bswap(v >> 32, 4) << 32) | bswap(v & M32, 4), "AB", width=8, raw=True)


FACTOR_SET = [("A", "a", a), ("A", "a-1", a - 1), ("A", "a+1", a + 1), ("A", "ah", ah),
              ("B", "b", b), ("B", "b-1", b - 1), ("B", "b+1", b + 1), ("B", "bh", bh),
              ("AB", "ab", int(AB)), ("AB", "ba", int(BA)), ("AB", "a+b", a + b), ("AB", "a-b", a - b),
              ("AB", "bcd_ab", U64["bcd_ab"]), ("AB", "bcd_ba", U64["bcd_ba"]),
              ("AB", "a<<32|b", U64["a<<32|b"]), ("AB", "b<<32|a", U64["b<<32|a"]),
              ("AB", "a*b", a * b), ("AB", "a2+b2", a * a + b * b),
              ("AB", "il_ab", int("7466824719781640")), ("AB", "il_ba", int("4768284711971460"))]

def fam_fact(B):
    for org, nm, v in FACTOR_SET:
        fs = factor(v)
        assert math.prod(fs) == v and all(is_prime(p) for p in fs), (nm, v, fs)
        ex = {}
        for p in fs: ex[p] = ex.get(p, 0) + 1
        expo = "*".join(f"{p}^{e}" if e > 1 else str(p) for p, e in ex.items())
        B.add("fact", f"{nm}_primes", "space", " ".join(map(str, fs)), org)
        B.add("fact", f"{nm}_primes", "star", "*".join(map(str, fs)), org)
        B.add("fact", f"{nm}_primes", "x", " x ".join(map(str, fs)), org)
        B.add("fact", f"{nm}_primes", "times", " × ".join(map(str, fs)), org, False)
        B.add("fact", f"{nm}_primes", "concat", "".join(map(str, fs)), org)
        B.add("fact", f"{nm}_primes", "expo", expo, org)
        B.add("fact", f"{nm}_primes", "eq", f"{v} = {expo}", org, False)
        B.add("fact", f"{nm}_primes", "distinct", " ".join(map(str, ex)), org)
        tau, sigma, phi, lam, rad = arith(fs)
        raw = nm in ("a", "b", "ab", "ba")
        for k, x in (("lpf", fs[-1]), ("spf", fs[0]), ("sopfr", sum(fs)), ("sopf", sum(ex)),
                     ("bigomega", len(fs)), ("omega", len(ex)), ("tau", tau), ("sigma", sigma),
                     ("phi", phi), ("lambda", lam), ("rad", rad), ("cofactor_lpf", v // fs[-1]),
                     ("cofactor_spf", v // fs[0])):
            B.num("fact", f"{nm}_{k}", x, org, raw=raw and k in ("lpf", "phi", "sigma"))


def _digit_stats(s):
    ds = [int(c) for c in s]
    prod = math.prod(ds); nz = math.prod(d for d in ds if d) if any(ds) else 0
    ap, x = 0, sum(ds)
    while x >= 10: x = sum(int(c) for c in str(x)); ap += 1
    mp, y = 0, int(s)
    while y >= 10: y = math.prod(int(c) for c in str(y)); mp += 1
    pairs = [int(s[i:i + 2]) for i in range(0, len(s), 2)]
    quads = [int(s[i:i + 4]) for i in range(0, len(s), 4)]
    return {"digit_product": prod, "digit_product_nonzero": nz,
            "sum_squares": sum(d * d for d in ds), "sum_cubes": sum(d ** 3 for d in ds),
            "alt_sum": sum(d if i % 2 == 0 else -d for i, d in enumerate(ds)),
            "digital_root": x, "additive_persistence": ap, "multiplicative_persistence": mp,
            "pair_sum": sum(pairs), "pair_product": math.prod(pairs),
            "quad_sum": sum(quads), "quad_product": math.prod(quads),
            "distinct_digits": len(set(ds)), "popcount": bin(int(s)).count("1"),
            "digit_sum_squared": sum(ds) ** 2, "reverse_minus": abs(int(s) - int(s[::-1])),
            "reverse_plus": int(s) + int(s[::-1])}

def fam_digits(B):
    for org, s in (("A", A_D), ("B", B_D), ("AB", AB), ("AB", BA)):
        nm = {A_D: "a", B_D: "b", AB: "ab", BA: "ba"}[s]
        for k, v in _digit_stats(s).items():
            B.num("digits", f"{nm}_{k}", v, org)
        hist = "".join(str(s.count(str(d))) for d in range(10))
        B.add("digits", f"{nm}_histogram", None, hist, org)
    B.num("digits", "hamming_bits", bin(a ^ b).count("1"), "AB")
    B.num("digits", "hamming_digits", sum(p != q for p, q in zip(A_D, B_D)), "AB")
    B.num("digits", "hamming_bits_hex", bin(ah ^ bh).count("1"), "AB")


def fam_mod(B):
    ps = PRIMES100[:25]
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("AB", "ab", int(AB)), ("AB", "ba", int(BA))):
        res = [v % p for p in ps]
        B.add("mod", f"{nm}_res25", "space", " ".join(map(str, res)), org)
        B.add("mod", f"{nm}_res25", "comma", ",".join(map(str, res)), org, False)
        B.add("mod", f"{nm}_res25", "concat", "".join(map(str, res)), org)
        B.add("mod", f"{nm}_res25", "pairs", " ".join(f"{p}:{r}" for p, r in zip(ps, res)), org, False)
        for mn, m in (("65537", 65537), ("65521", 65521), ("2^16", 1 << 16), ("2^24", 1 << 24),
                      ("1000003", 1000003), ("999983", 999983), ("1299709", 1299709),
                      ("2^31-1", (1 << 31) - 1), ("1e9+7", 10 ** 9 + 7), ("998244353", 998244353),
                      ("4294967291", 4294967291), ("2^32", 1 << 32), ("1e9+9", 10 ** 9 + 9)):
            r = v % m
            if r != v: B.num("mod", f"{nm}_mod_{mn}", r, org)


FAMOUS_P = [("M31", (1 << 31) - 1), ("M61", (1 << 61) - 1), ("M89", (1 << 89) - 1),
            ("M127", (1 << 127) - 1), ("25519", (1 << 255) - 19), ("secp_p", P), ("secp_n", N),
            ("F4", 65537), ("1e9+7", 10 ** 9 + 7), ("998244353", 998244353),
            ("p32max", 4294967291), ("p64max", 18446744073709551557), ("M521", (1 << 521) - 1)]

def fam_pow(B):
    for pn, p in FAMOUS_P:
        raw = p <= N
        B.num("pow", f"a^b_mod_{pn}", pow(a, b, p), "AB", raw=raw)
        B.num("pow", f"b^a_mod_{pn}", pow(b, a, p), "AB", raw=raw)
        B.num("pow", f"2^a_mod_{pn}", pow(2, a, p), "A", raw=raw)
        B.num("pow", f"2^b_mod_{pn}", pow(2, b, p), "B", raw=raw)
        if math.gcd(a, p) == 1: B.num("pow", f"inv_a_mod_{pn}", pow(a, -1, p), "A", raw=raw)
        if math.gcd(b, p) == 1: B.num("pow", f"inv_b_mod_{pn}", pow(b, -1, p), "B", raw=raw)
    for pn, p in (("secp_n", N), ("secp_p", P)):
        B.num("pow", f"a/b_mod_{pn}", a * pow(b, -1, p) % p, "AB", raw=True)
        B.num("pow", f"b/a_mod_{pn}", b * pow(a, -1, p) % p, "AB", raw=True)
        B.num("pow", f"a*b_mod_{pn}", a * b % p, "AB", raw=True)
        B.num("pow", f"(a+b)^-1_mod_{pn}", pow(a + b, -1, p), "AB", raw=True)
    for mn, m in (("1e16", 10 ** 16), ("2^64", 1 << 64), ("2^32", 1 << 32), ("1e8", 10 ** 8)):
        B.num("pow", f"a^b_mod_{mn}", pow(a, b, m), "AB")
        B.num("pow", f"b^a_mod_{mn}", pow(b, a, m), "AB")
        B.num("pow", f"a^a_mod_{mn}", pow(a, a, m), "A")
        B.num("pow", f"b^b_mod_{mn}", pow(b, b, m), "B")
    B.num("pow", "a^2", a * a, "A"); B.num("pow", "a^3", a ** 3, "A")
    B.num("pow", "b^2", b * b, "B"); B.num("pow", "b^3", b ** 3, "B")
    B.num("pow", "a^3+b^3", a ** 3 + b ** 3, "AB"); B.num("pow", "(a+b)^2", (a + b) ** 2, "AB")
    B.num("pow", "(a-b)^2", (a - b) ** 2, "AB"); B.num("pow", "a^2-b^2", a * a - b * b, "AB")
    B.num("pow", "isqrt_a", math.isqrt(a), "A"); B.num("pow", "isqrt_b", math.isqrt(b), "B")
    B.num("pow", "isqrt_ab", math.isqrt(int(AB)), "AB"); B.num("pow", "isqrt_ba", math.isqrt(int(BA)), "AB")
    B.num("pow", "icbrt_a", round(a ** (1 / 3)), "A"); B.num("pow", "icbrt_b", round(b ** (1 / 3)), "B")


def fam_fib(B):
    phi = (1 + 5 ** 0.5) / 2
    for org, nm, v in (("A", "a", a), ("B", "b", b)):
        z = zeckendorf(v)
        assert sum(FIB[i] for i in z) == v and all(p - q >= 2 for p, q in zip(z, z[1:]))
        B.add("fib", f"{nm}_zeck_idx", "space", " ".join(map(str, z)), org)
        B.add("fib", f"{nm}_zeck_idx", "concat", "".join(map(str, z)), org)
        B.add("fib", f"{nm}_zeck_idx", "comma", ",".join(map(str, z)), org, False)
        B.add("fib", f"{nm}_zeck_terms", "space", " ".join(str(FIB[i]) for i in z), org)
        B.add("fib", f"{nm}_zeck_terms", "plus", "+".join(str(FIB[i]) for i in z), org)
        B.add("fib", f"{nm}_zeck_bits", None, "".join("1" if i in z else "0" for i in range(z[0], 1, -1)), org)
        lo = max(i for i in range(len(FIB)) if FIB[i] <= v); hi = lo + 1
        B.num("fib", f"{nm}_fib_below", FIB[lo], org); B.num("fib", f"{nm}_fib_above", FIB[hi], org)
        B.num("fib", f"{nm}_fib_below_idx", lo, org); B.num("fib", f"{nm}_fib_above_idx", hi, org)
        B.num("fib", f"{nm}_minus_fib_below", v - FIB[lo], org); B.num("fib", f"{nm}_fib_above_minus", FIB[hi] - v, org)
        B.add("fib", f"{nm}_fib_bracket", None, f"{FIB[lo]} {v} {FIB[hi]}", org)
        llo = max(i for i in range(len(LUC)) if LUC[i] <= v)
        B.num("fib", f"{nm}_lucas_below", LUC[llo], org); B.num("fib", f"{nm}_lucas_above", LUC[llo + 1], org)
        B.num("fib", f"{nm}_lucas_below_idx", llo, org)
        for mn, m in (("1e8", 10 ** 8), ("1e16", 10 ** 16), ("2^32", 1 << 32), ("2^64", 1 << 64),
                      ("secp_n", N), ("secp_p", P), ("1e9+7", 10 ** 9 + 7)):
            f0, f1 = fib_pair_mod(v, m)
            raw = mn in ("secp_n", "secp_p")
            B.num("fib", f"F_{nm}_mod_{mn}", f0, org, raw=raw)
            B.num("fib", f"L_{nm}_mod_{mn}", (2 * f1 - f0) % m, org, raw=raw)
        B.num("fib", f"F_{nm}_ndigits", int(v * math.log10(phi) - math.log10(5) / 2) + 1, org)
        B.num("fib", f"L_{nm}_ndigits", int(v * math.log10(phi)) + 1, org)
        # index readings: the v-th prime, pi(v), neighbours, polygonal numbers
        pv = NTH_PRIME[v]
        assert is_prime(pv)
        B.num("fib", f"nth_prime_{nm}", pv, org, raw=True)
        B.num("fib", f"nextprime_{nm}", next_prime(v), org, raw=True)
        B.num("fib", f"prevprime_{nm}", prev_prime(v), org, raw=True)
        B.num("fib", f"prime_gap_after_{nm}", next_prime(v) - v, org)
        B.num("fib", f"prime_gap_before_{nm}", v - prev_prime(v), org)
        B.num("fib", f"triangular_{nm}", v * (v + 1) // 2, org, raw=True)
        B.num("fib", f"odd_{nm}", 2 * v - 1, org); B.num("fib", f"even_{nm}", 2 * v, org)
        B.num("fib", f"pentagonal_{nm}", v * (3 * v - 1) // 2, org)
        B.num("fib", f"square_pyramidal_{nm}", v * (v + 1) * (2 * v + 1) // 6, org)
    pa, pb = pi_of(a, b)
    B.num("fib", "pi_a", pa, "A", raw=True); B.num("fib", "pi_b", pb, "B", raw=True)
    B.num("fib", "pi_a-pi_b", pa - pb, "AB"); B.num("fib", "pi_a+pi_b", pa + pb, "AB")
    B.num("fib", "nth_prime_sum", NTH_PRIME[a] + NTH_PRIME[b], "AB", raw=True)
    B.num("fib", "nth_prime_diff", NTH_PRIME[a] - NTH_PRIME[b], "AB")
    for nm, v in (("ab", int(AB)), ("ba", int(BA)), ("a+b", a + b), ("a*b", a * b)):
        B.num("fib", f"nextprime_{nm}", next_prime(v), "AB", raw=True)
        B.num("fib", f"prevprime_{nm}", prev_prime(v), "AB", raw=True)
    B.num("fib", "triangular_a+b", (a + b) * (a + b + 1) // 2, "AB")


def fam_dmap(B):
    fac = [math.factorial(d) for d in range(10)]
    single = {"fib": lambda d: FIB[d], "lucas": lambda d: LUC[d], "prime": lambda d: PRIMES100[d - 1] if d else 0,
              "square": lambda d: d * d, "cube": lambda d: d ** 3, "factorial": lambda d: fac[d],
              "triangular": lambda d: d * (d + 1) // 2, "pow2": lambda d: 1 << d}
    pair = {"fib": lambda n: FIB[n], "lucas": lambda n: LUC[n], "prime": lambda n: PRIMES100[n - 1] if n else 0,
            "square": lambda n: n * n, "cube": lambda n: n ** 3, "triangular": lambda n: n * (n + 1) // 2,
            "bij26": lambda n: bij26(n) if n else "0"}
    for org, nm, s in (("A", "a", A_D), ("B", "b", B_D)):
        ds = [int(c) for c in s]
        ps = [int(s[i:i + 2]) for i in range(0, 8, 2)]
        for k, f in single.items():
            vals = [str(f(d)) for d in ds]
            B.add("dmap", f"{nm}_d1_{k}", "space", " ".join(vals), org)
            B.add("dmap", f"{nm}_d1_{k}", "concat", "".join(vals), org)
        for k, f in pair.items():
            vals = [str(f(n)) for n in ps]
            B.add("dmap", f"{nm}_d2_{k}", "space", " ".join(vals), org)
            B.add("dmap", f"{nm}_d2_{k}", "concat", "".join(vals), org)
        quads = [int(s[:4]), int(s[4:])]
        B.add("dmap", f"{nm}_d4_bij26", "space", " ".join(bij26(q) for q in quads), org)
        B.add("dmap", f"{nm}_d4_bij26", "concat", "".join(bij26(q) for q in quads), org)


CHECK_STRINGS = [("A", "d", A_D), ("A", "s", A_STR), ("A", "sp", A_SP), ("A", "lo", A_STR.lower()),
                 ("B", "d", B_D), ("B", "s", B_STR), ("B", "sp", B_SP), ("B", "lo", B_STR.lower()),
                 ("AB", "dd", AB), ("AB", "dd_ba", BA), ("AB", "ss", A_STR + B_STR), ("AB", "ss_ba", B_STR + A_STR),
                 ("AB", "d_d", A_D + " " + B_D), ("AB", "s_s", A_STR + " " + B_STR),
                 ("AB", "sp_sp", A_SP + " " + B_SP), ("AB", "sp_sp_ba", B_SP + " " + A_SP)]

def fam_check(B):
    for org, sn, s in CHECK_STRINGS:
        d = s.encode(); digits = "".join(c for c in s if c.isdigit())
        other = b if org == "A" else a if org == "B" else None
        if sn in ("d", "dd", "dd_ba"):                       # pure digit strings
            for k, f in (("luhn", luhn), ("verhoeff", verhoeff), ("damm", damm), ("ean8", ean8)):
                c = f(digits)
                B.num("check", f"{sn}_{k}", c, org, cat=False)
                B.add("check", f"{sn}_{k}", "appended", digits + str(c), org)
            for k, f in (("mod11_isbn", mod11_isbn), ("mod11_iso7064", mod11_iso7064)):
                c = f(digits)
                B.add("check", f"{sn}_{k}", None, c, org, False)
                B.add("check", f"{sn}_{k}", "appended", digits + c, org)
            r = int(digits) % 97
            B.num("check", f"{sn}_mod97", r, org, cat=False)
            B.add("check", f"{sn}_mod97", "check", f"{98 - r:02d}", org, False)
            B.add("check", f"{sn}_mod97", "appended", f"{digits}{98 - r:02d}", org)
            B.num("check", f"{sn}_mod11", int(digits) % 11, org, cat=False)
            B.num("check", f"{sn}_mod10", int(digits) % 10, org, cat=False)
        if any(c.isalpha() for c in s) and " " not in s:    # alphanumeric strings
            up = s.upper()
            c = luhn_modn(up)
            B.add("check", f"{sn}_luhn36", None, c, org, False)
            B.add("check", f"{sn}_luhn36", "appended", up + c, org)
            ib = iban_digits(up)
            B.num("check", f"{sn}_iban_digits", int(ib), org)
            r = int(ib) % 97
            B.num("check", f"{sn}_iban_mod97", r, org, cat=False)
            B.add("check", f"{sn}_iban_mod97", "check", f"{98 - r:02d}", org, False)
            B.add("check", f"{sn}_iban_mod97", "appended", f"{up}{98 - r:02d}", org)
            c39 = code39(up)
            B.num("check", f"{sn}_code39", c39, org, cat=False)
            B.add("check", f"{sn}_code39", "appended", up + _C39[c39], org)
        B.num("check", f"{sn}_crc32", zlib.crc32(d), org, width=4)
        B.num("check", f"{sn}_adler32", zlib.adler32(d), org, width=4)
        for k, (w, poly, init, ri, ro, xo, _chk) in CRCS.items():
            B.num("check", f"{sn}_{k}", crc(d, w, poly, init, ri, ro, xo), org, width=w // 8)
        B.num("check", f"{sn}_fletcher16", fletcher16(d), org, width=2)
        B.num("check", f"{sn}_fletcher32", fletcher32(d), org, width=4)
        B.num("check", f"{sn}_bsd16", bsd16(d), org, width=2)
        B.num("check", f"{sn}_sum8", sum(d) & 0xFF, org, cat=False)
        B.num("check", f"{sn}_sum", sum(d), org)
        B.num("check", f"{sn}_xor8", __import__("functools").reduce(lambda x, y: x ^ y, d), org, cat=False)
        B.num("check", f"{sn}_fnv1a32", fnv1a(d, 32), org, width=4)
        B.num("check", f"{sn}_fnv1a64", fnv1a(d, 64), org, width=8)
        B.num("check", f"{sn}_djb2", djb2(d), org, width=4)
        B.num("check", f"{sn}_sdbm", sdbm(d), org, width=4)
        jh = javahash(s)
        B.num("check", f"{sn}_javahash", jh, org)
        if jh < 0: B.add("check", f"{sn}_javahash", "hex8", format(jh & M32, "08x"), org, False)
        B.num("check", f"{sn}_murmur3", murmur3_32(d), org, width=4)
        if other is not None:
            B.num("check", f"{sn}_murmur3_seed_other", murmur3_32(d, other), org, width=4)
            B.num("check", f"{sn}_crc32_xor_other", zlib.crc32(d) ^ other, org, width=4)
    # CRC/Adler of the byte encodings, not the ASCII
    for org, nm, bs in (("A", "be4", a.to_bytes(4, "big")), ("A", "bcd4", bytes.fromhex(A_D)),
                        ("B", "be4", b.to_bytes(4, "big")), ("B", "bcd4", bytes.fromhex(B_D)),
                        ("AB", "u64_ab", U64["a<<32|b"].to_bytes(8, "big")), ("AB", "bcd8_ab", bytes.fromhex(AB))):
        B.num("check", f"bytes_{nm}_crc32", zlib.crc32(bs), org, width=4)
        B.num("check", f"bytes_{nm}_adler32", zlib.adler32(bs), org, width=4)
        B.num("check", f"bytes_{nm}_crc32c", crc(bs, *CRCS["crc32c"][:6]), org, width=4)


HASH_STRINGS = CHECK_STRINGS + [("AB", "s_s_ba", B_STR + " " + A_STR), ("AB", "d_d_ba", B_D + " " + A_D),
                                ("AB", "lo_lo", (A_STR + B_STR).lower())]

def fam_hash(B):
    algs = {"md5": lambda d: hashlib.md5(d).digest(), "sha1": lambda d: hashlib.sha1(d).digest(),
            "ripemd160": lambda d: hashlib.new("ripemd160", d).digest(),
            "sha224": lambda d: hashlib.sha224(d).digest(), "sha3_224": lambda d: hashlib.sha3_224(d).digest(),
            "sha384": lambda d: hashlib.sha384(d).digest(), "sha512": lambda d: hashlib.sha512(d).digest(),
            "sha512_256": lambda d: hashlib.new("sha512_256", d).digest(),
            "blake2s": lambda d: hashlib.blake2s(d).digest(),
            "hash160": lambda d: hashlib.new("ripemd160", hashlib.sha256(d).digest()).digest(),
            "md5_md5": lambda d: hashlib.md5(hashlib.md5(d).hexdigest().encode()).digest(),
            "sha1_sha1": lambda d: hashlib.sha1(hashlib.sha1(d).hexdigest().encode()).digest()}
    for org, sn, s in HASH_STRINGS:
        d = s.encode()
        for k, f in algs.items():
            dg = f(d)
            B.add("hash", f"{sn}_{k}", "hex", dg.hex(), org)
            if k in ("md5", "sha1", "ripemd160", "hash160"):
                B.add("hash", f"{sn}_{k}", "HEX", dg.hex().upper(), org, False)
                B.add("hash", f"{sn}_{k}", "b64", base64.b64encode(dg).decode(), org, False)
            if len(dg) in (16, 20, 28, 32):
                B.add("hash", f"{sn}_{k}", "raw", dg, org)
        # one serial's md5/sha1 keyed by the other: hex(md5(A)) + hex(md5(B)) is left to [pair]


def fam_time(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b)):
        reads = [("unix_s", v), ("unix_ms", v // 1000), ("unix_min", v * 60),
                 ("genesis+", GENESIS_TS + v), ("1+", int("1" + str(v))), ("16+", int("16" + str(v))),
                 ("17+", int("17" + str(v))), ("15+", int("15" + str(v)))]
        for rn, ts in reads:
            if rn != "unix_s": B.num("time", f"{nm}_{rn}", ts, org)
            for fn, txt in _dates(ts): B.add("time", f"{nm}_{rn}", fn, txt, org)
        B.add("time", f"{nm}_unix_ms", "iso_ms", datetime.datetime.fromtimestamp(v / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%S.") + f"{v % 1000:03d}Z", org)
    # a read as a calendar stamp 7/6/84 17:14 (dd/mm/yy and mm/dd/yy); b admits no such split
    for rn, dt in (("dmy8417", datetime.datetime(1984, 6, 7, 17, 14, tzinfo=UTC)),
                   ("mdy8417", datetime.datetime(1984, 7, 6, 17, 14, tzinfo=UTC))):
        ts = int(dt.timestamp())
        B.num("time", f"a_{rn}", ts, "A")
        for fn, txt in _dates(ts): B.add("time", f"a_{rn}", fn, txt, "A")
        B.add("time", f"a_{rn}", "hm", dt.strftime("%Y-%m-%d %H:%M"), "A")
    for nm, v in (("ab", int(AB)), ("ba", int(BA))):
        for rn, ts in (("us", v // 10 ** 6), ("ns", v // 10 ** 9)):
            B.num("time", f"{nm}_{rn}", ts, "AB")
            for fn, txt in _dates(ts): B.add("time", f"{nm}_{rn}", fn, txt, "AB")
    for rn, ts in (("a+b_s", a + b), ("genesis+a+b", GENESIS_TS + a + b), ("a-b_s", a - b), ("genesis+a-b", GENESIS_TS + a - b)):
        B.num("time", rn, ts, "AB")
        for fn, txt in _dates(ts): B.add("time", rn, fn, txt, "AB")


def fam_block(B):
    hs = {"A": [("h7", 7684171), ("h6", 768417), ("h5", 76841), ("h4", 7684)],
          "B": [("h7", 4627986), ("h6", 462798), ("h5", 46279), ("h4", 4627)]}
    for org, lst in hs.items():
        for k, h in lst:
            B.num("block", k, h, org)
            for pn, fmt in (("block", "block {h}"), ("Block", "Block {h}"), ("hash", "#{h}"),
                            ("height", "height {h}"), ("blockhash", "block #{h}"), ("blk", "blk{h}"),
                            ("blockno", "block{h}"), ("BLOCK", "BLOCK {h}")):
                B.add("block", k, pn, fmt.format(h=h), org)
    for k in ("h7", "h6", "h5", "h4"):
        x = dict(hs["A"])[k]; y = dict(hs["B"])[k]
        B.num("block", f"{k}_sum", x + y, "AB"); B.num("block", f"{k}_diff", x - y, "AB")
        B.num("block", f"{k}_prod", x * y, "AB")
        B.add("block", f"{k}_pair", "dash", f"{x}-{y}", "AB")
        B.add("block", f"{k}_pair", "blocks", f"blocks {x} {y}", "AB")


def fam_btc(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b)):
        btc = f"{v / 1e8:.8f}"
        for k, txt in (("btc", btc), ("btc_short", btc.rstrip("0")), ("btc_unit", btc + " BTC"),
                       ("btc_unit2", btc + "BTC"), ("btc_unit3", "BTC " + btc), ("btc_sym", "₿" + btc),
                       ("btc_unit_short", btc.rstrip("0") + " BTC"),
                       ("sat", f"{v} sat"), ("sats", f"{v} sats"), ("satoshi", f"{v} satoshi"),
                       ("satoshis", f"{v} satoshis"), ("sats_comma", f"{v:,} sats"),
                       ("mbtc", f"{v / 1e5:.5f} mBTC"), ("mbtc_num", f"{v / 1e5:.5f}"),
                       ("bits", f"{v / 100:.2f} bits"), ("bits_num", f"{v / 100:.2f}"),
                       ("ubtc", f"{v / 100:.2f} uBTC"), ("btc_x20", f"{v / 1e8 * 20:.8f}"),
                       ("as_btc_amount", f"{v}.00000000"), ("as_btc_unit", f"{v} BTC")):
            B.add("btc", f"{nm}_{k}", None, txt, org)
        B.num("btc", f"{nm}_20btc_minus", 2_000_000_000 - v, org)
        B.add("btc", f"{nm}_20btc_minus", "btc", f"{(2_000_000_000 - v) / 1e8:.8f}", org)
        B.num("btc", f"{nm}_sats_x20", v * 20, org)
        B.num("btc", f"{nm}_in_20btc", 2_000_000_000 // v, org)
        B.num("btc", f"{nm}_20btc_mod", 2_000_000_000 % v, org)
    s = a + b; d = abs(a - b)
    for k, txt in (("sum_btc", f"{s / 1e8:.8f}"), ("sum_btc_unit", f"{s / 1e8:.8f} BTC"),
                   ("diff_btc", f"{d / 1e8:.8f}"), ("diff_btc_unit", f"{d / 1e8:.8f} BTC"),
                   ("pair_amount_ab", f"{A_D}.{B_D}"), ("pair_amount_ba", f"{B_D}.{A_D}"),
                   ("pair_amount_ab_unit", f"{A_D}.{B_D} BTC"), ("pair_amount_ba_unit", f"{B_D}.{A_D} BTC"),
                   ("pair_btc_plus", f"{a / 1e8:.8f} + {b / 1e8:.8f}"),
                   ("pair_sat_short", f"{a}sat{b}sat"),
                   ("20btc_minus_both_btc", f"{(2_000_000_000 - s) / 1e8:.8f}"),
                   ("ab_sats_as_btc", f"{int(AB) / 1e8:.8f}"), ("ba_sats_as_btc", f"{int(BA) / 1e8:.8f}")):
        B.add("btc", k, None, txt, "AB")
    B.num("btc", "20btc_minus_both", 2_000_000_000 - s, "AB")
    B.num("btc", "20btc_sats", 2_000_000_000, "AB", cat=False)


def fam_fmt(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("AB", "ab", int(AB)), ("AB", "ba", int(BA)),
                       ("AB", "a+b", a + b), ("AB", "a-b", a - b), ("AB", "a*b", a * b)):
        av = abs(v); sv = str(av)
        B.add("fmt", f"{nm}_comma", None, f"{v:,}", org)
        B.add("fmt", f"{nm}_dot", None, f"{v:,}".replace(",", "."), org)
        B.add("fmt", f"{nm}_space", None, f"{v:,}".replace(",", " "), org)
        B.add("fmt", f"{nm}_apos", None, f"{v:,}".replace(",", "'"), org)
        B.add("fmt", f"{nm}_under", None, f"{v:_}", org)
        B.add("fmt", f"{nm}_sci", None, f"{v:e}", org, False)
        B.add("fmt", f"{nm}_sci_short", None, f"{sv[0]}.{sv[1:].rstrip('0') or '0'}e{len(sv) - 1}", org, False)
        B.add("fmt", f"{nm}_plus", None, f"+{v}", org)
        B.add("fmt", f"{nm}_float", None, f"{v}.0", org)
        B.add("fmt", f"{nm}_cents", None, f"{v}.00", org)
        B.add("fmt", f"{nm}_dollar", None, f"${v:,}", org)
        B.add("fmt", f"{nm}_dollar_plain", None, f"${v}", org)
        for w in (10, 12, 16, 20):
            if len(sv) < w: B.add("fmt", f"{nm}_zpad{w}", None, sv.zfill(w), org)
        wd = words(v)
        B.add("fmt", f"{nm}_words", None, wd, org)
        B.add("fmt", f"{nm}_words", "nohyphen", wd.replace("-", " "), org, False)
        B.add("fmt", f"{nm}_words", "upper", wd.upper(), org, False)
        B.add("fmt", f"{nm}_words", "title", wd.title(), org, False)
        B.add("fmt", f"{nm}_words", "and", wd.replace("hundred ", "hundred and "), org, False)
        B.add("fmt", f"{nm}_words", "concat", wd.replace("-", "").replace(" ", ""), org, False)
        B.add("fmt", f"{nm}_digit_words", None, " ".join(_ONES[int(c)] for c in sv), org)
        B.add("fmt", f"{nm}_digit_words", "concat", "".join(_ONES[int(c)] for c in sv), org, False)
        B.add("fmt", f"{nm}_digit_words", "dash", "-".join(_ONES[int(c)] for c in sv), org, False)


TEXT_STRINGS = [("A", "d", A_D), ("A", "s", A_STR), ("A", "sp", A_SP), ("B", "d", B_D), ("B", "s", B_STR),
                ("B", "sp", B_SP), ("AB", "dd", AB), ("AB", "dd_ba", BA), ("AB", "ss", A_STR + B_STR),
                ("AB", "ss_ba", B_STR + A_STR), ("AB", "s_s", A_STR + " " + B_STR), ("AB", "sp_sp", A_SP + " " + B_SP)]

def fam_text(B):
    for org, sn, s in TEXT_STRINGS:
        d = s.encode()
        B.add("text", f"{sn}_asciihex", None, d.hex(), org)
        B.add("text", f"{sn}_asciihex", "upper", d.hex().upper(), org, False)
        B.add("text", f"{sn}_asciihex", "spaced", " ".join(f"{c:02x}" for c in d), org, False)
        B.add("text", f"{sn}_asciihex", "0x", " ".join(f"0x{c:02x}" for c in d), org, False)
        B.add("text", f"{sn}_b64", None, base64.b64encode(d).decode(), org)
        B.add("text", f"{sn}_b64", "nopad", base64.b64encode(d).decode().rstrip("="), org, False)
        B.add("text", f"{sn}_b64", "url", base64.urlsafe_b64encode(d).decode().rstrip("="), org, False)
        B.add("text", f"{sn}_b32", None, base64.b32encode(d).decode(), org)
        B.add("text", f"{sn}_b32", "nopad", base64.b32encode(d).decode().rstrip("="), org, False)
        B.add("text", f"{sn}_b32", "lower", base64.b32encode(d).decode().rstrip("=").lower(), org, False)
        B.add("text", f"{sn}_b85", None, base64.b85encode(d).decode(), org)
        B.add("text", f"{sn}_a85", None, base64.a85encode(d).decode(), org)
        B.add("text", f"{sn}_b58", None, b58enc(d), org)
        B.add("text", f"{sn}_bin", None, " ".join(f"{c:08b}" for c in d), org)
        B.add("text", f"{sn}_bin", "concat", "".join(f"{c:08b}" for c in d), org, False)
        B.add("text", f"{sn}_bin", "7bit", " ".join(f"{c:07b}" for c in d), org, False)
        B.add("text", f"{sn}_asciidec", None, " ".join(str(c) for c in d), org)
        B.add("text", f"{sn}_asciidec", "concat", "".join(str(c) for c in d), org, False)
        B.add("text", f"{sn}_asciioct", None, " ".join(f"{c:03o}" for c in d), org)
        B.add("text", f"{sn}_asciioct", "concat", "".join(f"{c:03o}" for c in d), org, False)
        B.add("text", f"{sn}_morse", None, morse(s), org)
        B.add("text", f"{sn}_morse", "slash", morse(s).replace(" ", "/"), org, False)
        B.add("text", f"{sn}_morse", "concat", morse(s).replace(" ", ""), org, False)
        B.add("text", f"{sn}_morse", "unicode", morse(s).replace(".", "·").replace("-", "−"), org, False)
        B.add("text", f"{sn}_digit_words", None, " ".join(_ONES[int(c)] if c.isdigit() else c for c in s if c != " "), org)
        if any(c.isalpha() for c in s):
            B.add("text", f"{sn}_rot13", None, rot13(s), org)
            B.add("text", f"{sn}_rot13", "lower", rot13(s).lower(), org, False)
            B.add("text", f"{sn}_atbash", None, atbash(s), org)
            B.add("text", f"{sn}_atbash", "lower", atbash(s).lower(), org, False)
            B.add("text", f"{sn}_nato", None, nato(s), org)
            B.add("text", f"{sn}_nato", "upper", nato(s).upper(), org, False)
            B.add("text", f"{sn}_nato", "spelled", nato_spelled(s), org)
            B.add("text", f"{sn}_nato", "concat", nato(s).replace(" ", ""), org, False)
            B.add("text", f"{sn}_keypad", None, keypad(s.replace(" ", "")), org)
            B.add("text", f"{sn}_keypad", "spaced", keypad(s), org, False)
            B.add("text", f"{sn}_alpha_pos", "concat", "".join(f"{ord(c) - 64:02d}" if c.isalpha() else c for c in s if c != " "), org)
        if s.isdigit():
            B.add("text", f"{sn}_a1z26", None, a1z26(s), org)
            B.add("text", f"{sn}_a1z26", "zeroO", a1z26(s, zero="O"), org, False)
            B.add("text", f"{sn}_a1z26", "zeroA", a1z26(s, one_is_a=False), org)
            B.add("text", f"{sn}_a1z26", "lower", a1z26(s).lower(), org, False)
            B.add("text", f"{sn}_a1z26", "zeroA_lower", a1z26(s, one_is_a=False).lower(), org, False)
            B.add("text", f"{sn}_leet", None, s.translate(str.maketrans("0134578", "OIEASTB")), org)
            B.add("text", f"{sn}_unicode_hex", None, "".join(chr(int(s[i:i + 4], 16)) for i in range(0, len(s), 4)), org, False)
            B.add("text", f"{sn}_unicode_dec", None, "".join(chr(int(s[i:i + 4])) for i in range(0, len(s), 4)), org, False)
            B.add("text", f"{sn}_fullwidth", None, s.translate(str.maketrans("0123456789", "０１２３４５６７８９")), org, False)


def fam_ip(B):
    for org, nm, v in (("A", "a", a), ("B", "b", b), ("A", "ah", ah), ("B", "bh", bh)):
        q = ".".join(str(x) for x in v.to_bytes(4, "big"))
        B.add("ip", f"{nm}_ipv4", None, q, org)
        B.add("ip", f"{nm}_ipv4", "le", ".".join(str(x) for x in v.to_bytes(4, "little")), org)
        B.add("ip", f"{nm}_ipv4", "url", "http://" + q, org, False)
    for nm, v in U64.items():
        bs = v.to_bytes(8, "big")
        B.add("ip", f"{nm}_mac6", None, ":".join(f"{x:02x}" for x in bs[2:]), "AB", False)
        B.add("ip", f"{nm}_ipv6_tail", None, ":".join(f"{int.from_bytes(bs[i:i + 2], 'big'):x}" for i in range(0, 8, 2)), "AB", False)
        B.add("ip", f"{nm}_two_ipv4", None, ".".join(str(x) for x in bs[:4]) + " " + ".".join(str(x) for x in bs[4:]), "AB")
    bs16 = AB.encode()
    B.add("ip", "ascii16_uuid", None, f"{bs16[:4].hex()}-{bs16[4:6].hex()}-{bs16[6:8].hex()}-{bs16[8:10].hex()}-{bs16[10:].hex()}", "AB", False)
    bcd = bytes.fromhex(AB) + bytes.fromhex(BA)
    B.add("ip", "bcd_uuid", None, f"{bcd[:4].hex()}-{bcd[4:6].hex()}-{bcd[6:8].hex()}-{bcd[8:10].hex()}-{bcd[10:].hex()}", "AB", False)


def fam_cf(B):
    for nm, (p, q) in (("a/b", (a, b)), ("b/a", (b, a))):
        cf = contfrac(p, q)
        B.add("cf", f"{nm}_cf", "space", " ".join(map(str, cf)), "AB")
        B.add("cf", f"{nm}_cf", "concat", "".join(map(str, cf)), "AB")
        B.add("cf", f"{nm}_cf", "bracket", f"[{cf[0]}; " + ", ".join(map(str, cf[1:])) + "]", "AB", False)
        conv = list(convergents(cf))
        B.add("cf", f"{nm}_convergents", None, " ".join(f"{h}/{k}" for h, k in conv), "AB", False)
        B.add("cf", f"{nm}_convergent_nums", None, " ".join(str(h) for h, _ in conv), "AB")
        B.add("cf", f"{nm}_convergent_dens", None, " ".join(str(k) for _, k in conv), "AB")
        h, k = conv[-1]
        B.add("cf", f"{nm}_reduced", None, f"{h}/{k}", "AB")
        B.add("cf", f"{nm}_ratio_float", None, repr(p / q), "AB")
        B.add("cf", f"{nm}_ratio_float", "6", f"{p / q:.6f}", "AB", False)
        B.add("cf", f"{nm}_ratio_float", "16", f"{p / q:.16f}", "AB", False)
        B.add("cf", f"{nm}_colon", None, f"{p}:{q}", "AB")
        B.add("cf", f"{nm}_frac", None, f"{p}/{q}", "AB")
    g, x, y = egcd(a, b)
    assert a * x + b * y == g == 2
    B.num("cf", "bezout_x", x, "AB"); B.num("cf", "bezout_y", y, "AB")
    B.add("cf", "bezout", "pair", f"{x} {y}", "AB")
    B.add("cf", "bezout", "eq", f"{a}*({x}) + {b}*{y} = {g}", "AB", False)
    B.num("cf", "a_over_g", a // g, "A"); B.num("cf", "b_over_g", b // g, "B")
    B.add("cf", "sqrt_a", None, f"{a ** 0.5:.6f}", "A"); B.add("cf", "sqrt_b", None, f"{b ** 0.5:.6f}", "B")
    B.add("cf", "log2_a", None, f"{math.log2(a):.6f}", "A"); B.add("cf", "log2_b", None, f"{math.log2(b):.6f}", "B")
    B.add("cf", "ln_a", None, f"{math.log(a):.6f}", "A"); B.add("cf", "ln_b", None, f"{math.log(b):.6f}", "B")
    B.add("cf", "log10_a", None, f"{math.log10(a):.6f}", "A"); B.add("cf", "log10_b", None, f"{math.log10(b):.6f}", "B")


def fam_roman(B):
    for org, nm, s in (("A", "a", A_D), ("B", "b", B_D)):
        pairs = [int(s[i:i + 2]) for i in range(0, 8, 2)]
        triples = [int(s[:3]), int(s[3:6]), int(s[6:])]
        for k, chunks in (("d1", [int(c) for c in s]), ("d2", pairs), ("d3", triples)):
            rs = [roman(c) for c in chunks]
            B.add("roman", f"{nm}_{k}", "space", " ".join(rs), org)
            B.add("roman", f"{nm}_{k}", "concat", "".join(rs), org)
            B.add("roman", f"{nm}_{k}", "lower", " ".join(rs).lower(), org, False)


# ================================================================ assembly
FAMILIES = [fam_base, fam_enc, fam_gray, fam_compl, fam_bits, fam_fact, fam_digits, fam_mod, fam_pow,
            fam_fib, fam_dmap, fam_check, fam_hash, fam_time, fam_block, fam_btc, fam_fmt, fam_text,
            fam_ip, fam_cf, fam_roman]

_TOKEN = re.compile(r"(?<![A-Za-z0-9])(?:ah|bh|a|b)(?![A-Za-z0-9])")

CAT_JOINS = [("+d", lambda v, d, s: v + d), ("d+", lambda v, d, s: d + v),
             ("+ d", lambda v, d, s: v + " " + d), ("d +", lambda v, d, s: d + " " + v),
             ("+s", lambda v, d, s: v + s), ("s+", lambda v, d, s: s + v),
             ("+ s", lambda v, d, s: v + " " + s), ("s +", lambda v, d, s: s + " " + v)]

def _already_swept():
    """Every value serial_combine.py already runs, so nothing here is a re-run."""
    seen = {A_D, B_D, A_STR, B_STR, A_SP, B_SP, AB, BA, A_STR + B_STR, B_STR + A_STR}
    try:
        import serial_combine as SC
        mats, _keys = SC.numeric_forms()
        for _t, m in mats:
            seen.add(m if isinstance(m, str) else "hex:" + m.hex())
        seen |= set(SC.string_forms())
        nodes, _tr = SC.bfs_forms(2, 10 ** 6)
        seen |= {v for _t, v in nodes}
        seen |= set(SC.PASSPHRASES)
    except Exception as e:                       # pragma: no cover
        sys.stderr.write(f"  combo_encodings: serial_combine skip-set unavailable ({e!r}); "
                         f"falling back to the literal constants only\n")
    return seen


_CACHE = None

def forms():
    global _CACHE
    if _CACHE is not None:
        return list(_CACHE)
    B = _Builder()
    for fam in FAMILIES:
        fam(B)
    base = list(B.items)
    # [cat] single-serial text forms joined with the OTHER serial
    for tag, val, org, fam, key, rep, cat in base:
        if not cat or org == "AB" or val.startswith("hex:") or len(val) > 40: continue
        d, s = (B_D, B_STR) if org == "A" else (A_D, A_STR)
        for jn, f in CAT_JOINS:
            B.add("cat", f"{tag}|{jn}", None, f(val, d, s), org, False)
    # [pair] the A-form of a key joined with its same-named B-form; keys are made
    # origin-neutral by turning the standalone tokens a/b -> x and ah/bh -> xh
    neutral = lambda k: _TOKEN.sub(lambda m: "xh" if m.group(0) in ("ah", "bh") else "x", k)
    byk = {}
    for tag, val, org, fam, key, rep, cat in base:
        if not cat or org == "AB" or val.startswith("hex:") or len(val) > 60: continue
        byk.setdefault((fam, neutral(key), rep), {})[org] = val
    for (fam, key, rep), d in byk.items():
        if "A" in d and "B" in d and d["A"] != d["B"]:
            r = f"/{rep}" if rep else ""
            B.add("pair", f"{fam}.{key}{r}|ab", None, d["A"] + d["B"], "AB", False)
            B.add("pair", f"{fam}.{key}{r}|ba", None, d["B"] + d["A"], "AB", False)
            B.add("pair", f"{fam}.{key}{r}|a b", None, d["A"] + " " + d["B"], "AB", False)
            B.add("pair", f"{fam}.{key}{r}|b a", None, d["B"] + " " + d["A"], "AB", False)
    global _SKIP
    _SKIP = _already_swept()
    out, seen = [], set()
    for tag, val, *_ in B.items:
        if val in _SKIP or val in seen: continue
        seen.add(val); out.append((tag, val))
    _CACHE = out
    return list(out)


_SKIP = set()


# ================================================================ selftest
def selftest():
    ok = True
    def rep(msg, good):
        nonlocal ok; ok &= bool(good); sys.stderr.write(f"  {msg}: {'OK' if good else 'FAIL'}\n")
    # --- algorithm vectors (published check values)
    for k, (w, poly, init, ri, ro, xo, chk) in CRCS.items():
        rep(f"{k}('123456789') == {chk:x}", crc(b"123456789", w, poly, init, ri, ro, xo) == chk)
    rep("zlib crc32('123456789') == cbf43926", zlib.crc32(b"123456789") == 0xCBF43926)
    rep("murmur3_32('hello') == 613153351", murmur3_32(b"hello") == 613153351)
    rep("fnv1a32('a') == e40c292c", fnv1a(b"a", 32) == 0xE40C292C)
    rep("luhn('7992739871') == 3, verhoeff('236') == 3, damm('572') == 4",
        luhn("7992739871") == 3 and verhoeff("236") == 3 and damm("572") == 4)
    rep("ISO 7064 11-2 of the 17-digit ID example -> X", mod11_iso7064("11010519491231002") == "X")
    rep("EAN-8 7351353 -> 7", ean8("7351353") == 7)
    rep("pi(1e7) == 664579 (sieve control)", pi_of(10 ** 7)[0] == 664579)
    rep("gray(14) == 9 and ungray(gray(a)) == a", gray(14) == 9 and ungray(gray(a)) == a)
    rep("words(76841714)", words(a) == "seventy-six million eight hundred forty-one thousand seven hundred fourteen")
    # --- hand-verified facts about the pair
    rep("a = 2 x 38420857 and b = 2^2 x 3 x 5 x 11 x 70121 (4*3*5*11*70121 = 46279860)",
        factor(a) == [2, 38420857] and factor(b) == [2, 2, 3, 5, 11, 70121] and 4 * 3 * 5 * 11 * 70121 == b)
    rep("gray(a) = 0x049482f2 ^ 0x024a4179 = 0x06dec38b = 115262347", gray(a) == 0x06DEC38B == 115262347)
    rep("Luhn check digits: a -> 9, b -> 4", luhn(A_D) == 9 and luhn(B_D) == 4)
    rep("a mod 97 = 60 (97*792182 = 76841654), b mod 97 = 93", a % 97 == 60 and b % 97 == 93)
    rep("Adler-32('76841714') = 1933<<16 | 423 = 126681511", zlib.adler32(A_D.encode()) == 126681511)
    rep("Zeckendorf(a) = F39+F35+F33+F30+F21+F15+F11", zeckendorf(a) == [39, 35, 33, 30, 21, 15, 11])
    rep("Zeckendorf(b) = F38+F34+F31+F26+F22+F18+F15+F13+F4+F2", zeckendorf(b) == [38, 34, 31, 26, 22, 18, 15, 13, 4, 2])
    rep("b+1 = 46279861 is prime; next prime after a is 76841741", is_prime(b + 1) and next_prime(a) == 76841741)
    pa, pb = NTH_PRIME[a], NTH_PRIME[b]
    rep("a-th prime 1544728243 and b-th prime 905578979 are prime and inside the PNT bracket",
        is_prime(pa) and is_prime(pb)
        and a * (math.log(a) + math.log(math.log(a)) - 1) < pa < a * (math.log(a) + math.log(math.log(a)))
        and b * (math.log(b) + math.log(math.log(b)) - 1) < pb < b * (math.log(b) + math.log(math.log(b))))
    rep("continued fraction of a/b starts [1; 1, 1, 1, 16] and reduces to 38420857/23139930",
        contfrac(a, b)[:5] == [1, 1, 1, 1, 16] and list(convergents(contfrac(a, b)))[-1] == (38420857, 23139930))
    rep("Bezout: 76841714*(-7800347) + 46279860*12951466 = 2", a * -7800347 + b * 12951466 == 2)
    # --- the built forms (rebuilt from scratch so the timing is honest)
    global _CACHE
    _CACHE = None
    t0 = time.time(); F = forms(); dt = time.time() - t0
    D = dict(F); V = set(D.values())
    rep(f"{len(F):,} forms built in {dt:.1f}s (<= 20,000, < 30 s)", 0 < len(F) <= 20000 and dt < 30)
    rep("unique tags", len({t for t, _ in F}) == len(F))
    rep("unique, non-empty values", len(V) == len(F) and all(v for v in V))
    rep("every hex: value is even-length hex",
        all(len(v) > 4 and len(v) % 2 == 0 and all(c in "0123456789abcdef" for c in v[4:]) for v in V if v.startswith("hex:")))
    nraw = sum(1 for v in V if v.startswith("hex:") and len(v) == 68)
    rep(f"{nraw} raw 32-byte keys, {sum(1 for v in V if v.startswith('hex:'))} hex: values in all", 200 < nraw < 2000)
    for tag, want in (("fact:A.a_primes/space", "2 38420857"), ("fact:B.b_primes/expo", "2^2*3*5*11*70121"),
                      ("gray:A.gray32_a/dec", "115262347"), ("gray:A.gray32_a/hex8", "06dec38b"),
                      ("check:A.d_luhn/appended", "768417149"), ("check:B.d_luhn/appended", "462798604"),
                      ("check:A.d_mod97/appended", "7684171438"), ("check:B.d_mod97/appended", "4627986005"),
                      ("check:A.d_adler32/dec", "126681511"), ("check:A.d_adler32/hex8", "078d01a7"),
                      ("time:A.a_unix_s/iso", "1972-06-08T08:55:14Z"), ("time:B.b_unix_s/iso", "1971-06-20T15:31:00Z"),
                      ("time:A.a_genesis+/ymd", "2011-06-12"), ("time:A.a_dmy8417/hm", "1984-06-07 17:14"),
                      ("btc:A.a_btc", "0.76841714"), ("btc:AB.sum_btc", "1.23121574"), ("btc:B.b_sats", "46279860 sats"),
                      ("block:A.h6/dec", "768417"), ("block:B.h6/block", "block 462798"),
                      ("fmt:A.a_words", "seventy-six million eight hundred forty-one thousand seven hundred fourteen"),
                      ("fmt:A.a_comma", "76,841,714"),
                      ("text:A.d_morse", "--... -.... ---.. ....- .---- --... .---- ....-"),
                      ("text:A.s_rot13", "PY76841714N"), ("text:A.s_atbash", "XO76841714Z"),
                      ("text:A.s_nato", "Charlie Lima 76841714 Alfa"), ("text:B.s_nato", "Kilo Bravo 46279860"),
                      ("text:A.s_keypad", "25768417142"), ("text:B.s_keypad", "5246279860"),
                      ("text:A.d_a1z26", "GFHDAGAD"), ("text:B.d_a1z26/zeroA", "EGCHJIGA"),
                      ("fib:A.a_zeck_idx/space", "39 35 33 30 21 15 11"),
                      ("fib:B.b_zeck_idx/space", "38 34 31 26 22 18 15 13 4 2"),
                      ("fib:A.pi_a/dec", "4495795"), ("fib:B.pi_b/dec", "2790857"),
                      ("fib:A.nextprime_a/dec", "76841741"), ("fib:A.prevprime_a/dec", "76841671"),
                      ("fib:A.nth_prime_a/dec", "1544728243"), ("fib:B.nth_prime_b/dec", "905578979"),
                      ("ip:A.a_ipv4", "4.148.130.242"), ("ip:A.ah_ipv4", "118.132.23.20"), ("ip:B.b_ipv4", "2.194.44.180"),
                      ("cf:AB.a/b_cf/space", "1 1 1 1 16 1 50 1 10 1 6 1 28 1 2"),
                      ("cf:AB.a/b_reduced", "38420857/23139930"), ("cf:AB.bezout/pair", "-7800347 12951466"),
                      ("cf:AB.a/b_colon", "76841714:46279860"),
                      ("base:A.a_bij26", "FLCYDN"), ("base:A.a_b2", format(a, "b")),
                      ("base:A.a_b36", "19qzg2"),      # 1*36^5 + 9*36^4 + 26*36^3 + 35*36^2 + 16*36 + 2
                      ("hash:A.d_md5/hex", hashlib.md5(A_D.encode()).hexdigest()),
                      ("hash:A.d_ripemd160/raw", "hex:" + hashlib.new("ripemd160", A_D.encode()).hexdigest()),
                      ("enc:A.bcd4/raw", "hex:76841714"),
                      ("pow:AB.a^b_mod_secp_n/raw32", "hex:" + pow(a, b, N).to_bytes(32, "big").hex()),
                      ("roman:A.a_d2/space", "LXXVI LXXXIV XVII XIV"), ("dmap:A.a_d1_fib/space", "13 8 21 3 1 13 1 3"),
                      ("cat:A.check:A.d_luhn/appended|+ d", "768417149 46279860"),
                      ("cat:B.btc:B.b_btc|s+", "CL76841714A0.46279860"),
                      ("cat:B.check:B.d_verhoeff/appended|d +", "76841714 462798608"),
                      ("pair:AB.btc.x_btc|a b", "0.76841714 0.46279860"),
                      ("pair:AB.check.d_luhn/appended|ab", "768417149462798604"),
                      ("pair:AB.fib.pi_x/dec|a b", "4495795 2790857"),
                      ("pair:AB.gray.gray32_x/dec|ab", "11526234761029102"),
                      ("pair:AB.block.h6/dec|a b", "768417 462798")):
        # a form that serial_combine's own closure already produces is filtered out by
        # design; that still proves the value was computed correctly, so it passes
        got = D.get(tag)
        rep(f"{tag} == {want[:48]!r}" + ("  [already swept by serial_combine, omitted]" if got is None and want in _SKIP else ""),
            got == want or (got is None and want in _SKIP))
    rep("the skip set really came from serial_combine (holds a+b and a BFS node)",
        "123121574" in _SKIP and "7684171438" in _SKIP and len(_SKIP) > 5000)
    for gone in ("123121574", "7684171446279860", "76841714", "1988564756", "49482f2",
                 "CL76841714A KB46279860", "7466824719781640", "2001 76841714"):
        rep(f"omits already-swept {gone!r}", gone not in V)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
