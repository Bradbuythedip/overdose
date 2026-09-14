#!/usr/bin/env python3
"""Wave 2 of the typographic lens: word-surgery, leet, encodings, cross-joins."""
import base64, codecs, itertools, re, sys

R  = "The economy of love is infinitely more efficient than hate and war."
A1 = "BITCOIN IS TOXIC AF"
A2 = ("EVERY SINGLE ONE OF THE BITCOIN WANNABES - BCH, BSV, ETH, XRP, "
      "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD - IS "
      "FACING THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.")
A3 = "BITCOIN FIXES ALL THIS"
A4 = "MAX KEISER"
A5 = "OVERDOSE"
SPECIAL = [("R", R), ("A1", A1), ("A2", A2), ("A3", A3), ("A4", A4), ("A5", A5)]

HL = []
for ln in open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    p = ln.rstrip("\n").split("\t")
    if len(p) >= 3:
        HL.append(p[2])

out = []
def add(s):
    if s and len(s) < 3900 and s.strip():
        out.append(s.replace("\n", " ").replace("\r", ""))

def wl(s):    return re.findall(r"[A-Za-z0-9]+", s)
def alpha(s): return re.sub(r"[^A-Za-z]", "", s)
def alnum(s): return re.sub(r"[^A-Za-z0-9]", "", s)
def ini(s):   return "".join(w[0] for w in wl(s))
def nospace(s): return re.sub(r"\s+", "", s)

# ------------------------------------------------- A. word surgery
for tag, S in SPECIAL:
    ws = S.split()
    n = len(ws)
    # one word uppercased / lowercased / removed / doubled
    for i in range(n):
        for mk in (lambda w: w.upper(), lambda w: w.lower(),
                   lambda w: w.capitalize()):
            v = ws[:]; v[i] = mk(v[i]); t = " ".join(v)
            add(t); add(nospace(t))
        v = ws[:i] + ws[i+1:]
        if v:
            t = " ".join(v); add(t); add(t.lower()); add(nospace(t).lower())
        v = ws[:i] + [ws[i]] + ws[i:]
        t = " ".join(v); add(t); add(t.lower()); add(nospace(t).lower())
    # rotations of word order
    for k in range(1, n):
        t = " ".join(ws[k:] + ws[:k])
        add(t); add(t.lower()); add(t.upper()); add(nospace(t).lower())
    # split-and-swap at every boundary
    for k in range(1, n):
        t = " ".join(ws[k:]) + " " + " ".join(ws[:k])
        add(t); add(t.lower()); add(nospace(t).lower())
    # replace each word by its length
    lens = [str(len(alnum(w))) for w in ws]
    for j in ("", " ", "-", ",", "."):
        t = j.join(lens); add(t)
    # initials interleaved with lengths
    t = "".join(w[0] + str(len(alnum(w))) for w in wl(S))
    add(t); add(t.lower()); add(t.upper())
    t = "".join(str(len(alnum(w))) + w[0] for w in wl(S))
    add(t); add(t.lower()); add(t.upper())
    # A1Z26 of initials
    a = [str(ord(c.upper()) - 64) for c in ini(S) if c.isalpha()]
    for j in ("", " ", "-", ".", ","):
        t = j.join(a); add(t)
    # A1Z26 of every letter
    a2 = [str(ord(c.upper()) - 64) for c in alpha(S)]
    for j in ("", " ", "-"):
        t = j.join(a2)
        if len(t) < 3900: add(t)
    # letter/word counts
    add(f"{tag}{len(alpha(S))}"); add(str(len(alpha(S)))); add(str(len(ws)))
    add(f"{len(ws)}words"); add(f"{len(alpha(S))}letters")

# ------------------------------------------------- B. leet / substitution
SUBS = [
    ({"o": "0", "O": "0"}, "o0"),
    ({"i": "1", "I": "1", "l": "1", "L": "1"}, "i1"),
    ({"e": "3", "E": "3"}, "e3"),
    ({"a": "4", "A": "4"}, "a4"),
    ({"s": "5", "S": "5"}, "s5"),
    ({"t": "7", "T": "7"}, "t7"),
    ({"o": "0", "O": "0", "i": "1", "I": "1", "e": "3", "E": "3"}, "oie"),
    ({"o": "0", "O": "0", "i": "1", "I": "1", "e": "3", "E": "3",
      "a": "4", "A": "4", "s": "5", "S": "5", "t": "7", "T": "7"}, "full"),
]
def sub(s, m):
    return "".join(m.get(c, c) for c in s)
for tag, S in SPECIAL:
    for m, _ in SUBS:
        for base in (S, S.lower(), S.upper(), nospace(S), nospace(S).lower()):
            t = sub(base, m)
            add(t)
            add(re.sub(r"[^\w]", "", t))

# ------------------------------------------------- C. vowels / consonants
VOW = set("aeiouAEIOU")
for tag, S in SPECIAL:
    cons = "".join(c for c in alpha(S) if c not in VOW)
    vows = "".join(c for c in alpha(S) if c in VOW)
    for t in (cons, cons.lower(), cons.upper(), cons[::-1],
              vows, vows.lower(), vows.upper(), vows[::-1]):
        add(t)
    # vowel-stripped but spaces kept
    t = " ".join("".join(c for c in w if c not in VOW) for w in S.split())
    add(t); add(t.lower()); add(t.upper()); add(nospace(t).lower())

