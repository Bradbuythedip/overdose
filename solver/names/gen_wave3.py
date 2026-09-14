#!/usr/bin/env python3
"""Wave 3: real-world expansions/aliases of every named entity in the piece."""
import itertools, os, sys
OUT = os.path.dirname(os.path.abspath(__file__))

ALIAS = {
"Max Keiser": ["Max Keiser","Timothy Maxwell Keiser","Maxwell Keiser","Keiser Report",
  "Karmabanque","Hollywood Stock Exchange","HSX","StartCoin","Bitcoin Capital",
  "Max Keiser Report","Orange Juice","maxkeiser","MaxKeiserRT","Keiser Report RT",
  "Max Keiser El Salvador","Max Keiser Bitcoin Advisor","Bitcoin Advisor"],
"Stacy Herbert": ["Stacy Herbert","Stacy Louise Herbert","Stacy","Herbert",
  "Stacy Herbert Keiser","Stacy Keiser","Mrs Keiser","Max and Stacy",
  "Stacy Herbert El Salvador","Bitcoin Office","Oficina Nacional del Bitcoin"],
"Satoshi": ["Satoshi","Satoshi Nakamoto","Nakamoto","satoshi","SatoshiNakamoto",
  "Genesis Block","Chancellor on brink","Hal Finney","Dorian Nakamoto"],
"Faketoshi": ["Faketoshi","Craig Wright","Craig Steven Wright","Craig S Wright",
  "Calvin Ayre","nChain","CoinGeek","Tulip Trading","Craig Wright Faketoshi"],
"Vitalik Buterin": ["Vitalik Buterin","Vitaly Dmitrievich Buterin","Vitalik",
  "Buterin","VitalikButerin","Ethereum Foundation","mEthereum","Ethereum"],
"Jamie Dimon": ["Jamie Dimon","James Dimon","James Lee Dimon","Dimon","JPMorgan",
  "JPMorgan Chase","JP Morgan","Jamie Dimon JPMorgan","Chase"],
"Peter Schiff": ["Peter Schiff","Peter David Schiff","Schiff","Euro Pacific Capital",
  "Euro Pacific","SchiffGold","Peter Schiff Gold","Irwin Schiff"],
"Nayib Bukele": ["Nayib Bukele","Nayib Armando Bukele Ortez","Bukele","President Bukele",
  "Nuevas Ideas","San Salvador","Bitcoin Beach","El Zonte","Chivo","Chivo Wallet",
  "Volcano Bonds","Bitcoin City","Conchagua","Nayib"],
"Mike Novogratz": ["Mike Novogratz","Michael Novogratz","Michael Edward Novogratz",
  "Novogratz","Galaxy Digital","Galaxy Digital Holdings","Fortress","Novo"],
"Jack Mallers": ["Jack Mallers","Mallers","Strike","Zap","Strike App","Jack Mallers Strike",
  "Zap Solutions","Twenty One","Jack Dorsey"],
"Roger Ver": ["Roger Ver","Roger Keith Ver","Ver","Bitcoin Jesus","MemoryDealers",
  "Bitcoin.com","BCH","Bitcoin Cash","Roger Ver Bitcoin Jesus"],
"Peter McCormack": ["Peter McCormack","McCormack","What Bitcoin Did","WhatBitcoinDid",
  "Real Bedford","Defiance","Peter McCormack Bedford"],
"Michael Saylor": ["Michael Saylor","Michael J Saylor","Saylor","MicroStrategy",
  "Strategy","Hope.com","Saylor Academy","Michael Saylor MicroStrategy"],
"Nic Carter": ["Nic Carter","Nicholas Carter","Carter","Castle Island Ventures",
  "Coin Metrics","Castle Island","Nic Carter Castle Island"],
"Marty Bent": ["Marty Bent","Bent","Tales From The Crypt","TFTC","Marty Bent TFTC",
  "Ten31","Rabbit Hole Recap","RHR"],
"Elvis Costello": ["Elvis Costello","Declan Patrick MacManus","Declan MacManus","MacManus",
  "Costello","The Attractions","Nick Lowe","peace love and understanding",
  "What's So Funny Bout Peace Love and Understanding","Peace Love Understanding"],
"George Clinton": ["George Clinton","George Edward Clinton","Clinton","Parliament",
  "Funkadelic","Parliament Funkadelic","P Funk","PFunk","Dr Funkenstein",
  "Mothership Connection","Atomic Dog","One Nation Under a Groove","Star Child"],
"James Brown": ["James Brown","James Joseph Brown","Brown","Godfather of Soul",
  "Mr Dynamite","Soul Brother No 1","The Hardest Working Man in Show Business",
  "Sex Machine","Funky Drummer","JB","The JBs"],
"Martin Luther": ["Martin Luther","Luther","95 Theses","Ninety Five Theses",
  "Wittenberg","Diet of Worms","Here I stand","Reformation","Martin Luther Wittenberg"],
"John": ["John","John Lennon","John Winston Lennon","John Winston Ono Lennon","Lennon",
  "The Beatles","Beatles","Imagine","Give Peace a Chance","Plastic Ono Band"],
"Yoko": ["Yoko","Yoko Ono","Ono","Yoko Ono Lennon","John and Yoko","John Lennon Yoko Ono",
  "Bed In","Bed-In","Bed In for Peace","Amsterdam Hilton","Hilton Amsterdam",
  "Room 902","Hilton Hotel Amsterdam","Amsterdam 1969","bed-in 1969"],
"El Salvador": ["El Salvador","Republic of El Salvador","Republica de El Salvador",
  "San Salvador","SV","SLV","Bitcoin Country","El Salvador Bitcoin"],
"Bhutan": ["Bhutan","Kingdom of Bhutan","Druk Yul","Thimphu","Gross National Happiness"],
"Afghanistan": ["Afghanistan","Kabul","Islamic Republic of Afghanistan","Taliban"],
"London": ["London","City of London","The City","Square Mile","Scammer Paradise",
  "London is a scammer paradise","Canary Wharf","United Kingdom","UK","Britain"],
"Amsterdam": ["Amsterdam","Netherlands","Holland","Amsterdam Hilton","Hilton Amsterdam"],
"Vatican": ["Vatican","The Vatican","Vatican City","Holy See","Rome","Catholic Church",
  "Pope","Papacy","Tetzel","Indulgences"],
"Manhattan Bank": ["Manhattan Bank","Chase Manhattan Bank","Chase Manhattan",
  "Chase","David Rockefeller","Rockefeller","Manhattan"],
"Wall Street": ["Wall Street","WallStreet","Wall St","NYSE","New York Stock Exchange",
  "Lower Manhattan","Broad Street"],
"IMF": ["IMF","International Monetary Fund","Kristalina Georgieva","Bretton Woods",
  "World Bank","SDR","Special Drawing Rights","IMF loan"],
"Strike": ["Strike","Strike App","Zap","Jack Mallers Strike","Lightning Network"],
"Twitter": ["Twitter","X","tweet","Twitter dot com","@maxkeiser","maxkeiser"],
"Bitcoin": ["Bitcoin","bitcoin","BTC","XBT","Bitcoin Magazine","BTC Inc",
  "Bitcoin 2021","Bitcoin Miami","Bitcoin Magazine El Salvador"],
"mEthereum": ["mEthereum","Ethereum","ETH","Ether","proof of stake","mEthereum lab",
  "meth","Ethereum lab"],
"Volcano Bonds": ["Volcano Bonds","Volcano Bond","VolcanoBonds","Volcano Token",
  "Bitcoin Bond","Volcano"],
"Genesis Block": ["Genesis Block","GenesisBlock","Block 0","Block Zero",
  "Chancellor on brink of second bailout for banks","The Times 03 Jan 2009"],
"Block Size War": ["Block Size War","Blocksize War","The Blocksize War","Big Blockers",
  "SegWit","UASF","New York Agreement","Block Size War 2017"],
"Friends": ["Friends","Friends reruns","Central Perk","NBC"],
"Royals": ["Royals","The Royals","Royal Family","House of Windsor","Windsor",
  "Buckingham Palace","Prince Andrew"],
"XRP": ["XRP","Ripple","Ripple Labs","Brad Garlinghouse","Chris Larsen"],
"BCH": ["BCH","Bitcoin Cash","BitcoinCash"],
"BSV": ["BSV","Bitcoin SV","Bitcoin Satoshi Vision","BitcoinSV"],
"ETH": ["ETH","Ethereum","Ether"],
"ADA": ["ADA","Cardano","Charles Hoskinson","IOHK"],
"America": ["America","United States","USA","US","United States of America","Uncle Sam"],
}

