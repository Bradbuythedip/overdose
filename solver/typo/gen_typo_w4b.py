#!/usr/bin/env python3
"""Wave 4b: readings of the six anomalous gap widths (10,3,10,3,8,5)."""
import itertools, re, sys
R  = "The economy of love is infinitely more efficient than hate and war."
A1, A3, A4, A5 = "BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", "MAX KEISER", "OVERDOSE"
W = [10, 3, 10, 3, 8, 5]
AFT = ["Yes.", "central", "It's", "Fortunately,", "Get", "who"]
BEF = ["Really?", "traders,", "Fact:", "money.", "XRP.", "—"]
def ns(s): return re.sub(r"\s+", "", s)
def al(s): return re.sub(r"[^A-Za-z]", "", s)
def ini(s): return "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", s))
out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900: out.append(s)

variants = []
for w in (W, list(reversed(W)), [x - 1 for x in W], [x - 2 for x in W]):
    for j in ("", " ", "-", ",", "."):
        variants.append(j.join(str(x) for x in w))
    a = "".join(chr(64 + x) for x in w if 1 <= x <= 26)
    variants += [a, a.lower(), a[::-1], a.lower()[::-1]]
    a = "".join(chr(96 + x) for x in w if 1 <= x <= 26)
    variants.append(a)
    variants.append("".join(f"{x:02d}" for x in w))
    variants.append("".join(f"{x:x}" for x in w))
    variants.append("".join(f"{x:b}" for x in w))
    variants.append(str(sum(w)))
    p = 1
    for x in w: p *= x
    variants.append(str(p))
for v in variants: add(v)

# gap widths used as letter offsets into the special strings
for S in (R, A1, A3, A4, A5, R + R, A1 + A3 + A4 + A5):
    a = al(S)
    for w in (W, list(reversed(W))):
        t = "".join(a[x - 1] for x in w if x - 1 < len(a))
        add(t, t.lower(), t.upper())
        idx, acc = 0, []
        for x in w:
            idx += x
            if idx - 1 < len(a): acc.append(a[idx - 1])
        t = "".join(acc); add(t, t.lower(), t.upper())
    ws = S.split()
    for w in (W, list(reversed(W))):
        t = " ".join(ws[x - 1] for x in w if x - 1 < len(ws))
        add(t, t.lower(), ns(t).lower())

# gap words in every combination with the special strings
SEQ = {"aft": AFT, "bef": BEF, "both": [x for p in zip(BEF, AFT) for x in p]}
for _, seq in SEQ.items():
    base = " ".join(seq)
    for j in ("", " ", "-", "_"):
        t = j.join(seq)
        add(t, t.lower(), ns(t), ns(t).lower(),
            re.sub(r"[^\w]", "", t), re.sub(r"[^\w]", "", t).lower())
    a = "".join(al(x)[0] for x in seq if al(x))
    for t in (a, a.lower(), a.upper(), a[::-1], a.upper()[::-1]):
        add(t)
    for S in (R, A1, A3, A4, A5):
        for j in ("", " ", "-", "|"):
            add(base + j + S, S + j + base, a + j + S, S + j + a)
            add((base + j + S).lower(), (S + j + base).lower())
            add((a + j + ns(S)).lower(), (ns(S) + j + a).lower())
# permutations of the six after-words / before-words
for seq in (AFT, BEF):
    for perm in itertools.permutations(seq):
        t = " ".join(perm)
        add(t.lower(), ns(t).lower())
seen, u = set(), []
for s in out:
    s = s.replace("\n", " ")
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave4b: {len(u)}\n")
