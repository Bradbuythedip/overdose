#!/usr/bin/env python3
"""
Every mirror reading of the banknote serial, through the FULL derivation stack.

THE GAP THIS CLOSES
The $100 note on pages 73/74 is printed upside down, and its serial is
CL 76841714 A. `note_check.py` already tested the mirrored reading
`A41714867LC` -- but only through four script forms (P2PKH compressed and
uncompressed, P2WPKH, P2SH-P2WPKH) and only through direct hashes. It never
touched:

    P2TR (Taproot)            the article carries a BIP-84/segwit hint
    bare P2PK                 how a 2011-era key would have been locked
    the 20 wrapped/multisig forms in spk_extra
    ANY HD derivation         BIP-32/39/44/49/84/86 -- no seed was ever built
                              from a mirrored reading

So "the mirror serial was swept" was true of one narrow slice and was being
quoted as though it covered everything. This runs the complete stack.

WHAT COUNTS AS A MIRROR
Three distinct operations, kept separate because they are not the same thing
and the literature on this puzzle conflates them:

  reverse    read the string backwards: CL76841714A -> A41714867LC
  rotate     turn the page 180 degrees. Digits map 0->0 1->1 6->9 8->8 9->6;
             2/3/4/5/7 have NO rotated digit, which is why window/
             serial_as_checksum.md argues the rotation reading is optically
             impossible. Included anyway, with unmappable glyphs left as-is,
             because the argument is about what a reader sees and this is
             about what a puzzle author might have typed.
  mirror     reflect left-right. A H I M O T U V W X Y 0 1 8 map to
             themselves; the rest do not.

POSITIVE CONTROL
A planted key must be FOUND before any null here is reported. A sweep that
cannot find a key it was handed produces a null indistinguishable from a real
one, and this project has shipped that mistake.

  python3 mirror_serial.py --selftest
  python3 mirror_serial.py
"""
import argparse, hashlib, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

SERIAL, DIGITS, DISTRICT = "CL76841714A", "76841714", "L12"

ROT180 = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6",
          "N": "N", "S": "S", "Z": "Z", "H": "H", "I": "I", "O": "O",
          "X": "X", "L": "7"}
MIRROR = {c: c for c in "AHIMOTUVWXY018"}
MIRROR.update({"b": "d", "d": "b", "p": "q", "q": "p",
               "C": "Ɔ", "L": "⅃", "E": "Ǝ", "J": "Ⴑ"})


def rot180(s):
    return "".join(ROT180.get(c, c) for c in reversed(s))


def mirror(s):
    return "".join(MIRROR.get(c, c) for c in reversed(s))


def readings():
    """Every mirror-family reading of the serial, named."""
    out = {}

    def add(name, v):
        v = v.strip()
        if v and v not in out.values():
            out[name] = v

    bases = {
        "serial": SERIAL,
        "serial_sp": "CL 76841714 A",
        "digits": DIGITS,
        "district": DISTRICT,
        "serial_district": SERIAL + DISTRICT,
    }
    for bn, b in bases.items():
        add(bn, b)
        add(bn + "_rev", b[::-1])
        add(bn + "_rot180", rot180(b))
        add(bn + "_mirror", mirror(b))
        add(bn + "_rev_lower", b[::-1].lower())
        add(bn + "_rot180_nospace", rot180(b).replace(" ", ""))
    # the digits under rotation, keeping ONLY glyphs that legally rotate --
    # a stricter reading than leaving 4 and 7 in place
    strict = "".join(ROT180[c] for c in reversed(DIGITS) if c in ROT180)
    add("digits_rot180_strict", strict)
    # mirrored serial crossed with the article's stated clues
    for tail in ("OVERDOSE", "El Salvador", "Max Keiser", "20 BTC"):
        add(f"revserial_{tail[:6]}", SERIAL[::-1] + " " + tail)
        add(f"{tail[:6]}_revserial", tail + " " + SERIAL[::-1])
        add(f"revdigits_{tail[:6]}", DIGITS[::-1] + " " + tail)
    return out


