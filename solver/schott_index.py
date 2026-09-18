#!/usr/bin/env python3
"""
P2: PMC2117809 as a BOOK CIPHER, judged by checksums -- not by hashing.

THE GAP THIS FILLS
`gen_schott.py` already indexes the Schott paper with the banknote serial and
the citation numbers, but it emits the results as PHRASES FOR HASHING: every
reading ends up as a brainwallet passphrase scored against a chain oracle. That
is the wrong oracle twice over -- it needs the prize to have been funded, and it
cannot tell a correct extraction from a wrong one.

A book cipher does not produce a passphrase. It produces the key itself. So the
readings are judged here by the KEY FORMAT'S OWN CHECKSUM, which needs no chain
and no funding assumption:

  WIF        51/52 chars, 0x80-prefixed, 4-byte double-SHA256   ~1 in 4.3e9
  BIP38      58 chars, '6P' prefix, 4-byte check                ~1 in 4.3e9
  mini key   22/26/30 chars, 'S', sha256(k+'?') starts 0x00     ~1 in 14,848 (weak)
  BIP-39     every selected word in the wordlist AND checksum valid

The BIP-39 arm is the sharp one here and is why this is worth running. The
article's own BIP-39 windows are noise (STATUS.md: 18 valid windows vs ~17
expected) because the test there is only the 1-in-16 checksum. Indexing into
the PAPER adds a second, far stronger condition: every selected word must
independently land in the 2048-word list. That joint probability is measured
below against a random-index null rather than assumed.

INDEX SETS -- the numbers actually printed in or attached to Issue 24
  76841714 serial, in every grouping a reader would chunk it into
  73..79 page numbers; 20 (BTC); 24 (issue); 12 (district L12); 3,12 (C,L)
  2001 (series year); the body numbers in print order
  1969 1971 2008 2011 2017; 95 85 2 10; 51 42

Every set is run forwards and reversed, 0- and 1-based, against the paper read
forwards and MIRRORED -- mirror writing being the one device Keiser named.

  python3 schott_index.py --selftest
  python3 schott_index.py
"""
import argparse, hashlib, random, re, sys

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58SET = set(B58)


def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return b"\x00" * (len(s) - len(s.lstrip("1"))) + raw


def dsha(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def check_wif(s):
    if len(s) not in (51, 52) or any(c not in B58SET for c in s):
        return None
    try:
        raw = b58decode(s)
    except Exception:
        return None
    if len(raw) not in (37, 38) or raw[0] != 0x80:
        return None
    if dsha(raw[:-4])[:4] != raw[-4:]:
        return None
    if len(raw) == 38 and raw[33] != 0x01:
        return None
    return ("wif_compressed" if len(raw) == 38 else "wif_uncompressed",
            raw[1:33].hex())


def check_bip38(s):
    if len(s) != 58 or not s.startswith("6P") or any(c not in B58SET for c in s):
        return None
    try:
        raw = b58decode(s)
    except Exception:
        return None
    if len(raw) != 39 or dsha(raw[:-4])[:4] != raw[-4:]:
        return None
    return ("bip38", raw.hex())


def check_mini(s):
    if len(s) not in (22, 26, 30) or not s.startswith("S"):
        return None
    if any(c not in B58SET for c in s):
        return None
    if hashlib.sha256((s + "?").encode()).digest()[0] != 0x00:
        return None
    return ("minikey", hashlib.sha256(s.encode()).hexdigest())


def check_hex(s):
    t = s.lower()
    if len(t) == 64 and all(c in "0123456789abcdef" for c in t):
        n = int(t, 16)
        N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        if 0 < n < N:
            return ("raw_hex", t)
    return None


KEY_CHECKS = (check_wif, check_bip38, check_mini, check_hex)


def key_hit(s):
    for f in KEY_CHECKS:
        r = f(s)
        if r:
            return r
    return None


# ---------------------------------------------------------------- corpora
def load_paper(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"(?:\.\s){4,}\.?", " ", raw)          # dot-leader rules
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", raw)
    lines = [l.strip() for l in raw.splitlines()
             if l.strip() and re.search(r"[A-Za-z]", l)]
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", raw)
             if x.strip() and len(re.findall(r"[A-Za-z]", x)) >= 3]
    return {"words": words, "lines": lines, "sentences": sents}


