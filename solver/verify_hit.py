#!/usr/bin/env python3
"""
Take a checksum hit seriously: derive EVERYTHING from it and ask the chain.

WHY THIS EXISTS SEPARATELY
continuous_solver._verify_on_chain disposes of a hit using the offline index
and three key constructions into P2PKH. That is too thin to settle anything,
twice over. The index is a BALANCE SNAPSHOT — window/the_oracle_blind_spot.md
records that 64 of 64 known-swept brainwallets are absent from it — so a null
from it is not evidence the key was never funded. And three constructions is
not the derivation space.

A 4-byte checksum match is a 1-in-4-billion filter, which sounds decisive and
is not: the serial_cs family alone tests ~200M phrases against 14 products, so
several matches are EXPECTED from noise. The only way to tell a noise match
from the real thing is a second test whose false-positive rate is negligible,
and on-chain history is that test at roughly 2^-160.

So this emits the full derivation of each hit phrase for everfunded.py, whose
control is already proven against live swept addresses:

  7 direct key hashes            x 5 address forms + 20 wrapped script forms
  5 seed derivations x 72 paths  x 5 address forms
  the integer, hex-tiled and reversed readings of a numeric phrase
  bare P2PK, both pubkey encodings — invisible to every address index

  python3 verify_hit.py --selftest
  python3 verify_hit.py --from-ledger
  python3 verify_hit.py --phrase 68352982 --phrase CL32355025A
  python3 everfunded.py --base "$B" --addresses verify_hit_addrs.txt --auto

The second command writes verify_hit_addrs.txt and verify_hit_manifest.tsv, so
any hit the sweep reports is attributable to an exact derivation rather than to
a bare address.
"""
import argparse, hashlib, os, re, sqlite3, sys

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def key_variants(phrase):
    """Readings of a phrase AS a 32-byte key, beyond hashing it."""
    out, t = [], phrase.strip()
    if t.isdigit() and len(t) <= 78 and int(t) < N:
        out.append(("int", int(t).to_bytes(32, "big")))
        r = t[::-1]
        if int(r) < N:
            out.append(("int_rev", int(r).to_bytes(32, "big")))
    if re.fullmatch(r"[0-9a-fA-F]{8}", t):
        out.append(("hex_tiled", bytes.fromhex(t * 8)))
        out.append(("hex_tiled_rev", bytes.fromhex(t[::-1] * 8)))
    if re.fullmatch(r"[0-9a-fA-F]{64}", t):
        out.append(("hex", bytes.fromhex(t)))
    return [(n, k) for n, k in out if 0 < int.from_bytes(k, "big") < N]


def derive_all(phrase, emit, paths=None):
    from hd_sweep import all_addrs, build_paths, derive, direct_keys, seeds_from
    from spk_extra import spks_extra, sc_p2pk
    from everfunded import scripthash
    from coincurve import PrivateKey

    keys = list(direct_keys(phrase).items()) + key_variants(phrase)
    for sn, seed in seeds_from(phrase).items():
        for p in (paths if paths is not None else build_paths()):
            try:
                k = derive(seed, p)
            except Exception:
                continue
            if k:
                keys.append((f"{sn}:{p}", k))

    for dn, k in keys:
        for i, ad in enumerate(all_addrs(k)):
            emit(phrase, f"{dn}|addr{i}", ad)
        # the forms no address index can represent
        pub = PrivateKey(k).public_key
        for comp in (True, False):
            emit(phrase, f"{dn}|p2pk_{'c' if comp else 'u'}",
                 scripthash(sc_p2pk(pub.format(compressed=comp))))
        for st, spk in spks_extra(k):
            emit(phrase, f"{dn}|{st}", scripthash(spk))


def ledger_phrases(path="solver_ledger.sqlite"):
    if not os.path.exists(path):
        return []
    db = sqlite3.connect(path)
    try:
        rows = db.execute("SELECT DISTINCT label FROM hits").fetchall()
    except sqlite3.Error:
        return []
    out = []
    for (lab,) in rows:
        # the checksum families record the phrase as the label
        out.append(lab.split("|")[0] if "|" in lab else lab)
    return out


def selftest():
    """The derivation must reproduce everfunded's own control addresses, or
    this script is deriving something other than what the oracle was proven on.
    """
    from everfunded import SWEPT_CONTROLS
    ok = True
    for phrase, unc, comp in SWEPT_CONTROLS[:3]:
        got = []
        derive_all(phrase, lambda p, w, k: got.append((w, k)), paths=[])
        addrs = [k for w, k in got if w.startswith("sha256|addr")]
        good = unc in addrs and comp in addrs
        ok &= good
        sys.stderr.write(f"  {phrase!r:34} both control addresses present: "
                         f"{'OK' if good else 'FAIL'}\n")
    n = len(got)
    sys.stderr.write(f"  {n} keys per phrase with HD paths disabled "
                     f"(direct hashes and key readings only)\n")
    kv = key_variants("76841714")
    ok &= len(kv) >= 2
    sys.stderr.write(f"  numeric phrase yields {len(kv)} direct key readings: "
                     f"{', '.join(n for n, _ in kv)}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrase", action="append", default=[])
    ap.add_argument("--from-ledger", action="store_true")
    ap.add_argument("--ledger", default="solver_ledger.sqlite")
    ap.add_argument("--out", default="verify_hit_addrs.txt")
    ap.add_argument("--manifest", default="verify_hit_manifest.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("derivation disagrees with everfunded's control table; "
                 "refusing to emit a list the oracle was not proven on")
    if a.selftest:
        return

    phrases = list(a.phrase)
    if a.from_ledger:
        phrases += ledger_phrases(a.ledger)
    phrases = sorted({p for p in phrases if p})
    if not phrases:
        sys.exit("no phrases: pass --phrase, or --from-ledger with recorded "
                 "hits")

    sys.stderr.write(f"\n  {len(phrases)} phrase(s) to verify:\n")
    for p in phrases:
        sys.stderr.write(f"    {p!r}\n")

    rows, seen = [], set()

    def emit(phrase, why, key):
        if key in seen:
            return
        seen.add(key)
        rows.append((phrase, why, key))

    for p in phrases:
        derive_all(p, emit)

    with open(a.out, "w") as fh:
        for _p, _w, k in rows:
            fh.write(k + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("phrase\tderivation\tkey\n")
        for p, w, k in rows:
            fh.write(f"{p}\t{w}\t{k}\n")

    nsh = sum(1 for _p, _w, k in rows if k.startswith("sh:"))
    sys.stderr.write(f"\n  {len(rows):,} unique lookups -> {a.out}\n")
    sys.stderr.write(f"    {len(rows)-nsh:,} addresses, {nsh:,} scripthash "
                     f"(P2PK and the wrapped forms)\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n\n")
    sys.stderr.write(f"  now ask the chain, with the oracle whose control is "
                     f"proven:\n")
    sys.stderr.write(f"    python3 everfunded.py --base \"$B\" --addresses "
                     f"{a.out} --auto\n")


if __name__ == "__main__":
    main()
