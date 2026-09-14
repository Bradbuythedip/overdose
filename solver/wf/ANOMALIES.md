# Clue hunt: the author's fingerprints in the printed text (2026-09-14)

A setter hiding data in prose usually has to distort the cover text. This is a
systematic scan for those distortions, plus verification of the physical
elements earlier sessions took on trust. It found no cipher, but it does
produce the first complete anomaly catalogue for the piece.

## Deliberate typographic marks: there are only three

Bold is unusable (it tracks glyph identity, see `TYPOGRAPHY_CLOSED.md`), but
underline and strikethrough are unambiguous authorial acts. Across all five
text pages there are exactly three:

| page | mark | text |
|---|---|---|
| 75 L6 | underline | `They discount stuff in advance.` |
| 75 L18 | underline | `protocol.` |
| 76 L8 | strikethrough | `(and 10years of watching Peter Schiff miss buying bitcoin` |

Three marks cannot carry a key, and read together they say nothing.

The letter-spacing on p77 L25-27 (`Shitcoins, fiat and gold will starve to
death ... available energy.`) is **forced justification**, not a cipher: the
whole block is stretched to a flush right edge, word gaps included.

## Orthographic anomalies: five, of five different kinds

| anomaly | text | verified |
|---|---|---|
| unbalanced parenthesis | `(Sorry Bhutan, ...` opens and **never closes** | yes, on the page image |
| number disagreement | `that snake oil salesmen` (should be salesman) | yes, same line |
| internal capital | `mEthereum` (meth + Ethereum wordplay) | transcript |
| missing apostrophe | `Bitcoins coattails` | transcript |
| missing space | `10years` (inside the struck passage) | transcript |

Parenthesis count over the body: **11 open, 10 close**. The unclosed one is the
Bhutan aside on p77, confirmed against the scan rather than assumed from the
transcript, so it is a genuine printing-level anomaly and not a transcription
slip.

**Verdict: copy-editing, not cipher.** Five anomalies of five unrelated kinds
(punctuation, grammar, capitalisation, apostrophe, spacing) scattered across
1,282 words is what an unedited magazine column looks like. A marker system
needs to be uniform in kind so a reader can recognise it; these are not. Only
`mEthereum` is clearly intentional, and it is a joke, not a pointer.

## Wide gaps: six, all at rhetorical pauses

`Really?` / `Yes.` (10), `Fact:` / `It's Layer 1` (10), `at XRP.` / `Get ready`
(8), `Marty Bent —` / `who spend` (5), and two 3-space gaps. Every one sits at
a beat in the prose, which is how this designer sets a pause. Already measured
and swept as a digit sequence in an earlier session, 0 hits.

## Physical elements, re-verified directly

- **Capsules** (5 on p73, 6 on p79): plain orange-and-white gelatin, **no
  imprint, no numbers, no characters**. Checked at 3x on both pages rather than
  taken from the earlier note. The light flecks on the orange caps are
  specular highlights.
- **Banknotes** (p73, p74): a single note, serial `CL 76841714 A`, district
  `L12`, composited repeatedly at different rotations. Not several notes with
  different serials.
- **Ghost text** (p73, p74, p76, p78): set-off ink transfer from facing pages;
  p76's is p77's white block, p78's is p79's closing paragraph.

## External clue channels are closed

Every content host is refused at CONNECT: bitcoinmagazine.com, nasdaq.com,
x.com, nostr.com and every Nostr web client, medium, substack, threadreaderapp,
even google.com. Only search *snippets*, GitHub, and the package registries get
through, so the Nostr thread's seven notes and the other OVERDOSE columns
cannot be read from here.

## What the scan leaves

Nothing in the printed artefact is now unexamined. The anomalies are editorial,
the marks are too few, the artwork carries no characters, and the typographic
channel is a font artifact. This is consistent with `PREMISE.md`: the reason
nothing is found may simply be that there is nothing to find.
