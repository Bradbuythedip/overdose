# Every-Nth extraction: no hidden English, and a correction to my own test (2026-09-13)

Every-Nth word / letter / line extraction over the body text (the highlights
version was done long ago; the prose was never in any corpus until today).
924 letter-level extractions, plus word-, line- and initial-level ones, over
the whole article and per page, forward, reversed and mirrored, offsets
0..N-1 for N in 2..12.

## The prior question, asked before brute force

Sweeping 13,540 extracted strings as brainwallet passphrases only answers "is
one of these the key". The cheaper and more informative question is whether any
of them contains English word order at all. If a null cipher is really present,
the extracted text reads as language.

`englishness.py` scores common-English-trigram density and compares each
extraction against a null. No dictionary is installed on this box, and none is
needed: an every-Nth extraction inherits the source's letter FREQUENCIES but
destroys its ORDER, so a random permutation of the extraction's own letters is
a natural null.

Controls anchor the scale rather than asserting it:

| control | z |
|---|---|
| the article's prose (English) | **+70.7** |
| the same letters, shuffled | −0.2 |

## Result

| family | max z |
|---|---|
| 924 letter-level extractions | **+5.57** |
| the same 924, letters shuffled | +4.06 |
| prose control | +70.7 |

Nothing remotely resembles the prose control. The top-scoring string was
`ALL/mir/L2+0` — every 2nd letter of the mirrored article — at z=+5.49,
starting `rsexmvlneapt…`, which is just `…MXESR` backwards, i.e. "MAX KEISER"
decimated.

## The correction: a frequency null is not enough

+5.49 against a shuffled-null maximum of +4.06 looks like a signal, and the
first version of this test reported it as one. That was wrong.

Shuffling an extraction's letters controls for letter frequency but **not for
the extraction operation**, and some operations inflate the trigram score by
themselves. The matched null is the same operation applied to text that cannot
contain a message. Running mirror-then-every-2nd-letter on twelve word-shuffled
copies of the article — still English words, no possible global message:

```
+7.45 +6.43 +6.27 +5.56 +5.50 +5.41 +5.32 +5.19 +4.90 +4.84 +4.72 +4.72
+4.57 +4.45 +4.35 +4.30 +4.12 +4.05 +3.79 +3.66 +3.31 +3.00 +1.57
max +7.45   mean +4.63
```

The real article's +5.49 sits **below the null mean plus one standard
deviation** and far below the null maximum. The apparent signal is entirely an
artifact of mirror-then-decimate.

For comparison, the unmirrored every-2nd-letter extractions of the real article
score +0.14 and +0.85, against a word-shuffled control maximum of +1.32 — dead
centre of the null.

**Conclusion: no every-Nth extraction of this article, at any N, offset,
direction or page, contains hidden English.** The axis is closed on evidence
rather than on failure to find a brainwallet hit.

## Methodological note worth keeping

> A null model has to match the OPERATION, not just the data's marginal
> statistics. A frequency-matched null made noise look like signal here; an
> operation-matched null made it obviously noise.

This is the same family of error as the earlier ones in this repo — a null from
a source that was never shown to produce a positive, and a "funded brainwallet"
control that could not have succeeded. `englishness.py` now carries the warning
inline so the next reader does not repeat it.

## The same test applied to the acrostic / column families

Run over 1,031 acrostic, column and line-length readings (block acrostics,
line-edge first/last word and letter, line-length letter mappings):

| family | max z |
|---|---|
| real readings | **+18.77** |
| the same strings, letters shuffled | +5.56 |
| prose control | +70.7 |

+18.77 against a shuffled-null max of +5.56 looks like a strong signal. It is
not, and the reason is the same as before, only more obvious once you look at
the string:

```
HERE'S REALLY MARKETS ALL AROSE AND IN AND LOOK THAT'S TO NOW KEEP THE HANDS
TO GET IT'S NAILING GOTTA SINCE THE OUR PUTS ...
```

That is the first-word-of-each-line reading. It is built out of real English
words by construction, so a high English-trigram score is guaranteed and
carries no information whatsoever. It is also plainly word salad rather than a
sentence.

The matched null settles it. Taking the same first-word-of-each-line reading
from twelve word-shuffled copies of the article, where no message can exist:

```
+27.2 +24.2 +22.1 +21.6 +21.3 +20.4 +20.0 +19.9 +19.2 +18.6 +18.0 +16.8
max +27.18   mean +20.77
```

The real reading scores **+19.45, below the null mean**. A first-word null
cipher over this article is exactly as English-looking as drawing words from it
at random — which is what it is.

**Both the every-Nth and the acrostic/column families are closed**, and in both
cases the naive frequency-matched null would have reported a false positive
(+5.57 and +18.77) that the operation-matched null erases.
