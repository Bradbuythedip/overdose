#!/usr/bin/env python3
"""Wave 2 of the oddity lens: typographic normalisation, bracketed/quoted
extractions, the OVERDOSE drug lexicon, repetition markers, and the 10years
correction span."""
import re, itertools

B = '\n'.join(l for l in open('/home/user/overdose/solver/article_transcript.txt',
              encoding='utf-8').read().split('\n')
              if not l.startswith('#') and not l.startswith('==='))
FLAT = re.sub(r'\s+', ' ', B).strip()

out = []
def add(*xs):
    for x in xs:
        if x is None: continue
        x = x.strip()
        if x and len(x) < 4000:
            out.append(x)

def variants(s):
    v = {s, s.lower(), s.upper(), s.title()}
    w = re.split(r'[\s_\-.]+', s)
    w = [x for x in w if x]
    if w:
        v |= {''.join(w), ''.join(w).lower(), ''.join(w).upper(),
              ' '.join(w), ' '.join(w).lower(), '-'.join(w).lower(),
              '_'.join(w).lower(), ''.join(x.capitalize() for x in w),
              ' '.join(w[::-1]), ''.join(w[::-1]).lower()}
    v.add(s[::-1]); v.add(s.lower()[::-1])
    v.add(''.join(c for c in s if c.isalnum()))
    v.add(''.join(c for c in s if c.isalnum()).lower())
    return v
def addv(*xs):
    for x in xs:
        for y in variants(x): add(y)

# ---------------------------------------------------------------- 1. TYPOGRAPHY
# The magazine sets curly quotes and apostrophes; the transcript uses straight
# ones.  Any phrase typed FROM THE PAGE carries U+2019 / U+201C / U+201D.
def curl(s):
    s = s.replace("'", '’')
    # opening / closing doubles
    o = True; r = []
    for c in s:
        if c == '"':
            r.append('“' if o else '”'); o = not o
        else:
            r.append(c)
    return ''.join(r)

KEY = [
 "Here's the bitter truth.",
 "Bitcoin was not a reaction to the Global Financial Crisis of 2008. It caused it.",
 "toxicity is Layer 1 of the protocol",
 "It's only the language of the shameless opportunists trying to cash in by riding Bitcoins coattails that give it a bad name.",
 "Now he's slinging proof of stake at the mEthereum lab.",
 "Don't fall for shitcoinery.",
 "Keep your dignity.",
 "Go Bitcoin Toxic Maximalist, the Layer 1 of the whole Satoshi experience.",
 "It's the freaking UTXO ghetto up in here, y'all.",
 "Gotta be this way.",
 "It's a stun gun to the genitals.",
 "A monetary defibrillator to the treasure chest.",
 "Don't believe me?",
 "London is a scammer paradise. Full Stop.",
 "It's a guaranteed, mathematical certainty.",
 "bitcoin was designed to be a 51% attack on the world's energy supply",
 "(Elvis Costello was right)",
 "Everyone will live their own experience in the rabbit hole.",
 "We are getting our souls back and our minds.",
 "Stacy and I have been living in here for 10 years.",
 "We've seen some shit.",
 "the agony and ecstasy",
 "as Bitcoin conquers fear and hate and replaces it with peace and love",
 "MAX KEISER",
 "BITCOIN IS TOXIC AF",
 "Bitcoin's rabbit hole",
 "y'all", "Don't", "It's", "Here's", "Everybody's", "Bitcoin's", "world's",
 "nation's", "Yoko's", "Mallers'", "nocoiners'", "shitcoiners'", "U.K.'s",
 "We've", "you're", "wouldn't", "weren't", "hasn't", "That's", "He's",
]
for k in KEY:
    add(k, curl(k), curl(k).lower(), curl(k).upper())
    add(k.replace("'", ''), curl(k).replace(' ', ''))
# every apostrophe word with curly form
for m in set(re.findall(r"[A-Za-z]+'[A-Za-z]*", B)):
    add(m, curl(m), curl(m).lower(), m.replace("'", ''), m.replace("'", '')+'')
