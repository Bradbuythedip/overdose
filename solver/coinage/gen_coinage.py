#!/usr/bin/env python3
"""
LENS: Max Keiser's INVENTED PHRASES -- the coinages only he would write.

Not literal spans of the article (those are swept). This takes the ~230 phrases
Keiser coined in "Overdose" and produces every capitalisation, punctuation-
stripped, space-stripped, hyphen-variant, joined and reversed form, plus
adjacent and cross pairings of two coinages.

  python3 gen_coinage.py --out coinage_all.txt
  python3 gen_coinage.py --tier1 --out coinage_tier1.txt
"""
import argparse, itertools, re, sys

# ---------------------------------------------------------------- coinages
# In article order. Marked T1 = the phrases a showman would actually remember.
COINAGES = [
 # ---- page 75
 ("BITCOIN IS TOXIC AF", 1),
 ("Bitcoin is toxic AF", 1),
 ("toxic AF", 1),
 ("Here's the bitter truth", 0),
 ("The markets sensed Bitcoin was coming", 0),
 ("the central nervous system of the global economy", 0),
 ("the sum of all our neuroses", 1),
 ("the global unconscious of money printers", 0),
 ("money printers", 0),
 ("banking terrorists", 1),
 ("central bank arsonists", 1),
 ("The Bitcoin rabbit hole was opening", 0),
 ("the Bitcoin rabbit hole", 1),
 ("the black hole of the Cosmic Now", 1),
 ("black hole of the Cosmic Now", 1),
 ("the Cosmic Now", 1),
 ("it had fiat markets in its sight", 0),
 ("Nocoiners and shitcoiners", 0),
 ("Toxic Bitcoin Maximalists", 1),
 ("Toxic Bitcoin Maximalist", 1),
 ("toxicity is Layer 1 of the protocol", 1),
 ("Look, toxicity is Layer 1 of the protocol", 0),
 ("Layer 1 of the protocol", 1),
 ("riding Bitcoins coattails", 0),
 ("the Maximalist epithet", 0),
 ("slinging proof of stake at the mEthereum lab", 1),
 ("the mEthereum lab", 1),
 ("mEthereum", 1),
 ("Don't fall for shitcoinery", 1),
 ("shitcoinery", 1),
 ("Keep your dignity", 1),
 ("Go Bitcoin Toxic Maximalist", 1),
 ("the Layer 1 of the whole Satoshi experience", 1),
 ("Layer 1 of the whole Satoshi experience", 1),
 ("the whole Satoshi experience", 1),
 ("the Satoshi experience", 1),
 ("digging blindly with your bare hands", 0),
 ("the muck of Bitcoin's rabbit hole", 1),
 ("Anything worth hearing is hard to listen to", 1),
 ("easy listening for the gullible and unloved", 0),
 ("the gullible and unloved", 1),
 # ---- page 76
 ("Get some toxicity. Get some bitcoin.", 1),
 ("Get some toxicity", 1),
 ("Get some bitcoin", 1),
 ("Open your heart to Bitcoin", 1),
 ("It's the freaking UTXO ghetto up in here, y'all", 1),
 ("the freaking UTXO ghetto", 1),
 ("freaking UTXO ghetto", 1),
 ("UTXO ghetto", 1),
 ("up in here y'all", 0),
 ("funkier than a whole parallel universe", 0),
 ("George Clinton and James Brown clones", 0),
 ("Martin Luther nailing the Vatican with ultimatums", 1),
 ("nailing the Vatican with ultimatums", 1),
 ("the sound of skin being ripped off live central bankers", 1),
 ("live central bankers tied to a burning stake", 1),
 ("tied to a burning stake", 0),
 ("Gotta be this way", 1),
 ("Forty years of dumb post-1971 fiat money nonsense", 1),
 ("dumb post-1971 fiat money nonsense", 1),
 ("post-1971 fiat money nonsense", 1),
 ("fiat money nonsense", 1),
 ("watching Peter Schiff miss buying bitcoin", 0),
 ("honey-badgering", 1),
 ("honey-badgering him to buy some at $1 back in 2011", 1),
 ("controlled now by psychotic cats", 1),
 ("psychotic cats", 1),
 ("plays Friends reruns all day in our heads", 1),
 ("Friends reruns", 0),
 ("Our imaginations and inventiveness have been euthanized", 1),
 ("euthanized by the rancid catnip of fiat money", 1),
 ("the rancid catnip of fiat money", 1),
 ("rancid catnip of fiat money", 1),
 ("rancid catnip", 1),
 ("the paper chase Manhattan Bank money laundering lobotomy", 1),
 ("paper chase Manhattan Bank money laundering lobotomy", 1),
 ("Manhattan Bank money laundering lobotomy", 1),
 ("money laundering lobotomy", 1),
 ("It's a stun gun to the genitals", 1),
 ("a stun gun to the genitals", 1),
 ("stun gun to the genitals", 1),
 ("stun gun", 0),
 ("A monetary defibrillator to the treasure chest", 1),
 ("monetary defibrillator to the treasure chest", 1),
 ("monetary defibrillator", 1),
 ("the treasure chest", 0),
 ("Don't believe me?", 1),
 ("trolling the International Monetary Fund", 0),
 ("buying the dip", 1),
 ("tap his nation's volcanoes", 1),
 ("$1 billion in bitcoin", 0),
 ("collateralized Volcano Bonds", 1),
 ("Volcano Bonds", 1),
 ("get rid of those leeches", 1),
 ("Wall Street crony pals", 1),
 ("a shitcoiner at heart", 1),
 ("he's a shitcoiner at heart", 0),
 # ---- page 77
 ("hyperbitcoinized", 1),
 ("42% of the country is now hyperbitcoinized", 1),
 ("a mind-bending 100,000", 1),
 ("mind-bending", 0),
 ("Toxic Bitcoin Maximalists within six months", 1),
 ("Sorry Bhutan", 1),
 ("snake oil salesmen over at XRP", 1),
 ("Get ready to experience shitcoin hell", 1),
 ("shitcoin hell", 1),
 ("Has anyone heard from Roger Ver lately?", 0),
 ("Big blockers got their heads ripped off", 1),
 ("the Block Size War of 2017", 0),
 ("Faketoshi and his army of high-priced London legal hacks", 1),
 ("his army of high-priced London legal hacks", 1),
 ("high-priced London legal hacks", 1),
 ("London legal hacks", 1),
 ("harass old women and children", 0),
 ("demented shitcoiners", 1),
 ("useless Royals", 1),
 ("career criminals and banksters", 1),
 ("demented shitcoiners, useless Royals, career criminals and banksters", 1),
 ("London is a scammer paradise. Full Stop.", 1),
 ("London is a scammer paradise", 1),
 ("a scammer paradise", 1),
 ("scammer paradise", 1),
 ("Full Stop", 0),
 ("EVERY SINGLE ONE OF THE BITCOIN WANNABES", 1),
 ("THE BITCOIN WANNABES", 1),
 ("the Bitcoin wannabes", 1),
 ("12,000 OTHER SHITCOINS", 1),
 ("THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN", 1),
 ("the ignominious fate of demonetization versus Bitcoin", 1),
 ("ignominious fate of demonetization", 1),
 ("a guaranteed, mathematical certainty", 1),
 ("bitcoin was designed to be a 51% attack on the world's energy supply", 1),
 ("a 51% attack on the world's energy supply", 1),
 ("51% attack on the world's energy supply", 1),
 ("51% attack", 1),
 ("Bitcoin's insatiable conquest of all available energy", 1),
 ("insatiable conquest of all available energy", 1),
 ("starve to death", 0),
 ("it simultaneously demonetizes war, violence, hatred and the state itself", 1),
 ("demonetizes war violence hatred and the state itself", 1),
 ("demonetizes war, violence, hatred", 1),
 ("monetizing, for the first time in human history, peace, love and understanding", 1),
 ("peace, love and understanding", 1),
 ("Elvis Costello was right", 1),
 # ---- page 78
 ("an economy and a money that incentivizes love", 1),
 ("a money that incentivizes love", 1),
 ("incentivizes love", 1),
 ("Love opens up the collective unconscious", 1),
 ("our joint inner cosmic being", 1),
 ("joint inner cosmic being", 1),
 ("The economy of love is infinitely more efficient than hate and war", 1),
 ("the economy of love", 1),
 ("economy of love", 1),
 ("I listen to these eggheads", 1),
 ("these eggheads", 1),
 ("pouring over spreadsheets and gallons of iced espresso", 1),
 ("gallons of iced espresso", 1),
 ("The numbers don't lie", 1),
 ("gargantuanly wasteful", 1),
 ("an uber class of banksters", 1),
 ("uber class of banksters", 1),
 ("fiat money Ponzi schemes", 1),
 ("$85 BILLION worth of hate toys", 1),
 ("worth of hate toys", 0),
 ("hate toys", 1),
 ("$2 trillion fiat cuck-bucks", 1),
 ("fiat cuck-bucks", 1),
 ("cuck-bucks", 1),
 ("BITCOIN FIXES ALL THIS", 1),
 ("Bitcoin fixes all this", 1),
 ("oil-dripping, corpse-ridden, poppy-harvesting fiat money", 1),
 ("oil-dripping corpse-ridden poppy-harvesting", 1),
 ("poppy-harvesting fiat money", 1),
 ("perfect bitcoin", 1),
 ("Remove the war incentive, and you remove the hate incentive", 1),
 ("Remove the war incentive", 1),
 ("Bitcoin fills the gap with love", 1),
 ("our most natural tendency if given a chance", 1),
 ("The warmongers will start mining bitcoin", 1),
 ("the game-theorized Bitcoin protocol", 1),
 ("game-theorized Bitcoin protocol", 1),
 ("right there in the Genesis Block", 1),
 ("the Genesis Block", 0),
 # ---- page 79
 ("a war and violence economy", 1),
 ("a peace and love economy", 1),
 ("the efficiencies of love", 1),
 ("efficiencies of love", 1),
 ("drops by 95% or more", 1),
 ("Bitcoin will take all the energy", 1),
 ("its 51% attack on global energy supply", 1),
 ("51% attack on global energy supply", 1),
 ("our natural tendency toward love and peace", 1),
 ("Poverty disappears because the fear of being poor disappears", 1),
 ("the fear of being poor", 1),
 ("a cyber sea of billions of souls", 1),
 ("cyber sea of billions of souls", 1),
 ("cyber sea", 1),
 ("billions of souls all looking to connect", 1),
 ("this explosion of peace", 1),
 ("explosion of peace", 1),
 ("the cost for this explosion of peace is the same as a smile", 1),
 ("the same as a smile", 1),
 ("virtually nothing", 0),
 ("John and Yoko's hotel room in Amsterdam", 1),
 ("their 1969 bed-in", 1),
 ("1969 bed-in", 1),
 ("Everyone will live their own experience in the rabbit hole", 1),
 ("their own experience in the rabbit hole", 1),
 ("We are getting our souls back and our minds", 1),
 ("getting our souls back", 1),
 ("Stacy and I have been living in here for 10years", 1),
 ("living in here for 10years", 1),
 ("We've seen some shit", 1),
 ("Happy to share it all with you", 1),
 ("the agony and ecstasy", 1),
 ("as Bitcoin conquers fear and hate", 1),
 ("replaces it with peace and love", 1),
 ("MAX KEISER", 1),
 ("OVERDOSE", 1),
 ("Overdose", 1),
 ("Max Keiser Overdose", 1),
]

