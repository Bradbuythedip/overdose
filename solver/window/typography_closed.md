# The typographic channel is closed (2026-09-13)

With the user's 400 dpi scan in hand, every remaining way of hiding a key in
the *typography* of this article has now been tested on data good enough to
decide, and all of them are negative. This file records what was tested, on
what evidence, and — importantly — which earlier conclusions in this repo were
reached by broken code and happened to be right anyway.

## What the scan is

An MRC/mixed-raster PDF, not a flat 400 dpi image:

| layer | what it holds |
|---|---|
| 200 dpi RGB JPEG per page | photos and colour washes, **text removed** (17-188 glyphs/page instead of ~1,200) |
| 1-bit masks, 305-386 dpi, CCITT G4 | all black-on-white text; **lossless**, so no JBIG2 symbol substitution |

Page 77 has no mask because it is printed **white on dark brown**, so the
scanner had no black-on-white layer to separate. It was also **scanned upside
down**. Rotated and rendered at 600 dpi it is the best conditioned text in the
whole artefact: large, high contrast, wide tracking.

## 1. Bacon cipher — ruled out on CAPACITY, not on a null sweep

Eight agents (four transcribers, four adversarial verifiers) read whole-word
bold off the lossless masks. Their notes are pixel-quantitative, e.g. p76 L22
*"President 8.35-10.80 every glyph; Nayib 7.51-9.33; Bukele 7.16-10.77, against
a regular capital B of 3.90-3.98 on the same page"*.

The bold is not a per-word binary channel at all. It arrives in **six
contiguous display runs** (38, 38, 30, 20, 13, 13 words) holding 152 of the 191
bold words, and

```
five-bit groups that are uniform: 170/199 (85%)   random would be 6%
```

A bit string that degenerate cannot carry a key however it is sliced. This is
a stronger result than another 0-hit sweep: the mechanism is excluded by
information capacity.

## 2. Whole-word bold as a NULL cipher — swept, 0 hits

The 39 isolated bold words (bold inside running text, as against the display
runs) are the reading a null cipher would use, and they had never been swept
from trustworthy data:

> Yes global unconscious view protocol UTXO ghetto up in here shitcoiners' El
> President Nayib Bukele IMF loan Michael Saylor Nic Carter Marty Bent fiat
> money Ponzi schemes It's a fact baked into Bitcoin rabbit hole We've seen
> some shit

8,192 phrases x 72 derivation paths = **15,032,320 addresses, 0 funded hits.**

## 3. Word spacing — a new channel, measured, absent

Never testable before: it needs lossless bilevel at high dpi. It is also the
better fit for the clue, since a monospace double space is invisible to a
reader and survives print.

Result: word gaps run **0.80-0.86 of a glyph pitch, sd 0.16-0.29**, and the
two-component fit collapses to a single mean on every page. No channel.

## 4. Per-CHARACTER bold on page 77 — the face, not a cipher

At 600 dpi page 77 shows what looks unmistakably like sub-word bold:
*"star**ve** to **death** as **the** resu**l**t"*. Two weight populations are
genuinely present (BIC +1108 against a unimodal null of -15). But the heavy
calls are wildly uneven across letter identities:

```
l 50%   e 28%   i 26%   h 21%   n 17%   |   d 7%   t 6%   s 5%   a 0%   o 0%   r 0%
```

That is a distressed face drawing each glyph at its own weight. To separate
identity from weight, each character's stroke width is divided by the mean for
**that letter**, which removes the face's built-in per-glyph weight and leaves
only how heavy this instance is against other instances of itself — exactly
what a cipher would modulate:

```
identity effect across letters          1.46x
after removing identity: two-component  0.978 / 1.094  = 1.12x, 19% heavy
```

1.12x is not a font weight; a legible bold is 1.3-1.8x. **No per-character
cipher.** This is the third time the project has reached this conclusion and
the first time with verified alignment on well-conditioned data.

Alignment is not assumed anywhere in that chain. Characters are read off a
fitted monospace grid rather than from connected components — the face breaks
strokes, so component counts overshoot by 10-20% per line and shift every
identity after the first break. Each line's grid must place the transcript's
spaces on empty cells better than the best of 30 **permutations of that line's
own spaces**, and lines are matched to transcript lines by a monotonic DP, so
print order is enforced. 17 of 32 lines cleared both checks; the rest were
dropped rather than mis-assigned.

## Errors found in this work, and what they cost

Recording these because two of them produced confident answers that were
wrong, and one of them silently corrupted an input.

- **`sd_floor` inverted the bimodality test.** `bic_1_vs_2` floored component
  sd at 0.35, which suited raw pixel gaps and was then applied to quantities
  normalised to ~1.0 with sd 0.18 — a floor twice the data's whole spread. Both
  components get pinned so wide that EM converges to one mean and the
  two-component likelihood falls *below* the one-component fit, so genuinely
  bimodal data is reported unimodal with a large negative margin. This had
  already produced a "no channel" verdict for word spacing. The floor now
  scales with the data, several EM initialisations are tried, and **both
  affected results were re-run** — spacing stayed negative, p77 flipped to two
  populations, which is what led to the identity analysis above.
- **The first `gap_cipher` was worthless.** It sliced lines by row-ink profile
  across the full page, pooling body text with the rotated sidebar (687 px
  line-start spreads, "gaps" averaging 147 px), and its null returned exactly
  1.00 on every page because letter gaps are small integers and any histogram
  of few integers has a perfect valley. A saturated null calibrates nothing.
- **Type size confounded the spacing test.** Without per-line normalisation
  p78's display type produced a spurious CHANNEL at ratio 1.77.
- **The null was quantised wrongly.** It rounded to integers while the data sat
  on a 1/30 grid.
- **The reading extractor matched bold words by STRING**, so a bold "the"
  marked every "the" on its line. The agents return their lists in reading
  order; ordered positional matching recovers the real positions.
- **Ink polarity was assumed.** Page 77 is white-on-dark, and getting this
  backwards does not fail loudly — it segments the paper as ink and returns a
  few hundred fragments that look like a plausible glyph count.

## Where this leaves the puzzle

Typography is exhausted: weight (word and character), spacing, and the Bacon
and null readings of both. Cumulative across the project, roughly **95M derived
addresses, 0 funded hits**, against both the 56.8M current-balance index and
the 1.05M historical ever-funded index.

No private key. Nothing here is a key and nothing here should be presented as
one.
