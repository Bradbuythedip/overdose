#!/usr/bin/env python3
"""Banknote-derived candidates from the $100 note photographed on pages 73/74
(serial CL 76841714 A, district L12), tested offline against address_map.bin."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_check import Index, sha, h160, keys_from_phrase, key_forms
import coincurve
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 2**256 - 2**32 - 977
def scripts_for(pc, pu):
    hc=h160(pc); hu=h160(pu); ph=h160(b'\x00\x14'+hc)
    return [b'\x76\xa9\x14'+hc+b'\x88\xac', b'\x76\xa9\x14'+hu+b'\x88\xac',
            b'\x00\x14'+hc, b'\xa9\x14'+ph+b'\x87']
def check(idx, kb, label, out):
    ki=int.from_bytes(kb,'big')
    if not (0<ki<N): return 0
    xy=coincurve.PublicKey.from_valid_secret(kb).format(compressed=False)
    x,y=xy[1:33],xy[33:65]; yi=int.from_bytes(y,'big'); ev=yi%2==0
    n=0
    for mi,(pc,pu) in enumerate([((b'\x02' if ev else b'\x03')+x, b'\x04'+x+y),
                                 ((b'\x03' if ev else b'\x02')+x, b'\x04'+x+((P-yi)%P).to_bytes(32,'big'))]):
        for spk in scripts_for(pc,pu):
            b=idx.lookup(sha(spk))
            if b:
                out.write(f"HIT\t{label}\tmirror={mi}\t{b}\n"); out.flush()
                sys.stderr.write(f"*** HIT *** {label} bal={b}\n"); n+=1
    return n

SER = "76841714"
base = ["CL76841714A","CL 76841714 A","CL76841714","76841714A","76841714","L12",
        "CL76841714AL12","CL76841714A L12","cl76841714a","A41714867LC","41714867",
        "CL","A","L 12","12","76841714AL12","CL76841714A12"]
extra=[]
for b in base:
    extra += [b, b.upper(), b.lower(), b[::-1], b.replace(" ","")]
for tail in ["", " OVERDOSE", " Max Keiser", " MAX KEISER", " overdose", " Bitcoin",
             " El Salvador", " 20", " 20 BTC", " Overdose Max Keiser"]:
    extra.append("CL76841714A"+tail); extra.append(SER+tail)
cands = sorted(set(extra))
idx = Index('/tmp/od/address_map.bin')
sys.stderr.write(f"index {idx.n:,}; candidates {len(cands)}\n")
out=open('note_hits.tsv','w'); out.write("result\tlabel\tmirror\tbalance_sats\n")
nk=0; hits=0
for c in cands:
    for kind,k in keys_from_phrase(c):
        for form,kk in key_forms(k):
            nk+=1; hits+=check(idx,kk,f"{c!r}|{kind}|{form}",out)
# serial digits interpreted directly as key material
for pad in ('big','little'):
    kb=int(SER).to_bytes(32,pad); nk+=1; hits+=check(idx,kb,f"serial-int-{pad}",out)
out.close()
sys.stderr.write(f"DONE candidates={len(cands)} keys={nk:,} HITS={hits}\n")
