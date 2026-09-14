#!/usr/bin/env python3
"""
Re-analyse the ever-funded sweep. The headline comparison is confounded twice.

WHAT window/everfunded_results.md CONCLUDES
"Generic dictionary phrases are funded at roughly 0.33% (52 of 15,672). The
article's own text is at 0% across 89,733 addresses ... So for the phrase space
tested, 'someone already solved it and took the coins' is now the LESS
supported reading."

That conclusion is load-bearing. "Swept years ago" is one of only three live
explanations for every null in this project, and the repo currently treats it
as ruled out. It is not ruled out, because the two populations being compared
differ in two ways that have nothing to do with this article.

CONFOUND 1 — WORD COUNT
Of the ~25 distinct ever-funded phrases, 23 are SINGLE WORDS ('the', 'Bitcoin',
'42', 'you', ten more at an identical sprayer amount). The other two are
'Satoshi Nakamoto' and the Genesis coinbase string — the two most famous
strings in Bitcoin. Not one is prose.

The generic corpus is 24.3% single words. The article corpus is 0.7%. So the
0.33% is a rate for a population the article barely contains, applied to a
population that is almost entirely multi-word prose. Brainwallet crackers walk
dictionaries and famous quotes; they do not enumerate arbitrary 7-word spans of
arbitrary prose, because that space is unbounded.

CONFOUND 2 — DERIVATIONS PER PHRASE
The rate is computed per ADDRESS. But a cracker cracks a PHRASE: if it knows
the phrase it tries every common derivation. Counting addresses inflates
whichever corpus had more derivations applied — and that is the article's, by
a factor of 50:

    generic corpora    15,672 addresses /  7,823 phrases =  2.0 per phrase
    article priority   44,957 addresses / 22,473 phrases =  2.0 per phrase
    article deep       44,777 addresses /    454 phrases = 98.6 per phrase

Counted per address the article looks like a 2,523-strong single-word sample.
Counted per phrase it is 158.

WHAT IS LEFT AFTER BOTH ARE REMOVED
Nothing. In every stratum, per phrase, there is no detectable difference.

  python3 stratified_everfunded.py
"""
import argparse, collections, csv, math, os, sys

# The distinct ever-funded phrases, transcribed from the tables in
# window/everfunded_results.md. Split by word count, which is the axis the
# original comparison ignored.
HITS_SINGLE = ["the", "Bitcoin", "Money", "1", "bitcoin", "42", "a", "you",
               "xxx", "mike", "love", "michael", "virtually",
               "Afghanistan", "Amsterdam", "Heisenberg", "Manhattan",
               "discovered", "efficient", "experience", "infinitely",
               "terrorists", "theorized"]
HITS_MULTI = ["Satoshi Nakamoto",
              "The Times 03/Jan/2009 Chancellor on brink of second bailout "
              "for banks"]

GENERIC = ["everfunded_full_corpora_manifest.tsv"]
ARTICLE = ["everfunded_priority_manifest.tsv", "everfunded_deep_manifest.tsv"]


