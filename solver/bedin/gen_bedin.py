#!/usr/bin/env python3
"""Lens: John & Yoko Amsterdam Hilton bed-in 1969, plus the article's other
real-world cultural references. Builds candidates that are NOT literal spans
of the article."""
import itertools, sys, re

OUT = set()
def add(s):
    if s and len(s) < 200:
        OUT.add(s)

# ---------------------------------------------------------------- base tokens
NAMES = [
    "John Lennon", "Yoko Ono", "John and Yoko", "John & Yoko", "John Yoko",
    "Yoko and John", "Lennon", "Ono", "John", "Yoko", "Lennon Ono",
    "John Ono Lennon", "John Winston Lennon", "John Winston Ono Lennon",
    "Yoko Ono Lennon", "JohnandYoko", "Johnandyoko", "The Lennons",
    "Mr and Mrs Lennon", "Lennon and Ono",
]
PLACES = [
    "Amsterdam", "Amsterdam Hilton", "Hilton Amsterdam", "Hilton",
    "Hilton Hotel", "Amsterdam Hilton Hotel", "Hilton Hotel Amsterdam",
    "Apollolaan", "Apollolaan 138", "Netherlands", "Holland", "Room 902",
    "room902", "Suite 702", "Room 702", "902", "702", "Presidential Suite",
    "Suite 902", "Lennon Suite", "John Lennon Suite", "hotel room",
    "hotel room in Amsterdam", "Amsterdam hotel room",
]
EVENT = [
    "bed-in", "bed in", "bedin", "Bed In", "Bed-In", "BedIn", "bed-ins",
    "Bed-In for Peace", "bed in for peace", "bedinforpeace",
    "Bed Peace", "bedpeace", "honeymoon", "Hair Peace", "War Is Over",
    "War is over if you want it", "waroverifyouwantit",
    "Give Peace a Chance", "give peace a chance", "givepeaceachance",
    "All we are saying is give peace a chance", "All we are saying",
    "allwearesaying", "Imagine", "imagine all the people", "Happy Xmas",
    "Plastic Ono Band", "The Ballad of John and Yoko", "Two Virgins",
    "Amsterdam bed-in", "Amsterdam bedin", "1969 bed-in", "1969 bedin",
]
ARTICLE = [
    "rabbit hole", "rabbithole", "the rabbit hole", "Bitcoin rabbit hole",
    "the Bitcoin rabbit hole", "bitcoinrabbithole", "peace and love",
    "peaceandlove", "love and peace", "peace love and understanding",
    "peace, love and understanding", "peaceloveandunderstanding",
    "Overdose", "overdose", "OVERDOSE", "Max Keiser", "maxkeiser",
    "MaxKeiser", "Keiser", "Stacy Herbert", "Stacy and I", "Bitcoin",
    "bitcoin", "BITCOIN", "toxic", "Toxic Maximalist",
    "Bitcoin fixes all this", "bitcoinfixesallthis", "Genesis Block",
    "El Salvador", "elsalvador", "Volcano Bonds", "volcanobonds",
    "51% attack", "51 attack", "95%", "95 percent", "Bitcoin Magazine",
    "the agony and ecstasy", "we have seen some shit",
]
CULTURE = [
    "Elvis Costello", "elviscostello",
    "What's So Funny 'Bout Peace, Love and Understanding",
    "Whats So Funny Bout Peace Love and Understanding",
    "What's So Funny Bout Peace Love and Understanding",
    "whatssofunnyboutpeaceloveandunderstanding",
    "George Clinton", "georgeclinton", "James Brown", "jamesbrown",
    "George Clinton and James Brown", "Parliament Funkadelic",
    "Martin Luther", "martinluther", "95 theses", "95theses",
    "Ninety Five Theses", "Ninety-five Theses", "ninetyfivetheses",
    "The 95 Theses", "Martin Luther 95 theses", "martinluther95theses",
    "Wittenberg", "Wittenberg 1517", "1517", "31 October 1517",
    "Friends", "Friends reruns", "friendsreruns", "Peter Schiff",
    "Nayib Bukele", "Vitalik Buterin", "Jamie Dimon", "Roger Ver",
    "Michael Saylor", "Jack Mallers", "Mike Novogratz", "Marty Bent",
    "Nic Carter", "Peter McCormack", "Faketoshi", "Satoshi",
    "Satoshi Nakamoto",
]

