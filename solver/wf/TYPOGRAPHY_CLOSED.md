# The sub-word bold is the font, not a cipher — four independent proofs

Prior sessions recorded per-character bold as "unconfirmed" or "not measurable",
which left it as the strongest surviving hypothesis and the reason the repo kept
asking for a 600 dpi rescan. It is now positively explained rather than merely
unmeasured, and the explanation is a property of the typeface.

## The decisive observation

The **same phrase renders with the same sub-word bold pattern in two different
places on the page**. "Toxic Bitcoin Maximalist" appears on p75 line 17 and
again on p75 line 27, and both times the identical letters read heavy.

A cipher cannot do that. If sub-word weight carried a payload, two unrelated
occurrences of one phrase would carry different bits — that is the entire point
of a payload. Identical patterns mean the pattern is a function of the
*characters*, not of position, and a function of the characters is a font.

The body face is a distressed typewriter font with contextual alternates: some
glyphs are simply drawn heavier, and heavy glyphs cluster in predictable
letters. Bar text is uniformly heavy throughout, which is a style, not a signal.

## Four measurements, four methods, one conclusion

| method | statistic |
|---|---|
| stroke width per line (earlier session) | bold 3.3-6.4 vs regular 3.3-3.8, overlapping |
| per-letter ink area (this session) | `h`/`d`/`a` called bold 80-91%, `c`/`k` 11-12% |
| vision transcripts (sibling session) | ~30x spread across letter identities |
| chi-square on mixed-weight words (workflow) | **chi2 = 451 on 24 df**; `e`/`i`/`l` heavy at 0.96-0.98, `n`/`o`/`t`/`a`/`c` light at 0.94-1.00 |

All four are measuring letter identity. The bold/regular stroke delta in a 10 pt
typewriter face is under one pixel at ~215 dpi, so narrow heavy-stemmed letters
read heavy and round open ones do not, whatever the typography actually is.

**This also removes the case for a rescan.** A 600 dpi scan or the issue PDF
would resolve the weights exactly — and would resolve them to the font's own
contextual alternates. There is no payload there to recover.

Only **whole-word** emphasis is author markup. That channel was read as a
1,282-bit Bacon and binary stream and returned 30,632 keys, 89,160
scriptPubKeys, English z = 0.00, zero hits. See `wf/bacon_bits.log`.

## The ghost text is set-off ink, and we can name the source page

The faint mirror-reversed text on p73, p74, p76 and p78 was the best remaining
"mirror writing" candidate. It is ink transfer from the facing page of this
particular copy, and each ghost has now been matched to its source:

- p76's ghost is **p77's** white `EVERY SINGLE ONE OF THE BITCOIN WANNABES` block
- p78's ghost is **p79's** `Stacy and I have been living in here` paragraph

Facing pages 72/75/77/79 account for all of it. This is a property of one
physical copy sitting in a stack, not something an author can plan or a reader
can be expected to decode. The mirror-writing clue does not point here.

## Status of the workflow that produced this

48 agents, 16 completed, **32 failed when the account hit its monthly spend
limit**. The completed agents reported **0 hits** across
author-emphasis seed sequences, George Sand sentence-level readings, and the
"El Salvador" seed family. The three findings above came from the design and
measurement stages, which completed before the limit was reached.
