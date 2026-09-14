#!/usr/bin/env python3
"""
LENS: typographically special text in "Overdose" -- the repeated sentence,
the all-caps set-apart blocks, the masthead, the highlighted runs.
Builds concatenations, orderings, acrostics, capitalisation and mirror forms.
Emphasis on strings that are NOT literal spans of the article.
"""
import itertools, re, sys

# ---------------------------------------------------------------- base strings
R  = "The economy of love is infinitely more efficient than hate and war."
A1 = "BITCOIN IS TOXIC AF"
A2EM = ("EVERY SINGLE ONE OF THE BITCOIN WANNABES — BCH, BSV, ETH, XRP, "
        "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD — IS "
        "FACING THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.")
A2HY = A2EM.replace("—", "-")
A2DD = A2EM.replace("—", "--")
A3 = "BITCOIN FIXES ALL THIS"
A4 = "MAX KEISER"
A5 = "OVERDOSE"

CAPS = [A1, A2EM, A3, A4, A5]
CAPS_SHORT = [A1, A3, A4, A5]          # short caps blocks, for permutations

HL = []
for ln in open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    parts = ln.rstrip("\n").split("\t")
    if len(parts) >= 3:
        HL.append((parts[0], parts[1], parts[2]))

out = []
def add(s):
    if s and len(s) < 3900:
        out.append(s)

# ---------------------------------------------------------------- transforms
def nopunct(s):   return re.sub(r"[^\w\s]", "", s)
def nospace(s):   return re.sub(r"\s+", "", s)
def alnum(s):     return re.sub(r"[^A-Za-z0-9]", "", s)
def alpha(s):     return re.sub(r"[^A-Za-z]", "", s)
def words(s):     return re.findall(r"[A-Za-z0-9'$%,\.]+", s)
def wordsplain(s):return re.findall(r"[A-Za-z0-9]+", s)
def initials(s):  return "".join(w[0] for w in wordsplain(s))
def lasts(s):     return "".join(w[-1] for w in wordsplain(s))
def revw(s):      return " ".join(reversed(s.split()))
def revc(s):      return s[::-1]
def eachrev(s):   return " ".join(w[::-1] for w in s.split())
def camel(s):     ws = wordsplain(s); return ws[0].lower() + "".join(w.capitalize() for w in ws[1:]) if ws else ""
def pascal(s):    return "".join(w.capitalize() for w in wordsplain(s))
def snake(s):     return "_".join(w.lower() for w in wordsplain(s))
def kebab(s):     return "-".join(w.lower() for w in wordsplain(s))
def dot(s):       return ".".join(w.lower() for w in wordsplain(s))
def collapse(s):  return re.sub(r"\s+", " ", s).strip()

CASES = [lambda s: s,
         lambda s: s.upper(),
         lambda s: s.lower(),
         lambda s: s.title(),
         lambda s: s.capitalize()]

def forms(s, deep=True):
    """Every typographic form of one string."""
    s = collapse(s)
    base = {s}
    base |= {f(s) for f in CASES}
    nod = s.rstrip(".").rstrip()
    base |= {nod, nod.upper(), nod.lower()}
    for t in list(base):
        base.add(nopunct(t))
        base.add(collapse(nopunct(t)))
    for t in list(base):
        base.add(nospace(t))
    if deep:
        for f in (alnum, alpha, initials, lasts, revw, revc, eachrev,
                  camel, pascal, snake, kebab, dot):
            try:
                base.add(f(s))
                base.add(f(s.lower()))
                base.add(f(s.upper()))
            except Exception:
                pass
        # initials / lasts case variants
        i = initials(s)
        base |= {i, i.upper(), i.lower(), i[::-1], i.upper()[::-1]}
        l = lasts(s)
        base |= {l, l.upper(), l.lower(), l[::-1]}
        # reversed of the squashed forms (mirror-writing clue)
        for t in (nospace(s), alnum(s), alpha(s)):
            base |= {t[::-1], t.upper()[::-1], t.lower()[::-1]}
    return {b for b in base if b and b.strip()}

JOIN = ["", " ", "  ", "\t", "-", "_", ".", ",", ";", ":", "|", "+", "/",
        " | ", " - ", " -- ", " / ", "--", "==", "*", "~", "—", " — "]
