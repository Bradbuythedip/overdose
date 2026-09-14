#!/usr/bin/env python3
"""Round 2: word-quantity-inclusive BIP39 index maps, ASCII codes, roman, bases."""
import re, sys, itertools
from mnemonic import Mnemonic
W = Mnemonic("english").wordlist

RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
lines = [l for l in RAW.split('\n') if not l.startswith('#')]
page, pages, body = None, {}, []
for l in lines:
    m = re.match(r'=== PAGE (\d+)', l)
    if m: page = int(m.group(1)); pages[page] = []; continue
    if page is not None: pages[page].append(l); body.append(l)
BODY = '\n'.join(body)

SEQ = {
 # sequences that INCLUDE the written-out quantities - the gap in prior work
 'words_in':   [2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'words_nol':  [2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'words_mag':  [2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
                85000000000,2000000000000,51,95,1969,10],
 'words_one':  [2008,1,1,1,40,1971,10,1,2011,1,1000000000,42,20000,100000,6,2017,1,12000,51,
                85,1000000000,2,1000000000000,51,95,1969,10],
 'quant_only': [40,6,1000000000,1000000000,1000000000000],   # the written-out ones alone
 'quant_sm':   [40,6,1,1,1],
 'first12_w':  [2008,1,1,1,40,1971,10,1,2011,1,42,20000],
 'last12_w':   [100000,6,2017,12000,51,85,2,51,95,1969,10,40],
 'tail12_w':   [20000,100000,6,2017,12000,51,85,2,51,95,1969,10],
 'mid12_w':    [40,1971,10,1,2011,1,42,20000,100000,6,2017,12000],
 'dedup_w':    [2008,1,40,1971,10,2011,42,20000,100000,6,2017,12000,51,85,2,95,1969],
}
for k in list(SEQ):
    SEQ['r_'+k] = SEQ[k][::-1]

# nine index conventions, 0- and 1-based
def conv(v):
    yield 'mod', v % 2048
    yield 'inrange', v if v < 2048 else None
    yield 'last3', int(str(v)[-3:])
    yield 'last4mod', int(str(v)[-4:]) % 2048
    yield 'digsum', sum(int(c) for c in str(v))
    yield 'rev', int(str(v)[::-1]) % 2048
    yield 'sq', (v * v) % 2048
    yield 'x11', (v * 11) % 2048
    yield 'and2047', v & 2047

out = []
def add(s):
    if s: out.append(str(s))

for name, s in SEQ.items():
    for cname in ['mod','inrange','last3','last4mod','digsum','rev','sq','x11','and2047']:
        for base in (0, 1):
            idx = []
            ok = True
            for v in s:
                got = dict(conv(v)).get(cname)
                if got is None: ok = False; break
                idx.append((got - base) % 2048)
            if not ok: continue
            ws = [W[i] for i in idx]
            for n in (len(ws), 12, 15, 18, 21, 24):
                if n > len(ws): continue
                for st in range(0, len(ws) - n + 1):
                    m = ' '.join(ws[st:st+n])
                    add(m); add(m.upper())
                    add(' '.join(ws[st:st+n][::-1]))

# ASCII / latin-1 code readings
for name, s in SEQ.items():
    for mod in (256, 128):
        t = ''.join(chr(v % mod) for v in s if v % mod >= 32 or v % mod in (9,10,13))
        add(t); add(t.strip()); add(t[::-1])
    t = ''.join(chr(65 + (v - 1) % 26) for v in s)      # A1Z26
    add(t); add(t.lower()); add(t[::-1]); add(t.lower()[::-1])
    t = ''.join(chr(97 + v % 26) for v in s)
    add(t); add(t.upper()); add(t[::-1])

# roman numerals
def rom(n):
    if n <= 0 or n > 3999: return ''
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),
            (40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    r = ''
    for v, sy in vals:
        while n >= v: r += sy; n -= v
    return r
for name, s in SEQ.items():
    for sep in ['', ' ', '-']:
        r = sep.join(rom(v) for v in s if rom(v))
        add(r); add(r.lower()); add(r[::-1])

# base conversions of the concatenated integer
def tob(n, b, digs="0123456789abcdefghijklmnopqrstuvwxyz"):
    if n == 0: return "0"
    o = ""
    while n: n, r = divmod(n, b); o = digs[r] + o
    return o
for name, s in SEQ.items():
    j = ''.join(str(v) for v in s)
    n = int(j)
    for b in (2, 8, 16, 32, 36, 58, 62):
        if b <= 36:
            t = tob(n, b); add(t); add(t.upper())
    add(hex(n)[2:]); add(hex(n)[2:].upper()); add(oct(n)[2:]); add(bin(n)[2:])
    # binary of the small values, concatenated
    add(''.join(bin(v)[2:] for v in s))
    add(''.join(f'{v:08b}' for v in s if v < 256))
    add(''.join(f'{v:016b}' for v in s if v < 65536))

# 64-hex raw keys from these word-inclusive sequences
hexes = []
for name, s in SEQ.items():
    j = ''.join(str(v) for v in s)
    n = int(j) % (1 << 256)
    hexes += [f'{n:064x}', n.to_bytes(32,'little').hex()]
    for pad in (j.rjust(64,'0'), j.ljust(64,'0'), j[:64], j[-64:]):
        if len(pad) == 64: hexes.append(pad)
    pos = [v for v in s if v >= 0]
    b1 = bytes(v % 256 for v in pos)
    for v in (b1.rjust(32,b'\0'), b1.ljust(32,b'\0'), b1[::-1].rjust(32,b'\0'), b1[::-1].ljust(32,b'\0')):
        if len(v) == 32: hexes.append(v.hex())
    for w in (2,4):
        for e in ('big','little'):
            bb = b''.join((v % (1<<(8*w))).to_bytes(w,e) for v in pos)
            for v in (bb.rjust(32,b'\0'), bb.ljust(32,b'\0'), bb[:32], bb[-32:]):
                if len(v)==32: hexes.append(v.hex())
    ab = j.encode()
    for v in (ab.rjust(32,b'\0'), ab.ljust(32,b'\0'), ab[:32], ab[-32:]):
        if len(v)==32: hexes.append(v.hex())
out += hexes + [h.upper() for h in hexes]

seen, fin = set(), []
for x in out:
    x = x.strip()
    if x and x not in seen and len(x) < 3900:
        seen.add(x); fin.append(x)
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(fin)+'\n')
print(len(fin), 'unique')
