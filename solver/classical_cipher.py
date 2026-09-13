#!/usr/bin/env python3
"""
Classical keyword ciphers over the article, keyed on Keiser's own clue words.

WHY THIS IS NEW
"El Salvador is a clue" has only ever been used here as a hash input or a KDF
salt. It was never used as what a clue word usually IS in a puzzle: the KEY to
a classical cipher. Vigenere, Beaufort, autokey and running-key over the
article text, keyed on EL SALVADOR / OVERDOSE / MAX KEISER / MIRROR, have not
been tried at all.

Two oracles are applied to every decryption, neither needing chain access:

  1. englishness -- does the plaintext read as English? A correct keyword makes
     the output read; a wrong one leaves it at the noise floor. Judged against
     the same operation applied to a shuffled key, so the null matches.
  2. the key-format checksum -- does the output contain a checksum-valid WIF,
     BIP38 or mini key? A 1-in-4-billion filter for WIF/BIP38.

Both are cheap, so the whole keyword x cipher x scope space is exhaustible.

  python3 classical_cipher.py --selftest
  python3 classical_cipher.py --transcript article_transcript.txt
"""
import argparse, random, re, sys

from englishness import letters, zscore
from wif_hunt import scan as wif_scan

A = ord("a")


def vigenere(text, key, decrypt=True):
    out, ki = [], 0
    for c in text:
        if not c.isalpha():
            continue
        k = ord(key[ki % len(key)]) - A
        v = ord(c.lower()) - A
        out.append(chr(A + ((v - k) % 26 if decrypt else (v + k) % 26)))
        ki += 1
    return "".join(out)


def beaufort(text, key):
    out, ki = [], 0
    for c in text:
        if not c.isalpha():
            continue
        k = ord(key[ki % len(key)]) - A
        v = ord(c.lower()) - A
        out.append(chr(A + ((k - v) % 26)))
        ki += 1
    return "".join(out)


def autokey(text, key):
    """Vigenere autokey decryption: recovered plaintext extends the key."""
    t = [c.lower() for c in text if c.isalpha()]
    k = list(key)
    out = []
    for i, c in enumerate(t):
        kc = ord(k[i]) - A if i < len(k) else ord(out[i - len(key)]) - A
        p = chr(A + ((ord(c) - A - kc) % 26))
        out.append(p)
        if i >= len(k):
            k.append(p)
    return "".join(out)


def running_key(text, keytext):
    """Vigenere with a long key: the article decrypted against another text."""
    t = [c.lower() for c in text if c.isalpha()]
    k = [c.lower() for c in keytext if c.isalpha()]
    if not k:
        return ""
    return "".join(chr(A + ((ord(c) - A - (ord(k[i % len(k)]) - A)) % 26))
                   for i, c in enumerate(t))


CIPHERS = {
    "vigenere": lambda t, k: vigenere(t, k, True),
    "vigenere_enc": lambda t, k: vigenere(t, k, False),
    "beaufort": beaufort,
    "autokey": autokey,
}

KEYWORDS = [
    "elsalvador", "salvador", "elzonte", "bukele", "nayibbukele",
    "overdose", "maxkeiser", "keiser", "stacyherbert", "mirror",
    "mirrorwriting", "georgesand", "sand", "bitcoin", "toxic",
    "hyperbitcoinized", "volcano", "volcanobonds", "twentybtc", "satoshi",
]


def selftest():
    """A known keyword must be recovered from a known plaintext, and the
    englishness scorer must separate the right key from wrong ones."""
    rng = random.Random(5)
    plain = ("thequickbrownfoxjumpsoverthelazydog" * 12
             + "andthemarketssensedbitcoinwascomingandstartedtocrash" * 6)
    ct = vigenere(plain, "elsalvador", decrypt=False)
    back = vigenere(ct, "elsalvador", decrypt=True)
    ok = back == plain
    sys.stderr.write(f"  vigenere round-trip: {'OK' if ok else 'FAIL'}\n")

    zr, _, _ = zscore(back, 60, rng)
    zw, _, _ = zscore(vigenere(ct, "wrongkeyxx", decrypt=True), 60, rng)
    sys.stderr.write(f"  englishness with the RIGHT key: z = {zr:+.1f}\n")
    sys.stderr.write(f"  englishness with a WRONG key:   z = {zw:+.1f}\n")
    sep = zr > 10 and zr > zw * 2
    ok &= sep
    sys.stderr.write(f"  scorer separates right from wrong key: "
                     f"{'OK' if sep else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("refusing to run: cipher or scorer is not working")
    if a.selftest:
        return

    rng = random.Random(20260913)
    raw = open(a.transcript, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    pages, it = [], iter(parts[1:])
    for num, body in zip(it, it):
        pages.append((num, " ".join(l.strip() for l in body.splitlines() if l.strip())))
    scopes = [("ALL", " ".join(t for _, t in pages))] + [(f"p{n}", t) for n, t in pages]

    results, wifhits = [], []
    for tag, text in scopes:
        t = letters(text)
        if len(t) < 100:
            continue
        for kw in KEYWORDS:
            for cname, fn in CIPHERS.items():
                try:
                    pt = fn(t, kw)
                except Exception:
                    continue
                if len(pt) < 100:
                    continue
                z, _, _ = zscore(pt, 25, rng)
                results.append((z, tag, kw, cname, pt[:90]))
                wif_scan(pt, f"{tag}/{cname}/{kw}", wifhits)
        # running key: the article against each page, and against itself offset
        for kn, ktext in pages:
            pt = running_key(t, ktext)
            if len(pt) >= 100:
                z, _, _ = zscore(pt, 25, rng)
                results.append((z, tag, f"runkey:p{kn}", "running", pt[:90]))
                wif_scan(pt, f"{tag}/running/p{kn}", wifhits)

    results.sort(reverse=True)
    sys.stderr.write(f"\n{len(results)} decryptions "
                     f"({len(KEYWORDS)} keywords x {len(CIPHERS)} ciphers x "
                     f"{len(scopes)} scopes, plus running-key)\n\n")
    sys.stderr.write("  top 10 by englishness z:\n")
    for z, tag, kw, cname, s in results[:10]:
        sys.stderr.write(f"    z={z:+6.2f}  {tag:5} {cname:12} {kw:16} {s[:60]}\n")

    strong = [h for h in wifhits if h[4] != "casascius_mini"]
    sys.stderr.write(f"\n  checksum-valid WIF/BIP38 in any decryption: {len(strong)}\n")
    for h in strong:
        sys.stderr.write(f"    *** {h}\n")

    best = results[0][0] if results else 0
    sys.stderr.write(f"\n  best z = {best:+.2f}. For reference the article's own\n"
                     f"  plaintext scores about +70 and random letters about 0.\n  ")
    sys.stderr.write("NO KEYWORD CIPHER: nothing decrypts to English\n"
                     if best < 10 else
                     "SOMETHING DECRYPTS -- inspect the top rows by hand\n")


if __name__ == "__main__":
    main()
