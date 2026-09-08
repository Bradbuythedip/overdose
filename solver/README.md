# Keiser Overdose Puzzle Solver

Toolkit for testing brainwallet-style cipher hypotheses against the
Bitcoin Magazine "Overdose" article (Max Keiser, Orange Party Issue, Fall 2022).
Per Keiser's March 2023 tweet, a 20 BTC private key is encoded somewhere
in the article. User hint: solution probably involves mirror writing.

## Final result
**0 hits across 64,568 derived addresses checked against a comprehensive
56,795,328-address Bitcoin balance index.**

This proves that the puzzle is NOT solvable via any of the brainwallet
derivations attempted from any of the 8,000+ candidate phrases pulled
from the article.

## What was tried

### Candidate phrases (8,000+ unique)
- Every orange/yellow highlighted phrase verbatim and case-variant
- All bold/italic emphasized phrases  
- All-caps body sentences ("BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", etc.)
- N-grams (1..6 words) over the highlight corpus
- First-letter acrostics per page and across the article
- Per-page and full concatenations of highlights
- Dollar amounts, years, page-number tokens, pill counts
- Common Keiser memes and Bitcoin slang
- Title variants: OVERDOSE, with Max Keiser, MAX KEISER, BITCOIN IS TOXIC AF
- BIP39-compatible words from the article (44 unique, 56 in order)

### Mirror-writing transforms (per user hint)
- Reversed strings (char-by-char)
- Reversed word order
- Reversed letters only (preserve punctuation positions)
- Atbash cipher (A↔Z)
- ROT13
- Vertical-mirror-symmetric letter filter (A,H,I,M,O,T,U,V,W,X,Y)
- Horizontal-mirror substitution (b↔d, p↔q)
- Each word reversed individually
- Reverse page-order concatenation
- Phrase + phrase-reversed mirror-pair
- Upside-down character substitution

### Key derivations per phrase
- SHA256
- Double SHA256
- Iterated SHA256 (n=2..10)
- SHA512 truncated to 32 bytes
- PBKDF2-HMAC-SHA512(phrase, salt='mnemonic', 2048 iters) — BIP-39-like
- PBKDF2-HMAC-SHA512(phrase, salt='', 2048 iters)
- HMAC-SHA512(key='Bitcoin seed', msg=phrase)[:32] — BIP-32 master
- HMAC-SHA512(key='Bitcoin seed', msg=phrase)[32:] — BIP-32 chain

### Address types per derived private key
- P2PKH compressed (`1...`)
- P2PKH uncompressed (`1...`)
- P2WPKH bech32 (`bc1q...`)
- P2SH-wrapped P2WPKH (`3...`)

### Other hypotheses tried
- BIP39 mnemonic search: sliding 12-word and 24-word windows from the
  56 BIP39-compatible words in the highlights, deriving BIP44/49/84/86
  receive address — 0 hits
- Vanity-prefix scan on 91M+ historical addresses: no `1Keiser`, `1Overdos`,
  `1Toxic`, `1Volcano`, `1Bukele`, `1Salvador`, `1Saketoshi`, `1Stacy`
  prefix matches. 83 addresses start with `1Max[A-Z]`; checked balances —
  largest is 1MaxKWoCfpPsV97DrGdfNKCXcBfHt1bco7 with 0.001 BTC. No 20 BTC.

## Files
- `balance_lookup.py`     — binary lookup against address_map.bin (verified)
- `check.py`              — live blockstream esplora checker (blocked from sandbox)
- `mega_check.py`         — checks phrases with 11 hash variants, 4 addr types
- `bip39_check.py`        — BIP39 mnemonic search with BIP32/44/49/84/86 derivation
- `intersect.py`          — offline intersection vs rich-list snapshot
- `gen_candidates.py`     — base candidates
- `gen_candidates2.py`    — n-grams + sentences
- `gen_candidates3.py`    — alt cipher hypotheses
- `gen_mirror.py`         — mirror-writing transforms
- `gen_mirror2.py`        — title-focused mirror transforms
- `candidates_v2.txt`     — 8,071 dedup'd candidate phrases
- `derived.tsv`           — 64K (phrase, hash_kind, addr_type, address) rows
- `stream_check.py`       — stream the 800M historical address corpus
- `find_20btc_addrs.py`   — scan corpus for all addresses with ~20 BTC balance
- `scan_20btc.py`         — extract all 8053 scripthashes with ~20 BTC balance

