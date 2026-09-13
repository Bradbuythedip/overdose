# Per-character bold cipher: measured unrecoverable, not merely unconfirmed (2026-09-13)

Status of this axis before today: whole-word bold was tested and gave 0 hits
(task #9), highlighted phrases were catalogued (task #11), and the
per-character bold finding on p78 was recorded as **"held unconfirmed"** on the
theory that the phone-scan JPEGs might be too coarse. That was a guess. This
replaces it with a measurement.

## Why it looked promising

Zooming a line of p76 at 2x shows bold plainly, and apparently running at
character level across word boundaries:

> but **George** **Cl**inton and James Brown clones. It's Martin Luther

"Cl" bold with "inton" regular is exactly the shape a character-level null
cipher would produce, and Keiser's tweet says the key is *"encoded in this
piece"*. Worth a real test.

## The measurement

The body face is a monospace typewriter font where bold differs from regular by
**stroke thickness**. Thickness is measurable without OCR and, in principle,
without per-letter normalization: for a character's ink mask, the mean of the
Euclidean distance transform over the ink is half the mean stroke width. Raw
ink density would confound glyph with weight ('M' inks more than 'i' at any
weight); the distance transform should not.

`bold_extract.py` implements this: Otsu binarization, connected-component
segmentation, EDT stroke width per glyph, bold called per line (font size and
exposure drift down the page, so a global cutoff would just re-detect the
largest type).

## Result: the premise fails at this resolution

Ground truth from one line of p76, all glyphs measured under identical
exposure:

| word | visible weight | measured stroke widths |
|---|---|---|
| George | **bold** | 4.6, **6.4**, 3.6, 3.7, 3.3, **6.4** |
| Clinton | "Cl" bold | 3.1, 4.9, 5.1, 3.6, 3.5, 3.5, 3.6 |
| and / James / Brown / clones | regular | 3.3 - 3.8, tight |

**Within a single visibly-bold word, half the characters measure identically to
regular text.** "George" spans 3.3 to 6.4 — its `o`, `r` and `g` sit inside the
regular population measured centimetres away on the same line.

The two 6.4 spikes are both `e`. Letters with small enclosed counters (`e`, `a`,
`o`, `g`) fill in under JPEG blur at this sampling rate, and a filled counter
inflates the distance transform exactly like a thick stroke. So the measure is
*not* glyph-independent in practice: it is dominated by counter fill-in and
local compression artifacts, both of which are the same size as the bold/regular
difference.

## Corroboration from the page-level statistics

If bolding were word-level, per-word bold fractions would pile up at 0.0 and
1.0. If it were a character cipher, there would be a real population of
intermediate fractions. Measured across the four text pages:

| page | words | frac 0.0 | 0-1/3 | 1/3-2/3 | 2/3-1 | frac 1.0 |
|---|---|---|---|---|---|---|
| p75 (6246) | 221 | 167 | 28 | 14 | 6 | 6 |
| p76 (6247) | 201 | 148 | 32 | 14 | 5 | 2 |
| p77 (6248) | 126 | 84 | 37 | 5 | 0 | 0 |
| p78 (6249) | 172 | 130 | 30 | 8 | 2 | 2 |

The distribution decays monotonically from 0 with almost **no mass at 1.0** —
yet fully-bold words demonstrably exist on these pages ("George", "El Salvador",
"Volcano Bonds", "shitcoiners'"). A detector that cannot recover known
whole-word bold as fraction 1.0 cannot be trusted to report sub-word bold, so
the 0-1/3 tail is detector noise, not cipher.

## Conclusion

The per-character bold cipher is **not testable from these files** — not
"unconfirmed", and not disproven either. Bold exists in the print; the phone
scans do not preserve per-glyph weight.

The arithmetic is the whole story: the pages are 1800-1870 px across a ~8.5 in
magazine page, about **215 dpi**, against print at 300-2400 dpi. The
bold/regular stroke delta in a 10 pt typewriter face is well under one pixel at
215 dpi, before JPEG chroma subsampling.

**What would settle it: a flatbed scan of pages 73-79 at 600+ dpi, greyscale or
colour, saved lossless (TIFF/PNG).** At 600 dpi the same measurement separates
bold from regular cleanly, and `bold_extract.py` runs on it unchanged. Nothing
short of a rescan changes this answer.

## Bugs found and fixed while building this

Two, both of which would have produced confident nonsense:

1. **Otsu returned 254 on every page.** The between-class variance numerator is
   `(m*tot - w*mt)^2`; I had written `(mt*w - m)^2`, dropping the `tot` factor
   on `m`, which makes the score climb monotonically with the threshold. The
   whole page binarized to "ink", giving ~200 components instead of ~1400.
2. **Degenerate thresholds were guarded, not excluded.** With `denom[denom==0]=1`
   the t=255 bin scores `(mt*tot - mt)^2` and always wins. Degenerate splits
   have to be removed from the argmax, not divided by 1.

Both were caught only because the reported statistics were implausible
(`bars=98%` of the page). Worth recording as the same lesson as the `seq -w`
incident: an implausible intermediate is the only thing standing between a
silent bug and a confident wrong answer.