# 10years / 10 years both ways (the p76 correction cuts both directions)
_extra = []
for s, t in COINAGES:
    if "10years" in s:
        _extra.append((s.replace("10years", "10 years"), t))
COINAGES = COINAGES + _extra

APOS = "’"


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def cores(base):
    """Punctuation / hyphen / apostrophe skeletons of one phrase."""
    b = _norm(base.replace(APOS, "'"))
    out = {b}
    out.add(b.replace("'", ""))                      # apostrophes dropped
    out.add(b.rstrip(".!?,"))                        # terminal punctuation off
    out.add(b.replace("-", " "))                     # hyphens -> spaces
    out.add(b.replace("-", ""))                      # hyphens closed up
    np = _norm(re.sub(r"[^\w\s]", " ", b))           # all punctuation -> space
    out.add(np)
    np2 = _norm(re.sub(r"[^\w\s]", "", b))           # all punctuation deleted
    out.add(np2)
    # $ and % spelled / dropped
    if "$" in b or "%" in b:
        out.add(_norm(b.replace("$", "").replace("%", " percent")))
        out.add(_norm(b.replace("$", "dollars ").replace("%", " percent")))
    # numerals with commas
    if "," in b and re.search(r"\d,\d", b):
        out.add(re.sub(r"(\d),(\d)", r"\1\2", b))
    return {_norm(x) for x in out if _norm(x)}


