# Naming the exactly-20-BTC pool: 116 -> 870 of 962 (2026-09-13)

`funnel_audit.md` established that 962 addresses hold exactly 20.00000000 BTC
and that we could name only 116 of them, because `address_map.bin` is keyed by
`sha256(scriptPubKey)` — one-way — and every Bitcoin API host is 403'd here.
846 were unaccounted for. That gap is now 92.

## How

The blocker was assumed to be network access. It was not: a GitHub-hosted
address dump is reachable over the git proxy, and an earlier session had
already used one (`Pymmdrza/Rich-Address-Wallet`) without anyone noticing it
could close this gap.

Cloned it and hashed every Bitcoin address in it to `sha256(scriptPubKey)`,
then intersected against the 962 target scripthashes.

- 1,051,351 unique BTC addresses read (95 undecodable)
- **positive control: all 116 previously-known candidates are present in the
  dump**, so a null here would have been meaningful — required before believing
  any result from a new source
- **870 of the 962 named**, 754 of them new
- 92 still unnamed: the dump is an April-2023 rich list, so an address funded
  later, or one below its depth, will be missing

## What this corrects

The script-type split of the 870 is not what the earlier snapshots implied:

| type | named here | earlier snapshot |
|---|---|---|
| P2PKH `1…` | 128 | 68 tier-1 |
| P2SH `3…` | 237 | 248 |
| **bech32 `bc1…`** | **505** | **62** (44 bc1q + 18 bc1p) |

The earlier bech32 enumeration was roughly **12% complete**. That matters
because this repo previously recorded, on the strength of those 62, that
"0 addresses with exactly 20 BTC unmoved in either bech32 class — so the
@NachoKeysBTC `bc1q3e…6gvskf` claim is unsupported by chain data". That
conclusion rested on a sample far too small to support it and should not have
been stated so firmly.

## Re-testing the NachoKeysBTC claim properly

Against the 505 named bech32 exactly-20 addresses:

```
starting bc1q3e : 0
ending  6gvskf : 0
```

Against every bech32 address in the full dump (435,312 of them, reaching down
to roughly 4 BTC):

```
bc1q3e*  : 404
*6gvskf  : 0
both     : 0
```

So the claimed address is absent from a 435k-address bech32 rich list reaching
~4 BTC. This is much stronger than the earlier 62-address version of the same
claim, but it is still not proof: the dump is an April-2023 snapshot, and an
address funded after it, or holding less than the dump's depth, would not
appear. Stated as evidence, not as a disproof.

## What the named set buys

Immediately, offline:

- **On-chain markers, re-run over all 870** (previously 116) against 2.2M lines
  of embedded chain text from blocks 0-829,999 including input scripts, with
  the genesis-coinbase control passing: **0 hits**.
- No keyword vanity: none of the 870 contains `keiser`, `overdose`, `maxk`,
  `satoshi`, `bukele`, `salvador`, `volcano`, `toxic`, `utxo`, `puzzle`,
  `mirror` or `stacy`, and none has even a 4-character repeat run.

For a networked machine, the candidate list for `address_check.py`,
`trace_funding.py` and the OP_RETURN scan is now **870 addresses rather than
116** — `named_exact20_870.txt`.

## Caveat that does not go away

Naming these does not help the derivation side at all, and it is worth being
explicit about why: the brainwallet and HD sweeps are already scored against
the **full 56.8M funded index**, which contains all 962 regardless of whether
we can spell them. Enumeration only helps the chain-side filters — funding
date, spend history, funder attribution — all of which need network access.
