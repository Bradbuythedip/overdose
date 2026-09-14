# What the nulls actually prove, and what is left (2026-09-14)

## The offline oracle is a real success condition, not a proxy

`address_map.bin` indexes ~56,000,000 addresses holding a **non-zero balance**.
That has been treated here as a weak stand-in for a chain query. It is not, for
the case that matters most:

> **If the prize is real and unspent, its address is in that index.**

So a correct derivation fires offline, with no network access. Across roughly
**150,000,000 derivations from this article, it has never fired** — not for
20 BTC, not for any balance at all.

This is the strongest statement this project can make, and it has never been
stated plainly:

**For the entire derivation space tested, no address derived from this
article's text holds a single satoshi today.**

Its blind spot is precise and narrow: an address funded and then **swept** has
a zero balance and is absent. That is the one scenario the offline index cannot
see — which is exactly why `swept_key_untested.md` matters, and why that
hypothesis remaining open is the live question rather than a technicality.

## Closed in this round

| hypothesis | scale | result against its own null |
|---|---|---|
| Keiser persona as passphrase | 1,377,100 scriptPubKeys | 0 hits. `honey badger`, the silver campaign and `Death to the Fed` had never been in any corpus despite the article containing **honey-badgering** |
| Sand's device (alternate lines) | 200 null draws | z −0.71, below the null mean |
| Musset's device (first word of each line) | 200 null draws | z −0.12, below the null mean |
| all 7 line devices | — | **not one exceeds its own null's maximum** |
| BIP-39 words in the highlighted runs | 38 runs, 200 words | 12-word windows 1/37 vs **2.31 expected**; 24-word 0/25 vs 0.10. No stratum holds exactly 12 or 24 |
| Genesis block constants as key material | 23,875 scriptPubKeys | 0 hits — hash, merkle root, nonce, timestamp, coinbase pubkey, and each crossed with the serial |
| wide-gap sequence `[10,3,10,3,8,5]` | 23,650 scriptPubKeys | 0 hits; five of six gaps are justification inside highlight rectangles |

## Page 72 identified

`scan400/p72_mask.png` is the only 400dpi mask with no source JPEG and no
transcript entry. It is the magazine's **NUMBERS** department — a remittance
infographic (Western Union, Palestine, `$930.44 BILLION BY 2026`) facing the
column, not Keiser's writing. It is also the page whose text bleeds through
page 73's blank left half, which accounts for the mirrored show-through text
visible there. Already covered by `gen_numbers.py --set p72`.

## What is actually left

Three things, in order of how much they would move the answer:

1. **The swept-key hypothesis.** Untested — `swept_key_untested.md` shows the
   test that claimed to close it had power to expect 1.74 hits and observed 0
   (p = 0.402). This is the only hypothesis the offline oracle is structurally
   blind to. Settling it needs transaction-graph forensics on the 962
   exactly-20-BTC addresses, which needs chain access.
2. **An escrow address.** Keiser never published one across four public
   statements. Without it there is no success condition for the swept case, and
   `PREMISE.md` is right that this is the first question that should have been
   asked.
3. **Derivations outside the tested space.** Always possible, and always will
   be. But the space now includes 7 direct hashes, 5 seed types over 72 HD
   paths, 5 address forms, 20 wrapped and multisig forms, stretched KDFs over
   4 salts, bare P2PK, and every phrase, n-gram, cipher, line device and
   persona string enumerated above.

## The honest summary

No key has been found. No key has been fabricated. Every hypothesis that was
closed is closed with a stated power and a matched null, and the one that was
closed on a confounded statistic has been reopened.
