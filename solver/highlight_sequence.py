#!/usr/bin/env python3
"""
The highlight sequence as a null cipher — the one channel Keiser controls.

WHY THIS CHANNEL AND NOT THE OTHERS
The typographic axis was closed here on a structural argument: Keiser wrote a
column, Bitcoin Magazine's designers set the type, so he cannot choose glyph
weight, glyph position, letter spacing or where a highlight box justifies its
contents.

But there is one typographic element an author does control. He marks up his
manuscript, or tells an editor which lines to pull. **Which phrases get
highlighted is his decision**, and the designer merely renders it.

Two facts make that the most interesting remaining space:

  1. `verified_map.py` found the highlighted blocks are the LEAST verified part
     of the article — knocked-out white-on-colour and bold display type that a
     glyph extractor tuned for black-on-white body text cannot read at all.
  2. They are also the most memorable, most quotable strings in the piece, and
     so the highest-prior brainwallet candidates in it.

And `highlights_ordered.tsv` flags this exact gap in its own header:

    "What has not been tried is their ORDERED CONCATENATION, or acrostics taken
     across the sequence -- the classic null-cipher reading, and the one that
     matches 'encoded in this piece' better than any single phrase does."

The individual phrases were catalogued and swept long ago. The SEQUENCE was not.

WHAT IS SWEPT
38 runs in page and reading order — 22 orange, 10 black, 6 white. For the whole
set, for each colour alone, for odd and even positions, and for each page:
ordered concatenation (three joinings), first words, last words, the acrostic
of first letters in three cases and reversed, and the reversed orderings. Each
in three cases. 361 distinct readings.

  python3 highlight_sequence.py --selftest
  python3 highlight_sequence.py
"""
import argparse, re, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PATH = "highlights_ordered.tsv"


def load(path=PATH):
    out = []
    for l in open(path, encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        p = l.rstrip("\n").split("\t")
        if len(p) >= 3:
            out.append((p[0], p[1], p[2]))
    return out


def words(t):
    return re.findall(r"[A-Za-z0-9']+", t)


def subsets(runs):
    d = {"all": runs,
         "orange": [r for r in runs if r[1] == "orange"],
         "black": [r for r in runs if r[1] == "black"],
         "white": [r for r in runs if r[1] == "white"],
         "odd": runs[0::2], "even": runs[1::2]}
    for pg in sorted({r[0] for r in runs}):
        d[f"p{pg}"] = [r for r in runs if r[0] == pg]
    return d


def readings(runs):
    """Every ordered reading of the highlight sequence."""
    out = set()
    for _name, sub in subsets(runs).items():
        if not sub:
            continue
        txts = [r[2] for r in sub]
        fw = [words(t)[0] for t in txts if words(t)]
        lw = [words(t)[-1] for t in txts if words(t)]
        fl = "".join(w[0] for w in fw)
        for s in (" ".join(txts), "".join(txts), "\n".join(txts),
                  " ".join(fw), "".join(fw), " ".join(lw), "".join(lw),
                  fl, fl.lower(), fl.upper(), fl[::-1],
                  " ".join(reversed(txts)), " ".join(reversed(fw))):
            if s.strip():
                out.add(s)
                out.add(s.lower())
                out.add(s.upper())
    return sorted(s for s in out if len(s) < 4000)


def selftest():
    ok = True
    runs = load()
    ok &= len(runs) >= 30
    sys.stderr.write(f"  {len(runs)} highlighted runs "
                     f"({sum(1 for r in runs if r[1]=='orange')} orange, "
                     f"{sum(1 for r in runs if r[1]=='black')} black, "
                     f"{sum(1 for r in runs if r[1]=='white')} white)\n")

    # order is the whole point: a set would destroy the cipher
    ok &= runs[0][2].startswith("They are the sum")
    ok &= runs[-1][2].startswith("We are getting our souls")
    sys.stderr.write(f"  reading order preserved, first -> last: "
                     f"{'OK' if runs[0][2].startswith('They') else 'FAIL'}\n")

    r = readings(runs)
    ok &= len(r) > 200
    sys.stderr.write(f"  {len(r)} distinct readings\n")

    acro = "".join(words(x[2])[0][0] for x in runs if words(x[2]))
    ok &= acro in r or acro.lower() in r
    sys.stderr.write(f"  acrostic present: {acro[:40]}\n")
    # it is not base58, so it cannot be a WIF — worth asserting, not assuming
    b58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    bad = sorted(set(acro) - b58)
    sys.stderr.write(f"  acrostic is not valid base58 (excluded chars "
                     f"{bad}), so it is not a WIF\n")
    ok &= bool(bad)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("highlight sequence is not loading as expected; refusing")
    if a.selftest:
        return

    import continuous_solver as CS
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    from spk_extra import spks_extra

    cands = readings(load())
    sys.stderr.write(f"\n  {len(cands)} readings of the highlight sequence\n")
    keys = []
    for s in cands:
        for hn, k in direct_keys(s).items():
            if 0 < int.from_bytes(k, "big") < CURVE_N:
                keys.append((hn, k))
        for sn, seed in seeds_from(s).items():
            for p in build_paths()[:8]:
                try:
                    kk = derive(seed, p)
                except Exception:
                    continue
                if kk and 0 < int.from_bytes(kk, "big") < CURVE_N:
                    keys.append((f"{sn}:{p}", kk))
    meta, spks = [], []
    for l, k in keys:
        for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
            meta.append(f"{l}|{st}")
            spks.append(spk)
    sys.stderr.write(f"  {len(keys):,} keys -> {len(spks):,} scriptPubKeys\n")
    orc = CS.IndexOracle()
    hits = list(orc.check(spks))
    sys.stderr.write(f"\n  INDEX ORACLE [{orc.name}]: {len(hits)} hit(s)\n")
    for j, bal in hits:
        sys.stderr.write(f"    *** {meta[j]}  {bal}\n")
    if not hits:
        sys.stderr.write("    none — no reading of the highlight sequence "
                         "derives to a funded address\n")


if __name__ == "__main__":
    main()
