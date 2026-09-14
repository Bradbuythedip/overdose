#!/usr/bin/env python3
"""
George Sand positional-cipher extractions over the transcribed body text,
verified offline against address_map.bin. No network required.

Keiser, Dec 2022 (tweet 1607378060172460032): "Like George Sand's hidden
cryptography, I have hidden private keys in the text."
"""
import hashlib, itertools, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_check import Index, sha, h160, keys_from_phrase, key_forms
import coincurve

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 2**256 - 2**32 - 977
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58SET = set(B58)

def scripts_for(pc, pu):
    hc = h160(pc); hu = h160(pu); ph = h160(b'\x00\x14' + hc)
    return [b'\x76\xa9\x14'+hc+b'\x88\xac', b'\x76\xa9\x14'+hu+b'\x88\xac',
            b'\x00\x14'+hc, b'\xa9\x14'+ph+b'\x87']

def check_priv(idx, kb, label, out):
    ki = int.from_bytes(kb, 'big')
    if not (0 < ki < N): return 0
    xy = coincurve.PublicKey.from_valid_secret(kb).format(compressed=False)
    x, y = xy[1:33], xy[33:65]; yi = int.from_bytes(y, 'big'); even = yi % 2 == 0
    forms = [((b'\x02' if even else b'\x03')+x, b'\x04'+x+y),
             ((b'\x03' if even else b'\x02')+x, b'\x04'+x+((P-yi)%P).to_bytes(32,'big'))]
    n = 0
    for mi, (pc, pu) in enumerate(forms):
        for spk in scripts_for(pc, pu):
            bal = idx.lookup(sha(spk))
            if bal:
                out.write(f"HIT\t{label}\tmirror={mi}\t{sha(spk).hex()}\t{bal}\n"); out.flush()
                sys.stderr.write(f"*** HIT *** {label} bal={bal}\n"); n += 1
    return n

# ---------- extractions ----------
def extractions(lines):
    text_lines = [l.rstrip('\n') for l in lines if l.strip()]
    joined = ' '.join(text_lines)
    words = joined.split()
    chars = re.sub(r'\s+', '', joined)
    E = {}
    E['first_letter_per_line'] = ''.join(l.lstrip()[0] for l in text_lines if l.strip())
    E['last_letter_per_line']  = ''.join(l.rstrip()[-1] for l in text_lines if l.strip())
    for n in range(2, 11):
        E[f'every_{n}th_line_firstletter'] = ''.join(
            l.lstrip()[0] for l in text_lines[::n] if l.strip())
        E[f'every_{n}th_word_firstletter'] = ''.join(w[0] for w in words[::n])
        E[f'every_{n}th_char'] = chars[::n]
    for off in range(1, 3):
        E[f'alt_line_off{off}_firstletter'] = ''.join(
            l.lstrip()[0] for l in text_lines[off::2] if l.strip())
        E[f'alt_line_off{off}_text'] = ''.join(text_lines[off::2])
    E['first_word_per_line'] = ''.join(l.split()[0] for l in text_lines if l.split())
    E['last_word_per_line']  = ''.join(l.split()[-1] for l in text_lines if l.split())
    E['caps_only'] = ''.join(c for c in joined if c.isupper())
    E['digits_only'] = ''.join(c for c in joined if c.isdigit())
    base = dict(E)
    for k, v in base.items():          # mirrored variants
        E[k + '__rev'] = v[::-1]
    return E

def main():
    idx = Index('/tmp/od/address_map.bin')
    sys.stderr.write(f"index: {idx.n:,} scripthashes\n")
    out = open('/home/user/overdose/solver/gsand_hits.tsv', 'w')
    out.write("result\tlabel\tmirror\tscripthash\tbalance_sats\n")
    D = '/home/user/overdose/solver/transcript'
    sources = {'all': open(f'{D}/all_pages.txt').readlines()}
    for p in ('p75','p76','p77','p78','p79'):
        sources[p] = open(f'{D}/{p}.txt').readlines()
    total_hits = 0; nkeys = 0
    for src, lines in sources.items():
        E = extractions(lines)
        for label, s in E.items():
            if len(s) < 4: continue
            tag = f"{src}:{label}"
            # (a) as a brainwallet passphrase, all hash variants x key involutions
            for kind, k in keys_from_phrase(s):
                for form, kk in key_forms(k):
                    nkeys += 1
                    total_hits += check_priv(idx, kk, f"{tag}|{kind}|{form}", out)
            # (b) as raw hex
            hx = re.sub(r'[^0-9a-fA-F]', '', s)
            if len(hx) >= 64:
                for st in range(0, len(hx)-63):
                    nkeys += 1
                    total_hits += check_priv(idx, bytes.fromhex(hx[st:st+64]), f"{tag}|rawhex@{st}", out)
            # (c) as WIF
            cand = ''.join(c for c in s if c in B58SET)
            for L in (51, 52):
                for st in range(0, max(0, len(cand)-L+1)):
                    w = cand[st:st+L]
                    if L == 51 and not w.startswith('5'): continue
                    if L == 52 and w[0] not in 'KL': continue
                    try:
                        num = 0
                        for ch in w: num = num*58 + B58.index(ch)
                        raw = num.to_bytes(37 if L==51 else 38, 'big')
                        if raw[0] != 0x80: continue
                        nkeys += 1
                        total_hits += check_priv(idx, raw[1:33], f"{tag}|wif@{st}", out)
                    except Exception: pass
        sys.stderr.write(f"  {src}: {len(E)} extractions, cumulative keys={nkeys:,} hits={total_hits}\n")
    out.close()
    sys.stderr.write(f"DONE extractions checked, keys={nkeys:,}, HITS={total_hits}\n")

if __name__ == '__main__':
    main()
