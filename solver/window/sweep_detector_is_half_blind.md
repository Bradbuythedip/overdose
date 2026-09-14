# The sweep detector can only see sweeps that happened after the snapshot (2026-09-14)

## The constraint nobody wrote down

`chain_tail_scan`'s SWEEP detector matches a revealed pubkey against
`load_targets()` — the 795 scripthashes in `window/Tnew_exact_20.tsv`, each of
which held **exactly 20.00000000 BTC as of the `address_map.bin` snapshot,
2025-10-11** (~block 918,388).

For the detector to fire, an address must satisfy both:

1. **held 20 BTC on 2025-10-11** — otherwise it is not in the 795, and
2. **was spent inside the scanned range** — otherwise there is no sweep.

Those two are simultaneously satisfiable **only for blocks after ~918,388.**
Before that date, any address that had already been emptied has a zero balance
at snapshot time and is therefore absent from the target list.

> Running the SWEEP detector on blocks below ~918,388 is guaranteed to return
> nothing. Not because nothing happened there — because the target list excludes
> by construction every address that was already empty when it was built.

That reframes the earlier result. The scan over 918,000+ found 1,449 SWEEP
records; that is not evidence that sweeping concentrates there. It is the only
region in which the detector is capable of producing a record at all.

## What it does NOT invalidate

The 64 swept-once addresses remain a live test, and this is the distinction that
matters:

- membership in the 795 constrains **when the address was emptied** (after
  2025-10-11), and says **nothing about when it was funded**
- so one of those 64 could have been funded in 2021, sat dormant across the
  announcement, and been claimed last month — which is precisely the prize
  profile

Dating them is therefore the right test, and it is what `age_check.py` does now
that `chain_tail_scan` records each sweep's `prev_txid`. A `PRE-PRINT` or
`PRE-ANNOUNCE` row is the lead; all-`RECENT` closes the hypothesis for this
window.

## The hole that remains

The announcement was 2023-03-04, block ~782,000. The snapshot is block
~918,388.

```
782,000 ....................................... 918,388 ......... tip
|<--- 136,000 blocks, ~2.5 years, UNDETECTABLE --->|<-- detector works -->|
```

A prize solved and swept inside that 2.5-year span leaves **no trace any oracle
in this tree can find**:

- it is absent from `address_map.bin` (zero balance on 2025-10-11)
- it is absent from the 795, so the SWEEP detector cannot match it
- it is absent from the April-2023 rich list too, if it was swept before
  April 2023

And that span is the *most* likely time for a claim, because it opens the moment
Keiser publicly attached 20 BTC to the puzzle and attention peaked.

## What would actually close it

`hist_index.py`'s own docstring already states the requirement and is worth
quoting, because it was written before anyone connected it to this detector:

> a null from this index means "not rich in April 2023", and a null from both
> means "not holding coins at either of two moments". Neither means "never
> funded". Closing that properly needs **every output ever created** — a full
> chain scan or an ever-used-address dump — which is not in this tree.

Two balance snapshots are two instants. The question "was this address ever
funded" is about an interval, and no number of instants answers it.

So the delta index described in the plan is the right structure but was aimed at
the wrong window. Pointed at blocks 782,000 → tip rather than only at the
post-horizon tail, an ever-funded set of scripthashes answers the sweep question
and the staleness question at once — and it is the only construction here that
can return a null meaning *"never funded"* rather than *"not funded on one of
two particular days."*
