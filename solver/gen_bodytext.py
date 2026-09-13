#!/usr/bin/env python3
"""
Build a passphrase corpus from the article's RUNNING BODY TEXT.

THE GAP THIS FILLS
------------------
The 8,490-phrase corpus in this repo was built from the highlighted/bold
phrase catalogue. Spot-checking it against a fresh OCR transcript shows the
ordinary body sentences were never in it at all:

    "tied to a burning stake"                     -> 20 variants present
    "Open your heart to Bitcoin"                  -> 34 variants present
    "A monetary defibrillator to the treasure chest" -> 0
    "nailing the Vatican with ultimatums"         -> 0
    "have dulled shitcoiners"                     -> 0
    "Don't believe me?"                           -> 0

So every prior sweep, however deep in the derivation dimension, was blind to
most of the prose Keiser actually wrote. This enumerates it.

Source is tesseract at native resolution with --psm 6, which reads the body
text well but mangles the highlighted runs (those are already covered by the
existing corpus, so the two are complementary rather than redundant).

Emits, for each of sentences / printed lines / paragraphs / word n-grams:
as-written, lowercase, uppercase, title case, punctuation-stripped, and
whitespace-stripped forms.

  python3 gen_bodytext.py --ocr /tmp/ocr --out /tmp/bodytext_phrases.txt
"""
import argparse, glob, os, re, sys

# Lines that are page furniture or OCR noise rather than prose.
JUNK = re.compile(r"^[\s|{}\[\]<>=~`'\"^_.,;:!?/\\*+-]*$")
FURNITURE = re.compile(r"^(OVERDOSE|Bitcoin Magazine.*|El Salvador|\d{1,3})$", re.I)


def clean_line(s):
    """Strip the column rules and marginalia tesseract picks up as text."""
    s = s.replace("—", " - ").replace("’", "'").replace("“", '"')
    s = s.replace("”", '"').replace("‘", "'")
    # leading gutter marks: '| U ', '{ ', '. ', '\ ', 'e ', 'i ' etc.
    s = re.sub(r"^[\s|{}\[\]\\/<>=~`^_]+", "", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


def usable(s):
    if len(s) < 4 or JUNK.match(s) or FURNITURE.match(s):
        return False
    letters = sum(c.isalpha() for c in s)
    # prose is mostly letters; OCR garbage from the graphics is mostly not
    return letters >= 4 and letters / max(len(s), 1) >= 0.55


def variants(s):
    s = s.strip()
    if not s:
        return []
    out = {s, s.lower(), s.upper(), s.title()}
    nop = re.sub(r"[^\w\s]", "", s)
    out |= {nop, nop.lower(), nop.upper()}
    out.add(re.sub(r"\s+", "", s))
    out.add(re.sub(r"\s+", "", s).lower())
    return [x for x in out if 3 <= len(x) <= 200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr", default="/tmp/ocr")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-n", type=int, default=2)
    ap.add_argument("--max-n", type=int, default=12)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.ocr, "n*.txt")))
    if not files:
        sys.exit(f"no OCR transcripts in {a.ocr} (expected n<page>.txt)")

    phrases = set()
    n_lines = n_sent = n_ngram = 0

    for fp in files:
        raw = open(fp, encoding="utf-8", errors="replace").read()
        lines = [clean_line(l) for l in raw.splitlines()]
        lines = [l for l in lines if usable(l)]
        n_lines += len(lines)
        for l in lines:
            phrases.update(variants(l))

        body = " ".join(lines)

        # sentences
        for s in re.split(r"(?<=[.!?])\s+", body):
            s = s.strip()
            if usable(s):
                n_sent += 1
                phrases.update(variants(s))

        # paragraphs: runs of consecutive lines between blank-ish breaks
        for para in re.split(r"\n\s*\n", raw):
            pl = [clean_line(l) for l in para.splitlines()]
            pl = [l for l in pl if usable(l)]
            if len(pl) >= 2:
                phrases.update(variants(" ".join(pl)))

        # word n-grams over the page's running text
        words = re.findall(r"[A-Za-z0-9'$-]+", body)
        for n in range(a.min_n, a.max_n + 1):
            for i in range(len(words) - n + 1):
                g = " ".join(words[i:i + n])
                n_ngram += 1
                phrases.update(variants(g))

        sys.stderr.write(f"  {os.path.basename(fp)}: {len(lines)} usable lines, "
                         f"{len(words)} words\n")

    # also the whole article as one blob, and its per-page blobs
    allbody = []
    for fp in files:
        ls = [clean_line(l) for l in
              open(fp, encoding="utf-8", errors="replace").read().splitlines()]
        ls = [l for l in ls if usable(l)]
        allbody.append(" ".join(ls))
        phrases.update(variants(" ".join(ls)))
    phrases.update(variants(" ".join(allbody)))

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(phrases):
            f.write(p + "\n")
    sys.stderr.write(f"\n{n_lines} lines, {n_sent} sentences, {n_ngram} n-grams "
                     f"-> {len(phrases):,} unique phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
