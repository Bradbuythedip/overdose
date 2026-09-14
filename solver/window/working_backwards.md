# Working backwards from a solution (2026-09-14)

Thought experiment: assume the puzzle *was* solved. Which of our results is the
false negative? The negative set is large enough that this is a constraint
problem with few surviving answers.

## The constraint set

| # | result | what it forbids |
|---|---|---|
| C1 | ~150M derivations from article text, all n-grams 2-12, case/punctuation/whitespace variants, reversals, atbash, word-order reversal, under 7 fast hashes x 5 script types, scored against the FULL 56.8M funded index **and** the Apr-2023 rich list | a fast-hash brainwallet over any contiguous or simply-transformed span of the article — *unless the address is invisible to both oracles* |
| C2 | stretched KDFs: WarpWallet N=2^18, PBKDF2 1k-65k x 8 salts, scrypt 2^12/2^14, over 338-1,988 **curated** phrases | curated-phrase KDFs only. The full n-gram space under a KDF is **not** covered |
| C3 | 84 selection rules x 6 scopes, forward and mirrored, against WIF/BIP38/mini checksums; longest alphanumeric token in the article is 16 chars | the key being printed contiguously as base58 |
| C4 | channel capacity: capitalisation 30 + highlight colour 38 + all-caps 44 + wide gaps 7 + quoted strings 5 = **124 bits**, against 128 for a 12-word mnemonic | any discrete editorial channel carrying a key. A bound, not a search |
| C5 | bold ratios 1.00/1.01/1.03/0.98 at 400 dpi — *flatter* than on the phone photos; no drawn rules; no glyph printed reversed | any per-glyph channel |
| C6 | BIP-39 93 checksum-valid windows x 17 passphrases (every El Salvador spelling), Electrum v2 123 seed-version-valid, old Electrum 508 windows | seed-phrase windows over the prose |
| C7 | no trailing data, EXIF, COM, APPn, LSB; DQT byte-identical across all 7 photos | binary steganography in the images |
| C8 | no OP_RETURN or inscription marker in blocks 0-829,999 including input scripts; 1,372 exactly-20 addresses carry no word >= 4 chars | an on-chain marker or a vanity prize address |
| C9 | both serials, singly and as a two-component split, additive and hashed | the two-note split-key reading |
| C10 | no public writeup in 3.5 years; an independent puzzle cataloguer excluded it for having no published escrow address | — (evidence about the premise, not the method) |

## The three joints

Any solution must break at exactly one of these. There is no fourth.

### J1 — the oracle joint: our detector cannot see the answer

Every sweep asks *"is this address funded now, or was it rich in April 2023?"*
An address is invisible to both if it holds zero today and was never a rich-list
entry — i.e. **if it was funded and then swept**.

This is the joint that requires no cleverness at all on the solver's part, and
it has a property none of the others do: **it makes C1 vacuous**. If the prize
was swept, then one of our ~150 million derivations may already have produced
the correct private key, and we recorded it as a miss and threw it away.

It is also strongly favoured on priors. A phrase-derived key is swept by bots
within seconds of funding; that is why all 8 famous brainwallets this project
probed hold zero. Keiser's "nobody's figured it out yet" would still read as
true to him, because he had no reason to watch an address he was not tracking.

**The asymmetry that matters:** a human solver imports a candidate key into any
wallet and sees *history*. We can only see *balance*. Those are different
questions, and we have only ever been able to ask the weaker one.

### J2 — the corpus joint: the material is not in what we searched

Keiser said key**s**, plural, "in the text" of his column generally. Only Issue
24 has ever been examined. Page 72 is the proof of concept for this joint: it
sat inside the issue we already had, absent from every transcript, for three
sessions — and it carried a second banknote serial and 22 printed numerals that
no corpus contained.

### J3 — the derivation joint: right material, derivation never tried

C1-C6 cover a very large space, but two gaps are real rather than rhetorical:

1. **KDFs over the full n-gram space.** C2 only ever ran stretched KDFs over a
   few hundred *curated* phrases. A KDF is deliberately expensive, so it is
   exactly where a bulk sweep cannot follow — the coverage claim was always
   "150M addresses *under fast hashes*".
2. **A human-in-the-loop step.** A cipher whose plaintext is an *instruction*
   rather than a key — read the message, then type something not literally
   present in the text. No mechanical sweep can cross that gap.

## Which joint, on the evidence

J1. It alone explains the *pattern* of the nulls rather than just their
existence: a universal, featureless zero across every method, every corpus and
every resolution, with no partial signal anywhere. J2 and J3 would be expected
to leave traces — a near-miss, a checksum that fires, a readable fragment — and
there are none. A blind detector produces exactly this: nothing, everywhere,
regardless of how well the method is chosen.

## How to identify the method from a solution

Given a solution, the method is recoverable, and cheaply. Ranked by how much
each datum settles:

**1. The private key alone identifies the passphrase.** `reverse_lookup.py`
inverts our own corpora: for every phrase this project ever generated
(`candidates_v2.txt`, the transcript n-grams, the highlight catalogue, the
Keiser biography set — hundreds of thousands of strings) it recomputes all
seven fast hashes and both KDF families and compares to the given key. A match
names the exact phrase and the exact derivation. This is the single most
informative test and it runs in minutes.

**2. The address alone identifies the joint.**
- currently funded → our oracle *should* have caught it → the derivation lies
  outside our swept space, so **J2 or J3**
- zero balance with on-chain history → **J1 confirmed**, our oracle was blind,
  and the derivation may well be one we already computed
- no history at all → the key was never funded; the prize claim was empty

**3. The key format names the family.** Raw 64-hex vs WIF vs a 12- or 24-word
mnemonic vs a Casascius mini key each implicate a different half of the search.

**4. The funding transaction dates the puzzle** and, through its inputs, may
attribute the funder — which would settle the premise question in `PREMISE.md`
independently of the cipher.
