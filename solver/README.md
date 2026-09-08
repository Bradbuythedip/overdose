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

## Conclusion
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

## CRITICAL FINDING (RETRACTED — see Session 2 update below)

The prior "critical finding" here identified `1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j`
as the target wallet. **This was wrong** — that address predates Keiser's
article by 6 years (created 2016 by a memo.cash user). See Session 2 update
below for correction and expanded testing.

---

## SESSION 2 UPDATE (Sep 2026): retraction + extensive re-testing

### Retraction of `1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j` identification

The prior "CRITICAL FINDING" above was WRONG. Transaction history for that
address shows it was created in 2016 by a memo.cash user — years before
Keiser's article (Fall 2022). The `1xxx` vanity prefix is coincidental,
not connected to the article's X-mark graffiti.

**Target address unknown.** No public identification of Keiser's puzzle
wallet exists as of Sep 2026. The March 2023 Keiser tweet confirms 20 BTC
prize but never disclosed the address.

### Additional testing (this session)

All 400+ additional cipher extractions negative. Verifier scans full 56.8M
address balance index for ANY funded-wallet derivation — no target-address
guessing needed.

| Approach | Variants | Hits |
|---|---|---|
| Per-char bold detection (page 76, 6× per-word zoom, 169 words, 9 batches) | 3 partial bolds → "GeeCbe" | 0 |
| Per-char bold detection (pages 75/77/78/79, 6× per-word zoom, 742 words, 40 batches) | 3 more bolds → "GeeCbeworthofhatetoysinAfghanistanppll" | 0 |
| Highlighted-phrase extractions (orange + black + white-on-dark, 34 phrases) | 55 × 3 hash methods | 0 |
| Per-phrase individual variants | 35 phrases × 12 transforms × 6 hash methods = 3,150 | 0 |
| Famous Keiser catchphrases | 75 × 8 hash methods | 0 |
| Genesis Block + Bitcoin whitepaper variants | 37 × 10 hash methods | 0 |
| Number/metadata brainwallets | 40+ candidates | 0 |
| First-word-of-line acrostic (vision-agent transcribed, 143 lines) | 24 patterns × 3 methods | 0 |
| Multimodal BIP-39 sliding-window (1,228 tokens) | 0 valid mnemonics (longest run = 4 words) | 0 |
| Multimodal 2nd/3rd/last-word acrostic | 120 × transforms | 0 |
| Multimodal every-Nth-word (N=2,3,5,7,11,13) | 254 variants × 4064 addrs | 0 |
| Multimodal line-length/word-count encoding | 5 valid 64-hex private keys tested directly | 0 |
| Multimodal reverse + cross-page reordering | 32 variants × 96 keys × 384 addrs | 0 |
| Multimodal transposition ciphers (columnar/rail-fence/rot13-47/caesar 1-25) | 76 transformations | 0 |
| Multimodal sentence brainwallets (~50 sentences × transforms × hashes) | 0 | 0 |
| Punctuation/spacing cipher (dot-comma binary, all-punct hex, line-end pattern) | 8 candidates | 0 |
| WarpWallet-style scrypt (8 passphrases × 9 salts) | 72 | 0 |

**Total session-2 tests: ~5,000 unique cipher extractions × multiple hash methods = ~15,000 individual private-key derivations. All 0 hits.**

### Key vision-agent findings

- **Dollar bill serial** on p73/p74: `CL76841714A` (11 chars, valid base58 alphabet, wrong length for any Bitcoin key format). Same $100 bill photographed multiple times. Tested as brainwallet with 26 variants — 0 hits.
- **Photographer credit**: `@ANNABELLEBAZ` (Annabelle Baz Instagram handle). Not viable as key.
- **Pill capsules** (p73 + p79): plain white/orange gelatin caps, NO printed text/imprint/numbers.
- **Graffiti** (X marks on p76/78, "FUCK ALL" on p78, "SHIT" on p77, hand-drawn ₿ + barbed wire on p79, Max Keiser signature): NO hidden micro-characters.
- **OVERDOSE title stencil**: no hidden micro-chars in negative spaces.
- **Bleed-through on p73**: normal offset-printing show-through of unrelated TOC spread, mirror-reversed but no key material.
- **No mirror-writing** anywhere in the Overdose pages themselves.

### Per-char bold detection results (definitive)

Per-letter-normalized stroke-width detection was noise-limited at 1843px scan resolution. Ran 6× per-word deep-zoom vision agents on 911 body-text words across pages 75-79. Only these 6 words showed partial-char bolding:

