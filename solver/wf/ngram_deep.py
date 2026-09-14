#!/usr/bin/env python3
"""
Every word n-gram of the column x a medium derivation path set.

THE GAP
STATUS.md's table shows the two large prose corpora were only ever swept
"direct":

    body text (OCR), direct        84,687 phrases -> 2,964,045 addrs (~35/phrase)
    transcript + mirror, direct   373,660 phrases -> 13,078,100 addrs (~35/phrase)

while the ~1,835-addresses-per-phrase deep set only ever ran against the 8,490
curated phrases, which contained no prose. wf/column_deep.py closed that for
the column's NATURAL UNITS (lines, sentences, clauses, paragraphs, pages) --
2,864,435 addresses, 0 hits. But a brainwallet phrase need not be a natural
unit: Keiser could have taken any contiguous run of words. That space --
arbitrary n-grams x more than direct digests -- is still open.

Here: every contiguous word n-gram of lengths 1..12 over the column's 1,258
words, in three normalisations including the mirrored form, against a medium
path set (the 20 most plausible HD paths x 5 seed schemes, plus the direct
digests). Medium rather than deep because the phrase count is ~50x larger; this
trades path depth for phrase coverage, which is the axis that was starved.

  python3 wf/ngram_deep.py --selftest
  python3 wf/ngram_deep.py
"""
import os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDIR = os.path.join(ROOT, "transcript")
PAGES = [75, 76, 77, 78, 79]
MAXN = 12

# the 20 paths a 2021 wallet would most plausibly have used
MED_PATHS = ["m", "m/0", "m/0/0", "m/0/1", "m/1/0", "m/0'", "m/0'/0",
             "m/0'/0/0", "m/0'/0'", "m/0'/0'/0'", "m/1", "m/2",
             "m/44'/0'/0'/0/0", "m/44'/0'/0'/0/1", "m/44'/0'/0'/0/2",
             "m/49'/0'/0'/0/0", "m/84'/0'/0'/0/0", "m/84'/0'/0'/0/1",
             "m/86'/0'/0'/0/0", "m/44'/0'/0'"]


def words():
    out = []
    for p in PAGES:
        fn = os.path.join(TDIR, f"p{p}.txt")
        if os.path.exists(fn):
            out += open(fn, encoding="utf-8").read().split()
    return out


def ngrams(ws, maxn=MAXN):
    seen, out = set(), []
    for n in range(1, maxn + 1):
        for i in range(len(ws) - n + 1):
            g = " ".join(ws[i:i + n])
            if g not in seen:
                seen.add(g); out.append(g)
    return out


def forms(g):
    lo = g.lower()
    return (g, lo, lo[::-1])


def keys_for(phrase):
    for tag, k in HD.direct_keys(phrase).items():
        yield f"direct:{tag}", k
    for sname, seed in HD.seeds_from(phrase).items():
        for path in MED_PATHS:
            try:
                k = HD.derive(seed, path)
            except Exception:
                continue
            if k:
                yield f"{sname}:{path}", k


def selftest():
    ok = True
    ws = words()
    good = 1200 < len(ws) < 1400
    print(f"  column words: {'OK' if good else 'FAIL'} ({len(ws)})")
    ok &= good
    g = ngrams(ws)
    print(f"  distinct n-grams (1..{MAXN}): {len(g):,}")
    ok &= len(g) > 10000
    good = "Here's the bitter truth." in g
    print(f"  contains a known 4-gram: {'OK' if good else 'FAIL'}")
    ok &= good
    good = len(list(keys_for("x"))) == 7 + 5 * len(MED_PATHS)
    print(f"  keys per phrase = {7 + 5*len(MED_PATHS)}: "
          f"{'OK' if good else 'FAIL'} ({len(list(keys_for('x')))})")
    ok &= good
    k = HD.direct_keys("correct horse battery staple")["sha256"]
    good = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T" in HD.all_addrs(k)
    print(f"  derivation path: {'OK' if good else 'FAIL'}")
    ok &= good
    # planted: a real n-gram must be recovered end to end
    probe = g[0]
    tgt = HD.all_addrs(next(keys_for(probe))[1])[0]
    good = any(tgt in HD.all_addrs(kk) for _, kk in keys_for(probe))
    print(f"  planted n-gram recovered: {'OK' if good else 'FAIL'} ({tgt})")
    ok &= good
    o = H.Oracle()
    gg = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis: {'OK' if gg else 'FAIL'}")
    ok &= gg
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")
    from index_oracle import spk_from_address
    ws = words()
    G = ngrams(ws)
    o = H.Oracle(use_full=False)
    full = H.full_index()
    kpp = 7 + 5 * len(MED_PATHS)
    print(f"\nn-grams {len(G):,} x 3 forms x {kpp} keys x 5 addrs "
          f"=> ~{len(G)*3*kpp*5:,} addresses")
    hits, n_addr, t0, PEND = [], 0, time.time(), []

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

    for i, g in enumerate(G):
        for ph in forms(g):
            for tag, k in keys_for(ph):
                for ad in HD.all_addrs(k):
                    PEND.append((f"{tag}|{ph[:40]}", ad, k.hex()))
                flush()
        if i % 1000 == 0 and i:
            print(f"  {i:,}/{len(G):,} n-grams  {n_addr:,} addrs  "
                  f"{time.time()-t0:.0f}s", flush=True)
    flush(force=True)
    print(f"\nn-grams {len(G):,}  addresses {n_addr:,} in {time.time()-t0:.0f}s")
    print("ngram-deep hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
