#!/usr/bin/env python3
"""
Diff the publisher's own text against our transcript, and sweep what differs.

WHY THIS IS THE HIGHEST-VALUE THING LEFT
Every one of ~150,000,000 derivations in this project assumed
article_transcript.txt is a perfect transcription of the printed page. Exactly
two characters' worth of that assumption has ever been verified against the
scan: the line breaks (83 of 95 at offset zero, against glyph geometry) and the
apostrophe (a straight typewriter U+0027, at 400dpi). Everything else rests on
one human reading a photograph.

And `window/no_digital_footprint.md` establishes that the column's most
distinctive phrases return zero web results — so our transcript may be the only
digital copy in existence, with nothing to check it against.

Unless the publisher's text can be obtained. Bitcoin Magazine publishes print
columns digitally: the Orange Party issue's OVERDOSE column, "Who is The Banana
Republic Now, Biatch?", is on bitcoinmagazine.com, and there is a /print/ path.
If the El Salvador issue's "Bitcoin Is Toxic AF" is there too, that text is
canonical — the publisher's own bytes, not a transcription of a photograph of
them.

`mega_solve.py --families edit1_all` BOUNDS the transcription risk by
enumerating every single-character error. This ELIMINATES it.

This container is egress-blocked from bitcoinmagazine.com, so fetching is the
user's job. This does the rest: takes whatever they save, finds every
difference, and re-derives only the phrases that actually changed — so a
one-character correction costs seconds rather than another full sweep.

  # save the article text or HTML, then:
  python3 transcript_diff.py --selftest
  python3 transcript_diff.py --other publisher.html
"""
import argparse, difflib, html, itertools, re, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


BLOCK_TAGS = ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
              "tr", "section", "article", "blockquote", "pre", "figcaption")


def strip_html(raw):
    """Text out of a saved page, without a parser dependency.

    INLINE tags are removed, not turned into breaks. A first pass replaced
    every tag with a newline, which splits "<b>bitter</b> truth" onto separate
    lines and so manufactures differences that are purely an artifact of the
    publisher's markup — exactly the false positives this tool exists to avoid.
    Only block-level tags become line breaks. The selftest caught this.
    """
    raw = re.sub(r"(?is)<(script|style|nav|header|footer|svg)[^>]*>.*?</\1>",
                 " ", raw)
    raw = re.sub(r"(?is)<!--.*?-->", " ", raw)
    blocks = "|".join(BLOCK_TAGS)
    raw = re.sub(rf"(?is)</?({blocks})\b[^>]*>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", "", raw)          # inline tags: just drop them
    raw = html.unescape(raw)
    lines = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in raw.splitlines()]
    return [l for l in lines if l]


