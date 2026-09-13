# Outside-the-box readings, tested and closed (2026-09-13)

Ideas that come from treating this as a showman's visual joke rather than a
cryptographer's construction. Each is recorded with how it was tested, because
several are attractive enough to be re-proposed later.

## 1. Recto/verso superimposition — the physical mirror

In a magazine, pages 73 and 74 are the **same sheet of paper**, recto and
verso; likewise 75/76 and 77/78. Hold a leaf up to the light and the back shows
through **mirrored**. That is literally mirror writing, it is the kind of
physical trick a film-maker would build, and it would be invisible in a scan of
either page alone — orange bars on one side could highlight words on the other.

Tested by mirroring each verso and compositing it onto its recto.

**Negative.** The pages do not register. p75's centred lines and mirrored-p76's
two blocks sit on different baselines with no systematic bar-to-word
coincidence; the composite is visual noise, not a designed effect. Ink-overlap
over union: p73/74 26.9%, p75/76 6.0%, p77/78 7.6% — consistent with two
independently typeset pages, not with a registered overlay.

Caveat kept: the two photographs are not perfectly registered to each other, so
this rules out a gross alignment cipher, not a millimetre-precise one.

## 2. Whole-document hashes — the obvious non-cryptographer move

Thousands of fragments and n-grams have been swept, but "sha256 of my article"
in its exact whole-document form had never been tested. Keiser is not a
cryptographer; this is the first thing such a person would do.

55 serializations: lines joined with `\n`, `\r\n`, spaces, nothing; with and
without a trailing newline; whitespace-squashed; letters-only;
alphanumeric-only; the raw transcript file; each page alone; each of those in
lower case, upper case and reversed. Six hash functions (sha256, dsha256, both
sha512 halves, sha3-256, blake2b), five script types, screened against **both**
the current-balance index and the historical ever-funded index.

**Negative.** 0 hits.

## 3. The Bacon cipher over whole-word bold

Recorded in full in the commit history. The mechanism is sound and the capacity
works (1,282 words = 256 Bacon letters = 160 bytes, ample for a WIF), but it
needs near-perfect per-word classification: a single mis-call shifts every
subsequent 5-bit group, and a 51-character WIF needs 255 consecutive correct
calls. At 99% per-word accuracy that is a 7.7% chance of a clean run; at 98%,
0.6%.

Neither pixel measurement nor vision marking reaches that. Pixel measurement
fails outright — test-retest on identical words gives a median 2.2x spread
against a real bold effect of 1.4-1.8x. Vision marking reproduces the same
glyph-identity bias: across the sibling session's five-page transcription the
sub-word bold calls select v 12.7%, i 10.5%, l 9.1% against a 0.4%, c 0.5%,
n 0.6% — a ~30x spread where a real cipher would be roughly uniform.

Whole-word marks only (430 of 1,282) were run through the full harness anyway.

## What these three share

Each was worth testing precisely because it does **not** assume a
cryptographer. That remains the right instinct for Keiser. But the article has
now absorbed the showman readings as thoroughly as the cryptographic ones.

## 4. Self-referential book cipher

The article's numbers used as indices into the article's OWN words, letters and
lines — the Schott paper was tried as the key text, but never the article
against itself.

24 numbers: 2008, 1, 1, 1, 1971, 10, 1, 2011, 1, 42, 20, 000, 100, 000, 2017,
12, 000, 51, 85, 2, 51, 95, 1969, 10.

The word-index reading is nonsense: *"certainty IS IS IS Full not IS explain IS
in It BITCOIN The BITCOIN the reaction BITCOIN the of TOXIC the Wall scammer"*.
48 products across word/letter/line indices, base 0 and 1, forward and
reversed, four hash functions, both indices. **0 hits.**

## 5. "The numbers don't lie" taken literally

That phrase is orange-highlighted on p78, so it is worth reading as an
instruction rather than as rhetoric.

The article's entire digit stream, in order, is 56 digits:

```
20081111971101201114220000100000201712000518525195196910
```

That settles it by length alone. A 256-bit key needs **78 decimal digits or 64
hex characters**; this is 56 digits = 184 bits. It cannot be a private key
directly, whatever the phrase suggests. Tested anyway as a decimal integer, as
hex left- and right-padded, and hashed in every form: **0 hits.**

The phrase is rhetoric.
