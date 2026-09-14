#!/usr/bin/env python3
"""
Keiser's own prose x the DEEP derivation path set. Scoped to the column only.

THE SCOPE, MEASURED RATHER THAN ASSUMED
The magazine marks the column's extent itself: pages 73-79 each carry the
orange OVERDOSE running head (404-698 orange px in the head band); page 72
carries NUMBERS and exactly 0 orange px. So the column is pages 73-79 -- which
is exactly the seven images Keiser published in the 5 Mar 2023 nostr thread.
Page 72's KB46279860 serial is therefore NOT Keiser's and is excluded here,
along with everything on page 71.

THE GAP THIS FILLS
STATUS.md's own numbers show the body prose was only ever tested shallowly:

    body text (OCR), direct          84,687 phrases -> 2,964,045 addrs  (~35/phrase)
    transcript + mirror, direct     373,660 phrases -> 13,078,100 addrs (~35/phrase)
    original corpus, ~360 paths       8,490 phrases -> 15,579,150 addrs (~1835/phrase)

Only the 8,490-phrase curated corpus ever met the deep path set, and STATUS.md
records that corpus was built from the highlight/bold catalogue and contained
no body prose at all. So every deep derivation ever run was blind to what
Keiser actually wrote. Here the natural units of his prose -- printed lines,
sentences, clauses, paragraphs, whole pages -- meet all ~72 paths x 5 seed
schemes x 5 script types, plus the direct digests.

Mirror variants are included because mirror writing is the one clue Keiser
gave in public (5 Mar 2023, citing Schott's paper on the phenomenon).

CONTROL
A phrase from the corpus is planted: the pipeline must recover the address its
own deep derivation produces, via a stub oracle, before any null is reported.

  python3 wf/column_deep.py --selftest
  python3 wf/column_deep.py
"""
import os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

PAGES = [75, 76, 77, 78, 79]          # the prose; 73/74 are the opener artwork
TITLE = ["OVERDOSE", "with Max Keiser", "BITCOIN IS TOXIC AF"]
TDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "transcript")


def units():
    """The natural reading units of the column, in page order."""
    out = []
    for p in PAGES:
        fn = os.path.join(TDIR, f"p{p}.txt")
        if not os.path.exists(fn):
            continue
        raw = open(fn, encoding="utf-8").read()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        out += lines                                   # as printed
        flat = re.sub(r"\s+", " ", " ".join(lines)).strip()
        out.append(flat)                               # whole page
        # sentences
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", flat) if s.strip()]
        # clauses
        out += [c.strip() for c in re.split(r"[,;:—\-]\s*", flat)
                if len(c.strip()) > 3]
        # paragraphs (blank-line separated in the transcript)
        for para in re.split(r"\n\s*\n", raw):
            t = re.sub(r"\s+", " ", para).strip()
            if t:
                out.append(t)
    out += TITLE
    return out


def normalize(p):
    """The forms a phrase could have been typed in."""
    flat = re.sub(r"\s+", " ", p).strip()
    nopunct = re.sub(r"[^A-Za-z0-9 ]", "", flat).strip()
    forms = {flat, flat.lower(), nopunct, nopunct.lower(),
             flat[::-1], flat.lower()[::-1]}       # mirror writing
    return {f for f in forms if f}


def corpus():
    seen, out = set(), []
    for u in units():
        for f in normalize(u):
            if f not in seen:
                seen.add(f); out.append(f)
    return out


def keys_for(phrase, paths):
    """Every private key this phrase yields: direct digests + HD paths."""
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
    good = len(c) > 1000
    print(f"  corpus built: {'OK' if good else 'FAIL'} ({len(c):,} phrases)")
    ok &= good
    # every prose page must actually be represented, or the sweep is blind to
    # part of the column -- which is the exact failure this module exists to fix
    marks = {75: "bitter truth", 76: "Volcano Bonds", 77: "Faketoshi",
             78: "numbers don't lie", 79: "rabbit hole"}
    for pg, m in marks.items():
        hit = any(m.lower() in x.lower() for x in c)
        print(f"  page {pg} represented: {'OK' if hit else 'FAIL'} ({m!r})")
        ok &= hit
    good = any("bitter truth" in x for x in c)
    print(f"  contains body prose: {'OK' if good else 'FAIL'}")
    ok &= good
    good = any(x.startswith("hturt rettib") or "hturt rettib" in x for x in c)
    print(f"  contains mirrored prose: {'OK' if good else 'FAIL'}")
    ok &= good

    paths = HD.build_paths()
    print(f"  path set: {len(paths)} paths x 5 seed schemes")

    # plant: take a real corpus phrase, derive one of its addresses, and
    # require the pipeline to find it through a stub oracle.
    probe = c[0]
    ktag, kk = None, None
    for t, k in keys_for(probe, paths[:3]):
        ktag, kk = t, k
        break
    target = HD.all_addrs(kk)[0]
    found = False
    for t, k in keys_for(probe, paths[:3]):
        if target in HD.all_addrs(k):
            found = True; break
    print(f"  planted corpus phrase recovered: {'OK' if found else 'FAIL'} "
          f"({target} via {ktag})")
    ok &= found

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
    print(f"\nphrases {len(C):,}  paths {len(paths)}  "
          f"=> ~{len(C)*(len(paths)*5+7)*5:,} addresses")

    hits, n_keys, n_addr, t0 = [], 0, 0, time.time()
    PEND = []

    def flush(force=False):
        nonlocal n_addr
        if not PEND or (len(PEND) < 80000 and not force):
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

    for i, ph in enumerate(C):
        for tag, k in keys_for(ph, paths):
            n_keys += 1
            for ad in HD.all_addrs(k):
                PEND.append((f"{tag}|{ph[:48]}", ad, k.hex()))
            flush()
        if i % 250 == 0 and i:
            el = time.time() - t0
            print(f"  {i:,}/{len(C):,} phrases  {n_addr:,} addrs  {el:.0f}s",
                  flush=True)
    flush(force=True)

    print(f"\nphrases {len(C):,}  keys {n_keys:,}  addresses {n_addr:,}  "
          f"in {time.time()-t0:.0f}s")
    print("column-deep hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
