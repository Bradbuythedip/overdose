#!/usr/bin/env python3
"""
The oddity lens: every non-standard spelling, coinage, typo, grammar slip,
factual error, pun, duplication and self-reference a human eye catches in
"Overdose", expanded aggressively.  These are NOT literal spans of the article
except where the span IS the anomaly.
"""
import itertools, sys

out = []
def add(*xs):
    for x in xs:
        x = x.strip()
        if x and len(x) < 4000:
            out.append(x)

def variants(s):
    """case / separator / order variants of one core string."""
    v = {s, s.lower(), s.upper()}
    v.add(s.title())
    words = s.replace('-', ' ').replace('_', ' ').replace('.', ' ').split()
    if words:
        v.add(''.join(words))
        v.add(''.join(words).lower())
        v.add(''.join(words).upper())
        v.add(' '.join(words))
        v.add(' '.join(words).lower())
        v.add('-'.join(words).lower())
        v.add('_'.join(words).lower())
        v.add('.'.join(words).lower())
        v.add(''.join(w.capitalize() for w in words))
        v.add(words[0].lower() + ''.join(w.capitalize() for w in words[1:]))
        v.add(' '.join(words[::-1]))
        v.add(''.join(words[::-1]).lower())
    v.add(s[::-1])
    v.add(s.lower()[::-1])
    v.add(''.join(c for c in s if c.isalnum()))
    v.add(''.join(c for c in s if c.isalnum()).lower())
    return v

def addv(*xs):
    for x in xs:
        for y in variants(x):
            add(y)

# =====================================================================
# 1. NON-STANDARD SPELLINGS, COINAGES, PORTMANTEAUX  (printed forms)
# =====================================================================
COIN = [
  "mEthereum", "10years", "Bitcoins coattails", "shitcoinery",
  "hyperbitcoinized", "banksters", "cuck-bucks", "Faketoshi",
  "honey-badgering", "gargantuanly", "nocoiners", "Nocoiners",
  "shitcoiners", "shitcoiner", "shitcoin", "Shitcoins", "SHITCOINS",
  "cypherpunks", "UTXO ghetto", "bed-in", "game-theorized",
  "mind-bending", "oil-dripping", "poppy-harvesting", "corpse-ridden",
  "high-priced", "sign-ups", "y'all", "Gotta", "AF", "Full Stop",
  "banking terrorists", "central bank arsonists", "Cosmic Now",
  "paper chase Manhattan Bank", "monetary defibrillator", "treasure chest",
  "stun gun to the genitals", "Volcano Bonds", "Toxic Bitcoin Maximalist",
  "Toxic Bitcoin Maximalists", "hate toys", "fiat cuck-bucks",
  "rancid catnip", "psychotic cats", "uber class", "snake oil salesmen",
  "pouring over spreadsheets", "iced espresso", "orange",
  "the whole Satoshi experience", "Layer 1", "51% attack", "buying the dip",
  "scammer paradise", "Block Size War", "Big blockers", "Royals",
]
for c in COIN:
    addv(c)

# the single most-flagged one, every mangling
for s in ["mEthereum", "methereum", "METHEREUM", "MEthereum", "mETHEREUM",
          "meth Ethereum", "meth ethereum", "methEthereum", "meth+Ethereum",
          "meth", "Ethereum", "m Ethereum", "mE", "Me", "ethereum lab",
          "mEthereum lab", "the mEthereum lab", "proof of stake mEthereum",
          "Vitalik mEthereum", "mEthereumlab"]:
    addv(s)

# =====================================================================
# 2. THE ERROR DELTAS -- printed vs correct, and the characters involved
# =====================================================================
PAIRS = [
  ("Bitcoins", "Bitcoin's"), ("mEthereum", "Ethereum"), ("10years", "10 years"),
  ("salesmen", "salesman"), ("pouring", "poring"), ("gargantuanly", "gargantuan"),
  ("Mallers'", "Mallers's"), ("nocoiners'", "nocoiners"),
  ("shitcoiners'", "shitcoiners"), ("Vatican", "Wittenberg"),
  ("Elvis Costello", "Nick Lowe"), ("Full Stop", "Period"),
]
for a, b in PAIRS:
    addv(a + b); addv(a + " " + b); addv(b + a); addv(a + "->" + b)
