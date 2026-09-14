#!/usr/bin/env python3
"""Wave 2: the coinages put through the transforms a passphrase-picker uses
that are NOT plain case/space edits -- initialisms, leet, tagging, stop-word
stripping, vowel stripping, doubling, and the full coinage sequence."""
import re, sys, itertools
sys.path.insert(0, "/home/user/overdose/solver/coinage")
from gen_coinage import COINAGES

ALL = [s for s, _ in COINAGES]
T1  = [s for s, t in COINAGES if t == 1]

STOP = {"the","a","an","of","to","in","is","it","its","and","for","on","at",
        "with","that","this","be","are","was","as","up","by","from","some",
        "all","our","their","his","her","you","your","we","i","me","he","she"}

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.replace("’","'"))).strip()

out = set()

# 1. initialisms of every coinage
for s in ALL:
    ws = clean(s).split()
    if len(ws) >= 2:
        ini = "".join(w[0] for w in ws)
        out |= {ini.lower(), ini.upper(), ini}
        # keep multi-char tokens that are numbers/acronyms whole
        ini2 = "".join(w if (w.isupper() or w.isdigit()) else w[0] for w in ws)
        out |= {ini2, ini2.lower(), ini2.upper()}

# 2. leetspeak on the signature coinages
FULL = str.maketrans("aeiost", "431057")
VOW  = str.maketrans("aeio", "4310")
for s in T1:
    base = clean(s).lower()
    for v in (base, base.replace(" ", "")):
        out.add(v.translate(FULL))
        out.add(v.translate(VOW))
        out.add(v.translate(FULL).upper())

# 3. tagged coinages
TAGS = ["2021","2011","20","20BTC","20btc","btc","BTC","!","!!!","?",
        "MaxKeiser","maxkeiser","Keiser","keiser","Overdose","overdose",
        "OVERDOSE","ElSalvador","elsalvador","Bukele","bukele",
        "BitcoinMagazine","bitcoinmagazine","24","issue24","Satoshi","satoshi",
        "bitcoin","Bitcoin","Stacy","stacy","1","0","123"]
for s in T1:
    for v in (clean(s), clean(s).lower(), clean(s).lower().replace(" ", "")):
        for t in TAGS:
            out.add(v + t); out.add(t + v)
            out.add(v + " " + t); out.add(t + " " + v)

# 4. stop-word-stripped (content words only)
for s in ALL:
    ws = [w for w in clean(s).lower().split() if w not in STOP]
    if 1 < len(ws) < len(clean(s).split()):
        j = " ".join(ws)
        out |= {j, j.replace(" ", ""), j.replace(" ", "-"), j.upper(),
                j.title().replace(" ", "")}

# 5. vowel-stripped, signature coinages
for s in T1:
    v = clean(s).lower()
    dv = re.sub(r"[aeiou]", "", v)
    out |= {dv, dv.replace(" ", ""), dv.upper()}

# 6. doubled
for s in T1:
    v = clean(s).lower().replace(" ", "")
    if len(v) < 40:
        out.add(v + v)
        out.add(v + " " + v)

# 7. the full coinage sequence, several renderings
HEAD = ["UTXO ghetto","Toxic Bitcoin Maximalist","toxicity is Layer 1 of the protocol",
        "the Satoshi experience","monetary defibrillator to the treasure chest",
        "a stun gun to the genitals","rancid catnip of fiat money","fiat cuck-bucks",
        "hate toys","honey-badgering","Volcano Bonds","buying the dip",
        "black hole of the Cosmic Now","the Bitcoin rabbit hole",
        "central bank arsonists","banking terrorists","shitcoinery",
        "Keep your dignity","BITCOIN FIXES ALL THIS","Get some toxicity",
        "Get some bitcoin","Open your heart to Bitcoin","We've seen some shit",
        "the agony and ecstasy","51% attack on the world's energy supply"]
for n in (3, 4, 5, 6, 8, 10, 12, 25):
    for sub in (HEAD[:n], HEAD[-n:]):
        for j in (" ", "", "-", ", ", "_"):
            t = j.join(clean(x) for x in sub)
            out.add(t); out.add(t.lower())
        out.add(" ".join(clean(x).lower() for x in sub))
# acrostic of the coinage sequence
for n in (5, 10, 15, 20, 25):
    a = "".join(clean(x)[0] for x in HEAD[:n])
    out |= {a, a.lower(), a.upper()}

out = {x for x in out if 0 < len(x) < 400}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    for s in sorted(out):
        f.write(s + "\n")
sys.stderr.write(f"wave2: {len(out):,}\n")
