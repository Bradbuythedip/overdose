#!/usr/bin/env python3
"""Massively expanded candidate generator for the Keiser Overdose puzzle.

Pulls from:
  - All article body sentences (transcribed manually from the JPEGs)
  - Highlighted phrases (orange and yellow) in order
  - Bold/italic emphasized words
  - All n-grams (1..6 words) over the highlighted corpus
  - Case variants per candidate (verbatim / lower / upper / titlecase / stripped)
  - First-letter acrostics per page and across the article
  - Article title and meta phrases
  - Common Keiser memes + numeric tokens (pill counts, X counts, page nums)
  - Concatenations with different separators

Writes /home/user/overdose/solver/candidates2.txt (deduped).
"""
import os, re, itertools

# === Article highlighted phrases (orange / yellow), in reading order ===
HL = {
    75: [
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
    ],
    76: [
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
    ],
    77: [
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
    ],
    78: [
        "The numbers don't lie.",
        "gargantuanly wasteful",
        "money printing",
        "wars to keep it going",
        "America left $85 BILLION worth of hate toys in Afghanistan,",
        "$2 trillion fiat cuck-bucks.",
        "the game-theorized Bitcoin protocol,",
    ],
    79: [
        "war and violence economy",
        "infinitely more efficient to transact and store wealth in than fiat, shitcoins or gold",
        "That's right, Bitcoin will take all the energy",
        "Everyone will live their own experience in the rabbit hole. We are getting our souls back and our minds.",
    ],
}

# Bold/italic non-highlighted phrases
BOLD = [
    "They discount stuff in advance.",
    "global unconscious",
    "collective panic",
    "central nervous system of the global economy",
    "the black hole of the Cosmic Now",
    "Maximalist",
    "shameless opportunists",
    "noncoiners",
    "shitcoiners",
    "Toxic Bitcoin Maximalists",
    "Vitalik Buterin",
    "Peter Schiff",
    "Roger Ver",
    "the Block Size War of 2017",
    "Peter McCormack",
    "useless Royals",
    "Mike Novogratz",
    "Michael Saylor",
    "Nic Carter",
    "Marty Bent",
    "Elvis Costello",
    "John and Yoko",
    "Bitcoin rabbit hole",
    "Bitcoin Magazine",
    "El Salvador",
    "Jack Mallers",
    "Strike",
    "$1 billion",
    "20,000 new sign-ups",
    "100,000",
    "42%",
    "51%",
    "$85 BILLION",
    "$2 trillion",
    "Cosmic Now",
    "Manhattan",
    "Afghanistan",
    "Amsterdam",
    "Genesis Block",
    "1969 bed-in",
    "Stacy",
    "BITCOIN FIXES ALL THIS",
    "BITCOIN IS TOXIC AF",
]

# Body sentences (a sample of full sentences from each page)
SENTENCES = [
    # Page 75
    "Here's the bitter truth. Bitcoin was not a reaction to the Global Financial Crisis of 2008. It caused it.",
    "The markets sensed Bitcoin was coming and started to crash.",
    "Markets are like that. They discount stuff in advance.",
    "Look, toxicity is Layer 1 of the protocol.",
    "It's Layer 1 for every great thing that's ever been invented or discovered.",
    "Go Bitcoin Toxic Maximalist, the Layer 1 of the whole Satoshi experience.",
    # Page 76
    "Get some toxicity. Get some bitcoin. Open your heart to Bitcoin.",
    "It's the freaking UTXO ghetto up in here, y'all.",
    "Have you seen the president of El Salvador trolling the International Monetary Fund (IMF) on Twitter?",
    "Maybe because he's a shitcoiner at heart.",
    # Page 77
    "Meanwhile, back in El Salvador, 42% of the country is now hyperbitcoinized.",
    "Jack Mallers' Strike app has gone from 20,000 new sign-ups a day to a mind-bending 100,000.",
    "Has anyone heard from Roger Ver lately?",
    "London is a scammer paradise. Full Stop.",
    "It's a guaranteed, mathematical certainty.",
    "Bitcoin was designed to be a 51% attack on the world's energy supply.",
    # Page 78
    "The economy of love is infinitely more efficient than hate and war.",
    "The numbers don't lie.",
    "BITCOIN FIXES ALL THIS by replacing oil-dripping, corpse-ridden, poppy-harvesting fiat money with perfect bitcoin.",
    "The warmongers will start mining bitcoin for sure.",
    "It's a fact baked into the game-theorized Bitcoin protocol, observable by anyone choosing to see it, right there in the Genesis Block.",
    # Page 79
    "To wrap this up, as we move from a war and violence economy to a peace and love economy, the efficiencies of love",
    "Bitcoin will take all the energy.",
    "Everyone will live their own experience in the rabbit hole.",
    "We are getting our souls back and our minds.",
    "Yes, for some, the Bitcoin rabbit hole ends up in John and Yoko's hotel room in Amsterdam during their 1969 bed-in.",
    "Stacy and I have been living in here for 10 years.",
    "We've seen some shit. Happy to share it all with you - the agony and ecstasy - as Bitcoin conquers fear and hate and replaces it with peace and love.",
]

