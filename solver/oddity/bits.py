#!/usr/bin/env python3
"""Case/typography bit-channels over the printed article -> key material."""
import re, sys, hashlib, json

ART = '/home/user/overdose/solver/article_transcript.txt'

def body():
    out = []
    for ln in open(ART, encoding='utf-8').read().split('\n'):
        if ln.startswith('#') or ln.startswith('==='):
            continue
        out.append(ln)
    return '\n'.join(out).strip('\n')

B = body()

# ---- token stream with positions, in printed order -------------------------
TOK = re.compile(r"[A-Za-z][A-Za-z'’]*")
toks = [(m.start(), m.group(0)) for m in TOK.finditer(B)]

def is_allcaps(w):
    letters = [c for c in w if c.isalpha()]
    return len(letters) > 1 and all(c.isupper() for c in letters)

def sentence_initial(pos):
    """crude: preceded (ignoring space/newline/quote) by . ! ? : or start."""
    i = pos - 1
    while i >= 0 and B[i] in ' \n\t"“‘(':
        i -= 1
    if i < 0:
        return True
    return B[i] in '.!?:;—'

# which lowercase-forms appear with more than one casing anywhere?
from collections import defaultdict
forms = defaultdict(set)
for _, w in toks:
    forms[w.lower()].add(w)

CHANNELS = {}

# A1: bitcoin family (Bitcoin/bitcoin/Bitcoins/Bitcoiners/Bitcoin's...), skip ALLCAPS
fam = [(p, w) for p, w in toks if w.lower().startswith('bitcoin') and not is_allcaps(w)]
CHANNELS['A1_bcfam'] = ''.join('1' if w[0] == 'B' else '0' for _, w in fam)

# A2: strict Bitcoin / bitcoin only
s2 = [(p, w) for p, w in toks if w in ('Bitcoin', 'bitcoin')]
CHANNELS['A2_strict'] = ''.join('1' if w[0] == 'B' else '0' for _, w in s2)

# A2b: include the ALLCAPS BITCOIN as 1
s2b = [(p, w) for p, w in toks if w.lower() == 'bitcoin']
CHANNELS['A2b_withcaps'] = ''.join('1' if w[0] == 'B' else '0' for _, w in s2b)

# A2c: bitcoin family INCLUDING allcaps, in printed order
famc = [(p, w) for p, w in toks if w.lower().startswith('bitcoin')]
CHANNELS['A2c_famcaps'] = ''.join('1' if w[0] == 'B' else '0' for _, w in famc)

# A3: every word whose lowercase form appears in >1 casing, all positions
amb = {k for k, v in forms.items() if len({x[0].isupper() for x in v}) > 1}
a3 = [(p, w) for p, w in toks if w.lower() in amb and not is_allcaps(w)]
CHANNELS['A3_ambig'] = ''.join('1' if w[0].isupper() else '0' for _, w in a3)

# A4: same, excluding sentence-initial positions
a4 = [(p, w) for p, w in a3 if not sentence_initial(p)]
CHANNELS['A4_ambig_nosi'] = ''.join('1' if w[0].isupper() else '0' for _, w in a4)

# A4b: content words only (drop stopwords) non-sentence-initial
STOP = set('the a an and or of it is in to this that he she they we you i at on for '
           'but so as be was were are'.split())
a4b = [(p, w) for p, w in a4 if w.lower() not in STOP]
CHANNELS['A4b_content_nosi'] = ''.join('1' if w[0].isupper() else '0' for _, w in a4b)

# A5: every alphabetic character, upper=1
CHANNELS['A5_allchars'] = ''.join('1' if c.isupper() else '0' for c in B if c.isalpha())

# A6: first letter of each word
CHANNELS['A6_initials'] = ''.join('1' if w[0].isupper() else '0' for _, w in toks)

# A7: whole word ALLCAPS = 1
CHANNELS['A7_allcaps'] = ''.join('1' if is_allcaps(w) else '0' for _, w in toks)

# A8: line-level -- line begins with capital
lines = [l for l in B.split('\n') if l.strip()]
CHANNELS['A8_linecap'] = ''.join('1' if l.strip()[0].isupper() else '0' for l in lines)

# A9: word length parity (odd=1) -- typographic, not case
CHANNELS['A9_lenparity'] = ''.join('1' if len(w) % 2 else '0' for _, w in toks)

if __name__ == '__main__':
    for k, v in CHANNELS.items():
        print(f'{k:22s} n={len(v):5d}  {v[:120]}{"..." if len(v)>120 else ""}')
