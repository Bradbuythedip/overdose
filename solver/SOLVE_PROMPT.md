# Hand-off prompt: Max Keiser "Overdose" 20 BTC puzzle

Paste everything below the line into a fresh capable model with code execution.

---

You are attacking an unsolved Bitcoin puzzle. Do not guess, do not present a
plausible-sounding answer, and do not produce a private key you have not
verified. A wrong key wastes real effort. If you find nothing, say so.

## The target

Max Keiser hid a private key for 20 BTC in his column "OVERDOSE", published in
**Bitcoin Magazine Issue 24, the El Salvador edition, pages 73-79**.

Four statements from Keiser, dated exactly by decoding the tweet snowflake IDs
(`(id >> 22) + 1288834974657` ms), not by reading article datelines:

| date | tweet | content |
|---|---|---|
| 2022-02-11 | 1492173067723886594 | Bukele photographed holding the printed El Salvador edition — **the article was public by this date** |
| 2022-12-26 | 1607378060172460032 | "Like **George Sand's hidden cryptography**, I have hidden private key**s** in the text" |
| 2023-03-04 | 1632068898169450497 | "Nobody's figured it out yet, but it's for 20 BTC" |
| 2023-03-05 | 1632391507008278528 | **mirror writing**, linking the paper PMC2117809 (Della Sala & Cubelli) |
| 2023-12-30 | 1741134493769965603 | "Obviously, **'El Salvador' is a clue**" — replying about this puzzle |

Note the article is from **February 2022**, not March 2023. Most public
discussion gets this wrong and mis-dates every timing argument as a result.

## What is already eliminated — do not redo any of this

Roughly 72 million derived addresses, all scored against a complete offline
index of all 56,795,328 funded Bitcoin addresses, so a hit registers regardless
of balance, spend history or funding date:

- **Fast hashes** over every corpus: sha256, double-sha256, both sha512 halves,
  sha3-256, blake2b, keccak — across the article's full prose, every contiguous
  word n-gram (2..12) in as-is/lower/upper/title/punctuation-stripped/
  whitespace-stripped forms, plus full reversals, word-order reversals,
  per-word reversals and atbash of all of them.
- **Stretched KDFs**: WarpWallet (verified against its published test vector,
  derives 1J32CmwScqhwnNQ77cKv9q41JGwoZe2JYQ), PBKDF2-SHA256/SHA512 at
  1k-65k iterations across 8 salts, scrypt at N=2^12/2^14/2^18.
- **BIP-39**: 281 BIP-39 words appear in the prose (462 under the 4-letter
  abbreviation rule); 186 checksum-valid mnemonics extracted and HD-derived
  across 72 paths x 5 script types x 8 passphrases, plus a deep index scan
  (accounts 0-2, change 0/1, indices 0-49).
- **Null ciphers**: George Sand alternate-line readings (full lines, steps 2-5,
  all offsets, per page and whole article, forward and mirrored), acrostics,
  telestichs, first/last word of every line, every-Nth word/letter/line,
  highlight-run concatenations and acrostics, line-length sequences.
- **Printed key formats**: 153,192 characters across 84 selection rules and 6
  scopes, forwards and mirrored, checked against the formats' OWN checksums.
  Zero checksum-valid WIF or BIP38.
- **Image forensics**: no trailing data, no COM/EXIF/APPn payload, no LSB
  steganography; the quantization tables are byte-identical across all seven
  page images, so the files were never re-encoded.
- **Per-character bold**: measured unrecoverable at the available ~215 dpi. A
  visibly-bold word measures 3.3-6.4 stroke width while regular text on the
  same line sits at 3.3-3.8.
- **On-chain markers**: all 870 named candidate addresses absent from 2.2M
  lines of embedded chain text (blocks 0-829,999, including input scripts).

Two statistical results that closed families rather than merely failing to find
things in them, both of which required an **operation-matched null** — a
frequency-matched null gave false positives at z=+5.6 and z=+18.8:

- No every-Nth extraction contains hidden English at any N, offset or direction.
- No acrostic/column reading does either; the best one scores *below* the mean
  of the same reading taken from word-shuffled copies of the article.

## Chain-side state

962 addresses hold exactly 20.00000000 BTC. That property therefore
discriminates nothing — 20 BTC is a popular round holding, about 7x its
whole-BTC neighbours (19 BTC: 142, 21 BTC: 94). Any argument of the form "this
address is the one because it holds exactly 20 BTC" is circular.

870 of the 962 are named. Three are "personal peel" shaped (1-2 inputs, payment
plus change, not an exchange sweep) and funded near publication:
`1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t` (2 Nov 2021),
`1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi` (27 Feb 2022, 16 days after publication),
`1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64` (1 Jun 2022).

`1Q7kHGPCrMWgB16EvhZpqSovc1LLPo3o28` is **ruled out**: its funding transaction
is a 66-input consolidation and `18r8ftfovKza9cDEvVRaqRjkaDPXj16dAQ` appears
twice among the inputs — the documented CashFX Group Ponzi deposit/withdrawal
wallet, whose published pattern is "deposits grouped together and sent to
multiple withdrawals in single transactions".

Understand that **an address is not a key**. HASH160 does not invert. Finding
the right address gets you nothing without a derivation, and a derivation can
be tested without knowing the address at all.

## The transferable method

Do not use the blockchain as your oracle. It is slow, it needs API access, and
it cannot see a key that was printed rather than derived, or an address that
was never funded.

Use the key format's own checksum instead. A WIF carries a 4-byte checksum: a
1-in-4-billion filter needing no address and no network. If a selection rule
over the article's characters yields a checksum-valid WIF, that is essentially
proof of the rule. Caution, measured: this holds for WIF and BIP38, but the
Casascius mini-key format's only test is a single checksum byte after an 'S'
prefix — about 1 in 14,848 — so mini hits are mostly noise and need a second
filter. BIP-39's checksum is 1-in-16 per mnemonic and likewise weak alone.

## Where to actually look

1. **Other issues.** The Dec 2022 tweet says key**s**, plural, "in the text" of
   his column generally. OVERDOSE ran across multiple issues; only Issue 24 has
   been examined. If each column carries a fragment, everything above was done
   on a fraction of the material. Obtaining other OVERDOSE columns is probably
   the single highest-value action available.
2. **The linked paper as a book-cipher key.** Keiser did not merely say "mirror
   writing" — he linked a *specific document*, PMC2117809. A setter linking a
   document is a classic book-cipher pointer. Try the article as index into
   that paper's text, and the reverse.
3. **The highlight overlay as spatial data.** The orange and black bars are
   positioned deliberately. Their coordinates, lengths, or per-line counts are
   a numeric sequence nobody has treated as data.
4. **"El Salvador" as a keyword, not a passphrase.** Vigenere, Playfair, or a
   running-key cipher over the article with EL SALVADOR as the key has not been
   tried — everything so far treated it as a hash input or a salt.
5. **It may never have been funded.** Every negative here is consistent with
   that, and it is unfalsifiable from outside. Do not force a solve.

## Output contract

For any candidate: state the exact derivation, show the resulting address,
and state whether it is funded. If a claim rests on a control, run the
control and show it. If your method returns nothing, report the null and what
would have had to be true for it to fire. Never present an unverified key.