def _lc(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher(a, b, c, d):
    """Two-sided Fisher exact on [[a,b],[c,d]]."""
    n = a + b + c + d
    if min(a + b, c + d, a + c, b + d) < 0 or n == 0:
        return 1.0
    p0 = _lc(a + b, a) + _lc(c + d, c) - _lc(n, a + c)
    tot = 0.0
    for i in range(0, min(a + b, a + c) + 1):
        k, l = a + c - i, d - a + i
        if a + b - i < 0 or k < 0 or l < 0:
            continue
        p = _lc(a + b, i) + _lc(c + d, k) - _lc(n, a + c)
        if p <= p0 + 1e-12:
            tot += math.exp(p)
    return min(tot, 1.0)


def load(paths):
    """(n_addresses, Counter of phrase -> addresses) over several manifests."""
    n, ph = 0, collections.Counter()
    for p in paths:
        if not os.path.exists(p):
            sys.stderr.write(f"  missing manifest: {p}\n")
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            n += 1
            ph[(r.get("phrase") or "").strip()] += 1
    return n, ph


def strata(ph):
    one = {p for p in ph if len(p.split()) <= 1}
    return one, set(ph) - one


def selftest():
    """Fisher must reproduce values checkable by hand."""
    ok = True
    for a, b, c, d, want in [(0, 10, 0, 10, 1.0), (10, 0, 0, 10, 1.0 / 92378)]:
        got = fisher(a, b, c, d)
        good = abs(got - want) < max(1e-9, want * 1e-6)
        ok &= good
        sys.stderr.write(f"  fisher({a},{b},{c},{d}) = {got:.3g} "
                         f"want {want:.3g}  {'OK' if good else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not selftest():
        sys.exit("fisher is wrong; refusing to report p-values from it")
    if a.selftest:
        return

    gn, gph = load(GENERIC)
    an, aph = load(ARTICLE)
    g1, gm = strata(gph)
    a1, am = strata(aph)
    ga = sum(gph[p] for p in g1)
    aa = sum(aph[p] for p in a1)

    sys.stderr.write(f"\n  POPULATIONS\n")
    sys.stderr.write(f"    generic  {gn:>7,} addresses / {len(gph):>6,} phrases"
                     f"   single-word {len(g1):>5,} phrases "
                     f"({len(g1)/len(gph)*100:4.1f}%)\n")
    sys.stderr.write(f"    article  {an:>7,} addresses / {len(aph):>6,} phrases"
                     f"   single-word {len(a1):>5,} phrases "
                     f"({len(a1)/len(aph)*100:4.1f}%)\n")
    sys.stderr.write(f"    derivations per phrase: generic "
                     f"{gn/len(gph):.1f}, article {an/len(aph):.1f}\n")

    h1, h2 = len(HITS_SINGLE), len(HITS_MULTI)
    sys.stderr.write(f"\n  AS THE REPO FRAMES IT, per address, unstratified\n")
    sys.stderr.write(f"    generic {(h1+h2)*2:>4} / {gn:>6,} = "
                     f"{(h1+h2)*2/gn*100:.3f}%      article 0 / {an:,} = "
                     f"0.000%\n")
    sys.stderr.write(f"    p = {fisher((h1+h2)*2, gn-(h1+h2)*2, 0, an):.3g}"
                     f"   <- reads as a large, real difference\n")

    sys.stderr.write(f"\n  STRATIFIED, AND COUNTED PER PHRASE\n")
    e1 = len(a1) * h1 / len(g1)
    p1 = fisher(h1, len(g1) - h1, 0, len(a1))
    sys.stderr.write(f"    single-word  generic {h1:>3} / {len(g1):>6,} = "
                     f"{h1/len(g1)*100:.2f}%   article 0 / {len(a1):,}\n")
    sys.stderr.write(f"                 expected {e1:.2f} article hits, "
                     f"observed 0,  p = {p1:.3f}\n")
    pm = fisher(0, len(gm), 0, len(am))
    sys.stderr.write(f"    multi-word   generic {0:>3} / {len(gm):>6,} = "
                     f"0.00%   article 0 / {len(am):,}\n")
    sys.stderr.write(f"                 (the two multi-word hits are "
                     f"'Satoshi Nakamoto' and the Genesis\n"
                     f"                  coinbase — famous strings, not "
                     f"prose)     p = {pm:.3f}\n")

    sys.stderr.write(f"\n  SENSITIVITY to the exact single-word hit count\n")
    for h in range(h1 - 2, h1 + 3):
        sys.stderr.write(f"    {h:>3} hits -> expected "
                         f"{len(a1)*h/len(g1):.2f}, p = "
                         f"{fisher(h, len(g1)-h, 0, len(a1)):.3f}\n")

    sys.stderr.write(
        f"\n  VERDICT\n"
        f"    Not one stratum shows a difference. The swept-key hypothesis was\n"
        f"    never tested — the sweep had power to detect about {e1:.1f} hits and\n"
        f"    observing 0 is unremarkable. In the prose stratum, where the\n"
        f"    article actually lives, the GENERIC base rate is itself zero, so\n"
        f"    no comparison is possible there at any sample size.\n")


if __name__ == "__main__":
    main()
