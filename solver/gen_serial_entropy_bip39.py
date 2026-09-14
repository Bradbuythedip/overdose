#!/usr/bin/env python3
"""
The serial as BIP-39 ENTROPY, against the ever-funded oracle.

THE GAP, MEASURED
serial_entropy.py already treats the serial as a seed for nine generators and
turns the output into BIP-39 entropy. But it scored everything against the two
offline BALANCE indices, and the API lists never carried the mnemonics: the
deep list's 180 entropy entries are RAW 32-byte private keys, not mnemonics.
So the chain has never been asked about

    serial -> BIP-39 entropy -> mnemonic -> seed -> HD path -> address

which is a different key at every step from the raw-key path.

WHY THE FRAMING IS SOUND AND WHAT IT COSTS
BIP-39 entropy must be 16, 20, 24, 28 or 32 bytes. The serial's eight digits are
four bytes read as hex, so using them AS entropy requires extending them, and
the extension is the guess. Three that a person would actually make are
covered — repeat the digits until the field is full (the by-hand move:
"76841714" four times is exactly 32 hex characters), zero-pad at either end, and
hash them — alongside the nine seeded generators.

The honest consequence: extending 4 bytes to 16 adds no entropy. Whatever the
method, the keyspace stays about 26.6 bits, which is exhaustible. So if this IS
the mechanism, the coins were takeable by anyone who guessed the same extension,
and the ever-funded oracle is the only thing that can see that happening. That
is exactly why this list exists rather than another balance-index sweep.

  python3 gen_serial_entropy_bip39.py --selftest
  python3 gen_serial_entropy_bip39.py
"""
import argparse, glob, hashlib, os, sys

from mnemonic import Mnemonic

from hd_sweep import all_addrs, derive
import serial_entropy as SE

M = Mnemonic("english")
SIZES = (16, 24, 32)
PASSPHRASES = ["", "bitcoin", "El Salvador", "CL76841714A"]
CORE_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0",
              "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0"]
SERIAL, DIGITS = "CL76841714A", "76841714"


def direct_entropies():
    """Extensions a person would make by hand, not via a library."""
    out = {}
    for d in (DIGITS, DIGITS[::-1]):
        for n in SIZES:
            need = n * 2
            out[f"tiled:{d}:{n}"] = bytes.fromhex((d * (need // len(d) + 1))[:need])
            out[f"zpad_left:{d}:{n}"] = bytes.fromhex(d.rjust(need, "0"))
            out[f"zpad_right:{d}:{n}"] = bytes.fromhex(d.ljust(need, "0"))
    for s in (SERIAL, SERIAL.lower(), DIGITS, SERIAL[::-1], DIGITS + "L12"):
        h = hashlib.sha256(s.encode()).digest()
        for n in SIZES:
            out[f"sha256:{s}:{n}"] = h[:n]
    return out


def generator_entropies():
    """serial_entropy's nine seeded generators, at BIP-39 legal sizes."""
    out = {}
    for sname, sv in SE.seeds().items():
        for gname, fn in SE.GENS.items():
            for n in SIZES:
                try:
                    out[f"{gname}:{sname}:{n}"] = fn(sv, n)
                except Exception:
                    pass
    return out


def already_queried():
    seen = set()
    for f in glob.glob("everfunded_*.txt"):
        if "manifest" in f:
            continue
        seen |= {l.strip() for l in open(f) if l.strip()}
    return seen


def selftest():
    ok = True
    v = ("abandon abandon abandon abandon abandon abandon abandon abandon "
         "abandon abandon abandon about")
    want = ("c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553"
            "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")
    ok &= Mnemonic.to_seed(v, passphrase="TREZOR").hex() == want
    sys.stderr.write(f"  BIP-39 TREZOR vector: {'MATCH' if ok else 'MISMATCH'}\n")

    d = direct_entropies()
    t = d[f"tiled:{DIGITS}:32"]
    exact = t.hex() == DIGITS * 8
    ok &= exact
    sys.stderr.write(f"  tiled 32-byte entropy is the digits repeated 8x: "
                     f"{'OK' if exact else 'FAIL'}\n")
    ok &= all(len(v) in (16, 24, 32) for v in d.values())
    sys.stderr.write(f"  {len(d)} hand extensions, all BIP-39 legal sizes\n")

    # every entropy must produce a checksum-valid mnemonic by construction
    bad = 0
    for k, e in list(d.items())[:20]:
        if not M.check(M.to_mnemonic(e)):
            bad += 1
    ok &= bad == 0
    sys.stderr.write(f"  to_mnemonic output is checksum-valid by construction: "
                     f"{'OK' if not bad else 'FAIL'}\n")

    g = generator_entropies()
    sys.stderr.write(f"  {len(g)} generator entropies\n")
    ok &= len(g) > 300
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_serial_bip39.txt")
    ap.add_argument("--manifest", default="everfunded_serial_bip39_manifest.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("BIP-39 handling fails its vector; refusing")
    if a.selftest:
        return

    ents = {}
    ents.update(direct_entropies())
    ents.update(generator_entropies())
    sys.stderr.write(f"\n  {len(ents)} entropies -> mnemonics\n")

    already = already_queried()
    sys.stderr.write(f"  skipping {len(already):,} already-queried addresses\n")

    rows, seen = [], set()
    for label, e in ents.items():
        try:
            m = M.to_mnemonic(e)
        except Exception:
            continue
        for pw in PASSPHRASES:
            seed = Mnemonic.to_seed(m, passphrase=pw)
            for path in CORE_PATHS:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if not k:
                    continue
                for ad in all_addrs(k):
                    if ad in already or ad in seen:
                        continue
                    seen.add(ad)
                    rows.append((f"{label}|pw={pw!r}|{path}", m[:90], ad))

    with open(a.out, "w") as fh:
        for _w, _m, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("entropy_source\tmnemonic\taddress\n")
        for w, m, ad in rows:
            fh.write(f"{w}\t{m}\t{ad}\n")
    sys.stderr.write(f"  {len(rows):,} NEW addresses -> {a.out}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  at ~250/s that is about {len(rows)/250/60:.0f} minutes\n")


if __name__ == "__main__":
    main()
