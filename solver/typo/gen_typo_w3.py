#!/usr/bin/env python3
"""Wave 3: printed line breaks, case patterns, doubling, BIP-39 word mappings."""
import itertools, re, sys, hashlib

R  = "The economy of love is infinitely more efficient than hate and war."
# how the sentence is actually SET on page 78
R_L1 = "The economy of"                     # end of one printed line
R_L2 = "love is infinitely more efficient than hate and war."
PRE  = "our joint inner cosmic being."      # what precedes the in-paragraph one

A1 = "BITCOIN IS TOXIC AF"
A2_LINES = ["EVERY SINGLE ONE OF",
            "THE BITCOIN WANNABES - BCH, BSV, ETH, XRP,",
            "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT",
            "MONEY AND GOLD - IS FACING THE IGNOMINIOUS",
            "FATE OF DEMONETIZATION VERSUS BITCOIN."]
A2 = " ".join(A2_LINES)
A3 = "BITCOIN FIXES ALL THIS"
A4 = "MAX KEISER"
A5 = "OVERDOSE"

def ns(s):  return re.sub(r"\s+", "", s)
def wl(s):  return re.findall(r"[A-Za-z0-9]+", s)
def al(s):  return re.sub(r"[^A-Za-z]", "", s)
def ini(s): return "".join(w[0] for w in wl(s))

out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900:
            out.append(s.replace("\n", " ").replace("\r", ""))

# ---------------------------------------------- 1. the printed line break in R
frag = [R_L1, R_L2]
for j in ("", " ", "-", "_", "|", ".", "/"):
    add(j.join(frag), j.join(reversed(frag)))
    add(j.join(frag).lower(), j.join(reversed(frag)).lower())
    add(ns(j.join(frag)), ns(j.join(reversed(frag))).lower())
add(R_L1, R_L1.lower(), R_L1.upper(), ns(R_L1).lower(),
    R_L2, R_L2.lower(), R_L2.upper(), ns(R_L2).lower(),
    R_L2.rstrip("."), R_L2.rstrip(".").lower(), ns(R_L2.rstrip(".")).lower())
# swapped halves, doubled
for j in ("", " ", " | "):
    t = j.join([R_L2, R_L1])
    add(t, t.lower(), ns(t).lower(), t + j + t, (t + j + t).lower())
# preceded by its paragraph context
for j in ("", " "):
    add(PRE + j + R, (PRE + j + R).lower(), ns(PRE + j + R).lower())
    add(PRE + j + R + j + R, (PRE + j + R + j + R).lower())

# ---------------------------------------------- 2. A2 line structure
for j in ("", " ", "-", "_", "|", "/"):
    t = j.join(A2_LINES)
    add(t, t.lower(), ns(t).lower())
    t = j.join(reversed(A2_LINES))
    add(t, t.lower(), ns(t).lower())
for perm in itertools.permutations(A2_LINES):
    t = " ".join(perm)
    add(t.lower())
# line acrostics of A2
for fn in (lambda x: x.strip()[0], lambda x: x.strip()[-1],
           lambda x: wl(x)[0], lambda x: wl(x)[-1], lambda x: ini(x)):
    a = "".join(fn(x) for x in A2_LINES)
    add(a, a.lower(), a.upper(), a[::-1], a.upper()[::-1])
    for j in (" ", "-", "_"):
        b = j.join(fn(x) for x in A2_LINES)
        add(b, b.lower(), b.upper())

# ---------------------------------------------- 3. case patterns (typographic)
def alt(s, phase=0):
    o, i = [], 0
    for c in s:
        if c.isalpha():
            o.append(c.upper() if (i + phase) % 2 == 0 else c.lower()); i += 1
        else: o.append(c)
    return "".join(o)
def everyn(s, n, phase=0):
    o, i = [], 0
    for c in s:
        if c.isalpha():
            o.append(c.upper() if (i % n) == phase else c.lower()); i += 1
        else: o.append(c)
    return "".join(o)
def vowcaps(s, invert=False):
    V = set("aeiouAEIOU")
    return "".join((c.upper() if (c in V) != invert else c.lower())
                   if c.isalpha() else c for c in s)
def lastcaps(s):
    return " ".join(w[:-1].lower() + w[-1].upper() if w else w for w in s.split())

BASES = [R, R.rstrip("."), A1, A2, A3, A4, A5, ns(R), ns(R.rstrip("."))]
for S in BASES:
    for p in (0, 1):
        add(alt(S, p), ns(alt(S, p)))
    for n in (3, 4, 5):
        for p in range(n):
            add(everyn(S, n, p), ns(everyn(S, n, p)))
    add(vowcaps(S), vowcaps(S, True), ns(vowcaps(S)), ns(vowcaps(S, True)))
    add(lastcaps(S), ns(lastcaps(S)))

