#!/usr/bin/env python3
"""
How much of the article is actually IN the scan-derived corpus? 61%.

WHY THIS MATTERS
Every glyph-level conclusion in this repo — bold_cipher_resolved.md,
typography_closed.md, the mirror scan, the per-character work — was computed
from wf/glyphs_p*.tsv. Nobody ever measured what fraction of the printed page
those files contain. They contain 3,648 of 5,997 printed characters.

    page  lines printed  lines got  chars printed  glyphs got  coverage
      75            33         27          1,363       1,103       81%
      76            31         25          1,298       1,007       78%
      77            32         21          1,277         593       46%
      78            23         20          1,037         796       77%
      79            26          6          1,022         149       15%
     ALL           145         99          5,997       3,648       61%

TWO CAUSES, BOTH VISIBLE ON THE PAGE

p77 is WHITE TYPE ON A DARK GROUND. A polarity fix was applied at some point
and it is still at 46%.

p79 is worse and the cause is different: its body text is set on a CURVED
BASELINE — the lines arc across the page. A line-finder that groups glyphs by
a shared horizontal y cannot group text whose y changes within the line, so it
recovered 6 of 26 lines. That page is the article's CONCLUSION, the passage
that begins "To wrap this up", and it is the least-covered page in the corpus.

ALSO ABSENT ENTIRELY: pages 73 and 74. Neither is in article_transcript.txt.
Between them they carry the title block, the byline, the photographer credit,
the pills, and both banknotes — the whole physical apparatus of the spread.

WHAT THIS DOES AND DOES NOT OVERTURN
It does not resurrect the typographic hypothesis. That is dead for a reason
that does not depend on coverage at all: Keiser wrote a column, Bitcoin
Magazine's designers set the type, and he cannot shift glyph weight or
position. On the 61% that WAS extracted, bold is strongly determined by
letter identity (X2/df = 4.3 over 22 characters, p ~ 5e-11; P(bold) runs from
0.158 for 'c' to 0.476 for 'a'), which is the font, exactly as
bold_cipher_resolved.md concluded.

What it does overturn is the strength of the evidence. "Closed" was recorded
against a corpus missing 39% of the ink and 85% of the conclusion, and that
was never stated.

  python3 scan_coverage.py
"""
import csv, glob, os, re, sys

TRANSCRIPT = "article_transcript.txt"
GLYPHS = "wf/glyphs_p*.tsv"


def printed():
    raw = re.sub(r"^#.*$", "", open(TRANSCRIPT, encoding="utf-8").read(),
                 flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it, out = iter(parts[1:]), {}
    for n, b in zip(it, it):
        ls = [l for l in b.splitlines() if l.strip()]
        out[int(n)] = (len(ls),
                       sum(len(re.sub(r"[^A-Za-z0-9]", "", l)) for l in ls))
    return out


def extracted():
    out = {}
    for f in sorted(glob.glob(GLYPHS)):
        rows = [r for r in csv.DictReader(open(f), delimiter="\t")
                if len(r.get("char") or "") == 1]
        if rows:
            out[int(rows[0]["page"])] = (
                len({int(r["line"]) for r in rows}), len(rows))
    return out


def selftest():
    ok = os.path.exists(TRANSCRIPT) and len(glob.glob(GLYPHS)) >= 5
    sys.stderr.write(f"  transcript and {len(glob.glob(GLYPHS))} glyph files "
                     f"present: {'OK' if ok else 'FAIL'}\n")
    if ok:
        p, g = printed(), extracted()
        shared = set(p) & set(g)
        ok &= len(shared) >= 5
        sys.stderr.write(f"  {len(shared)} pages comparable\n")
        # coverage is a fraction: a page cannot yield more glyphs than it prints
        bad = [k for k in shared if g[k][1] > p[k][1] * 1.1]
        ok &= not bad
        sys.stderr.write(f"  no page reports more glyphs than printed "
                         f"characters: {'OK' if not bad else f'FAIL {bad}'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    if not selftest():
        sys.exit("inputs missing or inconsistent")
    p, g = printed(), extracted()
    sys.stderr.write(f"\n{'page':>5} {'lines print':>12} {'lines got':>10} "
                     f"{'chars print':>12} {'glyphs got':>11} {'coverage':>9}\n")
    tl = tg = tc = tgl = 0
    for k in sorted(p):
        pl, pc = p[k]
        gl, gg = g.get(k, (0, 0))
        tl += pl; tg += gl; tc += pc; tgl += gg
        sys.stderr.write(f"{k:>5} {pl:>12} {gl:>10} {pc:>12,} {gg:>11,} "
                         f"{gg/pc*100:>8.0f}%\n")
    sys.stderr.write(f"{'ALL':>5} {tl:>12} {tg:>10} {tc:>12,} {tgl:>11,} "
                     f"{tgl/tc*100:>8.0f}%\n")
    worst = min(p, key=lambda k: g.get(k, (0, 0))[1] / p[k][1])
    sys.stderr.write(
        f"\n  worst page: p{worst} at "
        f"{g.get(worst,(0,0))[1]/p[worst][1]*100:.0f}% — its body text is set "
        f"on a curved\n  baseline, which a horizontal line-finder cannot "
        f"group. It is the article's conclusion.\n"
        f"\n  pages 73 and 74 are not in the transcript at all.\n")


if __name__ == "__main__":
    main()