def cases(s):
    out = {s, s.lower(), s.upper()}
    out.add(s.title())
    out.add(s[:1].upper() + s[1:].lower())
    ws = s.split(" ")
    if len(ws) > 1:
        # camelCase / PascalCase over word-parts
        parts = [re.sub(r"[^\w]", "", w) for w in ws]
        parts = [p for p in parts if p]
        if parts:
            pas = "".join(p[:1].upper() + p[1:].lower() for p in parts)
            out.add(pas)
            out.add(pas[:1].lower() + pas[1:])
    return {x for x in out if x}


def joins(s):
    """Re-join the words of s with the separators a human actually types."""
    ws = [w for w in s.split(" ") if w]
    out = {s}
    if len(ws) > 1:
        for sep in ("", "-", "_", ".", "+", "/", "|", "  "):
            out.add(sep.join(ws))
    return out


def variants(base):
    out = set()
    for c in cores(base):
        for cs in cases(c):
            out |= joins(cs)
    # reversals, over the clean skeletons only
    np = _norm(re.sub(r"[^\w\s]", " ", base.replace(APOS, "'")))
    for form in (np, np.lower(), np.upper()):
        ws = form.split(" ")
        if len(ws) > 1:
            rw = " ".join(reversed(ws))
            out.add(rw)
            out.add(rw.replace(" ", ""))
            out.add("-".join(reversed(ws)))
        out.add(form[::-1])
        out.add(form.replace(" ", "")[::-1])
    return {x for x in out if 0 < len(x) < 400}


