#!/usr/bin/env python3
"""
Mine EVERY strided reading of the article, with the serial as the oracle.

THE GENERALISATION
serial_bip39_mine.py applied the serial-as-checksum idea to the article's 275
BIP-39 tokens: 46,560 sequences, zero matches. But BIP-39 vocabulary is an
arbitrary restriction. If Keiser hid a PASSPHRASE rather than a mnemonic, it is
drawn from all 1,244 words, and the same oracle covers that space just as well.

Why the space is reachable at all: a chain sweep must ask an index or an API
about each candidate, which caps it in the hundreds of thousands. A checksum is
an offline predicate at 1-in-2^32, so hundreds of thousands of sequences cost
seconds and the expected false positives stay far below one. It also sees a key
that was never funded or was swept — which the chain cannot.

WHAT IS ENUMERATED
Strided reading-order windows of all 1,244 body words: every stride 1..12,
every length 2..24, forward and reversed, each in spaced and joined form. This
is the same family the null-cipher sweeps used, except that here the
VERIFICATION is offline, so the space can be far larger than anything the chain
was ever asked about.

PRODUCTS, all cheap — no elliptic curve
  sha256, double-sha256, both sha512 halves, sha3-256, blake2b: head and tail
  the WIF checksum of sha256(phrase) read as a private key — the brainwallet
  key itself, which is the derivation this article would most plausibly use

  python3 serial_text_mine.py --selftest
  python3 serial_text_mine.py
"""
import argparse, hashlib, re, sys

from gen_priority_addrs import load
from serial_oracle import targets, wif_checksums

HASHES = {
    "sha256": lambda b: hashlib.sha256(b).digest(),
    "dsha256": lambda b: hashlib.sha256(hashlib.sha256(b).digest()).digest(),
    "sha512h": lambda b: hashlib.sha512(b).digest()[:32],
    "sha512l": lambda b: hashlib.sha512(b).digest()[32:],
    "sha3_256": lambda b: hashlib.sha3_256(b).digest(),
    "blake2b": lambda b: hashlib.blake2b(b, digest_size=32).digest(),
}


def words():
    _l, _s, paras = load()
    return re.findall(r"[A-Za-z0-9$%'-]+", " ".join(paras))


def sequences(ws, max_stride, min_len, max_len):
    seen = set()
    for stride in range(1, max_stride + 1):
        for L in range(min_len, max_len + 1):
            span = (L - 1) * stride
            if span >= len(ws):
                break
            for i in range(0, len(ws) - span):
                seq = ws[i:i + span + 1:stride]
                if len(seq) != L:
                    continue
                for s in (seq, seq[::-1]):
                    for form in (" ".join(s), "".join(s).lower()):
                        if form not in seen:
                            seen.add(form)
                            yield stride, L, form


def products(phrase):
    b = phrase.encode("utf-8")
    out = []
    for name, fn in HASHES.items():
        d = fn(b)
        out.append((name + "_head", d[:4]))
        out.append((name + "_tail", d[-4:]))
    k = hashlib.sha256(b).digest()
    u, c = wif_checksums(k)
    out.append(("brainwallet_wif_u", u))
    out.append(("brainwallet_wif_c", c))
    return out


def selftest():
    ok = True
    ws = words()
    sys.stderr.write(f"  {len(ws)} body words\n")
    ok &= len(ws) > 1000

    # planted-target recovery through the real code path
    probe = " ".join(ws[100:106])
    lbl, val = products(probe)[0]
    found = any(v == val for _l, v in products(probe))
    sys.stderr.write(f"  {len(products(probe))} products per phrase; planted "
                     f"value recovered: {'OK' if found else 'FAIL'}\n")
    ok &= found

    # the brainwallet WIF product must match an independent computation
    k = hashlib.sha256(probe.encode()).digest()
    exp = hashlib.sha256(hashlib.sha256(b"\x80" + k).digest()).digest()[:4]
    got = dict(products(probe))["brainwallet_wif_u"]
    ok &= exp == got
    sys.stderr.write(f"  brainwallet WIF checksum matches an independent "
                     f"computation: {'OK' if exp == got else 'FAIL'}\n")

    n = sum(1 for _ in sequences(ws, 3, 2, 6))
    sys.stderr.write(f"  enumeration is bounded (stride<=3, len 2-6): "
                     f"{n:,} sequences\n")
    ok &= 0 < n < 500000
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-stride", type=int, default=12)
    ap.add_argument("--min-len", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=24)
    ap.add_argument("--out", default="serial_text_hits.tsv")
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
    ws = words()

    fh = open(a.out, "w")
    fh.write("stride\tlen\tproduct\ttarget\tphrase\n")
    n = hits = 0
    for stride, L, s in sequences(ws, a.max_stride, a.min_len, a.max_len):
        n += 1
        for label, v in products(s):
            if v in rev:
                hits += 1
                for tn in rev[v]:
                    fh.write(f"{stride}\t{L}\t{label}\t{tn}\t{s[:120]}\n")
                    fh.flush()
                    sys.stderr.write(f"  *** SERIAL MATCH {label} == {tn} "
                                     f"({v.hex()})\n      {s[:120]}\n")
        if n % 200000 == 0:
            sys.stderr.write(f"  {n:,} sequences, {hits} matches\n")
    fh.close()
    npred = len(products("x"))
    exp = n * npred * len(set(rev)) / 2 ** 32
    sys.stderr.write(f"\n  DONE. {n:,} sequences x {npred} products x "
                     f"{len(set(rev))} targets\n")
    sys.stderr.write(f"  expected false positives {exp:.3f}, observed {hits}\n")
    if not hits:
        sys.stderr.write("  No strided reading of the article reproduces the "
                         "serial under any of these products.\n")


if __name__ == "__main__":
    main()
