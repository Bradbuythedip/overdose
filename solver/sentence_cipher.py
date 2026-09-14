#!/usr/bin/env python3
"""
The George Sand device on the AUTHOR's units — sentences and paragraphs.

THE AXIOM THIS RESTS ON
Keiser wrote the words. Bitcoin Magazine's art department did everything else:
the bold, the highlight bars, the kerning, and — decisively — the LINE BREAKS.
An author submitting a manuscript does not control where a line wraps, and a
cipher keyed to line breaks would be destroyed by any reflow, resize or font
change between his draft and the printed page. He could only key a line cipher
to the printed layout by working from proofs, which is a far stronger
assumption than the clue supports.

Every Sand-style test in this project so far — full alternate lines, steps 2-5,
all offsets, per page, forward and mirrored, 1.5M addresses — used the printed
LINE. That is the designer's unit, not the author's.

Sentences and paragraphs are the author's. He decides where a sentence ends;
nobody downstream changes it. So the axiomatically correct form of "read every
other line, in full" is read every other SENTENCE, and that has never been
generated here.

THE NULL
The extraction is scored for hidden English against an OPERATION-MATCHED null:
the same extraction applied to copies of the article with its sentence order
shuffled. A letter-frequency-matched null is not good enough and this project
has the scars to prove it — frequency-matched nulls previously returned
z=+5.6 for every-Nth and z=+18.8 for acrostics, and operation-matched nulls
erased both. Shuffling sentence order preserves every sentence's internal
English while destroying only the thing the cipher would exploit, which is
which sentences the rule selects.

  python3 sentence_cipher.py --selftest
  python3 sentence_cipher.py --out /tmp/sentence_phrases.txt
"""
import argparse, random, re, sys

from englishness import letters, score

WORD = re.compile(r"[A-Za-z'-]+")


def load(path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    pages = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(pages[1:])
    paras, sents = [], []
    for _num, body in zip(it, it):
        # a blank line is the author's paragraph break and survives layout
        for block in re.split(r"\n\s*\n", body):
            flat = " ".join(l.strip() for l in block.splitlines() if l.strip())
            if len(WORD.findall(flat)) < 2:
                continue
            paras.append(flat)
            for s in re.split(r"(?<=[.!?])\s+", flat):
                s = s.strip()
                if len(WORD.findall(s)) >= 1:
                    sents.append(s)
    return sents, paras


def extractions(units, tag):
    """Every Sand-style reading of a list of author units."""
    out = {}
    for step in range(2, 6):
        for off in range(step):
            sel = units[off::step]
            if len(sel) < 3:
                continue
            k = f"{tag}_step{step}_off{off}"
            out[k + "_full"] = " ".join(sel)
            fw = [WORD.findall(s)[0] for s in sel if WORD.findall(s)]
            lw = [WORD.findall(s)[-1] for s in sel if WORD.findall(s)]
            out[k + "_first"] = " ".join(fw)
            out[k + "_last"] = " ".join(lw)
            out[k + "_acro"] = "".join(w[0] for w in fw)
    # whole-sequence readings (step 1) belong here too: they are the controls
    out[f"{tag}_all_full"] = " ".join(units)
    fw = [WORD.findall(s)[0] for s in units if WORD.findall(s)]
    out[f"{tag}_all_first"] = " ".join(fw)
    out[f"{tag}_all_acro"] = "".join(w[0] for w in fw)
    return out


def op_null(units, tag, key, trials, rng):
    """Same extraction, applied to sentence-order-shuffled copies."""
    vals = []
    u = list(units)
    for _ in range(trials):
        rng.shuffle(u)
        e = extractions(u, tag)
        s = letters(e.get(key, ""))
        if len(s) >= 3:
            vals.append(score(s))
    return vals


def z_against(vals, obs):
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)
    sd = var ** 0.5
    return (obs - m) / sd if sd else 0.0


def selftest():
    """The scorer must separate real English from the same words reordered,
    and the operation-matched null must not flag an ordinary reading."""
    sents, paras = load()
    sys.stderr.write(f"  {len(sents)} sentences, {len(paras)} paragraphs\n")
    ok = len(sents) > 50 and len(paras) > 8

    prose = letters(" ".join(sents))
    shuf = list(prose)
    random.Random(1).shuffle(shuf)
    a, b = score(prose), score("".join(shuf))
    sys.stderr.write(f"  positive control, article prose      trigram score "
                     f"{a:.4f}\n")
    sys.stderr.write(f"  negative control, its letters shuffled            "
                     f"{b:.4f}\n")
    ok &= a > 2 * b
    sys.stderr.write(f"  scorer separates English from noise: "
                     f"{'OK' if a > 2 * b else 'FAIL'}\n")

    # An ordinary reading must NOT be called anomalous by the op-matched null.
    rng = random.Random(7)
    key = "sent_step2_off0_full"
    obs = score(letters(extractions(sents, "sent")[key]))
    vals = op_null(sents, "sent", key, 40, rng)
    z = z_against(vals, obs)
    sys.stderr.write(f"  alternate sentences vs shuffled-order null: "
                     f"z={z:+.2f} (must be modest; shuffling order does not "
                     f"change which words appear)\n")
    ok &= abs(z) < 8
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/sentence_phrases.txt")
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("scorer or null fails its controls; refusing to report")
    if a.selftest:
        return

    sents, paras = load()
    rng = random.Random(11)
    allex = {}
    allex.update(extractions(sents, "sent"))
    allex.update(extractions(paras, "para"))
    sys.stderr.write(f"\n  {len(allex)} author-unit extractions\n")

    rows = []
    for k, v in sorted(allex.items()):
        s = letters(v)
        if len(s) < 12:
            continue
        obs = score(s)
        units = sents if k.startswith("sent") else paras
        tag = "sent" if k.startswith("sent") else "para"
        vals = op_null(units, tag, k, a.trials, rng)
        rows.append((z_against(vals, obs), obs, k, len(s)))
    rows.sort(reverse=True)

    sys.stderr.write("\n  most English-like author-unit readings "
                     "(z vs OPERATION-matched null):\n")
    for z, obs, k, n in rows[:12]:
        sys.stderr.write(f"    z={z:+6.2f}  score={obs:.4f}  n={n:5}  {k}\n")
    sys.stderr.write("\n  least:\n")
    for z, obs, k, n in rows[-4:]:
        sys.stderr.write(f"    z={z:+6.2f}  score={obs:.4f}  n={n:5}  {k}\n")

    best = rows[0]
    sys.stderr.write(
        f"\n  VERDICT: best author-unit reading is {best[2]} at z={best[0]:+.2f}. "
        + ("A selection rule carrying hidden English would stand far above the "
           "rest; it does not.\n" if best[0] < 8 else
           "This clears the +8 threshold real English reaches and warrants "
           "reading directly.\n"))

    with open(a.out, "w", encoding="utf-8") as fh:
        seen = set()
        for _z, _o, k, _n in rows:
            for form in (allex[k], allex[k].lower(),
                         allex[k].lower().replace(" ", ""),
                         allex[k].lower()[::-1]):
                if form and form not in seen:
                    seen.add(form)
                    fh.write(form.replace("\n", " ") + "\n")
    sys.stderr.write(f"  {len(seen)} phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
