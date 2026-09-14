#!/usr/bin/env python3
"""
Boustrophedon: Keiser's two clues applied TOGETHER instead of separately.

THE SYNTHESIS
He gave two devices, a year apart, and this project has always tested them as
two families:

  2022-12-26  "Like George Sand's hidden cryptography"  -> alternate units
  2023-03-05  mirror writing, linking PMC2117809        -> reversed direction

Alternate units, each reversed, read continuously, is boustrophedon — "as the
ox plows" — the ancient way of writing where every second line runs the other
way. It is also precisely what mirror writing IS: Leonardo's script runs
right-to-left. So boustrophedon is not a third guess bolted on; it is the
single operation that both clues describe at once, and neither clue alone
specifies it.

Every prior test took alternate lines forward, or took the whole text mirrored.
Neither is this. Reversing ONLY the alternate units, and keeping the others as
written, is a distinct operation and was never generated.

UNITS
Run over lines, sentences and paragraphs. Lines are the designer's unit and
sentences and paragraphs are the author's — the author-unit argument says the
latter are the ones he could actually key to, so they are reported separately
rather than pooled.

REVERSAL LEVELS
Reversing "a line" is ambiguous, so all three readings are generated:
character order, word order, and word order with each word also reversed.

THE NULL
Operation-matched, as everywhere else here: the same boustrophedon transform
applied to copies of the text with unit order shuffled. A frequency-matched
null is not sufficient — this project has already had z=+5.6 and z=+18.8 false
positives from one, both erased once the null was operation-matched.

  python3 boustrophedon.py --selftest
  python3 boustrophedon.py --out /tmp/boustro.txt
"""
import argparse, random, re, sys

from englishness import letters, score

WORD = re.compile(r"[A-Za-z'-]+")

# Common English WORD bigrams. A character-trigram scorer is the wrong
# instrument for word-order reversal: reversing the order of words leaves
# nearly every character trigram intact, so it moves the score by ~+0.011 and
# cannot distinguish a recovered message from unchanged prose. Word bigrams are
# destroyed by exactly that operation, so they have the power the trigram
# scorer lacks, and they close the branch it left inconclusive.
BIGRAMS = set("""
of|the in|the to|the on|the and|the for|the it|is is|a to|be that|the
with|the at|the from|the this|is there|is as|a will|be have|been can|be
has|been it|was in|a of|a to|a by|the all|the one|of out|of such|as
more|than we|are you|are they|are i|am does|not do|not going|to want|to
part|of end|of kind|of some|of most|of because|of instead|of based|on
""".split())


def wscore(text):
    """Common-word-bigram hits per adjacent pair. Word-ORDER sensitive."""
    ws = [w.lower() for w in WORD.findall(text)]
    if len(ws) < 2:
        return 0.0
    n = sum(1 for a, b in zip(ws, ws[1:]) if f"{a}|{b}" in BIGRAMS)
    return n / (len(ws) - 1)


def load(path="article_transcript.txt"):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    pages = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(pages[1:])
    lines, sents, paras = [], [], []
    for _n, body in zip(it, it):
        for block in re.split(r"\n\s*\n", body):
            ls = [l.strip() for l in block.splitlines() if l.strip()]
            if not ls:
                continue
            lines.extend(ls)
            flat = " ".join(ls)
            paras.append(flat)
            for s in re.split(r"(?<=[.!?])\s+", flat):
                if WORD.findall(s):
                    sents.append(s.strip())
    return {"line": lines, "sent": sents, "para": paras}


def rev_chars(s):
    return s[::-1]


def rev_words(s):
    return " ".join(WORD.findall(s)[::-1])


def rev_words_and_chars(s):
    return " ".join(w[::-1] for w in WORD.findall(s)[::-1])


REVERSALS = {"chars": rev_chars, "words": rev_words,
             "wordchars": rev_words_and_chars}


def boustro(units, revfn, phase=1, step=2):
    """Reverse every `step`-th unit starting at `phase`; keep the rest."""
    out = []
    for i, u in enumerate(units):
        out.append(revfn(u) if i % step == phase % step else u)
    return " ".join(out)


