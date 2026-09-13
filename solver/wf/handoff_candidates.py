#!/usr/bin/env python3
"""
High-conviction brainwallet candidates, emitted as addresses for a HISTORICAL
check that this sandbox cannot perform.

THE BLIND SPOT THIS ADDRESSES
Every sweep in this project -- roughly 100 million derived addresses across
three sessions -- asked the same question: "is this address funded NOW?"
(address_map.bin), or "was it rich in April 2023?" (the Pymmdrza dump).

Both are blind to the single most likely fate of a brainwallet prize. Automated
sweeper bots watch the chain and drain any address whose key comes from a
guessable phrase, usually within seconds of it being funded. Every famous
brainwallet is empty for exactly this reason -- the repo already measured it,
8/8 probed came back with zero balance. If Keiser funded a phrase-derived
address in late 2021, the 20 BTC was very likely gone long before anyone
"solved" anything, and Keiser's "nobody's figured it out yet" would still be
true from his point of view.

Under that hypothesis a CORRECT derivation is indistinguishable from a wrong
one using any oracle available here. The distinguishing query is
"did this address EVER receive coins", which needs a full historical chain
index or any block explorer -- both unreachable from this sandbox (every
Bitcoin API host is 403 at CONNECT).

So this script does not try to answer it. It emits the candidates so that
someone with ordinary internet access can, in a couple of minutes.

WHAT IS EMITTED
The canonical 2011-era brainwallet derivation -- sha256(passphrase) as the
private key -- for the phrases a puzzle setter would actually reach for from
this specific article, plus the mirror-writing variants Keiser's own clue
points at. Uncompressed P2PKH is listed first because that was the default in
the brainwallet.org / bitaddress.org era Keiser came up in; compressed is given
too since it is a one-character change in most tools.

Each row is also checked against both oracles we DO have, so the output states
plainly that they are not currently funded -- that is expected, and is not
evidence against them.

  python3 handoff_candidates.py > handoff_candidates.tsv
"""
import hashlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H

# Phrases ranked by what a setter would plausibly choose from THIS piece:
# the display headlines, the signature lines, the clue words Keiser himself
# flagged, and the lines the layout shouts at the reader.
PHRASES = [
    # the clue Keiser explicitly confirmed
    "El Salvador", "el salvador", "EL SALVADOR", "ElSalvador",
    # the column and the headline it ran under
    "OVERDOSE", "Overdose", "overdose",
    "BITCOIN IS TOXIC AF", "Bitcoin Is Toxic AF", "Bitcoin is toxic af",
    # the display lines set in bars / caps, in reading order
    "They are the sum of all our neuroses.",
    "Gotta be this way.",
    "Keep your dignity.",
    "Don't fall for shitcoinery.",
    "Go Bitcoin Toxic Maximalist,",
    "Toxic Bitcoin Maximalist",
    "the Layer 1 of the whole Satoshi experience.",
    "A monetary defibrillator to the treasure chest.",
    "It's a stun gun to the genitals.",
    "Volcano Bonds", "buying the dip",
    "BITCOIN FIXES ALL THIS",
    "The numbers don't lie.",
    "That's right, Bitcoin will take all the energy.",
    "Everyone will live their own experience in the rabbit hole.",
    "We are getting our souls back and our minds.",
    "We've seen some shit.",
    "The economy of love is infinitely more efficient than hate and war.",
    "right there in the Genesis Block.",
    # signature / byline
    "MAX KEISER", "Max Keiser", "maxkeiser",
    "Stacy and I have been living in here for 10 years.",
    # the two clue words as a pair
    "Max Keiser El Salvador", "OVERDOSE El Salvador",
]

# Keiser's mirror-writing clue, applied as the three transforms it can mean.
def mirror_variants(p):
    return {
        "reversed": p[::-1],
        "words_reversed": " ".join(p.split()[::-1]),
        "each_word_reversed": " ".join(w[::-1] for w in p.split()),
    }


def main():
    O = H.Oracle()
    rows = []
    seen = set()

    def add(phrase, kind):
        if phrase in seen or not phrase.strip():
            return
        seen.add(phrase)
        k = hashlib.sha256(phrase.encode()).digest()
        a = H.addrs_for_priv(k)
        rows.append((phrase, kind, a.get("p2pkh_u", ""), a.get("p2pkh_c", ""),
                     k.hex(),
                     "FUNDED" if (O.funded(a.get("p2pkh_u", "")) or
                                  O.funded(a.get("p2pkh_c", ""))) else "empty-now"))

    for p in PHRASES:
        add(p, "plain")
    for p in PHRASES:
        for kind, v in mirror_variants(p).items():
            add(v, kind)

    print("phrase\tvariant\taddr_uncompressed\taddr_compressed\tprivkey_sha256_hex\toracle_now")
    for r in rows:
        print("\t".join(r))
    sys.stderr.write(f"{len(rows)} candidates emitted\n")
    funded = [r for r in rows if r[5] == "FUNDED"]
    sys.stderr.write(f"currently funded: {len(funded)}\n")
    for r in funded:
        sys.stderr.write("  FUNDED " + str(r) + "\n")


if __name__ == "__main__":
    main()
