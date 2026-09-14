# The oracle is complete: a null now means something (2026-09-14)

Every "0 hits" in this project rests on one unexamined assumption -- that
`address_map.bin` actually contains the address we are looking for. If the
index were partial, or blind to a script type, every null would be worthless
and the whole search would be unfalsifiable. It is now measured.

## Method

Take addresses **known** to hold coins -- the enumerated sets of addresses
holding ~20 BTC, which were derived from chain data independently of this
index -- and ask the index whether it sees them.

| set | found | rate |
|---|---|---|
| named exact-20 | 870/870 | 100% |
| exact-20, in publication window | 122/122 | 100% |
| wide candidate set | 12,418/12,418 | 100% |

13,410 known-funded addresses, **every one present**.

## Script-type coverage, which was the real worry

| type | found |
|---|---|
| P2PKH (`1...`) | 1,517 / 1,517 |
| P2SH (`3...`) | 3,129 / 3,129 |
| P2WPKH (`bc1q...`) | 8,522 / 8,522 |
| **P2TR (`bc1p...`)** | **242 / 242** |

Taproot included. Combined with the earlier check that the derivation side
produces all five forms (p2pkh compressed and uncompressed, p2wpkh,
p2sh-p2wpkh, p2tr) and that `spk_from_address` parses bech32m, both ends of
the pipeline cover every address type in use.

## What this settles

`window/unswept_changes_everything.md` argued that if the prize is unswept its
address must be in this index, so a correct derivation would fire, leaving only
J2 (wrong material) or J3 (wrong method). That argument depended on the index
being complete. It is.

So the ~100M derivations swept from the column are **genuine negative
evidence**, not an artifact of a partial oracle. The remaining explanations are:

1. the derivation has not been tried (J3)
2. the material is not what we searched (J2)
3. the unswept premise is wrong, and the prize was taken years ago

A note on one control that failed on the way: the negative control originally
used `1BitcoinEaterAddressDontSendf59kuE` and the index reported it FUNDED.
That is correct -- people really do burn coins to that address, so it carries a
balance. The control was wrong, not the index. It now uses a freshly derived
key instead.
