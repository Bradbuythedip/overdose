#!/usr/bin/env python3
"""
The actual George Sand cipher: full alternate LINES, and a test for it.

WHY THIS WAS MISSING
Keiser named the mechanism himself, in a tweet predating the one this repo has
been working from (x.com/maxkeiser/status/1607378060172460032, Dec 2022):

    "Have you ever picked up a physical copy of @BitcoinMagazine and read my
     column and Like George Sand's hidden cryptography, I have hidden private
     keys in the text."

George Sand's cipher (the apocryphal Sand / Alfred de Musset exchange) is: read
EVERY OTHER LINE, in full, and the alternate lines form a separate message.

This repo's alternating-line work only ever took the FIRST or LAST WORD of
alternate lines (column_cipher.py: first_word_odd, last_word_even, ...). The
full-line reading -- the thing Sand's cipher actually is -- was never generated
and never swept. Verified: the odd-line concatenation appears in none of the
swept corpora.

THE TEST THAT MATTERS
A Sand cipher is not merely "text that contains English words" -- every
alternate-line reading of English prose is that, trivially. What makes it a
cipher is CONTINUITY ACROSS THE JOIN: the setter wrote line 1 to flow
grammatically into line 3. In ordinary prose line 1 flows into line 2, so
skipping a line breaks the grammar at every boundary.

So the discriminator is the boundary score: how English-like is the text
straddling each join, for step-1 (natural) versus step-2 (Sand) readings,
against a line-shuffled null. A real Sand cipher makes step-2 joins score like
step-1 joins. Absent one, step-2 joins score like the shuffled null.

  python3 gen_sand.py --transcript article_transcript.txt --out /tmp/sand.txt
"""
import argparse, random, re, sys

from englishness import TRIGRAMS, letters

NON_BODY = {"bitcoin is toxic af", "max keiser"}


def pages(path, drop_non_body=True):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    out, it = [], iter(parts[1:])
    for num, body in zip(it, it):
        ls = [l.strip() for l in body.splitlines() if l.strip()]
        if drop_non_body:
            ls = [l for l in ls if l.lower() not in NON_BODY]
        out.append((num, ls))
    return out


def boundary_score(lines, step, offset=0, win=12):
    """Trigram density in the text straddling each join of a step-N reading."""
    sel = lines[offset::step]
    if len(sel) < 3:
        return None
    hits = tot = 0
    for a, b in zip(sel, sel[1:]):
        la, lb = letters(a), letters(b)
        if not la or not lb:
            continue
        s = la[-win:] + lb[:win]
        # only trigrams that actually span the join
        lo = max(len(la[-win:]) - 2, 0)
        hi = min(len(la[-win:]) + 2, len(s))
        for i in range(lo, max(hi - 2, lo)):
            if i + 3 <= len(s):
                tot += 1
                if s[i:i + 3] in TRIGRAMS:
                    hits += 1
    return hits / tot if tot else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pg = pages(a.transcript)
    allines = [l for _, ls in pg for l in ls]
    rng = random.Random(20260913)

    sys.stderr.write(f"{len(allines)} body lines across {len(pg)} pages\n\n")
    sys.stderr.write("  BOUNDARY CONTINUITY TEST (trigram density straddling each join)\n")
    nat = boundary_score(allines, 1)
    sys.stderr.write(f"    step 1 (natural reading, real continuity)   {nat:.4f}\n")
    for step in (2, 3, 4):
        for off in range(step):
            v = boundary_score(allines, step, off)
            if v is not None:
                sys.stderr.write(f"    step {step} offset {off} "
                                 f"(Sand-style)                {v:.4f}\n")
    nulls = []
    for _ in range(30):
        sh = allines[:]
        rng.shuffle(sh)
        v = boundary_score(sh, 1)
        if v is not None:
            nulls.append(v)
    m = sum(nulls) / len(nulls)
    sd = (sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1)) ** 0.5
    sys.stderr.write(f"    line-shuffled null                          "
                     f"{m:.4f} +/- {sd:.4f}\n\n")
    s2 = max(v for off in range(2)
             for v in [boundary_score(allines, 2, off)] if v is not None)
    z = (s2 - m) / sd if sd else 0
    znat = (nat - m) / sd if sd else 0
    sys.stderr.write(f"  best step-2 reading is {z:+.1f} sd from the shuffled null; "
                     f"natural reading is {znat:+.1f} sd\n")

    # POWER GUARD. The natural reading is this test's positive control: it has
    # real grammatical continuity by construction. If it does not separate from
    # the line-shuffled null, the metric cannot detect continuity at all and no
    # verdict about a Sand cipher is admissible from it. That happens here
    # because this article's lines break at phrase boundaries, so even true
    # continuity leaves almost no trigram signal straddling a join.
    if znat < 1.0:
        sys.stderr.write(
            "  INCONCLUSIVE - the metric has no power: its own positive control\n"
            "  (the natural reading) scores no better than randomly ordered lines,\n"
            "  so it cannot detect continuity and must not be used to judge the\n"
            "  step-2 readings either way. Judge by reading the output below.\n\n")
    elif z > znat * 0.5:
        sys.stderr.write("  SAND CIPHER PLAUSIBLE: alternate lines join like real prose\n\n")
    else:
        sys.stderr.write("  NO SAND CIPHER: alternate lines join no better than "
                         "randomly ordered lines\n\n")

    # generate the readings regardless, for the passphrase sweep
    out = set()

    def add(s):
        s = s.strip()
        if s and 8 <= len(s) <= 3000:
            out.add(s)
            out.add(s.lower())
            out.add(s.upper())
            out.add(re.sub(r"\s+", "", s))
            out.add(re.sub(r"[^A-Za-z0-9 ]", "", s).strip())

    scopes = [("ALL", allines)] + [(f"p{n}", ls) for n, ls in pg]
    for tag, ls in scopes:
        for step in (2, 3, 4, 5):
            for off in range(step):
                sel = ls[off::step]
                if len(sel) < 3:
                    continue
                add(" ".join(sel))
                add(" ".join(reversed(sel)))
    # also with the non-body lines left in, in case the headline counts
    for tag, ls in [("ALLraw", [l for _, ls in pages(a.transcript, False) for l in ls])]:
        for step in (2, 3):
            for off in range(step):
                add(" ".join(ls[off::step]))

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")
    sys.stderr.write(f"\n{len(out):,} George Sand readings -> {a.out}\n")
    sys.stderr.write("\n  odd-line reading (ALL), first 300 chars:\n    "
                     + " ".join(allines[0::2])[:300] + "\n")
    sys.stderr.write("\n  even-line reading (ALL), first 300 chars:\n    "
                     + " ".join(allines[1::2])[:300] + "\n")


if __name__ == "__main__":
    main()
