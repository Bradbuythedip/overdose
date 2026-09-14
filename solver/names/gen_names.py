#!/usr/bin/env python3
"""Lens: every named person, place, brand, organisation in 'Overdose'."""
import itertools, sys, os, re

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- entity inventory, in printed order (first occurrence) ----------------
# (display name, kind, first, last)
ENT = [
 ("Bitcoin","brand","",""),
 ("Wall Street","place","",""),
 ("Jamie Dimon","person","Jamie","Dimon"),
 ("Vitalik Buterin","person","Vitalik","Buterin"),
 ("mEthereum","brand","",""),
 ("Satoshi","person","Satoshi",""),
 ("George Clinton","person","George","Clinton"),
 ("James Brown","person","James","Brown"),
 ("Martin Luther","person","Martin","Luther"),
 ("Vatican","place","",""),
 ("Peter Schiff","person","Peter","Schiff"),
 ("Friends","brand","",""),
 ("Manhattan Bank","org","",""),
 ("El Salvador","place","",""),
 ("International Monetary Fund","org","",""),
 ("IMF","org","",""),
 ("Twitter","brand","",""),
 ("Nayib Bukele","person","Nayib","Bukele"),
 ("Volcano Bonds","brand","",""),
 ("Mike Novogratz","person","Mike","Novogratz"),
 ("Jack Mallers","person","Jack","Mallers"),
 ("Strike","brand","",""),
 ("Bhutan","place","",""),
 ("XRP","brand","",""),
 ("Roger Ver","person","Roger","Ver"),
 ("Block Size War","brand","",""),
 ("Faketoshi","person","Faketoshi",""),
 ("London","place","",""),
 ("Peter McCormack","person","Peter","McCormack"),
 ("BCH","brand","",""),
 ("BSV","brand","",""),
 ("ETH","brand","",""),
 ("ADA","brand","",""),
 ("Elvis Costello","person","Elvis","Costello"),
 ("Michael Saylor","person","Michael","Saylor"),
 ("Nic Carter","person","Nic","Carter"),
 ("Marty Bent","person","Marty","Bent"),
 ("America","place","",""),
 ("Afghanistan","place","",""),
 ("Genesis Block","brand","",""),
 ("John","person","John",""),
 ("Yoko","person","Yoko",""),
 ("Amsterdam","place","",""),
 ("Stacy","person","Stacy",""),
 ("Max Keiser","person","Max","Keiser"),
]

EXTRA = [
 ("Stacy Herbert","person","Stacy","Herbert"),
 ("Keiser Report","brand","",""),
 ("Bitcoin Magazine","brand","",""),
 ("Royals","org","",""),
 ("UK","place","",""),
 ("Ethereum","brand","",""),
 ("Twitter","brand","",""),
]

NAMES   = [e[0] for e in ENT]
PEOPLE  = [e[0] for e in ENT if e[1]=="person"]
PLACES  = [e[0] for e in ENT if e[1]=="place"]
ORGS    = [e[0] for e in ENT if e[1]=="org"]
BRANDS  = [e[0] for e in ENT if e[1]=="brand"]
SURNAME = [e[3] for e in ENT if e[3]]
FIRST   = [e[2] for e in ENT if e[2]]

out = []
def add(s):
    if s is None: return
    s = s.strip("\n")
    if s and len(s) < 3500:
        out.append(s)

# ---- per-string variant expander -----------------------------------------
def casevars(s):
    v = {s, s.lower(), s.upper(), s.title()}
    v.add(s[:1].lower()+s[1:])
    v.add(s[:1].upper()+s[1:])
    return v

SEPS = ["", " ", "_", "-", ".", "+", ",", "|", ":", "/"]

def joinvars(words):
    """all separator joins of a word list, across cases"""
    res = set()
    for sep in SEPS:
        j = sep.join(words)
        res |= casevars(j)
        # camel / pascal
    if len(words) > 1:
        res.add("".join(w.capitalize() for w in words))
        res.add(words[0].lower()+"".join(w.capitalize() for w in words[1:]))
        res.add("".join(w.upper() for w in words))
        res.add("".join(w.lower() for w in words))
    return res

