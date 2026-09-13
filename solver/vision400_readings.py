#!/usr/bin/env python3
"""
Turn the 400 dpi vision transcription into every reading worth sweeping.

INPUT  scan400/bold_vision_400.json — four pages, per line: text, bold_words,
bar_words, uncertain_words. Produced by eight agents on the lossless 320 dpi
CCITT G4 text masks (four transcribers, four adversarial verifiers), reading
whole words only because sub-word marks track glyph identity, not weight.

WHAT THE DATA ACTUALLY LOOKS LIKE, AND WHY THAT MATTERS
The bold is not interleaved. It comes in CONTIGUOUS RUNS — p78 lines 1-5 are
39 consecutive bold words, p79 lines 11-14 another 27. A Bacon cipher needs a
per-word binary channel that looks roughly balanced at the five-bit scale; a
handful of long blocks carries almost no information no matter how it is
sliced. So the run-length structure is measured here and reported, rather than
feeding Bacon a bit string that cannot hold a key and calling the null result
evidence.

Six readings are emitted:
  bits_bold      whole-word bold as 1
  bits_emph      bold OR inside a highlight bar as 1
  phrase_all     every bold word in reading order
  phrase_iso     ISOLATED bold only — bold words whose run is <= --isolated
                 words long. These are emphasis inside running text, as
                 against display passages set bold wholesale, and they are the
                 ones a null cipher would use.
  phrase_first   first bold word of each run
  phrase_bar     highlight-bar text in reading order

  python3 vision400_readings.py --selftest
  python3 vision400_readings.py --out /tmp/v400
"""
import argparse, itertools, json, os, re, sys

WORD = re.compile(r"[A-Za-z0-9$%'-]+")


def norm(w):
    return WORD.findall(w)[0].lower() if WORD.findall(w) else ""


def mark(line_words, listed):
    """Positions in line_words named by `listed`, matched IN ORDER.

    Set membership is wrong here and quietly corrupts the reading: the agents
    return e.g. bold_words ["They","are","the","sum","of"] for a line that
    also contains two other unbolded "the"s, and a set match would mark all
    three. The lists come back in reading order, so greedy ordered matching
    recovers the actual positions. A word that cannot be matched in order is
    returned as a miss rather than dropped silently.
    """
    hit, i, misses = set(), 0, []
    for w in listed:
        n = norm(w)
        j = i
        while j < len(line_words) and norm(line_words[j]) != n:
            j += 1
        if j < len(line_words):
            hit.add(j)
            i = j + 1
        else:                      # not found from here on — try from the top
            k = next((t for t, lw in enumerate(line_words)
                      if norm(lw) == n and t not in hit), None)
            if k is None:
                misses.append(w)
            else:
                hit.add(k)
    return hit, misses


def load(path, report=None):
    """Yield (page, line_no, word, bold, bar, uncertain) in reading order."""
    pages = json.load(open(path, encoding="utf-8"))["pages"]
    for p in sorted(pages, key=lambda x: x["page"]):
        for ln in p["lines"]:
            lw = WORD.findall(ln["text"])
            b, mb = mark(lw, ln.get("bold_words", []))
            r, mr = mark(lw, ln.get("bar_words", []))
            u, mu = mark(lw, ln.get("uncertain_words", []))
            if report is not None and (mb or mr or mu):
                report.append((p["page"], ln["line_no"], mb + mr + mu))
            for i, w in enumerate(lw):
                yield p["page"], ln["line_no"], w, i in b, i in r, i in u


def runs(flags):
    """Run lengths of the True regions, and each word's own run length."""
    own, rl = [0] * len(flags), []
    i = 0
    while i < len(flags):
        j = i
        while j < len(flags) and flags[j] == flags[i]:
            j += 1
        if flags[i]:
            rl.append(j - i)
            for k in range(i, j):
                own[k] = j - i
        i = j
    return rl, own


def selftest():
    """The run-length machinery must agree with a hand-checked example."""
    f = [0, 1, 1, 1, 0, 0, 1, 0, 1, 1]
    rl, own = runs([bool(x) for x in f])
    ok = rl == [3, 1, 2] and own == [0, 3, 3, 3, 0, 0, 1, 0, 2, 2]
    sys.stderr.write(f"  run lengths {rl} (want [3, 1, 2]): "
                     f"{'OK' if rl == [3, 1, 2] else 'FAIL'}\n")
    sys.stderr.write(f"  per-word own-run {own}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="scan400/bold_vision_400.json")
    ap.add_argument("--out", default="/tmp/v400")
    ap.add_argument("--isolated", type=int, default=6,
                    help="max run length still counted as inline emphasis")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("run-length code is wrong; refusing to emit readings")
    if a.selftest:
        return

    miss = []
    rows = list(load(a.json, report=miss))
    for pg, ln, ws in miss:
        sys.stderr.write(f"  UNMATCHED p{pg} line {ln}: {ws} — the agent named "
                         f"a word its own line text does not contain\n")
    words = [r[2] for r in rows]
    bold = [r[3] for r in rows]
    bar = [r[4] for r in rows]
    unc = [r[5] for r in rows]

    n = len(rows)
    sys.stderr.write(f"\n  {n} words, {sum(bold)} bold ({sum(bold)/n*100:.1f}%), "
                     f"{sum(bar)} in bars, {sum(unc)} uncertain\n")

    rl, own = runs(bold)
    sys.stderr.write(f"  bold runs: {len(rl)}  lengths {sorted(rl, reverse=True)}\n")
    long_ = [x for x in rl if x > a.isolated]
    sys.stderr.write(f"  {len(long_)} runs longer than {a.isolated} words hold "
                     f"{sum(long_)}/{sum(bold)} of all bold words\n")

    # Capacity check BEFORE any Bacon claim. A Bacon cipher needs the bit
    # string to look balanced at the five-bit scale; measure that directly.
    quints = [bold[i:i + 5] for i in range(0, n - 4, 5)]
    allsame = sum(1 for q in quints if len(set(q)) == 1)
    sys.stderr.write(f"  five-bit groups that are uniform (all bold or all "
                     f"regular): {allsame}/{len(quints)} "
                     f"({allsame/max(len(quints),1)*100:.0f}%) — random would "
                     f"be 6%\n")

    def write(name, text):
        p = f"{a.out}_{name}.txt"
        open(p, "w", encoding="utf-8").write(text)
        sys.stderr.write(f"  {name:13} {len(text):6} chars -> {p}\n")

    sys.stderr.write("\n  readings:\n")
    write("bits_bold", "".join("1" if b else "0" for b in bold))
    write("bits_emph", "".join("1" if b or c else "0" for b, c in zip(bold, bar)))
    write("phrase_all", " ".join(w for w, b in zip(words, bold) if b))
    iso = [w for w, b, o in zip(words, bold, own) if b and o <= a.isolated]
    write("phrase_iso", " ".join(iso))
    first = []
    prev = False
    for w, b in zip(words, bold):
        if b and not prev:
            first.append(w)
        prev = b
    write("phrase_first", " ".join(first))
    write("phrase_bar", " ".join(w for w, c in zip(words, bar) if c))

    sys.stderr.write(f"\n  ISOLATED bold ({len(iso)} words), the null-cipher "
                     f"reading:\n    {' '.join(iso)}\n")
    sys.stderr.write(f"\n  first word of each run ({len(first)}):\n    "
                     f"{' '.join(first)}\n")


if __name__ == "__main__":
    main()
