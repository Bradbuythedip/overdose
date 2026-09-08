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

---

# Second iteration — resolving the coupling that Design B left behind

Design B pushed FR2/FR4 offline but left FR1/FR3 stranded on the laptop, because
the sandbox held **scripthashes, not addresses**, and every Bitcoin API is
egress-blocked. So the binding requirement became a new one, not in the original
decomposition:

> **FR-R** — resolve a scripthash to its address for a wallet created *after*
> 2021-01-17 (the point where the only reachable corpus ends).

## DP candidates for FR-R

| DP | verdict | reasoning |
|---|---|---|
| DP-c live network query | rejected | 403 policy denial (C1) |
| DP-d invert SHA256(scriptPubKey) | rejected | 2^160. Even a 7-char vanity constraint only reduces it to ~2^125 |
| DP-b address-keyed balance index | rejected | `address_map.bin` is built from Bitcoin Core **chainstate**, which stores no addresses — confirmed from upstream README |
| DP-f snapshot bracketing for dates | tested, dead | dated 2023 release tags survive but their assets were consolidated away; probed 8 filenames + READMEs at 3 tags, all 404 |
| **DP-R address+balance corpus on GitHub releases** | **selected** | a reachable data class nobody had used yet |

DP-R works because the constraint is on *hosts*, not on *data*. GitHub releases
are allowlisted, and a 1.6 GB `address,balance` dump of all 56.2 M funded
addresses is served from exactly there.

## Why the second snapshot also strengthens FR3

The resolution corpus is dated **2026-08**; the balance index is **2025-10**.
That mismatch is not noise, it is a second independent FR3 test:

> A wallet satisfying `tx_count == 1 ∧ spent_txo_sum == 0` holds a constant
> balance forever. So it must appear in the band at *both* snapshot dates.
> Anything present at 2025-10 but absent at 2026-08 either spent or received
> again — failing FR3 either way.

So the 889 unresolved scripthashes are not a coverage gap; they are **excluded
by FR3**. Resolution and filtering turned out to be the same operation.

## Updated design matrix

| | DP4′ band scan | DP6 corpus subtract | DP-R address resolve | DP-A address_check | DP5 rank |
|---|---|---|---|---|---|
|FR4| **X** | 0 | 0 | 0 | 0 |
|FR2| **X** | **X** | 0 | 0 | 0 |
|FR-R| **X** | **X** | **X** | 0 | 0 |
|FR3| **X** | 0 | **X** | **X** | 0 |
|FR1| 0 | **X** | **X** | **X** | 0 |
|FR5| **X** | **X** | **X** | **X** | **X** |

Still triangular ⇒ decoupled. The first four columns are now **entirely
offline**; only DP-A needs the network, and it needs one cheap address query
per candidate instead of 26,000 block fetches.

## Information-content ledger (measured, not estimated)

| stage | set | bits |
|---|---|---|
| all funded scripthashes | 56,795,328 | — |
| band [19.5, 20.5] BTC | 5,745 | 13.3 |
| − pre-2021 corpus (Corollary) | 3,448 | 0.7 |
| − failed cross-snapshot FR3 | 2,559 | 0.4 |
| exactly 20.00000000 | 212 | 3.6 |
| legacy P2PKH | **68** | 1.6 |
| **extracted offline** | | **19.7** |
| remaining: window date + funding source | | **~6.1** |
| **total** | | **≈ 25.8** |

Section 3 predicted ≈ 26 bits for the whole problem from first principles. The
measured total is 25.8. The estimate held.

## Result

FR-R is solved. 2,559 candidates in plaintext, ranked into tiers; the top tier
is **68 addresses** that are simultaneously exactly 20.00000000 BTC, legacy
P2PKH, created after 2021-01-17, and unmoved across two independent snapshots
13 months apart.

## Negative results worth recording

- **No Keiser-token vanity match** among any of the 2,559 candidates, nor among
  the 3,345 pre-2021 addresses recovered earlier. The FR5 vanity signal is
  exhausted: if the puzzle wallet is in this set, it does **not** advertise
  itself in its address. Ranking must come from funding date and funding source.
