#!/usr/bin/env python3
"""
numscalar.py -- The article's NUMERALS as raw key material (no hashing).

HYPOTHESIS (puzzle-setter lens). A writer cannot control a designer's line
breaks, but he can guarantee that the NUMBERS in his piece survive layout.
"The key is the digits in my article" is a construction a non-cryptographer
can execute with no tooling and later describe as "hidden in the text";
"mirror writing" then means the digit string read backwards. The eliminated
list covers HASHES of number strings (number/metadata brainwallets) and the
banknote digits as a few raw integers (gen_banknote.py), and the article's
numbers as indices into the SCHOTT PAPER's words (running_key_hunt.py) --
but never the article's numerals used directly as the secp256k1 scalar, as
indices into the BIP-39 / old-Electrum wordlists, as BIP-39 entropy, or as
BIP-32 path components.

TOKENS (reading order, $ , % stripped; asserted against the transcript):
  2008 1 1 1 1971 10 1 2011 1 42 20000 100000 2017 12000 51 85 2 51 95 1969 10
Variants: spelled numbers in place (Forty=40 p76, six=6 p77; +ONE=1 p77,
zero=0 p79), magnitude words expanded ($1 billion, $85 BILLION, $2 trillion),
banknote serial 76841714 / plate 12 / series 2009 (p73-74), page numbers
73..79, Issue 24, the 20 BTC prize.

FAMILIES
  A. Raw scalar: every digit string (whole article, per page, years only,
     without the three "Layer 1" ones, each variant above, every contiguous
     token window, token sums and products) read as decimal and as hex, in
     four directions (as-is, token order reversed, digits-within-token
     reversed, whole string reversed), plus negation (n-k) and byte-mirror of
     each, plus the ASCII bytes of 32-digit slices -> 5 script types -> oracle.
     Plus EVERY small scalar 1..--scan-limit (covers each single token).
  B. BIP-39 index book-cipher: tokens < 2048 (0- and 1-based) and tokens
     mod 2048, every 12/15/18/21/24 window, forward and reversed -> checksum
     -> passphrases x HD paths -> oracle. Checksum-failing windows are also
     derived (marked) since a 2021 tool could have been lenient.
  C. Integer as BIP-39 ENTROPY: each whole-list digit string as a 128/256-bit
     number -> proper mnemonic (checksum computed) -> passphrases -> oracle.
  D. Old Electrum: tokens < 1626 / mod 1626, 12-windows -> stretched key;
     and each digit string's 128-bit value as the old hex seed directly.
  E. Numbers as HD path components: seeds from the setter's own display
     sentences, the clue words, the ordered highlight concatenation and the
     whole prose (sha256 / sha512 / BIP-39-text / Electrum-text seeds) x paths
     whose account or index is an article number, and paths built from the
     whole number SEQUENCE.
  F. (completeness only, overlaps prior brainwallet work) the digit strings as
     brainwallet passphrases through check_phrase_direct.

ORACLE. harness.Oracle = 1.72M Apr-2023 rich list (set) + the full 56.8M
current-balance index. The per-address index lookup is a cold mmap binary
search (~0.25 s); this script loads the 454 MB prefix array into RAM and
checks addresses in vectorised batches through index_oracle.contains_spks.

CONTROLS (all must pass before a null is reported):
  1. addrs_for_priv(k=1) yields the two well-known k=1 addresses
     (1EHNa6... uncompressed, 1BgGZ9... compressed).
  2. The batch checker flags injected KNOWN-FUNDED addresses of every script
     type it will meet (P2PKH genesis, P2SH, P2WPKH, P2TR) and not an
     unfunded one.
  3. If the small-scalar scan finds any funded k <= --scan-limit, that k is
     pushed through the family-A code path and must be flagged (end-to-end).
  4. Index pipeline on [0]*11+[3] (0-based) gives 'abandon x11 about', passes
     bip39_valid and derives 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA at
     m/44'/0'/0'/0/0 through the family-B code path.
  5. Entropy pipeline on 0 gives the same mnemonic.
  6. Old-Electrum vector words -> indices -> family-D pipeline -> its old/0/0
     address 1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo.
  7. Family-E path pipeline with the BIP-39 vector seed and n=0 reproduces
     1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA.

Usage (from solver/):  python3 wf/numscalar.py [--scan-limit 100000]
"""
import os, re, sys, time, hashlib, argparse
from functools import reduce

HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.path.dirname(HERE)
sys.path.insert(0, SOLVER)
import numpy as np
import harness as H
import index_oracle as IO
from mnemonic import Mnemonic

N = H.CURVE_N
TRANSCRIPT = os.path.join(SOLVER, "article_transcript.txt")
HL_TSV = os.path.join(SOLVER, "highlights_ordered.tsv")

PASSPHRASES = ["", "El Salvador", "ElSalvador", "el salvador", "elsalvador",
               "EL SALVADOR", "Overdose", "OVERDOSE", "Max Keiser", "20"]

EXPECTED_TOKENS = [2008, 1, 1, 1, 1971, 10, 1, 2011, 1, 42, 20000, 100000,
                   2017, 12000, 51, 85, 2, 51, 95, 1969, 10]
LAYER1_POS = {1, 2, 3}          # positions of the three "Layer 1" ones

# known-funded controls for the batch checker, one per script type it meets
FUNDED_CONTROLS = {
    "p2pkh": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",   # genesis coinbase
    "p2sh": "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r",    # Bitfinex cold
    # rich-list addresses verified present in the full index by
    # index_oracle.Oracle.balance() (the window/current_exact20_bc1{q,p} files
    # are Apr-2023 rich-list entries that have since been spent: NOT in the index)
    "p2sh-exact20": "3E8svDc3ZJ2jYhYKrx3vasr2b3BQW8sDxV",
    "p2wpkh": "bc1q000cqh4rx9552j7lwvm2gqmzamyshw5trcl7tv",
    "p2tr": "bc1p02caf37sw5k40lw93cs5dtu6v2852mxyvp3mxhc4v5zc3njyvutqnfc8g9",
}
UNFUNDED_CONTROL = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"   # swept brainwallet


# ------------------------------------------------------------ bookkeeping --
class Stats:
    def __init__(self):
        self.c = {}
        self.hits = []

    def inc(self, k, n=1):
        self.c[k] = self.c.get(k, 0) + n

    def fmt(self):
        return ", ".join(f"{k}={v}" for k, v in sorted(self.c.items()))


S = Stats()
O = None          # harness oracle
CK = None         # batch checker
LOG = None


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    if LOG:
        LOG.write(s + "\n")
        LOG.flush()


class Checker:
    """Buffers (family, deriv, type, addr, priv, sink) rows; flushes them
    against the rich-list set and, vectorised, against the full index."""
    BATCH = 20000

    def __init__(self, oracle):
        self.O = oracle
        self.full = oracle.full
        if self.full is not None and isinstance(self.full.prefix, np.memmap):
            t0 = time.time()
            self.full.prefix = np.load(IO.NPY)          # into RAM, not mmap
            log(f"  prefix index loaded into RAM: {self.full.prefix.nbytes/1e6:.0f} MB in {time.time()-t0:.1f}s")
        self.buf = []
        self.n_checked = 0

    def add(self, family, deriv, typ, addr, priv_hex, sink=None):
        self.buf.append((family, deriv, typ, addr, priv_hex, sink))
        if len(self.buf) >= self.BATCH:
            self.flush()

    def flush(self):
        if not self.buf:
            return
        rows, self.buf = self.buf, []
        self.n_checked += len(rows)
        S.inc("addresses_checked", len(rows))
        found = {}                                    # j -> balance or None
        for j, r in enumerate(rows):
            if r[3] in self.O.addrs:
                found[j] = None
        if self.full is not None:
            spks, js = [], []
            for j, r in enumerate(rows):
                spk = IO.spk_from_address(r[3])
                if spk is not None:
                    spks.append(spk)
                    js.append(j)
            for jj, bal in self.full.contains_spks(spks):
                found[js[jj]] = bal
        for j in sorted(found):
            family, deriv, typ, addr, priv_hex, sink = rows[j]
            rec = dict(family=family, derivation=deriv, type=typ, address=addr,
                       priv=priv_hex, balance_sats=found[j],
                       in_richlist=addr in self.O.addrs)
            (sink if sink is not None else S.hits).append(rec)
            log(f"HIT [{family}] {deriv} {typ} {addr} bal={found[j]} richlist={rec['in_richlist']} priv={priv_hex}")