# ---------------------------------------------- 4. doubling as typography
def chardouble(s): return "".join(c * 2 for c in s)
def worddouble(s): return " ".join(w + " " + w for w in s.split())
for S in (R, R.rstrip("."), R.lower(), R.upper(), ns(R), ns(R).lower(),
          A1, A3, A4, A5, A1.lower(), A5.lower()):
    add(chardouble(S), worddouble(S))
    add(ns(chardouble(S)), ns(worddouble(S)).lower())
    add(chardouble(al(S)), chardouble(al(S).lower()))
# interleave the two printings char-by-char with a separator
a = ns(R)
add("".join(c + "." for c in a), "".join(c + "-" for c in a))
add(" ".join(a), " ".join(a.lower()), " ".join(al(R)), " ".join(al(R).lower()))
add(" ".join(al(A1)), " ".join(al(A3)), " ".join(al(A4)), " ".join(A5))

# ---------------------------------------------- 5. BIP-39 word mappings
WORDS = [w.strip() for w in open(
    "/usr/local/lib/python3.11/dist-packages/mnemonic/wordlist/english.txt")
    if w.strip()]
BYLETTER = {}
for w in WORDS:
    BYLETTER.setdefault(w[0], []).append(w)

def map_seq(src_words, fn):
    o = []
    for w in src_words:
        try:
            x = fn(w)
        except Exception:
            return None
        if x is None:
            return None
        o.append(x)
    return " ".join(o)

RW = R.rstrip(".").split()
CW = (A1 + " " + A3 + " " + A4 + " " + A5).split()
for src in (RW, CW, RW + CW, wl(A2)):
    maps = [
        lambda w: WORDS[len(al(w)) % 2048],
        lambda w: WORDS[(ord(w[0].upper()) - 64) % 2048],
        lambda w: WORDS[sum(ord(c.upper()) - 64 for c in al(w)) % 2048],
        lambda w: WORDS[int(hashlib.sha256(w.lower().encode()).hexdigest(), 16) % 2048],
        lambda w: BYLETTER.get(w[0].lower(), [None])[0],
        lambda w: (w.lower() if w.lower() in WORDS else
                   min(BYLETTER.get(w[0].lower(), ["abandon"]),
                       key=lambda x: abs(len(x) - len(w)))),
    ]
    for f in maps:
        t = map_seq(src, f)
        if t:
            add(t, t.upper(), ns(t))
# words of R that really are BIP-39 words, in order
real = [w.lower() for w in RW if w.lower() in WORDS]
if real:
    add(" ".join(real), " ".join(real).upper(), ns(" ".join(real)))
realc = [w.lower() for w in CW if w.lower() in WORDS]
if realc:
    add(" ".join(realc), " ".join(realc).upper())

# ---------------------------------------------- 6. progressive acrostics
SPEC = [R, A1, A2, A3, A4, A5]
for order in (SPEC, [A5] + SPEC[:-1], list(reversed(SPEC))):
    for k in range(1, 6):
        a = "".join(al(x)[k-1] if len(al(x)) >= k else "" for x in order)
        add(a, a.lower(), a.upper())
    a = "".join(al(x)[i] if len(al(x)) > i else "" for i, x in enumerate(order))
    add(a, a.lower(), a.upper())
    a = "".join(al(x)[-(i+1)] if len(al(x)) > i else "" for i, x in enumerate(order))
    add(a, a.lower(), a.upper())

# ---------------------------------------------- 7. caps-block letter arithmetic
for S in (A1, A2, A3, A4, A5, R):
    tot = sum(ord(c.upper()) - 64 for c in al(S))
    add(str(tot), f"{al(S)[0]}{tot}", f"{tot}{al(S)[0]}")
    add(str(len(al(S))), str(len(wl(S))))
COMBO = al(A1 + A2 + A3 + A4 + A5)
add(COMBO, COMBO.lower(), COMBO[::-1], COMBO.lower()[::-1])
add(str(sum(ord(c) - 64 for c in COMBO)), str(len(COMBO)))
CR = al(R)
add(CR + COMBO, (CR + COMBO).lower(), COMBO + CR, (COMBO + CR).lower())

# ---------------------------------------------- 8. quote / dash typography
QUOTES = [('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"),
          ("«", "»"), ("", "")]
for l, r in QUOTES:
    for S in (R, R.rstrip("."), A1, A3, A4, A5):
        add(l + S + r, (l + S + r).lower())
for dash in ("-", "--", "—", "–", " - ", " — "):
    t = dash.join([A1, A3])
    add(t, t.lower(), ns(t).lower())
    t = dash.join([R, R])
    add(t, t.lower(), ns(t).lower())

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave3: {len(u)}\n")
