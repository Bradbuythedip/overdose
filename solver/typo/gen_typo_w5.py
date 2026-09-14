#!/usr/bin/env python3
"""Wave 5: repetition as the signal. Every phrase the piece prints more than
once, the words it uses exactly twice, plus block-on-block Vigenere/XOR and
letter-multiset readings of the special strings."""
import re, sys, itertools, collections

TXT = open("/home/user/overdose/solver/article_transcript.txt", encoding="utf-8").read()
body, page = [], None
for ln in TXT.splitlines():
    if ln.startswith("#"): continue
    m = re.match(r"=== PAGE (\d+)", ln)
    if m: page = m.group(1); continue
    if page and ln.strip(): body.append(ln)
BODY = " ".join(body)
R  = "The economy of love is infinitely more efficient than hate and war."
A1, A3, A4, A5 = "BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", "MAX KEISER", "OVERDOSE"
A2 = ("EVERY SINGLE ONE OF THE BITCOIN WANNABES - BCH, BSV, ETH, XRP, ADA, AND "
      "12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD - IS FACING THE "
      "IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.")

def ns(s): return re.sub(r"\s+", "", s)
def al(s): return re.sub(r"[^A-Za-z]", "", s)
def wl(s): return re.findall(r"[A-Za-z0-9]+", s)
def ini(s): return "".join(w[0] for w in wl(s))
out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900: out.append(s.replace("\n", " "))

# ------------------------------------------- 1. repeated n-grams
toks = [w.lower() for w in re.findall(r"[A-Za-z0-9']+", BODY)]
rep = {}
for n in range(2, 12):
    c = collections.Counter(tuple(toks[i:i+n]) for i in range(len(toks) - n + 1))
    for g, k in c.items():
        if k >= 2:
            rep.setdefault(n, []).append((" ".join(g), k))
# maximal repeated phrases: drop any that is a sub-phrase of a longer repeat
longest = []
for n in sorted(rep, reverse=True):
    for g, k in rep[n]:
        if not any(g in L for L, _ in longest):
            longest.append((g, k))
sys.stderr.write(f"maximal repeated phrases: {len(longest)}\n")
for g, k in longest[:30]:
    sys.stderr.write(f"   x{k}  {g}\n")
REPS = [g for g, _ in longest]
REPS_ORD = sorted(REPS, key=lambda g: BODY.lower().find(g))
for seq in (REPS_ORD, REPS, list(reversed(REPS_ORD))):
    for j in ("", " ", "-", "_", "|"):
        t = j.join(seq)
        add(t, t.upper(), ns(t), ns(t).upper())
    a = "".join(x[0] for x in seq); add(a, a.upper(), a[::-1])
    b = "".join(ini(x) for x in seq); add(b, b.upper(), b.lower())
    for k in (3, 5, 8, 12, 20):
        t = " ".join(seq[:k]); add(t, ns(t))
        t = " ".join(seq[-k:]); add(t, ns(t))
# each repeated phrase doubled (as the piece doubles the sentence)
for g in REPS:
    for j in ("", " ", ". "):
        add(g + j + g, (g + j + g).upper())
    add(g, g.upper(), g.title(), ns(g), ns(g).upper())
# repeated phrases joined to the sentence
for g in REPS[:60]:
    for r in (R, R.lower(), ns(R).lower()):
        for j in ("", " "):
            add(g + j + r, r + j + g, (g + j + r).lower())

# ------------------------------------------- 2. words used exactly twice
cnt = collections.Counter(toks)
twice = [w for w in dict.fromkeys(toks) if cnt[w] == 2]
sys.stderr.write(f"words used exactly twice: {len(twice)}\n")
for seq in (twice, list(reversed(twice)), sorted(twice)):
    for j in ("", " ", "-", "_"):
        t = j.join(seq)
        add(t, t.upper())
    a = "".join(w[0] for w in seq); add(a, a.upper(), a[::-1])
    for k in (12, 24, 32):
        t = " ".join(seq[:k]); add(t, ns(t))
