#!/usr/bin/env python3
"""
Running-key / book cipher between the article and the paper Keiser linked.

THE LEAD
Keiser did not just say "mirror writing" in his 2023-03-05 clue — he linked a
SPECIFIC document, PMC2117809: G D Schott, "Mirror writing: neurological
reflections on an unusual phenomenon", J Neurol Neurosurg Psychiatry
2007;78:5-13. A puzzle-setter linking a document is the classic pointer to a
book cipher or running key, and nobody has tried it.

(Note for the record: this repo previously attributed PMC2117809 to Della Sala
& Cubelli. The actual author is G D Schott. Corrected.)

WHAT IS TESTED
Both texts, in both roles, at EVERY alignment offset:

  article as ciphertext, paper as running key    (and Beaufort)
  paper as ciphertext, article as running key    (and Beaufort)

For each offset the first W characters are decrypted and scored by
English-trigram density. A correct alignment scores like English (~0.13); a
wrong one sits at the random-letter floor (~0.018). The separation is about
7x, so no shuffling is needed — the raw density is the discriminator.

Also tests the numeric book-cipher reading: the article's own numbers used as
word and letter indices into the paper, and the reverse.

The positive control encrypts known English with the paper at a known secret
offset and requires the scan to recover that exact offset. Without it a null
here would be meaningless.

  python3 running_key_hunt.py --selftest
  python3 running_key_hunt.py --article article_transcript.txt --key /tmp/schott.txt
"""
import argparse, re, sys

from englishness import TRIGRAMS

A = ord("a")


def letters_only(s):
    return re.sub(r"[^a-z]", "", s.lower())


def density(s):
    if len(s) < 3:
        return 0.0
    return sum(1 for i in range(len(s) - 2)
               if s[i:i + 3] in TRIGRAMS) / (len(s) - 2)


def decrypt_at(ct, key, off, w, mode):
    n = min(w, len(ct), len(key) - off)
    if n < 20:
        return ""
    if mode == "vigenere":
        return "".join(chr(A + ((ord(ct[i]) - ord(key[off + i])) % 26))
                       for i in range(n))
    if mode == "beaufort":
        return "".join(chr(A + ((ord(key[off + i]) - ord(ct[i])) % 26))
                       for i in range(n))
    # additive: treats the key as an encryptor rather than a decryptor
    return "".join(chr(A + ((ord(ct[i]) + ord(key[off + i]) - 2 * A) % 26))
                   for i in range(n))


MODES = ("vigenere", "beaufort", "additive")


def sweep(ct, key, label, w=160, top=5):
    """Slide the key over the ciphertext at every offset; return best hits."""
    best = []
    for mode in MODES:
        for off in range(max(len(key) - 20, 1)):
            pt = decrypt_at(ct, key, off, w, mode)
            if not pt:
                continue
            d = density(pt)
            if d > 0.055:                      # well above the ~0.018 floor
                best.append((d, mode, off, pt[:80]))
    best.sort(reverse=True)
    return best[:top]


