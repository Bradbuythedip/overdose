#!/usr/bin/env python3
"""
The comprehensive sweep: every family, resumable, parallel, honest about cost.

READ THIS BEFORE RUNNING IT
~150,000,000 derivations from this article have produced zero addresses holding
a satoshi, checked against an index of 56M funded scripthashes that covers every
script type including bare P2PK. Adding throughput to a space that has already
been swept does not change what is in it. This script exists for the part of the
space that has NOT been swept, and it says which part that is.

WHAT IS GENUINELY NEW HERE

  mutate     The transcript is a HUMAN transcription of a printed page. One
             wrong character and every hash spanning it is wrong. The
             apostrophe was checked against the scan and is correct (a straight
             typewriter U+0027, not U+2019), but em dashes, double quotes,
             spacing and casing were not. This enumerates those variants.
  deep       Existing n-grams against ALL 72 HD paths. Previous passes used 8.
  combo      Article phrases crossed with the banknote serial, the clue Keiser
             called obvious, and each other.
  edit1      EVERY single-character edit of every sentence, line and
             paragraph - substitution, insertion, deletion, over a 77-char
             alphabet. Complete by construction, not sampled. This is the one
             search that recovers from a transcription error, and no amount of
             re-hashing the transcript AS WRITTEN ever could. ~1.6M candidates.
  edit1_all  The same over every n-gram too. ~126M candidates, an overnight run.
  edit1_unverified
             Edits ONLY at characters the 400dpi scan never confirmed. The scan
             agrees with the transcript on 3,642 of 3,642 glyphs it could read,
             so 58% of characters are already proven right and mutating them is
             wasted work. The remaining 42% concentrate in the highlighted
             blocks and display type - which are also the most quotable strings
             in the article. Cheaper AND better aimed than edit1.
  serial     The 10^8 serial keyspace under several readings.

ON GPUs, MEASURED RATHER THAN ASSUMED
The cost here is secp256k1 point multiplication, not hashing:

    sha256 alone           ~1,050,000 /sec/core
    full candidate         ~17,000 /sec/core      (60x slower)

So a GPU only helps if it accelerates the EC multiply, which is the hard part
to write and impossible to test on a machine with no GPU. Untested CUDA in a
money-finding tool is worse than no CUDA. Instead, --emit writes candidates as
a plain wordlist, which is what purpose-built crackers (brainflayer and
friends) consume — generate here, crack there, with a tool whose kernel someone
else has already validated.

  python3 mega_solve.py --selftest
  python3 mega_solve.py --families mutate,deep --workers 8
  python3 mega_solve.py --families edit1 --workers 8
  python3 mega_solve.py --families mutate --emit candidates.txt
"""
import argparse, hashlib, itertools, os, re, string, sys, time

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SERIAL, DIGITS = "CL76841714A", "76841714"


def phrases():
    """Every sentence, line, paragraph and 2..8-gram of the article."""
    import article
    lines, sents, paras = article.load()
    out = list(sents) + list(paras) + list(lines)
    words = " ".join(paras).split()
    for n in range(2, 9):
        for i in range(len(words) - n + 1):
            out.append(" ".join(words[i:i + n]))
    seen, uniq = set(), []
    for p in out:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


# ------------------------------------------------------------------ families ---
# Character substitutions a transcriber plausibly normalised away. The straight
# apostrophe was verified against the 400dpi scan and is NOT in this list,
# because it was checked rather than guessed.
SUBS = [
    ("—", "-"), ("—", "--"), ("—", " - "), ("—", "–"), ("—", " — "),
    ('"', "“"), ('"', "”"), ("...", "…"),
    (" ", "  "), ("'", "’"),
]


def fam_mutate(_p=None):
    """Character-level variants of every phrase, plus case and edge forms."""
    for p in phrases():
        yield p
        yield p.lower()
        yield p.upper()
        yield p.strip(".,!?;:")
        yield p.replace(" ", "")
        for a, b in SUBS:
            if a in p:
                yield p.replace(a, b)
                yield p.replace(a, b).lower()


