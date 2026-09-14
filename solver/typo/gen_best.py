#!/usr/bin/env python3
"""The highest-prior strings of the typographic lens, for the full HD pass."""
import re, sys
R  = "The economy of love is infinitely more efficient than hate and war."
A1 = "BITCOIN IS TOXIC AF"
A2 = ("EVERY SINGLE ONE OF THE BITCOIN WANNABES - BCH, BSV, ETH, XRP, "
      "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD - IS "
      "FACING THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.")
A2E = A2.replace(" - ", " — ")
A3 = "BITCOIN FIXES ALL THIS"
A4 = "MAX KEISER"
A5 = "OVERDOSE"
HL = [l.rstrip("\n").split("\t")[2] for l in
      open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8")
      if not l.startswith("#") and l.count("\t") >= 2]

def ns(s): return re.sub(r"\s+", "", s)
def wl(s): return re.findall(r"[A-Za-z0-9]+", s)
def ini(s): return "".join(w[0] for w in wl(s))
def al(s): return re.sub(r"[^A-Za-z]", "", s)
def npunct(s): return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s)).strip()

out = []
def add(*ss):
    for s in ss:
        if s and s.strip():
            out.append(s.replace("\n", " "))

Rn = R.rstrip(".")
# --- the repeated sentence, core forms
add(R, R.lower(), R.upper(), R.title(), Rn, Rn.lower(), Rn.upper(),
    ns(R), ns(R).lower(), ns(R).upper(), ns(Rn), ns(Rn).lower(), ns(Rn).upper(),
    npunct(R), npunct(R).lower(), npunct(R).upper(),
    al(R), al(R).lower(), al(R).upper(),
    R[::-1], R.lower()[::-1], ns(R)[::-1], ns(R).lower()[::-1],
    " ".join(reversed(R.split())), " ".join(reversed(Rn.split())).lower(),
    ini(R), ini(R).lower(), ini(R).upper(), ini(R)[::-1], ini(R).upper()[::-1],
    "_".join(w.lower() for w in wl(R)), "-".join(w.lower() for w in wl(R)),
    ".".join(w.lower() for w in wl(R)))
# --- printed twice: every plausible joiner on every core case
for base in (R, R.lower(), R.upper(), Rn, Rn.lower(), Rn.upper(),
             ns(R), ns(R).lower(), npunct(R), npunct(R).lower()):
    for j in ("", " ", "  ", ". ", ".", " - ", " — ", "-", "_", "|", " | ",
              "\t", "; ", ", ", " and "):
        add(base + j + base)
    add(base + " " + base + " " + base)
    add(base + base + base)
    add(base + base[::-1])
    add(base[::-1] + base)

# --- the all-caps blocks
for S in (A1, A2, A2E, A3, A4, A5):
    add(S, S.lower(), S.title(), ns(S), ns(S).lower(), npunct(S),
        npunct(S).lower(), al(S), al(S).lower(), ini(S), ini(S).lower(),
        S[::-1], ns(S).lower()[::-1])

# --- caps blocks in page order
for seq in ([A1, A2, A3, A4], [A5, A1, A2, A3, A4], [A1, A2, A3, A4, A5],
            [A1, A3], [A1, A3, A4], [A5, A1, A3, A4], [A1, A2E, A3, A4]):
    for j in ("", " ", " | ", "-", "_", ". ", "\t"):
        raw = j.join(seq)
        add(raw, raw.lower(), ns(raw), ns(raw).lower(), npunct(raw).lower())
    add("".join(ini(x) for x in seq), "".join(ini(x) for x in seq).lower(),
        "".join(x[0] for x in seq), "".join(x[0] for x in seq).lower())

# --- the sentence joined to each caps block, both orders
for S in (A1, A2, A2E, A3, A4, A5):
    for r in (R, R.lower(), Rn, Rn.lower(), ns(R).lower(), ini(R), ini(R).lower()):
        for c in (S, S.lower(), ns(S), ns(S).lower(), ini(S), ini(S).lower()):
            for j in ("", " ", " | ", "-", "_"):
                add(r + j + c, c + j + r)

# --- the sentence bracketing the whole caps sequence
for seq in ([A1, A2, A3, A4], [A5, A1, A2, A3, A4], [A1, A3]):
    for j in ("", " ", " | "):
        raw = j.join([R] + seq + [R])
        add(raw, raw.lower(), ns(raw).lower())
        raw = j.join([R] + seq)
        add(raw, raw.lower(), ns(raw).lower())
        raw = j.join(seq + [R])
        add(raw, raw.lower(), ns(raw).lower())

# --- highlight sequence forms combined with the sentence
hall = " ".join(HL)
for hv in (hall, hall.lower(), ns(hall).lower(),
           "".join(ini(x) for x in HL), "".join(ini(x) for x in HL).lower(),
           "".join(x.strip()[0] for x in HL),
           "".join(x.strip()[0] for x in HL).lower(),
           " ".join(wl(x)[0] for x in HL if wl(x)),
           " ".join(wl(x)[0] for x in HL if wl(x)).lower()):
    add(hv)
    for r in (R, R.lower(), ns(R).lower(), ini(R).lower()):
        for j in ("", " ", "|"):
            add(hv + j + r, r + j + hv)

# --- masthead / byline
for a in (A5, A5.lower(), A5.title()):
    for b in (A4, A4.lower(), ns(A4), ns(A4).lower(), "MaxKeiser", "maxkeiser"):
        for j in ("", " ", "-", "_", " | "):
            add(a + j + b, b + j + a)
    for r in (R, R.lower(), ns(R).lower(), ini(R).lower()):
        for j in ("", " ", "-", " | "):
            add(a + j + r, r + j + a)

# --- context tags on the sentence
for r in (R, R.lower(), Rn, Rn.lower(), ns(R).lower(), ini(R).lower()):
    for t in ("78", "p78", "page78", "24", "2021", "20BTC", "20",
              "ElSalvador", "BitcoinMagazine", "Overdose", "overdose",
              "MaxKeiser", "maxkeiser", "twice", "x2", "mirror"):
        for j in ("", " ", "-", "_"):
            add(r + j + t, t + j + r)

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"best: {len(u)}\n")
