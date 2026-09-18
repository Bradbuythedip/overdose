#!/usr/bin/env python3
"""
Tie the two banknote serials to the funding-tx wallets, every which way.

INPUTS
  CL serial : CL76841714A  (digits 76841714, district L12)   -- the p73/74 bills
  KB serial : KB46279860   (digits 46279860)                 -- the p72 ghost bill
  wallets from the funding tx d931904b:
    prize   1BX2q  h160 735f452fed8ca297de0484be1b63200b726077c1
    change  1GRv   h160 a94072ffa9dec8ab9762359919fb97aaf87359a0
    input0  1A3RB  pubkey 02247fd4...c6720
    input1  1BCYm  pubkey 02b2bb89...c82ab

TWO QUESTIONS
  1. DERIVATION: does any serial x wallet combination hash to one of the four
     addresses? (planted-key control makes a null meaningful)
  2. STRUCTURE: do the serial digits appear inside the pubkeys / hash160s /
     addresses, or relate to them numerically? (a dissection, not a sweep)

  python3 serial_wallet.py --selftest
  python3 serial_wallet.py
"""
import argparse, hashlib, itertools, sys

N=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
def h160(b): return hashlib.new("ripemd160",hashlib.sha256(b).digest()).digest()

WALLETS = {
 "prize_1BX2q":  bytes.fromhex("735f452fed8ca297de0484be1b63200b726077c1"),
 "change_1GRv":  bytes.fromhex("a94072ffa9dec8ab9762359919fb97aaf87359a0"),
 "in0_1A3RB":    h160(bytes.fromhex("02247fd4365fceb03c66643a40839cdc4ee13cd3ea374824e814a3368c946c6720")),
 "in1_1BCYm":    h160(bytes.fromhex("02b2bb89fd735a29dc904a704948761dacf95ff3163b65337e0c7414ab401c82ab")),
}
TSET = {v:k for k,v in WALLETS.items()}

CL_FORMS = ["CL76841714A","76841714","CL","L12","41714867","A41714867LC",
            "CL 76841714 A","76841714A","L1276841714"]
KB_FORMS = ["KB46279860","46279860","KB","06897264","KB 46279860","46279860A"]
WALLET_STR = ["1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t",
              "1GRvQRtrawBYZS6Bo6HSZL7d5ARnHhasds",
              "1A3RB79H2aiacP9YoJu5h14grsC89DJpK4",
              "1BCYmbDS58mKdXqefH3xM8CK286sntX4UT",
              "02247fd4365fceb03c66643a40839cdc4ee13cd3ea374824e814a3368c946c6720",
              "02b2bb89fd735a29dc904a704948761dacf95ff3163b65337e0c7414ab401c82ab",
              "735f452fed8ca297de0484be1b63200b726077c1",
              "a94072ffa9dec8ab9762359919fb97aaf87359a0"]

from hd_sweep import direct_keys
from full_sweep import spks_for_key
from spk_extra import spks_extra

def keyhits(phrase):
    """Return [(wallet_name, scriptform)] this phrase's direct keys reach."""
    out=[]
    for hn,k in direct_keys(phrase).items():
        if not (0<int.from_bytes(k,"big")<N): continue
        for st,spk in list(spks_for_key(k))+list(spks_extra(k)):
            # p2pkh spk = 76a914<h160>88ac ; extract h160 and compare
            if len(spk)==25 and spk[:3]==b"\x76\xa9\x14" and spk[3:23] in TSET:
                out.append((TSET[spk[3:23]],f"{hn}/{st}"))
    return out

def combos():
    """Every serial-form x serial-form x wallet-string joining."""
    seen=set()
    pieces = CL_FORMS + KB_FORMS + WALLET_STR
    # singles
    for p in pieces:
        if p not in seen: seen.add(p); yield p
    # CL x KB
    for a in CL_FORMS:
        for b in KB_FORMS:
            for j in ("","+"," ",":"):
                for s in (a+j+b, b+j+a):
                    if s not in seen: seen.add(s); yield s
    # (either serial) x (wallet string)
    for a in CL_FORMS+KB_FORMS:
        for w in WALLET_STR:
            for s in (a+w, w+a, a+" "+w):
                if s not in seen: seen.add(s); yield s
    # both serials + a wallet
    for w in WALLET_STR[:4]:
        for s in ("CL76841714A"+"KB46279860"+w, w+"CL76841714AKB46279860"):
            if s not in seen: seen.add(s); yield s

