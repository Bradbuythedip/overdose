# Is 400 dpi enough? Yes — and my earlier diagnosis was wrong

I had been recommending "600+ dpi" on the theory that sub-pixel **aliasing**
was destroying the weight measurement. That diagnosis was wrong, and measuring
it properly changes the recommendation.

## What the current scans actually are

Measured on p76 at native resolution (1800 px across a ~8.5 in page = 212 dpi):

| | |
|---|---|
| glyph height | 17.5 px |
| glyph advance | 15.5 px |
| **stroke width** | **1.81 px** |

A bold face runs 1.3–1.5x the regular stem, so the difference to detect is
**0.54–0.91 px — sub-pixel**. That much was right.

## But aliasing is not the failure mode

Shifting the image half a pixel and re-measuring every glyph gives a
stroke-width change of only **1–4%**, against a bold effect of 30–50%. Aliasing
is negligible. Something else produces the 2.2x spread on identical words.

## The real failure mode: segmentation instability

The same word does not split into the same number of components twice:

| word | characters | detected glyph counts |
|---|---|---|
| `get` | 3 | **2, 8, 3** |
| `bitcoin` | 7 | **1, 7, 7** |
| `heart` | 5 | **3, 6** |
| `the` | 3 | 3, 3, 3, **1**, 3, 3 |

5 of 10 repeated words segment differently. Glyph-count spread **2.00x**;
ink-area spread **1.99x**. Those match, which identifies the cause: at a 1.8 px
stroke in a distressed typewriter face, adjacent letters merge into one blob
and thin strokes break into two. The per-word measure then divides by an
unstable denominator, and the entire "noise" follows from that.

Highlight bars are not the cause either — excluding every word touching a bar
leaves the spread at 2.27x, unchanged.

## Why 400 dpi should fix it

| dpi | stroke width | bold−regular gap |
|---|---|---|
| 212 (current) | 1.81 px | 0.54–0.91 px — sub-pixel |
| 300 | 2.57 px | 0.77–1.28 px |
| **400** | **3.42 px** | **1.03–1.71 px — resolved** |
| 600 | 5.14 px | 1.54–2.57 px |

400 dpi is the point where the bold/regular difference first exceeds one pixel,
and it nearly doubles the stroke width — which is what stops letters merging.
Going to 600 buys more margin but is not the threshold.

**Format matters as much as the number.** The current source is JPEG from a
phone. A lossless 400 dpi flatbed additionally removes compression blur (which
is what fills counters and welds adjacent letters), uneven illumination,
perspective distortion and hand shake. Several of those, not just the dpi, are
in the 2.0x segmentation figure.

## Honest limits of this prediction

Upsampling the existing images does not improve either the noise (2.19x, same
as native) or the merge rate — no new information, as expected. So the 400 dpi
claim rests on the physics above plus the identified failure mode, not on a
direct measurement of real 400 dpi data, which cannot be synthesised.

## What to send

- **400 dpi or higher, flatbed, greyscale or colour**
- **lossless: TIFF or PNG. Not JPEG at any quality setting**
- pages 73–79, page flat on the glass, lid closed
- no auto-crop, no sharpening, no "document/text enhance" mode — those
  quantise strokes and destroy exactly the signal being measured

`bold_extract.py`, `word_bold.py` and `bacon_cipher.py` all run on it unchanged.