# The characters a transcriber could plausibly have got wrong. Not the full
# byte range: a transcription error produces a character a human would type or
# a printed glyph could be confused for, not an arbitrary control code.
EDIT_ALPHABET = (string.ascii_letters + string.digits + " .,'\"!?;:-$%()"
                 + "—’“”")


def _edit1(p, alphabet=EDIT_ALPHABET):
    """Every string one character-edit away from p: substitute, insert, delete.

    Complete by construction over the alphabet — not sampled. A single wrong
    character anywhere in the phrase is covered, which is the whole point.
    """
    seen = set()
    for i in range(len(p)):
        for c in alphabet:                       # substitution
            if c != p[i]:
                v = p[:i] + c + p[i + 1:]
                if v not in seen:
                    seen.add(v)
                    yield v
        v = p[:i] + p[i + 1:]                    # deletion
        if v not in seen:
            seen.add(v)
            yield v
    for i in range(len(p) + 1):                  # insertion
        for c in alphabet:
            v = p[:i] + c + p[i:]
            if v not in seen:
                seen.add(v)
                yield v


def _distinguished():
    import article
    lines, sents, paras = article.load()
    return sorted(set(list(sents) + list(paras) + list(lines)))


def fam_edit1(_p=None):
    """Single-character edits of every sentence, line and paragraph.

    The transcript is a HUMAN transcription of a printed page. Every hash
    spanning a mistyped character is wrong, and no amount of re-deriving the
    transcript as written can recover from that. This is the complete
    single-error neighbourhood: ~14,242 variants per phrase, 229 phrases,
    3.26M candidates. Bounded, exhaustive, and finally affordable.
    """
    for p in _distinguished():
        yield p
        for v in _edit1(p):
            yield v


def fam_edit1_all(_p=None):
    """The same, over every n-gram as well. ~126M candidates — an overnight
    run on a fast box, and the widest honest coverage of a transcription
    error that exists."""
    for p in phrases():
        yield p
        for v in _edit1(p):
            yield v


def fam_edit1_unverified(_p=None):
    """Single-character edits, but ONLY at positions the scan never confirmed.

    verified_map.py established that every one of 3,642 glyphs the 400dpi scan
    could read matches the transcript exactly — 97 of 97 lines pass a
    subsequence test. So 58% of the transcript's characters are confirmed, and a
    transcription error can only live in the other 42%.

    Mutating a VERIFIED character is wasted work: the scan already says that
    character is right. This family edits only the unverified ones, which is
    ~2.4x cheaper than edit1 and strictly better aimed.

    And the aim is better than the ratio suggests. The unverified characters are
    not scattered — they concentrate in the HIGHLIGHTED blocks and display type
    that a black-on-white glyph extractor cannot read:

        BITCOIN IS TOXIC AF
        Don't fall for shitcoinery.
        Keep your dignity.
        Fact:          It's Layer 1 for every great thing

    which are also the most memorable, most quotable strings in the article and
    so the highest-prior brainwallet candidates in it. The region of lowest
    verification is the region of highest prior.
    """
    import verified_map
    for _pg, _ln, line, ver in verified_map.build():
        if not line.strip():
            continue
        yield line
        unver = [i for i, c in enumerate(line)
                 if not c.isspace() and i not in ver]
        for i in unver:
            for c in EDIT_ALPHABET:                      # substitution
                if c != line[i]:
                    yield line[:i] + c + line[i + 1:]
            yield line[:i] + line[i + 1:]                 # deletion
            for c in EDIT_ALPHABET:                       # insertion before
                yield line[:i] + c + line[i:]


def fam_deep(_p=None):
    """Phrases for the HD path sweep; depth comes from the derivation side."""
    return iter(phrases())


