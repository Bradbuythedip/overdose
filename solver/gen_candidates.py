#!/usr/bin/env python3
"""Generate brainwallet candidate phrases for the Keiser Overdose puzzle.

Pulls from:
  - Each individually-highlighted phrase (verbatim, lowercase, stripped)
  - Common Keiser/Bitcoin meme phrases
  - Article title/header text
  - First-letter acrostics of highlighted phrases per page and across the article
  - Concatenations of highlights per page
  - Pill-count and X-mark numeric hints
Writes one candidate per line to candidates.txt (deduped, preserving order).
"""
import os, hashlib, itertools, re

# Highlighted orange phrases in reading order, per page
PAGE75 = [
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
]
PAGE76 = [
    "Get some toxicity. Get some bitcoin. Open your heart to Bitcoin,",
    "UTXO ghetto up in here,",
    "ripped off live central bankers tied to a burning stake",
    "Gotta be this way. Forty years of dumb post-1971 fiat money nonsense",
    "by the rancid catnip of fiat money.",
    "it's a stun gun to the genitals.",
    "buying the dip.",
    "$1 billion",
    "Volcano Bonds",
    "Mike Novogratz",
    "shitcoiner at heart.",
]
PAGE77 = [
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
]
PAGE78 = [
    "The numbers don't lie.",
    "gargantuanly wasteful",
    "money printing",
    "wars to keep it going",
    "America left $85 BILLION worth of hate toys in Afghanistan,",
    "$2 trillion fiat cuck-bucks.",
    "the game-theorized Bitcoin protocol,",
]
PAGE79 = [
    "war and violence economy",
    "infinitely more efficient to transact and store wealth in than fiat, shitcoins or gold",
    "That's right, Bitcoin will take all the energy",
    "Everyone will live their own experience in the rabbit hole. We are getting our souls back and our minds.",
]

ALL_PAGES = [PAGE75, PAGE76, PAGE77, PAGE78, PAGE79]
ALL_HIGHLIGHTS = [p for page in ALL_PAGES for p in page]

# Keiser / Bitcoin meme phrases & article boilerplate
EXTRA = [
    "OVERDOSE",
    "Overdose",
    "overdose",
    "$OVERDOSE",
    "OVERDOSE with Max Keiser",
    "Overdose with Max Keiser",
    "BITCOIN IS TOXIC AF",
    "Bitcoin is toxic AF",
    "bitcoin is toxic af",
    "Max Keiser",
    "MAX KEISER",
    "max keiser",
    "Maximalist",
    "Toxic Maximalist",
    "Toxic Bitcoin Maximalist",
    "toxic bitcoin maximalist",
    "Stacy Herbert",
    "Nayib Bukele",
    "President Nayib Bukele",
    "El Salvador",
    "Volcano Bonds",
    "Layer 1",
    "Layer 1 for every great thing",
    "Fact: It's Layer 1 for every great thing that's ever been invented or discovered.",
    "stack sats",
    "Stack sats",
    "STACK SATS",
    "hyperbitcoinization",
    "hyperbitcoinized",
    "fix the money fix the world",
    "Fix the money fix the world",
    "Buy bitcoin",
    "buy bitcoin",
    "BUY BITCOIN",
    "Get some toxicity. Get some bitcoin.",
    "Open your heart to Bitcoin",
    "Bitcoin fixes this",
    "Bitcoin fixes everything",
    "we are all satoshi",
    "We Are All Satoshi",
    "I AM SATOSHI",
    "Satoshi Nakamoto",
    "satoshi nakamoto",
    "rabbit hole",
    "the rabbit hole",
    "Bitcoin rabbit hole",
    "Bitcoin's rabbit hole",
    "John and Yoko",
    "Bed-in for Bitcoin",
    "Don't fall for shitcoinery",
    "Keep your dignity",
    "Buying the dip",
    "shitcoiner",
    "Shitcoiner",
    "FUCK ALL",
    "fuck all",
    "Fuck All",
    "shit",
    "SHIT",
    "Full Stop.",
    "Full Stop",
    "full stop",
    "20 BTC",
    "20 bitcoin",
    "Mr. President",
    "Mr President",
    "Bitcoin Magazine",
    "BTC Magazine",
    "El Zonte",
    "Bitcoin Beach",
    "Hyperbitcoinization",
    "love and peace",
    "Peace and love",
    "war and violence",
    "Roger Ver",
    "Saketoshi",
    "buying the dip",
    "$1 billion",
    "21 million",
    "21000000",
    "Genesis Block",
    "Genesis block",
]

def first_letters(phrase):
    # take first letter of each word
    return ''.join(w[0] for w in re.findall(r"[A-Za-z0-9'$%]+", phrase))

def first_word(phrase):
    m = re.match(r"[A-Za-z0-9'$%]+", phrase)
    return m.group(0) if m else ''

def main():
    cands = []
    seen = set()
    def add(s):
        if not s: return
        if s in seen: return
        seen.add(s); cands.append(s)

    # 1. each highlight verbatim, lowercased, stripped of punctuation
    for h in ALL_HIGHLIGHTS:
        add(h)
        add(h.lower())
        add(h.strip(' .,;:!?\'"()'))
        add(h.lower().strip(' .,;:!?\'"()'))
        add(re.sub(r"[^A-Za-z0-9 ]", "", h).strip())
        add(re.sub(r"[^A-Za-z0-9 ]", "", h).strip().lower())

    # 2. extras
    for e in EXTRA:
        add(e)
        add(e.lower())
        add(e.upper())

    # 3. concatenations: per-page join of highlights (verbatim, space-separated)
    for i, page in enumerate(ALL_PAGES, start=75):
        joined = " ".join(page)
        add(joined)
        add(joined.lower())

    # 4. all highlights concatenated, in order
    all_joined = " ".join(ALL_HIGHLIGHTS)
    add(all_joined)
    add(all_joined.lower())

    # 5. acrostics — first letter of each highlighted phrase, per page and all
    for i, page in enumerate(ALL_PAGES, start=75):
        acr = ''.join(first_letters(p)[:1] for p in page)
        add(acr); add(acr.lower()); add(acr.upper())
        # first word of each
        fws = ' '.join(first_word(p) for p in page)
        add(fws); add(fws.lower())
    all_acr = ''.join(first_letters(p)[:1] for p in ALL_HIGHLIGHTS)
    add(all_acr); add(all_acr.lower()); add(all_acr.upper())
    all_fw = ' '.join(first_word(p) for p in ALL_HIGHLIGHTS)
    add(all_fw); add(all_fw.lower())

    # 6. first-letter-of-each-word for each highlight as a single candidate
    for h in ALL_HIGHLIGHTS:
        fl = first_letters(h)
        add(fl); add(fl.lower()); add(fl.upper())

    # 7. pill counts and X mark numeric tokens
    for n in ['5 4', '4 5', '54', '45', '6 4', '64', '46', '9', '11', '20',
              '5+4=9', '20 BTC', 'BTC20', '20BTC']:
        add(n)

    # 8. signature variants
    for s in ['Max Keiser signed', 'MAX KEISER 20 BTC', 'Max Keiser Overdose',
              'OVERDOSE Max Keiser', 'Max Keiser Bitcoin Magazine']:
        add(s); add(s.lower())

    out = os.path.join(os.path.dirname(__file__), 'candidates.txt')
    with open(out, 'w') as f:
        for c in cands:
            f.write(c + '\n')
    print(f"wrote {len(cands)} candidates to {out}")

if __name__ == '__main__':
    main()
