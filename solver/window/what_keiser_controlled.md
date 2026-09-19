# What Keiser controlled — a trusting-trust audit (2026-09-19)

Ken Thompson's point in *Reflections on Trusting Trust* is not that you should
read the source more carefully. It is that the backdoor lives in a layer nobody
audits, because everybody trusts it. He put it in the compiler, and `login.c`
stayed clean forever.

This project has audited the printed page for four years. **The printed page is
not what Keiser wrote.** It is what a Bitcoin Magazine designer produced from
what Keiser wrote. Between his manuscript and the artifact sit a copyeditor, a
typesetter who chose every line break, a designer who chose the highlights, the
bold, the $100 cutout and its serial, the rotated sidebar, and a production
department that assigned the page numbers.

So the question was never "what is hidden in the page". It is **"what could he
have put there and been certain would survive?"** — and, separately, how much
of the search has been spent reading the art department's output.

`provenance_audit.py` measures all of it. Run it.

## 1. The serial's motivating premise is a tautology

`serial_oracle.py:9` states the reason the serial-as-checksum branch exists:

> the serial's eight digits are 76841714, and every one of those is a legal
> HEX digit, so `0x76841714` is a well-formed FOUR-BYTE value

`second_serial.md` calls that branch *"the most powerful framing this project
has, because it is self-certifying and needs no chain"*, and applies the same
reasoning to the second note: *"`4 6 2 7 9 8 6 0` are all legal hex digits, so
`0x46279860` is a well-formed four-byte value."*

US banknote serials are eight **decimal** digits. Every decimal digit is a
legal hex digit. Measured:

```
random 8-digit US serials that are valid 4-byte hex: 200,000/200,000 = 1.0000
```

The property holds for **every banknote ever printed**, with probability 1. It
is not a coincidence worth explaining and it is not evidence of design. The
searches run under that framing are still valid as searches; what is void is
the reason they were prioritised, and the claim that the framing was
"self-certifying".

## 2. The $100 note is one asset, duplicated

Page 74 is a composite: Keiser in a field, firing a revolver, banknotes in
flight. Reading the cutouts directly off `IMG_6245.jpeg` at 4x:

| copy | serial | district | orientation |
|---|---|---|---|
| large, right of frame | `CL 76841714 A` | `L12` | upright, curled |
| left edge, torn margin | `CL 76841714 A` | `L12` | **rotated 180°** |

Real banknotes have unique serials. Two notes in one photograph carrying the
*same* serial cannot be two notes. It is one cutout, placed repeatedly under
rotation — and visually there are six to seven placements.

This settles the duplication, and it kills one reading outright: a setter
encoding ~27 bits does not paste the same 27 bits seven times across a spread.
The repetition is a layout operation.

**It does not settle who chose the bill.** Two readings survive:

- (a) the designer pulled a stock cutout of a curled $100 — the note is the
  pre-2013 design, Series 2001, San Francisco, i.e. an old stock image; or
- (b) Keiser supplied a photograph of a specific note and the designer
  duplicated it.

Under (b) the serial is his and the branch is live. A search for `CL76841714A`
returns nothing — stock libraries are not indexed by serial, so this cannot be
resolved from here. **It is exactly the P6 question: ask the interior
designer.** One email decides whether ~2.3M derivations were aimed at the art
department's clip art.

## 3. The text was never copyedited — the one positive result

Four author errors and an unbalanced parenthesis reached print in a
professionally typeset national magazine:

```
parentheses: 6 open, 5 close -> UNBALANCED   (line 78 "(Sorry Bhutan," never closes)
FOUND  10years (no space)
FOUND  Bitcoins coattails (no apostrophe)
FOUND  pouring over (should be poring)
FOUND  that snake oil salesmen (number disagreement)
```

Bitcoin Magazine set Keiser's file essentially as received. That matters more
than it looks:

- The printed character stream **is** his manuscript. The transcript, modulo
  transcription error, is his source — not a rendering of it.
- So the text channel is genuinely his, and the nulls over it mean something,
  unlike the nulls over the visual channels.
- `no_digital_footprint.md` worried the transcript is the only digital copy and
  therefore load-bearing with nothing to check it against. This is a partial
  check: the surviving errors are a fingerprint of an un-normalised pipeline.

## 4. Where the search actually went

STATUS.md's table is the only itemised derivation count in the repo. Tagged by
who controlled the channel each corpus reads:

```
designer    31,081,230   46.4%
author      17,693,825   26.4%
mixed       18,256,520   27.2%
                         (sums to 67,031,575, reconciling with STATUS.md)
```

**46.4% of the audited search went into channels Keiser did not control.** The
single largest line item — `line/column readings + every-Nth`, 26,143,245
derivations, **39% of the entire project** — reads the typesetter's line breaks.

## 5. The Sand problem

The one device Keiser named is a **line** device: alternate lines, and
first-word-of-each-line. `sand_device.py` went to real trouble to verify the
transcript is line-faithful against the scan geometry (83 of 95 recoverable
lines at offset zero) so the device could be run on the printed lines "for
real".

But Keiser did not choose the printed lines. A Bitcoin Magazine designer did.
He could not have encoded anything in them at writing time, and he could not
have known what they would be.

Three ways out, and they are not equal:

1. **Sand is a loose metaphor.** He meant "there is something hidden in the
   prose", not a specific line-parity algorithm. Most likely, and consistent
   with a non-technical setter.
2. **His unit is the sentence**, not the printed line — a word-processor user's
   "line". `wf/sand_sentences.py` already tests this on sentences and
   paragraphs, and it is the right reading of the device.
3. **He built the key from the printed artifact after publication.** He had the
   issue by Feb 2022 and announced the prize in Mar 2023, so this is
   chronologically open, and under it the designer channels are live again. But
   it contradicts the framing of both statements — "I have hidden private keys
   **in the text**" and "a private key encoded in **this piece I wrote**" — and
   it would require a rule he never hinted at.

## What this changes

Not a solve, and it does not produce a key. What it does is re-rank the
remaining space:

- The visual branches (serial, highlights, gaps, line-parity, acrostics,
  page furniture) are **downstream of the author** and should not be extended
  without first answering P6. That is 46% of the search so far.
- The text branch is **the only one provably his**, it is now known to be
  un-normalised, and it is null under both oracles: ~69M chain-scored
  derivations, and checksum-first sweeps that need no chain
  (`wif_hunt.py`: 153,190 chars, 6 scopes x 84 streams, 0 valid WIF/BIP38;
  `schott_index.py`: 848 book-cipher readings, 0).
- Which leaves `final_assessment.md` §5 branch 1 — **never funded** — as the
  hypothesis the evidence keeps re-selecting, now for a second, independent
  reason: the channels that look designed are the ones he could not design.
