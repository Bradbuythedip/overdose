#!/usr/bin/env python3
"""
Find checksum-valid BIP-39 mnemonics in the article text and HD-derive them.

THE GAP THIS FILLS
------------------
bip39_check.py hardcodes ARTICLE_BIP39_SEQ -- 56 BIP-39 words taken from the
HIGHLIGHT catalogue. The article's 1,254-word body prose was never fed to it,
exactly like the phrase corpus. So "are there valid mnemonics hidden in the
article" has only ever been asked of the highlights.

This runs it over the full accurate transcript, in several extraction modes,
including REVERSED word order -- mirror writing is Keiser's only stated clue,
and a mnemonic read backwards is a natural expression of it.

EXTRACTION MODES
  subseq        every BIP-39 word in reading order, non-BIP-39 words skipped
  subseq_rev    the same sequence reversed
  runs          maximal runs where CONSECUTIVE text words are all BIP-39
  prefix        as subseq, but a text word matches a BIP-39 word if its first
                4 letters uniquely identify one (BIP-39's own abbreviation rule)
  prefix_rev    the same reversed
each also computed per page.

Windows of 12/15/18/21/24 words are checksum-tested; survivors are HD-derived
across the full path set and checked against the offline funded index.

  python3 bip39_sweep.py --selftest
  python3 bip39_sweep.py --transcript article_transcript.txt --out bip39_valid.tsv
"""
import argparse, hashlib, re, sys

from mnemonic import Mnemonic

from hd_sweep import build_paths, derive
from full_sweep import spks_for_key
from index_oracle import Oracle

WORDLIST = Mnemonic("english").wordlist
WORDSET = set(WORDLIST)
LENGTHS = (12, 15, 18, 21, 24)

# 4-letter prefix -> word, only where the prefix is unambiguous (BIP-39
# guarantees the first four letters are unique, so this is a total map)
PREFIX = {}
for w in WORDLIST:
    PREFIX.setdefault(w[:4], []).append(w)
PREFIX = {k: v[0] for k, v in PREFIX.items() if len(v) == 1}