- p76: "George" → "Gee" (high), "Clinton" → "C" (high), "being" → "be" (medium)
- p78: "BILLION worth of hate toys in Afghanistan" → within an orange highlight strip, "BILLION" appears lighter than "worth of hate toys in Afghanistan". **UNCONFIRMED as cipher** — mixed weight inside a highlight bar is a plausible design choice, and the sibling branch's independent 55-candidate highlight-phrase sweep returned 0 hits testing this exact string.
- p79: "Happy" → "pp" (medium), "all" → "ll" (medium)

These are all NATURAL RHETORICAL EMPHASIS in Keiser's writing style (musicians' names, headline emphasis, orange highlight strip typographic variation). Not steganographic marking.

### Web search findings

- Keiser tweet Mar 2023: "I hid a private #Bitcoin key encoded in this piece" — 20 BTC prize, unsolved
- Keiser tweet Dec 2022: "Like George Sand's hidden cryptography, I have hidden private keys in the text"
- Nostr post from March 2023 with the same 7 page images (nostr.com blocked from sandbox)
- No public solution or writeup found on Reddit, Twitter, StackerNews, Cipher Mysteries, or crypto puzzle databases (as of Sep 2026)

George Sand's actual cipher method: **read every other line** (odd or even) to reveal the hidden message. Applied to Keiser's article, neither odd nor even line sets form a coherent hidden message — so his reference is metaphorical, not literal.

### FINAL STATUS

**The puzzle is not solvable from the phone-scan JPEGs alone.** Remaining actionable paths:

1. **User's `window_scan.py`** on their laptop (block-window fingerprint scan for 20-BTC wallets funded **2021-09..2023-03** — see Session 3 update below for window correction; earlier 2022-10..2023-04 range was wrong by a year). Sandbox is 403-blocked from both Alchemy and blockstream APIs.
2. **Higher-quality PROFESSIONAL PRINT SCAN** — 1843px phone JPEG is at the noise floor for any subtle typographic signal.
3. **Physical magazine features** — UV inks, watermarks, embossing not visible in reflected-light JPEG.
4. **Additional hint from Keiser** — puzzle unsolved publicly since March 2023.

If the block-window fingerprint identifies Keiser's wallet address, its
funding transaction inputs may reveal the source wallet (which may itself
be a well-known Keiser address on-chain), giving fingerprint-triangulation
of the private key derivation approach.

---

## SESSION 3 UPDATE (Sep 2026): cross-reference with sibling branch `claude/keiser-overdose-puzzle-itkf6t`

A parallel Claude session did superior chain-side analysis on branch
`claude/keiser-overdose-puzzle-itkf6t`. Its consolidated handoff document is
`solver/STATUS.md` on that branch — treat it as authoritative for the chain-side
funnel and next actions.

### Two important corrections to prior work on THIS branch

**Window correction.** This branch's earlier work assumed the article was Bitcoin
Magazine Fall 2022 Orange Party Issue (Issue 27). It is actually **Issue 24, the
El Salvador Issue, Fall 2021**. Every datable reference in the text lands in
autumn 2021:

- p76: "10 years of ... since I started honey-badgering him to buy some at $1
  back in 2011" ⇒ 2021
- p78: "America left $85 BILLION worth of hate toys in Afghanistan" ⇒ Aug 2021
  US withdrawal
- p77: "Sorry Bhutan, you fell for that snake oil salesmen over at XRP" ⇒
  Sept 2021 Bhutan/Ripple partnership
- Nostr announcement names "Issue 24"; every page sidebar reads "El Salvador"

Correct block-window scan range is **695,000 → 781,000** (Sept 2021 through
2023-03-04 announcement), not 754,000 → 784,000. This invalidates roughly
two thirds of any block-window scan that used the earlier range.

**Swept-wallet hypothesis.** Every text-side cipher test on this branch — and
every chain-side scan on the sibling branch — assumes the puzzle wallet is
still funded. If the puzzle was solved after March 2023 (when Keiser last
said it was unsolved), the wallet is now spent and invisible to every filter
we have used. Sibling branch measured this blind spot:

> **889 post-2021 wallets in the ~20 BTC band moved between the 2025-10 and
> 2026-08 snapshots — 130 of them holding exactly 20.00000000 BTC.**

`solver/apr2023_analysis.py` on the sibling branch tests this hypothesis
directly once an April-2023 address snapshot is available (via
`ghcr.io/shlima/fortune`). It reports addresses that (a) held a balance
in April 2023, (b) hold nothing today, and (c) were absent from the pre-2021
corpus — exactly the shape a silently-solved puzzle wallet has.

### Chain-side funnel (from sibling branch)

