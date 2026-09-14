#!/usr/bin/env python3
"""
Given a solution, identify the method. Inverts this project's own corpora.

THE POINT
If someone solves this puzzle, "how did you do it" is answerable mechanically.
This project has generated hundreds of thousands of candidate phrases across
many sessions. If the winning key is the hash of any of them, that phrase can
be named exactly -- which identifies both the extraction rule and the
derivation, in one step.

It also settles which of the three joints in window/working_backwards.md the
solution broke:

  key matches a corpus phrase  -> we computed the right key and DISCARDED it,
                                  because the address was not funded when we
                                  looked. Joint J1, the oracle blind spot.
  key matches nothing          -> the material or the derivation is outside
                                  what we ever built. Joint J2 or J3.

USAGE
  python3 wf/reverse_lookup.py --selftest
  python3 wf/reverse_lookup.py --key <64-hex | WIF>
  python3 wf/reverse_lookup.py --addr <bitcoin address>

An address tells you the joint; a private key tells you the phrase.
"""
import argparse, hashlib, glob, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from hd_sweep import direct_keys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLVER = os.path.join(ROOT, "solver")

CORPUS_GLOBS = [
    "candidates*.txt", "likely_seeds.txt", "targets_*.txt",
    "article_transcript.txt", "highlights_ordered.tsv",
]


def load_corpus(verbose=True):
    """Every candidate phrase this project ever wrote to disk, plus the
    transcript's own n-grams."""
    phrases = set()
    for g in CORPUS_GLOBS:
        for path in glob.glob(os.path.join(SOLVER, g)):
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        s = line.rstrip("\n")
                        if 3 <= len(s) <= 400:
                            phrases.add(s)
                            phrases.add(s.strip())
            except Exception:
                continue
    # transcript n-grams, which were swept but never persisted as a file
    tp = os.path.join(SOLVER, "article_transcript.txt")
    if os.path.exists(tp):
        body = open(tp, encoding="utf-8", errors="replace").read()
        body = body.split("=== PAGE 75")[-1]
        words = re.findall(r"[A-Za-z0-9'$%.,-]+", body)
        for n in range(1, 13):
            for i in range(len(words) - n + 1):
                phrases.add(" ".join(words[i:i + n]))
    if verbose:
        sys.stderr.write(f"corpus: {len(phrases):,} distinct phrases\n")
    return phrases


def build_index(phrases, verbose=True):
    """phrase -> every fast-hash key this project ever derived from it."""
    t0 = time.time()
    idx = {}
    for p in phrases:
        try:
            for name, k in direct_keys(p).items():
                idx.setdefault(k, (p, name))
        except Exception:
            continue
    if verbose:
        sys.stderr.write(f"index: {len(idx):,} distinct keys in "
                         f"{time.time()-t0:.0f}s\n")
    return idx


def parse_key(s):
    s = s.strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", s):
        return bytes.fromhex(s)
    r = H.wif_check(s)
    if r:
        return r[1]
    return None


def report_key(priv, idx=None):
    print(f"private key : {priv.hex()}")
    print(f"WIF (comp)  : {H.to_wif(priv, True)}")
    print(f"WIF (uncomp): {H.to_wif(priv, False)}")
    o = H.Oracle()
    print("\naddresses:")
    for t, a in H.addrs_for_priv(priv).items():
        print(f"  {t:12} {a}   funded_now={o.funded(a)}")
    if idx is None:
        idx = build_index(load_corpus())
    hit = idx.get(priv)
    print("\ncorpus inversion:")
    if hit:
        phrase, deriv = hit
        print(f"  *** MATCH: this key is {deriv}({phrase!r})")
        print("  => the phrase and derivation are both identified.")
        print("  => JOINT J1: we computed this key and discarded it, because")
        print("     the address was not funded when our oracle looked.")
    else:
        print("  no match against any phrase this project ever generated")
        print("  => JOINT J2 or J3: the material or the derivation is outside")
        print("     everything we built. The phrase is not in our corpora.")


def report_addr(addr):
    o = H.Oracle()
    funded = o.funded(addr)
    print(f"address     : {addr}")
    print(f"funded now / in Apr-2023 rich list : {funded}")
    print("\njoint identification:")
    if funded:
        print("  currently visible to our oracle -- yet every sweep returned 0.")
        print("  => the derivation lies OUTSIDE our swept space: JOINT J2 or J3.")
    else:
        print("  invisible to both oracles.")
        print("  => if this address has on-chain HISTORY, JOINT J1 is confirmed:")
        print("     our detector could only ever see balance, never history, so")
        print("     a swept prize reads identically to a wrong answer.")
        print("  => if it has NO history, the key was never funded at all.")
        print("  (we cannot distinguish these two from here: every Bitcoin API")
        print("   host is refused at CONNECT. One explorer lookup settles it.)")


def selftest():
    ok = True
    phrases = {"correct horse battery staple", "OVERDOSE", "El Salvador"}
    idx = build_index(phrases, verbose=False)
    k = hashlib.sha256(b"correct horse battery staple").digest()
    hit = idx.get(k)
    good = hit is not None and hit[0] == "correct horse battery staple"
    print(f"  corpus inversion names a planted phrase: {'OK' if good else 'FAIL'}")
    ok &= good
    a = H.addrs_for_priv(k)["p2pkh_u"]
    good2 = a == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    print(f"  derivation vector: {'OK' if good2 else 'FAIL'} ({a})")
    ok &= good2
    w = H.to_wif(bytes.fromhex("0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D"), False)
    good3 = w == "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ"
    print(f"  WIF vector: {'OK' if good3 else 'FAIL'}")
    ok &= good3
    good4 = parse_key("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ") is not None
    print(f"  WIF parsing: {'OK' if good4 else 'FAIL'}")
    ok &= good4
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key")
    ap.add_argument("--addr")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.addr:
        report_addr(a.addr)
    elif a.key:
        priv = parse_key(a.key)
        if priv is None:
            sys.exit("could not parse --key as 64-hex or WIF")
        report_key(priv)
    else:
        ap.print_help()
        print("\nCorpus size check:")
        build_index(load_corpus())


if __name__ == "__main__":
    main()
