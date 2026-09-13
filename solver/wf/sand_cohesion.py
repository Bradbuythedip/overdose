#!/usr/bin/env python3
"""
Word-level lexical-cohesion test for alternate-SENTENCE (George Sand) readings.

WHY: englishness_z (letter trigrams vs a letter shuffle) cannot see sentence
ORDER at all -- in sand_sentences.py's control, a planted odd-parity English
message ranked only 6/31 against unit-shuffled copies. A Sand cipher is about
coherence ACROSS the selected units, so the statistic must be word-level.

METRIC: for each adjacent pair of units in a reading, cosine overlap of their
content-word stems; reading score = mean over pairs. Coherent adjacent
sentences share more content words than random pairs.

TEST: for the article, compare the natural reading (step 1) with odd / even /
3rd@k readings, against a 30x unit-shuffled null. A planted Sand message makes
a parity reading score like (or above) the natural reading; ordinary prose
makes every parity reading fall toward the shuffled null.

POSITIVE CONTROL: interleave p75's sentences with p79's sentences one-by-one.
The odd reading is then p75 verbatim (a real coherent text) and the natural
reading alternates topics. The test must rank the odd reading above the
natural reading and far above the null, or it has no power.
"""
import os, re, sys, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import sand_sentences as S

STOP = set("""a an the and or but if of to in on at by for with from as is are was were be been being it its this that these
those he she they them his her their we our you your i my me not no so do does did have has had will would can could
than then there here what which who whom when where why how all any some every each into up out over under about
into off just also very more most much many such only own same too s t ll ve re d m y dont its whats thats hes shes
theyre youre weve ive im""".split())


def stem(w):
    w = w.lower()
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def content(u):
    ws = re.findall(r"[A-Za-z][A-Za-z'’-]*", u)
    ws = [re.sub(r"[^a-z]", "", w.lower()) for w in ws]
    return {stem(w) for w in ws if w and w not in STOP and len(w) > 2}


def cohesion(units):
    cs = [content(u) for u in units]
    vals = []
    for a, b in zip(cs, cs[1:]):
        if not a or not b:
            continue
        vals.append(len(a & b) / math.sqrt(len(a) * len(b)))
    return sum(vals) / len(vals) if vals else float("nan")


def readings(units):
    yield "natural", units
    yield "odd", units[0::2]
    yield "even", units[1::2]
    for k in range(3):
        yield f"3rd@{k}", units[k::3]


def run(units, tag, rng, n_shuf=30):
    out = {}
    print(f"\n--- {tag} ({len(units)} units) ---")
    nulls = []
    for _ in range(n_shuf):
        sh = units[:]
        rng.shuffle(sh)
        nulls.append(cohesion(sh))
    m = sum(nulls) / len(nulls)
    sd = (sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1)) ** 0.5
    for name, sel in readings(units):
        c = cohesion(sel)
        z = (c - m) / sd if sd else float("nan")
        out[name] = (c, z)
        print(f"  {name:8} n={len(sel):3d} cohesion={c:.4f}  z vs unit-shuffled null={z:+5.1f}")
    print(f"  null (unit-shuffled, step 1): mean={m:.4f} sd={sd:.4f} max={max(nulls):.4f}")
    return out


def main():
    rng = random.Random(20260913)
    pages = S.load_pages()
    per_page = {pno: S.units_A(paras) for pno, paras in pages}
    allu = [u for pno in sorted(per_page) for u in per_page[pno]]

    # ---- positive control: interleave p75 and p79 sentence by sentence ----
    a, b = per_page[75], per_page[79]
    n = min(len(a), len(b))
    inter = [s for pair in zip(a[:n], b[:n]) for s in pair]
    ctrl = run(inter, "CONTROL: p75/p79 interleaved (odd = p75 verbatim, even = p79 verbatim)", rng)
    ok = ctrl["odd"][0] > ctrl["natural"][0] and ctrl["odd"][1] > 2.5 and ctrl["even"][1] > 2.5
    print(f"  CONTROL {'PASS' if ok else 'FAIL'}: planted parities must beat the natural reading and the null "
          f"(odd z={ctrl['odd'][1]:+.1f}, even z={ctrl['even'][1]:+.1f}, natural z={ctrl['natural'][1]:+.1f})")

    # ---- full-length positive control: interleave the article's first half with its
    # second half sentence by sentence (odd = first 44 sentences verbatim, even = last 43),
    # i.e. planted parities at the same n as the real odd/even readings ----
    h = (len(allu) + 1) // 2
    first, second = allu[:h], allu[h:]
    inter2 = []
    for i in range(h):
        inter2.append(first[i])
        if i < len(second):
            inter2.append(second[i])
    c2 = run(inter2, "CONTROL: first-half/second-half interleaved (odd = sentences 1-44, even = 45-87)", rng)
    ok = c2["odd"][0] > c2["natural"][0] and c2["even"][0] > c2["natural"][0] and c2["odd"][1] > 2.5 and c2["even"][1] > 2.5
    print(f"  FULL-LENGTH CONTROL {'PASS' if ok else 'FAIL'}: odd z={c2['odd'][1]:+.1f}, even z={c2['even'][1]:+.1f}, "
          f"natural z={c2['natural'][1]:+.1f} (small-n p75/p79 control above is reported but not relied on)")

    # ---- second control: the article itself should be coherent in its natural order ----
    real = run(allu, "REAL article, unit set A (87 sentences)", rng)
    ok2 = real["natural"][1] > 2.5
    print(f"  NATURAL-ORDER CONTROL {'PASS' if ok2 else 'FAIL'}: natural reading z={real['natural'][1]:+.1f}")

    for us, fn in (("B", S.units_B), ("P", S.units_P)):
        uu = [u for pno, paras in pages for u in fn(paras)]
        run(uu, f"REAL article, unit set {us}", rng)
    for pno in sorted(per_page):
        run(per_page[pno], f"REAL p{pno}, unit set A", rng)

    print("\nVERDICT:")
    if not (ok and ok2):
        print("  test has no power here -- inconclusive")
    else:
        best = max((v[1], k) for k, v in real.items() if k != "natural")
        print(f"  best parity reading of the real article: {best[1]} z={best[0]:+.1f} "
              f"vs natural z={real['natural'][1]:+.1f}")
        if best[0] >= real["natural"][1]:
            print("  a parity reading is as coherent as the natural reading -> Sand-style structure PLAUSIBLE")
        else:
            print("  every parity reading is less coherent than the natural reading -> no alternate-sentence message")


if __name__ == "__main__":
    main()
