#!/usr/bin/env python3
"""
The article's BIP-39 mnemonics against the EVER-FUNDED oracle.

THE GAP THIS FILLS
The article's body contains 275 BIP-39 tokens (152 distinct), and reading them
in print order yields 32 checksum-valid windows: 18 twelve-word, 9 fifteen,
4 eighteen, 1 twenty-one. `bip39_sweep.py` extracted 186 checksum-valid
mnemonics and HD-derived them across 72 paths, 5 script types and 8
passphrases — and scored every one of them against the CURRENT-BALANCE index
only.

That index answers "holds coins today". A mnemonic that was derived, funded and
swept is invisible to it, and so is one funded before the April-2023 rich list.
So the BIP-39 family has never actually been asked the question that matters.

WHY THE CHECKSUM IS NOT DOING THE WORK HERE
A 12-word BIP-39 checksum is 4 bits: 1 in 16 of ANY word sequence passes. Over
the ~1,200 windows the article offers, ~75 pass by chance, and 18 observed is
in that range. The checksum is a length filter, not evidence, so it is used
only to keep the list a sane size — never as a reason to believe a mnemonic.
The chain is the filter with a usable base rate.

PASSPHRASES
The BIP-39 passphrase is the "25th word" and this repo's sweep used eight
thematic ones. The serial is added here because a secret printed on a physical
prop handed to the solver is the canonical use of that field, and it was never
tried in combination with the ARTICLE's mnemonics against a real history
oracle.

  python3 gen_bip39_addrs.py --selftest
  python3 gen_bip39_addrs.py
"""
import argparse, glob, os, re, sys

from mnemonic import Mnemonic

from hd_sweep import all_addrs, derive
from gen_priority_addrs import addrs_for_phrase, load

CORE_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0",
              "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0"]
PASSPHRASES = ["", "bitcoin", "Bitcoin", "overdose", "OVERDOSE", "Max Keiser",
               "mirror", "20", "El Salvador", "ORANGEPILL",
               "CL76841714A", "76841714"]
M = Mnemonic("english")
WORDS = set(M.wordlist)


def reading_order_windows():
    """Checksum-valid windows of the article's BIP-39 words, in print order."""
    lines, sents, paras = load()
    toks = [w.lower() for w in re.findall(r"[A-Za-z']+", " ".join(paras))
            if w.lower() in WORDS]
    out = []
    for L in (12, 15, 18, 21, 24):
        for i in range(len(toks) - L + 1):
            m = " ".join(toks[i:i + L])
            if M.check(m):
                out.append(m)
    return out, len(toks)


def from_file(path="bip39_valid.tsv"):
    out = []
    if not os.path.exists(path):
        return out
    for i, line in enumerate(open(path, encoding="utf-8")):
        s = line.strip().split("\t")[0].strip()
        if len(s.split()) in (12, 15, 18, 21, 24) and M.check(s):
            out.append(s)
    return out


def already_queried():
    seen = set()
    for f in glob.glob("everfunded_*.txt"):
        if "manifest" in f:
            continue
        seen |= {l.strip() for l in open(f) if l.strip()}
    return seen


def selftest():
    """BIP-39 handling must reproduce the official vector, the passphrase must
    change the seed, and the checksum base rate must be stated not assumed."""
    ok = True
    v = ("abandon abandon abandon abandon abandon abandon abandon abandon "
         "abandon abandon abandon about")
    want = ("c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553"
            "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")
    got = Mnemonic.to_seed(v, passphrase="TREZOR").hex()
    ok &= got == want
    sys.stderr.write(f"  BIP-39 TREZOR vector: {'MATCH' if got == want else 'MISMATCH'}\n")
    ok &= Mnemonic.to_seed(v, passphrase="x") != Mnemonic.to_seed(v)
    sys.stderr.write(f"  passphrase changes the seed: "
                     f"{'OK' if Mnemonic.to_seed(v, passphrase='x') != Mnemonic.to_seed(v) else 'FAIL'}\n")
    ok &= M.check(v) and not M.check(v.replace("about", "abandon"))
    sys.stderr.write(f"  checksum accepts the vector and rejects a corruption: "
                     f"{'OK' if ok else 'FAIL'}\n")
    w, n = reading_order_windows()
    sys.stderr.write(f"  article has {n} BIP-39 tokens -> {len(w)} "
                     f"checksum-valid windows in reading order\n")
    exp = (n - 11) / 16.0
    sys.stderr.write(f"  expected by chance at 1-in-16 for 12-word alone: "
                     f"~{exp:.0f} — the checksum is a LENGTH FILTER here, "
                     f"not evidence\n")
    ok &= len(w) > 0
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_bip39.txt")
    ap.add_argument("--manifest", default="everfunded_bip39_manifest.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("BIP-39 handling fails its vector; refusing")
    if a.selftest:
        return

    wins, _ = reading_order_windows()
    mns = list(dict.fromkeys(from_file() + wins))
    sys.stderr.write(f"\n  {len(mns)} distinct checksum-valid mnemonics "
                     f"({len(wins)} from reading order, rest from "
                     f"bip39_valid.tsv)\n")

    already = already_queried()
    sys.stderr.write(f"  skipping {len(already):,} already-queried addresses\n")

    rows, seen = [], set()
    for mi, m in enumerate(mns):
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
                    rows.append((f"pw={pw!r}:{path}", m[:100], ad))

    with open(a.out, "w") as fh:
        for _w, _m, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("derivation\tmnemonic\taddress\n")
        for w, m, ad in rows:
            fh.write(f"{w}\t{m}\t{ad}\n")
    sys.stderr.write(f"  {len(rows):,} NEW addresses -> {a.out}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  at ~250/s that is about {len(rows)/250/60:.0f} minutes\n")


if __name__ == "__main__":
    main()