# the inserted / deleted characters, in printed order of the anomalies
add("mespace'eu", "m eu", "meu", "MEU", "uem", "mue", "m,e,u", "m e u")
add("'m eau", "'meu", "apostrophe m space e u ly")
for s in ["m", "e", "u", "ly", "'", " "]:
    pass
# extra characters only (m from mEthereum, u from pouring, ly from gargantuanly)
addv("mu", "muly", "mely", "meuly", "mEu", "mEuly")
# missing characters (apostrophe, space, the 'a' of salesman)
addv("a", "'a", "' a")

# =====================================================================
# 3. THE UNCLOSED PARENTHESIS  (p77: "(Sorry Bhutan, ... shitcoin hell." )
# =====================================================================
addv("Sorry Bhutan", "Sorry Bhutan you fell for that snake oil salesmen over at XRP",
     "Get ready to experience shitcoin hell", "shitcoin hell", "Bhutan",
     "Bhutan XRP", "XRP Bhutan", "unclosed", "open paren", "(", "()",
     "Sorry Bhutan)", "(Sorry Bhutan)")

# =====================================================================
# 4. DUPLICATED SENTENCE (p78, printed twice)
# =====================================================================
DUP = "The economy of love is infinitely more efficient than hate and war."
addv(DUP.rstrip('.'))
add(DUP + " " + DUP, (DUP + " ") * 2, DUP * 2,
    (DUP.rstrip('.') + " ") * 2)
addv("economy of love", "efficiencies of love", "the economy of love twice")

# =====================================================================
# 5. FACTUAL ERRORS -> their corrections as key material
# =====================================================================
addv("Wittenberg", "Wittenberg door", "Castle Church Wittenberg",
     "95 theses", "Ninety-five Theses", "95theses", "Martin Luther 95 theses",
     "1517", "31 October 1517", "Martin Luther Wittenberg 1517",
     "Nick Lowe", "Nick Lowe was right", "Whats So Funny Bout Peace Love and Understanding",
     "What's So Funny 'Bout Peace, Love and Understanding",
     "peace love and understanding", "Elvis Costello was wrong",
     "Hilton Amsterdam", "room 902", "902", "Amsterdam Hilton room 902",
     "bed-in for peace", "March 25 1969", "1969 bed in", "Give Peace a Chance",
     "Chase Manhattan Bank", "paper chase", "The Paper Chase",
     "Wall Street and Jamie Dimon", "JPMorgan Chase")

# =====================================================================
# 6. THE SPACING RUNS  10 3 10 3 8 5   (only 6 multi-space runs in the piece)
# =====================================================================
RUNS = [10, 3, 10, 3, 8, 5]
for sep in ['', ' ', '-', ',', '.', '/']:
    add(sep.join(str(x) for x in RUNS))
    add(sep.join(str(x) for x in RUNS[::-1]))
    add(sep.join(str(x - 1) for x in RUNS))
    add(sep.join(str(x - 2) for x in RUNS))
alpha = lambda ns: ''.join(chr(64 + n) for n in ns if 1 <= n <= 26)
addv(alpha(RUNS), alpha([x - 1 for x in RUNS]), alpha([x - 2 for x in RUNS]),
     alpha(RUNS[::-1]))
add("1031038 5", "1031038.5", "10310385", str(sum(RUNS)), str(10*3*10*3*8*5))
# the words the runs separate
addv("Really Yes", "Fact It's Layer 1", "traders central bank arsonists",
     "money Fortunately", "XRP Get ready", "Marty Bent who spend")
addv("Really Yes Fact traders money XRP Marty")

# =====================================================================
# 7. THE PERCENT / NUMBER TRIPLE AND ITS ARITHMETIC
# =====================================================================
PCT = [42, 51, 95]
for sep in ['', ' ', '-', ',', '.', '%', '% ']:
    add(sep.join(str(x) for x in PCT))
    add(sep.join(str(x) for x in PCT[::-1]))
addv("42% 51% 95%", "42 51 95", "95 51 42", "forty two fifty one ninety five")
for a, b, c in itertools.permutations(PCT):
    add(f"{a}{b}{c}", f"{a}-{b}-{c}", f"{a}.{b}.{c}")
add(str(42+51+95), str(95-51), str(51-42), str(100-42), str(100-51), str(100-95),
    str(42*51*95), str(42*51), str(51*95), str(95*42))
