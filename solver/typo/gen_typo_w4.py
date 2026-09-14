#!/usr/bin/env python3
"""Wave 4: typography beyond the blocks -- the ALL-CAPS token stream across the
whole piece, the capitals-only character stream, hex-valid letter extraction,
and the words sitting either side of the anomalous multi-space gaps."""
import itertools, re, sys

TXT = open("/home/user/overdose/solver/article_transcript.txt", encoding="utf-8").read()
body_lines, page = [], None
for ln in TXT.splitlines():
    if ln.startswith("#"): continue
    m = re.match(r"=== PAGE (\d+)", ln)
    if m:
        page = m.group(1); continue
    if page and ln.strip():
        body_lines.append((page, ln))
BODY = "\n".join(l for _, l in body_lines)

R  = "The economy of love is infinitely more efficient than hate and war."
A1 = "BITCOIN IS TOXIC AF"
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

# ---------------------------------------------- 1. ALL-CAPS token stream
CAPTOK = re.findall(r"\b[A-Z][A-Z0-9'\.]{1,}\b", BODY)
CAPTOK = [t for t in CAPTOK if sum(c.isalpha() for c in t) >= 2]
CAPTOK_CLEAN = [re.sub(r"[^A-Z0-9]", "", t) for t in CAPTOK]
CAPTOK_CLEAN = [t for t in CAPTOK_CLEAN if t]
sys.stderr.write(f"all-caps tokens ({len(CAPTOK_CLEAN)}): "
                 f"{' '.join(CAPTOK_CLEAN[:40])}\n")
for seq in (CAPTOK_CLEAN, list(reversed(CAPTOK_CLEAN)),
            list(dict.fromkeys(CAPTOK_CLEAN))):
    for j in ("", " ", "-", "_", "."):
        t = j.join(seq)
        add(t, t.lower(), ns(t), ns(t).lower())
    a = "".join(x[0] for x in seq); add(a, a.lower(), a[::-1])
    b = "".join(x[-1] for x in seq); add(b, b.lower(), b[::-1])
    for n in (2, 3, 4, 5):
        for off in range(n):
            sub = seq[off::n]
            if len(sub) > 1:
                for j in ("", " "):
                    t = j.join(sub); add(t, t.lower())
                a = "".join(x[0] for x in sub); add(a, a.lower())
# caps tokens joined to the repeated sentence
CAPJ = [" ".join(CAPTOK_CLEAN), "".join(CAPTOK_CLEAN),
        "".join(x[0] for x in CAPTOK_CLEAN)]
for c in CAPJ:
    for r in (R, R.lower(), ns(R).lower(), ini(R), ini(R).lower()):
        for j in ("", " ", "|", "-"):
            add(c + j + r, r + j + c, (c + j + r).lower())

# ---------------------------------------------- 2. capitals-only char stream
def capsonly(s): return "".join(c for c in s if c.isupper())
WHOLE = capsonly(BODY)
sys.stderr.write(f"capitals-only stream: {len(WHOLE)} chars\n")
PAGES = {}
for p, l in body_lines:
    PAGES.setdefault(p, []).append(l)
streams = {"all": WHOLE}
for p, ls in PAGES.items():
    streams[p] = capsonly("\n".join(ls))
