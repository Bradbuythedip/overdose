#!/usr/bin/env python3
"""Mirror-writing candidate generator for the Keiser Overdose puzzle.

User hint: "the wallet has 20 BTC and the solution probably involves mirror writing".

Transforms applied to every highlighted phrase / bold token / title:
  M1. Reverse string char-by-char
  M2. Reverse word-by-word (preserve word internals)
  M3. Reverse only letters (preserve punctuation/spaces in place)
  M4. Atbash cipher (A<->Z, B<->Y, ... preserving case)
  M5. Vertical-mirror filter: keep only letters that are vertical-mirror-symmetric
       (A,H,I,M,O,T,U,V,W,X,Y), then verbatim or reversed
  M6. Horizontal-mirror substitution where possible (b->d, d->b, p->q, q->p, ...)
  M7. Each word individually reversed in a phrase
  M8. Mirror-pair concatenation: phrase + phrase_reversed
"""
import os, re

ALL_HL = [
    "They are the sum of all our neuroses",
    "money printers, banking terrorists, stock traders, central bank arsonists",
    "Layer 1",
    "Fact:",
    "It's Layer 1 for every great thing that's ever been invented or discovered.",
    "Maximalist",
    "Don't fall for shitcoinery.",
    "Keep your dignity.",
    "Layer 1",
    "You wouldn't be digging blindly with your bare hands in the muck of Bitcoin's rabbit hole if this weren't true.",
    "Get some toxicity. Get some bitcoin. Open your heart to Bitcoin",
    "UTXO ghetto up in here",
    "ripped off live central bankers tied to a burning stake",
    "Gotta be this way. Forty years of dumb post-1971 fiat money nonsense",
    "by the rancid catnip of fiat money.",
    "it's a stun gun to the genitals.",
    "buying the dip.",
    "$1 billion",
    "Volcano Bonds",
    "Mike Novogratz",
    "shitcoiner at heart.",
    "hyperbitcoinized",
    "Toxic bitcoin Maximalists within six months.",
    "(Sorry Bhutan, you fell for that snake oil salesmen over at XRP.",
    "Get ready to experience shitcoin hell.",
    "Saketoshi",
    "harass old women and children",
    "shitcoiners, useless Royals,",
    "Full Stop.",
    "51%",
    "fix this by monetizing,",
    "The numbers don't lie.",
    "gargantuanly wasteful",
    "money printing",
    "wars to keep it going",
    "America left $85 BILLION worth of hate toys in Afghanistan,",
    "$2 trillion fiat cuck-bucks.",
    "the game-theorized Bitcoin protocol,",
    "war and violence economy",
    "infinitely more efficient to transact and store wealth in than fiat, shitcoins or gold",
    "That's right, Bitcoin will take all the energy",
    "Everyone will live their own experience in the rabbit hole. We are getting our souls back and our minds.",
]
SINGLES = [
    "OVERDOSE","Overdose","overdose","$OVERDOSE",
    "Maximalist","Layer 1","Toxic","UTXO","Saketoshi","hyperbitcoinized",
    "Volcano Bonds","Mike Novogratz","Bitcoin","BITCOIN","Satoshi","Nakamoto",
    "Max Keiser","MAX KEISER","max keiser","Keiser","Stacy","Stacy Herbert",
    "BITCOIN IS TOXIC AF","Bitcoin is Toxic AF","Bitcoin Magazine",
    "El Salvador","Nayib Bukele","Bukele","peace and love","love and peace",
    "war and violence","rabbit hole","money printer","fiat money",
    "Full Stop","FUCK ALL","shit","20 BTC","Mr. President",
    "Who is the banana republic now biatch",
    "Banana Republic","banana republic",
]

def atbash(s):
    out = []
    for c in s:
        if 'a' <= c <= 'z': out.append(chr(ord('z')-(ord(c)-ord('a'))))
        elif 'A' <= c <= 'Z': out.append(chr(ord('Z')-(ord(c)-ord('A'))))
        else: out.append(c)
    return ''.join(out)

def reverse_letters_only(s):
    letters = [c for c in s if c.isalpha()]
    rev = letters[::-1]
    out = []
    j = 0
    for c in s:
        if c.isalpha():
            out.append(rev[j]); j += 1
        else:
            out.append(c)
    return ''.join(out)

