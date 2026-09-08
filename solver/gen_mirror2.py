#!/usr/bin/env python3
"""More aggressive mirror-writing focused candidate generator.

Focus: title variants, OVERDOSE/MAX KEISER acrostics, page-flip readings,
upside-down (180° rotation), Atbash + reverse combos."""
import os, re

ALL_HL = [
    "They are the sum of all our neuroses",
    "money printers, banking terrorists, stock traders, central bank arsonists",
    "Layer 1","Fact:",
    "It's Layer 1 for every great thing that's ever been invented or discovered.",
    "Maximalist","Don't fall for shitcoinery.","Keep your dignity.","Layer 1",
    "You wouldn't be digging blindly with your bare hands in the muck of Bitcoin's rabbit hole if this weren't true.",
    "Get some toxicity. Get some bitcoin. Open your heart to Bitcoin",
    "UTXO ghetto up in here",
    "ripped off live central bankers tied to a burning stake",
    "Gotta be this way. Forty years of dumb post-1971 fiat money nonsense",
    "by the rancid catnip of fiat money.","it's a stun gun to the genitals.",
    "buying the dip.","$1 billion","Volcano Bonds","Mike Novogratz","shitcoiner at heart.",
    "hyperbitcoinized","Toxic bitcoin Maximalists within six months.",
    "(Sorry Bhutan, you fell for that snake oil salesmen over at XRP.",
    "Get ready to experience shitcoin hell.","Saketoshi","harass old women and children",
    "shitcoiners, useless Royals,","Full Stop.","51%","fix this by monetizing,",
    "The numbers don't lie.","gargantuanly wasteful","money printing",
    "wars to keep it going","America left $85 BILLION worth of hate toys in Afghanistan,",
    "$2 trillion fiat cuck-bucks.","the game-theorized Bitcoin protocol,",
    "war and violence economy",
    "infinitely more efficient to transact and store wealth in than fiat, shitcoins or gold",
    "That's right, Bitcoin will take all the energy",
    "Everyone will live their own experience in the rabbit hole. We are getting our souls back and our minds.",
]

WORD_RE = re.compile(r"[A-Za-z0-9']+")

def atbash(s):
    out=[]
    for c in s:
        if 'a'<=c<='z': out.append(chr(ord('z')-(ord(c)-ord('a'))))
        elif 'A'<=c<='Z': out.append(chr(ord('Z')-(ord(c)-ord('A'))))
        else: out.append(c)
    return ''.join(out)

def rot(s, n):
    out=[]
    for c in s:
        if 'a'<=c<='z': out.append(chr(ord('a')+((ord(c)-ord('a')+n)%26)))
        elif 'A'<=c<='Z': out.append(chr(ord('A')+((ord(c)-ord('A')+n)%26)))
        else: out.append(c)
    return ''.join(out)

UPSIDE_DOWN = str.maketrans({
    'a':'ɐ','b':'q','c':'ɔ','d':'p','e':'ǝ','f':'ɟ','g':'ƃ','h':'ɥ','i':'ı','j':'ɾ','k':'ʞ','l':'l','m':'ɯ','n':'u','o':'o','p':'d','q':'b','r':'ɹ','s':'s','t':'ʇ','u':'n','v':'ʌ','w':'ʍ','x':'x','y':'ʎ','z':'z',
})

