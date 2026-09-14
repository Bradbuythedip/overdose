# Page 71 is not in our material, and that reframes J2 (2026-09-14)

User reports Keiser confirmed on Instagram that the key is **in this issue**,
and points to *"the arrow mid right centre on page 71"*.

## We do not have page 71

Verified rather than assumed. The `PAGE_MAP` in `extract_scan.py` was inferred
by an earlier session, so it could have been off by one. It is not: reading the
**printed folios** off the un-rotated renders gives `72` at bottom-right of the
NUMBERS page and `73` at bottom-left of the OVERDOSE opener. The scan is eight
sheets, printed pages **72-79**, and page 71 is not among them.

Two corrections to `window/thirty_clues.md` fall out of this:

- **Clue 9 is mislabelled.** The 224-232 x 32-36 strips I called folios are the
  **OVERDOSE running heads** — extracting and un-rotating xrefs 8, 27, 38, 51,
  66 and 78 renders the word OVERDOSE in every case.
- **The folio parity is the reverse of what I wrote.** Page 72 (even) carries
  its number bottom-**right**, page 73 (odd) bottom-**left**.

## What page 72 tells us about page 71

Pages 71 and 72 are the two sides of one leaf, so page 71 shows through onto
page 72. The scanner's 200 dpi colour layer is ideal for reading that, because
it has the text separated out: measured, its darkest pixel is L=197 against
paper L=245, i.e. **no ink at all** — it is purely the wash and ghost layer.

On it the ghosted banknote reads **KB 46279860**, and the decisive observation
is that this is **not page 73's note**. Page 73 carries CL76841714A, and
`window/looking_at_the_pages.md` established every legible bill on 73/74 is
that one cutout reused. A different serial on 72 therefore did not come from
73. It came through the sheet from **page 71**.

So page 71 carries a banknote. That is independent corroboration of the user's
pointer, from our own material.

The mirror-reversed `OVERDOSE` and `with Max Keiser` also visible on page 72
are page 73's, transferred face-to-face.

## The arrow: not resolvable here

Mid-right on page 71 maps to mid-**left** on page 72, since show-through is
mirrored. Both mid-band halves were isolated at 200 dpi with the scanner's
diagonal hatch suppressed by a 5-px median filter and the faint mid-greys
stretched. The band contains the two wireframe graphics, the note, and hatch.
**No arrow is resolvable.** The show-through is at or below the noise floor of
a 200 dpi wash layer.

This is a limit of the material, not a negative result about the arrow.

## The real reframing

`window/unswept_changes_everything.md` reduced the search to J2 (material not
searched) or J3 (derivation not tried), and read J2 as *other columns*. Keiser
saying "this issue" does **not** close J2 — it relocates it:

> The scan is 8 pages of a magazine that has at least 79. "In this issue" is
> not "in pages 72-79."

Page 72 already proved this failure mode once: it sat inside the issue we
thought we had, absent from every transcript for three sessions, and carried a
second serial and 22 numerals no corpus contained. Page 71 is the same problem
one page further out.

## What is needed

**Page 71**, and ideally the surrounding spread (70-71) or the whole issue.
Everything in this repository is built to consume it: `extract_scan.py` takes
any page count, and the transcript, corpus and sweep tooling are page-agnostic.
