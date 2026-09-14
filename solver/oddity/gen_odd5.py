#!/usr/bin/env python3
"""Wave 5: anomaly POSITIONS as key material, true mirror-glyph transforms of
the anomalies, self-indexing, and the short-display-line stream."""
import re, itertools
RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
B = '\n'.join(l for l in RAW.split('\n') if not l.startswith('#') and not l.startswith('==='))
FLAT = re.sub(r'\s+', ' ', B).strip()
WORDS = FLAT.split()
LET = ''.join(c for c in FLAT if c.isalpha())
out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = str(x).strip()
        if 2 < len(x) < 4000: out.append(x)
def addv(*xs):
    for s in xs:
        if not s: continue
        add(s, s.lower(), s.upper(), s[::-1], s.lower()[::-1],
            s.replace(' ', ''), s.replace(' ', '').lower())

# ------------------------------------------------ anomaly surface forms
ANOM = ['AF', 'cypherpunks', 'terrorists', 'arsonists', 'Cosmic', 'Nocoiners',
        'shitcoiners', 'Bitcoiners', 'Bitcoins', 'mEthereum', 'shitcoinery',
        'UTXO', "y'all", 'funkier', '10years', 'honey-badgering', 'psychotic',
        'catnip', 'lobotomy', 'defibrillator', 'hyperbitcoinized',
        'mind-bending', 'salesmen', 'Faketoshi', 'banksters', 'Stop',
        'eggheads', 'pouring', 'gargantuanly', 'uber', 'cuck-bucks',
        'oil-dripping', 'corpse-ridden', 'poppy-harvesting', 'game-theorized',
        'BILLION', 'bed-in']

# ------------------------------------------------ 1. POSITIONS
wpos, cpos, lpos = [], [], []
linestarts = {}
lines = B.split('\n')
for a in ANOM:
    ci = FLAT.find(a)
    if ci < 0: continue
    cpos.append(ci)
    wpos.append(len(FLAT[:ci].split()))
    lpos.append(len(''.join(c for c in FLAT[:ci] if c.isalpha())))
for lst, nm in ((wpos, 'w'), (cpos, 'c'), (lpos, 'l')):
    for sep in ['', ' ', '-', ',']:
        add(sep.join(str(x) for x in lst))
        add(sep.join(str(x) for x in lst[::-1]))
    add(str(sum(lst)))
    # deltas between consecutive anomalies
    d = [lst[i+1]-lst[i] for i in range(len(lst)-1)]
    for sep in ['', ' ', '-', ',']:
        add(sep.join(str(x) for x in d))
    add(''.join(chr(64 + (x % 26 or 26)) for x in d))
    add(''.join(chr(64 + (x % 26 or 26)) for x in d).lower())
    add(''.join(chr(97 + (x % 26)) for x in lst))
# the article letter standing at each anomaly's word index
add(''.join(WORDS[i][0] for i in wpos if i < len(WORDS)))
add(''.join(WORDS[i][0] for i in wpos if i < len(WORDS)).lower())
add(' '.join(WORDS[i] for i in wpos if i < len(WORDS)))
# mod-26 of char positions -> letters
add(''.join(chr(97 + (p % 26)) for p in cpos))
add(''.join(chr(97 + (p % 26)) for p in lpos))

# ------------------------------------------------ 2. SELF-INDEXING
# take the Nth letter of the Nth anomaly
s = ''
for i, a in enumerate(ANOM, 1):
    t = ''.join(c for c in a if c.isalpha())
    s += t[(i - 1) % len(t)] if t else ''
addv(s)
s2 = ''.join(a[0] for a in ANOM)
addv(s2)
s3 = ''.join(''.join(c for c in a if c.isalpha())[-1] for a in ANOM)
addv(s3)
# length of each anomaly as a digit stream
ln = [len(''.join(c for c in a if c.isalnum())) for a in ANOM]
for sep in ['', ' ', '-', ',']:
    add(sep.join(str(x) for x in ln)); add(sep.join(str(x) for x in ln[::-1]))
add(''.join(chr(64 + x) for x in ln if 1 <= x <= 26))
add(''.join(chr(64 + x) for x in ln if 1 <= x <= 26).lower())

