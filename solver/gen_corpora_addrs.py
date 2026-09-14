#!/usr/bin/env python3
"""
API list for the corpora that have NEVER touched the chain.

WHY THESE AND WHY NOW
The most principled work in this project — the boustrophedon reading that
applies both of Keiser's clues at once, the George Sand device run on the
AUTHOR's units rather than the designer's line breaks, the byte-level variants
a reader cannot resolve from the page, the printed-numbers trail, the
PMC2117809 pointers — was only ever scored against the two offline BALANCE
indices. Those answer "holds coins today" and "held a large balance in April
2023"; neither answers "was ever funded", which is the question that matters
for a weak key printed in a magazine. So every one of those nulls is still
untested against the oracle that can actually see a swept key.

Corpora are REGENERATED from their committed generators rather than copied out
of scratch, so this file's output is reproducible from the repo alone and each
corpus passes its own selftest before it contributes anything.

THE JUNK FILTER, and why it is not cosmetic
The earlier corpora pass returned 52 ever-funded addresses and every single one
was generic: "the" (5.28 BTC), "Bitcoin", "Money", "1", "42", "a", "you",
"xxx", "Satoshi Nakamoto" in six casings, and ten single words sharing an
identical 0.00005460 dust amount. Not one article-specific phrase. Those hits
came from single letters and bare digits sitting in candidates_*.txt — they
cost queries and teach nothing, because a one-character brainwallet says
nothing about this puzzle. Entries under 4 characters, and anything that is
only digits, are dropped, and the count dropped is printed so the reduction is
visible rather than silent.

  python3 gen_corpora_addrs.py --selftest
  python3 gen_corpora_addrs.py
"""
import argparse, glob, os, re, subprocess, sys, tempfile

from gen_priority_addrs import addrs_for_phrase

# generator -> (extra args, rough expected count) — each writes one phrase file
GENERATORS = [
    ("boustrophedon.py", [], "boustrophedon: both clues at once"),
    ("sentence_cipher.py", [], "Sand on the author's units"),
    ("gen_typographic.py", [], "byte variants: em dashes, wide gaps"),
    ("gen_numbers.py", [], "printed-numbers trail"),
    ("gen_numbers.py", ["--set", "p72"], "page-72 NUMBERS department"),
    ("gen_schott.py", [], "PMC2117809 pointers and Leonardo"),
]

JUNK = re.compile(r"^\d+$")


def keep(p):
    """A phrase worth a network call.

    SINGLE TOKENS ARE DROPPED, and that is not over-filtering. Every hit this
    project has ever recorded from a corpus list was a single common word —
    "the", "Bitcoin", "1", "42", "love", "michael", "virtually" — because every
    single word is in every brainwallet dictionary already, so its funding
    status says nothing about this article. They arrive here by accident: the
    byte-variant expansion replaces an em dash with the empty string, so a
    2-gram like "love —" collapses to "love".

    A single word cannot be the thing Keiser hid either. He said "hidden in the
    text", and a one-word brainwallet is not hidden, it is the first thing any
    cracker tries.
    """
    p = p.strip()
    return (len(p) >= 4 and not JUNK.match(p)
            and len(p.split()) >= 2)


def run_generators(tmpdir):
    """Run each generator into tmpdir; return [(label, path)]."""
    out = []
    for script, extra, label in GENERATORS:
        if not os.path.exists(script):
            sys.stderr.write(f"  MISSING {script}, skipping {label}\n")
            continue
        tag = script.replace(".py", "") + ("_" + extra[-1] if extra else "")
        path = os.path.join(tmpdir, tag + ".txt")
        cmd = [sys.executable, script] + extra + ["--out", path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = os.path.exists(path) and os.path.getsize(path) > 0
        n = sum(1 for _ in open(path)) if ok else 0
        sys.stderr.write(f"  {label:42} {n:>7,} phrases"
                         f"{'' if ok else '   FAILED'}\n")
        if not ok:
            sys.stderr.write("    " + (r.stderr or "").strip()[-300:] + "\n")
            continue
        out.append((label, path))
    return out


def already_queried():
    seen = set()
    for f in glob.glob("everfunded_*.txt"):
        if "manifest" in f:
            continue
        seen |= {l.strip() for l in open(f) if l.strip()}
    return seen


def selftest():
    """Derivation must agree with everfunded.py's embedded control table, and
    the junk filter must cut what it claims to."""
    from everfunded import SWEPT_CONTROLS
    ok = True
    for p, u, c in SWEPT_CONTROLS:
        got = addrs_for_phrase(p)
        good = got == [u, c]
        ok &= good
        sys.stderr.write(f"  {p!r:34} -> {got[0]}  "
                         f"{'OK' if good else 'MISMATCH'}\n")
    cases = [("a", False), ("42", False), ("1", False), ("xxx", False),
             ("the", False), ("Bitcoin", False), ("El Salvador", True),
             ("0000", False),
             # the three that actually produced hits, all single words
             ("love", False), ("michael", False), ("virtually", False),
             ("right there in the Genesis Block.", True)]
    bad = [c for c, want in cases if keep(c) != want]
    ok &= not bad
    sys.stderr.write(f"  junk filter: {len(cases)-len(bad)}/{len(cases)} "
                     f"cases correct{'' if not bad else ' — wrong: ' + str(bad)}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_corpora2.txt")
    ap.add_argument("--manifest", default="everfunded_corpora2_manifest.tsv")
    ap.add_argument("--keep-dir", help="also write the raw phrase files here")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("derivation or filter fails its controls; refusing")
    if a.selftest:
        return

    already = already_queried()
    sys.stderr.write(f"\n  skipping {len(already):,} addresses already queried\n\n")

    tmp = a.keep_dir or tempfile.mkdtemp(prefix="corpora")
    os.makedirs(tmp, exist_ok=True)
    files = run_generators(tmp)

    rows, seen, dropped, total = [], set(), 0, 0
    for label, path in files:
        for line in open(path, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n")
            if not p:
                continue
            total += 1
            if not keep(p):
                dropped += 1
                continue
            for ad in addrs_for_phrase(p):
                if ad in already or ad in seen:
                    continue
                seen.add(ad)
                rows.append((label, p[:110], ad))

    with open(a.out, "w") as fh:
        for _l, _p, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("corpus\tphrase\taddress\n")
        for l, p, ad in rows:
            fh.write(f"{l}\t{p}\t{ad}\n")

    sys.stderr.write(f"\n  {total:,} phrases read, {dropped:,} dropped as junk "
                     f"(under 4 chars or digits only)\n")
    sys.stderr.write(f"  {len(rows):,} NEW addresses -> {a.out}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  at ~120/s that is about {len(rows)/120/60:.0f} minutes\n")


if __name__ == "__main__":
    main()