PAIR_JOINS = ["", " ", "-", "_", ".", ", ", " and ", "  ", "|", "/", ": ", " + "]


def pair_forms(a, b):
    """Two coinages, adjacent, in the forms a person would actually type."""
    out = set()
    ca = _norm(re.sub(r"[^\w\s]", " ", a.replace(APOS, "'")))
    cb = _norm(re.sub(r"[^\w\s]", " ", b.replace(APOS, "'")))
    for x, y in ((ca, cb), (ca.lower(), cb.lower()), (ca.upper(), cb.upper())):
        for j in PAIR_JOINS:
            out.add(x + j + y)
        out.add((x + " " + y).replace(" ", ""))
        out.add((x + " " + y).replace(" ", "-"))
        out.add((x + " " + y).replace(" ", "_"))
    # raw, unstripped, as printed
    for j in (" ", "", ". ", " - ", ", "):
        out.add(a.strip() + j + b.strip())
    return {x for x in out if 0 < len(x) < 400}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="single",
                    choices=["single", "pairs", "tier1", "tier1pairs"])
    a = ap.parse_args()

    t1 = [s for s, t in COINAGES if t == 1]
    allp = [s for s, _ in COINAGES]
    out = set()

    if a.mode == "single":
        for s in allp:
            out |= variants(s)
    elif a.mode == "tier1":
        for s in t1:
            out |= variants(s)
    elif a.mode == "pairs":
        # adjacent pairs in article reading order, both directions
        for i in range(len(allp) - 1):
            out |= pair_forms(allp[i], allp[i + 1])
            out |= pair_forms(allp[i + 1], allp[i])
        # and skip-one neighbours
        for i in range(len(allp) - 2):
            out |= pair_forms(allp[i], allp[i + 2])
    elif a.mode == "tier1pairs":
        # the signature coinages, every ordered pair
        HEAD = [
            "UTXO ghetto", "Toxic Bitcoin Maximalist", "shitcoinery",
            "hate toys", "fiat cuck-bucks", "Volcano Bonds", "honey-badgering",
            "the Satoshi experience", "rancid catnip", "monetary defibrillator",
            "Keep your dignity", "BITCOIN FIXES ALL THIS", "the Cosmic Now",
            "psychotic cats", "shitcoin hell", "mEthereum", "hyperbitcoinized",
            "money laundering lobotomy", "stun gun to the genitals",
            "banking terrorists", "central bank arsonists", "scammer paradise",
            "cyber sea", "the economy of love", "these eggheads",
            "gargantuanly wasteful", "51% attack", "We've seen some shit",
            "the agony and ecstasy", "Get some toxicity", "Get some bitcoin",
            "Open your heart to Bitcoin", "buying the dip", "useless Royals",
            "the Bitcoin rabbit hole", "Gotta be this way", "Sorry Bhutan",
            "perfect bitcoin", "explosion of peace", "MAX KEISER",
        ]
        for x, y in itertools.permutations(HEAD, 2):
            out |= pair_forms(x, y)
        for x in HEAD:
            out |= variants(x)

    with open(a.out, "w", encoding="utf-8") as f:
        for s in sorted(out):
            f.write(s + "\n")
    sys.stderr.write(f"{a.mode}: {len(out):,} -> {a.out}\n")


if __name__ == "__main__":
    main()
