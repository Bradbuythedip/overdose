# There is no underline and no strikethrough (2026-09-14)

## What I claimed, looking at the pages

> **Page 75 has the only underline in the article.**
> *"Markets are like that. <u>They discount stuff in advance.</u>"*

> **Confirmed — that is a genuine strikethrough**, running from after the
> `nonsense` box through to `bitcoin`. Not a box edge; it passes through the
> letterforms at mid-height.

Both are wrong. Measured, neither mark exists.

## The measurement

A drawn rule is a long CONTIGUOUS run of dark pixels in a single row. Text is
dark in short bursts with gaps between glyphs. So the discriminator is the
longest contiguous run per row, not the row's total ink.

**p76, the "strikethrough" line.** The struck text sits at y 648-680 by ink
density (10-30%). Longest contiguous dark run anywhere in that band: **174px**,
which is glyph scale.

The only long runs nearby are at y 629-632 — 836, 746, 609px — and that is the
**bottom edge of the black highlight box on the line above**, which spans the
full measure. At 3x LANCZOS upscaling that edge smears downward, and the eye
carries it across the line below.

**p75, the "underline".** Longest contiguous run across the whole
"They discount stuff in advance." line: **21px**. Nothing. What reads as a
continuous rule is the bold weight of that phrase — and
`looking_at_the_pages.md` had already measured exactly this: the bold detector
flags 14 of 56 glyphs on that line and all 14 fall inside that phrase. It is
bold, not underlined.

## Why this keeps happening

Three messages before making these two claims I wrote, about the bold:

> Eyeballing stroke weight at 3x zoom reproduces the illusion and settles
> nothing.

And then eyeballed two marks at 3x zoom and called one of them "confirmed". The
upscaling that makes a feature legible is the same upscaling that invents it —
LANCZOS interpolation manufactures smooth continuous edges from broken ones,
which is precisely what a rule looks like.

The rule holds: **a typographic claim about these pages is worthless until it
is measured.** The measurement here is four lines of numpy and it takes a
minute.

## What the scan does find

`rule_scan.py` works — it finds a planted rule and stays silent on synthetic
text. Run across all seven pages at a 12%-of-width threshold it reports bands
which, sorted by height, split cleanly:

- **tall bands (12-30px)** — the orange and black highlight boxes, correctly
  found, since a filled rectangle is a long contiguous dark run
- **thin bands (1-4px)** — page furniture and photographic content; the two
  photo pages 73/74 dominate, as expected

No thin band coincides with either claimed mark, on either page.

## Status

The typographic channels on these pages are: **bold weight**, **highlight
colour**, and nothing else. No underline, no strikethrough, no rules.
