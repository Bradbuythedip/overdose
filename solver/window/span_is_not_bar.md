# "38 highlights" is a count of phrases, not of marks (2026-09-14)

Raised by the workflow's adversarial critic, verified here, and it makes one of
my own results conditional.

## The claim

`highlights_ordered.tsv` was built by READING the pages, so one row is one
phrase. A physical bar is one contiguous run of highlight ink on one text line.
These differ wherever a phrase wraps a line break, or two phrases share a bar.

## Direct verification, no detector needed

On page 77 the catalogued span

    (Sorry Bhutan, you fell for that snake oil salesmen over at XRP.

is printed across **two lines**: `...salesmen over` ends line 1 and `at XRP.`
begins line 2. It is therefore at least **two** physical bars recorded as
**one** row. On that same second line, `Get ready to experience shitcoin hell.`
is a separate bar. So in this small region the span count and the bar count
already disagree.

## What I could NOT establish, stated plainly

I tried three times to measure the physical bar count and the methods do not
agree:

| method | orange bars |
|---|---|
| erode the raw mask | 26 |
| close holes, then erode | 284 |
| threshold local ink density | 42 |

The failures are instructive and are recorded in `wf/bar_census.py`: eroding the
raw mask fragments each bar because the type sitting on it punches holes (black
counted **1** against a catalogued 10); closing those holes then welds ordinary
body text into bar-shaped blobs (**284**); thresholding local fill separates
solid bars from 10-25%-covered type and passes a planted-line-of-type negative
control, but still returns a per-page distribution that disagrees with a
per-line band split of the same pages.

**So the true physical bar count is not established.** It is not 38, and it is
probably larger, but I am not publishing 76 or 42 or 33 as a measurement when
three methods disagree by an order of magnitude. Getting it right needs the
bars registered against the text line bands, which is a bigger job than the
remaining value justifies.

## Consequence for wf/highlight_bits.py

That module tested the highlight sequence as **38 ordered binary symbols** and
concluded it carries no Baconian plaintext (best decode z=+4.35 against an
English control of +21.26; only 8 of 60 decodes avoided out-of-range values).

That conclusion is **conditional on the 38-symbol alphabet**, which is now
known not to be a physical count. The out-of-range argument is the more robust
half and does not depend on the exact length -- a real Baconian ciphertext
never produces impossible letters at any grouping -- but the englishness result
should be read as "no plaintext at THIS segmentation", not as a closed channel.

The critic makes a second point I accept: the module collapses three ink
classes (22 orange, 10 black knockout, 6 white-on-brown) into binary. White
type knocked out of a black bar and dark type restored on a light bar over a
brown ground are opposite objects, so the collapse discards a symbol.
`highlight_color.py` already sweeps the three-symbol stream as base-3, which
`highlight_bits.py` did not cite.