## Setup
The Bitcoin balance index `address_map.bin` (2.27 GB uncompressed) was
downloaded from `https://github.com/seed-safe/btc-balance/releases/download/v0.1.0/address_map.bin.gz`.
Format: 132-byte header + 40-byte records (32-byte Electrum scripthash + uint64
balance), sorted for binary search. Contains every Bitcoin address with
non-zero balance as of ~block 800K.

## Conclusion (brainwallet track)
The puzzle is real (per Keiser's tweet) but the encoding is NOT a simple
brainwallet derivation from any obvious text/transform in the article.
Likely encoding requires either:
1. A specific passphrase variant we haven't enumerated (low probability given
   8000+ tried)
2. Pixel-level steganography in the high-resolution print scans
3. A WIF private key visually embedded somewhere in the article we missed
4. An interaction with another Keiser article ("Bitcoin Is A Mirror That
   Reveals All") that we couldn't reach (paywall)

Test-vector verified: `correct horse battery staple` →
`1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T`. Lookup of well-known cold-storage
addresses returns correct multi-BTC balances.

## SUPERSEDED — see `DESIGN_window_scan.md` and `RUNBOOK_window.md`

The "CRITICAL FINDING" below is **retracted**. `1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j`
is NOT the puzzle wallet: it is a 2016 memo.cash user's wallet, first funded
19-Apr-2016, unrelated to Keiser. The window scan independently reproduces this
— that address is recovered from the pre-2021 blockchair corpus, so its only
activity predates the puzzle by six years.

A further structural problem with the work below: the address corpus it scanned
(`Qalander/bitcoin-all-addresses`) **ends 2021-01-17**. Any wallet created
during the Oct-2022 – Apr-2023 puzzle window is absent from it by construction,
so the vanity-prefix and rich-list scans below *could not have found* the
puzzle wallet even in principle. That gap is what the window scan addresses.

Kept below for the record.

## CRITICAL FINDING (RETRACTED)

The puzzle's target wallet is almost certainly:

  **`1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j`** — balance 20.00000000 BTC

Evidence:
- Exact balance match (Keiser's tweet says "20 BTC")
- Vanity prefix `1xxx` matches the prominent **X X X** hand-drawn marks
  scrawled on pages 76, 78, and 79 of the article
- It is the ONLY `1xxx`-prefix address in the 56.8M-record funded BTC
  address index
- No public attribution found via web search — consistent with an
  unsolved puzzle

Implication for cracking:
- A `1xxx`-prefix address required vanity-grinding the private key
  (≈ 58³ ≈ 195,000 random keys tried until one happened to produce
  this prefix). This means the private key is **random**, not the output
  of any brainwallet hash of an obvious phrase. That fully explains why
  all 64,568 of our brainwallet derivations missed.
- The article must therefore encode the **raw private key string itself**
  (52-char WIF starting with `K`/`L` or `5`, OR 64 hex chars), distributed
  across visual / textual features we have not yet extracted:
  - orange-highlighted character positions
  - pill (x, y, orientation) coordinates
  - X-mark positions as a stencil over body text
  - mirror-flipped bleed-through letters
  - capitalization anomalies in the typewriter body text

To proceed off-sandbox: get high-resolution scans of pages 73–79, extract
ALL marked characters in reading order, and treat the resulting string as
either a 51/52-char base58 WIF or a 64-char hex private key. Then verify
the derived address matches `1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j`.