# ------------------------------------------------------------------ numbers
DATES = []
# bed-in ran 25-31 March 1969 (Amsterdam); Montreal bed-in 26 May - 2 Jun 1969
days = [(3, d) for d in range(20, 32)] + [(5, d) for d in range(26, 32)] + [(6, 1), (6, 2)]
for m, d in days:
    Y, y = "1969", "69"
    dd, mm = f"{d:02d}", f"{m:02d}"
    for s in ("", "-", "/", ".", "_"):
        DATES += [f"{dd}{s}{mm}{s}{Y}", f"{mm}{s}{dd}{s}{Y}", f"{Y}{s}{mm}{s}{dd}",
                  f"{dd}{s}{mm}{s}{y}", f"{mm}{s}{dd}{s}{y}", f"{y}{s}{mm}{s}{dd}",
                  f"{d}{s}{m}{s}{Y}", f"{m}{s}{d}{s}{Y}"]
MONTHNAME = {3: "March", 5: "May", 6: "June"}
for m, d in days:
    mn = MONTHNAME[m]
    DATES += [f"{d} {mn} 1969", f"{mn} {d} 1969", f"{mn} {d}, 1969",
              f"{d}{mn}1969", f"{mn}{d}1969", f"{d} {mn} 69",
              f"{d}th {mn} 1969", f"{mn} {d}th 1969"]
NUMS = ["1969", "69", "902", "702", "1969902", "9021969", "1969702", "7021969",
        "138", "95", "1517", "20", "20BTC", "20 BTC", "51", "2008", "2011",
        "2021", "2017", "1971", "42", "12000", "100000", "20000", "85", "2",
        "March 1969", "march1969", "Spring 1969", "1969 Amsterdam",
        "Amsterdam 1969", "Hilton 1969", "1969 Hilton", "Room 902 1969",
        "25 March 1969", "March 25 1969", "19690325", "25031969", "03251969",
        "250369", "690325", "032569", "690525", "26 May 1969"]
DATES += NUMS

# ------------------------------------------------------------ case machinery
def strip_punct(s):
    return re.sub(r"[^A-Za-z0-9 ]", "", s)

def variants(s):
    """Case / spacing / punctuation variants of one string."""
    v = set()
    base = {s, strip_punct(s)}
    for b in list(base):
        b = b.strip()
        if not b:
            continue
        forms = {b, b.lower(), b.upper(), b.title(),
                 b.capitalize(), b.swapcase()}
        for f in list(forms):
            v.add(f)
            v.add(f.replace(" ", ""))
            v.add(f.replace(" ", "-"))
            v.add(f.replace(" ", "_"))
            v.add(f.replace(" ", "."))
            v.add(f.replace(" ", "+"))
        # camel / snake of words
        w = b.split()
        if len(w) > 1:
            v.add("".join(x.capitalize() for x in w))
            v.add(w[0].lower() + "".join(x.capitalize() for x in w[1:]))
            v.add("_".join(x.lower() for x in w))
            v.add("-".join(x.lower() for x in w))
            v.add("".join(x.lower() for x in w))
            v.add("".join(x.upper() for x in w))
            v.add(" ".join(reversed(w)))
            v.add("".join(reversed(w)))
        v.add(b[::-1])
        v.add(b.lower()[::-1])
        v.add(b.replace(" ", "")[::-1])
        v.add(b.replace(" ", "").lower()[::-1])
    return {x for x in v if x}

ALL_TOKENS = NAMES + PLACES + EVENT + ARTICLE + CULTURE
for t in ALL_TOKENS + DATES:
    for x in variants(t):
        add(x)

sys.stderr.write("after singles: %d\n" % len(OUT))

# ------------------------------------------------------------------- pairs
SEPS = ["", " ", "-", "_", ".", ", ", "/"]
CORE_A = ["John Lennon", "Yoko Ono", "John and Yoko", "Lennon", "Yoko",
          "JohnandYoko", "John Ono Lennon", "bed-in", "bedin", "bed in",
          "Amsterdam", "Amsterdam Hilton", "Hilton", "Give Peace a Chance",
          "Bed-In for Peace", "Room 902", "Suite 702", "902", "702",
          "rabbit hole", "peace and love", "Overdose", "Max Keiser",
          "Bitcoin", "War Is Over", "Imagine", "Plastic Ono Band",
          "Elvis Costello", "Martin Luther", "95 theses", "George Clinton",
          "James Brown", "Friends", "hotel room"]