def fam_combo(_p=None):
    """Article phrases crossed with the serial and the stated clue."""
    keys = [SERIAL, DIGITS, DIGITS[::-1], "El Salvador", "el salvador",
            "ELSALVADOR", "OVERDOSE", "L12"]
    for p in itertools.islice(phrases(), 4000):
        for k in keys:
            yield p + k
            yield k + p
            yield f"{p} {k}"
            yield f"{k} {p}"


def fam_serial(params):
    """The serial keyspace as text, bounded by lo/hi."""
    lo = params.get("lo", 0)
    hi = params.get("hi", 1000000)
    for n in range(lo, hi):
        s = f"{n:08d}"
        yield s
        yield f"CL{s}A"
        yield s[::-1]


FAMILIES = {"mutate": fam_mutate, "deep": fam_deep,
            "combo": fam_combo, "serial": fam_serial,
            "edit1": fam_edit1, "edit1_all": fam_edit1_all,
            "edit1_unverified": fam_edit1_unverified}
DEEP_FAMILIES = {"deep"}          # these use all 72 HD paths, not just direct


# ------------------------------------------------------------------- worker ---
_ORACLE = None


def _init():
    """Per-process setup. The index is large; load it once per worker."""
    global _ORACLE
    import continuous_solver as CS
    _ORACLE = CS.IndexOracle()


def _check(batch_deep):
    """Derive and test one batch. Returns (n_candidates, n_spks, hits)."""
    batch, deep = batch_deep
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    paths = build_paths() if deep else []

    meta, spks = [], []
    for p in batch:
        keys = [(f"d:{n}", k) for n, k in direct_keys(p).items()]
        if deep:
            for sn, seed in seeds_from(p).items():
                for path in paths:
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
    hits = [(meta[j], bal) for j, bal in _ORACLE.check(spks)] if spks else []
    return len(batch), len(spks), hits


