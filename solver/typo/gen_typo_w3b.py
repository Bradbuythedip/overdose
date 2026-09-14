#!/usr/bin/env python3
"""Wave 3b: the whole special-text stream in reading order, plus pair/triple
concatenations of the set-apart blocks and highlight windows joined to the
repeated sentence."""
import itertools, re, sys

R  = "The economy of love is infinitely more efficient than hate and war."
A1 = "BITCOIN IS TOXIC AF"
A2 = ("EVERY SINGLE ONE OF THE BITCOIN WANNABES - BCH, BSV, ETH, XRP, "
      "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD - IS "
      "FACING THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.")
A3 = "BITCOIN FIXES ALL THIS"
A4 = "MAX KEISER"
A5 = "OVERDOSE"

HLP = []
for ln in open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8"):
    if ln.startswith("#") or ln.count("\t") < 2: continue
    p = ln.rstrip("\n").split("\t")
    HLP.append((p[0], p[1], p[2]))

def ns(s):  return re.sub(r"\s+", "", s)
def wl(s):  return re.findall(r"[A-Za-z0-9]+", s)
def al(s):  return re.sub(r"[^A-Za-z]", "", s)
def ini(s): return "".join(w[0] for w in wl(s))
def cl(s):  return re.sub(r"\s+", " ", s).strip()

out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900:
            out.append(s.replace("\n", " ").replace("\r", ""))

hl = lambda pg: [t for p, c, t in HLP if p == pg]

# ------------------------------------------------ 1. the special-text stream
STREAM = ([A5, A1] + hl("75") + hl("76") + hl("77") + [A2] + hl("78")
          + [A3, R] + hl("79") + [A4])
STREAM_R2 = ([A5, A1] + hl("75") + hl("76") + hl("77") + [A2] + hl("78")
             + [R, A3, R] + hl("79") + [A4])          # both printings of R
STREAM_CAPS = [A5, A1, A2, A3, R, A4]
STREAM_NOHL = [A1, A2, A3, R, A4, A5]

def readings(seq, tag):
    for j in ("", " ", " | ", "-", "_", ".", "/"):
        raw = j.join(seq)
        add(raw, raw.lower(), ns(raw), ns(raw).lower(),
            cl(re.sub(r"[^\w\s]", "", raw)).lower())
    for fn, nm in ((lambda x: x.strip()[0], "f"),
                   (lambda x: x.strip()[-1], "l"),
                   (lambda x: wl(x)[0] if wl(x) else "", "fw"),
                   (lambda x: wl(x)[-1] if wl(x) else "", "lw"),
                   (lambda x: ini(x), "ini"),
                   (lambda x: al(x)[:2] if len(al(x)) > 1 else al(x), "f2"),
                   (lambda x: al(x)[-2:] if len(al(x)) > 1 else al(x), "l2"),
                   (lambda x: str(len(wl(x))), "nw"),
                   (lambda x: str(len(al(x))), "nl")):
        for j in ("", " ", "-", "_", "."):
            b = j.join(fn(x) for x in seq if fn(x))
            add(b, b.lower(), b.upper())
            if j == "":
                add(b[::-1], b.lower()[::-1], b.upper()[::-1])
    # every-nth item of the stream
    for n in (2, 3, 4, 5):
        for off in range(n):
            sub = seq[off::n]
            if len(sub) > 1:
                for j in ("", " ", "-"):
                    t = j.join(sub)
                    add(t.lower(), ns(t).lower())
                a = "".join(x.strip()[0] for x in sub)
                add(a, a.lower(), a.upper())
    # every-nth letter over the whole squashed stream
    base = ns(" ".join(seq))
    basea = al(" ".join(seq))
    for b in (base, basea, base.lower(), basea.lower()):
        for n in (2, 3, 5, 7, 11, 13):
            for off in range(min(n, 4)):
                t = b[off::n]
                if 3 < len(t) < 3900:
                    add(t)

for seq, tag in ((STREAM, "stream"), (STREAM_R2, "streamR2"),
                 (STREAM_CAPS, "caps"), (STREAM_NOHL, "nohl"),
                 (list(reversed(STREAM)), "streamrev"),
                 (list(reversed(STREAM_CAPS)), "capsrev")):
    readings(seq, tag)

# ------------------------------------------------ 2. caps x caps pairs/triples
CAPS = [A1, A2, A3, A4, A5]
def cforms(s):
    return [s, s.lower(), ns(s), ns(s).lower(), ini(s), ini(s).lower(),
            al(s), al(s).lower(), s.title()]
for x, y in itertools.permutations(CAPS, 2):
    for fx in cforms(x)[:6]:
        for fy in cforms(y)[:6]:
            for j in ("", " ", "-", "_", "|", "."):
                add(fx + j + fy)
for trip in itertools.permutations(CAPS, 3):
    for j in ("", " ", "-", "_"):
        t = j.join(trip)
        add(t, t.lower(), ns(t), ns(t).lower())
        t = j.join(ini(x) for x in trip)
        add(t, t.lower(), t.upper())

# ------------------------------------------------ 3. highlight windows + R
HLT = [t for _, _, t in HLP]
RF = [R, R.lower(), ns(R).lower(), ini(R), ini(R).lower(), R.rstrip(".")]
for w in (2, 3, 4, 5, 6):
    for i in range(len(HLT) - w + 1):
        win = HLT[i:i+w]
        for j in (" ", "", "-"):
            t = j.join(win)
            add(t.lower(), ns(t).lower())
        a = "".join(x.strip()[0] for x in win)
        add(a, a.lower(), a.upper())
        b = "".join(ini(x) for x in win)
        add(b, b.lower())
        if w in (2, 3):
            for r in RF[:3]:
                add((" ".join(win) + " " + r), (r + " " + " ".join(win)).lower())

# ------------------------------------------------ 4. colour-coded readings
ORANGE = [t for _, c, t in HLP if c == "orange"]
BLACK  = [t for _, c, t in HLP if c == "black"]
WHITE  = [t for _, c, t in HLP if c == "white"]
for name, seq in (("orange", ORANGE), ("black", BLACK), ("white", WHITE),
                  ("ob", ORANGE + BLACK), ("bo", BLACK + ORANGE),
                  ("obw", ORANGE + BLACK + WHITE),
                  ("bw", BLACK + WHITE), ("wb", WHITE + BLACK)):
    for j in ("", " ", "-", "_"):
        t = j.join(seq)
        add(t.lower(), ns(t).lower())
    a = "".join(x.strip()[0] for x in seq)
    add(a, a.lower(), a.upper(), a[::-1])
    b = "".join(ini(x) for x in seq)
    add(b, b.lower(), b.upper())
    for r in RF[:4]:
        for j in ("", " ", "|"):
            add((" ".join(seq) + j + r).lower())
            add((r + j + " ".join(seq)).lower())
            add(a + j + r, r + j + a)
# colour as a binary/ternary string over the ordered highlights
cseq = "".join({"orange": "o", "black": "b", "white": "w"}[c] for _, c, _ in HLP)
for m in ({"o": "0", "b": "1", "w": "2"}, {"o": "1", "b": "0", "w": "2"},
          {"o": "O", "b": "B", "w": "W"}, {"o": "0", "b": "1", "w": "0"},
          {"o": "1", "b": "1", "w": "0"}):
    t = "".join(m[c] for c in cseq)
    add(t, t[::-1])
    for r in RF[:3]:
        add(t + r, r + t, (t + " " + r).lower())
add(cseq, cseq.upper(), cseq[::-1])

seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave3b: {len(u)}\n")
