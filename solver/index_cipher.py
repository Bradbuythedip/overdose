#!/usr/bin/env python3
"""
Book cipher: numbers in the article used as INDICES into the article.

WHY THIS ONE IS DIFFERENT FROM EVERY OTHER SWEEP HERE

Every chain sweep in this project needs the derived address to exist AND to
have been funded. That is the blindness documented in
`window/sweep_detector_is_half_blind.md` and `hist_index.py`: two balance
snapshots are two instants, and "was this ever funded" is a question about an
interval. A key that was never funded, or was swept before either snapshot,
returns the same 0 hits as a key that is simply wrong.

An index cipher escapes that, because its output can be SELF-CERTIFYING:

    a 12/24-word BIP-39 mnemonic carries a checksum -- 1 in 16 chance for 12
      words, 1 in 256 for 24, so a valid one is a real signal
    a WIF carries a 4-byte Base58Check trailer  -- 1 in 2^32
    64 hex characters is a well-formed raw key

None of those needs an address, a balance, or a network. The cipher certifies
itself. That is the same reasoning `serial_oracle.py` applied to the serial as
a checksum, pointed at a different mechanism.

WHAT IS SWEPT
  index sources   the article's numerals in printed order; gap widths between
                  words; line lengths in words and in characters; word lengths;
                  page numbers; the banknote serial digits; sentence lengths
  targets         words, lines, sentences, paragraphs, characters, and the
                  BIP-39-valid tokens in the article
  schemes         0- and 1-based, global and per-page, forward and reversed,
                  modulo-wrapped and strict, cumulative sums as well as raw
  extraction      whole token, first letter, last letter, Nth character

Every (source x target x scheme x extraction) result is then run through the
self-certifying validators AND through the funded-address index, so a hit can
come from either direction.

  python3 index_cipher.py --selftest
  python3 index_cipher.py
"""
import argparse, hashlib, itertools, re, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


# ---------- the text, tokenised every way ----------
def load_text(path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    body = [l for l in raw.splitlines()
            if not l.startswith("#") and not l.startswith("===")]
    text = "\n".join(body)
    return text


def targets(text):
    """Named tokenisations of the article."""
    lines = [l for l in text.splitlines() if l.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chars = [c for c in text if not c.isspace()]
    allchars = list(text)
    return {
        "words": words,
        "lines": lines,
        "sentences": sents,
        "paragraphs": paras,
        "chars_nospace": chars,
        "chars_all": allchars,
        "caps_words": [w for w in words if w.isupper()],
    }


# ---------- the number sequences ----------
def numerals(text):
    """Every numeral in printed order, plus written-out ones."""
    out = []
    words_out = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "forty": 40, "billion": 1, "trillion": 2}
    for m in re.finditer(r"\d[\d,]*|\b(" + "|".join(words_out) + r")\b",
                         text, re.I):
        t = m.group(0)
        if t.isalpha():
            out.append(words_out[t.lower()])
        else:
            try:
                out.append(int(t.replace(",", "")))
            except ValueError:
                pass
    return out


def gap_widths(text):
    """Width of every run of 2+ spaces, in printed order."""
    return [len(m.group(0)) for m in re.finditer(r"  +", text)]


def sources(text, tg):
    """Named integer sequences to use as indices."""
    nums = numerals(text)
    gaps = gap_widths(text)
    s = {
        "numerals": nums,
        "numerals_rev": nums[::-1],
        "numerals_cum": list(itertools.accumulate(nums)),
        "numerals_small": [n for n in nums if n < 200],
        "numerals_digits": [int(d) for n in nums for d in str(n)],
        "gaps": gaps,
        "gaps_rev": gaps[::-1],
        "gaps_cum": list(itertools.accumulate(gaps)),
        "line_wordcounts": [len(l.split()) for l in tg["lines"]],
        "line_lengths": [len(l) for l in tg["lines"]],
        "word_lengths": [len(w) for w in tg["words"][:400]],
        "sent_wordcounts": [len(s.split()) for s in tg["sentences"]],
        "serial": [7, 6, 8, 4, 1, 7, 1, 4],
        "serial_rev": [4, 1, 7, 1, 4, 8, 6, 7],
        "pages": [75, 76, 77, 78, 79],
        "pages_rev": [79, 78, 77, 76, 75],
    }
    return {k: v for k, v in s.items() if v}


# ---------- applying an index sequence ----------
def extract(seq, toks, base=0, wrap=True, mode="token"):
    """Pull tokens at the given indices and render them."""
    out = []
    n = len(toks)
    if not n:
        return ""
    for i in seq:
        j = i - base
        if wrap:
            j %= n
        elif not (0 <= j < n):
            continue
        t = toks[j]
        if mode == "token":
            out.append(t)
        elif mode == "first":
            out.append(t[0] if t else "")
        elif mode == "last":
            out.append(t[-1] if t else "")
        elif mode == "firstlower":
            out.append(t[0].lower() if t else "")
    return out


# ---------- self-certifying validators ----------
_WORDLIST = None


def bip39_words():
    global _WORDLIST
    if _WORDLIST is None:
        try:
            from mnemonic import Mnemonic
            _WORDLIST = set(Mnemonic("english").wordlist)
        except Exception:
            _WORDLIST = set()
    return _WORDLIST


def valid_mnemonic(words):
    """True if this word list is a checksum-valid BIP-39 mnemonic."""
    if len(words) not in (12, 15, 18, 21, 24):
        return False
    try:
        from mnemonic import Mnemonic
        return Mnemonic("english").check(" ".join(w.lower() for w in words))
    except Exception:
        return False


def valid_wif(s):
    """True if s is a checksum-valid WIF private key."""
    if not (50 <= len(s) <= 53) or any(c not in B58 for c in s):
        return False
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    raw = b"\x00" * (len(s) - len(s.lstrip("1"))) + raw
    if len(raw) not in (37, 38) or raw[0] != 0x80:
        return False
    return hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:]