def expand(name, deep=True):
    """full variant set for one entity name"""
    res = set()
    w = name.split()
    res |= joinvars(w)
    if deep:
        # reversed word order
        res |= joinvars(w[::-1])
        # reversed characters
        for s in list(joinvars(w)):
            res.add(s[::-1])
        # initials
        ini = "".join(x[0] for x in w)
        res |= casevars(ini)
        if len(w) > 1:
            res |= casevars(".".join(x[0] for x in w))
            res |= casevars(".".join(x[0] for x in w)+".")
            res |= casevars(" ".join(x[0] for x in w))
        # strip non-alnum
        res.add(re.sub(r"[^A-Za-z0-9]","",name))
        res.add(re.sub(r"[^A-Za-z0-9]","",name).lower())
        res.add(re.sub(r"[^A-Za-z0-9]","",name).upper())
    return res

# =========================================================================
# 1. every entity, every variant
# =========================================================================
ALL_ENT = NAMES + [e[0] for e in EXTRA]
for n in ALL_ENT:
    for s in expand(n):
        add(s)
# surnames only / first names only
for s in SURNAME + FIRST + ["Herbert"]:
    for v in casevars(s):
        add(v); add(v[::-1])

# =========================================================================
# 2. full list in printed order, concatenated (many joins/cases)
# =========================================================================
def listforms(lst, tag=""):
    r = set()
    for sep in ["", " ", ",", ", ", "-", "_", ".", "|", "\n", ";"]:
        j = sep.join(lst)
        r.add(j); r.add(j.lower()); r.add(j.upper())
        jn = sep.join(x.replace(" ","") for x in lst)
        r.add(jn); r.add(jn.lower()); r.add(jn.upper())
    # reversed order
    for sep in ["", " ", ",", "-"]:
        j = sep.join(lst[::-1])
        r.add(j); r.add(j.lower()); r.add(j.upper())
    return r

for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS,
            [e[0] for e in ENT if e[1] in ("person",)],
            SURNAME, FIRST,
            NAMES + ["Stacy Herbert"],
            ["Max Keiser"] + NAMES,
            NAMES + ["Overdose"],
            ["Overdose"] + NAMES):
    for s in listforms(sub):
        add(s)

# =========================================================================
# 3. acrostics: first letters in printed order
# =========================================================================
def acro(lst):
    r = set()
    a1 = "".join(x[0] for x in lst)                 # first letter of each name
    a2 = "".join("".join(w[0] for w in x.split()) for x in lst)  # all initials
    a3 = "".join(x.split()[-1][0] for x in lst)     # last-word initial
    for a in (a1, a2, a3):
        r |= {a, a.lower(), a.upper(), a[::-1], a.lower()[::-1], a.upper()[::-1]}
        r.add(" ".join(a)); r.add(" ".join(a).upper()); r.add(" ".join(a).lower())
        r.add("-".join(a)); r.add(".".join(a))
    return r

for sub in (NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST,
            NAMES[::-1], PEOPLE+PLACES, PEOPLE+PLACES+ORGS+BRANDS):
    for s in acro(sub):
        add(s)

# =========================================================================
# 4. every adjacent pair and triple (printed order)
# =========================================================================
PAIRJOIN = ["", " ", "-", "_", ".", " and ", "+", "|", ",", " & ", "/"]
for i in range(len(NAMES)-1):
    a, b = NAMES[i], NAMES[i+1]
    for sep in PAIRJOIN:
        j = sep.join([a,b])
        add(j); add(j.lower()); add(j.upper())
        jn = sep.join([a.replace(" ",""), b.replace(" ","")])
        add(jn); add(jn.lower()); add(jn.upper())
for i in range(len(NAMES)-2):
    a, b, c = NAMES[i], NAMES[i+1], NAMES[i+2]
    for sep in ["", " ", "-", "_", ".", ","]:
        j = sep.join([a,b,c])
        add(j); add(j.lower()); add(j.upper())
        jn = sep.join([a.replace(" ",""), b.replace(" ",""), c.replace(" ","")])
        add(jn); add(jn.lower()); add(jn.upper())