def main():
    seen=set(); cands=[]
    def add(s):
        if not s or len(s)>500 or s in seen: return
        seen.add(s); cands.append(s)

    titles = [
        "OVERDOSE","Overdose","overdose","ESODREVO","esodrevo",
        "OVERDOSE with Max Keiser","ESODREVO htiw xaM resieK",
        "with Max Keiser","resieK xaM htiw",
        "Max Keiser","MAX KEISER","RESIEK XAM","resiek xam",
        "MAX","XAM","KEISER","RESIEK",
        "BITCOIN IS TOXIC AF","FA CIXOT SI NIOCTIB",
        "Bitcoin is Toxic AF","FA cixoT si nioctiB",
        "Who is The Banana Republic Now, Biatch?",
        "?hctaiB ,woN cilbupeR ananaB ehT si ohW",
        "20 BTC","CTB 02","20BTC","CTB02",
        "BTC 20","02 CTB","BTC20","02CTB",
        "I hid a private Bitcoin key encoded in this piece",
        "I hid a private #Bitcoin key encoded in this piece",
        "Nobody's figured it out yet",
        "for 20 BTC","20 BTC for","20BTC for","Mr. President",
        "Mr President","Nayib Bukele","President Nayib Bukele",
        "Stacy and I","Stacy Herbert","Stacy",
        "10 years","ten years","TEN YEARS",
    ]

    # Forward, reversed, atbash, atbash-reversed, rot13, double-rot13, upper, lower, title, no-punct
    for t in titles:
        for v in [t, t.lower(), t.upper(), t.title(),
                  t[::-1], t.lower()[::-1], t.upper()[::-1],
                  atbash(t), atbash(t)[::-1],
                  atbash(t.lower()), atbash(t.lower())[::-1],
                  rot(t, 13), rot(t.lower(), 13),
                  rot(t, 13)[::-1],
                  re.sub(r"\s+","",t), re.sub(r"\s+","",t)[::-1],
                  re.sub(r"\s+","",t.lower()), re.sub(r"\s+","",t.lower())[::-1],
                  re.sub(r"[^A-Za-z0-9]","",t), re.sub(r"[^A-Za-z0-9]","",t)[::-1],
                  re.sub(r"[^A-Za-z0-9]","",t.lower()), re.sub(r"[^A-Za-z0-9]","",t.lower())[::-1],
                  ]:
            add(v)

    # Combined article concat
    big = ' '.join(ALL_HL)
    bigl = big.lower()
    for v in [big, big[::-1], bigl, bigl[::-1],
              atbash(big), atbash(big)[::-1],
              re.sub(r"[^A-Za-z0-9]","",big), re.sub(r"[^A-Za-z0-9]","",big)[::-1],
              re.sub(r"[^A-Za-z0-9]","",big).lower(), re.sub(r"[^A-Za-z0-9]","",big).lower()[::-1],
              # each word reversed
              ' '.join(w[::-1] for w in WORD_RE.findall(big)),
              # all letters reversed (no spaces)
              re.sub(r"[^A-Za-z]","",big)[::-1],
              re.sub(r"[^A-Za-z]","",big.lower())[::-1],
              # words reversed order
              ' '.join(reversed(WORD_RE.findall(big))),
              ' '.join(reversed(WORD_RE.findall(bigl))),
              ]:
        add(v)

    # Page-reversed concat: 79, 78, 77, 76, 75
    # group by page based on the order in ALL_HL
    PG75 = ALL_HL[0:10]; PG76 = ALL_HL[10:21]; PG77 = ALL_HL[21:31]
    PG78 = ALL_HL[31:38]; PG79 = ALL_HL[38:]
    rev_pages = PG79 + PG78 + PG77 + PG76 + PG75
    revtxt = ' '.join(rev_pages)
    for v in [revtxt, revtxt[::-1], revtxt.lower(), revtxt.lower()[::-1]]:
        add(v)

    # Title acrostics
    titlewords = ['OVERDOSE','with','Max','Keiser','BITCOIN','IS','TOXIC','AF']
    for v in [' '.join(titlewords), ' '.join(titlewords)[::-1],
              ' '.join(reversed(titlewords)),
              ''.join(titlewords), ''.join(titlewords)[::-1],
              ''.join(w[0] for w in titlewords),
              ''.join(w[0] for w in titlewords).lower(),
              ''.join(w[0] for w in reversed(titlewords)),
              ]:
        add(v)

    # Stacy "We've seen some shit" + variants
    for s in ["We've seen some shit","weve seen some shit","WEVE SEEN SOME SHIT",
              "Stacy and I have been living in here for 10 years.",
              "stacy and i have been living in here for 10 years",
              "STACY AND I HAVE BEEN LIVING IN HERE FOR 10 YEARS",
              "Happy to share it all with you",
              "the agony and ecstasy",
              "as Bitcoin conquers fear and hate and replaces it with peace and love.",
              "as bitcoin conquers fear and hate and replaces it with peace and love",
              "10","ten","TEN","XX","XXX","fourteen","FOURTEEN","fourteen pills","20 pills",
              "9 pills","nine pills","five pills","FIVE PILLS","Five Pills","FivePills",
              ]:
        add(s); add(s[::-1]); add(re.sub(r"\s+","",s)); add(re.sub(r"\s+","",s)[::-1])

    out = os.path.join(os.path.dirname(__file__), 'candidates_mirror2.txt')
    with open(out,'w') as f:
        for c in cands: f.write(c+'\n')
    print(f"wrote {len(cands)} candidates to {out}")

if __name__ == '__main__':
    main()
