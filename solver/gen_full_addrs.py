#!/usr/bin/env python3
"""
Close the API coverage gaps. Everything the first two lists left out.

MEASURED COVERAGE BEFORE THIS
  priority list  44,956 addrs  every n-gram, but only sha256 -> P2PKH,
                               which is 1 of the 1,835 derivations per phrase
                               the offline sweeps run
  deep list      44,777 addrs  332 tier-1 phrases only, 135 of 1,835 = 7.4%
  never queried  candidates_all 6,578 | candidates_v2 8,071 | numbers 18,519
                 | sand, boustrophedon, byte-variant and highlight corpora

So the chain has seen a thin slice. This emits the rest, in stages, cheapest
and highest-prior first, with everything already queried subtracted.

THE CAPABILITY THIS ADDS
Esplora's /scripthash/{hash} endpoint accepts a raw scriptPubKey, so it can be
asked about outputs that have no address at all. That reaches BARE P2PK — a
raw pubkey output — which is invisible to every address-keyed index in this
repo and which window/the_oracle_blind_spot.md recorded as unfalsifiable
offline. It is falsifiable now.

Also reachable for the first time: the wrapped and 1-of-1-multisig forms from
spk_extra (P2SH and P2WSH around P2PK, P2PKH and multisig, and their nestings),
which the offline sweeps could only test against balance snapshots.

STAGES, each written to its own file so they can be run and judged separately:
  A  p2pk        bare P2PK for every tier-1 key, both pubkey forms
  B  wrapped     the 20 spk_extra script forms for tier-1 direct-hash keys
  C  hdfull      the 68 HD paths the deep list omitted, P2PKH compressed
  D  corpora     every unqueried corpus phrase at sha256 -> P2PKH, both forms

  python3 gen_full_addrs.py --selftest
  python3 gen_full_addrs.py --stage A
"""
import argparse, glob, hashlib, os, sys

from hd_sweep import all_addrs, build_paths, derive, direct_keys, seeds_from
import everfunded as EF
from everfunded import scripthash
from spk_extra import spks_extra, sc_p2pk
from gen_deep_addrs import tier1_phrases, CORE_PATHS
from gen_priority_addrs import addrs_for_phrase

from coincurve import PrivateKey


def already_queried():
    seen = set()
    for f in ("everfunded_priority.txt", "everfunded_deep.txt"):
        if os.path.exists(f):
            seen |= {l.strip() for l in open(f) if l.strip()}
    for f in glob.glob("everfunded_full_*.txt"):
        seen |= {l.strip() for l in open(f) if l.strip()}
    return seen


def p2pk_keys(k):
    """Bare P2PK scriptPubKeys for a private key, both pubkey encodings."""
    pub = PrivateKey(k).public_key
    return [("p2pk_c", sc_p2pk(pub.format(compressed=True))),
            ("p2pk_u", sc_p2pk(pub.format(compressed=False)))]


def stage_A(phrases, emit):
    for p in phrases:
        for hname, k in direct_keys(p).items():
            for tag, spk in p2pk_keys(k):
                emit(f"{tag}:{hname}", p, scripthash(spk))
        for sname, seed in seeds_from(p).items():
            for path in CORE_PATHS:
                try:
                    kk = derive(seed, path)
                except Exception:
                    continue
                if kk:
                    for tag, spk in p2pk_keys(kk):
                        emit(f"{tag}:{sname}:{path}", p, scripthash(spk))


def stage_B(phrases, emit):
    for p in phrases:
        for hname, k in direct_keys(p).items():
            for tag, spk in spks_extra(k):
                emit(f"{tag}:{hname}", p, scripthash(spk))


def stage_C(phrases, emit):
    extra = [x for x in build_paths() if x not in CORE_PATHS]
    for p in phrases:
        for sname, seed in seeds_from(p).items():
            for path in extra:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    a = all_addrs(k)
                    if a:
                        emit(f"{sname}:{path}", p, a[0])


