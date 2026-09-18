#!/usr/bin/env python3
"""
Run the Issue-24 device battery on ANOTHER Keiser column: the control test.

WHY  Keiser said "hidden private keyS in the text ... my column" when OVERDOSE
was a serial column (Issues 24, 27, 30 ...). If he embeds keys in his columns
by a textual device, the device should show on a sibling column too -- and two
of them exist as canonical digital text ("Buy Love, Sell Fear", Withdrawal
Issue #30, bitcoinmagazine.com/print/buy-love-sell-fear-bitcoin-magazine-
withdrawal-issue; "Bitcoin Is A Mirror That Reveals All", Inscription Issue,
also on nasdaq.com). Both are egress-blocked from the solver's container, so:
save the article as plain text (paragraphs separated by blank lines, line
breaks as printed if you have the print edition) and run this.

WHAT IT TESTS, per unit of the text (paragraphs, sentences, printed lines,
whole text) and per device:
  brainwallet    7 direct hashes x 25 script forms, plus 5 seed types x 72 HD
                 paths, for every paragraph / sentence / line / the whole text
  n-grams        2..8-word windows (direct hashes)
  Sand           alternate lines / sentences / paragraphs, both offsets
  Musset         first word and last word per line / sentence / paragraph;
                 initials and finals (acrostic / telestich)
  mirror         each unit character-reversed; word-reversed
  BIP-39         first / last wordlist word per unit and all wordlist words in
                 order, every 12-24 word window, checksum-tested vs chance
  WIF            any flattened string that is a checksum-valid WIF
Controls: the index's genesis control and a planted brainwallet through the
same code path. A hit prints immediately and lands in control_corpus_hits.tsv.

  python3 control_corpus.py --selftest
  python3 control_corpus.py --text buy_love_sell_fear.txt
"""
import argparse, hashlib, re, sys

