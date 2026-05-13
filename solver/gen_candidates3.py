#!/usr/bin/env python3
"""Additional cipher hypotheses for the Keiser Overdose puzzle.

Hypotheses:
  H1. The four ALL-CAPS sentences (BITCOIN IS TOXIC AF, EVERY SINGLE..., BITCOIN FIXES ALL THIS, etc.) ARE the cipher: take them as-is.
  H2. The orange + yellow highlights are read as Morse via length (short/long).
  H3. The X marks count + pill counts + page numbers concatenated.
  H4. The first letter of each WORD in each highlighted phrase, concatenated.
  H5. Letter-count of each highlighted phrase forms a numeric string.
  H6. Each phrase's first capital letter, concatenated (an acrostic of emphasis).
  H7. The dollar amounts in highlights: $1 billion, $85 BILLION, $2 trillion -> "1852".
  H8. Years: 2008, 1971, 2017, 1969 -> "2008197120171969" or sorted "1969 1971 2008 2017".
  H9. Highlighted phrases reversed.
  H10. Per-page word count of highlights as a string.
  H11. The graffiti words spliced: "shitFUCKALL", "FUCKALLshit", "XXFUCKALL", etc.
  H12. Use only highlighted *single-token* phrases (Maximalist, hyperbitcoinized, Saketoshi, etc.) concatenated.
  H13. The page numbers 73-79 as base or as text.
  H14. SHA256 of HL phrases prefixed/suffixed with page numbers.
"""
import os, re, hashlib

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

ALL_CAPS_SENTENCES = [
    "EVERY SINGLE ONE OF THE BITCOIN WANNABES - BCH, BSV, ETH, XRP, ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT MONEY AND GOLD - IS FACING THE IGNOMINIOUS FATE OF DEMONETIZATION VERSUS BITCOIN.",
    "BITCOIN FIXES ALL THIS by replacing oil-dripping, corpse-ridden, poppy-harvesting fiat money with perfect bitcoin.",
    "BITCOIN IS TOXIC AF",
    "MAX KEISER",
    "OVERDOSE",
]

WORD_RE = re.compile(r"[A-Za-z0-9']+")
def words(s): return WORD_RE.findall(s)

def main():
    seen = set(); cands = []
    def add(s):
        if not s or len(s)>250 or s in seen: return
        seen.add(s); cands.append(s)

    # H1: all-caps sentences verbatim and variants
    for s in ALL_CAPS_SENTENCES:
        add(s); add(s.lower()); add(s.title())
        add(re.sub(r"[^A-Za-z0-9 ]","",s).strip())
        add(re.sub(r"[^A-Za-z0-9 ]","",s).strip().lower())

    # H4: first letter of each WORD in each HL, concatenated (per phrase)
    for h in ALL_HL:
        fl = ''.join(w[0] for w in words(h))
        add(fl); add(fl.lower()); add(fl.upper())
    # globally
    all_fl = ''.join(''.join(w[0] for w in words(h)) for h in ALL_HL)
    add(all_fl); add(all_fl.lower()); add(all_fl.upper())

    # H5: letter-count of each HL phrase
    counts = [str(len(re.sub(r"\s","",h))) for h in ALL_HL]
    add(''.join(counts))
    add(' '.join(counts))
    # word-count per HL phrase
    wcounts = [str(len(words(h))) for h in ALL_HL]
    add(''.join(wcounts)); add(' '.join(wcounts))

    # H6: capital letters in each HL, concatenated
    for h in ALL_HL:
        caps = ''.join(c for c in h if c.isupper())
        add(caps); add(caps.lower())
    all_caps = ''.join(''.join(c for c in h if c.isupper()) for h in ALL_HL)
    add(all_caps); add(all_caps.lower())

    # H7: dollar-amount tokens
    for s in ['1852','185172','$1 $85 $2','185','125','1 85 2','1,85,2',
              '$1 billion $85 billion $2 trillion',
              '1 billion 85 billion 2 trillion',
              '1+85+2','88','852','58821','51421']:
        add(s)

    # H8: year tokens
    for s in ['2008','1971','2017','1969','2021','2022',
              '2008197120171969','1969197120082017',
              '08 71 17 69','2008 1971 2017 1969',
              '20081971','19712017','20081969','19692008']:
        add(s)

    # H9: highlighted phrases reversed (whole-string and per-word)
    for h in ALL_HL:
        add(h[::-1])
        rev_words = ' '.join(reversed(words(h)))
        add(rev_words); add(rev_words.lower())

    # H10: per-page word count strings
    per_page = {
        75:[10],76:[11],77:[10],78:[7],79:[4]
    }  # phrase counts
    add('10 11 10 7 4'); add('1011074'); add('1011 1074')
    # per-page summed word counts of highlighted phrases
    page_wc = {
      75: sum(len(words(p)) for p in ALL_HL[0:10]),
      76: sum(len(words(p)) for p in ALL_HL[10:21]),
      77: sum(len(words(p)) for p in ALL_HL[21:31]),
      78: sum(len(words(p)) for p in ALL_HL[31:38]),
      79: sum(len(words(p)) for p in ALL_HL[38:]),
    }
    s = ' '.join(str(page_wc[p]) for p in (75,76,77,78,79))
    add(s); add(s.replace(' ',''))

    # H11: graffiti combinations
    for g in ['shitFUCKALL','FUCKALLshit','shit FUCK ALL','XXFUCKALL',
              'XX shit XX','XXXX','FUCKALLshitXXXX','SHITFUCKALL',
              'shit fuck all','SHIT FUCK ALL']:
        add(g)

    # H12: single-token highlights concatenated
    singles = ['Layer 1','Maximalist','hyperbitcoinized','Saketoshi',
               'Mike Novogratz','Volcano Bonds','UTXO','51%','$1 billion']
    add(' '.join(singles)); add(''.join(singles))
    add(' '.join(singles).lower()); add(''.join(singles).lower())

    # H13: page numbers
    add('73 74 75 76 77 78 79'); add('73747576777879'); add('7374757677')

    # H14: SHA256 of HL phrases hex-stringified as passphrase
    # Not directly useful but try truncated hashes as candidate KEY phrases
    # (very long shot, but cheap)
    for h in ALL_HL:
        ho = hashlib.sha256(h.encode()).hexdigest()
        add(ho[:32]); add(ho[:16])

    # H15: every word that appears highlighted (deduped, sorted)
    all_words = set()
    for h in ALL_HL:
        for w in words(h):
            all_words.add(w); all_words.add(w.lower())
    add(' '.join(sorted(all_words)))
    add(''.join(sorted(all_words)))

    # H16: pill-encoded
    # 5 pills page 73 + 4 pills page 79 = 9, 11 pills total combined
    for s in ['5 pills 4 pills','54 pills','9 pills','11 pills',
              'five pills four pills','five four']:
        add(s)

    # H17: signature line
    for s in ['Max Keiser Overdose 20 BTC',
              'OVERDOSE 20 BTC MAX KEISER',
              'MAX KEISER OVERDOSE',
              'Overdose Max Keiser 20 BTC Bitcoin Magazine El Salvador',
              'Stacy and I have been living in here for 10 years.',
              'we have seen some shit',
              "We've seen some shit",
              "Stacy and I",
              "Stacy and I have been living in here for 10 years",
              "10 years",
              "ten years"]:
        add(s); add(s.lower())

    out = os.path.join(os.path.dirname(__file__), 'candidates3.txt')
    with open(out,'w') as f:
        for c in cands: f.write(c+'\n')
    print(f"wrote {len(cands)} candidates to {out}")

if __name__ == '__main__':
    main()