def check_addr(family, deriv, typ, addr, priv_hex, sink=None):
    CK.add(family, deriv, typ, addr, priv_hex, sink)


def check_priv(family, deriv, k_int, sink=None):
    """k_int -> 5 address types -> checker."""
    if not (0 < k_int < N):
        S.inc("scalars_out_of_range")
        return
    priv = k_int.to_bytes(32, "big")
    S.inc("keys_derived")
    for t, a in H.addrs_for_priv(priv).items():
        check_addr(family, deriv, t, a, priv.hex(), sink)


# ------------------------------------------------------------- tokens -----
def load_pages():
    txt = open(TRANSCRIPT, encoding="utf-8").read()
    pages = {}
    for m in re.finditer(r"=== PAGE (\d+) \(IMG_\d+\) ===\n(.*?)(?==== PAGE|\Z)", txt, re.S):
        pages[int(m.group(1))] = m.group(2)
    return pages


NUM_RE = re.compile(r"\$?\d[\d,]*%?")


def tokens_in(text):
    return [int(re.sub(r"[$,%]", "", m)) for m in NUM_RE.findall(text)]


def build_token_lists(pages):
    """Return ordered dict label -> list of ints."""
    body = "".join(pages[p] for p in sorted(pages))
    lists = {}
    allt = tokens_in(body)
    assert allt == EXPECTED_TOKENS, (allt, EXPECTED_TOKENS)
    lists["all"] = allt
    for p in sorted(pages):
        lists[f"p{p}"] = tokens_in(pages[p])
    lists["years"] = [t for t in allt if 1900 <= t <= 2100]
    lists["noL1"] = [t for i, t in enumerate(allt) if i not in LAYER1_POS]
    lists["nonyears"] = [t for t in allt if not 1900 <= t <= 2100]

    # spelled numbers in place: Forty (p76 l57, before 1971), six (p77 l89,
    # after 100,000 and before 2017), ONE (p77 l103, after 2017 before 12,000),
    # zero (p79 l159, after 95% before 1969)
    def with_spelled(base, full):
        out = []
        for i, t in enumerate(base):
            if t == 1971 and i > 0 and base[i - 1] == 1:      # "Forty years of dumb post-1971"
                out.append(40)
            out.append(t)
            if t == 100000:
                out.append(6)                                   # "within six months"
            if full and t == 2017:
                out.append(1)                                   # "EVERY SINGLE ONE OF"
            if full and t == 95 and 1969 in base[i:]:
                out.append(0)                                   # "drops to near zero"
        return out
    lists["spelled"] = with_spelled(allt, False)
    lists["spelled_full"] = with_spelled(allt, True)
    assert lists["spelled"] == [2008, 1, 1, 1, 40, 1971, 10, 1, 2011, 1, 42, 20000, 100000, 6,
                                2017, 12000, 51, 85, 2, 51, 95, 1969, 10], lists["spelled"]

    # magnitude words expanded: "$1 billion" (p76 l75), "$85 BILLION" (p78 l134),
    # "$2 trillion" (p78 l136)
    def with_mag(base):
        out = []
        for i, t in enumerate(base):
            if t == 1 and i > 0 and base[i - 1] == 2011:
                out.append(10 ** 9)
            elif t == 85:
                out.append(85 * 10 ** 9)
            elif t == 2 and i > 0 and base[i - 1] == 85:
                out.append(2 * 10 ** 12)
            else:
                out.append(t)
        return out
    lists["magnitude"] = with_mag(allt)
    lists["spelled_magnitude"] = with_mag(lists["spelled"])

    # extras: banknote serial / plate / series, page numbers, issue, prize
    bank = [76841714, 12]
    lists["bank_pre"] = bank + allt
    lists["bank_post"] = allt + bank
    lists["bank_pre_series"] = [2009] + bank + allt
    lists["pages_pre"] = [73, 74] + allt          # p73/74 carry no numerals but are the spread
    lists["issue_pre"] = [24] + allt
    lists["issue_post"] = allt + [24]
    lists["prize_post"] = allt + [20]
    wp = [73, 74]
    for p in sorted(pages):
        wp += [p] + tokens_in(pages[p])
    lists["with_pagenums"] = wp
    lists["everything"] = [24, 73, 74, 76841714, 12, 2009] + lists["spelled_full"]
    return lists


