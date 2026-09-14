#!/usr/bin/env python3
"""
Mirror writing applied at EVERY structural level, not just to the raw string.

WHY
Mirror writing is the only method clue Keiser ever gave (X, 5 Mar 2023, citing
Schott PMC2117809), and the column demonstrates it physically: the SAME $100
note appears un-mirrored on page 74 (CL 76841714 A, L12) and mirror-written on
page 73, where DOLLARS reads SRAJJOD, 100 reads OOI and the serial reads
A41714867LC -- exactly CL76841714A reversed.

Prior mirror work reversed the character string. But "mirror" is ambiguous
about its UNIT, and each choice yields a DIFFERENT string:

    chars   reverse every character            (what was already done)
    words   reverse word order, chars forward
    lines   reverse line order, lines forward
    sents   reverse sentence order
    pages   reverse page order, pages forward
    inline  reverse each line in place
    inword  reverse each word in place
    boustro boustrophedon: alternate line direction

Reversing word order is not reversing the string: "a bc" -> "bc a", not "cb a".
Only the first was covered. These are composed pairwise as well, since a mirror
of a mirror is the natural strange-loop reading of the clue.

Applied to the whole column and to each page separately, in several
normalisations, against the deep path set.

  python3 wf/mirror_levels.py --selftest
  python3 wf/mirror_levels.py
"""
import itertools, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDIR = os.path.join(ROOT, "transcript")
PAGES = [75, 76, 77, 78, 79]
SERIAL, SERIAL_M = "CL76841714A", "A41714867LC"


def page_text(p):
    fn = os.path.join(TDIR, f"p{p}.txt")
    return open(fn, encoding="utf-8").read() if os.path.exists(fn) else ""


def lines_of(txt):
    return [l.strip() for l in txt.splitlines() if l.strip()]


# ---------------------------------------------------------------- transforms
def t_chars(txt):
    return txt[::-1]


def t_words(txt):
    return " ".join(txt.split()[::-1])


def t_lines(txt):
    return "\n".join(lines_of(txt)[::-1])


def t_sents(txt):
    flat = re.sub(r"\s+", " ", txt).strip()
    s = [x.strip() for x in re.split(r"(?<=[.!?])\s+", flat) if x.strip()]
    return " ".join(s[::-1])


def t_inline(txt):
    return "\n".join(l[::-1] for l in lines_of(txt))


def t_inword(txt):
    return " ".join(w[::-1] for w in txt.split())


def t_boustro(txt):
    ls = lines_of(txt)
    return "\n".join(l if i % 2 == 0 else l[::-1] for i, l in enumerate(ls))


def t_ident(txt):
    return txt


TRANSFORMS = {"ident": t_ident, "chars": t_chars, "words": t_words,
              "lines": t_lines, "sents": t_sents, "inline": t_inline,
              "inword": t_inword, "boustro": t_boustro}


def column(reverse_pages=False):
    ps = PAGES[::-1] if reverse_pages else PAGES
    return "\n".join(page_text(p) for p in ps)


def normalize(s):
    flat = re.sub(r"\s+", " ", s).strip()
    nop = re.sub(r"[^A-Za-z0-9 ]", "", flat).strip()
    return {flat, flat.lower(), nop, nop.lower(), nop.replace(" ", ""),
            nop.lower().replace(" ", "")}


def corpus():
    out, seen = [], set()

    def add(s):
        for f in normalize(s):
            if f and f not in seen:
                seen.add(f); out.append(f)

    bodies = {"col": column(False), "colrevpages": column(True)}
    for p in PAGES:
        bodies[f"p{p}"] = page_text(p)

    # single transforms, and every composition of two
    for src in bodies.values():
        for n1, f1 in TRANSFORMS.items():
            a = f1(src)
            add(a)
            for n2, f2 in TRANSFORMS.items():
                if n1 == "ident" or n2 == "ident":
                    continue
                add(f2(a))

    # the serial, both ways, as a salt/prefix/suffix on the mirrored column
    mc = re.sub(r"\s+", " ", t_chars(column(False))).strip()
    for s in (SERIAL, SERIAL_M, SERIAL.lower(), SERIAL_M.lower(),
              "76841714", "41714867", SERIAL + "L12", "L12" + SERIAL):
        add(s); add(s + " " + mc[:200]); add(mc[:200] + " " + s)
        add(s + mc[:200]); add(mc[:200] + s)
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
    good = t_words("a bc d") == "d bc a"
    print(f"  word-order reverse != string reverse: {'OK' if good else 'FAIL'} "
          f"({t_words('a bc d')!r} vs {t_chars('a bc d')!r})")
    ok &= good
    good = t_inword("ab cd") == "ba dc"
    print(f"  in-word reverse: {'OK' if good else 'FAIL'}")
    ok &= good
    good = t_lines("x\ny\nz") == "z\ny\nx"
    print(f"  line-order reverse: {'OK' if good else 'FAIL'}")
    ok &= good
    good = t_boustro("ab\ncd\nef") == "ab\ndc\nef"
    print(f"  boustrophedon: {'OK' if good else 'FAIL'}")
    ok &= good
    good = SERIAL[::-1] == SERIAL_M
    print(f"  page-73 mirrored serial == reverse of page-74 serial: "
          f"{'OK' if good else 'FAIL'} ({SERIAL_M})")
    ok &= good
    c = corpus()
    print(f"  corpus: {len(c):,} phrases")
    ok &= len(c) > 200
    # the eight transforms must give eight DISTINCT strings on real text
    src = page_text(75)
    outs = {n: re.sub(r"\s+", " ", f(src)).strip() for n, f in TRANSFORMS.items()}
    good = len(set(outs.values())) == len(outs)
    print(f"  all 8 transforms distinct on p75: {'OK' if good else 'FAIL'} "
          f"({len(set(outs.values()))}/{len(outs)})")
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
    hits, n_addr, t0, PEND = [], 0, time.time(), []

    def flush(force=False):
        nonlocal n_addr
        if not PEND or (len(PEND) < 60000 and not force):
            return
        spks, meta = [], []
        for tag, ad, kh in PEND:
            if o.funded(ad):
                hits.append((tag, ad, kh)); print(f"*** HIT(richlist) {tag} {ad} {kh}", flush=True)
            spk = spk_from_address(ad)
            if spk is not None:
                spks.append(spk); meta.append((tag, ad, kh))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, ad, kh = meta[j]
                hits.append((tag, ad, kh, bal))
                print(f"*** HIT(fullindex) {tag} {ad} {bal/1e8:.8f} BTC {kh}", flush=True)
        n_addr += len(PEND); PEND.clear()

    for ph in C:
        for tag, k in keys_for(ph, paths):
            for ad in HD.all_addrs(k):
                PEND.append((f"{tag}|{ph[:40]}", ad, k.hex()))
            flush()
    flush(force=True)
    print(f"\nphrases {len(C):,}  addresses {n_addr:,} in {time.time()-t0:.0f}s")
    print("mirror-level hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
