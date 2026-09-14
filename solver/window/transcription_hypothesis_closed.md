# The transcription-error hypothesis is closed (2026-09-14)

For most of this project, ~150M derivations rested on an assumption nobody had
tested: that `article_transcript.txt` is a faithful transcription of the printed
page. One wrong character and every hash spanning it is wrong, and no amount of
re-deriving the transcript as written can recover from that.

It is now closed, in two steps.

## Step 1 — the scan agrees with the transcript everywhere it can read

Every glyph the 400dpi extraction produced was tested as a **subsequence** of
its transcript line. Deletions are extraction gaps; anything else would be a
transcription error.

```
97 lines, 3,642 glyphs, 97 pass, 0 fail
```

Not one character the scan could read disagrees. That covers **58% of the
article's non-space characters** (3,648 of 6,243), up from the two places
previously checked — the line breaks and one apostrophe.

## Step 2 — the other 42% swept under single-character mutation

An error could then only live in the 2,595 characters the scan could not
confirm. `mega_solve.py --families edit1_unverified` mutates exactly those
positions and no others — every substitution, insertion and deletion over a
77-character alphabet, complete by construction rather than sampled.

```
415,345 candidates, 72,685,375 scriptPubKeys, 0 hits, 11.6 min
```

Targeting the unverified positions rather than all of them made this **8.1x
cheaper** than a blanket edit1 (415,345 against 3,367,094) while covering
strictly the region where an error could still be.

## What that jointly establishes

For the distinguished phrases — every sentence, line and paragraph of the
article — **a single transcription error cannot explain the nulls.** Either the
character is verified correct against the scan, or its mutation has been swept.

This was the last hypothesis that both (a) would have explained 150M nulls and
(b) was testable offline.

## What it does not cover, stated plainly

- **n-grams.** `edit1_unverified` runs over sentences, lines and paragraphs.
  `edit1_all` extends single-character coverage to every 2..8-word n-gram
  (~126M candidates, an overnight run) and has not completed.
- **Two or more errors in one phrase.** A much smaller prior than one, and
  combinatorially out of reach: the edit-2 neighbourhood is ~14,000x edit-1.
- **p77 and p79 remain the weak pages.** p77 carries *three* polarities on one
  page — white type on dark brown, dark type inside white highlight boxes, and
  orange — so a single global threshold erases the inverted regions; that is why
  it sits at 46% and why no 400dpi mask exists for it. p79's text is set on a
  curved baseline, so a global row projection finds 6 lines where there are 26
  (strip-wise projection recovers 24-28, confirming the geometry). Character-level
  verification of either needs real OCR, which is not justified against the
  remaining probability.

## Separately: the four serial matches are noise, measured not assumed

`serial_matches.tsv` holds four 32-bit checksum collisions, two of which were
raised earlier as possible leads:

```
32355025  framed  hex_reversed            41714867
68352982  digits  hex_reversed_byteswap   67487141
70588125  digits  decimal_le              f2829404
86822479  framed  hex_reversed_byteswap   67487141
```

Both reproduce exactly, so they are genuine collisions. The base rate settles
what they mean:

```
10^8 serials x 14 products x 12 targets / 2^32 = 3.91 expected
observed                                       = 4
```

Exactly what noise produces. (`find_serial_matches.py`'s docstring estimated 5.2
from "8 products x 8 targets"; the real counts are 14 and 12, of which 10 are
distinct — `decimal_le` and `decimal_byteswap` are both `f2829404`, and
`decimal` and `decimal_le_byteswap` are both `049482f2`. The corrected
expectation is ~3.3-3.9 either way.)

All 73,400 derivations of those phrases were already checked against the
balance index: zero.
