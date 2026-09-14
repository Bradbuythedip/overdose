#!/usr/bin/env python3
"""
The serial as the SECRET INPUT — BIP-39 passphrase and KDF salt — not as a test.

WHY THIS AND NOT MORE CHECKSUM PREDICATES
The serial-as-checksum idea has now been fired from two directions and returned
null both times. The temptation is to keep inventing predicates, and that is a
trap with a measurable signature: a parallel run testing a Casascius-style
`sha256(p + '?')[0] == 0` rule over 7,755 payloads reported 95 hits and
correctly identified them as the 1-in-256 noise floor. Every additional
predicate over a fixed payload set multiplies the false-positive budget while
the prior stays flat. That is a garden of forking paths, not a search.

The serial has two roles it structurally FITS, where it is an input and the
verification stays honest (chain index, or the key format's own checksum):

  BIP-39 passphrase   the "25th word". A secret printed on a physical object
                      handed to the solver is the canonical use of this field.
  KDF salt            WarpWallet's second field is literally a salt; PBKDF2 and
                      scrypt take one too.

Both are genuinely untested here. This repo's BIP-39 sweep used passphrases
["", "bitcoin", "Bitcoin", "overdose", "OVERDOSE", "Max Keiser", "mirror",
"20"] and its KDF sweeps used salts drawn from the same thematic list. The
serial is in neither.

CORRECTION CARRIED BY THIS FILE
gen_banknote.py asserts the note is "series 2009A". That is wrong, and the
error originated here rather than in any outside analysis. The note photographed
on pages 73 and 74 shows no blue 3-D security ribbon, no large colour-shifting
100, no bell-in-inkwell, and a classic scalloped Treasury seal with engraved
numerals — a pre-2013 design. A 2009A note has all of those features. With a
first letter of C the note is consistent with an early-2000s series, so the
apparent "series letter contradicts the series year" anomaly is an artefact of
this repo's own mislabelling, not a designed signal.

  python3 serial_secret.py --selftest
  python3 serial_secret.py --mnemonics bip39_valid.tsv
"""
import argparse, hashlib, itertools, os, sys

from mnemonic import Mnemonic

from hd_sweep import build_paths, derive
from full_sweep import spks_for_key
from index_oracle import Oracle

SERIAL = "CL76841714A"
DIGITS = "76841714"
DISTRICT = "L12"


def variants():
    """Forms of the serial a setter might actually have typed."""
    base = [SERIAL, DIGITS, DISTRICT,
            "CL 76841714 A", "CL-76841714-A", "C L 7 6 8 4 1 7 1 4 A",
            SERIAL + DISTRICT, DISTRICT + SERIAL,
            SERIAL + " " + DISTRICT, DIGITS + DISTRICT,
            "CL76841714A 2001", "2001", "L", "CL", "A"]
    out = []
    for b in base:
        for f in (b, b.lower(), b.upper(), b.replace(" ", "")):
            out.append(f)
            out.append(f[::-1])          # the note is printed mirrored
    return list(dict.fromkeys(out))


def load_mnemonics(path):
    """Checksum-valid mnemonics already extracted from the article."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            s = line.strip()
            if not s or (i == 0 and not s[0].islower()):
                continue
            m = s.split("\t")[0].strip()
            if len(m.split()) in (12, 15, 18, 21, 24):
                out.append(m)
    return list(dict.fromkeys(out))


def selftest():
    """BIP-39 passphrase handling must reproduce the official test vector."""
    m = ("abandon abandon abandon abandon abandon abandon abandon abandon "
         "abandon abandon abandon about")
    want = ("c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553"
            "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")
    got = Mnemonic.to_seed(m, passphrase="TREZOR").hex()
    ok = got == want
    sys.stderr.write(f"  BIP-39 vector (passphrase TREZOR): "
                     f"{'MATCH' if ok else 'MISMATCH'}\n")
    if not ok:
        sys.stderr.write(f"    want {want[:32]}...\n    got  {got[:32]}...\n")

    # A different passphrase must give a different seed, or the field is
    # being ignored and the whole sweep would be a no-op repeated N times.
    alt = Mnemonic.to_seed(m, passphrase=SERIAL).hex()
    ok2 = alt != got
    sys.stderr.write(f"  serial passphrase changes the seed: "
                     f"{'yes' if ok2 else 'NO — field ignored (FAIL)'}\n")

    v = variants()
    sys.stderr.write(f"  {len(v)} serial variants, e.g. {v[:3]}\n")
    ok3 = SERIAL in v and SERIAL[::-1] in v
    sys.stderr.write(f"  contains the serial and its mirror: "
                     f"{'OK' if ok3 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok and ok2 and ok3 else "FAIL\n"))
    return ok and ok2 and ok3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mnemonics", default="bip39_valid.tsv")
    ap.add_argument("--out", default="/tmp/serial_secret_hits.tsv")
    ap.add_argument("--hist", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("BIP-39 handling fails its own vector; refusing to sweep")
    if a.selftest:
        return

    mns = load_mnemonics(a.mnemonics)
    pws = variants()
    paths = build_paths()
    sys.stderr.write(f"\n  {len(mns)} checksum-valid mnemonics x {len(pws)} "
                     f"serial passphrases x {len(paths)} paths\n")
    if not mns:
        sys.exit("no mnemonics loaded")

    if a.hist:
        from hist_index import HistIndex
        idx = HistIndex()
        sys.stderr.write(f"  scoring against the HISTORICAL ever-funded index "
                         f"({idx.n:,})\n")
    else:
        idx = Oracle(verbose=False)
        if not idx.calibrate():
            sys.exit("oracle calibration failed")
        sys.stderr.write("  scoring against the current-balance index "
                         "(56,795,328)\n")

    # Positive control: a known-funded scriptPubKey injected into the stream
    # must be reported, or a null means the pipeline is dead rather than clean.
    from index_oracle import spk_from_address
    ctrl_spk = spk_from_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    got = idx.contains_spks([ctrl_spk])
    sys.stderr.write(f"  CONTROL genesis spk found by index: "
                     f"{'yes' if got else 'NO (FAIL)'}\n")
    if not got:
        sys.exit("index cannot find a known-funded address; refusing")

    n_addr = n_hit = 0
    fh = open(a.out, "w")
    fh.write("mnemonic\tpassphrase\tpath\tscript\tbalance\n")
    for mi, m in enumerate(mns, 1):
        for pw in pws:
            seed = Mnemonic.to_seed(m, passphrase=pw)
            meta, spks = [], []
            for p in paths:
                try:
                    k = derive(seed, p)
                except Exception:
                    continue
                for st, spk in spks_for_key(k):
                    meta.append((p, st))
                    spks.append(spk)
            n_addr += len(spks)
            for j, bal in idx.contains_spks(spks):
                p, st = meta[j]
                n_hit += 1
                fh.write(f"{m}\t{pw}\t{p}\t{st}\t{bal}\n")
                fh.flush()
                sys.stderr.write(f"  *** HIT {bal} :: pw={pw!r} path={p} "
                                 f"{st}\n      {m}\n")
        if mi % 10 == 0:
            sys.stderr.write(f"  {mi}/{len(mns)} mnemonics, {n_addr:,} "
                             f"addresses, {n_hit} hits\n")
    fh.close()
    sys.stderr.write(f"\n  DONE. {len(mns)} mnemonics x {len(pws)} serial "
                     f"passphrases -> {n_addr:,} addresses, {n_hit} hits\n")


if __name__ == "__main__":
    main()
