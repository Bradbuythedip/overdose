#!/usr/bin/env python3
"""Second full-HD batch: the most novel strings from waves 3-4."""
import re, sys, itertools
R  = "The economy of love is infinitely more efficient than hate and war."
A1, A3, A4, A5 = "BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", "MAX KEISER", "OVERDOSE"
A2_LINES = ["EVERY SINGLE ONE OF",
            "THE BITCOIN WANNABES - BCH, BSV, ETH, XRP,",
            "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT",
            "MONEY AND GOLD - IS FACING THE IGNOMINIOUS",
            "FATE OF DEMONETIZATION VERSUS BITCOIN."]
A2 = " ".join(A2_LINES)
TXT = open("/home/user/overdose/solver/article_transcript.txt", encoding="utf-8").read()
body, page = [], None
for ln in TXT.splitlines():
    if ln.startswith("#"): continue
    m = re.match(r"=== PAGE (\d+)", ln)
    if m: page = m.group(1); continue
    if page and ln.strip(): body.append((page, ln))
BODY = "\n".join(l for _, l in body)
HLP = [l.rstrip("\n").split("\t") for l in
       open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8")
       if not l.startswith("#") and l.count("\t") >= 2]

def ns(s): return re.sub(r"\s+", "", s)
def al(s): return re.sub(r"[^A-Za-z]", "", s)
def wl(s): return re.findall(r"[A-Za-z0-9]+", s)
def ini(s): return "".join(w[0] for w in wl(s))
out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900: out.append(s.replace("\n", " "))

# gap anomalies
AFT = ["Yes.", "central", "It's", "Fortunately,", "Get", "who"]
BEF = ["Really?", "traders,", "Fact:", "money.", "XRP.", "-"]
W   = [10, 3, 10, 3, 8, 5]
for seq in (AFT, BEF, [x for p in zip(BEF, AFT) for x in p]):
    for j in ("", " ", "-", "_"):
        t = j.join(seq)
        add(t, t.lower(), ns(t).lower(), re.sub(r"[^\w]", "", t),
            re.sub(r"[^\w]", "", t).lower())
    a = "".join(al(x)[0] for x in seq if al(x))
    add(a, a.lower(), a.upper(), a[::-1], a.upper()[::-1])
for j in ("", " ", "-", ","):
    add(j.join(str(x) for x in W), j.join(str(x) for x in reversed(W)))
a = "".join(chr(64 + x) for x in W)
add(a, a.lower(), a[::-1], a.lower()[::-1])

# all-caps token stream
CT = [re.sub(r"[^A-Z0-9]", "", t) for t in
      re.findall(r"\b[A-Z][A-Z0-9'\.]{1,}\b", BODY)]
CT = [t for t in CT if len(t) >= 2]
for seq in (CT, list(dict.fromkeys(CT)), list(reversed(CT))):
    for j in ("", " ", "-", "_"):
        t = j.join(seq); add(t, t.lower())
    a = "".join(x[0] for x in seq); add(a, a.lower(), a[::-1])
    a = "".join(x[-1] for x in seq); add(a, a.lower())

# capitals-only stream
CAPS_ONLY = "".join(c for c in BODY if c.isupper())
add(CAPS_ONLY, CAPS_ONLY.lower(), CAPS_ONLY[::-1], CAPS_ONLY.lower()[::-1])
for n in (2, 3, 5):
    for off in range(n):
        t = CAPS_ONLY[off::n]
        if len(t) > 3: add(t, t.lower())
PG = {}
for p, l in body: PG.setdefault(p, []).append(l)
for p, ls in PG.items():
    s = "".join(c for c in "\n".join(ls) if c.isupper())
    add(s, s.lower(), s[::-1])
    f = "".join(l.strip()[0] for l in ls if l.strip())
    add(f, f.lower(), f.upper(), al(f), al(f).lower(), al(f).upper())
