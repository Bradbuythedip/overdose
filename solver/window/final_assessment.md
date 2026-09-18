# Final assessment (2026-09-18)

What the evidence supports, with the numbers, so the project has a defensible
position rather than an open-ended search. Everything here is measured or
cited; where a figure is an estimate it says so.

## 1. The derivation count, reconciled

The repo quotes 69M, 72M, 75M, 100M, 150M and 350M in different places. Only
one is auditable: `STATUS.md`'s own table, summed exactly:

```
12 corpora, 485,606 phrases -> 67,031,575 addresses, 0 hits
plus ~2,600,000 from the earlier big-corpus sweep
TOTAL  ~69,600,000 derived addresses
```

**Use ~69M.** The larger figures are rolling prose estimates with no itemised
backing. This matters because the whole argument turns on what the nulls cover,
and an inflated count makes the search look more exhaustive than it is.

## 2. The reframe: the detector was the constraint

Every one of those ~69M derivations was judged by `/tmp/address_map.bin`, the
**UTXO set as of 2025-10-11**. `STATUS.md:57-70` states the consequence itself:

> every "0 hits" means *no address that still holds coins*. It does NOT rule out
> a key that was funded and swept before then -- **which for a magazine-printed
> key is the most likely history of all**.

Its control: 32 famous brainwallet phrases x 2 pubkey forms = 64 addresses,
every one demonstrably funded once and drained, **0 of 64 in either offline
index**, genesis in both. `window/index_horizon.md` adds a second gap: the
snapshot is eleven months stale, so anything funded since is invisible too.

About 460M addresses have ever held a balance; about 56.8M still do. **The
detector has been seeing roughly 12% of the relevant space.** For the most
likely history of the prize, a correct derivation and a wrong one produce
identical silence. Four years went into the generator; this was never the
generator's problem.

`everused.py` closes it, with the control that matters -- one that
*discriminates* the two oracles rather than merely firing: the swept brainwallet
is present in the ever-used index and provably **absent** from `address_map.bin`.

## 3. The noise floor is zero, measured

An 80,305,062-address ever-used index (horizon 2021-01-17, control passing):

```
6,429 article phrases -> 225,015 addresses -> 0 ever-used hits
```

I had predicted thousands of false alarms. **That was wrong and the measurement
says so.** Crackers enumerate dictionaries and famous quotes, not arbitrary
multi-word spans of prose: 23 of the ~25 ever-funded phrases this project ever
found were single words, and the article is 0.6% single words against a generic
corpus's 24%. So in a full-horizon run, **any hit is signal**, not noise to be
triaged away.

## 4. What each closed channel actually rules out

| channel | result | what it rules out |
|---|---|---|
| typographic (capitalisation, highlight colour, all-caps, gaps, quotes) | 124 bits total | cannot *carry* a 128-bit key, whatever the encoding. A capacity bound, not a null |
| the 5 discrete channels decoded (Bacon both polarities, ASCII, Morse, BCD, 5/6-bit, BIP-39) | 4,527 decodings, best is a 5-letter word; shuffles produce one 53-71% of the time | no instruction hidden in them |
| Sand (alternate printed lines) and Musset (first word per printed line) on Issue 24's real print lines | every reading within ~0.6 sd of its own shuffled null, none imperative | the one device Keiser named does not fire on the text he pointed at |
| barcode/QR/DataMatrix, 400 dpi, 4 rotations x 6 preprocessings x tiles | 0 payloads, planted control recovered first | the only visual channel with key-capacity is empty |
| all 45 highlight rectangles as symbols | 11.3M scripts, 0 hits, mnemonics at chance | the measured half of the channel that had never been tested |
| the two banknote serials, every framing incl. combined, mirrored, as entropy | ~10^8 scripts | not key material by any reading tried |
| 4,550 most human-choosable strings, live "ever funded" endpoint | **0 ever funded, at any point in history** | the obvious phrases were never the key. This is the single strongest null in the project |

## 5. The three surviving branches, ranked

1. **The key was never funded.** Most probable, and *unfalsifiable from here*.
   No chain oracle can see a key that has no on-chain history. Consistent with
   everything: the emphasis on "physical copy"; his other giveaways being
   physical Opendimes and a quiz that paid out nothing; no address, balance,
   txid or signed message ever published across five statements; the mirror
   tweet being a bare link; "El Salvador is a clue" being a reply quip; and a
   verification question in June 2026 drawing a block on X, a Telegram ban and
   a block from Stacy. The chain-free checksum oracle is the only test that
   touches this branch, and it is null.
2. **Funded and swept.** Previously untestable; **Step 1 of the plan settles
   it** across all ~69M derivations at once.
3. **Funded, unspent, outside the index horizon** (after 2025-10-11, or a bare
   P2PK output which is address-derived-invisible). Step 2 covers the first;
   P2PK is a data-source limit, recorded at `spk_extra.py:11-24`.

## 6. What a hit would mean

An ever-used hit on a drained address is **evidence that the puzzle had a
solution and somebody took it**. That is a result, not a payday, and it should
be written up as one. It would still need: a reproducible derivation from
printed text, a ~20 BTC funding, dates inside Sept 2021 - Mar 2023, and
independent reproduction. Anything less is a brainwallet coincidence, and the
reference class for "exactly 20 BTC" is 962 addresses.

## 7. What remains, and who can do it

Blocked on artifacts, not on tooling or ideas:

- **A print copy of Issue 24.** Serves the physical checks nothing else reaches
  (UV, loupe, tipped-in card, paper stock) and the print-line literary test at
  once. `print_musset.py` takes a line-faithful transcription as readily as a
  PDF.
- **The full ever-used build**, two commands on a machine with network.
- **Keiser stating the address.** One sentence would end the question, and its
  absence across five public statements is itself the most informative fact in
  the record.

No honest work remains that this container can perform alone. Saying so is the
result of the search, not an abandonment of it.
