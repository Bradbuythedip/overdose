#!/usr/bin/env python3
"""Wave 6: the WHOLE-UNIT gap.  Prior sweeps covered sentences, paragraphs,
lines and 2-8 word n-grams -- but never a whole PAGE or the whole piece as one
string, in each normalisation, and never with the 10years correction toggled."""
import re, hashlib
RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
pages = re.split(r'=== PAGE (\d+) \(([^)]*)\) ===', RAW)
out = []
def add(*xs):
    for x in xs:
        if not x: continue
        x = x.strip()
        if 8 < len(x) < 4000: out.append(x)

def norms(t):
    """every plausible normalisation of a block of printed text"""
    flat = re.sub(r'[ \t]+', ' ', t).strip()
    one = re.sub(r'\s+', ' ', t).strip()
    yield t.strip()                                  # as printed, line breaks
    yield t.strip().replace('\n', ' ')
    yield flat
    yield one
    yield one.lower()
    yield one.upper()
    yield one.replace(' ', '')
    yield one.replace(' ', '').lower()
    yield ''.join(c for c in one if c.isalnum())
    yield ''.join(c for c in one if c.isalnum()).lower()
    yield ''.join(c for c in one if c.isalpha())
    yield ''.join(c for c in one if c.isalpha()).lower()
    yield ''.join(c for c in one if c.isalpha()).upper()
    yield one[::-1]
    yield one.lower()[::-1]
    yield ''.join(c for c in one if c.isalpha()).lower()[::-1]
    yield ' '.join(one.split()[::-1])                 # word-reversed
    yield '\n'.join(l.strip() for l in t.strip().split('\n') if l.strip())
    yield ' '.join(l.strip() for l in t.strip().split('\n') if l.strip())
    yield one.replace(' ', '').replace('.', '')
    yield re.sub(r'[^A-Za-z0-9]', '', one)
    yield re.sub(r'[^A-Za-z0-9]', '', one).lower()

# ---- per page ---------------------------------------------------------------
blocks = {}
for i in range(1, len(pages), 3):
    num, img, txt = pages[i], pages[i+1], pages[i+2]
    blocks[f'p{num}'] = txt
body_all = ''.join(blocks.values())
blocks['ALL'] = body_all

# consecutive page pairs and triples
keys = [k for k in blocks if k.startswith('p')]
for n in (2, 3, 4):
    for i in range(len(keys) - n + 1):
        blocks['+'.join(keys[i:i+n])] = ''.join(blocks[k] for k in keys[i:i+n])

for name, txt in blocks.items():
    for v in norms(txt):
        add(v)
    # with the 10years correction toggled back to the old transcript form
    if '10years' in txt:
        for v in norms(txt.replace('10years', '10 years')):
            add(v)
        for v in norms(txt.replace('10years', '10  years')):
            add(v)

# ---- whole piece, truncated to fit the tester's 4000-char limit -------------
one = re.sub(r'\s+', ' ', body_all).strip()
letters = ''.join(c for c in one if c.isalpha())
for s in (one, one.lower(), letters, letters.lower(), one.replace(' ', '')):
    add(s[:3999]); add(s[-3999:]); add(s[:2048]); add(s[:1024]); add(s[:512])
    add(s[:256]); add(s[:128]); add(s[:64]); add(s[:32])
# halves / thirds
for cut in (2, 3, 4):
    L = len(one) // cut
    for i in range(cut):
        seg = one[i*L:(i+1)*L]
        if len(seg) < 4000:
            add(seg, seg.lower(), ''.join(c for c in seg if c.isalpha()).lower())

# ---- the masthead-only pages 73-74 -----------------------------------------
for s in ['OVERDOSE', 'Overdose', 'overdose', 'OVERDOSE OVERDOSE',
          'OVERDOSE MAX KEISER', 'OVERDOSE BITCOIN IS TOXIC AF',
          'OVERDOSE 73 74', 'OVERDOSE pages 73 74']:
    add(s)

seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