- Address-type distribution of the candidates is 59.5 % P2WPKH, 21.2 % P2SH,
  12.1 % P2PKH — i.e. the legacy-P2PKH tier is a genuine 8× enrichment over
  base rate, not an arbitrary cut.

---

# Where the offline path terminates

The remaining ~6.1 bits are the funding **date** and the funding **source**.
Every offline DP for the date was enumerated and tested:

| DP for FR1 (date), offline | outcome |
|---|---|
| snapshot bracketing via dated 2023 releases | **dead** — tags survive, assets were consolidated away (8 filenames + 3 tag READMEs probed, all 404) |
| snapshot bracketing via 2024 monthlies | **dead** — no assets under those tags either; and a 2024-01 bound would not isolate a 2022-10..2023-04 window regardless |
| published UTXO dump carrying per-output height | **dead** — chainstate *does* store each UTXO's height, and for an FR3 wallet that height is exactly the funding height, but every result is a *tool* to produce such a dump, not a published dump. `seed-safe/btc-balance` is balance-only |
| address corpus preserving first-appearance order past 2021 | **dead** — the ordered corpus (Qalander) ends 2021-01-17; no successor found |

So FR1 is not solvable from an environment with no Bitcoin egress. That is a
constraint, not a gap in the method: **nothing reachable carries a date.**

## Final negative results

Three checks that close off search directions, all run against the resolved
candidate set:

1. **Brainwallet cross-check.** Intersecting all 64,568 previously-derived
   addresses with the 2,559 candidates gives **0 hits**. This independently
   confirms the prior session's balance-index result by a completely different
   route, and supports the conclusion that the key is random rather than the
   hash of any phrase in the article.
2. **Semantic scan.** Against a 344,415-word English dictionary, **0 of 2,559**
   candidate addresses contain an embedded word of 7+ characters. Combined with
   the token scan, the "the address advertises itself" hypothesis is dead in
   this set.
3. **XXX-prefix scan.** 0 candidates match the prior session's `1xxx`/repeated-
   character pattern.

## What the last step costs

68 addresses × one `blockstream.info/api/address/:a` call ≈ one minute
(`address_check.py`). That call returns `chain_stats` (FR3), the funding
txid, its height and timestamp (FR1) and the value (FR2) — i.e. all ~6.1
remaining bits except the funding-source trace.

---

# The "mirror" hypothesis, sourced and tested

## Sourcing first

The mirror idea traces to three things, and none of them is Keiser hinting at a cipher:

| claim | what it actually is |
|---|---|
| "Keiser hinted at mirror writing" | the repo README attributes this to **"User hint"** — the operator's hypothesis, not a Keiser statement |
| Keiser's *"Bitcoin Is A Mirror That Reveals All"* | published **2024-06-01**, in the Inscription Issue — **15 months after** the puzzle. Its "mirror" is a self-help metaphor about confronting yourself. It cannot be a hint for a March-2023 puzzle |
| the Finlow-Bates Medium piece | about **his own** treasure hunt (8 keys, 0.002 BTC each, hidden in his book), not Keiser's mechanism |

What *is* sourced: the announcement was a **7-note Nostr thread** ("check out the pages in...") — matching the 7 page images in this repo. The `nevent` decodes to event id
`2d73d71321d5ee832f170f40dc025812718aa673a4a7acf0cb5312653f2d1240` on relay
`wss://nostr.wine`, and carries no author-pubkey TLV. WebSocket is unsupported through
the proxy, so the thread body is unreachable from here.

## The one exotic mechanism the word actually maps onto

In Bitcoin there is a real mirror: **secp256k1 negation**. Every key `k` has a
partner `n − k`; their public keys share an x-coordinate with flipped y. For a
compressed key the mirror is literally the prefix byte `02 ↔ 03` — no elliptic-curve
multiplication at all.

Verified both ways before use: prefix-flip ≡ `n − k` scalar multiplication, for
compressed and uncompressed forms.

All prior work mirrored the **text** (reversed strings, atbash, ROT13, word order)
and then hashed. Nothing mirrored the **key**. That is a genuine untested half of
the space, and it is nearly free.

## What was run

`mirror_check.py`, entirely offline against `address_map.bin`:

