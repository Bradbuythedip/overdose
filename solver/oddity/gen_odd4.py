#!/usr/bin/env python3
"""Wave 4: extraction ANCHORED on the anomalies (not global every-Nth),
the lone caps-in-prose word, bit-masks used as selectors, and misc."""
import re, itertools
RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
B = '\n'.join(l for l in RAW.split('\n') if not l.startswith('#') and not l.startswith('==='))
FLAT = re.sub(r'\s+', ' ', B).strip()
LET = ''.join(c for c in FLAT if c.isalpha())
LETL = LET.lower()
WORDS = FLAT.split()
out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = x.strip()
        if 3 < len(x) < 4000: out.append(x)
def addv(*xs):
    for s in xs:
        if not s: continue
        add(s, s.lower(), s.upper(), s[::-1], s.lower()[::-1])

# ---- 1. ELS ANCHORED AT EACH ANOMALY ---------------------------------------
ANCH = {
 'mEthereum': FLAT.find('mEthereum'),
 '10years':   FLAT.find('10years'),
 'Bitcoins':  FLAT.find('Bitcoins coattails'),
 'BILLION':   FLAT.find('$85 BILLION'),
 'FullStop':  FLAT.find('Full Stop'),
 'shitcoinery': FLAT.find('shitcoinery'),
 'gargantuanly': FLAT.find('gargantuanly'),
 'salesmen':  FLAT.find('snake oil salesmen'),
 'pouring':   FLAT.find('pouring over'),
 'hyperbit':  FLAT.find('hyperbitcoinized'),
 'UTXO':      FLAT.find('UTXO'),
 'Vatican':   FLAT.find('Vatican'),
 'Costello':  FLAT.find('Elvis Costello'),
 'openparen': FLAT.find('(Sorry Bhutan'),
}
# map char offset -> letter-stream offset
pref = []
k = 0
for c in FLAT:
    pref.append(k)
    if c.isalpha(): k += 1
def letpos(cpos):
    return pref[cpos] if 0 <= cpos < len(pref) else -1

for name, cpos in ANCH.items():
    if cpos < 0: continue
    lp = letpos(cpos)
    for skip in list(range(2, 31)) + [42, 51, 73, 79, 95]:
        for ln in (12, 20, 32, 48):
            s = LET[lp::skip][:ln]
            if len(s) == ln:
                add(s, s.lower())
            s2 = LET[:lp+1][::-1][::skip][:ln]
            if len(s2) == ln:
                add(s2, s2.lower())
    # word-level skip anchored here
    wi = len(FLAT[:cpos].split())
    for skip in range(2, 16):
        ws = WORDS[wi::skip][:14]
        if len(ws) >= 6:
            t = ' '.join(w.strip('.,?!";:()') for w in ws)
            add(t, t.lower(), ''.join(w.strip('.,?!";:()') for w in ws).lower(),
                ''.join(w[0] for w in ws if w), ''.join(w[0] for w in ws if w).lower())

# ---- 2. THE LONE CAPS-IN-PROSE WORD ----------------------------------------
addv('BILLION', '85 BILLION', '$85 BILLION', 'BILLION billion billions',
     'billion BILLION', '85BILLION', 'America left 85 BILLION worth of hate toys',
     '85000000000', '85 BILLION 2 trillion 1 billion')
for a in ['BILLION', 'billion']:
    for b in ['85', '20', 'OVERDOSE', 'Afghanistan', 'hate toys', '2 trillion']:
        add(a + b, a + ' ' + b, b + a, b + ' ' + a)

# ---- 3. BIT MASKS USED AS SELECTORS (not as key bytes) ---------------------
import sys
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from bits import CHANNELS
SENTS = [s.strip() for s in re.split(r'(?<=[.!?])\s+', FLAT) if s.strip()]
LINES = [l.strip() for l in B.split('\n') if l.strip()]
for cname, bits in CHANNELS.items():
    for unit, name in ((WORDS, 'w'), (SENTS, 's'), (LINES, 'l')):
        for pol in ('1', '0'):
            sel = [unit[i] for i, b in enumerate(bits) if i < len(unit) and b == pol]
            if 3 <= len(sel) <= 60:
                t = ' '.join(x.strip('.,?!";:()') for x in sel)
                add(t, t.lower(), ''.join(x.strip('.,?!";:()') for x in sel),
                    ''.join(x.strip('.,?!";:()') for x in sel).lower(),
                    ''.join(x[0] for x in sel if x), ''.join(x[0] for x in sel if x).lower())

