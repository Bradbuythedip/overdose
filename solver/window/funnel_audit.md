# Funnel audit: the exactly-20-BTC pool is 962, not 212 (2026-09-13)

Direct measurement against `/tmp/address_map.bin` using the new offline oracle,
rather than re-deriving the number through the filter chain that produced it.

## The discrepancy

The candidate funnel used all session has been:

```
56,795,328 funded scripthashes
  ->  5,745  in the 19.5-20.5 BTC band
  ->  3,448  after the T_new filter
  ->  2,559  unmoved
  ->    212  exactly 20 BTC
  ->     68  tier-1 P2PKH  ->  67 after CashFX exclusion
  ->    116  P2PKH + P2SH under the corrected upper-bound-only window
```

Counting balances directly in the same file gives a different answer:

| balance | addresses |
|---|---|
| **exactly 20.00000000 BTC** | **962** |
| 20 +/- 0.01 | 3,162 |
| 20 +/- 0.1 | 4,012 |
| 19.5 - 20.5 | 5,745 |
| 19.0 - 21.0 | 8,053 |

The 19.5-20.5 figure reproduces exactly (5,745), which confirms this is the
same snapshot and the same file. So the gap is not data — it is filters.

`962 - 212 = 750` addresses were removed by `T_new` and `unmoved` *before* the
exactly-20 test was applied. Both deserve scrutiny:

- **`T_new`** is the filter already flagged in this session as encoding the
  discredited funding-date lower bound — the assumption the user demolished
  with "they could have been funded way earlier, why do you think they need to
  be funded around the launch". A key printed in a magazine can be arbitrarily
  old. This filter should never have been in the chain.
- **`unmoved`** (tx_count == 1, spent == 0) is *nearly* safe for an unsolved
  puzzle, but it is stricter than the premise requires: an address funded by
  two deposits, or that received an unsolicited dust payment, still holds an
  unspent 20 BTC and is still a live candidate. It fails `tx_count == 1`.

## Coverage of the real pool

Of the 962 exactly-20 addresses, the 116-address candidate list covers **116**.
**846 are unaccounted for** — measured, not estimated, by hashing all 116
candidates to scripthashes and differencing against the 962 extracted from the
index.

Scripthashes for all 962 are saved to `exact20_scripthashes.txt` so that any
address list obtained later (from a networked machine, an explorer export)
can be tested against the true pool offline and instantly.

## Why the 962 cannot be enumerated here

`address_map.bin` is keyed by `sha256(scriptPubKey)`, which is one-way. The
962 records can be *counted* and their scripthashes *extracted*, but the
addresses cannot be recovered from them. Naming the 846 requires an
address-indexed source, and this sandbox's egress policy 403s every Bitcoin
API host at the CONNECT layer.

## Why this does not block the search

The 116-address list was never the right object to search against. A
derivation sweep scored against the **full 56.8M index** covers all 962 —
and every address outside the band as well — so it inherits none of these
filter assumptions. That is what `full_sweep.py` now does, and it is strictly
more powerful than enumerating the 962 would be.

## Round-number context

Exactly-20 is a popular holding, which is worth stating plainly because it
caps how much any "it holds exactly 20 BTC" argument can ever be worth:

| balance | count | | balance | count |
|---|---|---|---|---|
| 18 BTC | 171 | | 20.01 BTC | 18 |
| 19 BTC | 142 | | 20.1 BTC | 16 |
| 19.9 BTC | 27 | | 20.5 BTC | 6 |
| 19.99 BTC | 17 | | 21 BTC | 94 |
| **20 BTC** | **962** | | 22 BTC | 44 |

20 BTC is ~7x more common than its immediate whole-BTC neighbours — a strong
round-number preference by ordinary holders, not a puzzle signature. This
independently confirms the workflow agent's observation that **the exact-20
property carries no discriminating information between candidates**, because
the set was pre-filtered on it. Every "but it holds exactly 20 BTC" argument
is circular, and now the size of the reference class is known: 962.

## Sanity check on the snapshot

Total supply across all 56,795,328 records: **19,919,810 BTC**. Consistent
with a 2024-2025 snapshot (~19.9M mined, minus provably lost/unindexed).
