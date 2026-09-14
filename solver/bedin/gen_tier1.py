#!/usr/bin/env python3
"""Tier-1: the ~highest-prior forms, for the full HD/BIP39 stack."""
import sys
OUT = []
def add(*ss):
    for s in ss:
        if s and s not in OUT:
            OUT.append(s)

CORE = [
 # the sentence's own real-world referent, in natural forms
 "John and Yoko", "John and Yoko's hotel room", "John and Yokos hotel room",
 "John and Yoko's hotel room in Amsterdam",
 "John and Yokos hotel room in Amsterdam",
 "John and Yoko bed-in", "John and Yoko bed in", "John and Yoko 1969",
 "John and Yoko Amsterdam", "John and Yoko Amsterdam 1969",
 "John and Yoko Amsterdam Hilton", "John and Yoko Hilton Amsterdam 1969",
 "John Lennon", "Yoko Ono", "John Lennon and Yoko Ono",
 "John Lennon Yoko Ono", "John Lennon Yoko Ono 1969",
 "John Ono Lennon", "Yoko Ono Lennon", "Lennon Ono",
 "JohnandYoko", "johnandyoko", "JOHNANDYOKO",
 # the event
 "bed-in", "bed in", "bedin", "Bed-In", "BedIn", "BED-IN", "BEDIN",
 "bed-in for peace", "Bed-In for Peace", "bedinforpeace", "BedInForPeace",
 "bed in for peace", "1969 bed-in", "1969 bedin", "bed-in 1969",
 "bedin1969", "bed-in1969", "Amsterdam bed-in", "amsterdambedin",
 "the Amsterdam bed-in", "First bed-in", "bed peace", "bedpeace",
 "hair peace", "hairpeace", "Hair Peace Bed Peace",
 "Stay in bed grow your hair", "stayinbedgrowyourhair",
 # the place
 "Amsterdam", "amsterdam", "AMSTERDAM", "Amsterdam Hilton",
 "amsterdamhilton", "AmsterdamHilton", "Hilton Amsterdam",
 "hiltonamsterdam", "Hilton Hotel Amsterdam", "Amsterdam Hilton Hotel",
 "Hilton", "hilton", "Apollolaan 138", "apollolaan138", "Apollolaan",
 # the rooms
 "room 902", "Room 902", "room902", "Room902", "ROOM902", "902",
 "suite 902", "Suite 902", "suite902",
 "room 702", "Room 702", "room702", "Room702", "ROOM702", "702",
 "suite 702", "Suite 702", "suite702", "Suite702",
 "Amsterdam Hilton room 902", "amsterdamhiltonroom902",
 "Amsterdam Hilton suite 702", "amsterdamhiltonsuite702",
 "Hilton room 902", "hiltonroom902", "room 902 Amsterdam",
 "room902amsterdam", "902 Amsterdam", "902amsterdam",
 "John Lennon Suite", "johnlennonsuite", "Lennon Suite",
 # dates
 "1969", "69", "25 March 1969", "March 25 1969", "March 25, 1969",
 "25031969", "19690325", "03251969", "250369", "690325", "032569",
 "25-03-1969", "1969-03-25", "03/25/1969", "25/03/1969",
 "31 March 1969", "1969-03-31", "19690331", "31031969",
 "26 May 1969", "19690526", "26051969",
 "March 1969", "march1969", "Spring 1969", "1969 Amsterdam",
 "Amsterdam 1969", "amsterdam1969", "1969amsterdam",
 "Hilton 1969", "hilton1969", "1969 Hilton",
 # the song
 "Give Peace a Chance", "give peace a chance", "GIVE PEACE A CHANCE",
 "givepeaceachance", "GivePeaceAChance", "Give Peace A Chance",
 "All we are saying is give peace a chance",
 "all we are saying is give peace a chance",
 "allwearesayingisgivepeaceachance",
 "All we are saying, is give peace a chance",
 "All We Are Saying Is Give Peace A Chance",
 "all we are saying", "allwearesaying",
 "War is over if you want it", "War Is Over If You Want It",
 "warisoverifyouwantit", "War is over! If you want it", "War Is Over",
 "warisover", "Imagine", "imagine", "Plastic Ono Band", "plasticonoband",
 "The Ballad of John and Yoko", "theballadofjohnandyoko",
 "Happy Xmas War Is Over",
]
ARTICLE_CROSS = [
 "the Bitcoin rabbit hole ends up in John and Yoko's hotel room in Amsterdam",
 "the bitcoin rabbit hole ends in john and yokos hotel room in amsterdam",
 "rabbit hole John and Yoko", "rabbitholejohnandyoko",
 "John and Yoko rabbit hole", "johnandyokorabbithole",
 "bed-in rabbit hole", "bedinrabbithole", "rabbit hole bed-in",
 "peace and love John and Yoko", "peaceandlovejohnandyoko",
 "John and Yoko peace and love", "johnandyokopeaceandlove",
 "Overdose bed-in", "overdosebedin", "bed-in Overdose",
 "Overdose John and Yoko", "overdosejohnandyoko",
 "Max Keiser bed-in", "maxkeiserbedin", "Max Keiser John and Yoko",
 "maxkeiserjohnandyoko", "Max Keiser Give Peace a Chance",
 "maxkeisergivepeaceachance", "Keiser 1969", "keiser1969",
 "Bitcoin bed-in", "bitcoinbedin", "bed-in Bitcoin", "bedinbitcoin",
 "Bitcoin 1969", "bitcoin1969", "1969 Bitcoin",
 "Bitcoin Amsterdam 1969", "bitcoinamsterdam1969",
 "Bitcoin rabbit hole Amsterdam 1969", "peace and love 1969",
 "peaceandlove1969", "peace love and understanding",
 "peaceloveandunderstanding", "Peace Love and Understanding",
 "peace, love and understanding",
 "monetizing peace love and understanding",
 "Elvis Costello", "elviscostello", "Elvis Costello was right",
 "elviscostellowasright",
 "What's So Funny 'Bout Peace, Love and Understanding",
 "Whats So Funny Bout Peace Love and Understanding",
 "whatssofunnyboutpeaceloveandunderstanding",
 "(What's So Funny 'Bout) Peace, Love and Understanding",
 "George Clinton", "georgeclinton", "James Brown", "jamesbrown",
 "George Clinton and James Brown", "georgeclintonandjamesbrown",
 "Parliament Funkadelic", "parliamentfunkadelic",
 "Martin Luther", "martinluther", "95 theses", "95theses",
 "Ninety Five Theses", "ninetyfivetheses", "Ninety-Five Theses",
 "ninety-five theses", "The Ninety-five Theses", "95 Theses 1517",
 "95theses1517", "Martin Luther 95 theses", "martinluther95theses",
 "Martin Luther 1517", "martinluther1517", "1517", "Wittenberg",
 "wittenberg", "Wittenberg 1517", "95 percent", "95percent", "95%",
 "drops by 95 percent", "ninety five percent", "95 theses 95 percent",
 "Friends", "friends", "Friends reruns", "friendsreruns",
 "Friends rerun", "psychotic cats Friends reruns",
]
for s in CORE + ARTICLE_CROSS:
    add(s)

# mirror-writing forms (Keiser's own follow-up clue) of the top strings
MIRROR_SRC = CORE[:120] + ARTICLE_CROSS[:40]
for s in MIRROR_SRC:
    add(s[::-1], s.lower()[::-1], s.replace(" ", "").lower()[::-1])

# a few separator variants on the very top strings
TOP = ["John and Yoko", "bed-in", "Amsterdam Hilton", "room 902", "suite 702",
       "Give Peace a Chance", "John Lennon", "Yoko Ono", "1969"]
for a in TOP:
    for b in TOP:
        if a == b:
            continue
        for sep in [" ", "-", ""]:
            add((a + sep + b), (a + sep + b).lower(),
                (a + sep + b).lower().replace(" ", ""))

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for s in OUT:
        fh.write(s + "\n")
sys.stderr.write("tier1 %d -> %s\n" % (len(OUT), sys.argv[1]))
