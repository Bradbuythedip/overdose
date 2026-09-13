# The banknote serial read as a CHECKSUM (2026-09-13)

Prior work treated the $100 note's serial `CL76841714A` as *material* — a
passphrase, a seed, a brainwallet input. 4,642 derivations, all null. This
tests it as a *checksum* instead, which is a different hypothesis and a much
more useful one.

## Why it is worth testing

The serial's eight digits are `76841714`, and every one is a legal hex digit,
so `0x76841714` is a well-formed **four-byte** value. Four bytes is exactly the
size of a Base58Check trailer:

```
WIF        base58check(0x80 || key [|| 0x01])   last 4 bytes
address    base58check(0x00 || hash160)         last 4 bytes
```

That coincidence is worth an afternoon because of what it would fix. Every
sweep in this project needs the **chain** to recognise success, and the chain
is blind to a key that was never funded or was swept years ago — which is
precisely the state this prize is most likely in, and the reason every "0
funded hits" here is uninformative about (a) the key never existing versus (b)
it existing unfunded versus (c) it having been taken. A checksum needs nothing
external. It certifies a derivation on its own.

It is also very cheap. A WIF checksum is two SHA-256s over 33 bytes with **no
elliptic-curve multiplication**, so this filter runs orders of magnitude faster
than an address sweep.

## Targets

"Which four bytes" is itself a guess, so eight distinct values are tested: the
digits as hex, as a decimal integer (big- and little-endian), both reversed —
the note is printed mirrored on page 73, this project's one demonstrated
mirror — and every byte-swap of those.

```
76841714  14178476  41714867  67487141
049482f2  f2829404  027c84b3  b3847c02
```

## Results — four tests, all null, all with controls

**1. Is the serial itself a valid Base58Check string?** If Keiser picked this
note because its serial self-validates, that would be a designed signal.

```
CL76841714A       no valid base58check framing at any length
CL76841714        no valid base58check framing at any length
76841714A         no valid base58check framing at any length
L1276841714A      no valid base58check framing at any length
CONTROL 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa   VALID, payload 0062e907b1...
```

**2. Does any exactly-20-BTC address have that Base58Check checksum?**

365 base58 addresses tested. **505 of the 870 are bech32 and were NOT tested** —
bech32/bech32m carry a six-character BCH checksum, not a four-byte trailer, so
the reading cannot apply to them. Reporting "870 addresses, no match" would
overstate the coverage by more than half. No match. Expected false positives
6.8e-07.

**3. Does any address in the 1.05M rich list?**

696,256 base58 addresses tested, 448,733 bech32 skipped. **Control: the genesis
address is present in the dump (2 occurrences)**, so a null is meaningful. No
match. Expected false positives 0.0013.

**4. Does any derived key have that WIF checksum, or any candidate phrase that
digest?**

- *Phrase-checksum oracle* — the strongest form of the idea: if the serial is a
  verification tag for "you extracted the right words", then some standard
  digest of the correct phrase begins or ends with those four bytes. No key
  format, no curve, no chain. 36,658 phrases x 4 encodings x 8 digests x 2
  positions x 8 targets ≈ 18.8M tests. Control with a planted checksum fires.
  **0 hits**, expected false positives 0.004.
- *WIF-checksum sweep* over the union corpus (36,658 phrases x 7 direct key
  hashes + 5 seed derivations x 72 HD paths). Control: a constructed key's real
  checksum is found when planted as a target; a one-bit change does not
  collide. Running; results appended below.

## What a hit would have meant, and what these nulls mean

A 4-byte match is 1 in 2^32, and the expected false-positive counts above are
all far below 1, so any hit would have been strong evidence rather than noise —
and, unlike every other test in this project, it would have been evidence that
did not depend on the coins still being there.

The nulls do not disprove the idea. They say: under eight readings of the
serial, no address in the funded or rich sets, and no phrase or key this
project has ever generated, carries it as a checksum. If the serial is a
checksum, then either the reading is one not tried, or it certifies material
this project has not yet produced — which points back at the same gap
everything else does: the other OVERDOSE columns.

## Also recorded

A **second note** exists. Page 72 carries show-through of a serial beginning
`KB 4?27`; the third and fourth digits are ambiguous and the rest is
overprinted. Only four legible characters, so it yields no 4-byte target and
cannot be used here. It matters only because every prior pass assumed the
artwork held one note.

The `CL76841714A` reading was re-verified against the 400 dpi scan: the tail
reads `...841714A`, matching. The head is behind a fold on page 73, and the
note on page 74 resolves to roughly 40 pixels in the 200 dpi background layer,
so the limit is the photograph, not the scanner.

No private key.

---

# Addendum: the bill on page 73 is ROTATED, not mirrored (2026-09-13)

This repo asserted, in `gen_banknote.py` and in `mirror_writing_scan.md`, that
"on page 73 the bill is printed fully reversed, every glyph on it reading
backwards", and treated that as the one demonstrated instance of Keiser's
mirror-writing clue. A parallel analysis went further and read the page as
printing the suffix-first form `A 41714867`.

Both are wrong, and the transform is directly testable. Taking the page-73
serial region and applying each candidate transform:

| transform | result |
|---|---|
| **rotate 180°** | **reads `...841714 A` cleanly, glyphs upright, the `100` upright** |
| horizontal mirror | glyphs laterally inverted, unreadable |
| vertical flip | glyphs upside down |

Rotation makes it readable; reflection does not. **The bill is printed 180°
rotated.** A 180° rotation is not a mirror: it reverses order AND turns each
glyph upside down, where a reflection inverts glyphs laterally and leaves them
in place.

Three consequences:

1. **Page 73 is not a visible instance of "mirror writing."** There is no
   reflected text anywhere in this issue that we have found. The 2023-03-05
   clue has no printed referent on these pages.
2. **`A41714867LC` is not what a reader sees.** Facing an upside-down bill, a
   reader tilts their head or turns the page and reads `CL76841714A`. The
   reversed string only exists if one chooses to read rotated glyphs as though
   upright — and the note's `4`s and `7`s make that impossible anyway, since
   neither maps to a digit under rotation. The optical argument that the serial
   is a poor Leonardo candidate is correct, and it defeats the premise it was
   offered to support.
3. **The rotation is probably not authored at all.** Every page in the 400 dpi
   scan is 180° rotated, the bills in the page-74 photograph lie at every
   angle, and the credited photographer is @ANNABELLEBAZI. An upside-down
   banknote in a dropped-money photoshoot is what a photograph looks like, not
   a cipher.

Swept anyway, since the readings were cheap: the reversed-serial digit pairs
(41, 71, 48, 67), the forward pairs (76, 84, 17, 14), the plate readings 21 and
21L, and the full reversed digit string, as indices into the column's words,
lines and sentences, 0- and 1-based, forward and mirrored — 265 readings,
486,275 addresses, **0 funded hits**. The word-level readings are ordinary
prose fragments ("in after system paper", "stuff time nervous white").
