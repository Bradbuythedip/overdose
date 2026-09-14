# The offline index is eleven months stale (2026-09-14)

## The measurement

`/tmp/address_map.bin` carries its snapshot date in its own header:

```
magic   AMAP\x01\x00\x84\x00
offset 60 -> 1760205236 -> 2025-10-11 17:53:56 UTC
```

Matching `DESIGN_window_scan.md` line 31, which records it as measured. Today is
2026-09-14 and the chain tip is 966,916, so:

```
elapsed        337 days  ~= 48,528 blocks
INDEX HORIZON  ~block 918,388   (+/- a few hundred for block-time variance)
```

**Blocks 918,388 – 966,916 are not in the index and never have been.**

## Why this matters more than it looks

`IndexOracle("index56m")` is the oracle behind **every one of the ~150,000,000
derivations** in this project. It is how `continuous_solver`, `mega_solve`,
`basic_crypto`, `highlight_sequence` and every ad-hoc sweep decide whether a
derived address holds anything.

An address funded after 2025-10-11 is absent from it. So for that case:

> **the solver would miss the prize while holding the correct key**, and every
> null it has produced is uninformative.

## What it corrects

`chain_side_is_redundant.md` argued, from six shortlist addresses all being
present in the index, that narrowing the chain side cannot produce a lead —
because anything still holding coins is in the index, and the index has already
been swept 150M times.

That argument is **sound only up to the horizon**. Those six were funded at
blocks 830,780–831,381, i.e. February 2024, comfortably inside the snapshot, so
the test could not have detected the staleness. Splitting the tail scan's
window:

| range | blocks | share | status |
|---|---|---|---|
| 830,000 – 918,388 | 88,388 | 65% | index covers this; chain side redundant, as argued |
| **918,388 – 966,916** | **48,528** | **35%** | **index-blind; the chain is the only oracle** |

So the conclusion inverts in the last third of the window. That is also the only
structurally non-redundant thing the FULL detector can produce — alongside
sweeps, which leave the index permanently and were always non-redundant.

## Consequence for the scan

`chain_tail_scan.py` currently starts at 830,000 and walks forward, so it
reaches the blind region **last**, after ~88,000 blocks of ground the index
already covers. That ordering is backwards.

Run the blind region first:

```
python3 chain_tail_scan.py --start 918000 --rpc "$B"
```

A `FULL` hit there — an output of ~20 BTC whose scripthash is absent from the
795 — is a candidate **no oracle in this project could ever have seen**, as
opposed to one already implicitly tested and failed.

## Caveat, stated

The horizon is estimated from elapsed days at 144 blocks/day, not read from the
chain. It is accurate to a few hundred blocks, which is immaterial at this
scale; starting at 918,000 is deliberately conservative. The snapshot date
itself is read from the file header and is exact.
