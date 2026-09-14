# Shared context for the strange-loop clue dissection

## Scope (measured, not assumed)
The Overdose column is printed pages **73-79** and nothing else. Each carries
the orange OVERDOSE running head (404-698 orange px); page 72 carries NUMBERS
and exactly 0. Page 72 and page 71 are OUT OF SCOPE. In particular the serial
**KB46279860 is NOT Keiser's** -- it is printed artwork on the NUMBERS page.

Page roles: 73 opener (title + byline + photo), 74 full-bleed photo,
75-79 body prose. Transcript: `transcript/p75.txt` .. `p79.txt` (1,258 words),
verified faithful (58% of characters checked glyph-by-glyph vs the 400 dpi
scan; the other 42% swept under complete single-character mutation).

## The setter's own clues
- Keiser, X, 4 Mar 2023: "I hid a private #Bitcoin key **encoded** in this
  piece I wrote for @BitcoinMagazine ... it's for 20 BTC."
- Keiser, X, 5 Mar 2023: **mirror writing**, citing G D Schott's paper on the
  phenomenon (PMC2117809). This is the ONLY explicit method clue.
- He has said key**s**, plural, "in the text".
- User intelligence: the prize is **unswept**, so its address is currently
  funded and IS inside our offline index. A correct derivation WOULD fire.

## The in-scope physical clues
- Banknote serial **CL76841714A**, district **L12** (L = San Francisco), on the
  $100 bills in the pages 73/74 photograph. The bills are photographed FLIPPED,
  so their text appears mirror-written on the page -- which is very likely what
  Keiser's mirror-writing clue points at.
- 38 highlighted spans, `highlights_ordered.tsv` (orange bar / knocked-out bar).
  Verified correct against the pages. **"Layer 1" is highlighted 3 times** on
  p75, which is editorially unusual.
- 3 marks nobody had catalogued, `marks_ordered.tsv`:
    p75 underline  "They discount stuff in advance."
    p75 underline  "protocol."
    p76 strikethrough "(and 10years of watching Peter Schiff miss buying bitcoin"
  The strikethrough stops at the LINE BREAK, not the sentence end.
- Artwork: gelatin capsules (p73, p79), barbed wire (p79), two hand-drawn X
  marks (p76), graffiti "SHIT" (p77), handwritten "MAX KEISER" + a drawn bitcoin
  symbol (p79), Keiser firing a money-gun (p74).

## Already ruled out -- do NOT repeat these
Roughly 75M derived addresses, 0 hits. Specifically:
- per-character bold (measured unrecoverable; font contextual alternates)
- whole-word bold, highlighted phrases as phrases, acrostics over them
- inter-word spacing / gap cipher (measurement sound, maps to no plaintext)
- the column's prose as natural units x the deep path set (2,864,435 addrs)
- the marks channel (447,740 addrs), incl. strikethrough-as-delete
- the serial CL76841714A + series + district (2,297,420 addrs), and every
  10^4 tail of the page-72 serial
- OP_RETURN / inscriptions on chain, blocks 0-829,999
- BIP-39 checksum-valid mnemonics from the prose (186 of them)
- classical steg in the JPEGs; the PDF image planes (scanner MMR residue)

## Tools you may use
`harness.py` (H.addrs_for_priv, H.Oracle, H.full_index), `hd_sweep.py`
(direct_keys, seeds_from, build_paths, derive, all_addrs). Script types covered:
p2pkh compressed+uncompressed, p2wpkh, p2sh-p2wpkh, p2tr.

## YOUR JOB
Do NOT run the oracle (memory contention). GENERATE candidate phrases only.
Write one phrase per line, UTF-8, to the file you are told to write.
Do NOT run git. Do NOT commit or push.