# ------------------------------------------------ 3. MIRROR-GLYPH TRANSFORMS
# Keiser's own clue was mirror writing.  A true mirror maps glyph shapes.
MIRROR = str.maketrans({
    'b': 'd', 'd': 'b', 'p': 'q', 'q': 'p', 'n': 'u', 'u': 'n',
    'B': 'a', 'E': '3', 'J': 'L', 'L': 'J', 'N': 'И', 'R': 'Я',
    'S': 'Z', 'Z': 'S', 'P': 'q', 'F': 'ꟻ', 'G': 'Ә', 'D': 'a',
    'C': 'Ɔ', 'K': 'ꓘ', 'e': 'ɘ', 'g': 'ǫ', 'j': 'ꞁ', 'r': 'ɿ',
    's': 'ꙅ', 'z': 'ƹ', 'a': 'ɒ', 'c': 'ɔ', 'f': 'ʇ', 'k': 'ʞ',
    't': 'ƚ', 'y': 'ʏ',
})
SYMM = set('AHIMOTUVWXYilovwx')
for a in ANOM + ['Overdose', 'OVERDOSE', 'Bitcoin', 'Max Keiser', 'El Salvador',
                 'mEthereum', '10years', 'Bitcoins coattails', 'shitcoinery']:
    add(a[::-1], a[::-1].lower(), a.translate(MIRROR),
        a.translate(MIRROR)[::-1], a.lower().translate(MIRROR),
        a.lower().translate(MIRROR)[::-1])
    # keep only mirror-symmetric glyphs
    k = ''.join(c for c in a if c in SYMM)
    add(k, k.lower(), k[::-1])
for phrase in ['BITCOIN IS TOXIC AF', 'MAX KEISER', 'OVERDOSE',
               'Go Bitcoin Toxic Maximalist', 'the whole Satoshi experience',
               "Don't fall for shitcoinery", 'Keep your dignity']:
    k = ''.join(c for c in phrase if c in SYMM or c == ' ')
    add(k.strip(), k.replace(' ', ''), k.replace(' ', '').lower(),
        phrase[::-1], phrase.translate(MIRROR), phrase.translate(MIRROR)[::-1])

# ------------------------------------------------ 4. SHORT DISPLAY LINES
short = [l.strip() for l in lines if 0 < len(l.strip()) <= 45]
add(' '.join(short), ''.join(short), ' '.join(short).lower())
add(''.join(l[0] for l in short if l), ''.join(l[0] for l in short if l).lower())
for k in (8, 12, 16, 24, 32):
    add(' '.join(short[:k]), ''.join(l[0] for l in short[:k] if l))
# lines that are a complete sentence on their own
solo = [l.strip() for l in lines if re.fullmatch(r"[^.!?]*[.!?]", l.strip() or 'x')]
add(' '.join(solo[:40]), ''.join(l[0] for l in solo if l))

# ------------------------------------------------ 5. LEET / KEYBOARD
LEET = str.maketrans({'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
                      't': '7', 'b': '8', 'g': '9', 'l': '1'})
for a in ['mEthereum', 'Overdose', 'shitcoinery', 'hyperbitcoinized',
          'Bitcoin is toxic af', 'Max Keiser', '10years', 'Bitcoins coattails',
          'toxic maximalist', 'orange pill']:
    add(a.lower().translate(LEET), a.upper().translate(LEET),
        a.lower().translate(LEET).upper())

# ------------------------------------------------ 6. ROT / ATBASH of anomalies
def atbash(s):
    return ''.join(chr(155 - ord(c)) if c.islower() else
                   chr(155 - 32 - ord(c)) if c.isupper() else c for c in s)
def rot(s, n):
    r = []
    for c in s:
        if c.islower(): r.append(chr((ord(c) - 97 + n) % 26 + 97))
        elif c.isupper(): r.append(chr((ord(c) - 65 + n) % 26 + 65))
        else: r.append(c)
    return ''.join(r)
for a in ['mEthereum', 'Overdose', 'OVERDOSE', '10years', 'shitcoinery',
          'Bitcoins coattails', 'BITCOIN IS TOXIC AF', 'MAX KEISER',
          'hyperbitcoinized', 'gargantuanly', 'Faketoshi', 'Full Stop']:
    add(atbash(a), atbash(a).lower())
    for n in (13, 20, 21, 24, 42, 51, 95, 3, 7):
        add(rot(a, n % 26), rot(a, n % 26).lower())

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
