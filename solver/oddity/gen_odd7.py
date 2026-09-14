#!/usr/bin/env python3
"""Wave 7: cross the case-bit null cipher with the article's BIP-39 vocabulary.
The article's 281 BIP-39 words were swept as a run; they have never been
SELECTED by the Bitcoin/bitcoin capitalisation mask."""
import re, sys, hashlib
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from bits import CHANNELS
from mnemonic import Mnemonic
M = Mnemonic('english')
WL = M.wordlist
WS = set(WL)

RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
B = '\n'.join(l for l in RAW.split('\n') if not l.startswith('#') and not l.startswith('==='))
FLAT = re.sub(r'\s+', ' ', B).strip()
WORDS = [w.strip('.,?!";:()—$%\'’').lower() for w in FLAT.split()]
BW = [w for w in WORDS if w in WS]
print(f'{len(BW)} BIP39 words in the piece', file=sys.stderr)

out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = x.strip()
        if x and len(x) < 4000: out.append(x)

def emit_mn(ws):
    """emit a word run, plus checksum-fixed variants (brute the last word)."""
    for k in (12, 15, 18, 24):
        if len(ws) >= k:
            run = ws[:k]
            add(' '.join(run))
            if M.check(' '.join(run)):
                add('VALID ' + ' '.join(run))
            # brute the final word to make it checksum-valid
            for cand in WL:
                trial = run[:-1] + [cand]
                if M.check(' '.join(trial)):
                    add(' '.join(trial))
            run2 = ws[-k:]
            add(' '.join(run2))
            for cand in WL:
                trial = run2[:-1] + [cand]
                if M.check(' '.join(trial)):
                    add(' '.join(trial))
    if 0 < len(ws) < 12:
        add(' '.join(ws))

# ---- 1. mask the article's BIP-39 words with each capitalisation channel ----
for cname, bits in CHANNELS.items():
    for pol in ('1', '0'):
        sel = [BW[i] for i, b in enumerate(bits) if i < len(BW) and b == pol]
        if len(sel) >= 4:
            emit_mn(sel)
            add(' '.join(sel), ''.join(sel))

# ---- 2. mask the FULL word stream, keep only resulting BIP-39 words ---------
for cname, bits in CHANNELS.items():
    for pol in ('1', '0'):
        sel = [WORDS[i] for i, b in enumerate(bits) if i < len(WORDS) and b == pol]
        sb = [w for w in sel if w in WS]
        if len(sb) >= 4:
            emit_mn(sb)

# ---- 3. BIP-39 words adjacent to each anomaly ------------------------------
ANOM = ['methereum', '10years', 'bitcoins', 'shitcoinery', 'hyperbitcoinized',
        'banksters', 'cuck-bucks', 'faketoshi', 'honey-badgering',
        'gargantuanly', 'salesmen', 'pouring', "y'all", 'utxo', 'gotta',
        'af', 'billion', 'bed-in', 'cypherpunks', 'nocoiners']
near = []
raw_words = [w.strip('.,?!";:()—$%').lower() for w in FLAT.split()]
for i, w in enumerate(raw_words):
    if w in ANOM or any(a in w for a in ('methereum', '10years')):
        for j in range(max(0, i - 4), min(len(raw_words), i + 5)):
            if raw_words[j] in WS:
                near.append(raw_words[j])
if near:
    emit_mn(near); add(' '.join(near), ''.join(near))

# ---- 4. BIP-39 words at anomaly word-indices -------------------------------
idxs = [i for i, w in enumerate(raw_words) if w in ANOM]
sel = [BW[i % len(BW)] for i in idxs] if BW else []
if len(sel) >= 4:
    emit_mn(sel); add(' '.join(sel))

# ---- 5. first BIP-39 word of each line / each sentence ---------------------
lines = [l.strip() for l in B.split('\n') if l.strip()]
firstbw = []
for l in lines:
    for w in [x.strip('.,?!";:()—$%').lower() for x in l.split()]:
        if w in WS:
            firstbw.append(w); break
emit_mn(firstbw); add(' '.join(firstbw))
lastbw = []
for l in lines:
    got = None
    for w in [x.strip('.,?!";:()—$%').lower() for x in l.split()]:
        if w in WS: got = w
    if got: lastbw.append(got)
emit_mn(lastbw); add(' '.join(lastbw))

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