# em dash vs hyphen vs double-hyphen in the dash sentences
for s in ["the Bitcoin rabbit hole was opening — the black hole of the Cosmic Now — and it had fiat markets in its sight",
          "these eggheads — Michael Saylor, Nic Carter, Marty Bent — who spend their days pouring over spreadsheets",
          "the efficiencies of love — because bitcoin is infinitely more efficient to transact and store wealth in than fiat, shitcoins or gold — the overall energy consumption",
          "— the agony and ecstasy —"]:
    add(s, s.replace('—', '-'), s.replace('—', '--'), s.replace(' — ', '—'),
        s.replace(' — ', '-'), s.replace('—', '–'))

# ---------------------------------------------------------------- 2. BRACKETED
PARENS = ['and 10years of watching Peter Schiff miss buying bitcoin since I started honey-badgering him to buy some at $1 back in 2011',
          'IMF', 'at the time of writing',
          'Sorry Bhutan, you fell for that snake oil salesmen over at XRP.',
          'and Peter McCormack', 'Elvis Costello was right']
for p in PARENS: addv(p)
for sep in ['', ' ', ' | ', '-', ',', '. ']:
    add(sep.join(PARENS)); add(sep.join(PARENS[::-1]))
addv(''.join(p[0] for p in PARENS))                      # aIaSaE
addv(''.join(p.split()[0] for p in PARENS))
addv(' '.join(p.split()[0] for p in PARENS))
addv(' '.join(p.split()[-1].strip('.,') for p in PARENS))
addv(''.join(p.split()[-1].strip('.,') for p in PARENS))

QUOTED = ['Toxic Bitcoin Maximalists', 'Maximalist', 'Friends', 'buying the dip.', 'Volcano Bonds']
for q in QUOTED: addv(q)
for sep in ['', ' ', ' | ', '-', ',']:
    add(sep.join(QUOTED)); add(sep.join(QUOTED[::-1]))
addv(''.join(q[0] for q in QUOTED))                      # TMFbV
addv(''.join(w[0] for q in QUOTED for w in q.split()))

# ---------------------------------------------------------------- 3. CAPS STREAM
toks = [(m.start(), m.group(0)) for m in re.finditer(r"[A-Za-z][A-Za-z'’]*", B)]
def si(pos):
    i = pos - 1
    while i >= 0 and B[i] in ' \n\t"“‘(': i -= 1
    return i < 0 or B[i] in '.!?:;'
caps = [w for p, w in toks if w[0].isupper() and not si(p)
        and not (len([c for c in w if c.isalpha()]) > 1 and w.isupper())]
acr = ''.join(w[0] for w in caps)
add(' '.join(caps), ''.join(caps), ' '.join(caps).lower(), acr, acr.lower(), acr[::-1])
for k in (12, 16, 20, 24, 32, 48, 64):
    add(acr[:k], acr[:k].lower(), acr[-k:], acr[-k:].lower())
    add(' '.join(caps[:k]), ' '.join(caps[-k:]))
# unique caps, order preserved
seenw, uc = set(), []
for w in caps:
    if w.lower() not in seenw:
        seenw.add(w.lower()); uc.append(w)
add(' '.join(uc), ''.join(uc), ''.join(w[0] for w in uc), ''.join(w[0] for w in uc).lower())

# ---------------------------------------------------------------- 4. OVERDOSE LEXICON
DRUG = ['OVERDOSE', 'toxic', 'toxicity', 'meth', 'mEthereum', 'dulled',
        'euthanized', 'catnip', 'rancid catnip', 'lobotomy', 'stun gun',
        'genitals', 'defibrillator', 'demented', 'poppy-harvesting', 'poppy',
        'espresso', 'gallons', 'muck', 'toys', 'high', 'hell', 'burning stake']
for d in DRUG: addv(d)
for sep in ['', ' ', '-', ',']:
    add(sep.join(DRUG)); add(sep.join(d.lower() for d in DRUG))
    add(sep.join(DRUG[::-1]))