# ------------------------------------------------- D. rot13 / atbash / encodings
def atbash(s):
    o = []
    for c in s:
        if "a" <= c <= "z": o.append(chr(219 - ord(c)))
        elif "A" <= c <= "Z": o.append(chr(155 - ord(c)))
        else: o.append(c)
    return "".join(o)
for tag, S in SPECIAL:
    for base in (S, S.lower(), S.upper(), nospace(S), nospace(S).lower(),
                 alpha(S), alpha(S).lower()):
        add(codecs.encode(base, "rot13"))
        add(atbash(base))
        b = base.encode()
        add(base64.b64encode(b).decode())
        add(base64.b64encode(b).decode().rstrip("="))
        add(base64.b32encode(b).decode())
        add(b.hex())
        add(b.hex().upper())
# hex of the repeated sentence doubled, and of caps concatenations
for base in (R + R, R + " " + R, nospace(R) * 2, (A1 + A3), (A1 + " " + A3),
             (A1 + A2 + A3 + A4), A5 + R):
    b = base.encode()
    add(b.hex()); add(base64.b64encode(b).decode())
    add(codecs.encode(base, "rot13")); add(atbash(base))

# ------------------------------------------------- E. context tags
TAGS = ["78", "p78", "page78", "P78", "pg78", "24", "issue24", "Issue24",
        "73-79", "7379", "2021", "ElSalvador", "El Salvador", "elsalvador",
        "BitcoinMagazine", "Bitcoin Magazine", "bitcoinmagazine",
        "20BTC", "20 BTC", "20btc", "20", "MaxKeiser", "maxkeiser",
        "Overdose", "overdose", "OVERDOSE", "twice", "x2", "2x", "again",
        "repeat", "echo", "mirror", "Mirror", "MIRROR", "Fall2021"]
R_BASES = [R, R.lower(), R.upper(), R.rstrip("."), R.rstrip(".").lower(),
           nospace(R), nospace(R).lower(), alpha(R).lower(), ini(R),
           ini(R).lower(), R[::-1], nospace(R).lower()[::-1]]
for r in R_BASES:
    for t in TAGS:
        for j in ("", " ", "-", "_", ":", "|"):
            add(r + j + t); add(t + j + r)
CAPS_BASES = [A1, A3, A4, A5, A1 + " " + A3, A1 + A3,
              nospace(A1).lower(), nospace(A3).lower(),
              A1.lower(), A3.lower(), A4.lower(), A5.lower()]
for c in CAPS_BASES:
    for t in TAGS:
        for j in ("", " ", "-", "_"):
            add(c + j + t); add(t + j + c)

# ------------------------------------------------- F. R x each highlight run
for h in HL:
    hf = [h, h.lower(), nospace(h), nospace(h).lower(), alpha(h).lower(), ini(h)]
    for hv in hf:
        for r in (R, R.lower(), nospace(R).lower(), ini(R), ini(R).lower()):
            for j in ("", " ", "|", "-"):
                add(r + j + hv); add(hv + j + r)
    for cb in (A1, A3, A4, A5):
        for j in ("", " ", "-"):
            add(cb + j + h); add(h + j + cb)
            add((cb + j + h).lower()); add((h + j + cb).lower())

# ------------------------------------------------- G. words of A2 x R
A2W = [w for w in wl(A2)]
for w in A2W:
    for r in (R, R.lower(), nospace(R).lower(), ini(R)):
        for j in ("", " ", "-", "_"):
            add(w + j + r); add(r + j + w)
            add((w + j + r).lower()); add((r + j + w).lower())

# ------------------------------------------------- H. every-nth over the caps run
CAPSRUN = nospace(A1 + A2 + A3 + A4 + A5)
CAPSRUN_A = alpha(A1 + A2 + A3 + A4 + A5)
for base in (CAPSRUN, CAPSRUN_A):
    for n in range(2, 13):
        for off in range(n):
            t = base[off::n]
            if 3 < len(t) < 3900:
                add(t); add(t.lower()); add(t[::-1])
# every-nth over the doubled sentence
DBL = nospace(R + R)
DBLA = alpha(R + R)
for base in (DBL, DBLA, DBL.lower(), DBLA.lower()):
    for n in range(2, 13):
        for off in range(n):
            t = base[off::n]
            if 3 < len(t) < 3900:
                add(t); add(t[::-1])

# ------------------------------------------------- I. interleave the two printings
a, b = nospace(R), nospace(R)[::-1]
add("".join(x + y for x, y in zip(a, b)))
add("".join(x + y for x, y in zip(a.lower(), b.lower())))
a2, b2 = R.split(), list(reversed(R.split()))
add(" ".join(x + " " + y for x, y in zip(a2, b2)))
add(" ".join(x + " " + y for x, y in zip(a2, b2)).lower())
# interleave R with each caps block
for cb in (A1, A3, A4, A5):
    x, y = nospace(R).lower(), nospace(cb).lower()
    add("".join(p + q for p, q in zip(x, y)))
    add("".join(p + q for p, q in zip(y, x)))

seen, uniq = set(), []
for s in out:
    if s not in seen:
        seen.add(s); uniq.append(s)
sys.stdout.write("\n".join(uniq) + "\n")
sys.stderr.write(f"wave2: {len(uniq)} unique\n")
