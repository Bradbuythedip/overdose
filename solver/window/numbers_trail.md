# The printed-numbers trail (2026-09-13)

A second solver worked this axis independently and reached "no key". This
records what of that holds up under independent check, what its method could
not do, and what re-examining the scan turned up that neither of us had.

## The inventory is confirmed

21 numbers are printed in the body of pages 75-79. Extracted from this repo's
pixel-verified transcript:

```
2008 1 1 1 1971 10 1 2011 1 42 20000 100000 2017 12000 51 85 2 51 95 1969 10
```

This matches the other solver's list **exactly**, including the three "Layer 1"
ones and both occurrences of 51. `gen_numbers.py --selftest` re-derives it from
the transcript and refuses to run if the hardcoded table drifts.

## Its four addresses are genuinely dead — verified here

Screened against this repo's offline indices, with the genesis coinbase as a
positive control:

| address | current | ever funded |
|---|---|---|
| 1GrKpvPyvZKUMB2JTseqPESbhD6MBLEKo2 | not funded | no |
| 19Vh2Y7Lt3wkBh8YY6CxwEaYsNDSMLb4HC | not funded | no |
| 1KHVVYSTsdZkt5kdir1UKZqjQSBgmZWzJK | not funded | no |
| 1QKXPLJPWiiBNvCpa1bMhVttKC4GuiWt6D | not funded | no |
| 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa | 54.38462888 BTC | yes (control) |

## The methodological problem, and the fix

The other solver filtered candidates on a **BIP-39 checksum** and then checked
survivors on chain. It correctly noticed the trap in its own numbers — three
passes from about 45 trials, against an expected 45/16 ≈ 3 — and called it
chance. That is right, and it is worse than it looks: a 12-word checksum is
4 bits, so filtering on it **discards 15 of every 16 candidates**, including
the correct one if the intended index convention differs from the guessed one
by an off-by-one. A filter that weak cannot select, and it can exclude.

The chain is the filter that works. Each derived address tested against
56,795,328 funded scriptPubKeys is roughly a 2^-160 test, so there is no
base-rate problem and no reason to pre-filter at all. **Every candidate is
derived and screened whether or not its checksum passes.**

## What was swept

`gen_numbers.py` enumerates subsets (all 21; the 18 with the Layer 1 labels
dropped; per page; first/last 12; in-range; years; no-years; duplicates
collapsed; every contiguous 12/15/18/21 window), four orderings including
reversed, nine number-to-word-index conventions each in 0- and 1-based form,
every 12/15/18/21/24-word window of the result, a dozen text renderings, the
numbers as positions indexing into the article's own words, and the 56-digit
stream as padded entropy — which the other solver declined to test on the
grounds that 184 bits "should not be padded". That is a taste argument, not
evidence, and padding costs nothing.

Each phrase is expanded by `full_sweep.py` into 7 direct key hashes plus 5 seed
derivations across ~72 HD paths, so every word list is tried both as a mnemonic
and as a passphrase.

| corpus | phrases | addresses | funded hits |
|---|---|---|---|
| numbers trail, first pass | 4,830 | 8,864,090 | **0** |

That pass contains the other solver's exact 18-word mnemonic
(`abstract junk abuse abandon access abandon ahead zoo zoo acoustic zoo alien
appear ability alien armed jungle abuse`) as a verbatim line, so its candidate
is now dead across all 72 paths rather than only at the two addresses it
checked.

## Two things found by re-reading the scan

**The page mapping in this repo was wrong at the front.** PDF page order is
73, 72, 74, 75, 77, 76, 79, 78 — the scan is not in page order and every page
is rotated 180 degrees. Two mask files were misnamed: what was `p73_mask.png`
is magazine page **72**, and what was `p74_mask.png` is page **73**. Renamed.
Body pages 75-79 were correctly labelled, which is why the transcription and
every sweep built on it are unaffected — confirmed by checking the workflow's
page 78 and 79 output line-for-line against the independent transcript.

**Page 72 is a "NUMBERS" department page**, facing the column opener, and its
numbers were never in any inventory:

```
165  572  2020  4.8  930.44  2026  3.9  35.8  2026  14.5  2019
```

It is a different section with its own footer and its own sources, so this is
not Keiser's text. But the column's orange highlight reads "The numbers don't
lie" and the facing department is called NUMBERS, which is cheap to test and
expensive to assume. Swept separately and labelled speculative.

**A second banknote serial exists.** Page 72 carries show-through of the
facing artwork, and in it a serial begins `KB 4?27` — the third and fourth
digits are ambiguous and the rest is overprinted. This repo has only ever
recorded `CL76841714A`. It is **not directly actionable**: a US note serial is
two letters, eight digits and a letter, and four known characters leave far too
much to enumerate. Recorded because it means the artwork contains more than one
note, which no prior pass assumed.

The `CL76841714A` tail was independently re-read from the new scan as
`...841714A`, matching. The head sits behind a fold on page 73 and the note on
page 74 resolves to about 40 pixels in the 200 dpi background layer, so no
further magnification helps — the limit here is the photograph, not the scan.

## Status

No private key. Nothing in this file is a key.
