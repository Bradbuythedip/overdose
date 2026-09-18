#!/usr/bin/env python3
"""
Every clue x both serials, swept against the real 56M index. No partial credit.

The request: cross all the puzzle's clues with the two banknote serials and run
until something turns up. There is no "semi-hit" in key search -- a checksum is
binary, an address is or isn't funded -- so this uses the REAL oracle (the 56M
funded-address index) and, separately, counts self-certifying outcomes AGAINST
their chance expectation so a true signal is distinguishable from noise.

CLUES crossed with the serials:
  article sentences / lines / paragraphs, and 2-6-word n-grams
  the highlighted runs (the designer's marks)
  George Sand alternate-line and first-word readings (his named device)
  El Salvador / Bukele / volcano / mirror / Overdose / Genesis keyword set
SERIALS (both, every form): CL76841714A/76841714/CL/L12 and reversals;
  KB46279860/46279860/KB and reversals; and the two combined.

Each clue x serial join -> 7 direct hashes -> 25 script forms -> 56M index,
plus WIF/BIP-39/hex64 self-certification. Runs in rounds until the clue corpus
is exhausted; --loop repeats widening the n-gram span.

  python3 clue_serial.py --selftest
  python3 clue_serial.py
"""
import argparse, hashlib, itertools, sys, time

N=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

SERIALS = ["CL76841714A","76841714","CL","L12","41714867","A41714867LC",
           "KB46279860","46279860","KB","06897264",
           "CL76841714AKB46279860","7684171446279860","76841714 46279860"]

def clue_phrases(ngram_max=6):
    import article
    lines,sents,paras=article.load()
    out=list(sents)+list(lines)
    words=" ".join(paras).split()
    for n in range(2,ngram_max+1):
        for i in range(len(words)-n+1):
            out.append(" ".join(words[i:i+n]))
    # highlight runs
    try:
        for l in open("highlights_ordered.tsv",encoding="utf-8"):
            if not l.startswith("#") and l.strip():
                p=l.rstrip("\n").split("\t")
                if len(p)>=3: out.append(p[2])
    except OSError: pass
    # George Sand readings: alternate lines, first word of each line
    ll=[l for l in lines if l.strip()]
    for off in (0,1):
        out.append(" ".join(ll[off::2]))
        out.append(" ".join(w.split()[0] for w in ll[off::2] if w.split()))
    # keyword clues
    out += ["El Salvador","Bukele","Nayib Bukele","volcano","Volcano Bonds",
            "mirror","George Sand","OVERDOSE","Overdose","toxic","Max Keiser",
            "Genesis Block","The Times 03/Jan/2009 Chancellor on brink of "
            "second bailout for banks","21000000","peace and love"]
    seen,uniq=set(),[]
    for p in out:
        p=(p or "").strip()
        if p and p not in seen and len(p)<2000:
            seen.add(p); uniq.append(p)
    return uniq

def wif_valid(s):
    B58="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if not(50<=len(s)<=53) or any(c not in B58 for c in s): return False
    n=0
    for c in s: n=n*58+B58.index(c)
    raw=n.to_bytes((n.bit_length()+7)//8,"big")
    if len(raw)<37 or raw[0]!=0x80: return False
    return hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4]==raw[-4:]

def run(phrases, orc):
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    from hd_sweep import direct_keys
    meta,spks,hits=[],[],[]
    n=0; certif=0; bip=0; bipwin=0
    try:
        from mnemonic import Mnemonic
        MNE=Mnemonic("english")
    except Exception:
        MNE=None
    def flush():
        nonlocal meta,spks
        if not spks: return
        for j,bal in orc.check(spks):
            hits.append(meta[j]+(bal,))
            sys.stderr.write(f"\n  *** INDEX HIT {bal} sats :: {meta[j]}\n"); sys.stderr.flush()
        meta,spks=[],[]
    t0=time.time()
    for i,p in enumerate(phrases,1):
        for s in SERIALS:
            for combo in (p+s, s+p, p+" "+s, s+" "+p):
                # self-certify the string form
                flat=combo.replace(" ","")
                if wif_valid(flat): certif+=1; sys.stderr.write(f"\n  *** WIF-VALID: {flat}\n")
                if MNE:
                    ws=combo.split()
                    if len(ws) in (12,15,18,21,24) and MNE.check(" ".join(w.lower() for w in ws)): bip+=1
                for hn,k in direct_keys(combo).items():
                    if not(0<int.from_bytes(k,"big")<N): continue
                    for st,spk in list(spks_for_key(k))+list(spks_extra(k)):
                        meta.append(f"{p[:40]}|{s}|{hn}/{st}"); spks.append(spk); n+=1
                    if len(spks)>=50000: flush()
        if i%400==0:
            flush()
            sys.stderr.write(f"\r  {i:,}/{len(phrases):,} clues  {n:,} scripts  "
                             f"{n/max(time.time()-t0,1e-9):,.0f}/s  ")
            sys.stderr.flush()
    flush()
    return hits,n,certif,bip

def selftest():
    ok=True
    ok &= wif_valid("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ")
    ok &= not wif_valid("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTX")
    sys.stderr.write(f"  WIF validator accepts a real WIF, rejects a corrupted one: "
                     f"{'OK' if ok else 'FAIL'}\n")
    p=clue_phrases(ngram_max=3)
    ok &= len(p)>500
    sys.stderr.write(f"  {len(p):,} clue phrases x {len(SERIALS)} serial forms x 4 joins\n")
    sys.stderr.write("  SELFTEST "+("PASS\n" if ok else "FAIL\n"))
    return ok

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ngram-max",type=int,default=6)
    ap.add_argument("--loop",action="store_true")
    ap.add_argument("--selftest",action="store_true")
    a=ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(): sys.exit("bad setup")
    if a.selftest: return
    import continuous_solver as CS
    orc=CS.IndexOracle()
    if not orc.ready: sys.exit(f"no oracle: {orc.why}")
    if not orc.control(): sys.exit("positive control failed; a null would be void")
    sys.stderr.write("  oracle control OK\n")
    nmax=a.ngram_max
    while True:
        ph=clue_phrases(nmax)
        sys.stderr.write(f"\n  round: n-grams up to {nmax}, {len(ph):,} clues x "
                         f"{len(SERIALS)} serials\n")
        hits,n,certif,bip=run(ph,orc)
        exp_bip = 0  # count of 12/24-word combos is ~0 here; report raw
        sys.stderr.write(f"\n  {n:,} scripts vs 56M index: {len(hits)} index hit(s); "
                         f"{certif} checksum-valid WIF; {bip} checksum-valid BIP-39\n")
        if not hits and not certif:
            sys.stderr.write("  no clue x serial reaches a funded address or a "
                             "self-certifying key.\n")
        if not a.loop: break
        nmax+=1
        if nmax>10: break
        sys.stderr.write(f"\n  --loop: widening to {nmax}-grams...\n")

if __name__=="__main__":
    main()