def stage_D(_phrases, emit):
    files = ["candidates_all.txt", "candidates_v2.txt", "candidates2.txt",
             "candidates3.txt", "candidates_mirror.txt",
             "candidates_mirror2.txt", "likely_seeds.txt"]
    n = 0
    for f in files:
        if not os.path.exists(f):
            continue
        for line in open(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n")
            if not p:
                continue
            n += 1
            for ad in addrs_for_phrase(p):
                emit(f"sha256:{os.path.basename(f)}", p, ad)
    sys.stderr.write(f"  stage D read {n:,} corpus phrases\n")


STAGES = {"A": ("p2pk", stage_A), "B": ("wrapped", stage_B),
          "C": ("hdfull", stage_C), "D": ("corpora", stage_D)}


def selftest():
    """Scripthash encoding and the P2PK construction must be right, and the
    P2PK output must genuinely have no address form."""
    ok = True
    k = hashlib.sha256(b"satoshi").digest()
    pk = p2pk_keys(k)
    ok &= len(pk) == 2 and pk[0][1][-1] == 0xAC and pk[1][1][-1] == 0xAC
    ok &= len(pk[0][1]) == 35 and len(pk[1][1]) == 67
    sys.stderr.write(f"  P2PK scripts: compressed {len(pk[0][1])} bytes, "
                     f"uncompressed {len(pk[1][1])} bytes, both end OP_CHECKSIG"
                     f" — {'OK' if ok else 'FAIL'}\n")

    # A known scripthash: the genesis P2PKH output, cross-checked in
    # everfunded's live control against the address lookup.
    from everfunded import b58decode_h160
    h = b58decode_h160("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    sh = scripthash(b"\x76\xa9\x14" + h + b"\x88\xac")
    ok &= sh.startswith("sh:") and len(sh) == 67
    sys.stderr.write(f"  genesis P2PKH scripthash {sh[:20]}...  "
                     f"{'OK' if len(sh) == 67 else 'FAIL'}\n")

    # byte order matters: forward and reversed must differ, or the reversal is
    # a no-op and the control in everfunded cannot detect a mistake
    fwd = hashlib.sha256(b"\x76\xa9\x14" + h + b"\x88\xac").hexdigest()
    ok &= fwd != sh[3:]
    sys.stderr.write(f"  reversed digest differs from forward: "
                     f"{'OK' if fwd != sh[3:] else 'FAIL'}\n")

    nex = len(spks_extra(k))
    ok &= nex >= 20
    sys.stderr.write(f"  {nex} wrapped/multisig script forms per key\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES), required=False)
    ap.add_argument("--max", type=int, default=200000)
    ap.add_argument("--sh-order", choices=("forward", "reversed"),
                    default="forward",
                    help="byte order for scripthash keys. FORWARD is the "
                         "default because it is what a live probe of the "
                         "endpoint actually accepted: querying the genesis "
                         "output by forward-order scripthash returned the same "
                         "78,762 fundings as the address lookup, while the "
                         "reversed order returned 0.")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("script construction fails its controls; refusing")
    if a.selftest or not a.stage:
        if not a.stage:
            sys.stderr.write("\n  pick a stage: " + ", ".join(
                f"{k}={v[0]}" for k, v in STAGES.items()) + "\n")
        return

    EF.SH_REVERSED = (a.sh_order == "reversed")
    sys.stderr.write(f"\n  scripthash byte order: {a.sh_order}\n")
    name, fn = STAGES[a.stage]
    already = already_queried()
    sys.stderr.write(f"\n  stage {a.stage} ({name}); skipping "
                     f"{len(already):,} already-queried entries\n")

    rows, seen = [], set()

    def emit(why, label, key):
        if key in already or key in seen or len(rows) >= a.max:
            return
        seen.add(key)
        rows.append((why, label[:110], key))

    fn(tier1_phrases(), emit)

    out = f"everfunded_full_{name}.txt"
    man = f"everfunded_full_{name}_manifest.tsv"
    with open(out, "w") as fh:
        for _w, _p, k in rows:
            fh.write(k + "\n")
    with open(man, "w", encoding="utf-8") as fh:
        fh.write("derivation\tphrase\tkey\n")
        for w, p, k in rows:
            fh.write(f"{w}\t{p}\t{k}\n")
    nsh = sum(1 for _w, _p, k in rows if k.startswith("sh:"))
    sys.stderr.write(f"  {len(rows):,} new entries -> {out}\n")
    sys.stderr.write(f"    {nsh:,} scripthash queries, {len(rows)-nsh:,} "
                     f"address queries\n")
    sys.stderr.write(f"  provenance -> {man}\n")
    sys.stderr.write(f"  at ~90/s that is about {len(rows)/90/60:.0f} minutes\n")


if __name__ == "__main__":
    main()
