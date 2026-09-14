#!/usr/bin/env python3
"""Number-sequence lens: every numeral/quantity of Overdose pp.75-79, ordered."""
import re, hashlib, itertools, sys

RAW = open('/home/user/overdose/solver/article_transcript.txt', encoding='utf-8').read()
lines = [l for l in RAW.split('\n') if not l.startswith('#')]
page, pages, body = None, {}, []
for l in lines:
    m = re.match(r'=== PAGE (\d+)', l)
    if m:
        page = int(m.group(1)); pages[page] = []
        continue
    if page is not None:
        pages[page].append(l); body.append(l)
BODY = '\n'.join(body)

# ---------------- the sequences ----------------
LAYER1 = [2008, 1, 1, 1]
S = {}
S['printed']   = [2008,1,1,1,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
S['brief']     = [2008,1971,40,10,1,2011,1,42,20000,100000,6,12000,2017,51,85,2,51,95,1969,10]
S['nolayer']   = [2008,40,1971,10,1,2011,1,42,20000,100000,6,2017,12000,51,85,2,51,95,1969,10]
S['numerals']  = [2008,1,1,1,1971,10,1,2011,1,42,20000,100000,2017,12000,51,85,2,51,95,1969,10]
S['expanded']  = [2008,1,1,1,40,1971,10,1,2011,1000000000,42,20000,100000,6,2017,12000,51,
                  85000000000,2000000000000,51,95,1969,10]
S['withone']   = [2008,1,1,1,40,1971,10,1,2011,1,1000000000,42,20000,100000,6,2017,1,12000,51,
                  85,1000000000,2,1000000000000,51,95,1969,10]
S['years']     = [2008,1971,2011,2017,1969]
S['pct']       = [42,51,51,95]
S['dollars']   = [1,1,85,2]
S['big']       = [2008,1971,2011,20000,100000,2017,12000,1969]
S['dedup']     = list(dict.fromkeys(S['printed']))
S['p75']       = [2008,1,1,1]
S['p76']       = [40,1971,10,1,2011,1]
S['p77']       = [42,20000,100000,6,2017,12000,51]
S['p78']       = [85,2]
S['p79']       = [51,95,1969,10]
S['striking']  = [51,42,95,21000000]
S['pair']      = [20000,100000]
S['puzzle']    = [20,24,2021,75,79]
S['printed21'] = S['printed'] + [21000000]
S['printed20'] = [20] + S['printed']

# derived sequences
def diffs(s):  return [s[i+1]-s[i] for i in range(len(s)-1)]
def absd(s):   return [abs(x) for x in diffs(s)]
def cums(s):
    o, t = [], 0
    for x in s: t += x; o.append(t)
    return o
for k in list(S):
    S['d_'+k]  = diffs(S[k])
    S['ad_'+k] = absd(S[k])
    S['c_'+k]  = cums(S[k])
    S['r_'+k]  = S[k][::-1]
    S['s_'+k]  = sorted(S[k])
    S['sd_'+k] = sorted(S[k], reverse=True)

SEPS = ['', ' ', '-', ',', '.', '/', ':', '_', '+', '|', ', ', ' - ', '\t', ';']

strs, hexes = [], []
def add(x):
    if x: strs.append(str(x))
def addhex(b):
    if isinstance(b, int):
        if b < 0: b = -b
        b = (b % (1 << 256)).to_bytes(32, 'big')
    if len(b) != 32: return
    hexes.append(b.hex()); hexes.append(b.hex().upper())

# ---------------- 1. joins ----------------
for name, seq in S.items():
    for sep in SEPS:
        add(sep.join(str(x) for x in seq))
        add(sep.join(str(x) for x in seq[::-1]))
        add(sep.join(str(x)[::-1] for x in seq))
    j = ''.join(str(x) for x in seq)
    add(j[::-1])
    add('0x' + j)
    add('#' + j)

# ---------------- 2. printed surface forms ----------------
SURF = ['2008','1','1','1','Forty','1971','10','1','2011','1 billion','42','20,000',
        '100,000','six','2017','12,000','51','85','2','51','95','1969','10']
SURF2 = ['2008','Forty','1971','10years','$1','2011','$1 billion','42%','20,000','100,000',
         'six','2017','12,000','51%','$85 BILLION','$2 trillion','51%','95%','1969','10 years']
SURF3 = ['2008','forty','1971','ten','one','2011','one billion','forty two','twenty thousand',
         'one hundred thousand','six','2017','twelve thousand','fifty one','eighty five','two',
         'fifty one','ninety five','1969','ten']
for src in (SURF, SURF2, SURF3):
    for sep in ['', ' ', '-', ',', '/', '_', ', ']:
        s = sep.join(src); add(s); add(s.lower()); add(s.upper()); add(s[::-1])
        s = sep.join(src[::-1]); add(s); add(s.lower()); add(s.upper())

# ---------------- 3. arithmetic scalars ----------------
import functools, operator
for name, seq in S.items():
    j = ''.join(str(x) for x in seq)
    n_concat = int(j) if j.lstrip('-').isdigit() else None
    tot  = sum(seq)
    prod = functools.reduce(operator.mul, [x for x in seq if x], 1)
    xo   = functools.reduce(operator.xor, [abs(x) for x in seq], 0)
    dsum = sum(int(c) for c in j if c.isdigit())
    for v in (n_concat, tot, prod, xo, dsum, tot*len(seq), prod % (1 << 256)):
        if v is None: continue
        add(v); addhex(v)
        if 0 <= v < (1 << 256):
            addhex(v.to_bytes(32, 'little'))
    add(f'sum={tot}'); add(f'{tot}'); add(str(tot)[::-1])

# ---------------- 4. raw-key byte renderings ----------------
for name, seq in S.items():
    pos = [x for x in seq if 0 <= x]
    j = ''.join(str(x) for x in seq if x >= 0)
    # decimal concat as hex digits, padded / truncated
    for pad in (j.rjust(64, '0'), j.ljust(64, '0'), j.rjust(64, 'f'), j.ljust(64, 'f'),
                j[:64], j[-64:]):
        if len(pad) == 64 and all(c in '0123456789abcdefABCDEF' for c in pad):
            hexes.append(pad); hexes.append(pad.upper())
    # one byte per value
    b1 = bytes(x % 256 for x in pos)
    for v in (b1.rjust(32, b'\0'), b1.ljust(32, b'\0'), b1[:32], b1[::-1].ljust(32, b'\0'),
              b1[::-1].rjust(32, b'\0')):
        addhex(v)
    # 2-byte and 4-byte big/little endian
    for w in (2, 4):
        for endi in ('big', 'little'):
            try:
                bb = b''.join((x % (1 << (8*w))).to_bytes(w, endi) for x in pos)
            except Exception:
                continue
            addhex(bb.rjust(32, b'\0')); addhex(bb.ljust(32, b'\0'))
            addhex(bb[:32]); addhex(bb[-32:]); addhex(bb[::-1][:32].ljust(32, b'\0'))
    # ascii of the joined decimal, padded
    ab = j.encode()
    addhex(ab.rjust(32, b'\0')); addhex(ab.ljust(32, b'\0')); addhex(ab[:32]); addhex(ab[-32:])
    addhex(ab.ljust(32, b' ')); addhex(ab.rjust(32, b' '))

# ---------------- 5. sequence as character indices ----------------
NORMS = {
    'raw':     BODY,
    'nospace': re.sub(r'\s+', '', BODY),
    'alpha':   re.sub(r'[^A-Za-z]', '', BODY),
    'alnum':   re.sub(r'[^A-Za-z0-9]', '', BODY),
    'collapse': re.sub(r'\s+', ' ', BODY).strip(),
    'lowalpha': re.sub(r'[^a-z]', '', BODY.lower()),
}
for pn, pl in pages.items():
    NORMS[f'p{pn}'] = re.sub(r'[^A-Za-z]', '', '\n'.join(pl))
WORDS = re.findall(r"[A-Za-z']+", BODY)

for name, seq in S.items():
    if len(seq) < 3: continue
    for nname, txt in NORMS.items():
        if not txt: continue
        for base in (0, 1):
            out = ''.join(txt[(x - base) % len(txt)] for x in seq if x >= 0)
            add(out); add(out.lower()); add(out.upper()); add(out[::-1])
        cs = cums([x for x in seq if x >= 0])
        for base in (0, 1):
            out = ''.join(txt[(x - base) % len(txt)] for x in cs)
            add(out); add(out.lower()); add(out[::-1])
    for base in (0, 1):
        w = ' '.join(WORDS[(x - base) % len(WORDS)] for x in seq if x >= 0)
        add(w); add(w.lower()); add(w.upper()); add(w.replace(' ', ''))
        add(w.replace(' ', '').lower())

# ---------------- 6. standalone striking numbers ----------------
STAND = ['51', '42', '95', '21000000', '21,000,000', '20000', '100000', '20,000', '100,000',
         '2008', '1971', '2011', '2017', '1969', '85', '12000', '12,000', '40', '6', '10', '2',
         '51%', '42%', '95%', '51% attack', '42% of the country', '95% or more']
for a in STAND:
    add(a); add(a * 2); add(a * 3); add(a[::-1])
    for b in STAND:
        for sep in ['', ' ', '-', '/', ':', '_', ',']:
            add(a + sep + b)
for v in (51, 42, 95, 21000000, 20000, 100000, 2008, 1971, 2011, 2017, 1969, 85, 12000,
          40, 6, 10, 2, 5142, 4251, 9551, 2000000000000, 85000000000, 1000000000):
    addhex(v); addhex(v.to_bytes(32, 'little'))
    add(f'{v:x}'); add(f'{v:064x}'); add(str(v))
# 51/42/95 permutations as a key
for perm in itertools.permutations([51, 42, 95, 21000000]):
    for sep in ['', ' ', '-', ':', '/']:
        add(sep.join(str(x) for x in perm))

# ---------------- 7. mixed word+number keys ----------------
KEYW = ['Overdose', 'overdose', 'OVERDOSE', 'MaxKeiser', 'Max Keiser', 'maxkeiser',
        'Bitcoin', 'bitcoin', 'ElSalvador', 'El Salvador', 'Layer1', 'Satoshi', 'toxic',
        'Toxic Bitcoin Maximalist', 'VolcanoBonds', 'Volcano Bonds', 'Stacy']
for name in ('printed', 'brief', 'nolayer', 'years', 'pct', 'striking'):
    for sep in ['', ' ', '-']:
        j = sep.join(str(x) for x in S[name])
        for k in KEYW:
            add(k + j); add(j + k); add(k + sep + j); add(j + sep + k)

out = []
seen = set()
for x in strs + hexes:
    x = x.strip('\n')
    if x and x not in seen and len(x) < 3900:
        seen.add(x); out.append(x)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
hx = [x for x in hexes if len(x) == 64]
print(f'{len(out)} unique candidates ({len(set(hx))} are 64-char literal-hex keys)')
