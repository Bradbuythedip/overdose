# Underlines and a strikethrough are real (2026-09-14)

This corrects a prior negative. The column carries typographic marks that were
never catalogued, and the earlier "they do not exist" finding was an artifact
of how it was measured.

## Why the earlier negative was wrong

It rested on 3x-LANCZOS-upscaled crops. LANCZOS interpolation manufactures
continuous edges between glyphs, so on that evidence a rule and its absence
look alike — the method could not decide the question in either direction.

Measured instead on the scanner's own **lossless CCITT G4 ink separation at
400 dpi** — no resampling at all — the marks are unambiguous.

## Method

`wf/strikethrough.py`. Connected components are the wrong primitive: a
strikethrough is connected to every glyph it crosses, so its bounding box comes
out tall and sparse (the first attempt found nothing for exactly this reason).
Rules are instead found as **clusters of long horizontal row-runs**, which
separates them from knocked-out highlight bars by vertical extent — a rule
persists a few rows, a bar tens of them. Both controls pass: a planted 550 px
rule is detected, a 60 px-tall bar is rejected.

## What is marked

| page | kind | width | text |
|---|---|---|---|
| 75 | underline | 2.62 in | `They discount stuff in advance.` |
| 75 | underline | 0.73 in | `protocol.` |
| 76 | strikethrough | 3.89 in | `(and 10years of watching Peter Schiff miss buying bitcoin` |

Page 78 has none. Page 73/74/79 candidates are the OVERDOSE slab headline, the
photograph and the barbed wire. **Page 77 is not measurable by this method** —
it is printed white on dark brown and has no black separation, so thresholding
its colour render returns 47 candidates that are mostly torn edge and graffiti.
Stated as a limit, not as a zero.

Two details worth keeping:

- The strikethrough stops at the **line break**. The parenthetical continues
  unstruck on the next line (`I started honey-badgering him to buy some at $1
  back in 2011)`). The mark is scoped to the printed line, not the sentence.
- Both underlined spans are also **bold**, so underline is a second layer of
  emphasis on top of an existing one, not a substitute for it.

## Why it mattered enough to test

None of the three appears in `highlights_ordered.tsv`, and STATUS.md records
that the curated corpus which received the deep path set was built from that
catalogue. So these phrases had never been swept at depth in any form.

## Result

`wf/marks.py`, 244 phrases x 72 paths x 5 seed schemes x 5 script types =
**447,740 addresses, 0 hits**. Readings tested: each mark alone and mirrored;
every ordered concatenation; underlines-only; the struck line alone;
strikethrough read as an *instruction* (the article with that line deleted);
and the marks folded into the highlight sequence in page order.

Null, but the marks themselves stand as corrected fact, and the catalogue in
`marks_ordered.tsv` is now part of the record.