# ------------------------------------------------------------ family A ----
def digit_strings(tokens):
    """Four directions of one token list -> {dir_label: digit string}."""
    fwd = "".join(str(t) for t in tokens)
    return {
        "asis": fwd,
        "tokrev": "".join(str(t) for t in tokens[::-1]),
        "digrev": "".join(str(t)[::-1] for t in tokens),
        "strrev": fwd[::-1],
    }


def scalars_from_string(s):
    """digit string -> {reading: int}."""
    out = {}
    if not s or not s.isdigit():
        return out
    out["dec"] = int(s)
    out["hex"] = int(s, 16)
    for name, v in list(out.items()):
        if 0 < v < N:
            out[name + "_neg"] = N - v
            out[name + "_bytemirror"] = int.from_bytes(v.to_bytes(32, "big")[::-1], "big")
    if len(s) >= 32:
        out["ascii_head32"] = int.from_bytes(s[:32].encode(), "big")
        out["ascii_tail32"] = int.from_bytes(s[-32:].encode(), "big")
    else:
        out["ascii_lpad32"] = int.from_bytes(s.rjust(32, "0").encode(), "big")
        out["ascii_rpad32"] = int.from_bytes(s.ljust(32, "0").encode(), "big")
    return out


WINDOW_LISTS = ("all", "spelled", "spelled_full", "magnitude", "everything", "noL1")


def family_A(lists, sink=None, seen=None):
    seen = seen if seen is not None else {}
    n_strings = 0
    for label, toks in lists.items():
        if not toks:
            continue
        strings = {}
        for d, s in digit_strings(toks).items():
            strings[f"{label}/{d}"] = s
        if label in WINDOW_LISTS:
            for order, tl in (("fwd", toks), ("rev", toks[::-1])):
                L = len(tl)
                for i in range(L):
                    for j in range(i + 1, L + 1):
                        w = tl[i:j]
                        if len(w) == L:
                            continue
                        strings[f"{label}/win{order}[{i}:{j}]"] = "".join(str(t) for t in w)
                        strings[f"{label}/win{order}[{i}:{j}]/digrev"] = "".join(str(t)[::-1] for t in w)
                        strings[f"{label}/win{order}[{i}:{j}]/sum"] = str(sum(w))
                        strings[f"{label}/win{order}[{i}:{j}]/prod"] = str(reduce(lambda a, b: a * b, w, 1))
            strings[f"{label}/sum"] = str(sum(toks))
            strings[f"{label}/prod"] = str(reduce(lambda a, b: a * b, toks, 1))
        for sl, s in strings.items():
            n_strings += 1
            for reading, k in scalars_from_string(s).items():
                if k in seen:
                    continue
                seen[k] = f"{sl}/{reading}"
                S.inc("A_scalars")
                check_priv("A", f"{sl}/{reading} k={k if k < 10**40 else hex(k)}", k, sink)
    S.inc("A_digit_strings", n_strings)
    return seen


def small_scalar_scan(limit, sink):
    """Every k in 1..limit through the family-A code path (covers each single
    token, and finds a funded small scalar to serve as the end-to-end control)."""
    t0 = time.time()
    for k in range(1, limit + 1):
        check_priv("A-scan", f"k={k}", k, sink)
    CK.flush()
    log(f"  small-scalar scan k=1..{limit}: {len(sink)} funded, {time.time()-t0:.0f}s")
    return sink


# ------------------------------------------------------------ family B ----
def index_words(tokens, wordlist, base, mod):
    """tokens -> words. base 0/1; mod: False (drop out-of-range) or wrap."""
    n = len(wordlist)
    out = []
    for t in tokens:
        i = t - base
        if mod:
            i %= n
        elif not 0 <= i < n:
            continue
        out.append(wordlist[i])
    return out


