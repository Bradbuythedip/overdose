#!/usr/bin/env python3
"""The NATURALLY checksum-valid mnemonics: word runs that the capitalisation
mask produced and that pass BIP-39 without any last-word brute force. These are
the only members of wave 7 with a real prior."""
import re, sys
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from bits import CHANNELS
from mnemonic import Mnemonic
M = Mnemonic('english'); WS = set(M.wordlist)
B = '\n'.join(l for l in open('/home/user/overdose/solver/article_transcript.txt',
              encoding='utf-8').read().split('\n')
              if not l.startswith('#') and not l.startswith('==='))
F = re.sub(r'\s+', ' ', B).strip()
WORDS = [w.strip('.,?!";:()—$%\'’').lower() for w in F.split()]
BW = [w for w in WORDS if w in WS]
out = []
def try_run(ws):
    for k in (12, 15, 18, 21, 24):
        for run in (ws[:k], ws[-k:]):
            if len(run) == k:
                s = ' '.join(run)
                if M.check(s):
                    out.append(s)
for bits in CHANNELS.values():
    for pol in ('1', '0'):
        for base, nm in ((BW, 'bw'), (WORDS, 'all')):
            sel = [base[i] for i, b in enumerate(bits) if i < len(base) and b == pol]
            if nm == 'all':
                sel = [w for w in sel if w in WS]
            if len(sel) >= 12:
                try_run(sel)
        # windows of the mask
        for off in range(0, 40, 4):
            sel = [BW[i] for i, b in enumerate(bits[off:], 0)
                   if i < len(BW) and b == pol]
            if len(sel) >= 12: try_run(sel)
seen = set()
for s in out:
    if s not in seen:
        seen.add(s); print(s)