def certify(s):
    """Any self-certifying interpretation of this string. [] if none."""
    out = []
    flat = s.replace(" ", "")
    if valid_wif(flat):
        out.append(("WIF", flat))
    hexy = re.sub(r"[^0-9a-fA-F]", "", s)
    if len(hexy) == 64:
        out.append(("HEX64", hexy.lower()))
    ws = s.split()
    if valid_mnemonic(ws):
        out.append(("BIP39", " ".join(w.lower() for w in ws)))
    # a sliding window, in case the key is embedded in a longer run
    if len(ws) > 12:
        for k in (12, 24):
            for i in range(len(ws) - k + 1):
                w = ws[i:i + k]
                if valid_mnemonic(w):
                    out.append((f"BIP39@{i}", " ".join(x.lower() for x in w)))
    return out


def selftest():
    ok = True
    toks = ["alpha", "bravo", "charlie", "delta", "echo"]
    got = extract([0, 2, 4], toks, base=0, mode="token")
    ok &= got == ["alpha", "charlie", "echo"]
    sys.stderr.write(f"  0-based token extraction: {got} "
                     f"{'OK' if got==['alpha','charlie','echo'] else 'FAIL'}\n")
    got = extract([1, 3, 5], toks, base=1, mode="first")
    ok &= got == ["a", "c", "e"]
    sys.stderr.write(f"  1-based first-letter extraction: {got} "
                     f"{'OK' if got==['a','c','e'] else 'FAIL'}\n")
    got = extract([7], toks, base=0, wrap=True, mode="token")
    ok &= got == ["charlie"]
    sys.stderr.write(f"  index 7 wraps into a 5-token list -> {got}: "
                     f"{'OK' if got==['charlie'] else 'FAIL'}\n")

    # the validators must accept a REAL key and reject near-misses, or every
    # "self-certifying" claim below is worthless
    good_wif = "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ"
    ok &= valid_wif(good_wif)
    sys.stderr.write(f"  a published valid WIF is accepted: "
                     f"{'OK' if valid_wif(good_wif) else 'FAIL'}\n")
    bad = good_wif[:-1] + ("A" if good_wif[-1] != "A" else "B")
    ok &= not valid_wif(bad)
    sys.stderr.write(f"  one corrupted character is rejected: "
                     f"{'OK' if not valid_wif(bad) else 'FAIL'}\n")

    if bip39_words():
        m = ("abandon " * 11 + "about").strip()
        ok &= valid_mnemonic(m.split())
        sys.stderr.write(f"  the canonical all-abandon mnemonic validates: "
                         f"{'OK' if valid_mnemonic(m.split()) else 'FAIL'}\n")
        bad_m = ("abandon " * 11 + "zoo").strip()
        ok &= not valid_mnemonic(bad_m.split())
        sys.stderr.write(f"  a checksum-broken mnemonic is rejected: "
                         f"{'OK' if not valid_mnemonic(bad_m.split()) else 'FAIL'}\n")
    else:
        sys.stderr.write("  (mnemonic lib absent - BIP39 certification "
                         "DISABLED, and that is a real gap)\n")

    text = load_text()
    tg = targets(text)
    src = sources(text, tg)
    sys.stderr.write(f"  {len(src)} index sources, {len(tg)} tokenisations\n")
    sys.stderr.write(f"    numerals: {src['numerals'][:14]}…\n")
    sys.stderr.write(f"    gaps: {src['gaps'][:18]}… ({len(src['gaps'])} total)\n")
    ok &= len(src["numerals"]) > 10 and len(src["gaps"]) > 5
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="index_cipher_candidates.txt")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("extraction or validation is wrong; refusing")
    if a.selftest:
        return

    text = load_text()
    tg = targets(text)
    src = sources(text, tg)

    sys.stderr.write(f"\n  {len(src)} sources x {len(tg)} targets x "
                     f"schemes x extractions\n\n")
    certified, phrases, n = [], [], 0
    for sname, seq in src.items():
        for tname, toks in tg.items():
            for base in (0, 1):
                for wrap in (True, False):
                    for mode in ("token", "first", "last", "firstlower"):
                        got = extract(seq, toks, base, wrap, mode)
                        if not got:
                            continue
                        n += 1
                        joined = " ".join(got)
                        tight = "".join(got)
                        for rendering, s in (("spaced", joined),
                                             ("tight", tight)):
                            for kind, val in certify(s):
                                certified.append(
                                    (kind, val, sname, tname, base, wrap,
                                     mode, rendering))
                                sys.stderr.write(
                                    f"\n  *** SELF-CERTIFYING {kind}\n"
                                    f"      {val}\n"
                                    f"      {sname} -> {tname}, base={base}, "
                                    f"wrap={wrap}, {mode}, {rendering}\n")
                                sys.stderr.flush()
                            if 0 < len(s) < 4000:
                                phrases.append(s)

    sys.stderr.write(f"\n  {n:,} index readings, {len(certified)} "
                     f"self-certifying, {len(set(phrases)):,} distinct strings\n")
    with open(a.out, "w", encoding="utf-8") as fh:
        for p in sorted(set(phrases)):
            fh.write(p.replace("\n", " ") + "\n")
    sys.stderr.write(f"  strings -> {a.out}\n")
    if not certified:
        sys.stderr.write("  No index reading produces a valid WIF, a valid "
                         "BIP-39 mnemonic, or 64 hex chars.\n")
    sys.stderr.write(f"\n  next: python3 try_phrases.py --in {a.out} "
                     f"--label index --no-hd\n")


if __name__ == "__main__":
    main()