| set | n | definition |
|---|---|---|
| funded scripthashes (2025-10 index) | 56,795,328 | — |
| holding 19.5–20.5 BTC | 5,745 | 20-BTC band |
| absent from pre-2021 corpus (`T_new`) | 3,448 | ⊇ any window wallet |
| resolved + unmoved 2025-10 → 2026-08 | 2,559 | candidates |
| exactly 20.00000000 BTC | 212 | |
| **and legacy P2PKH (tier 1)** | **68** | **start here** |

Files at `solver/window/*.txt` on the sibling branch.

### Additional attacks ruled out on sibling branch (do not repeat)

| attack | scale | result |
|---|---|---|
| brainwallet + secp256k1 mirror (k ↔ n−k) + 4 key involutions | 5,433,600 addrs | 0 |
| George Sand positional ciphers, 74 rules × 6 sources | 49,562 keys | 0 |
| banknote serial `CL 76841714 A` | 4,642 keys | 0 |
| vanity/token scan over 2,559 candidates | 5,904 addrs | 0 |
| dictionary scan (≥7-char words, 344k dict) | 2,559 addrs | 0 |
| literal key strings in body text (BIP38 `6P`, base58 ≥40, hex ≥32) | 142 lines | none present |

Combined with this branch's ~15,000 text-side derivations, the
**text-derived-key attack surface is now exhaustively covered.**

### Priority order (from sibling branch RUNBOOK)

Cheapest first, all off-sandbox:

1. **Docker → April-2023 snapshot intersection** — minutes, no Bitcoin API:
   ```
   docker pull ghcr.io/shlima/fortune
   docker cp $(docker create ghcr.io/shlima/fortune):/addresses/Bitcoin/2023/04 ./apr2023
   comm -12 <(sort apr2023/p2pkh_Rich_Max_100.txt) <(sort solver/window/candidates_p2pkh_exact20.txt)
   ```
   Any tier-1 address that appears in April 2023 was funded before then ⇒
   inside the puzzle window.
2. **`solver/address_check.py`** on survivors — fills funding txid, height,
   timestamp, `chain_stats` for FR3 confirmation.
3. **Block scan over 695,000 → 781,000** — independent cross-check via
   `solver/alchemy_window_scan.py`.
4. **Funding-source trace** on survivors — a Keiser-attributable input is
   the hit.
5. **Swept-wallet check** via `solver/apr2023_analysis.py` — same April-2023
   snapshot, catches wallets solved and swept post-March 2023.

### Split-funding and multi-key hedges

- If the 20 BTC is **split across multiple addresses**, single-output band
  search misses it. The sibling branch's `Tnew_b2` and `Tnew_b3` files carry
  the two- and three-output splits.
- Keiser said key**s** plural, "my column" — other Bitcoin Magazine columns
  by Keiser may carry additional keys. Only Issue 24 (Overdose) analyzed
  so far.

### Tier-1 justification — corrected

Sibling branch initially observed "0 of 1,707 segwit candidates hold exactly
20.00000000 BTC" vs 212 of 852 legacy, suggesting segwit is intrinsically
non-round. That was wrong — on the full 2026 band, segwit holds whole-BTC
amounts at 2.4% rate (62 addresses); the difference in the *filtered* set is
**temporal**, not format-intrinsic:

| type | in band | whole-BTC | rate |
|---|---|---|---|
| P2PKH  | 1,930 | 125 | 6.5% |
| P2SH   | 1,147 | 248 | 21.6% |
| segwit | 2,531 |  62 | 2.4% |

All 62 segwit whole-BTC addresses are absent from the 2025-10 snapshot ⇒
funded after Oct 2025, four years outside the window ⇒ correctly excluded.
The load-bearing claim is narrower but sound: **within the puzzle window,
the never-moved exactly-20-BTC population is entirely legacy** (68 P2PKH +
144 P2SH). Tier-1 ranking still holds; the reason is now correctly stated.

### Corpus bound verified

The `T_new` lower bound rests on the address corpus (Qalander/
bitcoin-all-addresses) ending 2021-01-17. Sibling branch initially took
"297 files" from the README without verifying. Probed past the documented
end: `xlk` returns 200 (69 MB), `xll` through `xna` all 404. **Corpus
genuinely stops at `xlk`.** No `mountaineerbr` variant is reachable
either. The T_new bound stands as constructed.

### What each branch's sandbox cannot reach

Both branches: Alchemy, blockstream, mempool, blockchair, bitcointalk, nostr,
bitcoinmagazine, archive.org, and `pkg-containers.githubusercontent.com` all
403 at CONNECT from the org egress proxy. Only github.com, raw/release
githubusercontent, ghcr.io manifests and the language package registries pass.

Everything past "priority 1" needs the user's laptop or an unrestricted host.
