# Axiomatic Design — Window Scan for the Keiser "Overdose" 20 BTC Wallet

Scope: find every wallet funded **once**, with **~20 BTC** (19.5–20.5), during
**2022-10-01 → 2023-04-01 UTC**, that has **never spent**.
Complementary to the parallel session (which enumerates *exactly* 20.00000000 BTC
with no date constraint).

---

## 0. Customer need → functional requirements

**CN**: Identify the wallet address whose private key Keiser claims to have
encoded in the Fall-2022 *Bitcoin Magazine* "Overdose" article.

| FR | Statement |
|----|-----------|
| FR1 | Delimit the set of blocks whose timestamps lie in the puzzle-creation window |
| FR2 | Extract every output in those blocks with value ∈ [19.5, 20.5] BTC, with (txid, vout, address/script, value, height, time) |
| FR3 | Retain only addresses with `tx_count == 1` ∧ `spent_txo_sum == 0` (funded once, never spent) |
| FR4 | Confirm each survivor's balance ≈ 20 BTC against an independent index snapshot |
| FR5 | Rank survivors by Keiser-attribution signal and emit the candidate table |

## 1. Constraints (the design driver)

| C | Constraint | Source |
|---|---|---|
| C1 | Sandbox egress is an **allowlist**: `github.com`, `*.githubusercontent.com`, pypi/npm/crates/goproxy. Alchemy, blockstream, mempool, blockchair all return **403 at CONNECT** (org egress policy). | measured |
| C2 | User's laptop reaches blockstream esplora **and** Alchemy Bitcoin RPC | given |
| C3 | Alchemy exposes block-indexed RPC only — no address or scripthash index | given |
| C4 | Must not duplicate the parallel session's exact-20.00000000 enumeration | given |
| C5 | `address_map.bin` snapshot is **2025-10-11**, 56,795,328 funded scripthashes, verified (`AMAP` magic, size == header+n*40+4) | measured |
| C6 | `Qalander/bitcoin-all-addresses` corpus (reachable) covers blockchair dumps only through **2021-01-17** | measured |

C1 is decisive: **the FR1/FR2 data-acquisition DPs cannot execute in the sandbox at all.**
The design must therefore partition DPs by *execution locus* and minimise what crosses
the sandbox↔laptop boundary.

## 2. Two candidate designs

### Design A — the literal brief (block-forward)

| | DP1 `getblockhash` sweep | DP2 `getblock <h> 2` + parse vouts | DP3 blockstream `chain_stats` | DP4 index lookup | DP5 semantic scoring |
|---|---|---|---|---|---|
|FR1| **X** | 0 | 0 | 0 | 0 |
|FR2| **X** | **X** | 0 | 0 | 0 |
|FR3| 0 | **X** | **X** | 0 | 0 |
|FR4| 0 | **X** | 0 | **X** | 0 |
|FR5| 0 | **X** | **X** | **X** | **X** |

Lower-triangular ⇒ **decoupled** (satisfies the Independence Axiom, execution order fixed).
It is *valid*. Its problem is the Information Axiom, below.

### Design B — pipeline inversion (balance-first)

The reordering rests on a small theorem.

> **Theorem (inversion is lossless).** Let `W` be the set of addresses funded exactly
> once, in-window, with a single output value ∈ [19.5, 20.5] BTC, never spent.
> For any `a ∈ W`: `tx_count(a) = 1` and `spent_txo_sum(a) = 0` ⇒ `balance(a)` equals
> its funding value at *every* time after funding — in particular at the snapshot
> instant `T_snap = 2025-10-11`, which is after the window (C5).
> Hence `scripthash(a) ∈ T`, where `T` = index entries with balance in the band.
> Therefore **`W ⊆ resolve(T)`**: enumerating `T` first discards nothing.

> **Corollary (corpus subtraction is sound).** If `a ∈ W`, its single transaction is
> in-window (≥ 2022-10). The corpus of C6 lists every address appearing in any output
> up to 2021-01-17. An address present there had a transaction before 2021, so
> `tx_count ≥ 2` once the in-window funding is added — contradicting `a ∈ W`.
> Hence **`W ⊆ T_new := T \ resolve(corpus)`**, and `T_new` is computable *entirely
> offline from the sandbox*, with **no false negatives**.

| | DP4′ index band scan (local) | DP6 corpus subtraction (local) | DP7 scripthash history (Electrum) | DP2′ raw-block scan (Alchemy, fallback) | DP5 semantic scoring |
|---|---|---|---|---|---|
|FR4| **X** | 0 | 0 | 0 | 0 |
|FR2| **X** | **X** | 0 | 0 | 0 |
|FR1| **X** | **X** | **X** | **X** | 0 |
|FR3| **X** | 0 | **X** | **X** | 0 |
|FR5| **X** | **X** | **X** | **X** | **X** |

Also triangular ⇒ **decoupled**. Same axiom-1 status as A, but a far lower information content.

## 3. Information-content check (Axiom 2)

`I = log₂(system range / common range)` — bits the pipeline must supply.
Measured/estimated ranges:

| Stage | system range | common range | I (bits) |
|---|---|---|---|
| FR2 outputs in window (Design A) | ~130 M outputs (26 k blk × ~2 k tx × ~2.5 vout) | ~3 k in-band outputs | **≈ 15.4** |
| FR3+FR4 (Design A) | ~3 k | ~50 | ≈ 5.9 |
| FR2+FR4 combined (Design B) | 56,795,328 funded scripthashes | **5,745 measured** | **≈ 13.3** |
| FR1 window filter (Design B) | 5,745 | ~50 | ≈ 6.8 |
| FR5 attribution | ~50 | 1 | ≈ 5.6 |
| **Total** | | | **≈ 26 bits** |

Both designs carry the same ~26 bits — as they must, since they identify the same set.
**The axioms do not separate them; the physical cost does**, and Design B wins on every
physical axis:

| | Design A | Design B |
|---|---|---|
| bytes over the wire | ~26,000 blocks × ~1.7 MB raw ≈ **45 GB** (≈180 GB at verbosity 2) | **5,745** small Electrum queries ≈ a few MB |
| rate-limited calls | ~26 k RPC + ~3 k blockstream | ~5.7 k Electrum + ~50 blockstream |
| reduction factor | — | **~10⁴** |
| executes in sandbox? | **no** (C1) | FR2/FR4 **yes**, FR1/FR3 no |

**Why this matters beyond speed:** Design A's DP1/DP2 are *entirely* blocked by C1, so
Design A delivers zero sandbox progress. Design B's DP4′ and DP6 run offline and
produce a provably-sound narrowing (`W ⊆ T_new`) before the laptop does anything.

### Sanity check on the search direction

The ruled-out brainwallet work searched the *key* space: for a vanity-ground or random
key, `I = log₂(2²⁵⁶/1) = 256` bits. The chain-side search is `I ≈ 26` bits.
That ~230-bit gap is the formal statement of why 64,568 brainwallet derivations
returned 0 hits and why chain-side enumeration is the correct attack.

## 4. Selected design

**Design B**, with Design A retained as an independent fallback/cross-check (it is the
only path that is *self-sufficient on the laptop*, and it validates B's inversion
empirically).

Decomposition by execution locus:

```
SANDBOX (offline, no Bitcoin egress)
  DP4′  scan address_map.bin  -> T   = 5,745 scripthashes @ [19.5,20.5] BTC   [DONE]
  DP6   sweep 784 M-address corpus -> resolve(T), subtract -> T_new           [running]
        ⇒ T_new provably ⊇ W, no false negatives (Corollary)
LAPTOP (has Bitcoin egress)
  DP7   Electrum blockchain.scripthash.get_history over T_new
        -> tx_count, funding height  ⇒ FR1 window filter + FR3               [primary]
  DP2′  Alchemy getblock verbosity 0 + local raw parse over 756k–782k        [fallback]
  DP3   blockstream chain_stats + /txs/chain on the finalists only           [confirm]
SANDBOX
  DP5   attribution scoring -> /tmp/window_candidates.tsv
```

**Decoupling note.** The sandbox↔laptop interface is a single small file in each
direction (`T_new` out, candidate rows back). No FR depends on a DP that spans the
boundary, so the partition does not introduce coupling.

## 5. Design decisions worth recording

1. **`getblock` verbosity 0, not 2.** Raw hex + a local parser moves ~1.7 MB/block
   instead of ~7 MB, a ~4× transfer cut, and yields `scriptPubKey` directly — which is
   the exact preimage of the Electrum scripthash, removing the address encode/decode
   round trip.
2. **Band width.** FR2 says one output ∈ [19.5, 20.5]. An address can receive two such
   outputs in one transaction and still satisfy FR3 (`tx_count == 1`), landing at
   [39, 41] BTC. Bands `b2`/`b3` were extracted (1,766 / 950 entries) so that case is
   not silently dropped.
3. **C4 compliance.** Exact-20.00000000 is 962 of the 5,745 band entries. My band is
   ~6× wider; the 4,783 non-exact entries are work the parallel session cannot reach.
4. **Validation.** Re-deriving the prior session's [19,21] count reproduced **8,053**
   exactly, cross-validating the index reader before any inference was drawn from it.

## 6. Known limitations (stated, not hidden)

- `T_new` is a **superset** of `W`: it also holds wallets funded 2021-01-18 → 2025-10
  outside the window. The window filter is FR1's job on the laptop; the sandbox cannot
  date anything.
- A wallet funded in-window that was **later spent** is outside `W` *by FR3's own
  definition*, and is invisible to both designs. If the puzzle wallet has been swept,
  neither this session nor the parallel one will see it.
- The corpus (C6) is address-level, not UTXO-level; subtraction relies only on
  *appearance*, which is what the Corollary needs.
- `address_map.bin` is a third-party snapshot. It is verified structurally (magic,
  record count, size, CRC-length) and behaviourally (8,053 reproduction), but its
  provenance is not independently audited; the laptop confirmation step re-derives
  every finalist from primary sources.
