# The page-72 banknote is printed artwork, not show-through (2026-09-14)

This corrects `window/page71.md`, which inferred that page 71 carries a
banknote. That inference is now void.

## The test

Show-through and face-to-face offset are both **mirrored**. Printed artwork is
not. So mirroring alone decides provenance, and page 72 carries a built-in
control: page 73's `OVERDOSE` headline and `with Max Keiser` byline appear on
page 72 **reversed** (and left-right swapped in position), exactly as transfer
from the facing page must.

Rendered straight from the PDF at 1200 dpi over the clip rect — no upscaling,
so no LANCZOS-manufactured edges — the ghosted banknote reads:

| element | orientation |
|---|---|
| `OVERDOSE`, `with Max Keiser` | **mirrored** (from page 73) |
| serial `KB 4627 …` | **left-to-right** |
| `THIS NOTE IS … LEGAL TENDER` | **left-to-right** |
| `FOR ALL DEBTS, P[UBLIC]…` | **left-to-right** |
| Treasury / Federal Reserve seals | **left-to-right** |

Non-mirrored on a page whose genuine transfer IS mirrored means the note was
printed on page 72 itself: a washed-out $100 in the NUMBERS page background,
consistent with the `$` and `₿` glyphs and the wireframe tori also printed
there.

## What this changes

- **We have no evidence about page 71's content.** The only reason to think it
  carried a banknote was this ghost, and the ghost is page 72's own ink. The
  user's pointer to an arrow on page 71 now stands entirely on its own.
- **The second serial is stronger, not weaker.** It is deliberate design inside
  the Keiser spread rather than an accident of paper opacity, so the
  two-component reading that `wf/mitm_split.py` tests is better founded.
- **The digits were over-trusted.** `K B 4 6 2 7` are unambiguous at 1200 dpi;
  the last four sit under the `In 2020,` / `WESTERN UNION` display type and
  were read *through* it. Every sweep so far held them fixed while varying only
  the trailing letter, so one misread digit would have invalidated all of them.
  `wf/serial_tail.py` enumerates the tail instead of assuming it.

## Provenance of the public material

Keiser's announcement (X, 4 Mar 2023) and a 7-note nostr thread (5 Mar 2023,
event `2d73d713…`, page images on nostr.build) are the canonical release.
**Seven** images matches exactly the seven phone photos this repo once held —
printed pages 73-79. Page 72 was never published; it exists here only because
it is on the back of the leaf that was scanned. So no public solver has seen
the second serial, which is consistent with the puzzle standing unsolved.

nostr.build, nostr.com, api.nostr.band, archive.org, every ordinals API and
Alchemy are all refused by this session's egress allowlist (GitHub only), so
the thread images cannot be retrieved from here.