def variants(units):
    out = {}
    for rname, fn in REVERSALS.items():
        for step in (2, 3):
            for phase in range(step):
                out[f"{rname}_s{step}_p{phase}"] = boustro(units, fn, phase, step)
        # the pure controls: nothing reversed, everything reversed
        out[f"{rname}_none"] = " ".join(units)
        out[f"{rname}_all"] = " ".join(fn(u) for u in units)
    return out


def op_null(units, key, trials, rng):
    """Same transform on unit-order-shuffled copies."""
    vals, u = [], list(units)
    for _ in range(trials):
        rng.shuffle(u)
        s = letters(variants(u).get(key, ""))
        if len(s) >= 3:
            vals.append(score(s))
    return vals


def z_of(vals, obs):
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)) ** 0.5
    return (obs - m) / sd if sd else 0.0


def selftest():
    """A PLANTED boustrophedon message must be recovered; ordinary prose
    must not be flagged."""
    ok = True
    msg = ("the quick brown fox jumps over the lazy dog and then the dog "
           "chases the fox back across the wide green field at dawn")
    ws = msg.split()
    chunks = [" ".join(ws[i:i + 6]) for i in range(0, len(ws), 6)]
    # write it boustrophedon-style, so UNDOING it should restore English
    planted = [c if i % 2 == 0 else rev_words(c) for i, c in enumerate(chunks)]
    undone = boustro(planted, rev_words, 1, 2)
    a, b = score(letters(undone)), score(letters(" ".join(planted)))
    sys.stderr.write(f"  planted boustrophedon text scores {b:.4f} as written, "
                     f"{a:.4f} once un-ploughed\n")
    ok &= a > b
    sys.stderr.write(f"  transform recovers a planted message: "
                     f"{'OK' if a > b else 'FAIL'}\n")

    u = load()
    sys.stderr.write(f"  article: {len(u['line'])} lines, {len(u['sent'])} "
                     f"sentences, {len(u['para'])} paragraphs\n")
    ok &= len(u["line"]) > 100 and len(u["sent"]) > 50

    # Reversing everything must LOWER the score - proves the scorer is
    # direction-sensitive and so can detect a direction error.
    fwd = score(letters(" ".join(u["sent"])))
    rev = score(letters(" ".join(s[::-1] for s in u["sent"])))
    sys.stderr.write(f"  article forward {fwd:.4f}, fully reversed {rev:.4f}: "
                     f"{'direction-sensitive OK' if fwd > rev else 'FAIL'}\n")
    ok &= fwd > rev
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/boustro.txt")
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("transform or scorer fails its controls; refusing to report")
    if a.selftest:
        return

    units = load()
    rng = random.Random(23)
    rows, emit = [], {}
    for uname, seq in units.items():
        vs = variants(seq)
        for k, v in vs.items():
            s = letters(v)
            if len(s) < 40:
                continue
            key = f"{uname}:{k}"
            emit[key] = v
            obs = score(s)
            rows.append((z_of(op_null(seq, k, a.trials, rng), obs), obs, key))
    rows.sort(reverse=True)

    sys.stderr.write(f"\n  {len(rows)} boustrophedon readings, z vs "
                     f"OPERATION-matched null\n\n")
    for z, o, k in rows[:14]:
        tag = "  <- control, nothing reversed" if k.endswith("_none") else ""
        sys.stderr.write(f"    z={z:+6.2f}  score={o:.4f}  {k}{tag}\n")
    sys.stderr.write("  ...\n")
    for z, o, k in rows[-3:]:
        sys.stderr.write(f"    z={z:+6.2f}  score={o:.4f}  {k}\n")

    # POWER GUARD, per reversal level. Comparing z across different
    # transforms is apples to oranges, and worse, the trigram scorer has very
    # different sensitivity to each. Reversing WORD ORDER leaves almost every
    # trigram intact, so an un-ploughed word-level text scores like prose
    # whether or not anything was recovered — a null there measures the
    # scorer, not the text. Measure the detectable effect at each level with a
    # planted message and refuse to report a verdict where it is too small.
    prose = score(letters(" ".join(units["sent"])))
    sys.stderr.write(f"\n  reference: untransformed article prose scores "
                     f"{prose:.4f}\n")
    # Power is measured by ENCODE-THEN-DECODE on the ARTICLE ITSELF. A toy
    # sentence is the wrong control: the first version used "the quick brown
    # fox..." and the word-bigram scorer read 0.0000 power simply because that
    # sentence contains none of the listed bigrams — a defect in the control
    # text, not in the scorer, which does separate article prose (0.0346) from
    # its words reversed (0.0000). boustro applied twice is the identity, so
    # encoding the real article and decoding it back is the exact control.
    chunks = list(units["sent"])
    sys.stderr.write("\n  power of each scorer, per reversal level:\n")
    power, wpower = {}, {}
    for rname, fn in REVERSALS.items():
        planted = [fn(c) if i % 2 == 1 else c for i, c in enumerate(chunks)]
        before = score(letters(" ".join(planted)))
        after = score(letters(boustro(planted, fn, 1, 2)))
        power[rname] = after - before
        wb, wa = wscore(" ".join(planted)), wscore(boustro(planted, fn, 1, 2))
        wpower[rname] = wa - wb
        sys.stderr.write(f"    {rname:10} trigram {before:.4f}->{after:.4f} "
                         f"({after-before:+.4f})   word-bigram "
                         f"{wb:.4f}->{wa:.4f} ({wa-wb:+.4f})\n")

    wprose = wscore(" ".join(units["sent"]))
    sys.stderr.write(f"\n  word-bigram reference: article prose {wprose:.4f}, "
                     f"its words reversed "
                     f"{wscore(' '.join(rev_words(s) for s in units['sent'])):.4f}\n")

    # Thresholds must be RELATIVE to each scorer's own dynamic range. An
    # absolute 0.02 cut-off is meaningless for the word-bigram statistic,
    # whose entire range is 0 to 0.0346 — it called +0.0145 (42% of full
    # recovery) "no power" purely because trigram scores happen to be bigger
    # numbers. Each level is decided by whichever scorer recovers the largest
    # FRACTION of its own prose-versus-scrambled span.
    sys.stderr.write("\n  VERDICT by reversal level "
                     "(relative power, best scorer):\n")
    for rname in REVERSALS:
        sub = [r for r in rows
               if f":{rname}_" in r[2] and not r[2].endswith(("_none", "_all"))]
        if not sub:
            continue
        rel_t = power[rname] / prose if prose else 0.0
        rel_w = wpower[rname] / wprose if wprose else 0.0
        if max(rel_t, rel_w) < 0.20:
            sys.stderr.write(
                f"    {rname:10} INCONCLUSIVE — best relative power "
                f"{max(rel_t, rel_w)*100:.0f}%; no scorer here can detect the "
                f"operation, so neither a hit nor a null is meaningful.\n")
            continue
        if rel_t >= rel_w:
            which, top, ref, rel = "trigram", max(r[1] for r in sub), prose, rel_t
        else:
            which, top = "word-bigram", max(wscore(emit[r[2]]) for r in sub)
            ref, rel = wprose, rel_w
        sys.stderr.write(
            f"    {rname:10} {which:11} rel.power {rel*100:3.0f}%  "
            f"best reading {top:.4f} vs prose {ref:.4f} -> "
            + ("CANDIDATE, read it directly\n" if top >= ref
               else "NULL with power\n"))

    with open(a.out, "w", encoding="utf-8") as fh:
        seen = set()
        for _z, _o, k in rows:
            v = emit[k]
            for f in (v, v.lower(), v.lower().replace(" ", "")):
                if f and f not in seen:
                    seen.add(f)
                    fh.write(f.replace("\n", " ") + "\n")
    sys.stderr.write(f"  {len(seen)} phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
