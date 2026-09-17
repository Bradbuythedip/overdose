# The funding transaction of candidate #1 (2026-09-17)

User supplied a raw tx hex. Decoded offline (well-formed, 373/373 bytes).

## The transaction

**txid** `d931904b054de23c21efe650843e5adf6d409c6537c792281aad47a07e850dfa`
version 1, locktime 0, 2 inputs, 2 outputs.

```
in [0]  195959af4de6bc00aba0989dc6402ef1fa85fc3f414b46209e02e1b212769c3a:1
        pubkey 02247fd4365fceb03c66643a40839cdc4ee13cd3ea374824e814a3368c946c6720
        => 1A3RB79H2aiacP9YoJu5h14grsC89DJpK4
in [1]  c9f7a370c299ccdb952e5395db3847dd4ef9e0c167506c4a8d93e8c105fd33d1:1
        pubkey 02b2bb89fd735a29dc904a704948761dacf95ff3163b65337e0c7414ab401c82ab
        => 1BCYmbDS58mKdXqefH3xM8CK286sntX4UT

out[0]  20.00000000 BTC -> 1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t   (PRIZE CANDIDATE #1)
out[1]  30.99997382 BTC -> 1GRvQRtrawBYZS6Bo6HSZL7d5ARnHhasds   (change)
```

~51 BTC in, split into an exactly-20 payment and ~31 change. A textbook
personal peel — payment plus change, two inputs, not an exchange sweep. This
confirms the classification `SOLVE_PROMPT.md` gave 1BX2q.

## Offline status of all five addresses (index56m + reachability)

| address | role | index56m | reachable by any derivation |
|---|---|---|---|
| 1BX2qZ9y…X29t | out: 20 BTC prize candidate | FUNDED 20 BTC (unspent) | NO |
| 1GRvQRtr…asds | out: change | FUNDED 30.99997382 BTC (unspent) | NO |
| 1A3RB79H…DJpK4 | in | absent (spent, now empty) | NO |
| 1BCYmbDS…tX4UT | in | absent (spent, now empty) | NO |

reachability checked against 20,086 direct-hash phrases and, behind them, the
project's full derivation history. **We have a key for none of them.**

## What this establishes, and what it does not

ESTABLISHES: 1BX2q's 20 BTC came from a deliberate-looking peel, funded from a
two-input wallet, with ~31 BTC of change. The funding wallet is now exposed
(two input addresses + one change address).

DOES NOT: yield a key. 1BX2q has never spent, so its public key is NOT in this
transaction — this is the funding side. The private key stays unrevealed until
the address spends. And 1BX2q remains 1 of 962 exactly-20-BTC addresses; the
peel shape raises its prior but does not tie it to Keiser.

## The traces that would confirm or kill it (need a block explorer)

1. **Same-wallet test — the decisive one.** Pull the funding txs of the other
   two peel candidates, 1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi and
   1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64. If they share inputs or the change
   wallet with this tx, ONE wallet made all three 20-BTC peels — a deliberate
   setup, near-decisive. If unrelated, this peel is probably ordinary flow.
2. **Trace the inputs backward.** Where did 1A3RB and 1BCYm get their coins? A
   KYC-exchange withdrawal, a known Keiser address, or an El Salvador wallet
   would tie the funder to Keiser.
3. **Trace the change forward.** What did 1GRvQRt (~31 BTC) do next? The change
   address is the strongest fingerprint of the owning wallet; its later spends
   reveal the cluster.
4. **Date the funding.** Block height/time of d931904b. SOLVE_PROMPT.md records
   1BX2q funded 2 Nov 2021 — before the issue reached Bukele (2022-02-11) and
   well before the "20 BTC" announcement (2023-03-04). A funding that predates
   the announcement by ~16 months is consistent with a genuine prize set up at
   publication; it does not prove one.

None of these can run from this container (no Bitcoin network). All are one
lookup each on blockstream.info or mempool.space.

## Derivation tests enabled by the tx (2026-09-17) — all null

Having the funding tx exposed the setter's own wallet material for the first
time, so two derivation families that were never possible before were tried
against the prize address 1BX2q (h160 735f452fed8ca297de0484be1b63200b726077c1)
directly, both compressed and uncompressed:

1. **Self-referential.** 792 constructions from material the setter chose
   BEFORE creating the prize address — the two input pubkeys (full and
   x-coord), the input/change addresses, pairwise concatenations in both
   orders with separators, the pubkey-x XOR — through 6 hashes. None produces
   1BX2q. (The funding txid and prevout txids are deliberately excluded: the
   address exists before the funding, so its key cannot depend on them.)

2. **Article × wallet.** 247 high-prior article phrases (sentences, lines,
   highlight runs, clue words) crossed with the 5 tx elements, 4 join forms,
   2 hashes = 9,880 keys. None produces 1BX2q.

Plus the full corpus + HD stack (`target_sweep --scope all`) against all four
tx addresses: the high-prior corpus (article, n-grams, highlights, persona)
cleared null; the edit1 tail continued low-prior. Planted-key control passed,
so the null is real.

Combined with the earlier reachability checks, every derivation family this
project has — now including ones tying the article to the funder's own
wallet — fails to reach the prize address or any of the four funding-tx
addresses. The tx confirms the prize was set up deliberately; it yields no
derivation foothold.

## "Same key as the funding?" — tested with the curve points (2026-09-17)

One private key yields two addresses (compressed vs uncompressed pubkey), so the
prize could in principle be a funder input's key in the other format. We have
the funder input POINTS, so this is decidable without any private key:

```
input0 1A3RB  compressed -> 1A3RB79H2aiacP9YoJu5h14grsC89DJpK4   (matches, sanity OK)
              uncompressed-> 12sKLJnW68n479mjo1QwpfsNmzfUw1KM34
input1 1BCYm  compressed -> 1BCYmbDS58mKdXqefH3xM8CK286sntX4UT   (matches, sanity OK)
              uncompressed-> 1DxAkYSUxUWyx8e2PdjZqyGDRqDtaELThZ
```

Neither uncompressed twin (nor either compressed form) is 1BX2q (prize) or 1GRv
(change). **The prize is a distinct key from both revealed funder keys.**

Combined with the earlier self-referential tests (792 constructions incl.
sha256 of the funder pubkeys/addresses -> 1BX2q, null), every "prize key = a
function of the funder's known material" hypothesis that is testable offline is
now closed.

What remains, and is NOT offline-testable: the prize and the funder could be
sibling keys of one HD wallet (different keys, one seed). That needs the seed
or an xpub+chaincode+one child priv, none of which we have. It is exactly what
the cluster trace probes indirectly: if 1BX2q was funded from the setter's own
personal wallet, that confirms common ownership -- but common ownership still
does not yield the prize key without the seed. The only paths from "same
wallet" to "the key" are (a) the seed leaking, or (b) a funder address in that
wallet leaking its key via nonce reuse AND the wallet being non-hardened with a
known xpub. Both are long shots, both need the cluster the tracer builds.
