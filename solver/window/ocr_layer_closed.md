# The PDF's OCR text layer: scanned, and closed (2026-09-14)

`98cec008` recorded that the scan's text layer is OCR of the pages rotated 180
degrees and "confirms the scan orientation and nothing more". It was dismissed
rather than searched. It is worth searching for one specific reason: the
scanner OCR'd the whole page surface, including regions no human transcribed —
show-through, artwork, furniture — so it can hold characters the transcript
never had.

## What the layer contains

| printed page | OCR chars |
|---|---|
| 72 | 83 |
| 73 | 790 |
| 74 | 9 |
| 75 | 1,597 |
| 76 | 0 |
| 77 | 1,553 |
| 78 | 1,049 |
| 79 | 1,234 |

The rotation is confirmed directly: page 72's `ESOCTtTE/\O` reversed is
OVERDOSE and `rasTex xEn` is "Max Keiser" — both **show-through from page 73**,
picked up by the scanner and never present in any transcript. Page 76 OCR'd to
nothing at all.

## Method

Every page's layer, forwards and reversed, reduced two ways (base58-legal runs
of 20+, and the full base58-only character stream), then every sliding window of
each valid key length (22, 26, 30, 51, 52, 58) tested against the formats' own
checksums.

**46,210 windows checksum-tested.**

## Result

| format | filter strength | hits |
|---|---|---|
| WIF (51/52) | 1 in 2^32 | 0 |
| BIP38 (58) | 1 in 2^32 | 0 |
| Casascius mini (22/26/30) | 1 in 256 | 1 |

The single mini candidate, `SqfredecuEoTTpr1dd1uEcords` from page 79's reversed
stream, is noise and is shown to be noise rather than assumed:

```
priv  8fea3ac7848620ff8f7336e8fe91d4d9417e5b5745165b878a3852c065c64f68
p2pkh_c      13oyakdj4KSz1FC7R8tv1ZnPwfpzTaKL37   unfunded
p2pkh_u      17c54DzfaBCnGg8SD2Q1dCjU6f8ApSuUAD   unfunded
p2wpkh       bc1qrmffud6saapczpk8cpd4hkp4apm0fnh73e8hhn   unfunded
p2sh_p2wpkh  36ADr91xYJnrS46kq1Zv9mf2pSns9kV5RG   unfunded
p2tr         bc1pkawx06jqap777k4f8esk5v4dzflm9w4ssvlnev06kzqrnk424hxsgtq0nt  unfunded
```

checked against both the April-2023 rich list and the full 56.8M funded index.

The base rate predicts this exactly. A mini key needs an `S` prefix (1 in 58 of
windows) and passes on one checksum byte (1 in 256), so across ~23,000 windows
of mini-valid length the expectation is **1 to 2 hits by chance**. One was
observed. This is why `SOLVE_PROMPT.md` warns that mini hits need a second
filter; applied, it disqualifies this one.

Had a WIF or BIP38 window passed, that would have been a 1-in-4-billion event
and essentially proof of the extraction rule. None did.

## Status

The OCR layer is closed. The commit that dismissed it was right about the
conclusion, and this makes the negative reproducible instead of assumed.
