#!/usr/bin/env python3
"""
The DEEP API list: the derivations the 45k brainwallet pass did not cover.

WHAT THE FIRST PASS ESTABLISHED
everfunded.py over everfunded_priority.txt returned a real ever-funded answer
for the first time in this project: 44,956 addresses — every sentence,
paragraph, line and 2..12 word n-gram of the column, both cases, as
sha256(phrase) -> P2PKH — never funded. Not now, not ever. The only two hits
were dust of 1,254 and 50,000 sats, dated February 2025, two years after the
announcement tweet; a sprayer or a scraper-fed cracker, not the prize.

WHAT IT DID NOT COVER
That pass deliberately took the cheapest slice: ONE hash into ONE script type.
The offline sweeps use seven direct key hashes across five script types plus
five seed derivations over an HD path set. Applying all of that to every n-gram
would be millions of API calls; applying it to the HIGH-PRIOR phrases only is a
few tens of thousands, and those phrases are where the prize would be if it is
anywhere.

So this emits, for the tier-1 phrase set alone (title, byline, headline, every
sentence, paragraph, line, the furniture strings) plus the serial and its
entropy readings:

  7 direct key hashes  x 5 script types
  5 seed derivations   x the four standard first-receive paths x 5 script types
  the nine seeded-generator entropy keys from serial_entropy

Script types are P2PKH compressed and uncompressed, P2SH-P2WPKH, P2WPKH and
P2TR — Esplora resolves bech32 and bech32m as happily as base58, so there is no
reason to restrict this to legacy addresses the way the offline P2PK blind spot
forced elsewhere.

Addresses already in everfunded_priority.txt are skipped, so this is purely
additional work.

  python3 gen_deep_addrs.py --selftest
  python3 gen_deep_addrs.py
"""
import argparse, hashlib, os, re, sys

from hd_sweep import all_addrs, build_paths, derive, direct_keys, seeds_from
from gen_priority_addrs import load, addrs_for_phrase

SERIAL, DIGITS = "CL76841714A", "76841714"
# the four standard first-receive paths, rather than the full 72-path set
CORE_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0",
              "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0"]


def tier1_phrases():
    lines, sents, paras = load()
    out = list(sents) + [s.lower() for s in sents] + paras + lines
    out += [
        "BITCOIN IS TOXIC AF", "Bitcoin Is Toxic AF", "bitcoin is toxic af",
        "OVERDOSE", "Overdose", "overdose", "MAX KEISER", "Max Keiser",
        "with Max Keiser", "ORANGEPILL", "orangepill",
        "THE EL SALVADOR ISSUE", "El Salvador", "el salvador",
        "The numbers don't lie.", "right there in the Genesis Block.",
        "Look, toxicity is Layer 1 of the protocol.",
        "the Layer 1 of the whole Satoshi experience.",
        "We've seen some shit.", "Don't believe me?",
        SERIAL, SERIAL.lower(), DIGITS, DIGITS[::-1], "L12",
    ]
    seen, uniq = set(), []
    for p in out:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def entropy_keys():
    """The seeded-generator keys, reusing serial_entropy's own generators."""
    import serial_entropy as SE
    out = []
    for sname, sv in SE.seeds().items():
        for gname, fn in SE.GENS.items():
            try:
                out.append((f"entropy:{sname}:{gname}", fn(sv, 32)))
            except Exception:
                pass
    return out


def selftest():
    """Derivations must agree with the modules they come from."""
    ok = True
    k = hashlib.sha256(b"satoshi").digest()
    a = all_addrs(k)
    b = addrs_for_phrase("satoshi")
    # NOTE the two modules order the pubkey forms differently: all_addrs gives
    # [compressed, uncompressed] and addrs_for_phrase gives [uncompressed,
    # compressed]. Same set, opposite order. Harmless for a membership check
    # like this one, and recorded here because anything that indexed them
    # positionally would silently pair the wrong address with the wrong form.
    same = set(a[:2]) == set(b)
    ok &= same
    sys.stderr.write(f"  all_addrs P2PKH pair matches the priority list's "
                     f"(order differs): {'OK' if same else 'FAIL'}\n")
    sys.stderr.write(f"    all_addrs        {a[0]} / {a[1]}\n")
    sys.stderr.write(f"    addrs_for_phrase {b[0]} / {b[1]}\n")
    kinds = len(a)
    ok &= kinds == 5
    sys.stderr.write(f"  {kinds} script types per key (want 5: p2pkh x2, "
                     f"p2sh-p2wpkh, p2wpkh, p2tr)\n")
    ek = entropy_keys()
    ok &= len(ek) > 100
    sys.stderr.write(f"  {len(ek)} seeded-generator entropy keys available\n")
    ok &= len(direct_keys("x")) >= 7 and len(seeds_from("x")) >= 5
    sys.stderr.write(f"  {len(direct_keys('x'))} direct hashes, "
                     f"{len(seeds_from('x'))} seed derivations per phrase\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_deep.txt")
    ap.add_argument("--manifest", default="everfunded_deep_manifest.tsv")
    ap.add_argument("--skip", default="everfunded_priority.txt")
    ap.add_argument("--max", type=int, default=90000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("derivations disagree with their source modules; refusing")
    if a.selftest:
        return

    already = set()
    if os.path.exists(a.skip):
        already = {l.strip() for l in open(a.skip) if l.strip()}
    sys.stderr.write(f"\n  skipping {len(already):,} addresses already in "
                     f"{a.skip}\n")

    phrases = tier1_phrases()
    sys.stderr.write(f"  {len(phrases):,} tier-1 phrases\n")

    rows, seen = [], set()

    def emit(why, label, key):
        for ad in all_addrs(key):
            if ad in already or ad in seen:
                continue
            seen.add(ad)
            rows.append((why, label[:110], ad))

    for p in phrases:
        for hname, k in direct_keys(p).items():
            emit(f"direct:{hname}", p, k)
        for sname, seed in seeds_from(p).items():
            for path in CORE_PATHS:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    emit(f"{sname}:{path}", p, k)
        if len(rows) >= a.max:
            break

    for label, k in entropy_keys():
        emit("entropy", label, k)

    rows = rows[:a.max]
    with open(a.out, "w") as fh:
        for _w, _p, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("derivation\tphrase\taddress\n")
        for w, p, ad in rows:
            fh.write(f"{w}\t{p}\t{ad}\n")

    sys.stderr.write(f"  {len(rows):,} NEW addresses -> {a.out}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  at the ~90/s the endpoint sustained, about "
                     f"{len(rows)/90/60:.0f} minutes\n")


if __name__ == "__main__":
    main()
