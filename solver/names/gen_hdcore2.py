#!/usr/bin/env python3
"""HD tier 2: handles, domains, per-page groupings, localities, skeletons,
   and the strongest name x phrase / name x 20BTC crosses. Excludes anything
   already sent through the full HD stack in names_hdcore.txt."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_names import NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, EXTRA
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)

# --- Twitter handles -------------------------------------------------------
HANDLES = ["maxkeiser", "MaxKeiser", "stacyherbert", "StacyHerbert", "nayibbukele",
 "NayibBukele", "novogratz", "jackmallers", "rogerkver", "PeterMcCormack", "saylor",
 "nic__carter", "MartyBent", "VitalikButerin", "PeterSchiff", "jamiedimon",
 "ElvisCostello", "georgeclinton", "yokoono", "johnlennon", "satoshi",
 "bitcoinmagazine", "KeiserReport", "RealMaxKeiser", "MaxKeiserRT", "Dr_CSWright",
 "elsalvador", "presidenciasv"]
for h in HANDLES:
    for f in (h, h.lower(), h.upper(), "@" + h, "@" + h.lower(), h.lower()[::-1]):
        A(f)
for sep in ["", " ", ","]:
    j = sep.join(HANDLES); A(j); A(j.lower())
a = "".join(x[0] for x in HANDLES); A(a); A(a.lower()); A(a.upper()); A(a[::-1])

# --- domains ---------------------------------------------------------------
DOMAINS = ["maxkeiser.com", "keiserreport.com", "bitcoinmagazine.com", "strike.me",
 "saylor.org", "microstrategy.com", "whatbitcoindid.com", "tftc.io", "bitcoin.com",
 "coingeek.com", "ripple.com", "cardano.org", "ethereum.org", "schiffgold.com",
 "jpmorgan.com", "imf.org", "vatican.va", "elsalvador.gob.sv", "bitcoinbeach.com",
 "bitcoin.org", "chivowallet.com"]
for d in DOMAINS:
    A(d); A(d.upper()); A(d.split(".")[0]); A("www." + d); A("https://" + d)

# --- per-page entity groupings --------------------------------------------
P75 = ["Bitcoin", "Wall Street", "Jamie Dimon", "Vitalik Buterin", "mEthereum", "Satoshi"]
P76 = ["George Clinton", "James Brown", "Martin Luther", "Vatican", "Peter Schiff",
       "Friends", "Manhattan Bank", "El Salvador", "International Monetary Fund",
       "IMF", "Twitter", "Nayib Bukele", "Volcano Bonds", "Mike Novogratz", "Wall Street"]
P77 = ["El Salvador", "Jack Mallers", "Strike", "Bhutan", "XRP", "Roger Ver",
       "Block Size War", "Faketoshi", "London", "Peter McCormack", "BCH", "BSV",
       "ETH", "ADA", "Elvis Costello"]
P78 = ["Michael Saylor", "Nic Carter", "Marty Bent", "America", "Afghanistan",
       "Genesis Block"]
P79 = ["John", "Yoko", "Amsterdam", "Stacy", "Max Keiser"]
for lst in (P75, P76, P77, P78, P79, P75 + P76 + P77 + P78 + P79):
    for sep in ["", " ", ",", "-", "_"]:
        for L in (lst, lst[::-1]):
            j = sep.join(L); A(j); A(j.lower()); A(j.upper())
            jn = sep.join(nosp(x) for x in L); A(jn); A(jn.lower()); A(jn.upper())
    for f in (lambda x: x[0], lambda x: x[-1], lambda x: x.split()[-1][0]):
        v = "".join(f(x) for x in lst)
        for g in (v, v.lower(), v.upper(), v[::-1], v.lower()[::-1]): A(g)
    v2 = "".join("".join(w[0] for w in x.split()) for x in lst)
    for g in (v2, v2.lower(), v2.upper(), v2[::-1]): A(g)
acr = "".join("".join(x[0] for x in L) for L in (P75, P76, P77, P78, P79))
for g in (acr, acr.lower(), acr.upper(), acr[::-1]): A(g)

# --- localities / deep cuts ------------------------------------------------
LOCAL = ["Bitcoin Beach", "El Zonte", "Conchagua", "Bitcoin City", "Chivo",
 "Chivo Wallet", "Mike Peterson", "San Salvador", "Nuevas Ideas",
 "Amsterdam Hilton", "Hilton Amsterdam", "Room 702", "Room 902",
 "Bed In for Peace", "Bed-In", "Amsterdam bed-in", "March 1969",
 "Wittenberg", "Diet of Worms", "Johann Tetzel", "Ninety Five Theses", "95 Theses",
 "Chase Manhattan Plaza", "David Rockefeller", "Kristalina Georgieva",
 "Bretton Woods", "Canary Wharf", "Square Mile", "Threadneedle Street",
 "Kabul", "Thimphu", "Druk Yul", "Gross National Happiness", "Parliament Funkadelic",
 "Mothership Connection", "Godfather of Soul", "Declan MacManus", "Bitcoin Jesus"]
for L in LOCAL:
    for f in (L, L.lower(), L.upper(), nosp(L), nosp(L).lower(), nosp(L).upper()):
        A(f)
for sep in ["", " ", ",", "-"]:
    j = sep.join(LOCAL); A(j); A(j.lower()); A(j.upper())
v = "".join(x[0] for x in LOCAL); A(v); A(v.lower()); A(v.upper()); A(v[::-1])

# --- consonant skeletons / vowel strips ------------------------------------
VOW = set("aeiouAEIOU")
for n in NAMES + SURNAME + FIRST + ["Stacy Herbert", "Keiser Report", "Max and Stacy"]:
    for base in (n, nosp(n)):
        for fn in (lambda s: "".join(c for c in s if c not in VOW),
                   lambda s: "".join(c for c in s if c in VOW)):
            v = fn(base)
            if v:
                A(v); A(v.lower()); A(v.upper()); A(v[::-1])
for sub in (NAMES, PEOPLE, SURNAME, FIRST):
    s = "".join(nosp(x) for x in sub)
    for fn in (lambda t: "".join(c for c in t if c not in VOW),
               lambda t: "".join(c for c in t if c in VOW)):
        v = fn(s)
        if v:
            A(v); A(v.lower()); A(v.upper()); A(v[::-1])

# --- top heads x the article's signature phrases ---------------------------
SIG = ["toxic af", "Bitcoin is toxic AF", "Layer 1", "UTXO ghetto", "rabbit hole",
 "hyperbitcoinized", "Volcano Bonds", "buying the dip", "51% attack",
 "Genesis Block", "peace and love", "peace love and understanding",
 "the agony and ecstasy", "Full Stop", "scammer paradise", "Cosmic Now",
 "Toxic Bitcoin Maximalists"]
HEAD = ["Max Keiser", "Stacy Herbert", "Max and Stacy", "Keiser Report", "Satoshi",
 "Nayib Bukele", "El Salvador", "Overdose", "Max", "Stacy", "Keiser"]
for h in HEAD:
    for s in SIG:
        for x, y in ((h, s), (s, h)):
            j = " ".join([x, y])
            A(j); A(j.lower()); A(nosp(j)); A(nosp(j).lower())

# --- top entities x 20 BTC spellings ---------------------------------------
TOP = NAMES + ["Stacy Herbert", "Keiser Report", "Max and Stacy"]
BTC20 = ["20 BTC", "20BTC", "twenty bitcoin", "20 bitcoin", "2000000000 sats"]
for n in TOP:
    for t in BTC20:
        for x, y in ((n, t), (t, n)):
            for sep in ["", " "]:
                j = sep.join([x, y]); A(j); A(j.lower()); A(nosp(j).lower())

# --- exclude what already went through full HD -----------------------------
done = set(l.rstrip("\n") for l in
           open(os.path.join(OUT, "names_hdcore.txt"), encoding="utf-8"))
seen, out = set(), []
for s in o:
    if s and s not in seen and s not in done:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_hdcore2.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"HDCORE2 {len(out)}")