def load_article(path):
    body = [l for l in open(path, encoding="utf-8").read().splitlines()
            if not l.startswith("#")]
    raw = "\n".join(body)
    return {"words": re.findall(r"[A-Za-z][A-Za-z'-]*", raw),
            "lines": [l.strip() for l in body if l.strip()]}


def article_numbers(path):
    """Numbers printed in the BODY, in reading order (comments stripped)."""
    body = "\n".join(l for l in open(path, encoding="utf-8").read().splitlines()
                     if not l.startswith("#")
                     and not re.match(r"^\s*=== PAGE", l))
    out = []
    for m in re.finditer(r"\d[\d,]*", body):
        v = int(m.group(0).replace(",", ""))
        if v > 0:
            out.append(v)
    return out


# ---------------------------------------------------------------- index sets
def index_sets(artnums):
    d = "76841714"
    s = {
        "serial_singles": [int(c) for c in d],
        "serial_pairs": [76, 84, 17, 14],
        "serial_triples_l": [768, 417, 14],
        "serial_triples_r": [76, 841, 714],
        "serial_quads": [7684, 1714],
        "serial_whole": [76841714],
        "pages_73_79": list(range(73, 80)),
        "prompt_list": [20, 24, 51, 42, 12],
        "district_L12": [12],
        "CL_letters": [3, 12],
        "series_2001": [2001],
        "years": [1969, 1971, 2008, 2011, 2017],
        "money": [95, 85, 2, 10],
        "twenty_btc": [20],
        "issue_24": [24],
        "fiftyone_fortytwo": [51, 42],
        "article_numbers": artnums,
        "citation": [2007, 78, 5, 13, 2006, 94870],
    }
    for k in list(s):
        s[k + "_rev"] = s[k][::-1]
    return {k: v for k, v in s.items() if v}


# ---------------------------------------------------------------- readings
def selections(idxs, seq, base, mirror):
    src = seq[::-1] if mirror else seq
    if not src:
        return []
    return [src[(v - base) % len(src)] for v in idxs]


def strings_from(sel):
    """Every string a reader would build out of the selected units."""
    out = []
    joined = " ".join(sel)
    out.append(("join", joined))
    out.append(("join_nospace", "".join(sel)))
    words = [w for w in re.findall(r"[A-Za-z]+", joined)]
    if words:
        out.append(("initials", "".join(w[0] for w in words)))
        out.append(("initials_up", "".join(w[0].upper() for w in words)))
        out.append(("finals", "".join(w[-1] for w in words)))
        out.append(("initials_rev", "".join(w[0] for w in words)[::-1]))
    return out


def pair_readings(idxs, lines, base, swap):
    """Classic book cipher: consecutive numbers as (line, word-in-line)."""
    if len(idxs) < 4 or len(idxs) % 2:
        return []
    sel = []
    for i in range(0, len(idxs), 2):
        a, b = idxs[i], idxs[i + 1]
        if swap:
            a, b = b, a
        line = lines[(a - base) % len(lines)]
        ws = re.findall(r"[A-Za-z][A-Za-z'-]*", line)
        if not ws:
            return []
        sel.append(ws[(b - base) % len(ws)])
    return sel


def scan(paper, article, sets, mnemo, verbose=False):
    keyhits, b39hits = [], []
    n_read = 0
    corpora = [("paper", paper), ("article", article)]
    for cname, corp in corpora:
        for uname, seq in corp.items():
            for iname, idxs in sets.items():
                for base in (0, 1):
                    for mirror in (False, True):
                        sel = selections(idxs, seq, base, mirror)
                        if not sel:
                            continue
                        n_read += 1
                        tag = f"{cname}/{uname}/{iname}/base{base}/{'mir' if mirror else 'fwd'}"
                        for sname, s in strings_from(sel):
                            r = key_hit(s)
                            if r:
                                keyhits.append((tag, sname, r[0], s, r[1]))
                        if uname == "lines":
                            for swap in (False, True):
                                p = pair_readings(idxs, seq, base, swap)
                                if not p:
                                    continue
                                n_read += 1
                                ptag = tag + f"/pair{'S' if swap else ''}"
                                for sname, s in strings_from(p):
                                    r = key_hit(s)
                                    if r:
                                        keyhits.append((ptag, sname, r[0], s, r[1]))
                                lw = [w.lower() for w in p]
                                if len(lw) in (12, 15, 18, 21, 24) and \
                                   all(w in mnemo.wordlist for w in lw):
                                    b39hits.append((ptag, mnemo.check(" ".join(lw)),
                                                    " ".join(lw)))
                        # BIP-39 arm: only meaningful on word units
                        if uname == "words":
                            lw = [w.lower() for w in sel]
                            if len(lw) in (12, 15, 18, 21, 24) and \
                               all(w in mnemo.wordlist for w in lw):
                                ph = " ".join(lw)
                                b39hits.append((tag, mnemo.check(ph), ph))
    return keyhits, b39hits, n_read