def bip39_derive(words, tag, passphrases, paths, sink=None):
    m = " ".join(words)
    n = 0
    for pw in passphrases:
        S.inc("B_mnemonic_pw_pairs")
        for p, t, a, priv in H.bip39_addrs(m, pw, paths):
            n += 1
            check_addr("B", f"{tag} pw='{pw}' {p}", t, a, priv.hex(), sink)
    S.inc("keys_derived", n // 5 if n else 0)
    return n


def family_B(lists, sink=None):
    seen = set()
    windows = valid = 0
    for label, toks in lists.items():
        if len(toks) < 12:
            continue
        for base in (0, 1):
            for mod in (False, True):
                seq = index_words(toks, H.BIP39, base, mod)
                for direction, sq in (("fwd", seq), ("rev", seq[::-1])):
                    for L in (12, 15, 18, 21, 24):
                        for i in range(0, len(sq) - L + 1):
                            w = tuple(sq[i:i + L])
                            if w in seen:
                                continue
                            seen.add(w)
                            windows += 1
                            ok = H.bip39_valid(list(w))
                            tag = f"B/{label}/base{base}/{'mod' if mod else 'drop'}/{direction}/L{L}@{i}"
                            if ok:
                                valid += 1
                                log(f"  bip39 checksum VALID: {tag}: {' '.join(w)}")
                                bip39_derive(w, tag + "/valid", PASSPHRASES, H.default_paths(), sink)
                            else:
                                bip39_derive(w, tag + "/nochk", PASSPHRASES, H.quick_paths(), sink)
    S.inc("B_windows", windows)
    S.inc("B_checksum_valid", valid)
    return windows, valid


# ------------------------------------------------------------ family C ----
MN = Mnemonic("english")


def entropy_mnemonics(k):
    """int -> list of (label, mnemonic) for 128- and 256-bit entropy readings."""
    out = []
    b32 = k.to_bytes(32, "big") if k < (1 << 256) else None
    for bits in (128, 256):
        nb = bits // 8
        if k < (1 << bits):
            out.append((f"ent{bits}", MN.to_mnemonic(k.to_bytes(nb, "big"))))
        out.append((f"ent{bits}_mod", MN.to_mnemonic((k % (1 << bits)).to_bytes(nb, "big"))))
        if b32 is not None:
            out.append((f"ent{bits}_highbytes", MN.to_mnemonic(b32[:nb])))
    return out


def family_C(lists, sink=None):
    seen = set()
    n = 0
    for label, toks in lists.items():
        if not toks:
            continue
        for d, s in digit_strings(toks).items():
            for reading in ("dec", "hex"):
                k = int(s) if reading == "dec" else int(s, 16)
                if not 0 < k < N:
                    continue
                for el, m in entropy_mnemonics(k):
                    if m in seen:
                        continue
                    seen.add(m)
                    n += 1
                    assert H.bip39_valid(m.split())
                    bip39_derive(m.split(), f"C/{label}/{d}/{reading}/{el}", PASSPHRASES,
                                 H.quick_paths(), sink)
    S.inc("C_mnemonics", n)
    return n


# ------------------------------------------------------------ family D ----
def old_electrum_derive(words_or_hex, tag, sink=None):
    rows = H.electrum_old_addrs(words_or_hex, 5) + H.electrum_old_addrs(words_or_hex, 2, change=True)
    S.inc("keys_derived", len(rows))
    for p, t, a, priv in rows:
        check_addr("D", f"{tag} {p}", t, a, priv.hex(), sink)
    return rows


def family_D(lists, sink=None):
    seen = set()
    n_words = n_hex = 0
    for label, toks in lists.items():
        if not toks:
            continue
        if len(toks) >= 12:
            for base in (0, 1):
                for mod in (False, True):
                    seq = index_words(toks, H.ELECTRUM_OLD, base, mod)
                    for direction, sq in (("fwd", seq), ("rev", seq[::-1])):
                        for i in range(0, len(sq) - 12 + 1):
                            w = tuple(sq[i:i + 12])
                            if w in seen:
                                continue
                            seen.add(w)
                            n_words += 1
                            assert H.electrum_old_valid(list(w))
                            old_electrum_derive(list(w), f"D/{label}/base{base}/{'mod' if mod else 'drop'}/{direction}@{i}", sink)
        for d, s in digit_strings(toks).items():
            for reading in ("dec", "hex"):
                k = int(s) if reading == "dec" else int(s, 16)
                for el, hx in (("low128", "%032x" % (k % (1 << 128))),
                               ("strdigits32", s[:32].ljust(32, "0"))):
                    if hx in seen:
                        continue
                    seen.add(hx)
                    n_hex += 1
                    old_electrum_derive(hx, f"D/{label}/{d}/{reading}/{el}", sink)
    S.inc("D_word_windows", n_words)
    S.inc("D_hex_seeds", n_hex)
    return n_words, n_hex


# ------------------------------------------------------------ family E ----
SEED_PHRASES = [
    "El Salvador", "OVERDOSE", "Overdose", "Bitcoin Is Toxic AF", "BITCOIN IS TOXIC AF",
    "Max Keiser", "MAX KEISER",
    "The numbers don't lie.",
    "They are the sum of all our neuroses.",
    "Gotta be this way.",
    "Keep your dignity.",
    "Don't fall for shitcoinery.",
    "Go Bitcoin Toxic Maximalist,",
    "Toxic Bitcoin Maximalist",
    "the Layer 1 of the whole Satoshi experience.",
    "It's a stun gun to the genitals.",
    "A monetary defibrillator to the treasure chest.",
    "BITCOIN FIXES ALL THIS",
    "That's right, Bitcoin will take all the energy.",
    "Everyone will live their own experience in the rabbit hole.",
    "We are getting our souls back and our minds.",
    "We've seen some shit.",
    "right there in the Genesis Block.",
    "Stacy and I have been living in here for 10 years.",
    "The economy of love is infinitely more efficient than hate and war.",
]


def load_highlight_concat():
    rows = []
    for line in open(HL_TSV, encoding="utf-8"):
        if line.startswith("#") or "\t" not in line:
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            rows.append(p[2].strip())
    return " ".join(rows)


def seeds_for_phrase(phrase):
    """(label, seed bytes) list: sha256, sha512, BIP-39-text, Electrum-text."""
    b = phrase.encode()
    out = [("sha256", hashlib.sha256(b).digest()), ("sha512", hashlib.sha512(b).digest())]
    for pw in ("", "El Salvador"):
        out.append((f"bip39text pw='{pw}'", H.bip39_seed(phrase, pw)))
        out.append((f"electrumtext pw='{pw}'", H.electrum_v2_seed(phrase, pw)))
    return out


def number_paths(numset, seqs):
    paths = []
    for n in sorted(numset):
        if n >= (1 << 31):
            continue
        paths += [f"m/44'/0'/0'/0/{n}", f"m/44'/0'/0'/1/{n}", f"m/44'/0'/{n}'/0/0",
                  f"m/49'/0'/0'/0/{n}", f"m/49'/0'/{n}'/0/0",
                  f"m/84'/0'/0'/0/{n}", f"m/84'/0'/{n}'/0/0",
                  f"m/86'/0'/0'/0/{n}",
                  f"m/0/{n}", f"m/0'/0/{n}", f"m/{n}", f"m/{n}'", f"m/{n}'/0/0", f"m/{n}/0"]
    for label, seq in seqs.items():
        sq = [t for t in seq if t < (1 << 31)]
        if not sq:
            continue
        for direction, s in (("fwd", sq), ("rev", sq[::-1])):
            paths.append("m/" + "/".join(str(t) for t in s))
            paths.append("m/" + "/".join(f"{t}'" for t in s))
            paths.append("m/44'/0'/0'/0/" + "/".join(str(t) for t in s))
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def hd_check(family, seed_label, seed, paths, sink=None):
    n = 0
    for p, t, a, priv in H.hd_addrs(seed, paths):
        n += 1
        check_addr(family, f"{seed_label} {p}", t, a, priv.hex(), sink)
    S.inc("keys_derived", n // 5 if n else 0)
    return n


def family_E(lists, sink=None):
    numset = set()
    for toks in lists.values():
        numset |= set(toks)
    numset |= {0, 20, 24, 73, 74, 75, 76, 77, 78, 79, 12, 2009, 76841714, 6, 40}
    seqs = {k: lists[k] for k in ("all", "years", "p75", "p76", "p77", "p78", "p79",
                                  "spelled", "noL1", "nonyears")}
    paths = number_paths(numset, seqs)
    S.inc("E_paths", len(paths))
    phrases = list(SEED_PHRASES) + [load_highlight_concat()]
    pages = load_pages()
    body = " ".join(" ".join(pages[p].split()) for p in sorted(pages))
    phrases.append(body)
    phrases.append(body.lower())
    n_seeds = 0
    t0 = time.time()
    for ph in phrases:
        for sl, seed in seeds_for_phrase(ph):
            n_seeds += 1
            short = ph if len(ph) <= 50 else ph[:47] + "..."
            hd_check("E", f"seed={sl} phrase='{short}'", seed, paths, sink)
        log(f"    E: {n_seeds} seeds done, {time.time()-t0:.0f}s")
    S.inc("E_seeds", n_seeds)
    return n_seeds, len(paths)


# ------------------------------------------------------------ family F ----
def family_F(lists, sink=None):
    seen = set()
    n = 0
    for label, toks in lists.items():
        if not toks:
            continue
        variants = set(digit_strings(toks).values())
        variants.add(" ".join(str(t) for t in toks))
        variants.add(",".join(str(t) for t in toks))
        variants.add(" ".join(str(t) for t in toks[::-1]))
        for v in variants:
            if v in seen:
                continue
            seen.add(v)
            n += 1
            from hd_sweep import direct_keys
            for name, k in direct_keys(v).items():
                S.inc("keys_derived")
                for t, a in H.addrs_for_priv(k).items():
                    check_addr("F", f"{label} brainwallet {name} '{v[:40]}'", t, a, k.hex(), sink)
    S.inc("F_phrases", n)
    return n


# ------------------------------------------------------------ controls ----
def controls(scan_limit):
    res = []

    def chk(name, ok, detail=""):
        res.append((name, bool(ok)))
        log(f"  CONTROL {'PASS' if ok else 'FAIL'}  {name}  {detail}")

    # 1. k=1 derivation (the task text had the two addresses swapped: G's
    #    UNcompressed hash160 is 1EHNa6..., the compressed one is 1BgGZ9...)
    a1 = H.addrs_for_priv((1).to_bytes(32, "big"))
    chk("k=1 uncompressed addr", a1["p2pkh_u"] == "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm", a1["p2pkh_u"])
    chk("k=1 compressed addr", a1["p2pkh_c"] == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", a1["p2pkh_c"])
    log(f"  info: k=1 addrs in current-balance oracle? u={O.funded(a1['p2pkh_u'])} c={O.funded(a1['p2pkh_c'])}"
        " (a current-balance index; they hold nothing today)")
    # 2. batch checker flags injected known-funded addresses of every type
    for typ, addr in FUNDED_CONTROLS.items():
        sink = []
        check_addr("ctrl", f"injected {typ}", typ, addr, "-", sink)
        CK.flush()
        chk(f"batch checker flags funded {typ} WITH full-index balance",
            len(sink) == 1 and sink[0]["address"] == addr and sink[0]["balance_sats"] is not None,
            f"bal={sink[0]['balance_sats'] if sink else None} richlist={sink[0]['in_richlist'] if sink else None}")
    sink = []
    check_addr("ctrl", "injected unfunded", "p2pkh_u", UNFUNDED_CONTROL, "-", sink)
    CK.flush()
    chk("batch checker ignores unfunded brainwallet", len(sink) == 0)
    # 3. small-scalar scan through the family-A code path
    scan = small_scalar_scan(scan_limit, [])
    if scan:
        ks = sorted({int(r["derivation"].split("=")[1]) for r in scan})
        chk(f"end-to-end: funded small scalar(s) found by family-A path k in {ks[:10]}", True,
            "; ".join(f"k={int(r['derivation'].split('=')[1])} {r['type']} {r['address']} bal={r['balance_sats']}" for r in scan[:10]))
        for r in scan:
            S.hits.append(dict(r, family="A-scan"))
    else:
        log(f"  info: no funded scalar in 1..{scan_limit}; family-A control is two-part "
            "(derivation vs known k=1 addresses + injected funded addresses through the checker)")
    # 4. index pipeline -> abandon x11 about -> bip44 address
    w = index_words([0] * 11 + [3], H.BIP39, 0, False)
    chk("index words abandon x11 about", " ".join(w) == "abandon " * 11 + "about", " ".join(w[-2:]))
    chk("bip39_valid on index words", H.bip39_valid(w))
    addrs = {a for _, _, a, _ in H.bip39_addrs(" ".join(w), "", ["m/44'/0'/0'/0/0"])}
    chk("family-B derivation bip44", "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA" in addrs)
    # 5. entropy pipeline
    em = dict(entropy_mnemonics(0)).get("ent128_mod")
    chk("entropy 0 -> abandon..about", em == ("abandon " * 11 + "about"))
    # 6. old electrum vector through the index pipeline
    vec = "powerful random nobody notice nothing important anyway look away hidden message over".split()
    idx = [H.ELECTRUM_OLD_IDX[x] for x in vec]
    w = index_words(idx, H.ELECTRUM_OLD, 0, False)
    rows = old_electrum_derive(w, "ctrl", sink=[])
    chk("old-electrum index pipeline addr0", rows and rows[0][2] == "1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo",
        rows[0][2] if rows else None)
    # 7. family-E path pipeline with the BIP-39 vector seed at n=0
    seed = H.bip39_seed("abandon " * 11 + "about", "")
    paths = number_paths({0}, {})
    rows = H.hd_addrs(seed, paths)
    chk("family-E paths include m/44'/0'/0'/0/0", "m/44'/0'/0'/0/0" in paths)
    chk("family-E path pipeline bip44 addr",
        any(a == "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA" for _, _, a, _ in rows))
    CK.flush()
    ok = all(v for _, v in res)
    log(f"CONTROLS {'ALL PASS' if ok else 'SOME FAILED'} ({sum(v for _, v in res)}/{len(res)})")
    return ok


# ---------------------------------------------------------------- main ----
def main():
    global O, CK, LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=os.path.join(HERE, "numscalar.log"))
    ap.add_argument("--hits", default=os.path.join(HERE, "numscalar_hits.tsv"))
    ap.add_argument("--scan-limit", type=int, default=100000)
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--skip", default="", help="comma list of families to skip, e.g. E")
    a = ap.parse_args()
    LOG = open(a.log, "w")
    O = H.Oracle()
    CK = Checker(O)
    t0 = time.time()

    log("== controls ==")
    if not controls(a.scan_limit):
        log("refusing to run: a control failed")
        sys.exit(2)
    scan_hits = [h for h in S.hits if h["family"] == "A-scan"]
    S.c.clear()
    S.hits.clear()
    S.hits.extend(scan_hits)
    if a.controls_only:
        return
    skip = set(a.skip.split(",")) if a.skip else set()

    pages = load_pages()
    lists = build_token_lists(pages)
    log("== token lists ==")
    for k, v in lists.items():
        log(f"  {k:18} ({len(v):2}) {v}")

    if "A" not in skip:
        log("== A. raw scalars ==")
        family_A(lists)
        CK.flush()
        log(f"  A done: {S.c.get('A_digit_strings')} digit strings, {S.c.get('A_scalars')} distinct scalars, {time.time()-t0:.0f}s")
    if "B" not in skip:
        log("== B. BIP-39 index book-cipher ==")
        family_B(lists)
        CK.flush()
        log(f"  B done: {S.c.get('B_windows')} windows, {S.c.get('B_checksum_valid')} checksum-valid, {time.time()-t0:.0f}s")
    if "C" not in skip:
        log("== C. integer as BIP-39 entropy ==")
        family_C(lists)
        CK.flush()
        log(f"  C done: {S.c.get('C_mnemonics')} mnemonics, {time.time()-t0:.0f}s")
    if "D" not in skip:
        log("== D. old Electrum index / hex seed ==")
        family_D(lists)
        CK.flush()
        log(f"  D done: {S.c.get('D_word_windows')} word windows, {S.c.get('D_hex_seeds')} hex seeds, {time.time()-t0:.0f}s")
    if "E" not in skip:
        log("== E. numbers as HD path components ==")
        family_E(lists)
        CK.flush()
        log(f"  E done: {S.c.get('E_seeds')} seeds x {S.c.get('E_paths')} paths, {time.time()-t0:.0f}s")
    if "F" not in skip:
        log("== F. digit strings as brainwallet passphrases (overlap, completeness) ==")
        family_F(lists)
        CK.flush()
        log(f"  F done: {S.c.get('F_phrases')} phrases, {time.time()-t0:.0f}s")

    log("== summary ==")
    log(f"  counts: {S.fmt()}, addresses_checked_total={CK.n_checked}")
    log(f"  hits: {len(S.hits)}")
    with open(a.hits, "w") as f:
        f.write("family\tderivation\ttype\taddress\tbalance_sats\tin_richlist\tpriv_hex\n")
        for r in S.hits:
            f.write(f"{r['family']}\t{r['derivation']}\t{r['type']}\t{r['address']}\t{r['balance_sats']}\t{r.get('in_richlist')}\t{r['priv']}\n")
    for r in S.hits:
        log(f"  HIT {r}")
    log(f"  elapsed {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
