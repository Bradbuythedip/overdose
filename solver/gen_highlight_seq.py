#!/usr/bin/env python3
"""
Sequence-level candidates from the ordered highlight catalogue.

The individual highlighted phrases are already in the corpus. What is not is
what you get by treating the highlights as an ORDERED SEQUENCE -- which is what
a null cipher actually is, and what "encoded in this piece" most naturally
describes. A reader is meant to notice the highlighting and read across it.

Generates, for the full sequence and for each colour subset and each page:
  - concatenation of the runs (space-joined and tight-joined)
  - first letter of each run          (acrostic)
  - first word of each run            (George Sand style null cipher)
  - last word of each run
  - initials of every word in the sequence

  python3 gen_highlight_seq.py --hl highlights_ordered.tsv --out /tmp/hlseq.txt
"""
import argparse, itertools, re, sys


def variants(s):
    s = s.strip()
    if not s or len(s) > 400:
        return []
    out = {s, s.lower(), s.upper(), s.title()}
    nop = re.sub(r"[^\w\s]", "", s)
    out |= {nop, nop.lower(), nop.upper()}
    tight = re.sub(r"\s+", "", s)
    out |= {tight, tight.lower(), tight.upper()}
    out.add(s[::-1])
    out.add(s[::-1].lower())
    return [x for x in out if 3 <= len(x) <= 400]


def derive(runs, tag, out, log):
    """All sequence-level readings of one ordered list of runs."""
    if not runs:
        return
    words_of = [re.findall(r"[A-Za-z0-9'$%-]+", r) for r in runs]
    words_of = [w for w in words_of if w]
    if not words_of:
        return

    joined_sp = " ".join(runs)
    joined_tt = "".join(runs)
    acrostic = "".join(w[0][0] for w in words_of)
    firstw = " ".join(w[0] for w in words_of)
    lastw = " ".join(w[-1] for w in words_of)
    initials = "".join(x[0] for w in words_of for x in w)

    for label, s in (("joined_sp", joined_sp), ("joined_tight", joined_tt),
                     ("acrostic", acrostic), ("first_words", firstw),
                     ("last_words", lastw), ("initials", initials)):
        before = len(out)
        out.update(variants(s))
        if label in ("acrostic", "initials") or len(s) < 90:
            log.append(f"  {tag:22} {label:13} {s[:90]!r}")
        if len(out) == before:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hl", default="highlights_ordered.tsv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for line in open(a.hl, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    if not rows:
        sys.exit("no highlight rows parsed")

    out, log = set(), []
    allruns = [t for _, _, t in rows]
    derive(allruns, "ALL", out, log)

    for col in sorted({c for _, c, _ in rows}):
        derive([t for _, c, t in rows if c == col], f"colour={col}", out, log)

    for pg in sorted({p for p, _, _ in rows}):
        derive([t for p, _, t in rows if p == pg], f"page={pg}", out, log)

    # orange+black together, excluding the page-77 white bars (different device)
    derive([t for _, c, t in rows if c in ("orange", "black")],
           "orange+black", out, log)

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")

    sys.stderr.write(f"{len(rows)} highlight runs\n")
    sys.stderr.write("\n".join(log) + "\n")
    sys.stderr.write(f"\n-> {len(out):,} sequence-level phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
