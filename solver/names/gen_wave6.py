#!/usr/bin/env python3
"""Wave 6: the named entities in their other public identities --
   Twitter handles, domains, ISO codes, email-style forms, locality deep cuts."""
import itertools, os, sys
OUT = os.path.dirname(os.path.abspath(__file__))
def nosp(s): return s.replace(" ", "")
o = []
def A(s):
    if s and len(s) < 3500: o.append(s)

HANDLES = ["maxkeiser", "MaxKeiser", "stacyherbert", "StacyHerbert", "nayibbukele",
 "NayibBukele", "novogratz", "Novogratz", "jackmallers", "JackMallers", "rogerkver",
 "RogerKVer", "PeterMcCormack", "petermccormack", "saylor", "Saylor", "michael_saylor",
 "nic__carter", "niccarter", "MartyBent", "martybent", "VitalikButerin", "vitalikbuterin",
 "PeterSchiff", "peterschiff", "jamiedimon", "JamieDimon", "ElvisCostello",
 "elviscostello", "georgeclinton", "GeorgeClinton", "jamesbrown", "yokoono", "YokoOno",
 "johnlennon", "JohnLennon", "satoshi", "Satoshi", "bitcoinmagazine", "BitcoinMagazine",
 "strike", "Strike", "IMFNews", "imf", "KeiserReport", "keiserreport", "RealMaxKeiser",
 "MaxKeiserRT", "CraigWright", "Dr_CSWright", "coingeek", "bitcoincom", "Ripple",
 "Cardano", "ethereum", "elsalvador", "ElSalvador", "presidenciasv"]
for h in HANDLES:
    for f in (h, h.lower(), h.upper(), "@" + h, "@" + h.lower(), "@" + h.upper(),
              h[::-1], h.lower()[::-1]):
        A(f)
    for x in ["Overdose", "20BTC", "20 BTC", "toxic", "bitcoin", "MaxKeiser"]:
        for a, b in ((h, x), (x, h)):
            for sep in ["", " ", "-", "_"]:
                j = sep.join([a, b]); A(j); A(j.lower()); A(nosp(j).lower())
# all handles concatenated / acrostic
for sep in ["", " ", ",", "-", "\n"]:
    for L in (HANDLES, HANDLES[::-1]):
        j = sep.join(L); A(j); A(j.lower()); A(j.upper())
a = "".join(x[0] for x in HANDLES); A(a); A(a.lower()); A(a.upper()); A(a[::-1])

DOMAINS = ["maxkeiser.com", "keiserreport.com", "bitcoinmagazine.com", "strike.me",
 "zaphq.io", "saylor.org", "microstrategy.com", "hope.com", "whatbitcoindid.com",
 "tftc.io", "ten31.vc", "castleisland.vc", "coinmetrics.io", "bitcoin.com",
 "coingeek.com", "nchain.com", "ripple.com", "cardano.org", "ethereum.org",
 "schiffgold.com", "europac.com", "jpmorgan.com", "imf.org", "vatican.va",
 "elsalvador.gob.sv", "presidencia.gob.sv", "bitcoinbeach.com", "galaxy.com",
 "bitcoin.org", "btcinc.com", "realbedford.com", "chivowallet.com"]
for d in DOMAINS:
    for f in (d, d.lower(), d.upper(), d.split(".")[0], d.split(".")[0].upper(),
              "www." + d, "https://" + d, "http://" + d, d[::-1]):
        A(f)
for sep in ["", " ", ",", "\n"]:
    j = sep.join(DOMAINS); A(j); A(j.lower())

ISO = ["SV", "SLV", "BT", "BTN", "AF", "AFG", "GB", "GBR", "NL", "NLD", "US", "USA",
 "VA", "VAT", "CA", "SVC", "USD", "BTC", "XBT"]
for r in (2, 3, 4):
    for c in itertools.permutations(["SV", "BT", "AF", "GB", "NL", "US", "VA"], r):
        j = "".join(c); A(j); A(j.lower())
for i in ISO:
    A(i); A(i.lower())
    for x in ["MaxKeiser", "Overdose", "20BTC", "bitcoin"]:
        A(i + x); A(x + i); A((i + x).lower()); A((x + i).lower())

EMAILS = ["max.keiser", "stacy.herbert", "m.keiser", "s.herbert", "keiser.max",
 "herbert.stacy", "maxk", "stacyh", "nayib.bukele", "michael.saylor", "nic.carter",
 "marty.bent", "jack.mallers", "roger.ver", "peter.mccormack", "peter.schiff",
 "jamie.dimon", "vitalik.buterin", "mike.novogratz", "elvis.costello",
 "george.clinton", "james.brown", "martin.luther", "john.lennon", "yoko.ono"]
for e in EMAILS:
    for f in (e, e.upper(), e.replace(".", ""), e.replace(".", "_"), e.replace(".", "-"),
              e + "@maxkeiser.com", e + "@bitcoinmagazine.com", e + "@protonmail.com",
              e + "@gmail.com", e[::-1]):
        A(f)

LOCAL = ["Bitcoin Beach", "El Zonte", "Playa El Zonte", "Conchagua",
 "Volcan de Conchagua", "Bitcoin City", "Chivo", "Chivo Wallet", "Mike Peterson",
 "Jaime Garcia", "San Salvador", "La Libertad", "Nuevas Ideas", "Casa Presidencial",
 "Amsterdam Hilton", "Hilton Amsterdam", "Room 702", "Room 902", "Suite 702",
 "Bed In for Peace", "Bed-In", "Amsterdam bed-in", "March 1969", "25 March 1969",
 "Wittenberg", "All Saints Church", "Diet of Worms", "Johann Tetzel",
 "Ninety Five Theses", "95 Theses", "31 October 1517", "Chase Manhattan Plaza",
 "David Rockefeller", "Kristalina Georgieva", "Bretton Woods", "Canary Wharf",
 "Square Mile", "Threadneedle Street", "Old Lady of Threadneedle Street",
 "Bagram", "Kabul", "Thimphu", "Druk Yul", "Gross National Happiness"]
for L in LOCAL:
    for f in (L, L.lower(), L.upper(), nosp(L), nosp(L).lower(), nosp(L).upper(),
              L.replace(" ", "_"), L.replace(" ", "-"), L.lower()[::-1]):
        A(f)
    for x in ["Max Keiser", "Stacy Herbert", "Overdose", "20BTC", "bitcoin"]:
        for a2, b2 in ((L, x), (x, L)):
            for sep in ["", " ", "-"]:
                j = sep.join([a2, b2]); A(j); A(j.lower()); A(nosp(j).lower())
for sep in ["", " ", ",", "-", "\n"]:
    for Lst in (LOCAL, LOCAL[::-1]):
        j = sep.join(Lst); A(j); A(j.lower()); A(j.upper())
        jn = sep.join(nosp(x) for x in Lst); A(jn); A(jn.lower())
a = "".join(x[0] for x in LOCAL); A(a); A(a.lower()); A(a.upper()); A(a[::-1])

seen, out = set(), []
for s in o:
    if s not in seen:
        seen.add(s); out.append(s)
open(os.path.join(OUT, "names_wave6.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"WAVE6 {len(out)}")