JOIN_S = ["", " ", "-", "_", ".", "|", " | ", " - "]

# ============================================================ 1. the repeat
RF = sorted(forms(R))
for f in RF:
    add(f)
# doubled / tripled with every joiner -- the sentence printed twice
for f in RF:
    for j in JOIN:
        add(f + j + f)
for f in sorted(forms(R))[:0] or []:
    pass
# x3 and x2 with count markers, on the compact forms only
COMPACT_R = sorted({collapse(R), R.upper(), R.lower(), nospace(R),
                    nospace(R).lower(), nospace(R).upper(),
                    nopunct(R), collapse(nopunct(R)),
                    collapse(nopunct(R)).lower(), collapse(nopunct(R)).upper(),
                    alnum(R), alpha(R), alpha(R).lower(), alpha(R).upper(),
                    initials(R), initials(R).upper(), initials(R).lower(),
                    R.rstrip("."), R.rstrip(".").lower(), R.rstrip(".").upper(),
                    revc(R), revw(R), eachrev(R), camel(R), pascal(R),
                    snake(R), kebab(R), dot(R)})
for f in COMPACT_R:
    for j in JOIN_S:
        add(j.join([f]*3))
    add(f + "2")
    add("2" + f)
    add(f + " x2")
    add(f + "x2")
    add(f + f[::-1])          # palindromic pairing (mirror clue)
    add(f[::-1] + f)
    add(f + " " + f[::-1])

# ============================================================ 2. caps blocks
CF = {}
for name, s in [("A1", A1), ("A2EM", A2EM), ("A2HY", A2HY), ("A2DD", A2DD),
                ("A3", A3), ("A4", A4), ("A5", A5)]:
    CF[name] = sorted(forms(s))
    for f in CF[name]:
        add(f)

# caps-block cores used for combination (keep the blow-up bounded)
def cores(s):
    return [collapse(s), s.upper(), s.lower(), s.title(),
            nospace(s), nospace(s).lower(), nospace(s.lower()),
            collapse(nopunct(s)), collapse(nopunct(s)).lower(),
            alnum(s), alnum(s).lower(), alpha(s), alpha(s).lower(),
            initials(s), initials(s).lower(), snake(s), kebab(s), camel(s),
            pascal(s), revc(s), revw(s)]

R_CORES = [collapse(R), R.upper(), R.lower(), R.rstrip("."),
           R.rstrip(".").upper(), R.rstrip(".").lower(),
           nospace(R), nospace(R).lower(), nospace(R).upper(),
           collapse(nopunct(R)), collapse(nopunct(R)).lower(),
           alnum(R), alpha(R), alpha(R).lower(), alpha(R).upper(),
           initials(R), initials(R).lower(), snake(R), kebab(R),
           camel(R), pascal(R), revc(R), revw(R)]

# ---- R x each caps block, both orders, every joiner
for name in ("A1", "A2EM", "A2HY", "A3", "A4", "A5"):
    s = {"A1": A1, "A2EM": A2EM, "A2HY": A2HY, "A3": A3, "A4": A4, "A5": A5}[name]
    for c in cores(s):
        for r in R_CORES:
            for j in JOIN_S:
                add(r + j + c)
                add(c + j + r)

# ---- all caps blocks in page order, several joiners and cases
ORDERS = {
    "page":   [A1, A2EM, A3, A4],
    "pageM":  [A5, A1, A2EM, A3, A4],
    "pageMend": [A1, A2EM, A3, A4, A5],
    "short":  [A1, A3],
    "shortM": [A1, A3, A4],
}
for _, seq in ORDERS.items():
    for j in JOIN:
        raw = j.join(seq)
        add(raw)
        add(raw.upper()); add(raw.lower()); add(collapse(nopunct(raw)))
        add(nospace(raw)); add(nospace(raw).lower())
        add(raw[::-1])
    for j in JOIN_S:
        add(j.join(alnum(x) for x in seq))
        add(j.join(alnum(x).lower() for x in seq))
        add(j.join(initials(x) for x in seq))
        add(j.join(initials(x).lower() for x in seq))
        add(j.join(nospace(x) for x in seq))
        add(j.join(nospace(x).lower() for x in seq))

