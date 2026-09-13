# On-chain marker scan (2026-09-13)

Tests whether Keiser marked the puzzle wallet on-chain — an OP_RETURN message,
an inscription, or the address appearing in any embedded text. This axis is
independent of every balance/UTXO filter used elsewhere: it would find the
wallet even if the balance moved or it fell outside the exact-20 set.

## Source

`cirosantilli/bitcoin-inscription-indexer` — a dump of every ASCII string of
length >= 20 found in Bitcoin **output scripts**, with txids and block numbers,
served from raw.githubusercontent.com (one of the few hosts this sandbox can
reach).

Layout: `data/out/NNNN.txt` covers blocks NNNN*1000 .. NNNN*1000+999.
Fetched `0000`–`0781` = blocks 0 through 781,999, i.e. genesis through the
4 Mar 2023 announcement. **782 files, 85 MB, 1,301,367 non-empty lines.**

## Validation FIRST (this matters)

An initial run reported "0 hits on all keywords" and it was **worthless**.
`seq -w 0 781` pads to three digits (`000`…`781`) but the repo uses four
(`0700.txt`). All 782 downloads were 14-byte `404: Not Found` bodies, which
passed a naive `[ -s ]` non-empty guard. The search ran over 3 MB of error
pages.

Caught by a positive control, and re-run correctly. Controls on the good data:

- genesis coinbase present: `The Times 03/Jan/2009 Chancellor on brink of
  second bailout for banks` — found in 0360.txt, 0368.txt, 0519.txt
- real inscription records with txid + block: e.g.
  `tx cfb9f04f… blk 700000 txid 300 / Bloque 700.000 achicrip.org :)`

**Rule adopted: a null from a data source means nothing until the source has
been shown to produce a known positive.**

## Results (index validated)

| query | hits |
|---|---|
| all 116 candidate addresses | **0** |
| 22 candidate funding txids | **0** |
| `george sand` | 0 |
| `bitcoin magazine` | 0 |
| `toxic maximalist` | 0 |
| `keiser` | 2 — both third-party |
| `overdose` | 1 — a Marilyn Monroe biography inscription |
| `bukele` / `el salvador` | 16 — Salvadoran protest graffiti transcriptions |

The two `keiser` hits, in full:

```
F You Money! cap owner: FYM 1.20 of 1.24 -> Max Keiser
EW Thanks to @maxkeiser I've made a lot of money! Great advices!
```

Neither authored by him. (The same "F You Money" cap series also lists
`FYM 1.23 of 1.24 -> Nayib Bukele`.)

## Why the null is informative rather than merely absent

Other puzzles **are** in this index:

```
Phemex puzzle address 1h8BNZkhsPiu6EKazP19WkGxDw3jHf9aT endomorphism
Welcome to Crypto Puzzles by ZDEN: http://crypto.haluska.sk
https://cpdproject.com/100_eth_puzzle.php
I solved the puzzle. You have 24 hours before I get the btc out, good luck!
```

So the index demonstrably surfaces exactly this pattern when a creator uses it.
Keiser's candidates produce nothing.

That agrees with a dispositional finding from the research sweep: Keiser is
publicly hostile to on-chain data embedding — he called Ordinals "a bug" on the
network and the OP_RETURN datacarrier limit increase "the OP RETURN regression"
(x.com/maxkeiser/status/1979595548295377117), and posted "Core has lost the
plot". An OP_RETURN marker would be out of character.

## Limits of this result — stated, not buried

1. The index only captures strings **>= 20 characters**. A bare 6-byte
   `keiser` OP_RETURN would be invisible to it.
2. The repository self-describes as "incomplete because of lack of time".
3. It indexes output scripts; it is not a guaranteed-complete OP_RETURN index.

This narrows the on-chain-marker hypothesis substantially. It does not
eliminate it. A complete check needs Blockchair's `/outputs` infinitable or the
BigQuery `crypto_bitcoin.outputs` table.

## Correction to earlier guidance

An earlier suggestion to query Blockchair with
`script_hex(~6b6569736572)` was **wrong**. Per Blockchair's own API docs,
`script_hex` supports only the `^` starts-with operator. Substring search lives
on a different field and takes the plain string, not hex:

```
https://api.blockchair.com/bitcoin/outputs?q=type(nulldata),script_bin(~keiser)
```
