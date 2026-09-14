# Narrowing the chain side cannot help (2026-09-14)

The tail scan produced a clean funnel on the first 1,037 blocks:

```
674 findings
  -> 399 distinct scripthashes paid ~20 BTC
     -> 298 EMPTY      everything that arrived has been spent
        94 OTHER       holds something, but not ~20 BTC
         6 HOLDS_NEAR_20
         0 HOLDS_EXACT_20
```

Six candidates out of 399. The filter works. Then the decisive test:

| address | BTC | tx | in index? |
|---|---|---|---|
| `bc1ql6mjsgtkh0z9x7h9e7yt2gdcgqak7uzv8s7h4c` | 20.00000624 | 3 | **IN** |
| `bc1pw34cpfs899qcc490ge9m5jcrc7q96v20cz52qp6y2zd90fm9gjeswacsz7` | 19.99880804 | 2 | **IN** |
| `bc1qwsh978w5hu04prym3z0chu0w8fh5yhtwf5yrep` | 20.05297162 | 4 | **IN** |
| `bc1qslh5tk2l384p8xqdm2yg7lvr8h6gsnnfey2w8v` | 20.00000624 | 3 | **IN** |
| `3KPHPMN7wxqAjwHfnSQ45bKocViTe5pJMx` | 19.99981322 | 1 | **IN** |
| `bc1qwxgwpr3j98xk890cz2v4qrnz2vqncyk2gaaqj2` | 20.00267853 | 3 | **IN** |

**Six of six are already inside `address_map.bin`.**

## What that means

The index holds ~56,000,000 addresses with a non-zero balance, and roughly
150,000,000 derivations from this article have been tested against it with zero
hits. So every one of these six has *already* been implicitly tested against
every phrase, n-gram, cipher, line device, BIP-39 window, persona string, KDF
and edit-1 variant this project has ever produced.

The shortlist is not new information. It is six addresses we have already failed
to derive.

And the argument generalises, which is the point:

> **If the prize exists and still holds coins, it is in the index. If it is in
> the index, 150M derivations have already failed to reach it. Therefore no
> amount of narrowing the CHAIN side can produce a lead.**

The bottleneck was never which addresses to look at. It is that nothing derived
from the article reaches any funded address at all.

## The one thing the chain side CAN still answer

There is exactly one gap in that argument, and it is the hypothesis
`swept_key_untested.md` reopened.

A swept address has a zero balance. `address_map.bin` is a balance snapshot, so
a swept address is **absent from it**. That is the single case the offline
oracle is structurally blind to, and therefore the single case where walking the
chain sees something the index cannot.

Which inverts the emphasis this scanner was given. The FULL detector — outputs
still holding ~20 BTC — is redundant with an index we already sweep against. The
SPEND detector — a known exactly-20 address being emptied — is not redundant
with anything, because the moment it is emptied it leaves the index forever.

Both are kept. But the one that can still teach us something is the one looking
at coins that have left, not coins that are sitting there.

## Caveat, stated rather than buried

This rests on `address_map.bin` covering all non-zero balances rather than being
a rich list with a floor. Six of six hits at ~20 BTC is consistent with full
coverage and, for a 20 BTC prize specifically, a floor low enough to miss it is
implausible. It has not been independently verified, and a small-balance test
would settle it.

## Consequence

Effort spent refining which 20-BTC addresses to look at is effort spent on the
half of the problem that is not the constraint. The derivation side is the
constraint, and the families that remain genuinely untested there are the ones
`mega_solve.py` covers: the complete single-transcription-error neighbourhood
(`edit1`, `edit1_all`), not another pass over the chain.