def load_other(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    if "<" in raw[:2000] and ">" in raw[:2000]:
        return strip_html(raw)
    return [l.strip() for l in raw.splitlines() if l.strip()]


def load_ours():
    import article
    lines, _s, _p = article.load()
    return lines


def norm(s):
    """Compare on content, not on whitespace the web renders differently."""
    return re.sub(r"\s+", " ", s).strip()


def align(ours, theirs):
    """Match our lines to the publisher's, tolerating reflow.

    The web version has no line breaks, so a naive line diff is meaningless.
    This joins both into one stream and diffs at WORD level, which is where a
    transcription error actually lives.
    """
    a = norm(" ".join(ours)).split()
    b = norm(" ".join(theirs)).split()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        diffs.append({
            "op": tag,
            "ours": " ".join(a[i1:i2]),
            "theirs": " ".join(b[j1:j2]),
            "context": " ".join(a[max(0, i1 - 6):i1]),
            "after": " ".join(a[i2:i2 + 6]),
        })
    return a, b, diffs, sm.ratio()


def phrases_around(words, theirs_words, diffs, span=12):
    """Candidate phrases built from the publisher's text near each difference.

    Only the neighbourhood matters: a phrase that contains no changed word
    hashes identically in both versions and has already been swept.
    """
    out = set()
    b = theirs_words
    sm = difflib.SequenceMatcher(None, words, b, autojunk=False)
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        lo, hi = max(0, j1 - span), min(len(b), j2 + span)
        seg = b[lo:hi]
        for n in range(2, min(13, len(seg) + 1)):
            for i in range(len(seg) - n + 1):
                p = " ".join(seg[i:i + n])
                out.add(p)
                out.add(p.lower())
    return sorted(out)


def selftest():
    ok = True
    ours = ["Here's the bitter truth. Bitcoin was not a reaction",
            "to the Global Financial Crisis of 2008. It caused it."]
    theirs = ["Here's the bitter truth. Bitcoin was not a reaction to the "
              "Global Financial Crisis of 2008. It caused it."]
    _a, _b, d, r = align(ours, theirs)
    ok &= not d and r == 1.0
    sys.stderr.write(f"  reflowed but identical text -> {len(d)} differences, "
                     f"ratio {r:.3f}: {'OK' if not d else 'FAIL'}\n")

    theirs2 = ["Here's the bitter truth. Bitcoin was not a reaction to the "
               "Global Financial Crisis of 2009. It caused it."]
    _a, b2, d2, _r = align(ours, theirs2)
    ok &= len(d2) == 1 and "2008" in d2[0]["ours"] and "2009" in d2[0]["theirs"]
    sys.stderr.write(f"  one changed word is found: "
                     f"{d2[0]['ours']!r} -> {d2[0]['theirs']!r} "
                     f"{'OK' if len(d2)==1 else 'FAIL'}\n")

    a2 = norm(" ".join(ours)).split()
    cand = phrases_around(a2, b2, d2)
    hit = [p for p in cand if "2009" in p]
    ok &= len(hit) > 5
    sys.stderr.write(f"  {len(cand)} candidate phrases around it, "
                     f"{len(hit)} containing the corrected word: "
                     f"{'OK' if hit else 'FAIL'}\n")
    ok &= all("2008" not in p for p in cand)
    sys.stderr.write(f"  candidates are built from THEIR text, not ours: "
                     f"{'OK' if all('2008' not in p for p in cand) else 'FAIL'}\n")

    t = strip_html("<p>Here&#39;s the <b>bitter</b> truth.</p><script>x</script>")
    ok &= any("bitter truth" in norm(x) for x in t) and not any("x" == x for x in t)
    sys.stderr.write(f"  HTML stripped, entities decoded, scripts dropped: "
                     f"{'OK' if any('bitter truth' in norm(x) for x in t) else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--other", help="the publisher's text or saved HTML")
    ap.add_argument("--max", type=int, default=400000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("diff logic fails its own checks; refusing")
    if a.selftest:
        return
    if not a.other:
        sys.exit("--other is required: save the publisher's article first.\n"
                 "  This container is egress-blocked from bitcoinmagazine.com;\n"
                 "  fetch it on a machine that is not, and pass the file here.")

    ours, theirs = load_ours(), load_other(a.other)
    aw, bw, diffs, ratio = align(ours, theirs)
    sys.stderr.write(
        f"\n  ours    {len(ours):>4} lines, {len(aw):>6,} words\n"
        f"  theirs  {len(theirs):>4} lines, {len(bw):>6,} words\n"
        f"  word-level similarity: {ratio:.4f}\n")

    if ratio < 0.5:
        sys.stderr.write(
            "\n  These do not look like the same article. Check that the file\n"
            "  is the OVERDOSE column from the El Salvador issue ('Bitcoin Is\n"
            "  Toxic AF') and not a different column — OVERDOSE is a recurring\n"
            "  title and the Orange Party issue has its own.\n")
        return

    if not diffs:
        sys.stderr.write(
            "\n  IDENTICAL. The transcript is confirmed against the publisher's\n"
            "  own text, and the transcription-error hypothesis is dead — not\n"
            "  bounded, dead. Every phrase already swept was the right phrase.\n")
        return

    sys.stderr.write(f"\n  {len(diffs)} DIFFERENCE(S)\n")
    for d in diffs:
        sys.stderr.write(f"\n    …{d['context']}  [{d['op'].upper()}]\n"
                         f"      ours   : {d['ours']!r}\n"
                         f"      theirs : {d['theirs']!r}\n"
                         f"      …{d['after']}\n")

    cand = phrases_around(aw, bw, diffs)[:a.max]
    sys.stderr.write(f"\n  {len(cand):,} phrases from THEIR text around the "
                     f"differences.\n  Sweeping only these — a phrase with no "
                     f"changed word hashes the same in\n  both versions and was "
                     f"already covered.\n")

    import continuous_solver as CS
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    meta, spks = [], []
    for p in cand:
        keys = list(direct_keys(p).items())
        for sn, seed in seeds_from(p).items():
            for path in build_paths()[:8]:
                try:
                    k = derive(seed, path)
                except Exception:
                    continue
                if k:
                    keys.append((f"{sn}:{path}", k))
        for dn, k in keys:
            if not (0 < int.from_bytes(k, "big") < CURVE_N):
                continue
            for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                meta.append(f"{p[:70]}|{dn}|{st}")
                spks.append(spk)
    sys.stderr.write(f"  {len(spks):,} scriptPubKeys\n")
    orc = CS.IndexOracle()
    hits = list(orc.check(spks))
    sys.stderr.write(f"\n  INDEX ORACLE [{orc.name}]: {len(hits)} hit(s)\n")
    for j, bal in hits:
        sys.stderr.write(f"    *** {meta[j]}  {bal}\n")
    if not hits:
        sys.stderr.write("    none — the corrections do not unlock anything\n")


if __name__ == "__main__":
    main()