- 8,490 candidate phrases × 16 hash variants
- × 5 key involutions: identity, byte-reversal, bitwise complement, 256-bit
  reversal, hex-nibble reversal
- × 2 curve orientations: `k` and `n − k`
- × 4 address types (P2PKH compressed/uncompressed, P2WPKH, P2SH-P2WPKH)

**679,200 keys → 5,433,600 addresses → 0 hits.** An ~84× expansion of the prior
64,568-address search.

## Positive control (so the zero means something)

| address | index says |
|---|---|
| genesis `1A1zP1eP…` | 54.38462888 BTC |
| tier-1 candidate `125dqocB…` | **20.00000000 BTC** |
| tier-1 candidate `1x495Vm3…` | **20.00000000 BTC** |
| `1JwSSubhmg…` (*correct horse battery staple*) | 0 — correctly drained |

The oracle fires. The zero is a real negative, not a broken lookup. Note the third
row is the exact address `mirror_check.py` derives from that phrase, so the
derivation path is demonstrably live.

## Conclusion

The "private key is a hash of some text in the article" family is now very hard to
sustain: 64,568 addresses previously, 5,433,600 now, including the full curve-mirror
space. Combined with the vanity-prefix and dictionary negatives, the chain-side
68-address path remains the live one.

## Untested hypotheses worth passing to the image-analysis track

- **BIP38.** An encrypted key prints as a 58-char string starting `6P`. This would
  explain every failed WIF/hex extraction: the printed string is not a key until a
  passphrase is applied. **Grep the OCR output for `6P`** — cheap and decisive.
- **7 shares.** The announcement was 7 notes and there are 7 page images; a split
  secret (Shamir, or plain concatenation across pages) fits that shape.

---

# The cipher: Keiser's hint is real. The WEIGHT reading is NOT confirmed (see correction below)

## The hint is sourced