def checksum_ok(words):
    """True if the word list is a checksum-valid BIP-39 mnemonic."""
    n = len(words)
    if n not in LENGTHS:
        return False
    try:
        idx = [WORDLIST.index(w) for w in words]
    except ValueError:
        return False
    bits = "".join(f"{i:011b}" for i in idx)
    ent_len = n * 11 * 32 // 33
    ent, chk = bits[:ent_len], bits[ent_len:]
    eb = int(ent, 2).to_bytes(ent_len // 8, "big")
    want = f"{hashlib.sha256(eb).digest()[0]:08b}"[:len(chk)]
    return chk == want


def page_texts(path):
    """Return [(page, text)] plus ('ALL', whole body)."""
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    out, it = [], iter(parts[1:])
    for num, body in zip(it, it):
        out.append((num, body))
    out.append(("ALL", "\n".join(b for _, b in out)))
    return out


def words_of(text):
    # keep letters only; BIP-39 words are lowercase a-z
    return [w.lower() for w in re.findall(r"[A-Za-z]+", text)]


def extract(text, mode):
    ws = words_of(text)
    if mode.startswith("prefix"):
        seq = []
        for w in ws:
            if w in WORDSET:
                seq.append(w)
            elif len(w) >= 4 and w[:4] in PREFIX:
                seq.append(PREFIX[w[:4]])
        return seq[::-1] if mode.endswith("_rev") else seq
    if mode == "runs":
        runs, cur = [], []
        for w in ws:
            if w in WORDSET:
                cur.append(w)
            else:
                if len(cur) >= 12:
                    runs.append(cur)
                cur = []
        if len(cur) >= 12:
            runs.append(cur)
        return runs                      # list of lists
    seq = [w for w in ws if w in WORDSET]
    return seq[::-1] if mode.endswith("_rev") else seq


def windows(seq):
    for n in LENGTHS:
        for i in range(len(seq) - n + 1):
            yield seq[i:i + n]


def selftest(oracle):
    ok = True
    good = ("abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon about").split()
    bad = good[:-1] + ["zoo"]
    for label, words, want in (("known-good vector", good, True),
                               ("checksum-broken vector", bad, False)):
        got = checksum_ok(words)
        ok &= got == want
        sys.stderr.write(f"  {label:24} checksum_ok={got} (want {want}) "
                         f"{'OK' if got == want else 'FAIL'}\n")
    # the canonical vector must also derive the canonical BIP44 address
    seed = Mnemonic.to_seed(" ".join(good), passphrase="")
    spks = dict(spks_for_key(derive(seed, "m/44'/0'/0'/0/0")))
    from index_oracle import spk_from_address
    want_spk = spk_from_address("1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA")
    good_spk = spks.get("p2pkh_c") == want_spk
    ok &= good_spk
    sys.stderr.write(f"  {'BIP44 derivation':24} "
                     f"{'OK' if good_spk else 'FAIL'}\n")
    sys.stderr.write("SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--out", default="bip39_valid.tsv")
    ap.add_argument("--hits", default="bip39_sweep_hits.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    oracle = Oracle(verbose=True)
    if not oracle.calibrate():
        sys.exit("oracle calibration failed")
    if not selftest(oracle):
        sys.exit("refusing to run: a null would be meaningless")
    if a.selftest:
        return

    pages = page_texts(a.transcript)
    modes = ["subseq", "subseq_rev", "prefix", "prefix_rev", "runs"]

    valid = {}                 # mnemonic string -> list of (page, mode, offset)
    stats = []
    for page, text in pages:
        for mode in modes:
            got = extract(text, mode)
            seqs = got if mode == "runs" else [got]
            total = sum(len(s) for s in seqs)
            nwin = nval = 0
            for s in seqs:
                for w in windows(s):
                    nwin += 1
                    if checksum_ok(w):
                        nval += 1
                        valid.setdefault(" ".join(w), []).append((page, mode))
            stats.append((page, mode, total, nwin, nval))

    sys.stderr.write("\n  page  mode         bip39_words  windows  valid\n")
    for page, mode, total, nwin, nval in stats:
        sys.stderr.write(f"  {page:4}  {mode:12} {total:11}  {nwin:7}  {nval:5}\n")
    sys.stderr.write(f"\n{len(valid):,} distinct checksum-valid mnemonics\n")

    with open(a.out, "w") as f:
        f.write("mnemonic\tn_words\tsources\n")
        for m, src in sorted(valid.items()):
            f.write(f"{m}\t{len(m.split())}\t"
                    f"{';'.join(f'{p}/{md}' for p, md in src)}\n")

    if not valid:
        sys.stderr.write("no valid mnemonics -> nothing to derive\n")
        return

    paths = build_paths()
    sys.stderr.write(f"deriving {len(valid):,} mnemonics x {len(paths)} paths "
                     f"x 5 script types\n")
    hits = open(a.hits, "w")
    hits.write("mnemonic\tpassphrase\tpath\tscript_type\tbalance_sats\tbalance_btc\n")

    n_addr = n_hit = 0
    # empty passphrase is the standard; the others are cheap and thematic
    passphrases = ["", "bitcoin", "Bitcoin", "overdose", "OVERDOSE",
                   "Max Keiser", "mirror", "20"]
    for mi, m in enumerate(sorted(valid), 1):
        for pw in passphrases:
            seed = Mnemonic.to_seed(m, passphrase=pw)
            meta, spks = [], []
            for p in paths:
                try:
                    k = derive(seed, p)
                except Exception:
                    continue
                for st, spk in spks_for_key(k):
                    meta.append((p, st))
                    spks.append(spk)
                    n_addr += 1
            for j, bal in oracle.contains_spks(spks):
                p, st = meta[j]
                n_hit += 1
                hits.write(f"{m}\t{pw}\t{p}\t{st}\t{bal}\t{bal/1e8:.8f}\n")
                hits.flush()
                sys.stderr.write(f"\n*** HIT {bal/1e8:.8f} BTC  {st}  {p}  "
                                 f"pw={pw!r}\n    {m}\n\n")
        if mi % 25 == 0:
            sys.stderr.write(f"  {mi}/{len(valid)} mnemonics, "
                             f"{n_addr:,} addrs, {n_hit} hits\n")
    hits.close()
    sys.stderr.write(f"\nDONE. {len(valid)} mnemonics, {n_addr:,} addresses, "
                     f"{n_hit} hits -> {a.hits}\n")


if __name__ == "__main__":
    main()
