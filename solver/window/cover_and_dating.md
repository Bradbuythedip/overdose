# The cover, the barcode, and the hardest dating evidence we have (2026-09-13)

## The barcode is clean, and that is now a measurement

The cover carries a UPC-A symbol, `0 74820 40388 4`, with a `21>` add-on and
`$12.99US`.

```
computed check digit 4, printed 4  -> VALID
control: same body with check digit 0 -> correctly INVALID
EAN-13 reading (leading zero) also checks out
```

A doctored or fabricated barcode would have been a real signal — it is a
printed number that must satisfy an arithmetic constraint, so tampering shows
up for free. It does not. `74820` is the publisher prefix, `40388` the product
code, `21` the standard two-digit issue add-on. There is nothing hidden in it.

Swept anyway with the rest of the cover data (UPC digits, price, dates, issue
strings, and pairings with the themed words): 223 phrases, 409,205 addresses,
0 funded hits.

## "Display Until Feb 23, 2022" — the best dating evidence in the project

This is the only PRIMARY-SOURCE date attached to the physical object. Every
other date here is inferred: from a Bukele photograph, from internal references
to Afghanistan and Bhutan, from snowflake IDs on tweets *about* the issue.

Newsstand "display until" dates run roughly three months past on-sale, which
puts this issue on sale around late November 2021 — consistent with the
2021-11-19 promo tweet ("Read my piece... promo code ORANGEPILL for 21% off")
and with the Fall 2021 attribution. It independently confirms the correction in
`date_correction.md`: this is a Fall 2021 issue, not the February 2022 one that
the Bukele photograph misled an earlier pass into assuming.

It also narrows the chain-side window at the front end. The repo's three
peel-shaped exactly-20 candidates now sit relative to a printed date rather
than an inferred one:

| funded | address | vs the printed on-sale window |
|---|---|---|
| 2 Nov 2021 | 1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t | just before / at on-sale |
| 27 Feb 2022 | 1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi | 4 days after display-until |
| 1 Jun 2022 | 1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64 | well after |

This tightens a prior. It is not evidence. OTC desks peel 20 BTC constantly and
962 addresses hold exactly 20.00000000.

## The cover photograph cannot carry the payload

Halftone printing destroys any pixel-level encoding, and the scan is a
photograph of a printed halftone. There is no LSB channel to recover. The cover
image is not a candidate and should not be treated as one.

## A note on meet-in-the-middle against the exact-20 list

A parallel effort asked for `named_exact20_870.txt` to close the loop on a
meet-in-the-middle. It is in this tree, but it would not help, and the reason
is worth stating so the work is not repeated.

Checking derived keys against 870 named addresses is **strictly weaker** than
what already runs here. Every candidate key is screened against
`address_map.bin`, an index of 56,795,328 currently-funded scriptPubKeys, plus
a historical ever-funded index. That index contains all 962 exactly-20
addresses **whether or not we can spell them** — enumeration was only ever
needed for chain-side attribution (funding date, funder, peel shape), which
requires network access. For key-side verification the named list adds nothing.

## Why the meet-in-the-middle family was always going to miss

The construction was sound and the null is not bad luck, it is arithmetic.

A checksum or HMAC framing cannot create entropy that is not already in its
two inputs. On the LEFT sits authorial style — orthographic slips, highlight
initials, the numeral string — a few dozen bits at most. On the RIGHT sit
published clue-words from public tweets, which carry **zero** bits, because
anyone can enumerate them. `HMAC(public_key, low_entropy_payload)` is a
low-entropy key however it is dressed up: the search space is just the size of
the LEFT set, and here that is 720 keys.

720 keys x 8 four-byte targets / 2^32 gives 0.003 expected false positives, so
observing zero is exactly what an unrelated pairing produces. The result is
informative about the design, not about luck: no combination of this column's
stylistic outliers with Keiser's published clue-words authenticates anything.
