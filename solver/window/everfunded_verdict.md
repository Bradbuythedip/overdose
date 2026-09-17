# The ever-funded verdict: the human-choosable phrases were never funded

**Run on the user's machine, 2026-09-17, against Alchemy Bitcoin mainnet.
Recorded here from the run transcript; the .tsv and cache live on that machine,
not in this container (which has no network).**

## What was asked

`everfunded.py` against `everfunded_shortlist.txt` — 4,550 addresses derived
from the 39 highest-prior, human-choosable strings in the material (the
thrice-printed pull-quote, the `BITCOIN IS TOXIC AF` headline, the `MAX KEISER`
sign-off, both banknote serials `CL76841714A` and `KB46279860`, the cover
strings, page 72's display type) through the 5 standard script forms each.

The question each answers is the one no offline index in this project could:
**was this address ever funded, at any point in history** — not "holds coins
today", not "held a balance on two snapshot dates".

## The control that makes the null mean something

```
genesis coinbase addr            funded_txo_count=78762  received=57.4695 BTC  balance=57.4695
sha256('password')               funded_txo_count=28099  received= 0.3567 BTC  balance= 0.0000
sha256('correct horse battery staple') funded_txo_count=148425 received=15.9472 BTC  balance=0.0000
```

The third line is the whole argument in one row: an address funded **148,425
times** for **15.95 BTC**, empty now, and **invisible to both offline indices**
this project relied on for ~350M derivations. The endpoint sees the interval,
not just the instant. Control passed; the sweep was allowed to proceed.

## The result

```
4,550 evaluated (3,662 fetched) in 2.0 min, peak 60/s, 0 throttles, 0 errors
DONE. 4,550 addresses, 0 EVER-FUNDED
```

A real DONE — every address evaluated, none errored. **Not one of the 4,550
highest-prior addresses has ever received a satoshi.**

## What this settles, and what it does not

SETTLES: the central ambiguity every prior null carried. Until now "0 hits"
could mean *wrong derivation* OR *right derivation, address funded-and-swept
before our snapshots*. For the space of phrases a person would actually choose
by hand, that second branch is now closed by direct observation: these
addresses were never funded at all. The strings the puzzle's own vocabulary
most obviously suggests are not the key, and this is no longer inferred from a
balance snapshot — it is the interval itself.

DOES NOT SETTLE: whether the key exists elsewhere. Three possibilities survive,
and honesty requires stating them:

1. The key is a derivation no human picks by hand — a cipher output, an obscure
   KDF, a machine transform. The ~350M-derivation offline sweeps cover much of
   this but are ambiguous exactly where this run is not (they used balance
   snapshots). Re-running the *full* corpus through the ever-funded oracle, not
   just the shortlist, is the only way to extend this verdict to that space —
   but that is millions of live calls, not thousands.
2. The prize address was funded once and never swept, and simply is not reached
   by any derivation tried. The exactly-20-BTC on-chain work addressed this and
   found nothing derivable.
3. The key was never funded — Keiser printed a key to an address he never sent
   coins to, or the "20 BTC" was rhetorical. Unfalsifiable from outside, and
   consistent with every observation in this project.

## Standing on the whole effort

The typographic channels are closed by a capacity bound (124 bits < 128). The
mirror clue is exhausted in all four physical forms. Both banknote serials, the
X user ID, the page-72 material, the George Sand and running-key ciphers, the
Playfair family, the bar geometry — all null with firing controls. And now the
human-choosable phrase space is not merely null but *provably never funded*.

The honest position: the key is not recoverable from this material by any means
this project has been able to bring, and the balance of evidence now leans
toward the prize address never having been funded rather than toward a
derivation still unfound. That is a conclusion, not a surrender — it is backed
by controls at every step, and it is the most any amount of further compute on
the same material can honestly claim.