CORE_B = CORE_A + ["1969", "69", "902", "702", "25 March 1969", "19690325",
                   "250369", "25031969", "1517", "95", "20", "138",
                   "Amsterdam 1969", "March 1969", "peace", "love",
                   "peace and love", "Bitcoin", "bitcoin", "toxic",
                   "El Salvador", "Satoshi", "Keiser", "Stacy"]

def case_forms(s):
    return {s, s.lower(), s.upper(), s.title(), s.replace(" ", ""),
            s.replace(" ", "").lower(), s.replace(" ", "").title()}

pairs = 0
for a, b in itertools.product(CORE_A, CORE_B):
    if a == b:
        continue
    for sep in SEPS:
        joined = a + sep + b
        for f in case_forms(joined):
            add(f); pairs += 1
sys.stderr.write("after pairs: %d\n" % len(OUT))

# ------------------------------------------------------------------ triples
T1 = ["John and Yoko", "John Lennon", "Yoko Ono", "JohnandYoko", "Lennon"]
T2 = ["Amsterdam", "Amsterdam Hilton", "Hilton", "Room 902", "Suite 702",
      "bed-in", "bedin", "hotel room"]
T3 = ["1969", "69", "25 March 1969", "19690325", "250369", "bed-in", "bedin",
      "Give Peace a Chance", "peace and love", "rabbit hole", "Overdose",
      "Bitcoin", "902", "702"]
for a, b, c in itertools.product(T1, T2, T3):
    for sep in ["", " ", "-", "_"]:
        j = sep.join([a, b, c])
        for f in case_forms(j):
            add(f)
sys.stderr.write("after triples: %d\n" % len(OUT))

# --------------------------------------------------- famous composed phrases
PHRASES = [
    "All we are saying is give peace a chance",
    "All we are saying, is give peace a chance",
    "Give peace a chance",
    "War is over if you want it",
    "War is over! If you want it",
    "Hair Peace Bed Peace",
    "Stay in bed grow your hair",
    "Stay in Bed, Grow Your Hair",
    "The Bitcoin rabbit hole ends in John and Yoko's hotel room",
    "John and Yoko's hotel room in Amsterdam",
    "John and Yokos hotel room in Amsterdam",
    "room 902 Amsterdam Hilton 1969",
    "suite 702 Amsterdam Hilton 1969",
    "The Amsterdam bed-in for peace 1969",
    "bed-in for peace Amsterdam Hilton room 902",
    "John and Yoko bed-in Amsterdam Hilton 1969",
    "John Lennon Yoko Ono Amsterdam Hilton room 902 1969",
    "peace love and understanding",
    "What's so funny bout peace love and understanding",
    "Elvis Costello was right",
    "monetizing peace love and understanding",
    "the economy of love",
    "Bitcoin fixes all this",
    "toxicity is Layer 1 of the protocol",
    "Bitcoin is toxic AF",
    "ninety five theses",
    "ninety-five theses",
    "Martin Luther nailing the Vatican with ultimatums",
    "95 theses 95 percent",
    "95theses95percent",
    "drops by 95% or more",
    "the whole Satoshi experience",
    "Happy to share it all with you",
    "we are getting our souls back and our minds",
    "Everyone will live their own experience in the rabbit hole",
    "give peace a chance max keiser",
    "20 BTC give peace a chance",
    "bed-in 1969 20 BTC",
]
for p in PHRASES:
    for x in variants(p):
        add(x)
sys.stderr.write("after phrases: %d\n" % len(OUT))

# ----------------------------------------- number/date crossed with the names
NAMEISH = ["John Lennon", "Yoko Ono", "John and Yoko", "JohnandYoko",
           "Lennon", "bed-in", "bedin", "Amsterdam", "Amsterdam Hilton",
           "Hilton", "Give Peace a Chance", "givepeaceachance", "Room",
           "room", "Suite", "suite", "Overdose", "Max Keiser", "rabbit hole"]
for nm in NAMEISH:
    for d in DATES:
        for sep in ["", " ", "-", "_"]:
            for order in (nm + sep + d, d + sep + nm):
                add(order)
                add(order.lower())
                add(order.lower().replace(" ", ""))
sys.stderr.write("after name x date: %d\n" % len(OUT))

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for s in sorted(OUT):
        fh.write(s + "\n")
sys.stderr.write("TOTAL %d -> %s\n" % (len(OUT), sys.argv[1]))