for name, S in streams.items():
    add(S, S.lower(), S[::-1], S.lower()[::-1])
    for n in (2, 3, 4, 5, 7):
        for off in range(min(n, 3)):
            t = S[off::n]
            if 3 < len(t) < 3900: add(t, t.lower())
    for w in (32, 64):
        for i in range(0, max(1, len(S) - w + 1), max(1, w // 4)):
            t = S[i:i+w]
            if len(t) == w: add(t, t.lower())
# lowercase-only stream of the caps blocks region? and first-letter-of-line
FIRSTL = "".join(l.strip()[0] for _, l in body_lines if l.strip())
LASTL  = "".join(l.strip()[-1] for _, l in body_lines if l.strip())
for S in (FIRSTL, LASTL):
    add(S, S.lower(), S.upper(), S[::-1], al(S), al(S).lower(), al(S).upper())
    for n in (2, 3, 5):
        for off in range(n):
            t = al(S)[off::n]
            if 3 < len(t) < 3900: add(t, t.lower(), t.upper())
for p, ls in PAGES.items():
    f = "".join(l.strip()[0] for l in ls if l.strip())
    la = "".join(l.strip()[-1] for l in ls if l.strip())
    for S in (f, la):
        add(S, S.lower(), S.upper(), S[::-1], al(S), al(S).lower(), al(S).upper())

# ---------------------------------------------- 3. hex-valid letter extraction
def hexletters(s): return "".join(c for c in s if c.upper() in "ABCDEF")
def hexchars(s):   return "".join(c for c in s if c.upper() in "0123456789ABCDEF")
SRC = {
    "R": R, "A1": A1, "A3": A3, "A4": A4, "A5": A5,
    "RR": R + R, "caps": A1 + A3 + A4 + A5,
    "A2": ("EVERY SINGLE ONE OF THE BITCOIN WANNABES BCH BSV ETH XRP ADA AND "
           "12000 OTHER SHITCOINS PLUS FIAT MONEY AND GOLD IS FACING THE "
           "IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN"),
    "body": BODY, "capsonly": WHOLE,
    "captok": "".join(CAPTOK_CLEAN),
}
for name, S in SRC.items():
    for f in (hexletters, hexchars):
        h = f(S)
        if not h: continue
        for t in (h.upper(), h.lower()):
            add(t)
            if len(t) >= 64:
                add(t[:64], t[-64:])
                for i in range(0, min(len(t) - 63, 2000), 8):
                    add(t[i:i+64])
            else:
                add((t * (64 // max(1, len(t)) + 1))[:64])
                add(t.rjust(64, "0"), t.ljust(64, "0"))

# ---------------------------------------------- 4. multi-space gap anomalies
GAPS = []   # (before_word, after_word, gap_len, page)
for p, l in body_lines:
    for m in re.finditer(r"(\S+)(\s{2,})(\S+)", l):
        GAPS.append((m.group(1), m.group(3), len(m.group(2)), p))
sys.stderr.write(f"multi-space gaps: {len(GAPS)} -> "
                 f"{[(a,b,n) for a,b,n,_ in GAPS]}\n")
BEF = [a for a, _, _, _ in GAPS]
AFT = [b for _, b, _, _ in GAPS]
LEN = [str(n) for _, _, n, _ in GAPS]
for seq in (BEF, AFT, BEF + AFT, AFT + BEF,
            [x for pair in zip(BEF, AFT) for x in pair]):
    for j in ("", " ", "-", "_"):
        t = j.join(seq)
        add(t, t.lower(), ns(t), ns(t).lower(),
            re.sub(r"[^\w]", "", t), re.sub(r"[^\w]", "", t).lower())
    a = "".join(al(x)[0] for x in seq if al(x))
    add(a, a.lower(), a.upper(), a[::-1], a.upper()[::-1])
    b = "".join(al(x)[-1] for x in seq if al(x))
    add(b, b.lower(), b.upper(), b[::-1])
for j in ("", " ", "-", ","):
    t = j.join(LEN); add(t)
# gap words joined to the repeated sentence
for seq in (AFT, BEF):
    base = " ".join(seq)
    a = "".join(al(x)[0] for x in seq if al(x))
    for r in (R, R.lower(), ns(R).lower(), ini(R), ini(R).lower()):
        for j in ("", " ", "|"):
            add(base + j + r, r + j + base, a + j + r, r + j + a)
            add((base + j + r).lower(), (r + j + base).lower())

# ---------------------------------------------- 5. one-off typographic oddities
ODD = ["mEthereum", "methereum", "MEthereum", "10years", "10 years",
       "Bitcoins coattails", "bitcoinscoattails", "Bitcoins",
       "UTXO", "IMF", "XRP", "AF", "BCH", "BSV", "ETH", "ADA",
       "Full Stop.", "FullStop", "fullstop",
       "(Sorry Bhutan, you fell for that snake oil salesmen over at XRP.",
       "Sorry Bhutan", "SorryBhutan"]
for o in ODD:
    add(o, o.lower(), o.upper(), ns(o), ns(o).lower())
    for r in (R, R.lower(), ns(R).lower(), ini(R).lower()):
        for j in ("", " ", "-", "_"):
            add(o + j + r, r + j + o, (o + j + r).lower(), (r + j + o).lower())
    for c in (A1, A3, A4, A5):
        for j in ("", " ", "-"):
            add(o + j + c, c + j + o, (o + j + c).lower(), (c + j + o).lower())

# ---------------------------------------------- 6. acrostic cross-products
ACR = {
    "R":   ini(R),
    "A1":  ini(A1), "A3": ini(A3), "A4": ini(A4), "A5": A5[0],
    "caps": "".join(x[0] for x in (A1, A3, A4, A5)),
    "capstok": "".join(x[0] for x in CAPTOK_CLEAN),
    "gapA": "".join(al(x)[0] for x in AFT if al(x)),
    "gapB": "".join(al(x)[0] for x in BEF if al(x)),
    "firstl": al(FIRSTL), "lastl": al(LASTL),
}
keys = list(ACR)
for a, b in itertools.permutations(keys, 2):
    x, y = ACR[a], ACR[b]
    if not x or not y: continue
    for j in ("", " ", "-", "_"):
        t = x + j + y
        if len(t) < 3900:
            add(t, t.lower(), t.upper())

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave4: {len(u)}\n")
