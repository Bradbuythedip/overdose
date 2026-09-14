#!/usr/bin/env python3
"""Wave 3: outside-knowledge keys a text-only sweep cannot reach, the
two-tens-make-twenty reading, the transcript's own OCR debris, and
anomaly-neighbour null ciphers."""
import re, itertools
B = '\n'.join(l for l in open('/home/user/overdose/solver/article_transcript.txt',
              encoding='utf-8').read().split('\n')
              if not l.startswith('#') and not l.startswith('==='))
FLAT = re.sub(r'\s+', ' ', B).strip()
out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = x.strip()
        if x and len(x) < 4000: out.append(x)
def variants(s):
    v = {s, s.lower(), s.upper(), s.title()}
    w = [x for x in re.split(r'[\s_\-.]+', s) if x]
    if w:
        v |= {''.join(w), ''.join(w).lower(), ''.join(w).upper(), ' '.join(w),
              ' '.join(w).lower(), '-'.join(w).lower(), '_'.join(w).lower(),
              ''.join(x.capitalize() for x in w),
              w[0].lower() + ''.join(x.capitalize() for x in w[1:]),
              ' '.join(w[::-1]), ''.join(w[::-1]).lower()}
    v.add(s[::-1]); v.add(s.lower()[::-1])
    v.add(''.join(c for c in s if c.isalnum()))
    v.add(''.join(c for c in s if c.isalnum()).lower())
    return v
def addv(*xs):
    for x in xs:
        for y in variants(x): add(y)

# ---- 1. KEISER'S OWN PROMO CODE AND CATCHPHRASES (outside the article) ------
addv('ORANGEPILL', 'orange pill', 'ORANGEPILL21', 'orangepill 21', 'orange pilled',
     'ORANGE PILL 21', 'promo code ORANGEPILL', '21% off', '21 off', '21',
     'ORANGEPILL20', 'ORANGEPILL 20 BTC', 'ORANGEPILLOVERDOSE')
for a in ['ORANGEPILL', 'orangepill', 'OrangePill']:
    for b in ['', '21', '20', '2021', 'OVERDOSE', 'overdose', 'MaxKeiser',
              'ElSalvador', '20BTC', 'BitcoinMagazine', '24', '73', '79']:
        add(a + b, a + ' ' + b, b + a, a + '-' + b)
KCATCH = ['Buy bitcoin', 'Death to the dollar', 'Genocide by central bank',
          'Stack sats', 'Keiser Report', 'MaxCoin', 'StartCOIN', 'Bitcoin Capital',
          'maxkeiser', 'stacyherbert', 'Stacy Herbert', 'Max and Stacy',
          'Hey hey ho ho fiat money has got to go', 'We are all Satoshi',
          'Bitcoin is a virus', 'El Salvador is a clue', 'George Sand',
          'hidden cryptography', 'Mr President', 'Nobody has figured it out yet',
          'I hid a private Bitcoin key encoded in this piece',
          'for 20 BTC', 'Bitcoin Is Toxic AF Overdose']
for k in KCATCH: addv(k)

# ---- 2. EL SALVADOR OUTSIDE FACTS ------------------------------------------
ES = ['Chivo', 'Chivo wallet', 'Bitcoin City', 'Conchagua', 'Volcano Bond',
      'Volcano Bonds', 'EBB1', 'Bitcoin Law', 'Ley Bitcoin', 'legal tender',
      'September 7 2021', '2021-09-07', '070921', '20210907', '200 BTC',
      'Nayib Bukele', 'Bukele', 'Samson Mow', 'Blockstream', 'Strike',
      'Jack Mallers', '$30 bonus', 'El Salvador 2021', 'La Libertad',
      'El Zonte', 'Bitcoin Beach', 'CL76841714A']
for e in ES: addv(e)
for a in ['ElSalvador', 'El Salvador', 'elsalvador']:
    for b in ['20', '20BTC', '2021', 'Overdose', 'OVERDOSE', 'Bukele', 'Keiser',
              'Chivo', '24', 'VolcanoBonds', '42']:
        add(a + b, a + ' ' + b, b + a, a + '-' + b)

# ---- 3. TWO TENS MAKE TWENTY -----------------------------------------------
# the ONLY number repeated in the piece is 10 (once as the printed "10years",
# once as "10 years"); the prize is 20.
addv('10years10 years', '10years 10 years', '10 years 10years', '1010',
     '10+10', '10 10', '10-10', 'twentyyears', 'twenty years', '20years',
     '20 years', 'ten years ten years', 'ten ten twenty',
     '10years and 10 years', '10years10years', 'tenyears', 'ten years')
for a in ['10years', '10 years', '1010', '20']:
    for b in ['20 BTC', '20BTC', 'Overdose', 'OVERDOSE', 'Keiser', 'Stacy',
              'Peter Schiff', 'rabbit hole', 'living in here']:
        add(a + b, a + ' ' + b, b + a, b + ' ' + a)
addv('Stacy and I have been living in here for 10years',
     'we have been living in here for 10years',
     'and 10years of watching Peter Schiff and 10 years living in here')

