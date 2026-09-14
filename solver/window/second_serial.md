# The second banknote serial, and why it sat unused (2026-09-14)

## It was found before, and abandoned for a reason that no longer holds

`serial_oracle.py` already knew about it:

```python
# Second note, ghosting through on page 72. Only four characters are legible
# ("KB 4?27"), so it cannot produce a 4-byte target; recorded, not used.
SECOND_NOTE_PARTIAL = "KB4?27"
```

Four characters is not enough for a four-byte value, so the whole
serial-as-checksum apparatus — the most powerful framing this project has,
because it is self-certifying and needs no chain — could not be pointed at it.
It was recorded honestly and set aside.

That reading came from the phone JPEGs in `public/images/`. Read instead from
the 400 dpi scan, with the faint layer isolated (keep mid-greys, discard both
the black display type and the white paper), all eight digits resolve:

```
KB 46279860
```

And it has the property that motivated the checksum idea in the first place:
`4 6 2 7 9 8 6 0` are all legal hex digits, so **`0x46279860` is a well-formed
four-byte value** — exactly the size of a Base58Check trailer. Same as
`0x76841714`.

`serial_oracle.py` now carries the full value; the partial is kept beside it as
a note of what the JPEGs could support.

## Every framing the first serial received

| framing | what it asks | scale | result |
|---|---|---|---|
| A textual | every case/spacing/reversal form through 7 hashes + 5 seed types x 72 HD paths x 25 scripts | 4,743,475 spks | 0 |
| B checksum | does any derivation reproduce `0x46279860`? 12 target readings — hex, decimal, both reversed, byte-swapped | 343 keys | **0** |
| C entropy | the value as an RNG seed across 7 generators (python, numpy, glibc, java, msvc, xorshift64, pcg32) | 280 keys | 0 |
| D stretched | pbkdf2-sha256/sha512, scrypt, WarpWallet over all 49 textual forms | 3,430 keys | 0 |
| F bip39 | the digits as wordlist indices, checksum-validated | 10 windows | see below |

## The one "hit", and its null

Framing F returned **1 checksum-valid mnemonic**. It is not a result:

```
10 windows tested, 1 valid
EXPECTED BY CHANCE: 0.62     (a 12-word window validates 1 in 16)
observed/expected: 1.60
```

With ten windows at p = 1/16, the probability of at least one is about 46%. The
phrase is the familiar degenerate artifact of the `mod` variant, drawn from the
lowest wordlist indices:

```
about absent ability absorb absurd abstract absent zoo aisle addict around alter
```

Swept anyway: 9,175 scriptPubKeys, 0 hits.

## Status

`KB46279860` is exhausted across textual derivation, the checksum framing that
its illegibility had previously blocked, RNG seeding, stretched KDFs and BIP-39
indexing. **All null.**

The repair that matters is to the record rather than to the puzzle: a value
this project had written off as unreadable is now readable, and the module that
wrote it off has been corrected so no future session re-derives the same
limitation from a lower-resolution source.
