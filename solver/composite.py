#!/usr/bin/env python3
"""
"KeyS", plural, in THIS magazine: one fragment per page, combined.

THE READING THIS TESTS
Keiser's only statement about method is "Like George Sand's hidden
cryptography, I have hidden private keyS in the text" -- plural. Every sweep
here has treated that as "there are several independent keys, find any one".

The other reading is that the key is ASSEMBLED: each page carries a fragment
and the fragments concatenate. That is how a setter makes a puzzle that needs
the whole spread rather than one lucky line, and it is why the plural would be
worth saying.

It also fits the constraint the reader is under. Other issues of the magazine
are not obtainable, so a solvable puzzle must be solvable from this one object.
A per-page assembly uses all of it and nothing else.

WHAT IS COMBINED
For each of pages 75-79 (and optionally 72-74), one element of a given KIND is
taken, and the five are concatenated in page order and in reverse:

  first / last highlighted run on the page
  first / last printed line
  the page's first / last word
  the page's largest and smallest numeral
  the page number itself
  the page's all-caps display string

Mixing kinds across pages is deliberately NOT done -- 8 kinds ^ 5 pages is 32k
combinations of mostly-nonsense, and a setter who assembles fragments uses the
same rule on every page. Same-kind assembly is 8 x 2 orders x several joiners,
which is small enough to be exhaustive over what a human would actually build.

THE COVER
The cover is part of this magazine and has never been swept as key material,
only as RNG seeds in serial_entropy. Its printed strings -- the UPC
074820403884, the "2 1>" supplement, $12.99US, "Display Until Feb 23, 2022",
"THE EL SALVADOR ISSUE" -- go through the full stack here.

  python3 composite.py --selftest
  python3 composite.py --out composite.txt
"""
import argparse, itertools, re, sys

COVER = [
    "074820403884", "74820403884", "0748204038842 1", "21",
    "$12.99US", "12.99", "1299", "Display Until Feb 23, 2022",
    "Display Until Feb 23 2022", "20220223", "Feb 23 2022",
    "THE EL SALVADOR ISSUE", "THEELSALVADORISSUE", "EL SALVADOR ISSUE",
    "BITCOIN MAGAZINE", "Bitcoin Magazine El Salvador Issue",
]


def pages():
    """{page: [printed lines]} from the transcript."""
    out, cur = {}, None
    for l in open("article_transcript.txt", encoding="utf-8").read().split("\n"):
        m = re.match(r"=== PAGE (\d+)", l)
        if m:
            cur = int(m.group(1))
            out[cur] = []
            continue
        if l.startswith("#") or cur is None:
            continue
        if l.strip():
            out[cur].append(l.rstrip())
    return out


def highlights():
    out = {}
    try:
        for line in open("highlights_ordered.tsv", encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                out.setdefault(int(p[0]), []).append(p[2])
    except OSError:
        pass
    return out


def elements(pg, hl):
    """{kind: {page: fragment}} -- one fragment per page, per kind."""
    k = {}
    order = sorted(pg)
    k["line_first"] = {p: pg[p][0] for p in order if pg[p]}
    k["line_last"] = {p: pg[p][-1] for p in order if pg[p]}
    k["word_first"] = {p: (pg[p][0].split() or [""])[0] for p in order if pg[p]}
    k["word_last"] = {p: (pg[p][-1].split() or [""])[-1] for p in order if pg[p]}
    k["hl_first"] = {p: hl[p][0] for p in order if hl.get(p)}
    k["hl_last"] = {p: hl[p][-1] for p in order if hl.get(p)}
    k["pageno"] = {p: str(p) for p in order}
    caps = {}
    for p in order:
        c = re.findall(r"\b[A-Z][A-Z0-9' ]{3,}\b", "\n".join(pg[p]))
        if c:
            caps[p] = max(c, key=len).strip()
    k["caps"] = caps
    nums = {}
    for p in order:
        n = re.findall(r"\d[\d,]*", "\n".join(pg[p]))
        if n:
            nums[p] = max(n, key=lambda x: int(x.replace(",", "")))
    k["num_max"] = nums
    return k


def build():
    pg, hl = pages(), highlights()
    ks = elements(pg, hl)
    out = set()
    for kind, d in ks.items():
        seq = [d[p] for p in sorted(d) if d.get(p)]
        if len(seq) < 3:
            continue
        for s in (seq, seq[::-1]):
            for j in ("", " ", "-", ".", "_"):
                out.add(j.join(s))
            out.add("".join(w[0] for w in s if w))          # acrostic of frags
            out.add("".join(w[0].lower() for w in s if w))
            out.add("".join(w[-1] for w in s if w))
    for c in COVER:
        out.add(c)
        out.add(c.upper())
        out.add(c.replace(" ", ""))
        out.add(c[::-1])
    # the cover crossed with the assembled fragments
    base = [x for x in out if 8 < len(x) < 120]
    for c in COVER[:8]:
        for b in base[:60]:
            out.add(f"{c} {b}")
            out.add(f"{b} {c}")
    return sorted(x for x in out if 0 < len(x) < 4000)


def selftest():
    ok = True
    pg = pages()
    ok &= set(pg) == {75, 76, 77, 78, 79}
    sys.stderr.write(f"  pages parsed: {sorted(pg)} "
                     f"{'OK' if set(pg)=={75,76,77,78,79} else 'FAIL'}\n")
    ok &= len(pg[75]) == 33 and len(pg[79]) == 26
    sys.stderr.write(f"  p75 {len(pg[75])} lines, p79 {len(pg[79])} lines "
                     f"(printed 33, 26): "
                     f"{'OK' if len(pg[75])==33 and len(pg[79])==26 else 'FAIL'}\n")
    hl = highlights()
    ks = elements(pg, hl)
    ok &= len(ks) >= 8
    sys.stderr.write(f"  {len(ks)} fragment kinds: {sorted(ks)}\n")
    # each kind must give one fragment per page, not several
    for kind, d in ks.items():
        if len(d) > 5:
            ok = False
            sys.stderr.write(f"  {kind} has {len(d)} entries for 5 pages: FAIL\n")
    sys.stderr.write(f"  every kind yields at most one fragment per page: "
                     f"{'OK' if ok else 'FAIL'}\n")
    ex = " ".join(ks["word_first"][p] for p in sorted(ks["word_first"]))
    sys.stderr.write(f"  e.g. first word of each page: {ex!r}\n")
    c = build()
    ok &= len(c) > 300
    sys.stderr.write(f"  {len(c):,} candidates\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="composite.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("fragment assembly is wrong; refusing")
    if a.selftest:
        return
    c = build()
    open(a.out, "w", encoding="utf-8").write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c):,} candidates -> {a.out}\n")


if __name__ == "__main__":
    main()
