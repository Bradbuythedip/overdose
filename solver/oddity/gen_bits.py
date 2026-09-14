#!/usr/bin/env python3
"""Expand each bit-channel into every reasonable key packing."""
import sys, hashlib
sys.path.insert(0, '/home/user/overdose/solver/oddity')
from bits import CHANNELS

BIP39 = None
def bip39():
    global BIP39
    if BIP39 is None:
        import os
        for p in ['/home/user/overdose/solver/oddity/english.txt',
                  '/usr/share/dict/bip39.txt']:
            if os.path.exists(p):
                BIP39 = open(p).read().split()
                break
        else:
            BIP39 = []
    return BIP39

out = []
def add(s):
    if s and len(s) < 4000:
        out.append(s)

def bacon(bits, a='0'):
    r = []
    for i in range(0, len(bits) - 4, 5):
        g = bits[i:i+5]
        v = int(''.join('1' if c != a else '0' for c in g), 2)
        r.append(chr(65 + v) if v < 26 else '?')
    return ''.join(r)

def ascii8(bits):
    r = []
    for i in range(0, len(bits) - 7, 8):
        v = int(bits[i:i+8], 2)
        r.append(chr(v) if 32 <= v < 127 else '?')
    return ''.join(r)

def pack(bits, name):
    n = len(bits)
    add(bits)
    add(bits[::-1])
    comp = ''.join('1' if c == '0' else '0' for c in bits)
    add(comp)
    add(comp[::-1])
    for b in (bits, bits[::-1], comp):
        try:
            v = int(b, 2)
        except ValueError:
            continue
        add(str(v))
        h = format(v, 'x')
        add(h); add(h.upper()); add('0x' + h)
        # padded literal private keys (64 hex chars)
        if len(h) <= 64:
            add(h.rjust(64, '0'))
            add(h.ljust(64, '0'))
            add(h.rjust(64, '0').upper())
            add(h.ljust(64, '0').upper())
        else:
            add(h[:64]); add(h[-64:]); add(h[:64].upper())
        # byte packing big/little
        nb = (len(b) + 7) // 8
        try:
            bb = v.to_bytes(nb, 'big')
            add(bb.hex()); add(bb[::-1].hex())
            add(bb.hex().rjust(64, '0')); add(bb[::-1].hex().rjust(64, '0'))
            add(hashlib.sha256(bb).hexdigest())
        except Exception:
            pass
    # bit-string slices that are exactly 256 bits
    for start in (0, 1, 8):
        if n >= 256 + start:
            seg = bits[start:start+256]
            add(format(int(seg, 2), 'x').rjust(64, '0'))
            add(format(int(seg[::-1], 2), 'x').rjust(64, '0'))
        if n >= 256 + start:
            seg = bits[-(256+start):len(bits)-start] if start else bits[-256:]
            add(format(int(seg, 2), 'x').rjust(64, '0'))
    # baconian both polarities
    for a in ('0', '1'):
        t = bacon(bits, a)
        if t and '?' not in t[:40]:
            add(t); add(t.lower()); add(t[:64])
        add(t[:200])
    # ascii
    t = ascii8(bits)
    add(t[:200])
    add(ascii8(bits[::-1])[:200])
    # 11-bit BIP39 words
    w = bip39()
    if w:
        for off in (0, 1):
            ws = []
            for i in range(off, len(bits) - 10, 11):
                ws.append(w[int(bits[i:i+11], 2)])
            for k in (12, 15, 18, 21, 24):
                if len(ws) >= k:
                    add(' '.join(ws[:k]))
                    add(' '.join(ws[-k:]))
            if 0 < len(ws) < 12:
                add(' '.join(ws))
    # label-prefixed forms
    add(name + bits)
    add(name + ':' + bits)

for name, bits in CHANNELS.items():
    pack(bits, name)

seen = set()
for s in out:
    if s not in seen:
        seen.add(s)
        print(s)