# =========================================================================
# 5. each name crossed with Overdose / 20 BTC / Max Keiser / toxic
# =========================================================================
CROSS = ["Overdose", "overdose", "OVERDOSE",
         "20 BTC", "20BTC", "20btc", "20 btc", "twenty BTC", "TwentyBTC",
         "Max Keiser", "MaxKeiser", "maxkeiser", "MAX KEISER",
         "toxic", "Toxic", "TOXIC", "toxic af", "Bitcoin is toxic AF"]
XSEP = ["", " ", "-", "_", ".", ":"]
for n in ALL_ENT:
    nn = n.replace(" ","")
    for c in CROSS:
        cc = c.replace(" ","")
        for sep in XSEP:
            for a,b in ((n,c),(c,n),(nn,cc),(cc,nn)):
                j = sep.join([a,b])
                add(j); add(j.lower()); add(j.upper())

# =========================================================================
# 6. Stacy / Keiser heavy coverage
# =========================================================================
SK_CORE = [
 "Stacy and I","Stacy and I have been living in here","Max and Stacy",
 "Stacy and Max","Max & Stacy","Stacy & Max","MaxAndStacy","StacyAndMax",
 "Stacy Herbert","Herbert Stacy","Stacy Louise Herbert","StacyHerbert",
 "Keiser Report","KeiserReport","The Keiser Report","Keiser Report Max Keiser",
 "Max Keiser and Stacy Herbert","Stacy Herbert and Max Keiser",
 "Max Keiser Stacy Herbert","MaxKeiserStacyHerbert",
 "Max Keiser & Stacy Herbert","Keiser and Herbert","Herbert and Keiser",
 "Max","Keiser","Stacy","Herbert","MK","SH","MKSH","SHMK","MaxK","StacyH",
 "Max Keiser Overdose","Overdose Max Keiser","Overdose by Max Keiser",
 "Stacy and I have been living in here for 10years",
 "Stacy and I have been living in here for 10 years",
 "Max and Stacy 20 BTC","Max and Stacy Overdose","Max and Stacy toxic",
 "Stacy Herbert 20 BTC","Stacy Herbert Overdose","Keiser Report 20 BTC",
 "Max Keiser 20 BTC","20 BTC Max Keiser","Max Keiser Stacy",
 "Keiser","keiser","KEISER","reseik","resieK",
 "Max Keiser El Salvador","El Salvador Max Keiser",
 "Stacy Herbert El Salvador","Max and Stacy El Salvador",
 "Max Keiser Bitcoin Magazine","Bitcoin Magazine Max Keiser",
 "MaxKeiserOverdose","maxkeiseroverdose","MAXKEISEROVERDOSE",
]
for s in SK_CORE:
    for v in casevars(s):
        add(v)
    add(s.replace(" ",""))
    add(s.replace(" ","").lower())
    add(s.replace(" ","").upper())
    add(s.replace(" ","_"))
    add(s.replace(" ","-"))
    add(s[::-1])
    add(s.lower()[::-1])
    add(s.replace(" ","").lower()[::-1])

# cross Stacy/Max core with the article's key nouns
SK_SHORT = ["Max and Stacy","Stacy Herbert","Keiser Report","Max Keiser",
            "Stacy","Max and Stacy Keiser"]
SK_X = ["Overdose","20 BTC","toxic","Bitcoin","El Salvador","1969",
        "10 years","10years","rabbit hole","Amsterdam","bed-in","love",
        "peace and love","Genesis Block","Satoshi"]
for a in SK_SHORT:
    for b in SK_X:
        for sep in ["", " ", "-", "_"]:
            for x,y in ((a,b),(b,a)):
                j = sep.join([x,y])
                add(j); add(j.lower()); add(j.upper())
                jn = sep.join([x.replace(" ",""),y.replace(" ","")])
                add(jn); add(jn.lower()); add(jn.upper())

