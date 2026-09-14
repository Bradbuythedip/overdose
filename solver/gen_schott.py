#!/usr/bin/env python3
"""
The Schott mirror-writing paper as the keyed object: serial-digit pointers,
Sand-style alternate reads, and the Leonardo vocabulary.

WHY THE PAPER IS A REAL TARGET AND NOT A THEME
On 2023-03-05 Keiser did not merely say "mirror writing" — he linked a specific
document, PMC2117809 (G D Schott, "Mirror writing: neurological reflections on
an unusual phenomenon", J Neurol Neurosurg Psychiatry 2007;78:5-13). A setter
who links one specific document is doing what book-cipher setters do: naming
the key text. Prior work here used the paper only as an ENGLISH BASELINE for
the anomaly scan, and touched the paper-as-key-into-the-article direction. The
directions below were never generated.

The paper is the canonical Leonardo da Vinci reference — he is named throughout
— which is the other half of the same clue rather than a separate one.

WHAT IS ENUMERATED

  serial pointers   the note's digits 76841714 as INDICES into the paper, under
                    every grouping a person would read them in: single digits,
                    pairs, triples both ways, quads, the whole number; plus the
                    serial with its letters valued (C=3, L=12, A=1) and the
                    district 12. Indexed into the paper's words, lines and
                    sentences, 0- and 1-based, forward and mirrored, wrapped.

  Sand reads        the paper's own alternate-line and alternate-sentence
                    readings at steps 2-5 and every offset. This is the device
                    Keiser named, applied to the text he linked rather than to
                    the one he wrote — which is the reading that was missing.

  citation numbers  2007, 78, 5, 13, 2006, 094870, 10.1136 and PMC2117809 are
                    printed identifiers attached to the object he pointed at.

  Leonardo corpus   the paper's title, author, journal, and the mirror-writing
                    vocabulary including the da Vinci forms.

Everything is emitted forward AND reversed, because mirror writing is the
stated clue and this is the document about it.

  python3 gen_schott.py --selftest
  python3 gen_schott.py --out /tmp/schott_phrases.txt
"""
import argparse, re, sys

SERIAL_DIGITS = "76841714"
CITATION = ["2007", "78", "5", "13", "2006", "094870", "10.1136",
            "PMC2117809", "jnnp.2006.094870", "78:5-13"]
LEONARDO = [
    "Leonardo da Vinci", "leonardo da vinci", "Leonardo", "da Vinci",
    "LeonardoDaVinci", "mirror writing", "Mirror writing", "mirrorwriting",
    "G D Schott", "Schott", "GDSchott",
    "Mirror writing: neurological reflections on an unusual phenomenon",
    "J Neurol Neurosurg Psychiatry",
    "neurological reflections on an unusual phenomenon",
]


def groupings(d=SERIAL_DIGITS):
    """Every way a reader would chunk the eight digits into numbers."""
    out = {
        "singles": [int(c) for c in d],
        "pairs": [int(d[i:i + 2]) for i in range(0, len(d), 2)],
        "triples_l": [int(d[0:3]), int(d[3:6]), int(d[6:])],
        "triples_r": [int(d[0:2]), int(d[2:5]), int(d[5:])],
        "quads": [int(d[0:4]), int(d[4:])],
        "whole": [int(d)],
        # letters valued in the alphabet: C=3, L=12, A=1
        "with_letters": [3, 12] + [int(c) for c in d] + [1],
        "district": [12],
    }
    out.update({k + "_rev": v[::-1] for k, v in list(out.items())})
    return out


def corpora(path="schott_full.txt"):
    """Word / line / sentence views of the paper.

    The PDF carries typographic dot-leader rules (". . . . . . . . .") between
    sections. Split naively on sentence punctuation these become hundreds of
    one-character "." sentences — measured, 4 of the first 4 pair-indexed
    sentences were literally ".", so the whole sentence family was reading
    punctuation. Leaders are stripped and punctuation-only units dropped.
    """
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"(?:\.\s){4,}\.?", " ", raw)      # dot-leader rules
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", raw)
    lines = [l.strip() for l in raw.splitlines() if l.strip()
             and re.search(r"[A-Za-z]", l)]
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", raw)
             if x.strip() and len(re.findall(r"[A-Za-z]", x)) >= 3]
    return {"words": words, "lines": lines, "sentences": sents}