# and words used exactly N times, N = 3,4
for n in (3, 4, 5):
    seq = [w for w in dict.fromkeys(toks) if cnt[w] == n]
    if not seq: continue
    for j in ("", " ", "-"):
        t = j.join(seq); add(t, t.upper())
    a = "".join(w[0] for w in seq); add(a, a.upper())

# ------------------------------------------- 3. block-on-block Vigenere
def vig(pt, key, dec=False):
    k = [ord(c.upper()) - 65 for c in al(key)]
    if not k: return ""
    o, i = [], 0
    for c in pt:
        if c.isalpha():
            b = 65 if c.isupper() else 97
            s = -k[i % len(k)] if dec else k[i % len(k)]
            o.append(chr((ord(c) - b + s) % 26 + b)); i += 1
        else: o.append(c)
    return "".join(o)
BLOCKS = {"R": R, "A1": A1, "A2": A2, "A3": A3, "A4": A4, "A5": A5}
for pn, pt in BLOCKS.items():
    for kn, key in BLOCKS.items():
        if pn == kn: continue
        for dec in (False, True):
            t = vig(pt, key, dec)
            add(t, t.lower(), t.upper(), ns(t), ns(t).lower())
    for key in ("OVERDOSE", "MAXKEISER", "BITCOIN", "SATOSHI", "ELSALVADOR",
                "LOVE", "WAR", "HATE", "ECONOMY", "TOXIC", "MIRROR"):
        for dec in (False, True):
            t = vig(pt, key, dec)
            add(t, t.lower(), ns(t).lower())

# ------------------------------------------- 4. block-on-block XOR -> hex
def xor_hex(a, b):
    ab, bb = a.encode(), b.encode()
    if not bb: return ""
    return bytes(x ^ bb[i % len(bb)] for i, x in enumerate(ab)).hex()
for an, a in BLOCKS.items():
    for bn, b in BLOCKS.items():
        if an == bn: continue
        for x, y in ((a, b), (ns(a).lower(), ns(b).lower()),
                     (al(a).upper(), al(b).upper())):
            h = xor_hex(x, y)
            if len(h) >= 64:
                add(h[:64], h[:64].upper(), h[-64:])
            elif h:
                add(h, h.upper(), h.ljust(64, "0"), h.rjust(64, "0"))

# ------------------------------------------- 5. letter-multiset readings
for name, S in BLOCKS.items():
    a = al(S).lower()
    seen_o = "".join(dict.fromkeys(a))                    # first occurrences
    add(seen_o, seen_o.upper(), seen_o[::-1])
    c = collections.Counter(a)
    dbl = "".join(ch for ch in dict.fromkeys(a) if c[ch] >= 2)
    add(dbl, dbl.upper(), dbl[::-1])
    once = "".join(ch for ch in dict.fromkeys(a) if c[ch] == 1)
    add(once, once.upper(), once[::-1])
    srt = "".join(sorted(a))
    add(srt, srt.upper(), srt[::-1])
    srtw = " ".join(sorted(S.split(), key=str.lower))
    add(srtw, srtw.lower(), ns(srtw).lower())
    freq = "".join(f"{ch}{c[ch]}" for ch in sorted(c))
    add(freq, freq.upper())

# ------------------------------------------- 6. the sentence around the page no.
for mid in ("78", "p78", "24", "20", "2021", "OVERDOSE", "overdose",
            "MAXKEISER", "BITCOIN", "LOVE", "WAR"):
    for base in (R, R.lower(), R.rstrip("."), ns(R).lower()):
        for j in ("", " ", "-"):
            add(base + j + mid + j + base)
# progressive initialisation of the sentence
ws = R.rstrip(".").split()
for k in range(1, len(ws) + 1):
    t = " ".join([w[0] for w in ws[:k]] + ws[k:])
    add(t, t.lower(), ns(t), ns(t).lower())
    t = " ".join(ws[:k] + [w[0] for w in ws[k:]])
    add(t, t.lower(), ns(t), ns(t).lower())

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave5: {len(u)}\n")