# =========================================================================
# 7. entity pairs that are semantically linked in the piece
# =========================================================================
LINKED = [
 ("George Clinton","James Brown"),("John","Yoko"),("Yoko","John"),
 ("John Lennon","Yoko Ono"),("Nayib Bukele","El Salvador"),
 ("El Salvador","Nayib Bukele"),("Jack Mallers","Strike"),
 ("Strike","Jack Mallers"),("Michael Saylor","Nic Carter"),
 ("Nic Carter","Marty Bent"),("Michael Saylor","Marty Bent"),
 ("Peter Schiff","Bitcoin"),("Vitalik Buterin","mEthereum"),
 ("Roger Ver","Faketoshi"),("Faketoshi","Peter McCormack"),
 ("Peter McCormack","London"),("Martin Luther","Vatican"),
 ("Jamie Dimon","Wall Street"),("Mike Novogratz","Wall Street"),
 ("IMF","El Salvador"),("Bhutan","XRP"),("Amsterdam","1969"),
 ("John and Yoko","Amsterdam"),("Satoshi","Genesis Block"),
 ("Manhattan Bank","IMF"),("Afghanistan","America"),
 ("Elvis Costello","peace love and understanding"),
 ("Max Keiser","Stacy Herbert"),
]
for a,b in LINKED:
    for sep in ["", " ", "-", "_", ".", " and ", " & ", "+"]:
        for x,y in ((a,b),(b,a)):
            j = sep.join([x,y])
            add(j); add(j.lower()); add(j.upper())
            jn = sep.join([x.replace(" ",""),y.replace(" ","")])
            add(jn); add(jn.lower()); add(jn.upper())

# also full-name expansions of the abbreviated ones
for s in ["John Lennon","Yoko Ono","John Lennon and Yoko Ono",
          "JohnLennonYokoOno","Lennon","Ono","Lennon Ono","John and Yoko",
          "JohnAndYoko","johnandyoko","JOHNANDYOKO","Yoko and John",
          "Satoshi Nakamoto","SatoshiNakamoto","satoshinakamoto",
          "Nakamoto","Craig Wright","CraigWright","Craig Steven Wright",
          "Nayib Armando Bukele","Nayib Bukele Ortez",
          "Jamie Dimon JPMorgan","JPMorgan","JP Morgan","JPMorgan Chase",
          "Chase Manhattan Bank","Chase Manhattan","ChaseManhattanBank",
          "Michael J Saylor","MicroStrategy","Marty Bent TFTC",
          "Peter McCormack What Bitcoin Did","Whats Bitcoin Did",
          "Elvis Costello Nick Lowe","George Clinton Parliament Funkadelic",
          "Parliament Funkadelic","James Brown Godfather of Soul",
          "Martin Luther 95 Theses","95 Theses","Ninety Five Theses",
          "Bukele","Novogratz","Mallers","Buterin","Dimon","Schiff",
          "Saylor","Carter","Bent","Ver","McCormack","Costello","Clinton",
          "Brown","Luther","Herbert","Keiser","Wright","Nakamoto"]:
    for v in casevars(s):
        add(v)
    add(s.replace(" ",""))
    add(s.replace(" ","").lower())
    add(s.replace(" ","").upper())
    add(s[::-1]); add(s.lower()[::-1])

# =========================================================================
# 8. ticker / coin cluster (printed order on p77)
# =========================================================================
TICK = ["BCH","BSV","ETH","XRP","ADA"]
for r in range(2, len(TICK)+1):
    for combo in itertools.permutations(TICK, r):
        for sep in ["", " ", ",", "-", "+"]:
            j = sep.join(combo)
            add(j); add(j.lower())
for extra in [TICK+["BTC"], ["BTC"]+TICK, TICK+["12000"],
              TICK+["and 12,000 other shitcoins"]]:
    for sep in ["", " ", ",", "-"]:
        j = sep.join(extra); add(j); add(j.lower()); add(j.upper())

# =========================================================================
# write
# =========================================================================
seen, final = set(), []
for s in out:
    if s not in seen:
        seen.add(s); final.append(s)
p = os.path.join(OUT, "names_all.txt")
with open(p,"w",encoding="utf-8") as f:
    f.write("\n".join(final)+"\n")
print(f"{len(final)} unique candidates -> {p}")