Correcting my previous entry. Keiser **did** state the method, in
[tweet 1607378060172460032](https://x.com/maxkeiser/status/1607378060172460032),
December 2022:

> "Have you ever picked up a physical copy of @BitcoinMagazine and read my column
> and Like George Sand's hidden cryptography, I have hidden private keys in the text."

Two details matter: **"keys" is plural**, and it says **"my column"** — so this may
span more than the Overdose piece. George Sand's trick is a null cipher: an
innocent surface text carrying a hidden message at marked positions.

## What the marking actually is

Not position — **weight**. Individual characters are set in a heavier face
*mid-word*, which no ordinary emphasis does. Confirmed by eye at 5–6× zoom on
native-resolution crops (`window/z_being.png`, `window/z_ripped.png`):

| word | reading |
|---|---|
| `skin being` | "skin" light; in "being", **b e i** heavy, **n g** light — the bolding stops mid-word |
| `ripped` | "r" light, **ipped** heavy |
| `central` | "c" light, **e** heavy, "ntra" light, **l** heavy |
| `bankers` | **b** heavy, "an" light, **e** heavy, "rs" light |

So the payload is the ordered sequence of heavy characters in the body text.
**This is a different set from the orange/black highlights** that earlier work
extracted (645 chars, no WIF/hex found). The highlights are design; the weight is
the cipher.

## Honest status of the detector

`bold_extract.py` segments lines and glyphs and measures per-glyph stroke width
(median horizontal ink-run length) rather than ink density, since density
confounds letter shape with weight.

It is **not reliable yet**, and should not be trusted as-is:

- at 1.2σ it under-detects (finds `ripped`'s **e** and `central`'s **e**, misses the rest)
- at 0.2σ it over-detects badly (271 flags/page; it boxes most instances of
  `e`, `s`, `o` regardless of weight)
- root cause: at 1800 px page width, regular strokes measure ~3 px and bold ~4–5 px,
  so **letter identity dominates the signal**. There is no clean global threshold.

The fix is one of: higher-resolution scans; or OCR each glyph and normalise its
stroke width against the median for *that same letter* elsewhere on the page,
which removes the shape confound. The second is the cheap one and is the
recommended next step.

## Why this matters for the search

If the payload is a passphrase rather than a raw WIF, it feeds straight into the
existing offline oracle (`address_map.bin`) — no network needed. Note the bold
characters observed so far include `l` (lowercase L), which is **not valid
base58**, so the extracted string is unlikely to be a WIF directly; a passphrase
or an intermediate encoding is more likely.

---

# CORRECTION: the weight-marking reading is not safe

I previously reported the marking as a per-character bold null cipher. On further
examination that conclusion was **overstated**, and a more parsimonious
explanation fits the same evidence.

## The competing explanation

Look at *which* spans are heavy on page 76:

> "UTXO ghetto up in here", "George Clinton", "James Brown", "shitcoiners'",
> "nocoiners'", "El Salvador", "President Nayib Bukele", "IMF", "Mike Novogratz",
> "being ripped ... central bankers"

These are **names and vivid phrases** — ordinary editorial emphasis. And the piece
is deliberately styled as a distressed, photocopied typewriter document (torn
edges, uneven strike, mottled stock). A distress effect produces per-glyph weight
noise, which makes an emphasis run *look* like it stops mid-word.

Under that reading, `bei|ng`, `r|ipped` and `Cl|inton` are ink/print variation at
the edges of genuine emphasis spans, not cipher marks.

## What the evidence actually supports

| observation | cipher reading | editorial + distress reading |
|---|---|---|
| heavy spans are names/vivid phrases | unexplained | **expected** |
| "It's funkier than a whole parallel universe..." uniformly light | expected | **expected** |
| `bei` heavy / `ng` light within one word | expected | possible (edge noise) |
| long heavy runs (18+ chars) | awkward | **expected** |

The editorial reading explains more of the data. I cannot rule the cipher reading
out, but I should not have asserted it.

## Why the tooling could not settle it

- fixed-pitch cell alignment fails: no (pitch, offset) makes space cells clean,
  so the face is not reliably monospace at this scan quality
- per-glyph segmentation merges ~10% of characters (41 blobs for 46 non-space
  characters on a validated line)
- stroke width at 1800 px page width is ~3 px regular vs ~4-5 px bold, so letter
  identity dominates the signal and no global threshold separates the classes

## What would settle it

1. **Higher-resolution scans** (600+ dpi). At 3 px stroke width the question is
   simply not decidable.
2. **OCR with per-character bounding boxes**, then normalise each glyph's ink mass
   against the median for *that same letter* elsewhere on the page. If two real
   font weights exist the per-letter distribution is **bimodal**; if it is
   distress noise it is unimodal. That test is decisive and cheap once boxes exist.

## What survives

Keiser's hint itself is solid and still points where the workflow is already
looking: a **positional** null cipher over the body text (every Nth line/word/
letter, acrostics), which is George Sand's actual method. Nothing here undermines
that line of attack — it only removes "character weight" as a shortcut to it.

---

# George Sand positional extractions: run, and negative

## Transcription

All five body pages (75–79) transcribed by direct vision read of the scans, with
**line breaks preserved exactly as printed** — `solver/transcript/p75..p79.txt`,
142 lines. Line structure is the whole ballgame for a positional cipher, and OCR
on this distressed typewriter face reflows lines badly, so this transcript is
likely more faithful than an OCR pass.

Layout notes that matter: page 76's top block is **centre-aligned** with hand-set
breaks; page 79's main paragraph is set on a **curved baseline**; page 77's final
paragraph is **justified** (which is what produces its irregular letter spacing —
typographic, not cipher).

## Extractions run

`gsand_extract.py`, offline against `address_map.bin`:

- first/last letter per line; first/last word per line
- every Nth line (N=2..10), first letter
- every Nth word (N=2..10), first letter
- every Nth character (N=2..10)
- alternating lines at both offsets — **George Sand's actual method**
- capitals only; digits only
- every one of the above also reversed

74 rules × 6 sources (5 pages + combined). Each output tested as
(a) a brainwallet passphrase across 16 hash variants × 5 key involutions × both
curve orientations, (b) raw hex at every 64-char offset, (c) WIF at every valid
51/52-char offset.

**49,562 keys → 0 hits.**

## Also negative: no readable acrostic

`first_letter_per_line` over all 142 lines gives
`HtRTMtaaataoIBacLFtItVNDKGtYhwtaGBIbnrGnshTcObplADHtHIh$bclNbhM...` — no English.
`digits_only` gives `20081111971101201114220000100000201712000518525195196910`,
which is simply the article's years and figures (2008, 1971, 2011, 42, 2017,
51, 85, 1969) — not key material.

