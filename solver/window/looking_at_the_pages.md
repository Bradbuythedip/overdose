# What I found by actually looking at the pages (2026-09-14)

Three sessions of statistics on derived files, and nobody had opened the
images. Six findings, in descending order of how much they change.

## 1. The scan-derived corpus is 61% of the article

Every glyph-level conclusion in this repo — `bold_cipher_resolved.md`,
`typography_closed.md`, the mirror scan, the per-character work — came from
`wf/glyphs_p*.tsv`. Nobody measured what fraction of the page those files hold.

| page | lines printed | lines got | chars printed | glyphs got | coverage |
|---|---|---|---|---|---|
| 75 | 33 | 27 | 1,363 | 1,103 | 81% |
| 76 | 31 | 25 | 1,298 | 1,007 | 78% |
| 77 | 32 | 21 | 1,277 | 593 | **46%** |
| 78 | 23 | 20 | 1,037 | 796 | 77% |
| 79 | 26 | 6 | 1,022 | 149 | **15%** |
| **ALL** | **145** | **99** | **5,997** | **3,648** | **61%** |

Two causes, both visible the moment you look:

- **p77 is white type on a dark brown ground.** A polarity fix was applied at
  some point; it is still at 46%.
- **p79's body text is set on a CURVED BASELINE.** The lines arc across the
  page. A line-finder that groups glyphs by shared horizontal `y` cannot group
  text whose `y` changes mid-line, so it recovered 6 of 26 lines. That page is
  the article's **conclusion** — "To wrap this up..." — and it is the
  least-covered page in the corpus.

Reproduce with `scan_coverage.py`.

## 2. Pages 73 and 74 are not in the transcript at all

`article_transcript.txt` holds pages 75–79. The spread is 73–79. Missing: the
`OVERDOSE` title block, the `with Max Keiser` byline, the `@ANNABELLEBAZ`
photographer credit, the five pills, and **both banknotes**.

## 3. The banknote is one cutout, reused

p73 carries one $100 bill; p74 carries six or seven in flight. Read at 4x,
every legible one is the same note: `CL 76841714 A`, with `L12` under the `CL`.
The designer composited a single asset. So the serial is not a sequence — it is
**one deliberate value, shown repeatedly across two pages**. That is emphasis,
and it is the reason the serial deserved the attention it got.

## 4. The six wide gaps are typesetting, not a channel

The transcript preserves six intra-line multi-space gaps, widths
`[10, 3, 10, 3, 8, 5]`. Measured against the font's character pitch from the
glyph geometry, p75 L4 (`Really?` -> `Yes.`) is 9.82 cells — the transcriber's
count of 10 is accurate, so the sequence is real.

It is still not a message. Five of the six are **justification artifacts**:

- `stock traders,` -> `central bank arsonists,` sits inside the black highlight
- `Fact:` -> `It's Layer 1` sits inside the orange highlight
- `at XRP.` -> `Get ready` sits inside the white highlight
- `Marty Bent —` -> `who spend their days pouring over spreadsheets` is a line
  stretched flush to both margins

A highlight is drawn as a rectangle and its contents are justified to fill it.
The sixth, `Really?` -> `Yes.`, is a rhetorical beat — a question and its
answer spaced for timing. All readings of the sequence (as digits `10310385`,
as letters, as word indices, as cumulative offsets) were derived and swept:
946 keys, 23,650 scriptPubKeys, **0 hits**.

## 5. Bold is the lettershape, confirmed on a cleaner test

The bold detector is high-precision and low-recall: on p75 L6 it flags 14 of 56
glyphs and **all 14 fall inside "They discount stuff in advance.", none
outside**. So its per-character output is not noise about *where* bold is.

But `P(bold | character)` is strongly non-uniform — 0.158 for `c`, 0.476 for
`a`, chi-square 93.9 on df 22, **X2/df = 4.3, p ~ 5e-11**. Bold tracks letter
identity. That is the font, exactly as `bold_cipher_resolved.md` concluded, now
with a test that states its own power.

## 6. Small corrections to the transcript

- The signature on p79 is **`MAX ♡ KEISER`** — a heart between the names. The
  transcript records `MAX KEISER`. In an article whose thesis is the "love
  economy", that glyph is content, not decoration.
- `10years` on p76 is **confirmed in the ink** (no space), and the adjacent
  black highlight reads `Forty years` spelled out, while p79 prints `10 years`
  with a space. Three renderings of the same quantity, one anomalous.
- `mEthereum` on p75 is **not** an error. It is "meth lab" -> "the mEthereum
  lab", wordplay matching the OVERDOSE drug theme.

## The structural argument that closes typography regardless

None of the above resurrects the typographic hypothesis, and the reason does
not depend on coverage:

> **Keiser wrote a column. Bitcoin Magazine's designers set the type.**

He cannot choose glyph weight, glyph position, letter spacing, or where a
highlight box justifies its contents. Any channel requiring sub-point control
of the page is a channel he did not have. The one typographic thing an author
*does* control is the spacing in his own manuscript — which is why the six gaps
were worth measuring, and why finding them to be justification matters.

What he controls is the words. Those have been ground exhaustively.
