# Golden-prompt leads 2, 3 and 4, run to completion (2026-09-14)

Four steps from `SOLVE_PROMPT.md`'s "Where to actually look". All null, each
with a control that fired.

## Step 1 — highlight bars as spatial data (lead 3)

The prompt: *"The orange and black bars are positioned deliberately. Their
coordinates, lengths, or per-line counts are a numeric sequence nobody has
treated as data."* Still true — `parse_typography.py` reads `[O:...]` markup a
human typed, so it has the bars' words, never their pixels.

It also survives `channel_capacity.md`: bar colour is 38 bits and dead, but
22 bars x (x0, x1, y, w, h) is 110 numbers, which has room for a key.

**Measured at 400 dpi: 22 orange bars.** 200 derived sequences — widths,
heights, edges, gaps, per-page counts, as digits, hex and letters — swept:
**1,835,250 scriptPubKeys, 0 hits.**

Three detector bugs found and fixed along the way, each caught by a control
rather than by inspection:

1. **81 bars** on the first run. A morphological CLOSE merged adjacent white
   body text on p77 into 39 phantom bars. Replaced with an OPEN, which erodes
   thin strokes away before joining anything.
2. **3 bars** after a hole-topology filter, because the flood fill seeded at
   `(0,0)` — which is *ink* whenever a bounding box starts on a glyph, so the
   fill did nothing and every region read as "holes closed". Caught by the
   regression test for text rows.
3. **A false confound.** With 22 detected against 22 catalogued the totals
   matched and the tool reported `corr(bar width, text length) = +0.545` and
   "width is NOT explained by text length". The pairing was wrong: p76 and p78
   over-detect by one each and p79 under-detects by two, netting to zero,
   because the catalogue splits a multi-line highlight per LINE while the
   detector sees one connected region. The gate now checks **per page** and
   refuses to report. Global totals matching is not alignment.

**Scope, stated:** orange only. Orange appears nowhere else on these pages, so
an orange region IS a bar. The knocked-out bars are not separable by colour —
window-density measurement shows the densest dark regions on p75 and p78 are
the `BITCOIN IS TOXIC AF` headline (0.57) and the `X FUCK ALL X` scribble
(0.25), not bars; and on p77 the body text is white on dark, the same value as
the white bars. Separating those needs segmentation, not thresholding.

## Step 2 — Playfair and friends (lead 4)

The prompt named Playfair specifically. `classical_cipher.py` had vigenere,
beaufort, autokey and running_key keyed on 20 clue words including
`elsalvador` — but grep for playfair across every `.py` returned nothing.

Implemented Playfair, four-square and Nihilist, each pinned to a published
vector first. Playfair reproduces `hidethegoldinthetreestump` /
`playfairexample` -> `BMODZBXDNABEKUDMUIXMMOUVIF` exactly and round-trips on
decrypt.

5,941 letters x 20 keywords x 3 ciphers x 2 directions. 140 plaintext
candidates, **0 self-certifying**, and swept: **1,284,500 scriptPubKeys,
0 hits.**

## Step 3 — the Schott paper as a running key (lead 2)

Keiser linked PMC2117809 specifically, and a setter naming one document is
what book-cipher setters do. `running_key_hunt.py` existed and the paper text
existed — in `/tmp`, which is why no result was ever recorded. Preserved to
`corpora_ref/schott_PMC2117809.txt` (1,092 lines, 44,946 letters).

```
planted offset 4321, recovered 4321, density 0.1321   (English ~0.1277)
positive control: OK

article as ciphertext, paper as running key:  nothing above the noise floor
paper as ciphertext, article as running key:  nothing above the noise floor
NO RUNNING KEY: neither text decrypts the other at any offset, in any mode
```

Its 10 numeric book-cipher products swept: **91,750 scriptPubKeys, 0 hits.**

## Step 4 — re-measure bold at 400 dpi

`bold_closed_at_full_coverage.md` measured bold clustering on the ~215 dpi
phone JPEGs. Re-run on the 400 dpi renders from `scan/Scan1.pdf`:

| percentile | 400 dpi | 215 dpi |
|---|---|---|
| 75 | **1.00x** | 1.10x |
| 85 | **1.01x** | 1.20x |
| 90 | **1.03x** | 1.21x |
| 95 | **0.98x** | 1.08x |

The higher resolution makes the null **flatter**, not weaker. The residual
1.1–1.2x clustering visible at JPEG resolution was itself an artifact of the
source. At 400 dpi bold glyph positions are indistinguishable from a shuffle.

## Status

Leads 2, 3 and 4 of the golden prompt are now closed, each with a control.
Lead 5 (never funded) is unfalsifiable by design. **Lead 1 — other OVERDOSE
columns — is the only one left**, and the prompt already ranked it highest:
"keys" was plural and "in the text" of his column generally. Today's discovery
of page 72, inside the issue we already had, is direct evidence that missing
source material is the binding constraint.