TITLES = [
    "OVERDOSE",
    "Overdose",
    "overdose",
    "$OVERDOSE",
    "OVERDOSE with Max Keiser",
    "Overdose with Max Keiser",
    "BITCOIN IS TOXIC AF",
    "Bitcoin is Toxic AF",
    "bitcoin is toxic af",
    "Max Keiser",
    "MAX KEISER",
    "max keiser",
    "Maxbitcoin",
    "Bitcoin Magazine El Salvador",
    "The Orange Party Issue",
    "Mr. President",
    "Who is The Banana Republic Now, Biatch?",
    "Who is the banana republic now biatch",
]

KEISER_MEMES = [
    "Buy bitcoin", "BUY BITCOIN", "buy bitcoin",
    "Stack sats", "STACK SATS", "stack sats",
    "fix the money fix the world", "Fix the money fix the world",
    "Toxic Maximalist", "Bitcoin Toxic Maximalist",
    "I am Satoshi", "We are all Satoshi",
    "Satoshi Nakamoto",
    "21 million", "twenty one million",
    "HODL", "hodl",
    "to the moon", "To the moon", "TO THE MOON",
    "Bitcoin fixes this", "BITCOIN FIXES THIS",
    "Wen moon", "WAGMI", "NGMI",
    "Number go up", "number go up",
    "Have fun staying poor",
    "Few understand",
    "Get rekt",
    "Genesis Block", "Block 0",
    "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks",
    "Run bitcoin", "Running bitcoin",
    "Keiser Report",
    "Heisenberg",
    "Stacy Herbert",
    "OrangePillApp",
    "El Zonte",
    "Bitcoin Beach",
    "Nayib Bukele",
    "President Bukele",
    "Bitcoin City",
    "Volcano Energy",
    "Volcano Bond",
    "Chivo wallet",
]

GRAFFITI = [
    "FUCK ALL", "FUCKALL", "fuck all", "fuckall", "Fuck All",
    "shit", "SHIT", "Shit",
    "XX", "XXX", "X", "x",
    "B", "₿", "BTC", "btc",
]

WORD_RE = re.compile(r"[A-Za-z0-9']+")

def words(text):
    return WORD_RE.findall(text)

def ngrams(toks, n):
    return [' '.join(toks[i:i+n]) for i in range(len(toks)-n+1)]

def case_variants(s):
    """Return common case variants for a candidate string."""
    yield s
    yield s.lower()
    yield s.upper()
    yield s.title()
    # capitalize only first letter
    if s:
        yield s[0].upper()+s[1:].lower()
    # strip outer punctuation
    s2 = s.strip(" .,;:!?'\"()-")
    if s2 != s:
        yield s2
        yield s2.lower()
        yield s2.upper()
    # remove ALL punctuation
    s3 = re.sub(r"[^A-Za-z0-9 ]", "", s).strip()
    if s3 and s3 not in (s, s.lower(), s.upper()):
        yield s3
        yield s3.lower()
        yield s3.upper()
    # remove all whitespace
    s4 = re.sub(r"\s+", "", s)
    if s4:
        yield s4
        yield s4.lower()
        yield s4.upper()

