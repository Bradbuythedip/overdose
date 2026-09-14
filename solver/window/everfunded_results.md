# The ever-funded sweep: first results (2026-09-14)

`window/the_oracle_blind_spot.md` established that this project's two offline
oracles are **balance snapshots** — `address_map.bin` answers "holds coins
today", the rich-list index answers "held a large balance in April 2023" — and
that neither answers "was ever funded". Control: 32 canonical brainwallet
phrases x 2 pubkey forms = 64 addresses that all demonstrably held coins once
and were drained, **0 of 64 present in either index**.

`everfunded.py` closes it over an Esplora endpoint. Its control passed live:

```
genesis coinbase                        78,762 fundings   57.4695 BTC   balance 57.4695
sha256('satoshi')                            5 fundings    0.0039 BTC   balance  0.0000
sha256('password')                      28,099 fundings    0.3567 BTC   balance  0.0000
sha256('correct horse battery staple') 148,425 fundings   15.9472 BTC   balance  0.0000
```

Nearly 16 BTC passed through that last address and it reads zero today. Both
offline indices report it absent. That is the history this project could not
see, and can now.

## Results

| pass | addresses | ever-funded |
|---|---|---|
| article n-grams, sha256 -> P2PKH | 44,956 | 2, dust, Feb 2025 |
| tier-1 phrases x 135 derivations | 44,777 | **0** |
| generic corpora (`candidates_*`) | 15,672 | 52, all generic |
| `10years` correction delta | 566 | **0** |
| HD paths (`hdfull`, 68 paths) | 112,880 | **0** |
| new corpora (`corpora2`) | 72,042 | 3, all single words |
| bare P2PK | 17,928 | pending |
| wrapped / 1-of-1 multisig | 46,480 | pending |
| **total evaluated** | **290,893** | **57** |

**Every one of the 57 is a generic dictionary entry.** Not one is an
article-specific reading.

The three from `corpora2` are the clearest demonstration, because that list is
the project's most principled work — boustrophedon, the Sand device on the
author's units, byte variants, the numbers trail, the Schott pointers — and the
only things in it that had ever been funded were:

```
0.01200000  love          0.00010000  michael      0.00005460  virtually
```

Three single common words, and the third at the **identical 0.00005460** that ten
earlier single-word hits share. They reached the list by accident: the
byte-variant expansion replaces an em dash with the empty string, so a 2-gram
like "love —" collapses to "love". `gen_corpora_addrs.keep()` now drops
single-token phrases, with those three as regression cases.

## The sprayer, identified

Eleven addresses across two independent passes received **exactly 0.00005460
BTC**: Afghanistan, Amsterdam, Heisenberg, Manhattan, discovered, efficient,
experience, infinitely, terrorists, theorized, virtually. One actor walking an
English word list and dusting every brainwallet it generates. It is the dominant
source of every "hit" in this project and it has nothing to do with the puzzle.

## The 52 hits are all generic, and that is the finding

Every one attributed through the manifest. Not one is article-specific:

```
5.28098999  the                 0.28187090  Bitcoin       0.28134000  Money
0.21293065  1                   0.17054557  bitcoin       0.13871027  42
0.03862600  The Times 03/Jan/2009 Chancellor on brink of second bailout for banks
0.02773589  Satoshi Nakamoto    0.01087000  mike          0.01010000  you
0.00005460  Afghanistan | Amsterdam | Heisenberg | Manhattan | discovered |
            efficient | experience | infinitely | terrorists | theorized
```

Ten of them share an identical **0.00005460** — one sprayer walking a word
list. The only long string is the Genesis coinbase, already known and already
attributed. The rest are single letters, bare digits, and famous names, which
is exactly what a generic brainwallet dictionary contains.

## What this does to the swept-key hypothesis

It argues against it, and that reverses the expectation this oracle was built
on.

Generic dictionary phrases are funded at roughly **0.33%** in this sample
(52 of 15,672). The article's own text is at **0%** across 89,733 addresses
covering every sentence, paragraph, line and 2..12 word n-gram in both cases,
plus 135 derivations each for the tier-1 phrases.

If a solver had derived a correct article phrase and swept 20 BTC, that address
would be ever-funded. None is. So for the phrase space tested, "someone already
solved it and took the coins" is now the *less* supported reading, not the more
supported one.

Stated precisely, because the distinction matters: this rules out **the
brainwallet family over the tested phrase space**. It does not rule out a key
that was never funded, a derivation outside the space, or an output type the
endpoint cannot reach.

## What the endpoint cannot reach

Alchemy answers `/address` but returns no `chain_stats` for `/scripthash` in
either byte order. That blocks the two stages built on raw scriptPubKeys:

- **bare P2PK** (17,928) — a raw pubkey output has no address form and is
  absent from every address-keyed index here, demonstrated with block 1's
  unspent coinbase
- **wrapped and 1-of-1 multisig** (46,480) — P2SH and P2WSH around P2PK, P2PKH
  and multisig, and their nestings; the only real test of the multisig question

`--debug-url` exists to tell a refusal apart from a genuine "never funded",
since an endpoint answering HTTP 200 with an error body parses as
`funded_txo_count=0` and is otherwise indistinguishable — the same shape as
this repo's 782-files-of-404-bodies incident. Until that diagnostic says
otherwise, these two families are recorded as **untestable with this endpoint**:
a data limit, not a cipher result.

## Reading a hit

`funded_txo_count > 0` is not the prize. Dust and collisions are common and the
52 above are all of that kind. What matters is **`received_btc`** — 20 BTC is
2,000,000,000 sats, six orders of magnitude above the dust floor seen here.
