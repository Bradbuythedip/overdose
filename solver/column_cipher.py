#!/usr/bin/env python3
"""
Left-edge / right-edge column ciphers over the article's printed lines.

WHY THE EDGES ARE INTERESTING HERE
----------------------------------
The Overdose pages are not set flush-left. Whole blocks are centred or ragged
on BOTH sides -- page 76's opening block steps in and out line by line -- so
the first words form one visible jagged column down the page and the last words
form another. Reading down an edge is the classic null cipher, and Keiser's
tweet says the key is "encoded in this piece".

This was only ever applied to the HIGHLIGHT catalogue. The body prose is new.

article_transcript.txt preserves the printed line breaks (that is why it was
transcribed by eye rather than taken from OCR, which reflows), so the edges can
be read off it exactly. The line breaks are cross-checked against the number of
text lines the image segmentation finds, so a transcription slip shows up
rather than silently shifting every column entry.

Readings produced, per page and for the whole article, forward and reversed:
  first word / last word of each line
  first letter / last letter of each line
  first word of each sentence, of each paragraph
  alternating lines (odd only, even only) -- the George Sand cipher reads
  alternate lines, and it is in this puzzle's documented lineage

  python3 column_cipher.py --transcript article_transcript.txt --out /tmp/cols.txt
"""
import argparse, re, sys


def parse(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    pages, it = [], iter(parts[1:])
    for num, body in zip(it, it):
        lines = [l.rstrip() for l in body.splitlines()]
        lines = [l for l in lines if l.strip()]
        pages.append((num, lines))
    return pages


def words(s):
    return re.findall(r"[A-Za-z0-9$%'-]+", s)


def readings(lines, tag):
    """Yield (name, string) for every edge reading of one block of lines."""
    ws = [words(l) for l in lines]
    ws = [w for w in ws if w]
    if len(ws) < 3:
        return

    yield_list = []

    def emit(name, seq):
        if not seq:
            return
        yield_list.append((f"{tag}:{name}", " ".join(seq)))
        yield_list.append((f"{tag}:{name}:tight", "".join(seq)))
        yield_list.append((f"{tag}:{name}:rev", " ".join(reversed(seq))))

    first = [w[0] for w in ws]
    last = [w[-1] for w in ws]
    emit("first_word", first)
    emit("last_word", last)
    emit("first_word_odd", first[0::2])
    emit("first_word_even", first[1::2])
    emit("last_word_odd", last[0::2])
    emit("last_word_even", last[1::2])

    fl = "".join(w[0][0] for w in ws)
    ll = "".join(w[-1][-1] for w in ws)
    yield_list.append((f"{tag}:first_letter", fl))
    yield_list.append((f"{tag}:first_letter:rev", fl[::-1]))
    yield_list.append((f"{tag}:last_letter", ll))
    yield_list.append((f"{tag}:last_letter:rev", ll[::-1]))
    yield_list.append((f"{tag}:first_letter_odd", "".join(w[0][0] for w in ws[0::2])))
    yield_list.append((f"{tag}:first_letter_even", "".join(w[0][0] for w in ws[1::2])))
    return yield_list


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pages = parse(a.transcript)
    allrows = []
    named = []

    for num, lines in pages:
        r = readings(lines, f"p{num}")
        if r:
            named += r
        allrows += lines
    r = readings(allrows, "ALL")
    if r:
        named += r

    # sentences / paragraphs across the article
    body = " ".join(allrows)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    sw = [words(s) for s in sents]
    sw = [w for w in sw if w]
    if sw:
        named.append(("ALL:sentence_first_word", " ".join(w[0] for w in sw)))
        named.append(("ALL:sentence_first_letter", "".join(w[0][0] for w in sw)))
        named.append(("ALL:sentence_last_word", " ".join(w[-1] for w in sw)))

    out = set()
    for name, s in named:
        s = s.strip()
        if not s or len(s) > 400:
            continue
        for v in (s, s.lower(), s.upper(), s.title()):
            out.add(v)
        nop = re.sub(r"[^\w\s]", "", s)
        out.add(nop)
        out.add(nop.lower())
        out.add(re.sub(r"\s+", "", s))
        out.add(re.sub(r"\s+", "", s).lower())

    out = {x for x in out if 3 <= len(x) <= 400}
    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")

    sys.stderr.write(f"pages: {[(n, len(l)) for n, l in pages]}\n")
    sys.stderr.write(f"{len(named)} named readings -> {len(out):,} phrases -> {a.out}\n\n")
    for name, s in named:
        if ":tight" in name or ":rev" in name:
            continue
        sys.stderr.write(f"  {name:28} {s[:150]}\n")


if __name__ == "__main__":
    main()
