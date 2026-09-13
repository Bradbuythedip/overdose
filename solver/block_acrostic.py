#!/usr/bin/env python3
"""
Acrostics over the units a reader could actually see: individual flush blocks.

aligned_blocks.py measures the left and right edge of every printed line. The
result: no page in this article has a full-page flush margin. Edge x wanders by
6-18 character widths (sd 196-712 px against a ~31-40 px glyph), and the
longest flush run on any page is 7 lines.

That bounds the whole family. An acrostic is a visual column device -- the
reader has to SEE letters lining up down an edge. A whole-page or
whole-article acrostic over centred type is not something anyone would notice
or that a setter would hide anything in. The readable unit is the paragraph
-sized flush block, 3-14 lines, which is exactly what the measured runs are.

So this generates acrostics per PARAGRAPH rather than per page, which is the
readable unit and a far smaller, better-motivated candidate set than the
whole-page readings already swept.

Also excludes the two lines a verification agent identified as not being
typeset body text at all, confirmed against the scans:
  "BITCOIN IS TOXIC AF" (p75) -- a display headline, not body type
  "MAX KEISER"          (p79) -- a hand-drawn signature graphic
Any reading that touches them is corpus-invalid.

  python3 block_acrostic.py --transcript article_transcript.txt --out /tmp/blocks.txt
"""
import argparse, re, sys

NON_BODY = {
    "bitcoin is toxic af",      # p75 display headline
    "max keiser",               # p79 hand-drawn signature
}


def blocks(path):
    """Yield (page, index, [lines]) for each paragraph-sized block."""
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    for num, body in zip(it, it):
        cur, k = [], 0
        for line in body.splitlines():
            s = line.rstrip()
            if s.strip():
                if s.strip().lower() in NON_BODY:
                    continue
                cur.append(s.strip())
            else:
                if len(cur) >= 3:
                    k += 1
                    yield num, k, cur
                cur = []
        if len(cur) >= 3:
            k += 1
            yield num, k, cur


def words(s):
    return re.findall(r"[A-Za-z0-9$%'-]+", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    named, nblocks = [], 0
    for page, k, lines in blocks(a.transcript):
        ws = [words(l) for l in lines]
        ws = [w for w in ws if w]
        if len(ws) < 3:
            continue
        nblocks += 1
        tag = f"p{page}b{k}"
        fl = "".join(w[0][0] for w in ws)
        ll = "".join(w[-1][-1] for w in ws)
        fw = " ".join(w[0] for w in ws)
        lw = " ".join(w[-1] for w in ws)
        for nm, s in (("acrostic", fl), ("telestich", ll),
                      ("first_words", fw), ("last_words", lw)):
            named.append((f"{tag}:{nm}", s))
            named.append((f"{tag}:{nm}:rev", s[::-1] if " " not in s
                          else " ".join(reversed(s.split()))))

    # the sequence of per-block acrostics, in reading order -- a reader who
    # spots one block's column would then read the rest
    seq = [s for n, s in named if n.endswith(":acrostic")]
    named.append(("ALLBLOCKS:acrostic_join", "".join(seq)))
    named.append(("ALLBLOCKS:acrostic_initials", "".join(s[0] for s in seq if s)))
    tel = [s for n, s in named if n.endswith(":telestich")]
    named.append(("ALLBLOCKS:telestich_join", "".join(tel)))

    out = set()
    for n, s in named:
        s = s.strip()
        if not s or len(s) > 400:
            continue
        for v in (s, s.lower(), s.upper(), s.title()):
            out.add(v)
        out.add(re.sub(r"\s+", "", s))
        out.add(re.sub(r"\s+", "", s).lower())
    out = {x for x in out if 3 <= len(x) <= 400}

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")

    sys.stderr.write(f"{nblocks} paragraph blocks (non-body lines excluded)\n")
    sys.stderr.write(f"{len(named)} readings -> {len(out):,} phrases -> {a.out}\n\n")
    for n, s in named:
        if n.endswith(":rev"):
            continue
        sys.stderr.write(f"  {n:28} {s[:110]}\n")


if __name__ == "__main__":
    main()
