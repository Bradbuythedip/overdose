#!/usr/bin/env python3
"""Wave 9: aggressive combinatorial expansion over the strongest flags."""
import itertools
TOK = ['mEthereum', 'meth', '10years', 'Bitcoins', 'shitcoinery',
       'hyperbitcoinized', 'gargantuanly', 'pouring', 'salesmen', 'BILLION',
       'FullStop', 'Overdose', 'OVERDOSE', 'MaxKeiser', 'ElSalvador',
       'ORANGEPILL', 'BitcoinMagazine', '20BTC', '20', '24', '2021', '73',
       '79', '42', '51', '95', 'fivepills', 'ToxicAF', 'Layer1', 'Satoshi',
       'VolcanoBonds', 'Bukele', 'rabbithole', 'CL76841714A']
SEP = ['', ' ', '-', '_', '.', '/', '+', ':']
out = []
def add(s):
    if 2 < len(s) < 4000: out.append(s)

for a, b in itertools.permutations(TOK, 2):
    for s in SEP:
        t = a + s + b
        add(t); add(t.lower()); add(t.upper())

CORE = ['Overdose', 'OVERDOSE', 'mEthereum', '10years', 'ORANGEPILL',
        'MaxKeiser', 'ElSalvador', '20BTC', 'Layer1', 'ToxicAF']
for a, b, c in itertools.permutations(CORE, 3):
    for s in ('', ' ', '-'):
        t = a + s + b + s + c
        add(t); add(t.lower())

# affixes on the single strongest flags
AFF = ['', '20', '21', '24', '73', '79', '95', '51', '42', '2021', '1', '0',
       '!', '?', '.', 'BTC', 'btc', 'key', 'KEY', 'private', 'seed']
for t in ['mEthereum', '10years', 'Overdose', 'OVERDOSE', 'ORANGEPILL',
          'shitcoinery', 'Bitcoins', 'BILLION', 'fivepills', 'Layer1']:
    for a in AFF:
        for b in AFF:
            add(a + t + b); add((a + t + b).lower()); add((a + t + b).upper())

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