# the A1 mask over the 30 bitcoin-token NEIGHBOURS
occ = [(m.start(), m.group(0)) for m in re.finditer(r"\b[Bb]itcoin[a-z']*\b", FLAT)]
a1 = CHANNELS['A1_bcfam']
for pol in ('1', '0'):
    nb = []
    for i, (p, w) in enumerate(occ):
        if i < len(a1) and a1[i] == pol:
            tail = FLAT[p + len(w):].split()
            if tail:
                t0 = tail[0].strip('.,?!";:()-—')
                if t0: nb.append(t0)
    if nb:
        add(' '.join(nb), ''.join(nb), ' '.join(nb).lower(),
            ''.join(x[0] for x in nb if x), ''.join(x[0] for x in nb if x).lower())

# ---- 4. FIRST/LAST ANCHORS -------------------------------------------------
addv('BITCOIN IS TOXIC AF MAX KEISER', 'MAX KEISER BITCOIN IS TOXIC AF',
     "Here's the bitter truth MAX KEISER", 'Overdose Bitcoin Is Toxic AF Max Keiser',
     'Heres love', 'BITCOINISTOXICAFMAXKEISER')
pagesplit = re.split(r'=== PAGE \d+ \([^)]*\) ===', RAW)[1:]
firsts, lasts = [], []
for p in pagesplit:
    ws = p.split()
    if ws: firsts.append(ws[0].strip('.,?!";:()')); lasts.append(ws[-1].strip('.,?!";:()'))
for lst in (firsts, lasts, firsts + lasts):
    add(' '.join(lst), ''.join(lst), ' '.join(lst).lower(),
        ''.join(x[0] for x in lst if x), ''.join(x[0] for x in lst if x).lower())

# ---- 5. THE NIXON SHOCK / DATE ARITHMETIC ---------------------------------
addv('post-1971', 'post1971', 'August 15 1971', '19710815', '15081971',
     'Nixon shock', 'Forty years post 1971', '1971 2011 2021',
     '1971+40', '1971+50', '2011', '2021', '1517', '2017', '1969',
     '1971 1969 2008 2011 2017 2021')
YEARS = ['2008', '1971', '2011', '2017', '1969', '2021']
for sep in ['', ' ', '-', ',', '/']:
    add(sep.join(YEARS)); add(sep.join(sorted(YEARS))); add(sep.join(YEARS[::-1]))
for c in itertools.permutations(['1969', '1971', '2008'], 3):
    add(''.join(c))

# ---- 6. WORDS THAT APPEAR EXACTLY ONCE IN THE PIECE, in order (hapax) ------
toks = [w.strip('.,?!";:()—').lower() for w in WORDS]
toks = [t for t in toks if t and t[0].isalpha()]
from collections import Counter
cnt = Counter(toks)
hap = [t for t in toks if cnt[t] == 1]
for k in (16, 24, 32, 48):
    add(' '.join(hap[:k]), ''.join(hap[:k]), ''.join(x[0] for x in hap[:k] if x))
    add(' '.join(hap[-k:]), ''.join(hap[-k:]))
add(''.join(x[0] for x in hap if x), ''.join(x[0] for x in hap if x)[:64])

# ---- 7. "OVERDOSE" NEVER APPEARS IN THE BODY -------------------------------
addv('the word overdose does not appear', 'Overdose is not in the text',
     'OVERDOSE', 'OVERDOSE OVERDOSE', 'O V E R D O S E', 'esodrevo',
     'OVERDOSE 20 BTC MAX KEISER', 'Overdose Max Keiser Bitcoin Magazine El Salvador')

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
