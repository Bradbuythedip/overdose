# The serials, as deep as the material goes (2026-09-18)

Request: "dive deep as possible into the serial, maybe it's encoded." Two
banknote serials: **CL 76841714 A** (seal L12) on the $100 note cut out and
reused across pages 73/74, and **KB 46279860** on the washed-out note printed
into page 72's background. This records what was checked, what was found, and
what remains running. Nothing here is a hit; every null carried its control.

## 1. Forensics of the object

- **Not a documented prop serial.** Web search on `CL76841714A`, `76841714`,
  `KB46279860`, `46279860` returns nothing. Prop bills carry fixed fake serials
  that surface in search; this one does not. The bills show the Series
  1996-2006 $100 layout with the district code `L12` printed under the serial
  where a real note prints it, matching the serial's second letter (L = 12 =
  San Francisco). Consistent with a genuine Series 2001 note (prefix C).
- **The two serial instances agree.** A real note prints its serial twice.
  Page 73's big note shows the lower-right instance (`…6841714 A` beside the
  100); page 74's flying bills show the upper-left instance with `L12`. Same
  digits. The serial was not retouched to carry a message.
- **The KB note has a suffix letter nobody transcribed.** At 400 dpi,
  keeping only the mid-grey ink of the page-72 ghost note, a glyph follows the
  final 0 in the suffix position: a stem with a small top serif and a baseline
  foot. It reads **L or I**. `page72.py` recorded the serial with no suffix;
  `serial2_exhaust.py` guessed `A`. All 24 BEP suffix letters are now swept
  (`reading_kb_suffix.py`: 912 forms, 8.4M scripts, 0 hits, control OK).
- **Series 2001 is the year El Salvador dollarised** (Ley de Integración
  Monetaria, 1 Jan 2001). Thematic, and probably how a Series 2001 note comes
  to be in a 2021 photo shoot anyway. Recorded, not weighted.
- 30561854 and 123121574 in `p72.txt` are **not printed figures**: `p72.txt`
  is `page72.py`'s generated candidate list, and lines 148-150 of that module
  compute the sum and difference of the two serials. No page-72 / serial link.

## 2. What "encoded" was made to mean, and the result

| reading | module | scale | result |
|---|---|---|---|
| serial as key material, every framing (text, checksum, RNG seed, KDF, mirror, BIP-39 index, entropy) | serial_oracle / serial2_exhaust / serial_entropy / gen_serial_entropy_bip39 / mirror_serial | prior sessions | null |
| serials vs the funding-tx wallets, derivation and structure | serial_wallet.py | 144k keys | null; digits appear nowhere in the wallet data |
| zero-padded serial as raw key | (inline) | 120 | null |
| every clue x both serials, n-grams to 10 | clue_serial.py | 58.6M+ scripts/round | rounds 6-8 null; 9-10 running |
| **both serials combined**: arithmetic, interleave, digit-wise ops, letters+banknote meaning, 128-bit entropy readings, HMAC/PBKDF2/scrypt/WarpWallet pairings, text-index, transform closure | serial_combine.py | 10^8 scripts | families 1-5 null; discovery depths 2-4 running |
| the two notes as **Key A / Key B of a multisig** (1-of-2, 2-of-2, 2-of-3 with a clue key; P2SH/P2WSH/P2SH-P2WSH; c/u; sorted) | serial_cipher.py | 3,744 scripts | **null, planted control found** |
| serial as **ciphertext**: base58 (CL76841714A is valid base58; KB46279860 is not), base36/62, Roman CL=150, Salvadoran formats (+503 mobile, DUI check digit 5 for both, IPv4), digit-wise Caesar/Vigenere with clue key streams, elements, ordinal sat names | serial_cipher.py forms | 501 forms x HD = 4.87M scripts | **null** (its '25 checksum-valid mnemonics' were mnemonics the pipeline itself built from 32-byte decodings, valid by construction; fixed in 31f7844b) |
| the clue **languages' wordlists** (Spanish / French / Italian) over every index sequence incl. serial digit groupings | reading_lang.py | 55,368 mnemonic candidates | running |
| KB suffix letter, all 24 | reading_kb_suffix.py | 912 forms, 8.4M scripts | null |
| author-controlled channels: acrostics, first/last words per unit, rule-picked BIP-39 words as every 12-24 word window, 'El Salvador' as a position marker (lines 51/64, paragraphs 7/8) | reading_quick.py | 3,788 forms, 36.2M scripts | null; 91 checksum-valid windows vs 90.9 expected by chance over all window sizes -- exactly chance |
| critics' plugins: numismatic, wallet-format, setter, encodings | combo_*.py | ~32k forms | verified, sweep pending |

## 3. What this means

The serial has now been read as material, as a checksum, as an index, as
entropy, as a seed, as a salt, as a passphrase, as a path, as one of two keys,
as a phone number, as an ID number, as a Roman numeral, as base-58, and as a
ciphertext under the clue words, alone and paired with the second serial in
every arithmetic and textual combination, in four languages' wordlists. The
object itself shows no retouching and no prop provenance. If the serial
encodes the key, it does so under a rule none of this reaches, and there is
no second reading of the bill left to take from these scans. The one new
fact from this pass is the KB suffix letter, and it changes nothing.

## 4. The mirrored serial as entropy, judged by the magazine (2026-09-18, user's idea)

Criterion independent of the chain: if the serial a reader sees in the mirrored
note (A 41714867 LC; the KB note mirrored I 06897264 BK) were the entropy of a
mnemonic hidden "in the text", the mnemonic's words should occur in the column
far above chance. `reading_mirror_entropy.py`: every mirror / rot180 form of
both serials plus the originals as controls, extended to 16 or 32 bytes every
way a person would (209 entropies), in four languages (836 mnemonics), scored
by words-in-article against 1,500 random mnemonics per size and language.
Best: 6 of 24 words (random 24-word English mnemonics reach 5 at the 99th
percentile and 7 at the max), i.e. expected given ~100 candidates. Mirrored
forms average 0.22 words in the article, originals 0.33. The 209 entropies
also swept against the index with 9 passphrases x 72 paths: null. The inverse
(every checksum-valid mnemonic window formed by the column's own wordlist
words, converted back to entropy and searched for the serial digits) finds no
8-digit match. The serial is not the entropy of a mnemonic hidden in the text.