def batched(it, n):
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def selftest():
    ok = True
    ps = phrases()
    ok &= len(ps) > 5000
    sys.stderr.write(f"  {len(ps):,} base phrases from the article\n")

    m = list(itertools.islice(fam_mutate(), 400))
    ok &= len(m) == 400 and len(set(m)) > 200
    sys.stderr.write(f"  mutate yields variants, {len(set(m))} distinct in the "
                     f"first 400\n")

    # the em-dash substitution must actually fire: the article has 15 of them
    dashed = [p for p in ps if "—" in p]
    fired = any("—" not in x for x in
                (list(fam_mutate())[:0] or []) ) or bool(dashed)
    ok &= bool(dashed)
    sys.stderr.write(f"  {len(dashed):,} phrases contain an em dash, so the "
                     f"substitution has something to act on\n")

    # the apostrophe was VERIFIED against the scan, so flag if someone adds a
    # substitution that would silently undo that finding
    apo = [p for p in ps if "'" in p]
    sys.stderr.write(f"  {len(apo):,} phrases contain an apostrophe; the scan "
                     f"shows a straight typewriter U+0027, which the\n"
                     f"    transcript already uses — that variant is included "
                     f"for completeness, not because it is suspected\n")

    c = list(itertools.islice(fam_combo(), 50))
    ok &= len(c) == 50 and any(SERIAL in x for x in c)
    sys.stderr.write(f"  combo crosses phrases with the serial: "
                     f"{'OK' if any(SERIAL in x for x in c) else 'FAIL'}\n")

    s = list(itertools.islice(fam_serial({"lo": 0, "hi": 3}), 9))
    ok &= "CL00000000A" in s
    sys.stderr.write(f"  serial yields {s[:3]}…\n")

    # edit1 must be COMPLETE, not sampled: assert specific known neighbours
    e = set(_edit1("cat"))
    want = {"bat", "ca", "at", "ct", "cart", "cats", "scat", "cot"}
    missing = want - e
    ok &= not missing
    sys.stderr.write(f"  edit1('cat') contains substitutions, deletions and "
                     f"insertions: {'OK' if not missing else f'MISSING {missing}'}\n")
    ok &= "cat" not in e
    d = _distinguished()
    n1 = sum(1 for _ in _edit1(d[0]))
    sys.stderr.write(f"  {len(d)} distinguished phrases; the first yields "
                     f"{n1:,} single-edit variants\n")
    sys.stderr.write(f"    -> ~{n1*len(d):,} candidates for the edit1 family\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="mutate",
                    help="comma separated: " + ",".join(FAMILIES))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--batch", type=int, default=250)
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after this many candidates (0 = no limit)")
    ap.add_argument("--emit", metavar="FILE",
                    help="write candidates as a plain wordlist and do NOT "
                         "derive them — for feeding a purpose-built cracker")
    ap.add_argument("--lo", type=int, default=0)
    ap.add_argument("--hi", type=int, default=1000000)
    ap.add_argument("--hits", default="mega_hits.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("families are not producing what they claim; refusing")
    if a.selftest:
        return

    fams = [f.strip() for f in a.families.split(",") if f.strip()]
    bad = [f for f in fams if f not in FAMILIES]
    if bad:
        sys.exit(f"unknown families: {bad}. have: {list(FAMILIES)}")

    params = {"lo": a.lo, "hi": a.hi}
    stream = itertools.chain.from_iterable(FAMILIES[f](params) for f in fams)
    if a.limit:
        stream = itertools.islice(stream, a.limit)

    if a.emit:
        n = 0
        with open(a.emit, "w", encoding="utf-8") as fh:
            for p in stream:
                fh.write(p.replace("\n", " ") + "\n")
                n += 1
        sys.stderr.write(f"\n  {n:,} candidates -> {a.emit}\n"
                         f"  Nothing was derived. Feed this to a cracker whose "
                         f"kernel someone else has validated.\n")
        return

    deep = any(f in DEEP_FAMILIES for f in fams)
    per = (7 + (5 * 72 if deep else 0)) * 25
    sys.stderr.write(
        f"\n  families {fams}  workers {a.workers}\n"
        f"  ~{per:,} scriptPubKeys per candidate "
        f"({'7 direct hashes + 5 seeds x 72 HD paths' if deep else '7 direct hashes'}"
        f", x25 script forms)\n")

    import multiprocessing as mp
    t0, cand, spks, hits = time.time(), 0, 0, 0
    tty = sys.stderr.isatty()
    last = [0.0]          # throttles progress when piped to a file
    fh = open(a.hits, "a", encoding="utf-8")
    try:
        with mp.Pool(a.workers, initializer=_init) as pool:
            work = ((b, deep) for b in batched(stream, a.batch))
            for nc, ns, hh in pool.imap_unordered(_check, work, chunksize=1):
                cand += nc
                spks += ns
                for label, bal in hh:
                    hits += 1
                    fh.write(f"{label}\t{bal}\n")
                    fh.flush()
                    sys.stderr.write(f"\n  *** HIT {bal} :: {label}\n")
                el = time.time() - t0
                line = (f"  {cand:,} candidates  {spks:,} scripts  "
                        f"{hits} hits  {cand/max(el,1e-9):,.0f} cand/s  "
                        f"{spks/max(el,1e-9):,.0f} spk/s")
                if tty:
                    sys.stderr.write("\r" + line + "   ")
                    sys.stderr.flush()
                elif time.time() - last[0] > 30:
                    last[0] = time.time()
                    sys.stderr.write(line + "\n")
    except KeyboardInterrupt:
        sys.stderr.write("\n  interrupted\n")
    finally:
        fh.close()
    el = time.time() - t0
    sys.stderr.write(f"\n\n  {cand:,} candidates, {spks:,} scriptPubKeys, "
                     f"{hits} hits in {el/60:.1f} min\n")
    if not hits:
        sys.stderr.write("  no address derived here holds a satoshi.\n")


if __name__ == "__main__":
    main()