## Bounds on this negative

It is only as good as (a) the transcription and (b) the rule set. Not covered:
display type (the "BITCOIN IS TOXIC AF" head, the hand-drawn scrawls, the
signature), word-level rather than letter-level acrostics, rules keyed to the
highlight colours, and any rule needing the physical page (column position,
line number on the printed page rather than in my concatenation).

The hand-drawn scrawls read **"SHIT"** (p77) and **"X FUCK ALL X"** (p78) — the
source of the "shitfuckall" candidate the cipher panel already tested.

---

# Closing out the weight question: the scans cannot answer it

Two further tests were run to settle whether the heavy characters are a cipher or
editorial emphasis. Both are reported because both constrain the answer.

## Test 1 — bimodality per letter

Method avoids OCR *and* pitch fitting: segment glyphs per line, keep only lines
where the glyph count **exactly equals** the transcription's non-space character
count (36 of 93 lines), which makes letter assignment unambiguous. Then compare
ink mass across instances of the same letter.

Result: distributions are **unimodal with a long right tail**, with a weak
secondary bump near 1.3–1.6x for `a`, `i`, `l`. A bold class plainly exists — but
that was never in doubt ("El Salvador", "IMF" are visibly bold. Bimodality was
the wrong question.

## Test 2 — run length and word alignment (the right question)

Editorial emphasis produces long, word-aligned runs. A per-character cipher
produces scattered singletons. Sweeping the heavy-threshold:

| threshold | heavy % | runs | single-char % | word-aligned % | max run |
|---|---|---|---|---|---|
| 1.20 | 32.4 | 144 | 51.4 | 4.2 | 33 |
| 1.40 | 20.9 | 124 | 56.5 | 0.8 | 17 |
| 1.60 | 12.6 | 103 | 73.8 | 1.0 | 15 |
| 1.80 | 6.7 | 72 | 81.9 | 2.8 | 5 |
| 2.00 | 3.4 | 34 | 79.4 | 8.8 | 5 |

**Word alignment never exceeds 9% at any threshold.** But I can see by eye that
"El Salvador", "IMF" and "President Nayib Bukele" are bold *and* word-aligned.
The measure therefore is not capturing the real bold class — it is measuring
print and scan noise, whose extreme tail is naturally isolated singletons.

## Conclusion

This is a negative about the **method**, not about the puzzle. At 1800 px page
width (~3 px regular vs ~4–5 px bold strokes) glyph weight is not measurable
reliably enough to decide the question, by any of the three approaches tried
(density, stroke width, per-letter normalised ink mass).

The qualitative evidence still favours **editorial emphasis**: the phrases that
read as bold to the eye are semantically coherent (names, vivid images), which is
what emphasis looks like and is not what a cipher would produce.

**Only a higher-resolution scan (600+ dpi) can settle it.** Until then the weight
channel should be treated as unresolved, and not as a confirmed cipher.

# Banknote serials

Pages 73 and 74 photograph the same $100 note (page 73's copy is mirror-flipped).
Serial **CL 76841714 A**, district **L12**. 58 candidate strings derived from it
(case variants, reversals, with/without district, concatenated with article
phrases) × 16 hash variants × 5 key involutions × both curve orientations
= 4,642 keys → **0 hits**.

Noted and deliberately down-weighted: `768417` is a valid block height inside the
puzzle window (≈ late Dec 2022). This is almost certainly coincidence — it is a
post-hoc match on 6 digits of a stock-photo serial, and the causality runs
backwards, since the Fall-2022 article predates that block. Cheap to check in a
block scan; should not be weighted.

# Text scan for encoded key strings

The 142-line transcript contains **no** BIP38 marker (`6P…`), no base58 run of 40+
characters, and no hex run of 32+ characters. The longest alphanumeric tokens are
ordinary words (`hyperbitcoinized`, `simultaneously`, `DEMONETIZATION`). If a key
is present as a literal string, it is not in the body text as transcribed.