# ---- 4. SATOSHI / AMOUNT ARITHMETIC ----------------------------------------
for s in ['2000000000', '20.00000000', '20.0 BTC', '2000000000 sats',
          '20 BTC 2000000000', '0.00000020', '2100000000000000',
          '20000000000', '2e9']:
    addv(s)

# ---- 5. THE TRANSCRIBER'S OCR DEBRIS (odd strings printed in the file) -----
addv('GEEECEEY', 'PRBSSRERS', 'GEEECEEY PRBSSRERS', 'IMG_6246',
     'IMG_6244', 'IMG_6250', 'CCITT-G4', 'band 5', 'p76_mask')
IMGS = ['6244', '6245', '6246', '6247', '6248', '6249', '6250']
for sep in ['', ' ', '-', ',']:
    add(sep.join(IMGS)); add(sep.join(IMGS[::-1]))
add('IMG_' + '_IMG_'.join(IMGS))

# ---- 6. ANOMALY NEIGHBOURS (null cipher: word before / word after each) -----
words = FLAT.split()
ANOMTOK = ['mEthereum', '10years', 'Bitcoins', 'shitcoinery', 'hyperbitcoinized',
           'banksters', 'cuck-bucks', 'Faketoshi', 'honey-badgering',
           'gargantuanly', 'salesmen', 'pouring', "y'all", 'UTXO', 'Gotta',
           'AF', 'Stop.', 'bed-in', 'game-theorized', 'mind-bending',
           'nocoiners', 'Nocoiners', 'cypherpunks']
prevs, nexts, both = [], [], []
for i, w in enumerate(words):
    cw = w.strip('.,?!";:()')
    if cw in ANOMTOK or w in ANOMTOK:
        if i: prevs.append(words[i-1].strip('.,?!";:()'))
        if i + 1 < len(words): nexts.append(words[i+1].strip('.,?!";:()'))
        both.append(w)
for lst, nm in ((prevs, 'prev'), (nexts, 'next'), (both, 'tok')):
    if not lst: continue
    add(' '.join(lst), ''.join(lst), ' '.join(lst).lower(),
        ''.join(lst).lower(), ''.join(x[0] for x in lst),
        ''.join(x[0] for x in lst).lower(), ' '.join(lst[::-1]))
add(' '.join(a + ' ' + b for a, b in zip(prevs, nexts)))

# ---- 7. THE ONLY MID-WORD CAPITAL: where mEthereum sits ---------------------
idx_w = next((i for i, w in enumerate(words) if 'mEthereum' in w), None)
idx_c = FLAT.find('mEthereum')
letters = [c for c in FLAT if c.isalpha()]
idx_l = ''.join(letters).find('mEthereum')
for v in (idx_w, idx_c, idx_l):
    if v is not None and v >= 0:
        add(str(v), f'mEthereum{v}', f'{v}mEthereum', f'Overdose{v}')
add(f'{idx_w} {idx_c} {idx_l}', f'{idx_w}-{idx_c}-{idx_l}',
    f'{idx_w}{idx_c}{idx_l}')

# ---- 8. DOLLAR FIGURES IN ORDER --------------------------------------------
DOL = ['1', '1000000000', '85000000000', '2000000000000']
DOLP = ['$1', '$1 billion', '$85 BILLION', '$2 trillion']
for sep in ['', ' ', '-', ',']:
    add(sep.join(DOL)); add(sep.join(DOL[::-1])); add(sep.join(DOLP))
add('1 1 85 2', '1-1-85-2', '11852', '1 billion 85 billion 2 trillion')

# ---- 9. PERCENT/NUMBER TRIPLE CROSSED WITH THE PRIZE -----------------------
for combo in itertools.permutations(['20', '42', '51', '95']):
    add(''.join(combo), '-'.join(combo), ' '.join(combo), '.'.join(combo))
for combo in itertools.permutations(['20', '21', '24', '42', '51', '95'], 3):
    add(''.join(combo))
add('42515120', '20425195', '4251952021', '42%51%95%20BTC')

# ---- 10. "FULL STOP" AS A SELF-REFERENCE: punctuation census ---------------
cnt = {c: FLAT.count(c) for c in '.,?!;:—"\'()%$-'}
add(''.join(str(v) for v in cnt.values()))
add(' '.join(f'{k}{v}' for k, v in cnt.items()))
for k, v in cnt.items():
    add(f'{k}{v}')
add(str(cnt['.']), f"Full Stop {cnt['.']}", f"{cnt['.']} full stops")

# ---- 11. STRUCTURE: the five body pages ------------------------------------
pages = re.split(r'=== PAGE', open('/home/user/overdose/solver/article_transcript.txt',
                                   encoding='utf-8').read())[1:]
pw = []
for p in pages:
    t = p.split('===', 1)[-1]
    pw.append(len(re.findall(r"[A-Za-z][A-Za-z'’-]*", t)))
for sep in ['', ' ', '-', ',']:
    add(sep.join(str(x) for x in pw)); add(sep.join(str(x) for x in pw[::-1]))
add(' '.join(f'p{75+i}={n}' for i, n in enumerate(pw)))

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