def main():
    seen = set()
    cands = []
    def add(s):
        if not s: return
        s = s.replace('—', '-').replace('–','-').replace('’',"'").replace('“','"').replace('”','"')
        if len(s) > 200: return
        if s in seen: return
        seen.add(s); cands.append(s)

    # 1. all highlights verbatim + variants
    all_hl = [p for plist in HL.values() for p in plist]
    for h in all_hl:
        for v in case_variants(h):
            add(v)

    # 2. bold phrases
    for b in BOLD:
        for v in case_variants(b):
            add(v)

    # 3. body sentences
    for s in SENTENCES:
        for v in case_variants(s):
            add(v)

    # 4. titles & memes
    for t in TITLES + KEISER_MEMES + GRAFFITI:
        for v in case_variants(t):
            add(v)

    # 5. n-grams (1..5) over all highlighted text combined
    corpus = ' '.join(all_hl)
    toks = words(corpus)
    for n in (1,2,3,4,5,6):
        for g in ngrams(toks, n):
            add(g); add(g.lower()); add(g.upper()); add(g.title())

    # 6. acrostics per page (first letter of each highlight, several formattings)
    for pg, lst in HL.items():
        acr_first_letters = ''.join(re.sub(r"[^A-Za-z0-9]","", p)[:1] for p in lst)
        for v in case_variants(acr_first_letters):
            add(v)
        # first word of each
        fws = ' '.join(words(p)[0] if words(p) else '' for p in lst)
        for v in case_variants(fws):
            add(v)
        # last word of each
        lws = ' '.join(words(p)[-1] if words(p) else '' for p in lst)
        for v in case_variants(lws):
            add(v)
    # across all pages
    all_acr = ''.join(re.sub(r"[^A-Za-z0-9]","", p)[:1] for p in all_hl)
    for v in case_variants(all_acr): add(v)
    all_fw = ' '.join(words(p)[0] if words(p) else '' for p in all_hl)
    for v in case_variants(all_fw): add(v)

    # 7. per-page concat of highlights
    for pg, lst in HL.items():
        joined_space = ' '.join(lst)
        joined_none = ''.join(lst)
        joined_nl   = '\n'.join(lst)
        for j in (joined_space, joined_none, joined_nl):
            add(j); add(j.lower())

    # 8. all highlights concat
    big_space = ' '.join(all_hl)
    big_none = ''.join(all_hl)
    add(big_space); add(big_space.lower())
    add(big_none); add(big_none.lower())

    # 9. numeric tokens
    for n in ['5','4','6','9','11','20','73','74','75','76','77','78','79',
              '54','45','64','46','9','11','20',
              '20BTC','20btc','20 BTC','BTC20','5BTC','10BTC',
              '5+4','6+4','5+5','6+5','5 4','4 5','6 4','5 5',
              '2008','2009','2017','1971','1969','2021','2022',
              '21000000','21,000,000','21 million','$85billion','85billion',
              '$2trillion','2trillion','$1billion','1billion',
              '51','51%','42','42%']:
        add(n)

    # 10. signature / meta combinations
    for a, b in itertools.product(['Max Keiser','MAX KEISER','max keiser','MK','M.K.'],
                                  ['20 BTC','Overdose','OVERDOSE','Bitcoin','El Salvador','Bukele']):
        add(f"{a} {b}"); add(f"{a}{b}"); add(f"{b} {a}")

    out = os.path.join(os.path.dirname(__file__), 'candidates2.txt')
    with open(out, 'w') as f:
        for c in cands:
            f.write(c + '\n')
    print(f"wrote {len(cands)} candidates to {out}")

if __name__ == '__main__':
    main()
