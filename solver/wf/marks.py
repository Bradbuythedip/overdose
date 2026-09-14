#!/usr/bin/env python3
"""
The underline / strikethrough channel -- emphasis nobody had catalogued.

WHAT WAS FOUND, AND WHY IT IS NEW
An earlier session concluded no underlines or strikethroughs exist in the
column, measured on 3x-LANCZOS-upscaled crops. LANCZOS manufactures continuous
edges, so that method could not decide the question either way. Measured on the
scanner's own lossless CCITT G4 ink separation at 400 dpi (wf/strikethrough.py,
row-run clustering, with planted-rule and highlight-bar controls), three marks
are unambiguous:

  p75  y=538  2.62 in underline   "They discount stuff in advance."
  p75  y=1766 0.73 in underline   "protocol."
  p76  y=640  3.89 in strikethrough
                    "(and 10years of watching Peter Schiff miss buying bitcoin"

  p78  none.  p73/74/79 hits are the OVERDOSE slab headline, the photograph and
  the barbed-wire graphic.  p77 is printed white on dark brown and has no black
  separation, so it is NOT measurable by this method -- reported, not guessed.

None of these three appears in highlights_ordered.tsv. The curated corpus that
received the deep path set was built from that catalogue, so these phrases have
never been swept at depth in any form.

THE READINGS TESTED
  1. each mark alone, in its written forms and mirrored
  2. the marks concatenated in page order (the null-cipher reading)
  3. underlines only / the struck line only
  4. strikethrough as an INSTRUCTION: the article with that line deleted
  5. the marks folded into the existing highlight sequence, in page order

  python3 wf/marks.py --selftest
  python3 wf/marks.py
"""
import itertools, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDIR = os.path.join(ROOT, "transcript")

UNDERLINED = ["They discount stuff in advance.", "protocol."]
STRUCK = ["(and 10years of watching Peter Schiff miss buying bitcoin"]
MARKS = UNDERLINED + STRUCK                      # page order: 75, 75, 76