def index_readings(idxs, corp):
    """Numbers used as positions into the paper."""
    out = set()
    for cname, seq in corp.items():
        if len(seq) < 2:
            continue
        for base in (0, 1):
            for rev in (False, True):
                src = seq[::-1] if rev else seq
                sel = [src[(v - base) % len(src)] for v in idxs]
                if cname == "words":
                    j = " ".join(sel)
                    out.add(j)
                    out.add(j.lower())
                    out.add("".join(w[0] for w in sel).lower())
                    out.add(j.lower()[::-1])
                else:
                    j = " ".join(s.strip() for s in sel)
                    if len(j) < 4000:
                        out.add(j)
                        out.add(j.lower())
    return out


def sand_reads(corp):
    """Alternate-line and alternate-sentence readings of the PAPER."""
    out = set()
    for cname in ("lines", "sentences"):
        seq = corp[cname]
        for step in (2, 3, 4, 5):
            for off in range(step):
                sel = seq[off::step]
                if not sel:
                    continue
                j = " ".join(s.strip() for s in sel)
                if 20 < len(j) < 60000:
                    out.add(j)
                    out.add(j.lower())
                    # first word of each selected unit, the classic null read
                    fw = [s.split()[0] for s in sel if s.split()]
                    if 3 < len(fw) < 400:
                        out.add(" ".join(fw).lower())
                        out.add("".join(w[0] for w in fw).lower())
    return out


def selftest():
    """Groupings must chunk correctly and indexing must be reproducible."""
    g = groupings()
    ok = (g["singles"] == [7, 6, 8, 4, 1, 7, 1, 4]
          and g["pairs"] == [76, 84, 17, 14]
          and g["triples_l"] == [768, 417, 14]
          and g["quads"] == [7684, 1714]
          and g["whole"] == [76841714]
          and g["singles_rev"] == [4, 1, 7, 1, 4, 8, 6, 7])
    sys.stderr.write(f"  pairs {g['pairs']}  triples {g['triples_l']}  "
                     f"quads {g['quads']}\n")
    sys.stderr.write(f"  grouping arithmetic: {'OK' if ok else 'FAIL'}\n")

    corp = {"words": ["alpha", "bravo", "charlie", "delta", "echo"]}
    r = index_readings([1, 3], corp)
    # 1-based -> bravo, delta ; 0-based -> bravo, delta shifted
    ok2 = any("bravo" in x for x in r)
    sys.stderr.write(f"  index into a 5-word corpus produced {len(r)} "
                     f"readings, contains 'bravo': {'OK' if ok2 else 'FAIL'}\n")

    c = corpora()
    sys.stderr.write(f"  paper: {len(c['words'])} words, {len(c['lines'])} "
                     f"lines, {len(c['sentences'])} sentences\n")
    ok3 = len(c["words"]) > 5000 and any("Leonardo" in w or "Vinci" in w
                                         for w in c["words"])
    sys.stderr.write(f"  paper loaded and names Leonardo: "
                     f"{'OK' if ok3 else 'FAIL'}\n")

    s = sand_reads({"lines": [f"line{i} word" for i in range(10)],
                    "sentences": []})
    ok4 = len(s) > 0
    sys.stderr.write(f"  Sand reads on a 10-line toy: {len(s)} "
                     f"{'OK' if ok4 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok and ok2 and ok3 and ok4
                                      else "FAIL\n"))
    return ok and ok2 and ok3 and ok4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="schott_full.txt")
    ap.add_argument("--out", default="/tmp/schott_phrases.txt")
    ap.add_argument("--maxlen", type=int, default=4096)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("generator fails its controls; refusing to emit")
    if a.selftest:
        return

    corp = corpora(a.paper)
    out = set()

    for gname, idxs in groupings().items():
        out |= index_readings(idxs, corp)
    sys.stderr.write(f"  after serial pointers: {len(out):,}\n")

    out |= sand_reads(corp)
    sys.stderr.write(f"  after Sand reads of the paper: {len(out):,}\n")

    for s in CITATION + LEONARDO:
        for f in (s, s.lower(), s.upper(), s.replace(" ", ""),
                  s.lower().replace(" ", ""), s[::-1], s.lower()[::-1]):
            out.add(f)
    # citation numbers combined, and paired with the serial
    joined = "".join(CITATION[:6])
    for f in (joined, joined[::-1], " ".join(CITATION[:6])):
        out.add(f)
    for s in LEONARDO:
        out.add(f"{s} {SERIAL_DIGITS}")
        out.add(f"{SERIAL_DIGITS} {s}".lower())
    sys.stderr.write(f"  after citation + Leonardo corpus: {len(out):,}\n")

    out = {s.replace("\n", " ").strip() for s in out}
    out = {s for s in out if 0 < len(s) <= a.maxlen}
    with open(a.out, "w", encoding="utf-8") as fh:
        for s in sorted(out):
            fh.write(s + "\n")
    sys.stderr.write(f"\n  {len(out):,} phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
