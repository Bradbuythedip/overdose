# The bold cipher, re-run on the whole article this time (2026-09-14)

## Why it needed redoing

Task #9 ran a whole-word bold null-cipher and returned 0 hits. It ran against
`wf/glyphs_p*.tsv` — which `looking_at_the_pages.md` later measured as holding
**61% of the article**, with page 77 at 46% and page 79 at **15%**. On the two
pages where coverage was worst, most glyphs were never extracted, so the null
covered text the detector had never seen.

`curve_residual.py` fixed the extraction (chain glyphs along the baseline
rather than bucket by shared y). Page 79 went from 149 glyphs to 1,083, page 77
from 593 to 1,489, and line counts now match the printed line counts.

## The measure, and its published control

Per-glyph stroke width from a distance transform — twice the mean
distance-to-edge of the glyph's ink — normalised by glyph height. Robust where
ink-area is not: a bold `a` and a regular `m` can carry the same ink, never the
same stroke.

`looking_at_the_pages.md` records a ground truth to check it against: on p75
line 6 the old detector flagged **14 of 56 glyphs**, all inside "They discount
stuff in advance.", none outside. This measure puts the closest line at a bold
fraction of **0.23** against the published **14/56 = 0.25**. It is measuring
the same thing.

## The result

At full coverage, 151 lines across five pages:

| page | glyphs | lines | bold runs >= 3 glyphs |
|---|---|---|---|
| 75 | 1,462 | 35 | 8 |
| 76 | 1,406 | 31 | 5 |
| 77 | 1,489 | 33 | 2 |
| 78 | 1,069 | 25 | 13 |
| 79 | 1,083 | 27 | 8 |

The masks are scattered, not blocked:

```
p75 L14  .BB.B.B..B..B.B.......BBBB.......B.....B
p78 L15  .BB..B..BB.B...B....BB.......B...B..B...B...B...BBB
```

Editorial emphasis makes long contiguous runs. Against an operation-matched
null — same line, same number of bold glyphs, shuffled — the observed runs are
no longer than chance:

```
observed  566 runs, mean length 1.33, max 12
shuffled  600 runs, mean length 1.26, max  8
ratio 1.06x
```

And that is not an artifact of one threshold. Sweeping the cut:

| percentile | % bold | obs mean run | null mean | ratio |
|---|---|---|---|---|
| 75 | 13.7% | 1.33 | 1.21 | 1.10x |
| 85 | 5.1% | 1.34 | 1.11 | 1.20x |
| 90 | 2.7% | 1.30 | 1.08 | 1.21x |
| 95 | 1.0% | 1.16 | 1.08 | 1.08x |
| 97 | 0.7% | 1.06 | 1.03 | 1.03x |

No threshold produces clustering. If editorial bold runs existed they would
emerge as the cut tightened; they do not.

## What this settles

`bold_cipher_resolved.md` concluded from P(bold | character) — 0.158 for `c`,
0.476 for `a`, chi-square 93.9 on df 22 — that weight tracks letter identity.
That was measured on 61% of the article. It is now confirmed on effectively all
of it, by a different statistic: bold glyphs are positioned at chance.

It also corrects something I claimed while reading the pages. I described "long
contiguous bold runs" on p79 — one "spanning two and a half lines and ending
mid-line at connect". The measurement says those runs are not there. The eye
groups adjacent heavy glyphs into runs; the distance transform does not.

**The bold channel is closed, on the whole article rather than on 61% of it.**
