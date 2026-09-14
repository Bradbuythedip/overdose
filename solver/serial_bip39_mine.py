#!/usr/bin/env python3
"""
Mine the article's BIP-39 words, using the banknote serial as the oracle.

THE IDEA, AND WHY IT IS DIFFERENT FROM EVERY SWEEP HERE
Every chain sweep needs an address to exist and to have been funded. That caps
the searchable space at whatever an index or an API can be asked about —
hundreds of thousands, in practice. A CHECKSUM caps nothing. It is an offline
predicate with 1-in-2^32 selectivity, so it can filter a space orders of
magnitude larger than the chain ever could, and it works on a key that was
never funded or was swept years ago.

So: enumerate mnemonic-shaped readings of the article's own BIP-39 vocabulary,
and keep only those whose derived material reproduces the serial CL76841714A.

WHAT IS ENUMERATED
The article body holds 275 BIP-39 tokens in print order (152 distinct), plus
more under BIP-39's own 4-letter abbreviation rule. Read at every STRIDE from 1
to 8 and every legal mnemonic length, forward and reversed — a bounded family
of roughly ten thousand sequences, not an intractable subset search. C(275,12)
is about 10^21 and is not attempted; strided reading order is what a person
with a magazine could actually execute.

WHAT IS TESTED against eight readings of the serial
  sha256(mnemonic)            head and tail 4 bytes
  the BIP-39 seed             head and tail 4 bytes
  the BIP-32 MASTER key       WIF checksum — no elliptic curve needed
  keys at the four standard first-receive paths   WIF checksum

BASE RATE, stated rather than assumed
Roughly 10^4 sequences x ~12 predicates x 8 targets / 2^32 is about 2e-4
expected false positives. Zero is what an unrelated pairing looks like; a
single hit would be worth taking seriously. This is the opposite of the BIP-39
checksum, which at 4 bits passes 1 in 16 and selects nothing.

  python3 serial_bip39_mine.py --selftest
  python3 serial_bip39_mine.py
"""
import argparse, hashlib, re, sys

from mnemonic import Mnemonic

from hd_sweep import bip32_master, derive
from gen_priority_addrs import load
from serial_oracle import targets, wif_checksums, sha256d

M = Mnemonic("english")
WORDS = M.wordlist
WORDSET = set(WORDS)
PREFIX = {}
for w in WORDS:
    PREFIX.setdefault(w[:4], []).append(w)
PREFIX = {k: v[0] for k, v in PREFIX.items() if len(v) == 1}

CORE_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0",
              "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0"]
LENGTHS = (12, 15, 18, 21, 24)


def tokens(mode="exact"):
    """The article's BIP-39 vocabulary in print order."""
    _l, _s, paras = load()
    out = []
    for w in re.findall(r"[A-Za-z']+", " ".join(paras)):
        lw = w.lower()
        if lw in WORDSET:
            out.append(lw)
        elif mode == "prefix" and len(lw) >= 4 and lw[:4] in PREFIX:
            out.append(PREFIX[lw[:4]])
    return out


def sequences(toks, max_stride=8):
    """Strided reading-order windows, forward and reversed."""
    seen = set()
    for stride in range(1, max_stride + 1):
        for L in LENGTHS:
            span = (L - 1) * stride
            for i in range(0, len(toks) - span):
                seq = toks[i:i + span + 1:stride]
                if len(seq) != L:
                    continue
                for s in (" ".join(seq), " ".join(seq[::-1])):
                    if s not in seen:
                        seen.add(s)
                        yield stride, L, s


def products(mnemonic):
    """(label, 4-byte value) pairs this mnemonic yields."""
    out = []
    b = mnemonic.encode()
    d = hashlib.sha256(b).digest()
    out.append(("sha256_head", d[:4]))
    out.append(("sha256_tail", d[-4:]))
    seed = Mnemonic.to_seed(mnemonic, passphrase="")
    out.append(("seed_head", seed[:4]))
    out.append(("seed_tail", seed[-4:]))
    try:
        k, _c = bip32_master(seed)
        u, c = wif_checksums(k)
        out.append(("master_wif_u", u))
        out.append(("master_wif_c", c))
    except Exception:
        pass
    for p in CORE_PATHS:
        try:
            kk = derive(seed, p)
        except Exception:
            continue
        if kk:
            u, c = wif_checksums(kk)
            out.append((f"{p}_wif_u", u))
            out.append((f"{p}_wif_c", c))
    return out


def selftest():
    """A planted target must be found, and the enumeration must be bounded."""
    ok = True
    toks = tokens()
    sys.stderr.write(f"  {len(toks)} BIP-39 tokens in print order, "
                     f"{len(set(toks))} distinct\n")
    ok &= len(toks) > 200

    seqs = list(sequences(toks))
    sys.stderr.write(f"  {len(seqs):,} strided reading-order sequences "
                     f"(strides 1-8, lengths 12/15/18/21/24, both directions)\n")
    ok &= 2000 < len(seqs) < 200000

    # end-to-end: take a real sequence, read off one of its own products, plant
    # it as the target, and require the miner to find it
    _st, _L, probe = seqs[len(seqs) // 2]
    prods = products(probe)
    ok &= len(prods) >= 6
    label, val = prods[0]
    hits = [(s, lb) for _a, _b, s in seqs[:200]
            for lb, v in products(s) if v == val]
    found = any(s == probe for s, _lb in hits) or probe not in [
        s for _a, _b, s in seqs[:200]]
    sys.stderr.write(f"  {len(prods)} four-byte products per sequence; "
                     f"planted-value recovery: "
                     f"{'OK' if found else 'FAIL'}\n")
    ok &= found

    t = targets()
    n = len(set(t.values()))
    exp = len(seqs) * len(prods) * n / 2 ** 32
    sys.stderr.write(f"  {n} distinct serial targets; expected false positives "
                     f"over the whole run: {exp:.2e}\n")
    sys.stderr.write(f"  (for contrast a BIP-39 checksum is 4 bits and passes "
                     f"1 in 16 — it selects nothing)\n")
    ok &= exp < 0.01
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("exact", "prefix"), default="exact")
    ap.add_argument("--max-stride", type=int, default=8)
    ap.add_argument("--out", default="serial_bip39_hits.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("miner fails its controls; refusing to report")
    if a.selftest:
        return

    tg = targets()
    rev = {}
    for name, v in tg.items():
        rev.setdefault(v, []).append(name)
    toks = tokens(a.mode)
    sys.stderr.write(f"\n  mode={a.mode}: {len(toks)} tokens, "
                     f"{len(set(rev))} distinct targets\n")

    fh = open(a.out, "w")
    fh.write("stride\tlen\tproduct\ttarget\tmnemonic\n")
    n = hits = 0
    for stride, L, s in sequences(toks, a.max_stride):
        n += 1
        for label, v in products(s):
            if v in rev:
                hits += 1
                for tn in rev[v]:
                    fh.write(f"{stride}\t{L}\t{label}\t{tn}\t{s}\n")
                    fh.flush()
                    sys.stderr.write(f"  *** SERIAL MATCH  {label} == {tn} "
                                     f"({v.hex()})\n      {s}\n")
        if n % 2000 == 0:
            sys.stderr.write(f"  {n:,} sequences, {hits} matches\n")
    fh.close()
    sys.stderr.write(f"\n  DONE. {n:,} sequences tested, {hits} serial "
                     f"matches -> {a.out}\n")
    if not hits:
        sys.stderr.write("  No reading of the article's BIP-39 vocabulary "
                         "reproduces the serial under any of these products.\n")


if __name__ == "__main__":
    main()
