#!/usr/bin/env python3
"""Curated tier-1 for the full HD stack + two extra bit packings."""
import sys, re, base64, itertools
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from bits import CHANNELS
out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = x.strip()
        if x and len(x) < 4000: out.append(x)
def addv(*xs):
    for s in xs:
        if not s: continue
        w = [x for x in re.split(r'[\s_\-]+', s) if x]
        add(s, s.lower(), s.upper(), ''.join(w), ''.join(w).lower(),
            ''.join(w).upper(), s[::-1], s.lower()[::-1],
            ''.join(x.capitalize() for x in w))

# ---- extra packings: run-length + base64 + base32 of every channel ----------
for name, bits in CHANNELS.items():
    rle, cur, n = [], bits[0] if bits else '0', 0
    for b in bits:
        if b == cur: n += 1
        else: rle.append(n); cur = b; n = 1
    rle.append(n)
    for sep in ['', ' ', '-', ',']:
        add(sep.join(str(x) for x in rle))
        add(sep.join(str(x) for x in rle[::-1]))
    add(''.join(chr(64 + x) for x in rle if 1 <= x <= 26))
    add(''.join(chr(64 + x) for x in rle if 1 <= x <= 26).lower())
    nb = (len(bits) + 7) // 8
    try:
        bb = int(bits, 2).to_bytes(nb, 'big')
        add(base64.b64encode(bb).decode(), base64.b32encode(bb).decode(),
            base64.b64encode(bb[::-1]).decode(), bb.hex())
    except Exception:
        pass
    # 6-bit base64 alphabet directly off the bit stream
    A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    add(''.join(A[int(bits[i:i+6], 2)] for i in range(0, len(bits) - 5, 6)))
    # 5-bit base32 alphabet
    A32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    add(''.join(A32[int(bits[i:i+5], 2)] for i in range(0, len(bits) - 4, 5)))

# ---- the curated oddity tier-1 ---------------------------------------------
T1 = [
 # the flagged misspellings / coinages
 'mEthereum', 'meth Ethereum', 'the mEthereum lab', 'proof of stake at the mEthereum lab',
 '10years', '10years of watching Peter Schiff', 'Bitcoins coattails',
 'riding Bitcoins coattails', 'shitcoinery', 'Don\'t fall for shitcoinery',
 'hyperbitcoinized', '42% of the country is now hyperbitcoinized',
 'gargantuanly', 'gargantuanly wasteful', 'pouring over spreadsheets',
 'snake oil salesmen', 'banksters', 'cuck-bucks', 'fiat cuck-bucks',
 'Faketoshi', 'honey-badgering', 'UTXO ghetto', 'Full Stop',
 'London is a scammer paradise. Full Stop.', '$85 BILLION', '85 BILLION',
 # two tens make twenty
 '10years 10 years', '10years10years', '1010', '20 years', 'twenty years',
 # the title
 'Overdose', 'OVERDOSE', 'Overdose 20 BTC', 'OVERDOSE20', 'overdose20btc',
 'an overdose of 20', 'Overdose Max Keiser', 'Max Keiser Overdose',
 'OVERDOSE Bitcoin Magazine El Salvador', 'Overdose 2021',
 # metadata
 'Bitcoin Magazine issue 24', 'issue 24', 'El Salvador issue', 'Fall 2021',
 '73 79', '73-79', '7379', '75-79', '2021', '24', '20 BTC', '20BTC',
 # Keiser outside knowledge
 'ORANGEPILL', 'orangepill', 'ORANGEPILL21', 'orangepill21', 'MaxCoin',
 'Keiser Report', 'Stacy Herbert', 'maxkeiser', 'El Salvador is a clue',
 'George Sand', 'Mr President',
 # numbers
 '42 51 95', '425195', '95 51 42', '42%51%95%', '20 42 51 95',
 '10 3 10 3 8 5', '1031038 5', '10310385',
 # factual corrections
 'Wittenberg', '95 theses', 'Martin Luther 95 theses 1517', 'Nick Lowe',
 'Hilton Amsterdam room 902', 'room 902', 'Chase Manhattan Bank',
 # bracketed / quoted extractions
 'Toxic Bitcoin Maximalists Maximalist Friends buying the dip. Volcano Bonds',
 'TMFbV', 'aIaSaE',
 # the drug lexicon
 'overdose meth poppy catnip lobotomy', 'toxic overdose',
 'meth poppy catnip euthanized lobotomy defibrillator',
 # duplicated sentence
 'The economy of love is infinitely more efficient than hate and war.',
 'The economy of love is infinitely more efficient than hate and war. '
 'The economy of love is infinitely more efficient than hate and war.',
 # self reference
 'toxicity is Layer 1 of the protocol', 'Layer 1', 'Genesis Block',
 'right there in the Genesis Block', 'BITCOIN IS TOXIC AF', 'MAX KEISER',
 'BITCOIN IS TOXIC AF MAX KEISER',
 'Go Bitcoin Toxic Maximalist, the Layer 1 of the whole Satoshi experience.',
 # El Salvador
 'El Salvador', 'Nayib Bukele', 'Volcano Bonds', 'Chivo', 'Bitcoin City',
 'Conchagua', 'CL76841714A',
]
for t in T1: addv(t)
# curly-apostrophe forms of the tier-1 strings that contain one
for t in T1:
    if "'" in t:
        c = t.replace("'", '’')
        add(c, c.lower(), c.upper())

# the anomaly acrostic, the caps acrostic, the parenthetical concat
ANOM = ['AF','cypherpunks','banking terrorists','Cosmic Now','Nocoiners','shitcoiners',
        'Bitcoiners','Bitcoins','mEthereum','shitcoinery','Satoshi','UTXO',"y'all",
        '10years','honey-badgering','psychotic cats','rancid catnip',
        'paper chase Manhattan Bank','defibrillator','Volcano Bonds',
        'hyperbitcoinized','mind-bending','salesmen','Faketoshi','banksters',
        'Full Stop','eggheads','pouring','gargantuanly','uber','cuck-bucks',
        'oil-dripping','corpse-ridden','poppy-harvesting','game-theorized',
        'cyber sea','bed-in']
addv(''.join(a[0] for a in ANOM))
add(' '.join(ANOM), ''.join(a.replace(' ', '') for a in ANOM),
    ''.join(a.replace(' ', '') for a in ANOM).lower())
addv('HGFCBWSJDBCNBBTBMLLBBMBTMLSBBGCJBMLVPSIFMBESIMFTPNBVBMNWSESMSTBMBRVBSWFLPMURSBECMSNCMBPABGBBBBBJYAIB')

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
