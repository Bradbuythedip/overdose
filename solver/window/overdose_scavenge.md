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

## Results landed after the first write (same day)

- **Two-serial combination sweep (`serial_combine.py --loop`) finished**: all
  families plus the transform closure to depth 4 (960,000 nodes, cap reported):
  0 index hits, 0 checksum-valid WIF. Closed.
- **Highlight runs as a pointer (`reading_hlkey.py`)**: 38 runs located; 4,630
  forms; 44.1M scripts; 0 hits; 100 checksum-valid mnemonic windows vs 117.6
  expected. Null.
- **Grille lens (scavenger, verified measurements)**: the 45 highlight
  rectangles measured properly for the first time (23 knock-out bars included;
  p79's bars tilt 2.9 deg); the body pages do NOT share one layout grid, only
  same-leaf pairs share a baseline phase; all 20 ordered page-pair overlays,
  absolute and mirrored, and every index-mode grille produce text fragments at
  the random-shift null (max z 2.1 over 40 tests). Null.
- **Pull-quote / furniture lens**: exactly TWO verbatim printings of the
  pull-quote, both on p78 (body, and white type inside the "X FUCK ALL X"
  scribble); the repo's "third printing" counted the transcript twice; p79's
  orange run is a different sentence. Running heads, folios, headline, byline,
  credit and sign-off carry no marks (mask-size differences are padding).
  **One physical mark**: in the scribble printing the 'o' of "love" is a closed
  ring with a horizontal bar through its centre exiting right into the 'v', in
  both the Canon layer and the phone photo; the printing's three other o's are
  clean rings and its e's have the bar inside the bowl. Font quirk or designer's
  mark cannot be decided at 200-215 dpi (no mask covers the scribble); a 600 dpi
  scan of that 3 x 2 cm patch would. Every reading it could imply
  (`reading_barred_o.py`: deletion, 0, e, o-slash, theta, the word, the position
  4/2 and letter 14, all-o variants, the four-line layout, the graffiti frame,
  plus the scavenger's own list): 177 forms x full stack, null.
- **PDF forensics on the column pages** (five lenses, skeptics pending): the
  Canon encoder inpaints under every mask (nothing hidden beneath text); the
  backgrounds are JPEG inside Flate (not lossless); highlighted phrases live only
  in the 200 dpi layer; facing-page set-off is strong and registered, reverse-side
  show-through is below 0.5/255 (pages 71 and 80 unrecoverable from this stock);
  all 22 orange bars are one ink, the "black" bars are the same dark warm brown
  as page 77's ground, the white bars are paper white, page 77 has no dark-on-dark
  content; the p79 pills are the p73 pill photograph reused (scale 0.760,
  rotation 10.15 deg) so pill geometry gives five readings not ten; 8 notes
  across 73/74, no plate letters legible beyond the serial; 14-15 bitcoin logos
  on the boxers.