def nosp(s): return s.replace(" ","")
o=[]
def A(s):
    if s and len(s)<3500: o.append(s)

allal=[]
for k,v in ALIAS.items():
    allal += v
    for a in v:
        for f in (a, a.lower(), a.upper(), nosp(a), nosp(a).lower(), nosp(a).upper(),
                  a.replace(" ","_"), a.replace(" ","-"), a.replace(" ","."),
                  a[::-1], a.lower()[::-1], nosp(a).lower()[::-1],
                  "".join(w.capitalize() for w in a.split()),
                  "".join(w[0] for w in a.split()),
                  "".join(w[0] for w in a.split()).lower()):
            A(f)
        # alias crossed with key article terms
        for x in ["Overdose","20BTC","20 BTC","toxic","Max Keiser","Stacy","bitcoin"]:
            for p,q in ((a,x),(x,a)):
                for sep in ["", " ", "-", "_"]:
                    j=sep.join([p,q]); A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower())
        # alias paired with its own canonical head
        for sep in ["", " ", "-"]:
            j=sep.join([k,a]); A(j); A(j.lower()); A(nosp(j).lower())
            j=sep.join([a,k]); A(j); A(j.lower()); A(nosp(j).lower())

# cross-alias pairs within each entity cluster
for k,v in ALIAS.items():
    for a,b in itertools.permutations(v,2):
        for sep in ["", " ", "-"]:
            j=sep.join([a,b]); A(j); A(j.lower()); A(nosp(j).lower())

# concatenations of one alias per entity, in printed order
KEYS=list(ALIAS.keys())
for idx in (0,1,2):
    lst=[ALIAS[k][idx] if len(ALIAS[k])>idx else ALIAS[k][0] for k in KEYS]
    for sep in ["", " ", ",", "-", "\n"]:
        for L in (lst, lst[::-1]):
            j=sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn=sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())
    a1="".join(x[0] for x in lst); A(a1); A(a1.lower()); A(a1.upper()); A(a1[::-1])
    a2="".join("".join(w[0] for w in x.split()) for x in lst)
    A(a2); A(a2.lower()); A(a2.upper()); A(a2[::-1])

seen,out=set(),[]
for s in o:
    if s not in seen: seen.add(s); out.append(s)
open(os.path.join(OUT,"names_wave3.txt"),"w",encoding="utf-8").write("\n".join(out)+"\n")
print(f"WAVE3 {len(out)}")
