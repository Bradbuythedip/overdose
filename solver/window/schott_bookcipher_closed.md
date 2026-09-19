# P2 closed: PMC2117809 as a book cipher does not fire (2026-09-18)

Keiser linked exactly one document — G D Schott, *Mirror writing: neurological
reflections on an unusual phenomenon*, PMC2117809 — on 2023-03-05. A setter who
names one specific document is doing what book-cipher setters do. This records
the test, run to completion, with its controls.

## What was already here, and why it was the wrong oracle

`gen_schott.py` indexes the paper with the banknote serial and the citation
numbers. But it emits every reading as a **phrase for hashing**: the readings
become brainwallet passphrases scored against a chain oracle. That oracle is
wrong twice over —

1. it requires the prize to have been funded, which is the project's single
   largest open question (`final_assessment.md` §5 ranks "never funded" as the
   most probable branch); and
2. a chain null cannot distinguish a *correct extraction* from a wrong one.

A book cipher does not produce a passphrase. It produces the key. So the
readings should be judged by the key format's own checksum, which needs no
chain and no funding assumption.

## What `schott_index.py` does

Every number printed in or attached to Issue 24, used as an index into the
paper (and, in the reverse direction, into the article):

| set | values |
|---|---|
| serial | 76841714 in every grouping: singles, pairs, triples both ways, quads, whole |
| pages | 73–79 |
| banknote | district 12 (`L12`), letters C=3 L=12 (`CL`), series year 2001 |
| body numbers, print order | 2008, 1, 1, 1, 1971, 10, 1, 2011, 1, 42, 20000, 100000, 2017, 12000, 51, 85, 2, 51, 95, 1969, 10 |
| prize/issue | 20, 24, 51, 42, 12 |
| citation | 2007, 78, 5, 13, 2006, 94870 |

Each set forwards and reversed, 0- and 1-based, against the paper read
forwards and **mirrored** — mirror writing being the device he named — over
word, line and sentence units, plus the classic two-dimensional form where
consecutive numbers are read as *(line, word-in-line)* pairs.

From each selection: the joined words, the joined words with no spaces, the
initials, the initials uppercased, the final letters, and the initials
reversed.

## The oracles, and why they are sharp

| test | false-alarm rate |
|---|---|
| WIF 51/52 char, 0x80 prefix, 4-byte double-SHA256 | ~1 in 4.3e9 |
| BIP38, 58 char, `6P` | ~1 in 4.3e9 |
| mini key, 22/26/30 char, `S`, sha256(k+'?') starts 0x00 | ~1 in 14,848 |
| raw hex, 64 char, in curve range | — |
| BIP-39: every selected word in the wordlist **and** checksum valid | see below |

The BIP-39 arm is the one worth stating plainly. On the article itself, BIP-39
is noise: the only test there is the 1-in-16 checksum, and `STATUS.md` records
18 valid 12-word windows against ~17 expected. Indexing into the **paper** adds
a second and far stronger condition — every selected word must independently
land in the 2048-word list. Measured on this paper:

```
paper tokens that are BIP-39 words: 1639/8151 = 0.2011
P(12 randomly-indexed words all in the list) = 4.37e-09
```

So an all-BIP-39 selection here would be signal, not a coincidence to triage.

## Controls

All five pass before the scan is allowed to report anything; the tool exits if
any fails, so a broken checksum cannot manufacture a null.

```
known WIF (privkey=1) recognised: True
corrupted WIF rejected: True
BIP-39 vector validates, corrupted one fails: True
1-based index into 4 words -> ['alpha', 'charlie']
out-of-range hex rejected: True        # >= curve order n
```

## Result

```
readings evaluated          : 848
checksum-valid key strings  : 0
all-BIP-39 word selections  : 0
null (4,000 random index sets): 0 key hits, 0 all-BIP-39
```

**The book cipher does not fire.** The null run confirms the oracle is not
merely silent because it is broken — it is silent on random input too, at the
rate the checksum arithmetic predicts.

## What this rules out, and what it does not

Ruled out: the numbers printed in Issue 24, used as positions into the document
Keiser linked, under every grouping, base, direction and unit a reader would
try, do not select a key in any standard printed format.

Not ruled out: an indexing rule that needs the paper's *printed* pagination
(the PMC HTML reflows; the journal's 78:5–13 page and line numbers are not
recoverable from this text), or a keyed offset this scan has no way to guess.
Both would need the typeset PDF, which is the same artifact wall as everywhere
else in this project.

## Also corrected here

`article_numbers()` was harvesting the transcript's own page markers
(`=== PAGE 75 (IMG_6246) ===`) as if 75 and 6246 were printed in the body.
They are not. The body-number set above is the corrected one.