FIRSTL = "".join(l.strip()[0] for _, l in body if l.strip())
LASTL  = "".join(l.strip()[-1] for _, l in body if l.strip())
for s in (FIRSTL, LASTL, al(FIRSTL), al(LASTL)):
    add(s, s.lower(), s.upper(), s[::-1])

# printed line break inside R
R_L1, R_L2 = "The economy of", "love is infinitely more efficient than hate and war."
for j in ("", " ", "-", "|"):
    for pair in ((R_L1, R_L2), (R_L2, R_L1)):
        t = j.join(pair)
        add(t, t.lower(), ns(t).lower())
add(R_L1, R_L1.lower(), R_L2, R_L2.lower(), ns(R_L2).lower())

# A2 line structure
for j in ("", " ", "-", "|"):
    t = j.join(A2_LINES); add(t, t.lower(), ns(t).lower())
    t = j.join(reversed(A2_LINES)); add(t, t.lower(), ns(t).lower())
for fn in (lambda x: x.strip()[0], lambda x: wl(x)[0], lambda x: wl(x)[-1],
           lambda x: ini(x)):
    a = "".join(fn(x) for x in A2_LINES); add(a, a.lower(), a.upper(), a[::-1])

# highlight colour orderings
ORANGE = [p[2] for p in HLP if p[1] == "orange"]
BLACK  = [p[2] for p in HLP if p[1] == "black"]
WHITE  = [p[2] for p in HLP if p[1] == "white"]
ALLH   = [p[2] for p in HLP]
for seq in (ORANGE, BLACK, WHITE, ORANGE + BLACK + WHITE, ALLH,
            list(reversed(ALLH))):
    for j in ("", " ", "-"):
        t = j.join(seq); add(t.lower(), ns(t).lower())
    a = "".join(x.strip()[0] for x in seq); add(a, a.lower(), a.upper(), a[::-1])
    b = "".join(ini(x) for x in seq); add(b, b.lower(), b.upper())
    for r in (R, R.lower(), ns(R).lower()):
        add((" ".join(seq) + " " + r).lower(), (r + " " + " ".join(seq)).lower())
cseq = "".join({"orange": "o", "black": "b", "white": "w"}[p[1]] for p in HLP)
add(cseq, cseq.upper(), cseq[::-1])
for m in ({"o": "0", "b": "1", "w": "2"}, {"o": "1", "b": "0", "w": "2"}):
    t = "".join(m[c] for c in cseq); add(t, t[::-1])

# hex extractions that land on exactly 64 chars
def hexchars(s): return "".join(c for c in s if c.upper() in "0123456789ABCDEF")
def hexletters(s): return "".join(c for c in s if c.upper() in "ABCDEF")
for S in (R, R + R, A1, A2, A3, A4, A5, A1 + A2 + A3 + A4 + A5, BODY,
          CAPS_ONLY, "".join(CT)):
    for f in (hexchars, hexletters):
        h = f(S)
        if len(h) >= 64:
            add(h[:64].upper(), h[:64].lower(), h[-64:].upper(), h[-64:].lower())
        elif h:
            add((h * (64 // len(h) + 1))[:64].upper(),
                (h * (64 // len(h) + 1))[:64].lower(),
                h.rjust(64, "0").upper(), h.ljust(64, "0").upper())

# case-pattern forms of the repeated sentence
def alt(s, ph):
    o, i = [], 0
    for c in s:
        if c.isalpha():
            o.append(c.upper() if (i + ph) % 2 == 0 else c.lower()); i += 1
        else: o.append(c)
    return "".join(o)
for S in (R, R.rstrip("."), ns(R)):
    for ph in (0, 1):
        add(alt(S, ph), ns(alt(S, ph)))
add("".join(c * 2 for c in R), "".join(c * 2 for c in ns(R)),
    " ".join(w + " " + w for w in R.split()))

# oddities x sentence
for o in ("mEthereum", "10years", "Bitcoins coattails", "UTXO", "AF"):
    for r in (R, R.lower(), ns(R).lower()):
        for j in ("", " ", "-"):
            add(o + j + r, r + j + o)

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"best2: {len(u)}\n")
