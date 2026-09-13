# The premise was never verified (2026-09-13)

Three sessions have derived roughly 100 million addresses from this article and
found nothing. This note reports the step that none of them took first, and
which explains the nulls better than any cipher hypothesis.

## Nobody has ever shown that the 20 BTC exists

There is **no published escrow address** for this puzzle. Keiser never posted
one. In four statements over two years he never named an address, a
transaction, or any way for a solver to confirm the prize is real and
unclaimed:

| date | statement |
|---|---|
| 2021-11-19 | "Read my piece in @BitcoinMagazine 'Bitcoin Is Toxic AF' ... **Use promo code ORANGEPILL for 21% off**" |
| 2022-12-26 | "**Have you ever picked up a physical copy** of @BitcoinMagazine and read my column and Like George Sand's hidden cryptography, I have hidden private keys in the text." |
| 2023-03-04 | "I hid a private #Bitcoin key encoded in this piece ... Nobody's figured it out yet, but it's for 20 BTC" |
| 2023-12-30 | "Obviously, 'El Salvador' is a clue." |

Both of the first two are framed as magazine promotion, one with an explicit
discount code.

## An independent researcher reached the same conclusion

`floflo777/open-crypto-puzzles` is a systematic catalogue of crypto puzzles:
31 funded puzzles, each with its escrow address, the author's clues, what was
tried, and where the research stopped. Its author states they worked about 40
of these and solved several.

Its opening sentence is the inclusion criterion:

> "Someone hides a crypto wallet inside a puzzle, **publishes the address**, and
> dares the internet to solve it and keep what is in it. These are real, still
> unsolved, and the coins are sitting on-chain right now."

and its standing instruction to solvers:

> "Before any effort, re-check the escrow yourself ... **The chain is the truth**,
> not this file."

Its verdict on this puzzle, in `archive/dead-ends/README.md` under
*Excluded without research*:

> **Max Keiser 20 BTC**: matches a known scam pattern; not onboarded.

Every puzzle it *did* onboard has a verifiable address. This one was excluded
for lacking exactly that.

## Why this explains the evidence better than any cipher

The unverified premise accounts for every observation, with no cipher
hypothesis required:

- ~100M derived addresses, three independent sessions, every cipher family,
  **zero funded hits**
- 962 addresses hold exactly 20.00000000 BTC and **not one** is attributable to
  Keiser, El Salvador, or this article
- no public solution in three and a half years, and no writeup of anyone even
  getting partway
- no OP_RETURN, inscription or on-chain marker anywhere in blocks 0-829,999

A cipher hypothesis has to explain why a puzzle aimed at magazine readers
resisted 100M automated derivations. "There is no funded address" explains it
in four words.

## What this does and does not establish

It does **not** prove the puzzle is fake. Keiser may have funded an address he
never disclosed. The honest statement is narrower and still decisive for how to
spend effort:

1. **The prize is unverifiable.** No address, so no one can confirm 20 BTC was
   ever escrowed, nor that it is still there.
2. **Success is unrecognisable.** Without a target address, a solver who derived
   the correct key could not tell they had won, and neither could any oracle we
   built. Every "0 hits" in this repo is compatible with the key having been
   found, with it having been swept, and with it never having existed.
3. **The burden is on the claim.** For every other puzzle in the catalogue, the
   chain settles it in one request.

## The correct first question, for next time

Before any extraction, cipher, or sweep:

> **Which address holds the prize, and does the chain show it funded and
> unspent?**

If that question has no answer, the search has no success condition, and no
amount of compute creates one. This project ran 100 million derivations without
ever asking it.

## What would revive this

One thing only: **an address**. From Keiser, from Bitcoin Magazine, or from
anyone who can show a 20 BTC output attributable to this puzzle. Given one, the
whole toolkit here becomes useful immediately, and
`wf/handoff_candidates.tsv` can be checked against it in seconds.
