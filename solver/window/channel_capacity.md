# The article cannot carry a key in any editorial channel (2026-09-14)

## The question three sessions of ciphers never asked

A private key needs **128 bits** (a 12-word BIP-39 mnemonic) or **256** (raw).
Every "hidden channel" hypothesis here is a claim that some observable property
of the printed page carries those bits. Nobody counted the bits.

A channel shorter than the payload cannot carry it, whatever cipher is applied.
That is not a search result — it is a bound, and it removes the ambiguity every
null in this project has suffered from, where "0 hits" could mean wrong method
*or* nothing there.

## The audit

| channel | symbols | bits | |
|---|---|---|---|
| Bitcoin/bitcoin capitalisation | 30 | 30 | too short |
| highlight colour (orange vs knockout) | 38 | 38 | too short |
| all-caps words | 44 | 44 | too short |
| intra-line wide gaps | 7 | 7 | too short |
| quoted strings | 5 | 5 | too short |
| **all discrete editorial channels combined** | | **124** | **still too short** |
| line count parity | 145 | 145 | has capacity |
| per-glyph bold weight | 6,243 | 6,243 | has capacity — **measured at chance** |
| per-glyph baseline residual | 6,243 | 6,243 | has capacity — **measured dead** |
| word-initial letter | 1,254 | 5,894 | the text itself, not a hidden channel |

**124 bits is four short of a 12-word mnemonic**, and that is the optimistic
figure: it assumes all five unrelated channels are stacked and used perfectly.

## What has capacity, and what is left of it

Only per-glyph channels are long enough. Both measurable ones are dead, each by
an operation-matched null rather than by inspection:

- **bold weight** — runs mean 1.33 against a shuffled 1.26, ratio 1.06x, and
  the ratio stays between 1.03x and 1.21x across every threshold from the 75th
  to the 97th percentile. Editorial emphasis would emerge as long runs when the
  cut tightened. It does not. (`bold_closed_at_full_coverage.md`, at ~100%
  corpus coverage.)
- **baseline residual** — p79's glyphs sit on its curve at 1.14x the flat
  pages' spread, with a planted 3px offset recoverable at 2.98px separation, so
  the measurement can see what it is looking for. (`curve_residual_and_coverage.md`)

Line count parity has 145 bits, which clears 128 by a margin so thin that a
single miscounted line breaks it, and it would require the author to have
controlled the exact line count of a magazine layout.

## Consequence

**The key is not carried by any editorial channel on these pages.** Either it
is derived from the TEXT as a passphrase — the space this project has swept
roughly 150,000,000 times — or it is not on the pages at all.

That does not prove the puzzle is unsolvable. It does mean that further search
for a *typographic* channel is search for something that has been shown to have
nowhere to fit, and effort is better spent on the passphrase space or on the
possibility that the prize was never in the article to begin with.
