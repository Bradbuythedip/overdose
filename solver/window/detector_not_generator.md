# The detector was the constraint, not the generator (2026-09-18)

Four years of this project optimised the **generator**: more phrases, ciphers,
serial framings, line devices, readings. This pass optimised the **detector**,
because that is where the problem is, and the repo's own notes said so.

## The measurement that reframes every null

Every sweep here -- **69M audited derivations** across 12 corpora
(`STATUS.md:73-88`) -- was judged by `/tmp/address_map.bin`: the UTXO set as of
**2025-10-11**, 56,795,328 scripthashes. `STATUS.md:57-70` states the
consequence itself:

> every "0 hits" means *no address that still holds coins*. It does NOT rule out
> a key that was funded and swept before then -- **which for a magazine-printed
> key is the most likely history of all**.

with the control: 32 famous brainwallet phrases x 2 pubkey forms = 64 addresses,
every one demonstrably funded once and drained, **0 of 64 in either index**,
genesis in both. `window/index_horizon.md` adds the second gap: the snapshot is
eleven months stale, so anything funded since is invisible too, and for that case
*"the solver would miss the prize while holding the correct key."*

About **460M** addresses have ever held a balance; about **56.8M** still do.

> **The detector has been seeing ~12% of the relevant address space.** For the
> most likely history of the prize, a correct derivation and a wrong one produce
> the same silence.

`window/what_the_nulls_prove.md` ranked the swept-key hypothesis the #1 open
question and assumed settling it required per-address transaction-graph
forensics on the 962 exactly-20-BTC addresses. It does not. A set of every
address ever used makes all 69M existing derivations testable against the swept
case at once, with no new derivations.

## What was built

`everused.py` -- a membership index over every address ever used:
`address -> scriptPubKey -> sha256 -> 8-byte prefix`, partitioned into 256
buckets by leading byte and sorted within each, so a lookup touches one bucket
with bounded RAM and no k-way merge. Unparseable lines are counted and reported,
never silently dropped (the flaw at `hist_index.py:42,52-53`). Balance is
reported as `None` -- "unknown", never `0`, which would read as "unfunded".

Wired into `continuous_solver.IndexOracle` as an opt-in tier
(`OVERDOSE_ORACLE=everused`) with its own name, so ~12 downstream scripts
inherit it and **no existing ledger row silently changes meaning**. When the
index is absent it falls back with an explicit reason rather than answering the
old question under the new name.

### The control that licenses any null from it

It must **discriminate the two oracles**, and it passes:

```
the swept brainwallet is found: OK
the swept control is ABSENT from address_map.bin: OK
```

`sha256('correct horse battery staple')` -> an address with 148,425 fundings and
a zero balance today. Present in the ever-used index, absent from the balance
index. That is the blind spot, demonstrated rather than argued. Also asserted:
genesis present, a fresh random address absent, and a hit reporting `None`.

### Status

The builder and the oracle tier are committed and selftested. The **full build
needs the user's machine** -- this container is blocked from the bulk dump hosts.
A partial build from a reachable mirror is running here as proof of pipeline;
its horizon is 2021-01-17, *before the article existed*, so it cannot contain the
prize and is only a base-rate calibration.

## Track 3: the one visual channel with enough capacity

The 124-bit capacity bound closes every typographic channel: they cannot hold a
128-bit key. A machine-readable code can. The only symbol-decoder pass ever run,
`qr_hunt.py`, ran on the **215 dpi phone JPEGs** at 2026-09-14 15:02 -- three and
a half hours *before* the 400 dpi renders existed -- and was never pointed at
them.

| item | result |
|---|---|
| QR / barcode over the 400 dpi renders of pages 73-79, 4 rotations x 6 preprocessings x adaptive scales, full page + 16 tiles | **0 payloads on all 7 pages**, planted-QR control recovered both plants first. Null at the better resolution |
| the p74 boxer logos | a **repeating textile print of identical glyphs**. Identical symbols in a lattice carry no alphabet, so there is nothing to decode; the "14-15" count in the record is visibility under drape, not a symbol count |
| all 45 highlight rectangles (`reading_bars45.py`, `bars45.tsv`) | `bars.tsv` held only the 22 orange; the 23 knockout bars are not colour-separable by `bar_geometry.py`'s method, so half the channel had never been captured. Full set now swept as colour streams, Bacon both polarities, Morse, quantised widths/heights, RLE, wordlist indices in four languages, gaps: **11,308,200 scripts, 0 index hits**, 32 checksum-valid mnemonics vs **30.5 expected by chance** |

Capacity, stated honestly: 45 symbols over a 3-letter alphabet is ~71 bits, over
2 letters 45 bits. Neither can carry a key. They were swept because they could
carry a pointer, and because leaving the measured half of a channel untested is
how a project convinces itself something is closed when it is not.

## What this does and does not buy

It eliminates one of the three live branches: *funded and swept before the
snapshot*, the most probable of them and the only one no sweep here could ever
have seen. It does not touch the branch that no chain oracle can ever reach --
**the key was never funded at all** -- for which the chain-free checksum oracle
remains the only test. An ever-used hit on a drained address would be evidence
that the puzzle had a solution and somebody took it. That is a result, not a
payday, and it should be written up as one.

## Base rate measured: it is zero, and that corrects my earlier warning

A 30-file ever-used index was built here from a reachable mirror
(`raw.githubusercontent.com/Qalander/bitcoin-all-addresses`): **80,305,062
addresses ever used**, horizon 2021-01-17, control passing (the swept
brainwallet present here, absent from `address_map.bin`).

Its horizon predates the article's publication, so it CANNOT contain the prize.
What it can do is measure the false-alarm rate, and that number was unknown:

```
6,429 article phrases (lines, sentences, paragraphs, 2-6-grams)
  -> 225,015 addresses
  -> 0 ever-used hits
```

**I predicted "tens to a few thousand hits, dominated by generic phrases".
For this corpus that was wrong, and the measurement says so.** The reason is
already in `window/swept_key_untested.md`: brainwallet crackers walk
dictionaries and famous quotes, not arbitrary multi-word spans of arbitrary
prose. Of the ~25 distinct ever-funded phrases that pass had found, 23 were
single words. The article is 0.6% single words; a generic corpus is 24%.

The consequence is favourable and worth stating plainly: **for article-derived
phrases the noise floor is zero, so in the user's full-horizon run any hit is
signal rather than something to be triaged away.** The triage ladder still
applies to what a hit means, but the expectation of drowning in false alarms
was unfounded.