# with 20 BTC and 51% twice
addv("20 42 51 51 95", "20BTC 42 51 95", "42 51 95 20")

# all numbers in the piece, in printed order
NUMS = ["2008", "1", "1971", "10", "1", "2011", "42", "20,000", "100,000",
        "six", "2017", "12,000", "51", "85", "2", "95", "1969", "10"]
NUMS_CLEAN = [n.replace(',', '') for n in NUMS]
for sep in ['', ' ', '-', ',']:
    add(sep.join(NUMS_CLEAN))
    add(sep.join(NUMS_CLEAN[::-1]))
add(' '.join(NUMS))

# =====================================================================
# 8. SELF-REFERENCE / MASTHEAD / METADATA
# =====================================================================
META = ["Overdose", "OVERDOSE", "Overdose 20", "Overdose 20 BTC",
        "overdose of 20", "20 BTC Overdose", "an overdose of twenty",
        "Bitcoin Magazine issue 24", "issue 24", "Bitcoin Magazine 24",
        "El Salvador issue", "The El Salvador Issue", "Fall 2021",
        "Bitcoin Magazine Fall 2021", "Max Keiser Overdose",
        "MAX KEISER", "Max Keiser", "Keiser", "Stacy and Max",
        "Stacy Herbert", "Keiser Report", "BITCOIN IS TOXIC AF",
        "Bitcoin Is Toxic AF", "pages 73 79", "73 79", "73-79", "737475767778 79",
        "73 74 75 76 77 78 79", "75 79", "75-79", "p73 p79",
        "73", "79", "24", "20", "2021", "El Salvador"]
for m in META:
    addv(m)
for a in ["Overdose", "OVERDOSE", "overdose"]:
    for b in ["20", "20BTC", "20 BTC", "24", "73", "79", "2021", "El Salvador",
              "ElSalvador", "MaxKeiser", "BitcoinMagazine"]:
        add(a + b, a + " " + b, b + a, b + " " + a, a + "-" + b)

# page numbers combined with issue and year
for combo in itertools.permutations(["24", "2021", "20"]):
    add(''.join(combo), '-'.join(combo), ' '.join(combo))
add("737475767778", "7374757677 7879", "2437379", "24737920")

# =====================================================================
# 9. THE SELF-DESCRIBING BITS -- "Layer 1", "Genesis Block", "Full Stop"
# =====================================================================
addv("Layer 1 of the protocol", "toxicity is Layer 1", "Layer1", "Layer 1 Layer 1 Layer 1",
     "right there in the Genesis Block", "Genesis Block", "the Genesis Block",
     "Full Stop.", "Let me explain why", "this might be the first time you're hearing this",
     "To wrap this up", "Don't believe me?", "Really? Yes.", "Fact:",
     "It's a fact baked into the game-theorized Bitcoin protocol",
     "observable by anyone choosing to see it")

# =====================================================================
# 10. THE ODD PROPER NOUNS AS A SET (names a sweep of prose n-grams splits up)
# =====================================================================
NAMES = ["Jamie Dimon", "Vitalik Buterin", "Peter Schiff", "Nayib Bukele",
         "Mike Novogratz", "Jack Mallers", "Roger Ver", "Peter McCormack",
         "Michael Saylor", "Nic Carter", "Marty Bent", "George Clinton",
         "James Brown", "Martin Luther", "Elvis Costello", "John and Yoko",
         "Faketoshi", "Satoshi", "Bhutan", "El Salvador", "Afghanistan",
         "Amsterdam", "London", "Manhattan", "Wall Street", "Vatican"]
for n in NAMES:
    addv(n)
for sep in ['', ' ', '-', ',']:
    add(sep.join(n.replace(' ', '') for n in NAMES))
    add(sep.join(n.replace(' ', '') for n in NAMES[::-1]))
# initials of the named people, in printed order
inits = ''.join(w[0] for n in NAMES for w in n.split())
addv(inits)
first_inits = ''.join(n[0] for n in NAMES)
addv(first_inits)

# =====================================================================
# 11. THE SHITCOIN TICKER LIST (printed in caps, an obvious key-shaped run)
# =====================================================================
TICK = ["BCH", "BSV", "ETH", "XRP", "ADA"]
for sep in ['', ' ', ',', '-', '/', ', ']:
    add(sep.join(TICK)); add(sep.join(TICK[::-1]))
    add(sep.join(t.lower() for t in TICK))
