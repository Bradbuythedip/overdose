#!/usr/bin/env python3
"""
The serial as ENTROPY — a seed fed to a random number generator.

THE THREE FRAMINGS, AND WHY THIS ONE IS DIFFERENT
The serial has now been tested as a PASSPHRASE (hash it: 4,642 keys, null) and
as a CHECKSUM (does some derivation reproduce it: 13.4M keys, null). Both treat
the digits as an object to be matched. This treats them as a SEED: the number a
person types into a generator to produce a key.

That is what a non-cryptographer actually does. "I used the serial number off
this bill" is a sentence a showman says; "I used it as the HMAC key over my
column's stylistic outliers" is not.

THE CONSEQUENCE THAT MAKES THIS WORTH RUNNING
Eight decimal digits is 10^8, about 26.6 bits. That is not a key, it is a
keyspace you can exhaust on a laptop. So this hypothesis carries a hard
prediction: if Keiser seeded a wallet this way, the 20 BTC was findable by
anyone running a seeded-PRNG sweep, and it would have been taken long ago.

Which means the current-balance index is the WRONG oracle for it. A key that
was funded in 2021 and swept in 2022 is invisible to a snapshot of today's
UTXOs and shows up only in the HISTORICAL ever-funded index. Every candidate
here is therefore screened against both, and a hit in the historical index
alone would still be the answer to "was this the mechanism" even though the
coins are gone.

GENERATORS
Seeded PRNGs differ by implementation, so the seed alone does not fix the
output. Covered: Python's Mersenne Twister via random.seed (the overwhelmingly
likely choice for someone scripting this), numpy's legacy RandomState, a
straight MT19937 byte stream, glibc rand(), and Java's java.util.Random LCG.
Each produces 32-byte keys and 16/32-byte BIP-39 entropies.

SEEDS
Every reading of the serial that is a number: the digits as decimal, as hex,
reversed, the letters valued, the district, and the printed date fields.

  python3 serial_entropy.py --selftest
  python3 serial_entropy.py
"""
import argparse, hashlib, random, struct, sys

import numpy as np
from mnemonic import Mnemonic

from hd_sweep import build_paths, derive
from full_sweep import spks_for_key
from index_oracle import Oracle, spk_from_address
from hist_index import HistIndex

SERIAL = "CL76841714A"
DIGITS = "76841714"


def seeds():
    """Numeric readings of the serial and its printed companions."""
    out = {}
    d = DIGITS
    out["decimal"] = int(d)
    out["decimal_rev"] = int(d[::-1])
    out["hex"] = int(d, 16)
    out["hex_rev"] = int(d[::-1], 16)
    out["district"] = 12
    out["with_letters"] = int("3" + "12" + d + "1")
    out["serial_sha_int"] = int.from_bytes(
        hashlib.sha256(SERIAL.encode()).digest()[:8], "big")
    out["date_display"] = 20220223          # Display Until Feb 23, 2022
    out["upc"] = 74820403884
    out["price"] = 1299
    for k in list(out):
        out[k + "_neg"] = -out[k] if out[k] < 2 ** 31 else out[k]
    return out


def gen_python(seed, n):
    r = random.Random(seed)
    return bytes(r.getrandbits(8) for _ in range(n))


def gen_python_urandom_style(seed, n):
    r = random.Random(seed)
    return r.getrandbits(n * 8).to_bytes(n, "big")


def gen_numpy(seed, n):
    rs = np.random.RandomState(abs(int(seed)) % (2 ** 32))
    return bytes(rs.randint(0, 256, size=n, dtype=np.uint8))


def gen_glibc(seed, n):
    """glibc rand(): TYPE_3 additive feedback, low byte of each output."""
    r = [0] * 344
    r[0] = int(seed) & 0xFFFFFFFF or 1
    for i in range(1, 31):
        r[i] = (16807 * r[i - 1]) % 2147483647
        if r[i] < 0:
            r[i] += 2147483647
    for i in range(31, 34):
        r[i] = r[i - 31]
    for i in range(34, 344):
        r[i] = (r[i - 31] + r[i - 3]) & 0xFFFFFFFF
    out, st = [], list(r)
    idx = 344
    while len(out) < n:
        v = (st[idx - 31] + st[idx - 3]) & 0xFFFFFFFF
        st.append(v)
        out.append((v >> 1) & 0xFF)
        idx += 1
    return bytes(out)


