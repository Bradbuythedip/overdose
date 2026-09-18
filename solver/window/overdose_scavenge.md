# Scavenging OVERDOSE (pages 73-79) in continuous mode (2026-09-18)

Scope per the user: the column itself, not page 72. Everything here is
measured or swept with controls; nothing is a hit.

## The PDF's own structure, applied to the column
- The Canon MRC scan separates text into bilevel masks by ink colour. On each
  body page (75, 76, 78, 79) it produced exactly one body-text mask, painted the
  same dark warm grey (rgb ~0.40/0.35/0.37) on every page. Words in a second ink
  would have been split into their own mask, as the highlight-bar text was
  (p79 masks 64/65: bar + glyphs, differing pixels spell known body text).
  **No second-ink channel exists in the body text.**
- Page 77 (dark ground) has no mask: its type exists only in the 200 dpi colour
  layer, and the phone photo is ~220 dpi. Every glyph-level measurement of 77
  was made at about half the resolution of the other pages. A 600 dpi photo-mode
  re-scan of page 77 is the one cheap physical action left.
- The small edge masks on 78/79 are the vertical running head and the scanned
  page edge over a pink underlay. Nothing printed.

## Author-level tells (`reading_scavenge.py`, quick tests)
- The column never uses key, wallet, seed, address, private, hidden, mirror,
  code, cipher or clue. "Salvador" 2x, "word" 1x.
- rot180-readable words: 1 of 1,276 ("dip"). Letter frequencies normal; no
  letter absent.
- The 30-bit Bitcoin/bitcoin capitalisation sequence
  `111111111010000101000101011111` decodes under Bacon (both polarities) to
  `??QUK?` / `ABPLVA`, under 7-bit ASCII to nothing printable, under 11-bit
  wordlist indices to `zero any`. The 44 all-caps words in order are the known
  display phrases.
- Geometric readings of the printed block (k-th character column per line
  k=1..40 and from the line end, diagonals both slopes, k-th word per line
  k=2..8 and their initials, punctuation counts per unit) and every acrostic
  decoded under Caesar 1-25, Atbash and Vigenere/Beaufort with 14 clue keys:
  1,867 strings, scored for English against shuffled baselines. Top margins
  ("seashns borace", "toeth enwb giifu", "GBLVRMGUTIPHZFFSKIBARS") are noise;
  the multiple-comparison ceiling over 1,810 strings exceeds them. Swept: 17.1M
  scripts, null.
- The highlight runs as a POINTER (`reading_hlkey.py`): the word after / before /
  n-th after each run, run lengths and positions as digit strings and as
  wordlist indices in four languages, the sentences they end, the word after
  each all-caps word, the quoted spans. Swept (result in its .out).
- Page furniture with the designer identified (`reading_furniture.py`): her
  handle and name, byline forms, running head, sign-off, issue names. 167 forms,
  1.5M scripts, null.

## The user's idea: the mirrored serial as entropy, judged by the magazine
See `window/serial_deep_dive.md` section 4. 209 entropies x 4 languages, words-
in-article vs 1,500 random mnemonics per size: best 6/24 (chance 99th pct 5,
max 7), expected over ~100 candidates; mirrored forms average fewer article
words than the originals. Extended to the 350 RNG/KDF-derived entropies from
prior sessions: best 5/24 = the chance 99th percentile. The inverse (valid
mnemonic windows from the column's own wordlist words -> entropy -> serial
digits?) finds no 8-digit match. No serial digit run occurs in the column's
wordlist-index or position streams.

## Still running when this was written
Five-lens scavenger workflow (highlight bars as a Cardan grille over other
pages; the three pull-quote printings diffed glyph by glyph; the photographs as
a rebus; author tells; the typographic channels decoded rather than counted),
each finding re-measured by a skeptic; the PDF forensics workflow; the depth-4
discovery closure; the language wordlist run; the forced-HD wallet-format run.
Their results are appended below as they land.