add("BCHBSVETHXRPADA12000", "BCH BSV ETH XRP ADA 12000 OTHER SHITCOINS")
addv("EVERY SINGLE ONE OF THE BITCOIN WANNABES")
addv("12000 OTHER SHITCOINS", "12,000 other shitcoins")
# first letters of the tickers
addv("BBEXA", "AXEBB", "bbexa")

# =====================================================================
# 12. THE HEADLINE-IN-CAPS BLOCKS (display type, not body prose)
# =====================================================================
CAPS = ["BITCOIN IS TOXIC AF",
        "EVERY SINGLE ONE OF THE BITCOIN WANNABES BCH BSV ETH XRP ADA AND 12000 "
        "OTHER SHITCOINS PLUS FIAT MONEY AND GOLD IS FACING THE IGNOMINIOUS "
        "FATE OF DEMONETIZATION VERSUS BITCOIN",
        "BITCOIN FIXES ALL THIS", "MAX KEISER"]
for c in CAPS:
    addv(c)
add(' '.join(CAPS), ''.join(c.replace(' ', '') for c in CAPS))
# acrostic of the caps words
capwords = ' '.join(CAPS).split()
addv(''.join(w[0] for w in capwords))

# =====================================================================
# 13. ODD ADJACENCIES / PUNS a systematic n-gram sweep would never isolate
# =====================================================================
PUNS = ["paper chase", "Chase Manhattan", "chase Manhattan Bank money laundering lobotomy",
        "stun gun genitals", "defibrillator treasure chest", "treasure chest",
        "UTXO ghetto up in here", "freaking UTXO ghetto",
        "funkier than a whole parallel universe", "George Clinton James Brown clones",
        "skin ripped off live central bankers", "burning stake",
        "honey badgering Peter Schiff", "honey badger",
        "black hole of the Cosmic Now", "Bitcoin rabbit hole",
        "rabbit hole", "digging blindly with your bare hands",
        "muck of Bitcoins rabbit hole", "Friends reruns",
        "psychotic cats play Friends reruns", "rancid catnip of fiat money",
        "monetary defibrillator to the treasure chest",
        "stun gun to the genitals", "Volcano Bonds to pay off the IMF loan",
        "get rid of those leeches", "leeches", "snake oil", "shitcoin hell",
        "London is a scammer paradise", "demented shitcoiners",
        "useless Royals career criminals and banksters",
        "high-priced London legal hacks", "oil-dripping corpse-ridden poppy-harvesting",
        "fiat cuck bucks", "hate toys in Afghanistan", "uber class of banksters",
        "cyber sea of billions of souls", "the cost for this explosion of peace is the same as a smile",
        "virtually nothing", "We've seen some shit", "the agony and ecstasy",
        "Happy to share it all with you"]
for p in PUNS:
    addv(p)

# =====================================================================
# 14. THE OPENING PARADOX AND THE ONE-WORD LINES
# =====================================================================
addv("Bitcoin was not a reaction to the Global Financial Crisis of 2008 It caused it",
     "It caused it", "Really", "Yes", "Really Yes", "Yes Really",
     "Keep your dignity", "Don't fall for shitcoinery", "Full Stop",
     "Nice pleasant words from con men and shitcoiners")

# =====================================================================
# 15. STRUCTURE COUNTS (self-referential metrics)
# =====================================================================
import re
B = '\n'.join(l for l in open('/home/user/overdose/solver/article_transcript.txt',
                              encoding='utf-8').read().split('\n')
              if not l.startswith('#') and not l.startswith('==='))
words = re.findall(r"[A-Za-z][A-Za-z'’-]*", B)
lines = [l for l in B.split('\n') if l.strip()]
paras = [p for p in re.split(r'\n\s*\n', B) if p.strip()]
sents = [s for s in re.split(r'(?<=[.!?])\s+', B) if s.strip()]
counts = [len(words), len(lines), len(paras), len(sents), len(B),
          len([c for c in B if c.isalpha()])]
for sep in ['', ' ', '-', ',']:
    add(sep.join(str(c) for c in counts))
for c in counts:
    add(str(c))
    add(f"Overdose {c}", f"{c} Overdose")

seen = set()
for s in out:
    if s not in seen:
        seen.add(s)
        print(s)
