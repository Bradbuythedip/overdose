# Overdose puzzle — current status (2026-09-13)

Not solved. This is what is actually established, what is ruled out and with
what evidence, and what would move it.

## The target

Max Keiser, 4 Mar 2023 ([tweet](https://x.com/maxkeiser/status/1632068898169450497)):

> I hid a private #Bitcoin key encoded in this piece I wrote for
> @BitcoinMagazine Mr. President. Nobody's figured it out yet, but it's for 20 BTC.

One follow-up clue, 5 Mar 2023
([tweet](https://x.com/maxkeiser/status/1632391507008278528)): **mirror
writing**, quoting Della Sala & Cubelli's paper on the phenomenon (PMC2117809).

Source material available here: seven iPhone photographs of pages 73-79,
1792-1870 px wide, ~4.4 MP each.

## Ruled out, with the evidence

| axis | result | how it was established |
|---|---|---|
| classical binary steg in the JPEGs | clean | trailing-data, COM, EXIF, APPn, LSB all negative; DQT byte-identical across all 7 files, so no re-encoding ever happened |
| per-character bold cipher | **not measurable at this resolution** | a visibly-bold word measures 3.3-6.4 stroke width while regular text on the same line sits at 3.3-3.8 — see `window/bold_cipher_resolved.md` |
| whole-word bold, highlighted phrases, acrostics, punctuation/spacing | 0 hits | tasks #9-#14 |
| highlight runs as an ordered sequence | 0 hits | `gen_highlight_seq.py`; concatenations, acrostics, first/last-word null ciphers, per colour and per page |
| mirror-writing image transforms | 0 hidden addresses | 35 vision scans, 7 pages x 5 transforms |
| on-chain markers (OP_RETURN / inscriptions) | 0 hits | 2.2M lines of embedded chain text, blocks 0-829,999, **including input scripts**; validated with data-source and search-method positive controls |
| bech32 / Taproot puzzle wallet | none exists | 0 addresses with exactly 20 BTC unmoved in either class — so the @NachoKeysBTC `bc1q3e...6gvskf` claim is unsupported by chain data |
| derivation from article text | 0 funded hits | see below |

## Derivation search, cumulative

All scored against the **full 56,795,328-address funded index** via the offline
oracle, so a hit would register regardless of balance, spend history or funding
date.

| corpus | phrases | addresses | hits |
|---|---|---|---|
| original corpus, ~360 paths | 8,490 | 15,579,150 | 0 |
| body text (OCR), direct | 84,687 | 2,964,045 | 0 |
| transcript + mirror variants, direct | 373,660 | *running* | 0 so far |
| highlight sequences, ~360 paths | 516 | 946,860 | 0 |
| page furniture / bill serial / photo credit, ~360 paths | 301 | 552,335 | 0 |

Plus ~2.6M from the earlier big-corpus sweep. **Roughly 23M derived addresses,
zero funded.**

## What was corrected this session

1. **The exactly-20-BTC pool is 962, not 212.** Measured directly rather than
   re-derived through the filter chain. 750 addresses were cut by `T_new` and
   `unmoved` before the exactly-20 test ran, and `T_new` encodes the
   funding-date lower bound that was already discredited — a magazine-printed
   key can be arbitrarily old. Our 116 candidates cover 116; **846 are
   unaccounted for**. See `window/funnel_audit.md`.

2. **The corpus had no body prose in it at all.** It was built from the
   highlighted/bold catalogue. "A monetary defibrillator to the treasure chest",
   "nailing the Vatican with ultimatums", "Don't believe me?" — zero coverage
   before today. Every prior sweep, however deep in derivation paths, was blind
   to most of what Keiser actually wrote.

3. **Mirror transforms had never touched the body text.** `gen_mirror.py`
   hardcodes the highlight catalogue as its input, so the one explicit clue had
   only ever been applied to highlighted phrases.

4. **Per-character bold moved from "unconfirmed" to "measured unrecoverable".**

## Why exactly-20 can never discriminate

962 addresses hold exactly 20.00000000 BTC, against 142 at 19 BTC and 94 at
21 BTC. That is ordinary round-number preference, ~7x the neighbouring whole-BTC
values — not a puzzle signature. Any argument of the form "this address is the
one because it holds exactly 20 BTC" is circular, because the candidate set was
filtered on that property. The reference class is 962.

## Network constraints in this environment

Every Bitcoin API host is refused by the egress policy at the CONNECT layer
(403): blockstream, mempool, blockchair, btc.com, bitaps, electrs, **and the
Alchemy endpoint**. Only `raw.githubusercontent.com` and `github.com` are
reachable. Chain lookups are therefore done offline against
`/tmp/address_map.bin` through `index_oracle.py`; anything needing
transaction-level detail or address enumeration has to run elsewhere.

## What would actually move this

1. **A 600+ dpi lossless scan of pages 73-79** (flatbed, TIFF/PNG, greyscale or
   colour). This is the highest-value item by a wide margin. The pages here are
   ~215 dpi against 300-2400 dpi print, and the bold/regular stroke delta in a
   10 pt typewriter face is under one pixel at that sampling rate.
   `bold_extract.py` runs on better scans unchanged.
2. **Enumerating the 846 unaccounted exactly-20 addresses**, which needs an
   address-indexed source from a networked machine.
   `window/exact20_scripthashes.txt` holds all 962 scripthashes so any candidate
   list can be tested against the true pool offline and instantly.

## Standing methodological rule

Adopted after a scan reported "0 hits" over 782 files that were all 14-byte
`404: Not Found` bodies (`seq -w` pads to three digits; the repo uses four):

> **A null from a data source means nothing until that source has produced a
> known positive.**

It has since caught two more would-be silent failures — an Otsu implementation
returning threshold 254 on every page, and a "funded brainwallet" control that
was itself invalid because `address_map.bin` holds only *currently*-funded
addresses and every famous brainwallet was swept to zero years ago (8/8 probed
came back empty).