addv(''.join(d[0] for d in DRUG))
CORE = ['overdose', 'meth', 'poppy', 'catnip', 'lobotomy', 'euthanized', 'toxic',
        'defibrillator', 'stun gun']
for r in range(2, 5):
    for c in itertools.permutations(CORE[:5], r):
        add(' '.join(c), ''.join(c))
addv('an overdose of Bitcoin', 'overdose of twenty', 'twenty bitcoin overdose',
     'OD', 'OD 20', 'overdose 20 BTC', 'toxic overdose', 'meth overdose',
     'overdose meth poppy catnip', 'Bitcoin overdose')

# ---------------------------------------------------------------- 5. REPETITION
REP = {'rabbit hole': 4, 'Layer 1': 3, 'infinitely more efficient': 3,
       'the first time': 3, 'peace and love': 2, 'love and peace': 1,
       'toxic': 4, 'shitcoin': 9, '51%': 2, 'Toxic Bitcoin Maximalists': 2,
       'El Salvador': 2, '10 years': 2, 'Wall Street': 2}
for k, v in REP.items():
    addv(k); add(f'{k} x{v}', f'{k}{v}', f'{v}{k}', (k + ' ') * v, k * v)
add(' '.join(f'{k}{v}' for k, v in REP.items()))
add(''.join(str(v) for v in REP.values()))
DUPSENT = 'The economy of love is infinitely more efficient than hate and war.'
add(DUPSENT, DUPSENT * 2, DUPSENT + ' ' + DUPSENT, curl(DUPSENT),
    (DUPSENT + '\n') * 2, DUPSENT.lower(), DUPSENT.replace(' ', ''),
    DUPSENT.lower().replace(' ', ''))

# ---------------------------------------------------------------- 6. 10years SPAN
# every window that CROSSES the corrected no-space token, printed form
i = FLAT.find('10years')
if i > 0:
    for a in range(1, 26):
        for b in range(1, 26):
            L = FLAT.rfind(' ', 0, i)
            # word-window around it
            pre = FLAT[:i].split()
            post = FLAT[i + 7:].split()
            w = pre[-a:] + ['10years' + (post[0] if post else '')] if False else None
    words = FLAT.split()
    idx = next(k for k, w in enumerate(words) if '10years' in w)
    for a in range(0, 13):
        for b in range(0, 13):
            seg = ' '.join(words[max(0, idx - a): idx + b + 1])
            if 3 < len(seg) < 400:
                add(seg); add(seg.lower())
addv('10years', '10yearsof', '10years of watching Peter Schiff',
     'and 10years of watching Peter Schiff miss buying bitcoin',
     '10years10years', '10years 10 years', '10 years 10years')

# ---------------------------------------------------------------- 7. ANOMALY ACROSTIC
ANOM = ['AF', 'cypherpunks', 'banking terrorists', 'Cosmic Now', 'Nocoiners',
        'shitcoiners', 'Bitcoiners', 'Bitcoins', 'mEthereum', 'shitcoinery',
        'Satoshi', 'UTXO', "y'all", '10years', 'honey-badgering',
        'psychotic cats', 'rancid catnip', 'paper chase Manhattan Bank',
        'defibrillator', 'Volcano Bonds', 'hyperbitcoinized', 'mind-bending',
        'salesmen', 'Faketoshi', 'banksters', 'Full Stop', 'eggheads',
        'pouring', 'gargantuanly', 'uber', 'cuck-bucks', 'oil-dripping',
        'corpse-ridden', 'poppy-harvesting', 'game-theorized', 'cyber sea',
        'bed-in']
for sep in ['', ' ', '-', ',', '_']:
    add(sep.join(ANOM)); add(sep.join(a.lower() for a in ANOM))
    add(sep.join(ANOM[::-1]))
addv(''.join(a[0] for a in ANOM))
addv(''.join(a[0] for a in ANOM).lower())
addv(''.join(a[-1] for a in ANOM))
add(' '.join(ANOM))

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