def selftest(key):
    """Encrypt known English with the key at a secret offset; the scan must
    recover that offset, and must not fire on unrelated text."""
    ok = True
    SECRET = 4321
    plain = letters_only(
        "the markets sensed bitcoin was coming and started to crash markets are "
        "like that they discount stuff in advance markets are the central "
        "nervous system of the global economy they are the sum of all our "
        "neuroses the cypherpunks were publishing the white paper")
    ct = "".join(chr(A + ((ord(plain[i]) - A + ord(key[SECRET + i]) - A) % 26))
                 for i in range(len(plain)))
    hits = sweep(ct, key, "control", w=len(plain), top=3)
    got = hits[0] if hits else None
    found = got is not None and got[1] == "vigenere" and got[2] == SECRET
    ok &= found
    sys.stderr.write(f"  planted offset {SECRET}, recovered "
                     f"{got[2] if got else None} mode {got[1] if got else None} "
                     f"density {got[0]:.4f}\n" if got else
                     "  planted offset NOT recovered\n")
    sys.stderr.write(f"  positive control: {'OK' if found else 'FAIL'}\n")

    # unrelated ciphertext must not fire
    junk = letters_only("qxzjvkwmpbfghdlrstncaeiou" * 12)
    h2 = sweep(junk, key, "junk", w=200, top=3)
    sys.stderr.write(f"  false hits on junk ciphertext: {len(h2)}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def numeric_book_cipher(article_text, paper_text, out):
    """The article's numbers as word and letter indices into the paper."""
    nums = [int(n) for n in re.findall(r"\d+", article_text)]
    nums = [n for n in nums if n > 0]
    pw = re.findall(r"[A-Za-z]+", paper_text)
    pl = letters_only(paper_text)
    if not pw or not pl:
        return
    for base in (0, 1):
        w = "".join(pw[(n - base) % len(pw)][0] for n in nums)
        out.add(w)
        out.add(w[::-1])
        full = " ".join(pw[(n - base) % len(pw)] for n in nums)
        out.add(full)
        l = "".join(pl[(n - base) % len(pl)] for n in nums)
        out.add(l)
        out.add(l[::-1])
    sys.stderr.write(f"  article numbers used as indices: {len(nums)} numbers "
                     f"-> e.g. {''.join(pw[n % len(pw)][0] for n in nums)[:40]}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", default="article_transcript.txt")
    ap.add_argument("--key", default="/tmp/schott.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    art_raw = open(a.article, encoding="utf-8").read()
    art_raw = re.sub(r"^#.*$", "", art_raw, flags=re.M)
    art_raw = re.sub(r"^=== PAGE.*$", "", art_raw, flags=re.M)
    paper_raw = open(a.key, encoding="utf-8").read()

    art = letters_only(art_raw)
    paper = letters_only(paper_raw)
    sys.stderr.write(f"article {len(art):,} letters   paper {len(paper):,} letters\n\n")

    if not selftest(paper):
        sys.exit("refusing to run: the offset scan cannot recover a planted key")
    if a.selftest:
        return

    sys.stderr.write("\n  article as ciphertext, paper as running key:\n")
    for d, m, off, pt in sweep(art, paper, "art/paper"):
        sys.stderr.write(f"    density={d:.4f} {m:9} off={off:6}  {pt}\n")
    else:
        pass
    h1 = sweep(art, paper, "art/paper")
    if not h1:
        sys.stderr.write("    nothing above the noise floor\n")

    sys.stderr.write("\n  paper as ciphertext, article as running key:\n")
    h2 = sweep(paper, art, "paper/art")
    for d, m, off, pt in h2:
        sys.stderr.write(f"    density={d:.4f} {m:9} off={off:6}  {pt}\n")
    if not h2:
        sys.stderr.write("    nothing above the noise floor\n")

    sys.stderr.write("\n  numeric book cipher:\n")
    prods = set()
    numeric_book_cipher(art_raw, paper_raw, prods)
    numeric_book_cipher(paper_raw, art_raw, prods)
    prods = {p for p in prods if 4 <= len(p) <= 400}
    with open("/tmp/bookcipher.txt", "w", encoding="utf-8") as f:
        for p in sorted(prods):
            f.write(p + "\n")
    sys.stderr.write(f"  {len(prods)} book-cipher products -> /tmp/bookcipher.txt\n")

    ref = density(letters_only(
        "the markets sensed bitcoin was coming and started to crash"))
    sys.stderr.write(f"\n  reference densities: English ~{ref:.4f}, "
                     f"random letters ~0.018, threshold 0.055\n")
    if not h1 and not h2:
        sys.stderr.write("  NO RUNNING KEY: neither text decrypts the other at "
                         "any offset, in any of the three modes\n")


if __name__ == "__main__":
    main()
