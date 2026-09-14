#!/usr/bin/env python3
"""
Delta list after the "10years" transcript correction.

WHAT CHANGED AND WHY IT MATTERS
article_transcript.txt recorded "10 years" where page 76 prints "10years" with
no space, verified on the 400 dpi CCITT-G4 mask and the 600 dpi colour render.
As a word list that space was harmless. As a BRAINWALLET INPUT it was not: every
hash taken over a string spanning that point was computed over a character
stream that does not exist on the page, so those derivations tested the wrong
key and their nulls say nothing about the right one.

WHY A DELTA RATHER THAN A REGENERATION
Regenerating every list would re-query roughly 280,000 addresses that are
already cached and already answered, for no gain: a phrase that does not span
the corrected point hashes identically before and after. Only phrases CONTAINING
that span change. This emits exactly those, minus everything already queried, so
the correction costs a few hundred calls instead of an afternoon.

The affected span is narrow but it sits inside a real sentence, so it appears in
every n-gram window that crosses it — which is why the count is larger than the
one-word change suggests.

  python3 gen_delta_addrs.py --selftest
  python3 gen_delta_addrs.py
"""
import argparse, glob, os, re, sys

from gen_priority_addrs import addrs_for_phrase, load

OLD, NEW = "10 years of watching", "10years of watching"

# There is a SECOND "10 years" in the article, on p79: "Stacy and I have been
# living in here for 10 years." The audit verified only the p76 occurrence
# against the print. The p79 one is therefore NOT assumed correct and NOT
# rewritten in the transcript — instead both spellings of any reading that
# spans it are emitted here, so whichever the page actually shows is covered.
# Silently "fixing" an unverified second site would be exactly the kind of
# normalisation that caused this problem in the first place.


def already_queried():
    seen = set()
    for f in glob.glob("everfunded_*.txt"):
        if "manifest" in f:
            continue
        seen |= {l.strip() for l in open(f) if l.strip()}
    return seen


def affected_phrases():
    """Every reading that spans the corrected point, in BOTH spellings.

    Both, deliberately: the corrected one because it is what the page says, and
    the old one because the previous sweeps only covered it as part of much
    larger lists and a targeted re-check is cheap insurance.
    """
    lines, sents, paras = load()
    out = set()
    for unit in list(sents) + paras + lines:
        if "10years" in unit or "10 years" in unit:
            for form in (unit, unit.lower(),
                         unit.replace("10years", "10 years"),
                         unit.replace("10 years", "10years")):
                out.add(form)
                out.add(form.lower())
    words = " ".join(paras).split()
    idx = [i for i, w in enumerate(words) if "10year" in w or w == "10"]
    for i in idx:
        for n in range(2, 13):
            for st in range(max(0, i - n + 1), i + 1):
                g = " ".join(words[st:st + n])
                if not g:
                    continue
                for form in (g, g.lower(),
                             g.replace("10years", "10 years"),
                             g.replace("10 years", "10years")):
                    out.add(form)
                    out.add(form.lower())
    # Only readings that actually CROSS the corrected point. A window ending at
    # "10" does not span the space and hashes identically either way, so
    # emitting it would spend calls on addresses already answered.
    return {p for p in out if p.strip() and ("10year" in p or "10 year" in p)}


def selftest():
    ok = True
    s = open("article_transcript.txt", encoding="utf-8").read()
    body = "\n".join(l for l in s.splitlines() if not l.startswith("#"))
    has_new = NEW in body
    has_old = OLD in body
    sys.stderr.write(f"  transcript body contains {NEW!r}: {has_new}\n")
    sys.stderr.write(f"  transcript body contains {OLD!r}: {has_old}\n")
    ok &= has_new and not has_old
    ph = affected_phrases()
    spanning = [p for p in ph if "10year" in p or "10 year" in p]
    ok &= len(spanning) == len(ph) and len(ph) > 50
    sys.stderr.write(f"  {len(ph):,} affected phrases, all spanning the "
                     f"correction: {'OK' if ok else 'FAIL'}\n")
    from everfunded import SWEPT_CONTROLS
    for p, u, c in SWEPT_CONTROLS[:1]:
        got = addrs_for_phrase(p)
        ok &= got == [u, c]
        sys.stderr.write(f"  derivation control {p!r}: "
                         f"{'OK' if got == [u, c] else 'MISMATCH'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_delta.txt")
    ap.add_argument("--manifest", default="everfunded_delta_manifest.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("transcript is not in the corrected state; refusing")
    if a.selftest:
        return

    already = already_queried()
    rows, seen = [], set()
    for p in sorted(affected_phrases()):
        for ad in addrs_for_phrase(p):
            if ad in already or ad in seen:
                continue
            seen.add(ad)
            rows.append((p[:110], ad))

    with open(a.out, "w") as fh:
        for _p, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("phrase\taddress\n")
        for p, ad in rows:
            fh.write(f"{p}\t{ad}\n")
    sys.stderr.write(f"\n  {len(rows):,} NEW addresses -> {a.out}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  (everything already queried subtracted: "
                     f"{len(already):,} known)\n")


if __name__ == "__main__":
    main()
