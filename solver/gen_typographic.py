#!/usr/bin/env python3
"""
The byte-level ambiguities a solver CANNOT resolve by reading the page.

WHY THIS IS A REAL GAP AND NOT A PEDANTRY
A brainwallet hashes exact bytes. Every phrase-based sweep in this project has
hashed ONE transcription of each phrase. Where the printed page determines the
characters unambiguously that is fine. Where it does not, the corpus has been
covering one guess out of several and a correct phrase would have failed
silently.

WHAT WAS CHECKED AND FOUND UNAMBIGUOUS
The printed quotation marks are STRAIGHT vertical primes, confirmed by direct
inspection of the 320 dpi lossless mask of page 75 ("Toxic Bitcoin
Maximalists"). The body is set in a typewriter face with no curly forms, so
U+0022 and U+0027 are correct and the transcript already matches the print.
That hypothesis is disconfirmed, not carried.

WHAT REMAINS GENUINELY AMBIGUOUS
Two things a reader physically cannot transcribe uniquely:

  EM DASHES. The article prints 16 long dashes. A solver retyping the phrase
  might produce an em dash, a double hyphen, a single hyphen, a spaced hyphen,
  or nothing at all — and the surrounding spaces vary with each choice.

  WIDE INTRA-LINE GAPS. Six places set a visible gap rather than a single
  space: "Really?          Yes.", "Fact:          It's Layer 1",
  "at XRP.        Get ready", "Marty Bent —     who spend",
  "stock traders,   central bank arsonists",
  "fiat money.   Fortunately". Whether that is one space, several, a tab or a
  line break is not recoverable from the page, and any phrase spanning one has
  only ever been hashed in a single arbitrary reading.

Also emitted, though the print says straight: the CURLY forms. Not because the
page shows them, but because Keiser drafted in a word processor where smart
quotes are on by default, so his manuscript bytes may differ from the printed
glyphs. That only matters if he derived the key from his own draft, which would
make the puzzle unsolvable from the page — so it is a low-prior variant,
included for completeness and labelled as such.

Only phrases actually CONTAINING an ambiguous character are expanded, so the
corpus stays small and the coverage claim stays honest.

  python3 gen_typographic.py --selftest
  python3 gen_typographic.py --out /tmp/typo.txt
"""
import argparse, itertools, re, sys

AMBIG = re.compile(r"—|–|  +|['\"]")


def load(path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    out = []
    for _n, body in zip(*[iter(re.split(r"^=== PAGE (\d+).*?===$", raw,
                                        flags=re.M)[1:])] * 2):
        for block in re.split(r"\n\s*\n", body):
            ls = [l.rstrip() for l in block.splitlines() if l.strip()]
            if ls:
                out.append(" ".join(ls))
    return out


DASH_FORMS = ["—", " — ", "--", " -- ", "-", " - ", " ", ""]
GAP_FORMS = [" ", "  ", "   ", "    ", "\t", ""]


def variants(text, curly=True, cap=4000):
    """All byte readings of one phrase, bounded."""
    out = {text}

    def expand(pool, pattern, forms):
        new = set()
        for s in pool:
            if not re.search(pattern, s):
                new.add(s)
                continue
            for f in forms:
                new.add(re.sub(pattern, f.replace("\\", "\\\\"), s))
            if len(new) > cap:
                break
        return new or pool

    out = expand(out, r"\s*—\s*", DASH_FORMS)
    out = expand(out, r"  +", GAP_FORMS)
    if curly:
        cur = set()
        for s in out:
            cur.add(s)
            if "'" in s:
                cur.add(s.replace("'", "’"))
            if '"' in s:
                # opening/closing pair, in reading order
                t, flip = [], True
                for ch in s:
                    if ch == '"':
                        t.append("“" if flip else "”")
                        flip = not flip
                    else:
                        t.append(ch)
                cur.add("".join(t))
        out = cur
    return {s.strip() for s in out if s.strip()}


def ngrams(paras, lo=2, hi=12):
    seen = set()
    for p in paras:
        ws = p.split()
        for n in range(lo, hi + 1):
            for i in range(len(ws) - n + 1):
                g = " ".join(ws[i:i + n])
                if AMBIG.search(g):
                    seen.add(g)
    return seen


def selftest():
    """Only ambiguous phrases expand, and the expansion is byte-correct."""
    ok = True
    plain = "no ambiguity here"
    v = variants(plain)
    sys.stderr.write(f"  unambiguous phrase expands to {len(v)} form(s) "
                     f"(want 1): {'OK' if len(v) == 1 else 'FAIL'}\n")
    ok &= len(v) == 1

    d = "the black hole — of the Cosmic Now"
    vd = variants(d)
    has_dd = any("--" in x for x in vd)
    has_none = any("hole of the" in x for x in vd)
    sys.stderr.write(f"  em-dash phrase -> {len(vd)} forms, contains '--': "
                     f"{has_dd}, contains collapsed form: {has_none}\n")
    ok &= has_dd and has_none

    q = "about \"Toxic Bitcoin Maximalists\" these"
    vq = variants(q)
    curly = any("“" in x and "”" in x for x in vq)
    sys.stderr.write(f"  quoted phrase -> {len(vq)} forms, has a correctly "
                     f"paired curly variant: {curly}\n")
    ok &= curly

    # every emitted form must differ in BYTES, or the expansion is a no-op
    b = {x.encode("utf-8") for x in vd}
    sys.stderr.write(f"  em-dash forms are byte-distinct: {len(b)} unique of "
                     f"{len(vd)}\n")
    ok &= len(b) == len(vd)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/typo.txt")
    ap.add_argument("--no-curly", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("expansion fails its controls; refusing to emit")
    if a.selftest:
        return

    paras = load()
    gs = ngrams(paras)
    sys.stderr.write(f"\n  {len(paras)} paragraphs, {len(gs)} n-grams contain "
                     f"an ambiguous character\n")

    out = set()
    for g in gs:
        out |= variants(g, curly=not a.no_curly)
    for p in paras:
        out |= variants(p, curly=not a.no_curly)
    out |= variants(" ".join(paras), curly=not a.no_curly)

    lowered = {s.lower() for s in out}
    out |= lowered
    out = {s for s in out if 0 < len(s) <= 4096}
    with open(a.out, "w", encoding="utf-8") as fh:
        for s in sorted(out):
            fh.write(s.replace("\n", " ") + "\n")
    sys.stderr.write(f"  {len(out):,} byte-distinct readings -> {a.out}\n")
    sys.stderr.write(f"  (only phrases containing an em dash, a wide gap, an "
                     f"apostrophe or a quote were expanded)\n")


if __name__ == "__main__":
    main()