def gen_java(seed, n):
    """java.util.Random: 48-bit LCG, nextInt() high bits."""
    s = (int(seed) ^ 0x5DEECE66D) & ((1 << 48) - 1)
    out = []
    while len(out) < n:
        s = (s * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        out.extend(struct.pack(">I", (s >> 16) & 0xFFFFFFFF))
    return bytes(out[:n])


def gen_msvc(seed, n):
    """MSVC rand(): 32-bit LCG, 15-bit output."""
    s = int(seed) & 0xFFFFFFFF
    out = []
    while len(out) < n:
        s = (s * 214013 + 2531011) & 0xFFFFFFFF
        out.append((s >> 16) & 0xFF)
    return bytes(out)


def gen_xorshift64(seed, n):
    """Marsaglia xorshift64*, a common one-liner PRNG."""
    x = int(seed) & 0xFFFFFFFFFFFFFFFF or 0x9E3779B97F4A7C15
    out = []
    while len(out) < n:
        x ^= (x >> 12) & 0xFFFFFFFFFFFFFFFF
        x ^= (x << 25) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 27) & 0xFFFFFFFFFFFFFFFF
        v = (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF
        out.extend(v.to_bytes(8, "big"))
    return bytes(out[:n])


def gen_pcg32(seed, n):
    """PCG32, the modern default in several languages' libraries."""
    MUL, INC = 6364136223846793005, 1442695040888963407
    st = (int(seed) + INC) & 0xFFFFFFFFFFFFFFFF
    st = (st * MUL + INC) & 0xFFFFFFFFFFFFFFFF
    out = []
    while len(out) < n:
        old = st
        st = (old * MUL + INC) & 0xFFFFFFFFFFFFFFFF
        xs = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rot = (old >> 59) & 31
        v = ((xs >> rot) | (xs << ((-rot) & 31))) & 0xFFFFFFFF
        out.extend(v.to_bytes(4, "big"))
    return bytes(out[:n])


def gen_tile(seed, n):
    """NOT a PRNG: the digits repeated to fill the key.

    This is the reading a person is most likely to actually produce. Asked to
    turn eight digits into a 32-byte key by hand, the obvious move is to repeat
    them until the field is full — "76841714" eight times is exactly 64 hex
    characters. No library, no seeding convention, no ambiguity.
    """
    d = str(abs(int(seed)))
    if not set(d) <= set("0123456789abcdefABCDEF"):
        d = "0"
    need = n * 2                       # hex characters
    return bytes.fromhex((d * (need // len(d) + 1))[:need])


GENS = {"python_mt": gen_python, "python_bits": gen_python_urandom_style,
        "numpy_legacy": gen_numpy, "glibc_rand": gen_glibc,
        "java_random": gen_java, "msvc_rand": gen_msvc,
        "xorshift64": gen_xorshift64, "pcg32": gen_pcg32,
        "tiled_digits": gen_tile}


def selftest():
    """Generators must be deterministic, distinct, and byte-correct where a
    published vector exists; and the indices must answer."""
    ok = True
    for name, fn in GENS.items():
        a, b = fn(12345, 32), fn(12345, 32)
        ok &= a == b and len(a) == 32
        sys.stderr.write(f"  {name:14} seed 12345 -> {a[:8].hex()}...  "
                         f"deterministic {'OK' if a == b else 'FAIL'}\n")
    outs = {fn(12345, 32) for fn in GENS.values()}
    sys.stderr.write(f"  {len(outs)} distinct outputs from {len(GENS)} "
                     f"generators on the same seed: "
                     f"{'OK' if len(outs) == len(GENS) else 'FAIL'}\n")
    ok &= len(outs) == len(GENS)

    # java.util.Random(0).nextInt() is a published value: -1155484576
    s = gen_java(0, 4)
    v = struct.unpack(">i", s)[0]
    sys.stderr.write(f"  java Random(0).nextInt() = {v} (want -1155484576): "
                     f"{'OK' if v == -1155484576 else 'FAIL'}\n")
    ok &= v == -1155484576

    # Python's MT is the reference; compare against ONE instance advanced four
    # times. Writing this as bytes(random.Random(42).getrandbits(8) for _ in
    # range(4)) rebuilds the generator on every iteration and yields the same
    # first byte four times (a3a3a3a3) — the reference, not gen_python, is what
    # that catches.
    ref = random.Random(42)
    ok &= gen_python(42, 4) == bytes(ref.getrandbits(8) for _ in range(4))
    sys.stderr.write(f"  python MT matches a single advanced instance: "
                     f"{'OK' if ok else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/serial_entropy_hits.tsv")
    ap.add_argument("--neighbourhood", type=int, default=0,
                    help="also try every serial within this Hamming distance "
                         "in DIGITS of 76841714, to cover a misread")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("generators fail their controls; refusing to sweep")
    if a.selftest:
        return

    cur = Oracle(verbose=False)
    if not cur.calibrate():
        sys.exit("oracle calibration failed")
    hist = HistIndex()
    ctrl = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    if not cur.contains_spks([ctrl]) or not hist.contains_spks([ctrl]):
        sys.exit("an index cannot see a known-funded address; refusing")
    sys.stderr.write(f"\n  CONTROL: both indices report the genesis address\n")
    sys.stderr.write(f"  current-balance index 56,795,328 | historical "
                     f"ever-funded {hist.n:,}\n")

    mnem = Mnemonic("english")
    paths = build_paths()
    sd = seeds()
    if a.neighbourhood:
        # The serial's head sits behind a fold on page 73 and the note on page
        # 74 resolves to ~40 px in the 200 dpi background layer, so one or two
        # digits could be misread. Enumerating the digit-neighbourhood costs
        # little and removes that doubt; enumerating all 10^8 would instead
        # test "some 8-digit number seeded a wallet", which is a different and
        # much weaker question about weak RNGs in general, not about this note.
        import itertools as _it
        base = list(DIGITS)
        extra, seen = {}, {DIGITS}
        for k in range(1, a.neighbourhood + 1):
            for pos in _it.combinations(range(8), k):
                for repl in _it.product("0123456789", repeat=k):
                    c = list(base)
                    for p, r in zip(pos, repl):
                        c[p] = r
                    t = "".join(c)
                    if t not in seen:
                        seen.add(t)
                        extra[f"nb_{t}"] = int(t)
        sd.update(extra)
        sys.stderr.write(f"  digit-neighbourhood radius {a.neighbourhood}: "
                         f"+{len(extra)} serial readings\n")
    sys.stderr.write(f"  {len(sd)} numeric readings x {len(GENS)} generators\n")
    sys.stderr.write("  NOTE: 8 decimal digits is ~26.6 bits. If this is the "
                     "mechanism the coins are long gone, so the HISTORICAL "
                     "index is the oracle that matters.\n\n")

    fh = open(a.out, "w")
    fh.write("seed\tgenerator\tform\tpath\tscript\tindex\tvalue\n")
    n_addr = n_hit = 0
    for sname, sv in sd.items():
        for gname, fn in GENS.items():
            keys = []
            try:
                k32 = fn(sv, 32)
            except Exception:
                continue
            keys.append((f"{gname}:raw32", k32))
            for ebytes in (16, 32):
                try:
                    ent = fn(sv, ebytes)
                    m = mnem.to_mnemonic(ent)
                except Exception:
                    continue
                seed64 = Mnemonic.to_seed(m, passphrase="")
                for p in paths:
                    try:
                        kk = derive(seed64, p)
                    except Exception:
                        continue
                    if kk:
                        keys.append((f"{gname}:bip39_{ebytes*8}:{p}", kk))
            meta, spks = [], []
            for form, k in keys:
                for st, spk in spks_for_key(k):
                    meta.append((form, st))
                    spks.append(spk)
            n_addr += len(spks)
            for idxname, idx in (("current", cur), ("historical", hist)):
                for j, val in idx.contains_spks(spks):
                    form, st = meta[j]
                    n_hit += 1
                    fh.write(f"{sname}={sv}\t{gname}\t{form}\t-\t{st}\t"
                             f"{idxname}\t{val}\n")
                    fh.flush()
                    sys.stderr.write(f"  *** HIT [{idxname}] {val} :: "
                                     f"seed {sname}={sv} :: {form} :: {st}\n")
        sys.stderr.write(f"  seed {sname:18} done, {n_addr:,} addresses, "
                         f"{n_hit} hits\n")
    fh.close()
    sys.stderr.write(f"\n  DONE. {n_addr:,} addresses from seeded generators, "
                     f"{n_hit} hits -> {a.out}\n")


if __name__ == "__main__":
    main()
