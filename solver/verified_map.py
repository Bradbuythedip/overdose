#!/usr/bin/env python3
"""
Which transcript characters have been checked against the scan, and which have not.

THE MEASUREMENT
Every glyph the 400dpi scan extracted was tested as a SUBSEQUENCE of its
transcript line — deletions are extraction gaps, anything else would be a
transcription error. 97 lines, 3,642 glyphs, 97 pass, 0 fail. Not one character
the scan could read disagrees with the transcript.

So the transcript is verified over 58% of its non-space characters. A
transcription error, if one exists, can only live in the other 42%.

    page   chars  unverified
      75   1,419         316   22%
      76   1,356         349   26%
      77   1,342         749   56%   <- white type on dark, no 400dpi mask
      78   1,074         278   26%
      79   1,052         903   86%   <- curved baseline defeats line-finding

AND THE UNVERIFIED PART IS NOT RANDOM
The 0%-verified lines are the HIGHLIGHTED blocks and the headline:

    BITCOIN IS TOXIC AF
    terrorists, stock traders,   central bank arsonists,
    Fact:          It's Layer 1 for every great thing
    Don't fall for shitcoinery.
    Keep your dignity.

Knocked-out white-on-colour and bold display type, which a glyph extractor
tuned for black-on-white body text cannot read. Those are also the article's
most memorable, most quotable strings — the highest-prior brainwallet
candidates in the piece.

The region of lowest verification coincides with the region of highest prior.
That makes a targeted edit sweep both better aimed and ~2.4x cheaper than
mutating every character.

  python3 verified_map.py --selftest
  python3 verified_map.py
"""
import argparse, collections, csv, glob, re, sys

TRANSCRIPT = "article_transcript.txt"
GLYPHS = "wf/glyphs_p*.tsv"


def transcript_pages(path=TRANSCRIPT):
    raw = re.sub(r"^#.*$", "", open(path, encoding="utf-8").read(), flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it, out = iter(parts[1:]), {}
    for n, b in zip(it, it):
        out[int(n)] = [l.strip() for l in b.splitlines() if l.strip()]
    return out


def scan_lines(pattern=GLYPHS):
    """page -> line -> the x-ordered string of glyphs the scan read."""
    out = collections.defaultdict(dict)
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f), delimiter="\t"):
            if len(r.get("char") or "") != 1:
                continue
            out[int(r["page"])].setdefault(int(r["line"]), []).append(
                (int(r["x"]), r["char"]))
    for p in out:
        for ln in out[p]:
            out[p][ln] = "".join(c for _x, c in sorted(out[p][ln]))
    return out


def verified_positions(line, scan):
    """Indices of `line` confirmed by `scan`, by greedy subsequence match.

    Greedy is the conservative direction here: it can only ever confirm FEWER
    characters than an optimal alignment would, so the unverified set it
    produces is a superset of the truth. Erring toward "not yet checked" is the
    safe error for a search that is trying not to miss anything.
    """
    idx = [i for i, c in enumerate(line) if not c.isspace()]
    matched, k = set(), 0
    for ch in scan:
        while k < len(idx) and line[idx[k]] != ch:
            k += 1
        if k < len(idx):
            matched.add(idx[k])
            k += 1
    return matched, idx


def build(path=TRANSCRIPT, pattern=GLYPHS):
    """[(page, line_no, text, verified_index_set)] for every transcript line."""
    T, G = transcript_pages(path), scan_lines(pattern)
    out = []
    for pg in sorted(T):
        for i, line in enumerate(T[pg], 1):
            scan = G.get(pg, {}).get(i, "")
            ver, idx = verified_positions(line, scan) if scan else (set(),
                [j for j, c in enumerate(line) if not c.isspace()])
            out.append((pg, i, line, ver))
    return out


def selftest():
    ok = True
    line = "Here's the bitter truth."
    ver, idx = verified_positions(line, "Heresthebitter")
    ok &= len(ver) == 14 and 0 in ver
    sys.stderr.write(f"  a partial scan confirms exactly its own {len(ver)} "
                     f"characters: {'OK' if len(ver)==14 else 'FAIL'}\n")
    ver2, _ = verified_positions(line, "")
    ok &= not ver2
    sys.stderr.write(f"  a line the scan could not read confirms nothing: "
                     f"{'OK' if not ver2 else 'FAIL'}\n")
    # spaces are never "verified" — the glyph stream has none
    ok &= all(not line[i].isspace() for i in ver)
    sys.stderr.write(f"  whitespace is never counted as verified: "
                     f"{'OK' if all(not line[i].isspace() for i in ver) else 'FAIL'}\n")

    rows = build()
    tot = sum(len([c for c in t if not c.isspace()]) for _p, _i, t, _v in rows)
    ver_n = sum(len(v) for _p, _i, _t, v in rows)
    ok &= tot > 5000 and 0 < ver_n < tot
    sys.stderr.write(f"  {len(rows)} transcript lines, {tot:,} characters, "
                     f"{ver_n:,} verified ({ver_n/tot*100:.0f}%)\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="unverified_lines.json",
                    help="write every line carrying an unverified character, "
                         "with the fraction of it the scan confirmed")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("verification map is inconsistent; refusing")
    if a.selftest:
        return

    rows = build()
    per = collections.Counter()
    per_tot = collections.Counter()
    for pg, _i, t, v in rows:
        n = len([c for c in t if not c.isspace()])
        per_tot[pg] += n
        per[pg] += n - len(v)
    tot = sum(per_tot.values())
    unv = sum(per.values())
    sys.stderr.write(f"\n  {tot:,} non-space characters, {tot-unv:,} verified "
                     f"({(tot-unv)/tot*100:.0f}%), {unv:,} never checked\n\n")
    sys.stderr.write(f"  {'page':>5} {'chars':>7} {'unverified':>11} {'%':>5}\n")
    for pg in sorted(per_tot):
        sys.stderr.write(f"  {pg:>5} {per_tot[pg]:>7,} {per[pg]:>11,} "
                         f"{per[pg]/per_tot[pg]*100:>4.0f}%\n")
    zero = [(p, i, t) for p, i, t, v in rows if not v and t.strip()]
    sys.stderr.write(f"\n  {len(zero)} lines the scan could not read at all — "
                     f"mostly highlighted blocks\n  and display type, which is "
                     f"also where the most quotable phrases are:\n")
    for p, i, t in zero[:12]:
        sys.stderr.write(f"    p{p} L{i:<3} {t[:60]}\n")

    if a.json:
        import json
        recs = []
        for pg, i, t, v in rows:
            n = len([c for c in t if not c.isspace()])
            if not n or len(v) == n:
                continue            # fully verified lines are not the target
            recs.append({"page": pg, "line": i, "text": t,
                         "chars": n, "verified": len(v),
                         "verified_frac": len(v) / n})
        recs.sort(key=lambda r: (r["verified_frac"], r["page"], r["line"]))
        json.dump(recs, open(a.json, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        sys.stderr.write(f"\n  {len(recs)} lines carrying an unverified "
                         f"character -> {a.json}\n")


if __name__ == "__main__":
    main()