def sweep(phrases, oracle, batch=60000):
    """Full stack: 7 direct hashes + 5 seed types x HD paths, x 25 scripts.

    BATCHED, and that is not an optimisation detail. Calling the oracle once
    per key costs ~329 ms of fixed setup against a 454 MB memory-mapped prefix
    index -- 13,212 such calls is 72 minutes, and the first version of this
    file was killed by its own timeout a fifth of the way through. Accumulating
    into large batches amortises the setup to ~234 us per scriptPubKey.
    """
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    paths = build_paths()
    hits, n = [], 0
    meta, spks = [], []

    def flush():
        nonlocal meta, spks
        if not spks:
            return
        for j, bal in oracle.check(spks):
            hits.append(meta[j] + (bal,))
            sys.stderr.write(
                f"\n  *** HIT  {bal} sats\n"
                f"      reading    {meta[j][0]} = {meta[j][1]!r}\n"
                f"      derivation {meta[j][2]}\n"
                f"      script     {meta[j][3]}\n")
            sys.stderr.flush()
        meta, spks = [], []

    for i, (name, p) in enumerate(sorted(phrases.items()), 1):
        keys = [(f"d:{h}", k) for h, k in direct_keys(p).items()]
        for sn, seed in seeds_from(p).items():
            for path in paths:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    keys.append((f"{sn}:{path}", k))
        for dn, k in keys:
            if not (0 < int.from_bytes(k, "big") < CURVE_N):
                continue
            for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                meta.append((name, p, dn, st))
                spks.append(spk)
                n += 1
            if len(spks) >= batch:
                flush()
        sys.stderr.write(f"\r  {i}/{len(phrases)} readings  {n:,} scripts  ")
        sys.stderr.flush()
    flush()
    return hits, n


def selftest():
    ok = True
    ok &= rot180("69") == "69" and rot180("18") == "81"
    sys.stderr.write(f"  rot180('69')={rot180('69')!r}, "
                     f"rot180('18')={rot180('18')!r}: "
                     f"{'OK' if rot180('69')=='69' and rot180('18')=='81' else 'FAIL'}\n")
    ok &= mirror("AHI") == "IHA"
    sys.stderr.write(f"  mirror maps self-symmetric glyphs and reverses: "
                     f"{'OK' if mirror('AHI')=='IHA' else 'FAIL'}\n")
    r = readings()
    ok &= r["serial_rev"] == "A41714867LC"
    sys.stderr.write(f"  the classic mirror reading is present: "
                     f"{r.get('serial_rev')} "
                     f"{'OK' if r.get('serial_rev')=='A41714867LC' else 'FAIL'}\n")
    ok &= r["digits_rev"] == "41714867"
    sys.stderr.write(f"  reversed digits: {r.get('digits_rev')} "
                     f"{'OK' if r.get('digits_rev')=='41714867' else 'FAIL'}\n")
    sys.stderr.write(f"  {len(r)} distinct readings\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the mirror operations fail their own checks; refusing")
    if a.selftest:
        return

    import continuous_solver as CS
    orc = CS.IndexOracle()
    if not orc.ready:
        sys.exit(f"no oracle: {orc.why}")

    # POSITIVE CONTROL: plant a key the oracle must find, or the null is void
    sys.stderr.write("\n  POSITIVE CONTROL\n")
    if not orc.control():
        sys.exit("  the oracle cannot find a known-funded address; refusing "
                 "to report a null")
    sys.stderr.write("  the oracle finds a known-funded address: OK\n")

    r = readings()
    sys.stderr.write(f"\n  {len(r)} mirror readings of the serial\n")
    for k, v in sorted(r.items()):
        sys.stderr.write(f"    {k:28} {v!r}\n")
    sys.stderr.write("\n  full stack: 7 direct hashes + 5 seed types x all HD "
                     "paths, into 25 script forms\n")
    hits, n = sweep(r, orc)
    sys.stderr.write(f"\n  {n:,} scriptPubKeys tested, {len(hits)} hit(s)\n")
    if not hits:
        sys.stderr.write(
            "  No mirror reading of the serial derives to a funded address\n"
            "  through any hash, seed type, HD path or script form.\n")


if __name__ == "__main__":
    main()