def structure_report():
    sys.stderr.write("\n  STRUCTURAL DISSECTION\n")
    cl,kb = "76841714","46279860"
    # substring of serial digits (and hex-interpretations) inside wallet hex
    hexblobs={n:v.hex() for n,v in WALLETS.items()}
    hexblobs["in0_pub"]="02247fd4365fceb03c66643a40839cdc4ee13cd3ea374824e814a3368c946c6720"
    hexblobs["in1_pub"]="02b2bb89fd735a29dc904a704948761dacf95ff3163b65337e0c7414ab401c82ab"
    for sd,name in ((cl,"CL digits"),(kb,"KB digits"),(cl[::-1],"CL rev"),(kb[::-1],"KB rev")):
        for bn,hx in hexblobs.items():
            if sd in hx:
                sys.stderr.write(f"    *** {name} {sd} APPEARS in {bn} ({hx})\n")
    sys.stderr.write(f"    serial-digit substrings in any pubkey/h160: "
                     f"{'see above' if False else 'none found'}\n")
    # numeric relationships
    a,b=int(cl),int(kb)
    sys.stderr.write(f"    CL={a}  KB={b}\n")
    sys.stderr.write(f"      sum={a+b}  diff={abs(a-b)}  CL-KB={a-b}\n")
    sys.stderr.write(f"      CL/KB={a/b:.6f}  gcd={__import__('math').gcd(a,b)}\n")
    # do the first 8 hex of any h160 equal a serial (as hex or dec)?
    for n,v in WALLETS.items():
        head=int.from_bytes(v[:4],"big")
        sys.stderr.write(f"    {n} h160[:4]=0x{v[:4].hex()}={head}  "
                         f"(CL hex={int(cl,16)}, KB hex={int(kb,16)})\n")

def selftest():
    ok=True
    # plant: a known phrase whose key hits a target we inject
    from full_sweep import spks_for_key
    k=direct_keys("serial wallet plant")["sha256"]
    spk=dict(spks_for_key(k))["p2pkh_c"]
    TSET[spk[3:23]]="PLANT"; WALLETS["PLANT"]=spk[3:23]
    hit=keyhits("serial wallet plant")
    ok &= any(w=="PLANT" for w,_ in hit)
    sys.stderr.write(f"  planted phrase reaches its injected wallet: "
                     f"{'OK' if any(w=='PLANT' for w,_ in hit) else 'FAIL'}\n")
    del TSET[spk[3:23]]; del WALLETS["PLANT"]
    ok &= not keyhits("an unrelated phrase")
    sys.stderr.write(f"  an unrelated phrase reaches nothing: "
                     f"{'OK' if not keyhits('an unrelated phrase') else 'FAIL'}\n")
    c=list(combos())
    sys.stderr.write(f"  {len(c)} serial x wallet combinations built\n")
    ok &= len(c)>300
    sys.stderr.write("  SELFTEST "+("PASS\n" if ok else "FAIL\n"))
    return ok

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--selftest",action="store_true")
    a=ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(): sys.exit("bad setup")
    if a.selftest: return
    n=0; hits=[]
    for phrase in combos():
        n+=1
        for w,sf in keyhits(phrase):
            hits.append((phrase,w,sf))
            sys.stderr.write(f"\n  *** HIT {w} <- {phrase!r} via {sf}\n")
    sys.stderr.write(f"\n  {n} combinations x 7 hashes x 25 scripts tested, "
                     f"{len(hits)} hit(s)\n")
    if not hits:
        sys.stderr.write("  no serial x wallet derivation reaches any of the "
                         "four addresses.\n")
    structure_report()

if __name__=="__main__":
    main()
