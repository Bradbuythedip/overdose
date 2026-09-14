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
| article n-grams, sha256 -> P2PKH | 44,956 | 2, both dust, dated Feb 2025 |
| tier-1 phrases x 135 derivations | 44,777 | 0 |
| generic corpora (`candidates_*`) | 15,672 | **52** |
| HD paths (`hdfull`) | 112,880 | in progress |
| new corpora | 72,042 | queued |

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
