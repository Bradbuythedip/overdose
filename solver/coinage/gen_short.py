#!/usr/bin/env python3
"""The few hundred most brainwallet-plausible renderings of the signature
coinages -- the set worth paying for the full 5-seed x 72-path HD stack."""
import re, sys, itertools

SIG = [
 "UTXO ghetto", "the UTXO ghetto", "freaking UTXO ghetto",
 "It's the freaking UTXO ghetto up in here y'all",
 "Toxic Bitcoin Maximalist", "Toxic Bitcoin Maximalists",
 "Go Bitcoin Toxic Maximalist", "BITCOIN IS TOXIC AF", "toxic AF",
 "toxicity is Layer 1 of the protocol", "Layer 1 of the protocol",
 "the Layer 1 of the whole Satoshi experience",
 "the whole Satoshi experience", "the Satoshi experience",
 "monetary defibrillator to the treasure chest", "monetary defibrillator",
 "a stun gun to the genitals", "stun gun to the genitals",
 "paper chase Manhattan Bank money laundering lobotomy",
 "money laundering lobotomy",
 "the rancid catnip of fiat money", "rancid catnip",
 "fiat cuck-bucks", "cuck-bucks", "hate toys", "honey-badgering",
 "Volcano Bonds", "collateralized Volcano Bonds", "buying the dip",
 "the black hole of the Cosmic Now", "black hole of the Cosmic Now",
 "the Cosmic Now", "the Bitcoin rabbit hole",
 "central bank arsonists", "banking terrorists", "shitcoinery",
 "Don't fall for shitcoinery", "Keep your dignity",
 "BITCOIN FIXES ALL THIS", "Get some toxicity. Get some bitcoin.",
 "Get some toxicity", "Get some bitcoin", "Open your heart to Bitcoin",
 "We've seen some shit", "the agony and ecstasy",
 "51% attack on the world's energy supply", "51% attack",
 "demonetizes war violence hatred", "mEthereum", "the mEthereum lab",
 "slinging proof of stake at the mEthereum lab",
 "psychotic cats", "shitcoin hell", "Sorry Bhutan", "scammer paradise",
 "London is a scammer paradise Full Stop", "useless Royals",
 "career criminals and banksters", "high-priced London legal hacks",
 "gargantuanly wasteful", "uber class of banksters", "these eggheads",
 "gallons of iced espresso", "the numbers don't lie",
 "the economy of love", "economy of love", "incentivizes love",
 "our joint inner cosmic being", "cyber sea of billions of souls",
 "cyber sea", "explosion of peace", "the same as a smile",
 "the efficiencies of love", "perfect bitcoin", "hyperbitcoinized",
 "the Bitcoin wannabes", "ignominious fate of demonetization",
 "nailing the Vatican with ultimatums", "Gotta be this way",
 "live central bankers tied to a burning stake",
 "Bitcoin fills the gap with love", "The warmongers will start mining bitcoin",
 "game-theorized Bitcoin protocol", "right there in the Genesis Block",
 "Wall Street crony pals", "get rid of those leeches", "a shitcoiner at heart",
 "1969 bed-in", "John and Yoko's hotel room in Amsterdam",
 "Stacy and I have been living in here for 10years",
 "the sum of all our neuroses", "the gullible and unloved",
 "Anything worth hearing is hard to listen to",
 "the muck of Bitcoin's rabbit hole", "a mind-bending 100,000",
 "post-1971 fiat money nonsense", "fiat money Ponzi schemes",
 "oil-dripping corpse-ridden poppy-harvesting fiat money",
 "peace love and understanding", "Elvis Costello was right",
 "MAX KEISER", "OVERDOSE",
]

def forms(s):
    b = re.sub(r"\s+", " ", s.replace("’", "'")).strip()
    np = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", b)).strip()
    hy = re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", "", b)).strip()
    o = set()
    for v in (b, np, hy):
        o |= {v, v.lower(), v.upper(), v.title()}
        o.add(v.lower().replace(" ", ""))
        o.add(v.upper().replace(" ", ""))
        o.add(v.title().replace(" ", ""))
        o.add(v.lower().replace(" ", "-"))
        o.add(v.lower().replace(" ", "_"))
    ws = np.lower().split()
    if len(ws) > 1:
        o.add(" ".join(reversed(ws)))
        o.add("".join(reversed(ws)))
    o.add(np.lower()[::-1])
    return {x for x in o if x}

out = set()
for s in SIG:
    out |= forms(s)

# the headline pairings, in the two forms a person types
HEAD = ["UTXO ghetto", "Toxic Bitcoin Maximalist", "shitcoinery", "hate toys",
        "fiat cuck-bucks", "Volcano Bonds", "honey-badgering", "rancid catnip",
        "the Satoshi experience", "Keep your dignity", "BITCOIN FIXES ALL THIS",
        "monetary defibrillator", "the Cosmic Now", "psychotic cats",
        "51% attack", "Get some toxicity", "Get some bitcoin",
        "We've seen some shit", "the agony and ecstasy", "MAX KEISER"]
for a, b in itertools.permutations(HEAD, 2):
    ca = re.sub(r"[^\w\s]", "", a).strip().lower()
    cb = re.sub(r"[^\w\s]", "", b).strip().lower()
    out.add(ca + " " + cb)
    out.add((ca + cb).replace(" ", ""))

with open(sys.argv[1], "w", encoding="utf-8") as f:
    for s in sorted(out):
        f.write(s + "\n")
sys.stderr.write(f"{len(out):,}\n")