def highlight_seq():
    fn = os.path.join(ROOT, "highlights_ordered.tsv")
    out = []
    for line in open(fn, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            out.append(p[2])
    return out


def article(drop_struck=False):
    txt = []
    for p in (75, 76, 77, 78, 79):
        fn = os.path.join(TDIR, f"p{p}.txt")
        if os.path.exists(fn):
            txt.append(open(fn, encoding="utf-8").read())
    s = "\n".join(txt)
    if drop_struck:
        s = s.replace("(and 10years of watching Peter Schiff miss buying bitcoin", "")
    return re.sub(r"\s+", " ", s).strip()


def phrases():
    out = []
    # 1. each mark alone
    out += MARKS
    out += [m.strip("().") for m in MARKS]
    # 2. concatenations in page order, every ordered subset
    for r in (2, 3):
        for combo in itertools.permutations(MARKS, r):
            out.append(" ".join(combo)); out.append("".join(combo))
    # 3. groups
    out.append(" ".join(UNDERLINED)); out.append("".join(UNDERLINED))
    out.append(" ".join(MARKS)); out.append("".join(MARKS))
    # 4. strikethrough as an instruction
    out.append(article(drop_struck=True))
    out.append(article(drop_struck=False))
    # 5. folded into the highlight sequence, in page order
    hs = highlight_seq()
    out.append(" ".join(hs))
    folded = hs[:10] + [UNDERLINED[0], UNDERLINED[1]] + hs[10:18] + STRUCK + hs[18:]
    out.append(" ".join(folded)); out.append("".join(folded))
    # acrostics over the marked set and the folded sequence
    for seq in (MARKS, UNDERLINED, folded):
        out.append("".join(w[0] for w in seq))
        out.append("".join(w[0] for w in seq).lower())
    return out


def normalize(p):
    flat = re.sub(r"\s+", " ", p).strip()
    nop = re.sub(r"[^A-Za-z0-9 ]", "", flat).strip()
    forms = {flat, flat.lower(), nop, nop.lower(),
             flat[::-1], flat.lower()[::-1], nop.replace(" ", ""),
             nop.lower().replace(" ", "")}
    return {f for f in forms if f}


def corpus():
    seen, out = set(), []
    for p in phrases():
        for f in normalize(p):
            if f not in seen:
                seen.add(f); out.append(f)
    return out


def keys_for(phrase, paths):
    for tag, k in HD.direct_keys(phrase).items():
        yield f"direct:{tag}", k
    for sname, seed in HD.seeds_from(phrase).items():
        for path in paths:
            try:
                k = HD.derive(seed, path)
            except Exception:
                continue
            if k:
                yield f"{sname}:{path}", k


def selftest():
    ok = True
    c = corpus()
    print(f"  corpus: {len(c):,} phrases")
    ok &= len(c) > 100
    good = any("discount stuff in advance" in x for x in c)
    print(f"  underline #1 present: {'OK' if good else 'FAIL'}")
    ok &= good
    good = any("Peter Schiff" in x for x in c)
    print(f"  struck line present:  {'OK' if good else 'FAIL'}")
    ok &= good
    a1, a2 = article(True), article(False)
    # whitespace is re-normalised after the deletion, so compare presence, not
    # raw length: the struck line must be gone from one and present in the other,
    # and nothing else may be lost.
    good = (STRUCK[0] not in a1) and (STRUCK[0] in a2) and \
           (len(a2) - len(a1) - len(STRUCK[0])) <= 2
    print(f"  deletion removes exactly the struck line: "
          f"{'OK' if good else 'FAIL'} (delta {len(a2)-len(a1)}, "
          f"line {len(STRUCK[0])})")
    ok &= good
    good = len(highlight_seq()) == 38
    print(f"  highlight catalogue reads 38 spans: "
          f"{'OK' if good else 'FAIL'} ({len(highlight_seq())})")
    ok &= good
    probe = c[0]
    paths = HD.build_paths()
    k = next(keys_for(probe, paths[:2]))[1]
    tgt = HD.all_addrs(k)[0]
    good = any(tgt in HD.all_addrs(kk) for _, kk in keys_for(probe, paths[:2]))
    print(f"  planted phrase recovered: {'OK' if good else 'FAIL'} ({tgt})")
    ok &= good
    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis: {'OK' if g else 'FAIL'}")
    ok &= g
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")
    from index_oracle import spk_from_address
    paths = HD.build_paths()
    C = corpus()
    o = H.Oracle(use_full=False)
    full = H.full_index()
    print(f"\nphrases {len(C):,}  paths {len(paths)}")
    hits, n_addr, t0 = [], 0, time.time()
    PEND = []

    def flush(force=False):
        nonlocal n_addr
        if not PEND or (len(PEND) < 60000 and not force):
            return
        spks, meta = [], []
        for tag, ad, kh in PEND:
            if o.funded(ad):
                hits.append((tag, ad, kh))
                print(f"*** HIT(richlist) {tag} {ad} {kh}", flush=True)
            spk = spk_from_address(ad)
            if spk is not None:
                spks.append(spk); meta.append((tag, ad, kh))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, ad, kh = meta[j]
                hits.append((tag, ad, kh, bal))
                print(f"*** HIT(fullindex) {tag} {ad} {bal/1e8:.8f} BTC {kh}",
                      flush=True)
        n_addr += len(PEND); PEND.clear()

    for ph in C:
        for tag, k in keys_for(ph, paths):
            for ad in HD.all_addrs(k):
                PEND.append((f"{tag}|{ph[:44]}", ad, k.hex()))
            flush()
    flush(force=True)
    print(f"\nphrases {len(C):,}  addresses {n_addr:,} in {time.time()-t0:.0f}s")
    print("marks hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