VERT_SYM = set("AHIMOTUVWXY")
def vert_sym_only(s):
    return ''.join(c for c in s.upper() if c in VERT_SYM)

HMIRROR = str.maketrans({
    'b':'d','d':'b','p':'q','q':'p',
    'B':'D','D':'B','P':'Q','Q':'P',
})

WORD_RE = re.compile(r"[A-Za-z0-9']+")
def words(s): return WORD_RE.findall(s)

def main():
    seen=set(); cands=[]
    def add(s):
        if not s or len(s)>250 or s in seen: return
        seen.add(s); cands.append(s)

    items = list(ALL_HL) + list(SINGLES)
    for s in items:
        # M1
        add(s[::-1]); add(s[::-1].lower()); add(s[::-1].upper())
        # M2
        rw = ' '.join(reversed(words(s)))
        add(rw); add(rw.lower()); add(rw.upper())
        # M3
        rl = reverse_letters_only(s)
        add(rl); add(rl.lower()); add(rl.upper())
        # M4 atbash
        ab = atbash(s); add(ab); add(ab.lower()); add(ab.upper())
        ab_rev = atbash(s[::-1]); add(ab_rev); add(ab_rev.lower())
        # M5 vertical-symmetric letters
        vs = vert_sym_only(s); add(vs); add(vs.lower())
        add(vs[::-1])
        # M6 horizontal mirror sub
        hm = s.translate(HMIRROR); add(hm); add(hm.lower()); add(hm[::-1])
        # M7 each word individually reversed
        ew = ' '.join(w[::-1] for w in words(s)); add(ew); add(ew.lower()); add(ew.upper())
        # M8 phrase + reversed phrase
        add(s + s[::-1]); add(s[::-1] + s); add((s + s[::-1]).lower())
        # punctuation-stripped reversed
        ss = re.sub(r"[^A-Za-z0-9 ]","", s).strip()
        if ss:
            add(ss[::-1]); add(ss[::-1].lower()); add(ss[::-1].upper())
            ss_rw = ' '.join(reversed(ss.split()))
            add(ss_rw); add(ss_rw.lower())

    # Specific iconic mirror candidates
    iconic = [
        "ESODREVO",  # OVERDOSE reversed
        "esodrevo",
        "ESODREVO with Max Keiser",
        "esodrevo with max keiser",
        "RESIEK XAM",  # MAX KEISER reversed
        "resiek xam",
        "resiek xam htiw esodrevo",
        "MAX KEISER reversed",
        "OXTU","oxtu",  # UTXO reversed
        "tsilamixaM","tsilamixam","TSILAMIXAM",
        "imuS","sum reversed",
        "RODAVLAS LE","rodavlas le",  # El Salvador reversed
        "elebukB","ELEBUKB",  # Bukele variants
        "elekuB","ELEKUB",
        "elekub biyan","ELEKUB BIYAN",
        "biyan elekub","BIYAN ELEKUB",
        "rotuB","ROTUB",
        "rotuB biyaN","BIYAN ROTUB",
        # Mirror-friendly puzzle answers
        "WAIT XOX","XOX WAIT",
        "MIRROR","mirror","Mirror",
        "MAX","XAM",
        "Mirror Mirror","MIRROR MIRROR",
        "Mirror writing","mirror writing","MIRROR WRITING",
        "writing mirror","WRITING MIRROR",
        # Reversed title text
        "esodrevO",
        "ESODREVO htiw xaM resieK",
        "esodrevo htiw xam resiek",
        # Article author signature reversed
        "REKEIS XAM",
        "rekeis xam",
        # 20 BTC mirror
        "02 CTB","ctb 02","CTB 02",
        "02BTC","02btc","02 BTC",
        # Page-79 signature variants
        "MAX KEISER 20 BTC",
        "20 BTC MAX KEISER",
        "RESIEK XAM CTB 02",
        "ctb 02 resiek xam",
    ]
    for s in iconic:
        add(s); add(s.lower()); add(s.upper()); add(s.title())

    out = os.path.join(os.path.dirname(__file__), 'candidates_mirror.txt')
    with open(out,'w') as f:
        for c in cands: f.write(c+'\n')
    print(f"wrote {len(cands)} mirror candidates to {out}")

if __name__ == '__main__':
    main()