# ---- every permutation of the 4 short caps blocks (+ hyphen variant of A2)
for perm in itertools.permutations([A1, A3, A4, A5]):
    for j in ("", " ", "-", "_", "|"):
        raw = j.join(perm)
        add(raw); add(raw.lower()); add(nospace(raw)); add(nospace(raw).lower())
# permutations of all 5 (120) with 3 joiners, upper+lower
for perm in itertools.permutations(CAPS):
    for j in ("", " ", "-"):
        raw = j.join(perm)
        add(raw); add(raw.lower())
        add(nospace(raw)); add(nospace(raw).lower())

# ---- R inserted into the caps sequence at every position
for seq in ([A1, A2EM, A3, A4], [A5, A1, A2EM, A3, A4]):
    for pos in range(len(seq) + 1):
        s2 = seq[:pos] + [R] + seq[pos:]
        for j in ("", " ", " | ", "-", "_", ".", "\n".replace("\n", " ")):
            raw = j.join(s2)
            add(raw); add(raw.upper()); add(raw.lower())
            add(nospace(raw)); add(nospace(raw).lower())
            add(collapse(nopunct(raw))); add(collapse(nopunct(raw)).lower())
# ---- R twice around the caps sequence (the sentence brackets the piece)
for seq in ([A1, A2EM, A3, A4], [A5, A1, A2EM, A3, A4], [A1, A3]):
    for j in ("", " ", " | ", "-", "_"):
        raw = j.join([R] + seq + [R])
        add(raw); add(raw.lower()); add(nospace(raw)); add(nospace(raw).lower())
        add(collapse(nopunct(raw)).lower())

# ============================================================ 3. acrostics
def acro_of(seq, fn):
    return "".join(fn(x) for x in seq if fn(x))

for seq_name, seq in [("caps", CAPS), ("capsPage", [A1, A2EM, A3, A4]),
                      ("capsM", [A5, A1, A2EM, A3, A4]),
                      ("capsR", [A1, A2EM, A3, A4, R]),
                      ("Rcaps", [R, A1, A2EM, A3, A4])]:
    for fn in (lambda x: x.strip()[0],
               lambda x: x.strip()[-1],
               lambda x: wordsplain(x)[0],
               lambda x: wordsplain(x)[-1],
               lambda x: initials(x),
               lambda x: lasts(x)):
        try:
            a = acro_of(seq, fn)
        except Exception:
            continue
        for t in (a, a.upper(), a.lower(), a[::-1], a.upper()[::-1]):
            add(t)
        for j in (" ", "-", "_", "."):
            b = j.join(fn(x) for x in seq)
            add(b); add(b.upper()); add(b.lower())

# word-level acrostics inside each special string
for s in [R, A1, A2EM, A2HY, A3, A4, A5]:
    ws = wordsplain(s)
    for k in (1, 2, 3):
        a = "".join(w[:k] for w in ws)
        for t in (a, a.upper(), a.lower(), a[::-1]):
            add(t)
        a = "".join(w[-k:] for w in ws)
        for t in (a, a.upper(), a.lower(), a[::-1]):
            add(t)
    # every nth word
    for n in (2, 3, 4, 5):
        for off in range(n):
            sel = ws[off::n]
            if len(sel) > 1:
                for j in (" ", "", "-"):
                    t = j.join(sel)
                    add(t); add(t.lower()); add(t.upper())
    # every nth letter
    letters = alpha(s)
    for n in (2, 3, 4, 5, 7):
        for off in range(n):
            t = letters[off::n]
            if len(t) > 3:
                add(t); add(t.lower()); add(t.upper()); add(t[::-1])

# ============================================================ 4. the ticker list
TICK = ["BCH", "BSV", "ETH", "XRP", "ADA"]
for perm_n, perm in enumerate(itertools.permutations(TICK)):
    for j in ("", " ", "-", ",", "_"):
        t = j.join(perm)
        add(t); add(t.lower())
add("BCHBSVETHXRPADA12000")
add("bchbsvethxrpada12000")
for j in ("", " ", "-", "_"):
    for tail in ("12000", "12,000", "12000OTHERSHITCOINS"):
        add(j.join(TICK) + j + tail)
        add((j.join(TICK) + j + tail).lower())
    add(j.join(TICK) + j + "FIAT" + j + "GOLD")
    add((j.join(TICK) + j + "FIAT" + j + "GOLD").lower())
