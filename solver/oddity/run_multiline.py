#!/usr/bin/env python3
"""Test strings that CONTAIN NEWLINES -- the printed-line form of each page and
of the whole piece.  These cannot be expressed in the one-per-line file format
that try_phrases.py reads, so they have never been tested."""
import re, sys
sys.path.insert(0, '/home/user/overdose/solver')
import continuous_solver as CS
from try_phrases import run

RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
pages = re.split(r'=== PAGE (\d+) \(([^)]*)\) ===', RAW)
blocks = {}
for i in range(1, len(pages), 3):
    blocks[f'p{pages[i]}'] = pages[i+2]
keys = list(blocks)
blocks['ALL'] = ''.join(blocks[k] for k in keys)
for n in (2, 3, 4):
    for i in range(len(keys) - n + 1):
        blocks['+'.join(keys[i:i+n])] = ''.join(blocks[k] for k in keys[i:i+n])

phrases = []
for name, t in blocks.items():
    tight = '\n'.join(l.strip() for l in t.strip().split('\n') if l.strip())
    raw = t.strip('\n')
    for v in {raw, raw.strip(), tight, tight.lower(), tight.upper(),
              tight + '\n', '\n' + tight, raw.replace('\n\n', '\n'),
              tight.replace('\n', '\r\n'), tight[::-1],
              '\n'.join(tight.split('\n')[::-1]),
              tight.replace('10years', '10 years'),
              raw.replace('10years', '10 years')}:
        if v and len(v) < 4000:
            phrases.append(v)
phrases = list(dict.fromkeys(phrases))
print(f'{len(phrases)} multi-line phrases', file=sys.stderr)

orc = CS.IndexOracle()
assert orc.ready, orc.why
assert orc.control(), 'POSITIVE CONTROL FAILED'
print('control OK', file=sys.stderr)
hits, n = run(phrases, orc, 'MULTILINE', hd=True)
print(f'{n:,} scriptPubKeys, {len(hits)} hit(s)', file=sys.stderr)
for p, dn, st, bal in hits:
    print(f'HIT\t{bal}\t{dn}\t{st}\t{p!r}')
if not hits:
    print('no hit', file=sys.stderr)
