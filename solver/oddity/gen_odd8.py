#!/usr/bin/env python3
"""Wave 8: the five pills on the OVERDOSE masthead (p73) as geometry, the
masthead byline, and a master string of every oddity found."""
import json, itertools, math
P = json.load(open('/home/user/overdose/solver/oddity/pills.json'))
out = []
def add(*xs):
    for x in xs:
        if x is None: continue
        x = str(x).strip()
        if 2 < len(x) < 4000: out.append(x)
def addv(*xs):
    for s in xs:
        if not s: continue
        s = str(s)
        add(s, s.lower(), s.upper(), s[::-1], s.lower()[::-1],
            s.replace(' ', ''), s.replace(' ', '').lower(),
            s.replace(' ', '').upper())

COMP = 'E NE N NW W SW S SE'.split()
ang = [p['ang'] for p in P]
ang180 = [a % 180 for a in ang]
clock = [int(round(((90 - a) % 360) / 30)) or 12 for a in ang]
clock2 = [((c + 5) % 12) + 1 for c in clock]
comp = [COMP[int(((a + 22.5) % 360) // 45)] for a in ang]
comp2 = [COMP[int(((a + 180 + 22.5) % 360) // 45)] for a in ang]

addv('5 pills', 'five pills', 'FIVE PILLS', 'OVERDOSE 5 pills',
     'five pills overdose', '5', 'five', '20 BTC 5 pills',
     'OVERDOSE with Max Keiser', 'with Max Keiser', 'OVERDOSE Max Keiser 73',
     'Bitcoin Magazine El Salvador OVERDOSE')

for name, seq in (('ang', [round(a) for a in ang]),
                  ('ang180', [round(a) for a in ang180]),
                  ('clock', clock), ('clock2', clock2)):
    for sep in ['', ' ', '-', ',', '.']:
        add(sep.join(str(x) for x in seq))
        add(sep.join(str(x) for x in seq[::-1]))
    add(str(sum(seq)))
    add(''.join(chr(64 + (x % 26 or 26)) for x in seq))
    add(''.join(chr(64 + (x % 26 or 26)) for x in seq).lower())
    add(''.join(chr(96 + (x % 26 or 26)) for x in seq))
for seq in (comp, comp2):
    for sep in ['', ' ', '-']:
        add(sep.join(seq)); add(sep.join(seq[::-1]))
    add(''.join(s[0] for s in seq), ''.join(s[0] for s in seq).lower())
    add(''.join(s[-1] for s in seq))

# positions, reading order, normalised to a 0-9 grid and to letters
xs = [p['cx'] for p in P]; ys = [p['cy'] for p in P]
mnx, mxx, mny, mxy = min(xs), max(xs), min(ys), max(ys)
g = [(int(round(9 * (p['cx'] - mnx) / (mxx - mnx))),
      int(round(9 * (p['cy'] - mny) / (mxy - mny)))) for p in P]
for sep in ['', ' ', ',', '-']:
    add(sep.join(f'{a}{b}' for a, b in g))
    add(sep.join(str(a) for a, b in g) + sep + sep.join(str(b) for a, b in g))
add(''.join(chr(65 + a) for a, b in g) + ''.join(chr(65 + b) for a, b in g))
add(''.join(str(round(p['cx'])) for p in P))
add(''.join(str(round(p['cy'])) for p in P))
add(' '.join(f'{round(p["cx"])},{round(p["cy"])}' for p in P))
# pairwise distances, rounded
d = []
for i in range(len(P)):
    for j in range(i + 1, len(P)):
        d.append(round(math.hypot(P[i]['cx'] - P[j]['cx'], P[i]['cy'] - P[j]['cy'])))
for sep in ['', ' ', '-', ',']:
    add(sep.join(str(x) for x in d))
add(str(sum(d)))
# blob sizes (relative pill areas)
sz = [p['size'] for p in P]
for sep in ['', ' ', '-', ',']:
    add(sep.join(str(x) for x in sz))
add(str(sum(sz)))
order = [i + 1 for i, _ in sorted(enumerate(sz), key=lambda t: -t[1])]
add(''.join(str(x) for x in order), ' '.join(str(x) for x in order))

# the banknote on the masthead, crossed with the pills and the title
for a in ['CL76841714A', 'CL 76841714 A', 'L12', '76841714']:
    for b in ['OVERDOSE', '5 pills', '20 BTC', 'Max Keiser', '73', 'overdose']:
        add(a + b, a + ' ' + b, b + a, b + ' ' + a, (a + b).lower(),
            (a + b).upper())
addv('L12', 'CL76841714A L12', 'L12 CL76841714A', 'L 12', 'San Francisco 12')

# ---- master string of every oddity in this lens -----------------------------
MASTER = ['mEthereum', '10years', 'Bitcoins', 'shitcoinery', 'hyperbitcoinized',
          'gargantuanly', 'salesmen', 'pouring', 'BILLION', 'Full Stop',
          'Vatican', 'Elvis Costello', 'Sorry Bhutan', 'five pills', 'OVERDOSE']
for sep in ['', ' ', '-', ',', '_', '|']:
    add(sep.join(MASTER)); add(sep.join(m.lower() for m in MASTER))
    add(sep.join(MASTER[::-1]))
addv(''.join(m[0] for m in MASTER))

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
