#!/usr/bin/env python3
"""Wave 3: article coinage x Keiser's own famous coinages from outside the
column. The article points at this itself -- 'honey-badgering' is the text
nodding to 'Bitcoin is the honey badger of money'. Neither side alone is new;
the CROSS is."""
import re, sys, itertools

ARTICLE = [
 "UTXO ghetto","Toxic Bitcoin Maximalist","toxicity is Layer 1 of the protocol",
 "the Satoshi experience","monetary defibrillator","stun gun to the genitals",
 "rancid catnip","fiat cuck-bucks","hate toys","honey-badgering",
 "Volcano Bonds","buying the dip","the Cosmic Now","the Bitcoin rabbit hole",
 "central bank arsonists","banking terrorists","shitcoinery","Keep your dignity",
 "BITCOIN FIXES ALL THIS","Get some toxicity","Get some bitcoin",
 "Open your heart to Bitcoin","We've seen some shit","the agony and ecstasy",
 "51% attack","psychotic cats","shitcoin hell","hyperbitcoinized",
 "the economy of love","perfect bitcoin","scammer paradise","cyber sea",
 "these eggheads","gargantuanly wasteful","mEthereum","Sorry Bhutan",
 "money laundering lobotomy","Gotta be this way","OVERDOSE",
]
KEISER = [
 "Bitcoin is the honey badger of money","the honey badger of money",
 "honey badger of money","honey badger","Buy silver crash JP Morgan",
 "Crash JP Morgan Buy Silver","Death to the Fed","We are all Satoshi",
 "Markets Finance Scandal","Keiser Report","Max Keiser","Stacy Herbert",
 "genocidal loan sharks","hyperbitcoinization","Orange Pill",
 "Karmabanque","Hollywood Stock Exchange","Nayib Bukele","El Salvador",
 "Bitcoin fixes this","Stacy and Max","Volcano Energy","Bitcoin Office",
]

def c(s):
    return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",s.replace("’","'"))).strip()

out = set()
for a, b in itertools.product(ARTICLE, KEISER):
    for x, y in ((c(a), c(b)), (c(b), c(a))):
        for form in (lambda p,q: p+" "+q, lambda p,q: p+q,
                     lambda p,q: p+"-"+q, lambda p,q: p+"_"+q,
                     lambda p,q: p+", "+q, lambda p,q: p+" and "+q):
            s = form(x, y)
            out.add(s); out.add(s.lower()); out.add(s.upper())
            out.add(s.lower().replace(" ", ""))
            out.add(s.title().replace(" ", ""))

out = {x for x in out if 0 < len(x) < 400}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    for s in sorted(out):
        f.write(s + "\n")
sys.stderr.write(f"wave3: {len(out):,}\n")
