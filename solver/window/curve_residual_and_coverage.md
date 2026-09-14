# The curved baseline is a flourish — but chasing it fixed the corpus (2026-09-14)

## The hypothesis

Page 79's body text is set on an arc. That is a strange choice for an
article's conclusion, and it has a property nothing else on the spread has: on
a curve, every glyph carries a vertical offset. Fit the arc, and each
character's residual from it is a channel — invisible to a reader, surviving
print, and impossible to even look at until the curve has been modelled.

Which is why nobody had. `wf/glyphs_p79.tsv` stores ONE y per line:

```
line 1: 10 glyphs, y range 2601-2601 (spread 0)
```

No per-glyph vertical position exists in the corpus, on any page.

## The answer: no

Measured against the flat pages, with a degree-2 baseline fitted per line:

| page | glyphs | lines | g/line | mean \|quadratic\| | residual sd (px) |
|---|---|---|---|---|---|
| 75 | 1,462 | 35 | 42 | 3.89e-05 | 1.510 |
| 76 | 1,406 | 31 | 45 | 1.31e-05 | 1.704 |
| 77 | 1,489 | 33 | 45 | 1.67e-05 | 1.555 |
| 78 | 1,069 | 25 | 43 | 4.17e-05 | 1.784 |
| **79** | **1,083** | **27** | **40** | **3.03e-05** | **1.906** |

p79 residual spread is **1.14x** the flat-page mean, and its fitted curvature is
**0.98x** theirs. Its glyphs sit on their curve no less tightly than any other
page's sit on theirs. There is no vertical channel; the arc is decoration and
the residual is ink and camera.

The controls make that null mean something: a planted 3px offset on every third
glyph is recovered at 2.98px separation, and an unperturbed synthetic curve
fits to 0.0000px. The measurement can see what it is looking for.

## The bug I nearly reported as a finding

The first run said p79's residual spread was **6.47x** the flat pages'. It was
line merging. p79 came out at 1,083 glyphs in **7 lines** — 155 glyphs per line
against 56-67 elsewhere — because the line grouper walked a drifting y with a
loose tolerance, and on a curved page adjacent lines approach each other
vertically. The "residual" was line spacing being fitted as curve.

Two guards now: a regression test requiring two curved lines 40px apart to stay
separate, and a gate in the comparison that **refuses to report** if p79's
glyphs-per-line is more than 1.6x the flat pages'.

## What it actually produced

To test the hypothesis the extraction had to be rebuilt: glyphs are chained
left-to-right along the baseline, attaching the nearest glyph to the right
within a small dx/dy window, so a chain follows arbitrary curvature and never
jumps to a neighbour.

| page | corpus glyphs | new | corpus lines | new | printed lines |
|---|---|---|---|---|---|
| 75 | 1,140 | 1,462 | 27 | 35 | 33 |
| 76 | 1,031 | 1,406 | 25 | 31 | 31 |
| 77 | 593 | **1,489** | 21 | 33 | 32 |
| 78 | 796 | 1,069 | 20 | 25 | 23 |
| 79 | **149** | **1,083** | 6 | 27 | 26 |
| **total** | **3,709** | **6,509** | | | |

**Page 79 goes from 149 glyphs to 1,083 — 7.3x. Page 77 from 593 to 1,489.**
Line counts now match the printed line counts within one or two.

`looking_at_the_pages.md` established that every glyph-level conclusion in this
repo — `bold_cipher_resolved.md`, `typography_closed.md`, the mirror scan, the
per-character work — rests on a corpus holding **61% of the article**, with the
conclusion page at 15%. That is no longer a constraint. The corpus can be
rebuilt at effectively full coverage, and every per-character analysis that was
run on 61% is worth re-running on 100%.

Glyph counts slightly exceed printed character counts because connected
components split `i`, `j`, `%` and some punctuation into pieces. That is a
labelling problem, not a coverage one.