NUMS = ["12000", "12,000", "85", "2", "51", "95", "20", "1971", "2011",
        "2017", "1969", "2008", "42", "20000", "100000", "10", "1", "24", "79"]
for r in (collapse(R), R.lower(), nospace(R), nospace(R).lower(),
          alpha(R), alpha(R).lower(), initials(R), initials(R).lower()):
    for n in NUMS:
        for j in ("", " ", "-", "_"):
            add(r + j + n)
            add(n + j + r)

# ============================================================ 5. highlights
hl_texts = [t for _, _, t in HL]
by_col = {}
by_page = {}
for pg, col, t in HL:
    by_col.setdefault(col, []).append(t)
    by_page.setdefault(pg, []).append(t)

def seq_variants(seq, tag):
    for j in ("", " ", " | ", "-", "_", "."):
        raw = j.join(seq)
        add(raw); add(raw.lower()); add(collapse(nopunct(raw)))
        add(collapse(nopunct(raw)).lower())
        add(nospace(raw)); add(nospace(raw).lower())
    a = "".join(x.strip()[0] for x in seq)
    for t in (a, a.upper(), a.lower(), a[::-1], a.upper()[::-1]):
        add(t)
    a = "".join(wordsplain(x)[0] for x in seq if wordsplain(x))
    for t in (a, a.lower(), a.upper()):
        add(t)
    a = "".join(wordsplain(x)[-1] for x in seq if wordsplain(x))
    for t in (a, a.lower(), a.upper()):
        add(t)
    a = "".join(initials(x) for x in seq)
    for t in (a, a.lower(), a.upper(), a[::-1]):
        add(t)

seq_variants(hl_texts, "all")
for col, seq in by_col.items():
    seq_variants(seq, col)
for pg, seq in by_page.items():
    seq_variants(seq, pg)
seq_variants(list(reversed(hl_texts)), "rev")

# highlights + the repeated sentence / caps blocks -- the cross-lens part
hl_join = {
    "hl_all_sp": " ".join(hl_texts),
    "hl_all_ns": nospace(" ".join(hl_texts)),
    "hl_ini":    "".join(initials(x) for x in hl_texts),
    "hl_first":  "".join(x.strip()[0] for x in hl_texts),
    "hl_fw":     " ".join(wordsplain(x)[0] for x in hl_texts if wordsplain(x)),
}
for _, hv in hl_join.items():
    for r in (collapse(R), R.lower(), nospace(R).lower(), initials(R),
              alpha(R).lower()):
        for j in ("", " ", "|", "-", "_"):
            add(hv + j + r)
            add(r + j + hv)
    for c in (A1, A3, A4, A5, A1 + A3, A1 + " " + A3):
        for j in ("", " ", "-", "_"):
            add(hv + j + c); add(c + j + hv)
            add((hv + j + c).lower()); add((c + j + hv).lower())

# ============================================================ 6. masthead play
for a in (A5, A5.lower(), A5.title(), A5[::-1], A5.lower()[::-1]):
    for b in (A4, A4.lower(), nospace(A4), nospace(A4).lower(),
              "maxkeiser", "MAXKEISER", "max keiser", "MaxKeiser"):
        for j in JOIN_S:
            add(a + j + b); add(b + j + a)
    for r in (collapse(R), R.lower(), nospace(R).lower(), initials(R)):
        for j in JOIN_S:
            add(a + j + r); add(r + j + a)
for extra in ("Overdose", "overdose", "OVERDOSE", "OverDose", "oVERDOSE",
              "esodrevo", "ESODREVO", "0VERDOSE", "0verdose"):
    add(extra)
    for j in ("", " ", "-", "_"):
        add(extra + j + "MaxKeiser"); add(extra + j + "maxkeiser")
        add(extra + j + collapse(R)); add(extra + j + nospace(R).lower())
        add(extra + j + "BitcoinMagazine"); add(extra + j + "24")
        add(extra + j + "ElSalvador")
        add(extra + j + "20BTC"); add(extra + j + "20")

# ============================================================ emit
seen, uniq = set(), []
for s in out:
    s = s.replace("\r", "").replace("\n", " ")
    if s and s not in seen:
        seen.add(s)
        uniq.append(s)
sys.stdout.write("\n".join(uniq) + "\n")
sys.stderr.write(f"generated {len(uniq)} unique candidates\n")
