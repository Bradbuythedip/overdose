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

Whole-word marks only (430 of 1,282) were run through the full harness anyway,
using the sibling session's vision transcription rather than pixel measurement:

    1,282 bits = 256 Bacon letters = 160 bytes
    direct Bacon decode, both polarities, both alphabets  -- not English
    2,054 32-byte key windows at every bit phase          -- 0 hits
    310 checksum-valid BIP-39 readings of the bits        -- 0 hits
    20 string products                                    -- 0 hits
    screened against BOTH the current-balance index and the historical
    ever-funded index

**Closed.** On the best bold classification available — a careful human-grade
vision transcription, not the pixel measurement that failed — the Bacon reading
produces nothing.

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

## 6. Hypothesis-free statistical anomaly scan — the strongest negative

Every other test here is hypothesis-first: guess a mechanism, build it, check
the chain. That only pays if the guess is right, and about twenty guesses have
now missed. This inverts the approach.

Any encoding embedded in text leaves a statistical trace. A region carrying
base58, hex, a raw key, or a substitution-ciphered payload does not have the
letter statistics of English prose. So instead of guessing the mechanism, scan
for the trace.

`anomaly_scan.py` profiles sliding 120-character windows by index of
coincidence, chi-square against English letter frequencies, per-character
entropy and vowel ratio, and compares the article's window distribution against
a matched baseline: the Schott paper, 44,946 letters of ordinary published
English, processed identically.

Power confirmed first — a planted 120-character random blob drops window IC
from 0.0648 to 0.0387 and is detected.

| metric | article | baseline |
|---|---|---|
| index of coincidence | 0.0635 ± 0.0051 | 0.0659 ± 0.0055 |
| chi2 vs English | 33.15 ± 18.33 | 31.36 ± 17.29 |
| entropy per character | 4.055 ± 0.080 | 4.001 ± 0.085 |
| vowel ratio | 0.379 ± 0.025 | 0.370 ± 0.026 |
| **worst-window z** | **11.1** | **13.6** |

**The article's most anomalous window is LESS anomalous than the most anomalous
window of ordinary academic English.** Its top-ranked "anomalies" are simply
real prose with skewed letters — `toxicbitcoinmaximalistswithinsixmonths`,
`loveeconomytheefficienciesoflove`.

### What this rules out, without assuming any mechanism

There is **no embedded non-English region anywhere in the article text**. No
disguised base58 or hex blob, no substitution-ciphered passage, no region whose
statistics differ from prose. Whatever else is true, the key is not sitting in
the text in modified form.

That leaves exactly three places it could be:

1. **Typography** — bold, weight, highlight state. Measured unrecoverable at
   ~215 dpi: per-character weight tracks glyph identity, and per-word ink shows
   a 2.2x test-retest spread on identical words against a 1.4-1.8x real effect.
2. **Selection** — which words or letters to read, the text itself unmodified.
   That is the null-cipher family, swept exhaustively and closed with
   operation-matched nulls.
3. **Nowhere in these pages.**