def null_rate(paper, mnemo, trials, rng):
    """Random index sets of the same shapes: measure the false-alarm rate."""
    words = paper["words"]
    fp_key = fp_b39 = 0
    for _ in range(trials):
        L = rng.choice([8, 12, 4, 7, 5])
        idxs = [rng.randrange(1, len(words)) for _ in range(L)]
        sel = selections(idxs, words, 1, False)
        for _sn, s in strings_from(sel):
            if key_hit(s):
                fp_key += 1
        lw = [w.lower() for w in sel]
        if len(lw) == 12 and all(w in mnemo.wordlist for w in lw):
            fp_b39 += 1
    return fp_key, fp_b39


def selftest(mnemo):
    ok = True
    wif = "5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf"
    r = check_wif(wif)
    ok &= bool(r) and r[1] == "00" * 31 + "01"
    print(f"  known WIF (privkey=1) recognised: {bool(r)}")
    bad = wif[:-1] + ("f" if wif[-1] != "f" else "g")
    ok &= check_wif(bad) is None
    print(f"  corrupted WIF rejected: {check_wif(bad) is None}")
    v = ("abandon " * 11) + "about"
    ok &= mnemo.check(v) and not mnemo.check(v.replace("about", "abandon"))
    print(f"  BIP-39 vector validates, corrupted one fails: {mnemo.check(v)}")
    sel = selections([1, 3], ["alpha", "bravo", "charlie", "delta"], 1, False)
    ok &= sel == ["alpha", "charlie"]
    print(f"  1-based index into 4 words -> {sel}")
    ok &= check_hex("f" * 64) is None          # >= curve order n
    print(f"  out-of-range hex rejected: {check_hex('f'*64) is None}")
    print("  SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="schott_full.txt")
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--trials", type=int, default=4000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    from mnemonic import Mnemonic
    mnemo = Mnemonic("english")
    if not selftest(mnemo):
        sys.exit("controls fail; refusing to report a null")
    if a.selftest:
        return

    paper = load_paper(a.paper)
    article = load_article(a.transcript)
    artnums = article_numbers(a.transcript)
    sets = index_sets(artnums)

    print(f"\npaper   : {len(paper['words'])} words, {len(paper['lines'])} lines, "
          f"{len(paper['sentences'])} sentences")
    print(f"article : {len(article['words'])} words, {len(article['lines'])} lines")
    print(f"body numbers in print order: {artnums}")
    print(f"index sets: {len(sets)}")

    inlist = sum(1 for w in paper["words"] if w.lower() in mnemo.wordlist)
    frac = inlist / len(paper["words"])
    print(f"paper tokens that are BIP-39 words: {inlist}/{len(paper['words'])} "
          f"= {frac:.4f}  -> P(12 random all in list) = {frac**12:.3e}")

    keyhits, b39hits, n_read = scan(paper, article, sets, mnemo)
    print(f"\nreadings evaluated: {n_read:,}")
    print(f"checksum-valid key strings : {len(keyhits)}")
    for h in keyhits:
        print("   HIT", h)
    print(f"all-BIP-39 word selections : {len(b39hits)}")
    for h in b39hits:
        print("   B39", h)

    rng = random.Random(20)
    fk, fb = null_rate(paper, mnemo, a.trials, rng)
    print(f"\nnull ({a.trials:,} random index sets): {fk} key hits, {fb} all-BIP-39")
    print("\nVERDICT: " + ("NOTHING -- the book cipher does not fire"
                           if not keyhits and not b39hits else
                           "SOMETHING FIRED, inspect above"))


if __name__ == "__main__":
    main()