def load_text(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", " ".join(paras)) if s.strip()]
    return lines, sents, paras

def generators(lines, sents, paras, ngram_max=8):
    """(plain_units, ngrams, mnemonic_candidates) as (tag, value) lists."""
    from mnemonic import Mnemonic
    WL = set(Mnemonic("english").wordlist)
    clean = lambda w: re.sub(r"[^A-Za-z]", "", w)
    words = " ".join(paras).split()
    plain, grams, mn = [], [], []
    def add(t, v):
        v = (v or "").strip()
        if v: plain.append((t, v))
    def variants(t, v):
        add(t, v)
        if v != v.lower(): add(t + "/lower", v.lower())
        ns = re.sub(r"\s+", "", v)
        if ns != v: add(t + "/nospace", ns)
    units = {"para": paras, "sent": sents, "line": lines}
    for un, U in units.items():
        for i, u in enumerate(U):
            variants(f"{un}{i}", u)
            add(f"{un}{i}/rev", u[::-1])
            add(f"{un}{i}/wordrev", " ".join(w[::-1] for w in u.split()))
        for off in (0, 1):
            variants(f"sand/{un}/alt{off}", " ".join(U[off::2]))
        variants(f"musset/{un}/first", " ".join(u.split()[0] for u in U if u.split()))
        variants(f"musset/{un}/last", " ".join(u.split()[-1] for u in U if u.split()))
        variants(f"acro/{un}/initials", "".join(u[0] for u in U if u))
        variants(f"acro/{un}/finals", "".join(clean(u.split()[-1])[-1:] for u in U if u.split()))
        add(f"{un}/reversed_order", " ".join(reversed(U)))
    whole = " ".join(paras)
    variants("whole", whole); add("whole/rev", whole[::-1]); add("whole/alpha_lower", re.sub(r"[^a-z]", "", whole.lower()))
    for n in range(2, ngram_max + 1):
        for i in range(len(words) - n + 1):
            grams.append((f"ng{n}@{i}", " ".join(words[i:i + n])))
    def picked(U, which):
        res = []
        for u in U:
            ws = [clean(w).lower() for w in u.split()]; ws = [w for w in ws if w in WL]
            if ws: res.append(ws[0] if which == "first" else ws[-1])
        return res
    seqs = {f"{un}/{wh}": picked(U, wh) for un, U in units.items() for wh in ("first", "last")}
    seqs["all_in_order"] = [clean(w).lower() for w in words if clean(w).lower() in WL]
    for sn, ws in seqs.items():
        for k in (12, 15, 18, 21, 24):
            for i in range(len(ws) - k + 1):
                mn.append((f"bip39/{sn}/w{k}@{i}", "mn:english:" + " ".join(ws[i:i + k])))
    return plain, grams, mn

def selftest():
    import article
    from serial_combine import Sweep, _Fake
    from full_sweep import spks_for_key
    lines, sents, paras = article.load()
    L = [l for l in lines if l.strip()]
    plain, grams, mn = generators(L, list(sents), list(paras))
    ok = len(plain) > 500 and len(grams) > 5000 and len(mn) > 500
    sys.stderr.write(f"  Issue-24 reference: {len(plain):,} plain units, {len(grams):,} n-grams, {len(mn):,} mnemonic windows\n")
    kp = hashlib.sha256(b"control corpus plant").digest()
    spk = dict(spks_for_key(kp))["p2pkh_c"]
    sw = Sweep(_Fake(spk), [], lambda m: None)
    sw.material("plant", "control corpus plant"); sw.flush()
    found = any("plant|sha256|p2pkh_c" in h[0] for h in sw.hits)
    ok &= found
    sys.stderr.write(f"  planted brainwallet found through the sweep path: {'OK' if found else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", help="plain-text file of the column")
    ap.add_argument("--ngram-max", type=int, default=8)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(): sys.exit("setup wrong; refusing")
    if a.selftest or not a.text: return
    import continuous_solver as CS
    from hd_sweep import build_paths
    from serial_combine import Sweep
    log = lambda m: (sys.stderr.write(m), sys.stderr.flush())
    orc = CS.IndexOracle()
    if not orc.ready: sys.exit(f"no oracle: {orc.why}")
    if not orc.control(): sys.exit("positive control failed; a null would be void")
    log(f"  oracle control OK ({orc.name})\n")
    lines, sents, paras = load_text(a.text)
    log(f"  {a.text}: {len(paras)} paragraphs, {len(sents)} sentences, {len(lines)} lines, {len(' '.join(paras).split())} words\n")
    plain, grams, mn = generators(lines, sents, paras, a.ngram_max)
    sw = Sweep(orc, build_paths(), log)
    for i, (t, v) in enumerate(plain, 1):
        sw.material("cc:" + t, v); sw.hd("cc:" + t, v)
        if i % 100 == 0: sw.progress(f"units {i:,}/{len(plain):,}")
    sw.flush(); log("\n")
    for i, (t, v) in enumerate(grams, 1):
        sw.material("cc:" + t, v)
        if i % 2000 == 0: sw.progress(f"n-grams {i:,}/{len(grams):,}")
    sw.flush(); log("\n")
    for t, v in mn: sw.material("cc:" + t, v)
    sw.flush()
    exp = sw.chance()
    log(f"\n  {sw.n:,} scripts from {sw.nkeys:,} keys vs {orc.name}: {len(sw.hits)} index hit(s); "
        f"{sw.certif} checksum-valid WIF; {sw.bip} checksum-valid mnemonic(s) (chance {exp:.1f})\n")
    if sw.hits:
        with open("control_corpus_hits.tsv", "w") as f:
            for t, bal in sw.hits: f.write(f"{bal}\t{t}\n")
        log("  hits -> control_corpus_hits.tsv (re-derive by hand before believing any of them)\n")
    else:
        log("  the device battery finds nothing in this column either: the METHOD, not just Issue 24's text, is null here.\n")

if __name__ == "__main__":
    main()
