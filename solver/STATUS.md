# Overdose puzzle — consolidated state

Keiser hid a private key for **20 BTC** in his "OVERDOSE" column. Two primary
sources fix the method and the target:

- [tweet 1607378060172460032](https://x.com/maxkeiser/status/1607378060172460032) (Dec 2022):
  *"Like George Sand's hidden cryptography, I have hidden private key**s** in the text."*
- [tweet 1632068898169450497](https://x.com/maxkeiser/status/1632068898169450497) (4 Mar 2023):
  *"I hid a private #Bitcoin key encoded in this piece … Nobody's figured it out yet, but it's for 20 BTC"*

## The window (corrected)

The article is **Bitcoin Magazine Issue 24, "The El Salvador Issue", Fall 2021** —
*not* the Fall 2022 Orange Party Issue (which is Issue 27). The Nostr
announcement names Issue 24; our page sidebars read "El Salvador"; and every
datable reference in the text (Bhutan/Ripple Sept 2021, Afghanistan Aug 2021,
pre-Merge Ethereum, El Salvador 42% adopted, "10 years since 2011") lands in
autumn 2021.

So the key existed by autumn 2021 and the wallet held 20 BTC by 4 Mar 2023:

| | date | height |
|---|---|---|
| publication | Sept–Nov 2021 | ~700,000 |
| announcement | 2023-03-04 | ~780,000 |

**Scan range: 695,000 → 781,000.** An earlier assumption of 754,000–784,000
misses roughly two thirds of the window, including the period around publication.

## Chain-side state (the live lead)

| set | n | definition |
|---|---|---|
| funded scripthashes (2025-10 index) | 56,795,328 | — |
| holding 19.5–20.5 BTC | 5,745 | FR2 band |
| `T_new` — absent from corpus ending 2021-01-17 | 3,448 | provably ⊇ any window wallet |
| resolved to addresses **and** unmoved 2025-10 → 2026-08 | **2,559** | candidates |
| exactly 20.00000000 BTC | 212 | |
| **and legacy P2PKH** | **68** | **tier 1** |

Files: `window/candidates_p2pkh_exact20.txt` (68),
`window/candidates_exact20.txt` (212), `window/candidates_all.txt` (2,559),
`window/candidates_resolved.tsv` (with balance/type/tier).

These are **date-agnostic above Jan 2021**, so the window correction did not
invalidate them.

## Next actions, cheapest first

1. **Date them with the April-2023 snapshot** — minutes, no blockchain API.
   `docker pull ghcr.io/shlima/fortune`, extract
   `addresses/Bitcoin/2023/04/p2pkh_Rich_Max_100.txt`, then
   `python3 apr2023_analysis.py --apr2023 <file>`. Commands in `RUNBOOK_window.md`.
2. **`address_check.py`** on the survivors → funding txid, height, timestamp,
   `chain_stats` (confirms funded-once / never-spent).
3. **Block scan** over 695,000–781,000 as an independent cross-check.
4. **Funding-source trace** on anything that survives — an exchange withdrawal in
   the window, or an address Keiser has posted, is the hit.

## Ruled out (do not repeat)

| attack | scale | result |
|---|---|---|
| brainwallet phrases (prior sessions) | 64,568 addresses | 0 |
| brainwallet + **secp256k1 mirror** (k ↔ n−k) + 4 key involutions | 5,433,600 addresses | 0 |
| George Sand positional ciphers, 74 rules × 6 sources | 49,562 keys | 0 |
| banknote serial `CL 76841714 A` | 4,642 keys | 0 |
| vanity/token scan over candidates | 2,559 + 3,345 addresses | 0 |
| dictionary scan (≥7-char words, 344k dict) | 2,559 addresses | 0 |
| literal key strings in body text (BIP38 `6P`, base58 ≥40, hex ≥32) | 142 lines | none present |
| typographic weight cipher | see below | unresolved, likely editorial |

## The weight/bold question

Bolding that appears to stop mid-word (`bei|ng`, `Cl|inton`) is **not confirmed**
as a cipher. Three measurement approaches (ink density, stroke width, per-letter
normalised mass) all fail at 1800 px, where regular strokes are ~3 px and bold
~4–5 px. Run-length analysis never exceeds 9% word-alignment at any threshold,
yet visibly-bold phrases *are* word-aligned — so the measure is tracking print
noise, not the real bold class. The phrases that read as bold are semantically
coherent (names, vivid images), which is what editorial emphasis looks like.
**Only a 600+ dpi scan can settle it.**

## Known blind spots

- **A swept wallet is invisible.** Everything assumes the wallet is unspent. If it
  was solved after Mar 2023 it is spent and outside every filter used here.
  Measured: **889** post-2021 wallets in the ~20 BTC band moved between the
  2025-10 and 2026-08 snapshots, **130 of them holding exactly 20.00000000 BTC**;
  those cannot be resolved to addresses from available data.
  `apr2023_analysis.py` tests this hypothesis directly once the April-2023 file
  is available.
- **Split funding.** If the 20 BTC sits across several addresses, a single-output
  band search misses it.
- Keiser said key**s** plural, "my column" — other issues may carry others.

## Sandbox constraint

No Bitcoin data source is reachable: Alchemy, blockstream, mempool, blockchair,
bitcointalk, nostr, bitcoinmagazine, archive.org and
`pkg-containers.githubusercontent.com` all return 403 at CONNECT from the org
egress proxy. Only github.com, raw/release githubusercontent, ghcr.io manifests
and the package registries pass. Every offline result above was produced within
that constraint.

---

## Session 3 additions (workflow + HD derivation)

**New derivation dimension — BIP32 hierarchy.** Every prior sweep, in both
sessions, treated a hash of the passphrase as the private key *directly*. Real
wallets do not: they turn the passphrase into a **seed** and walk a BIP32 path.
`hd_derive.py` closes that gap — PBKDF2-HMAC-SHA512(phrase, salt, 2048) → master
→ 11 paths (m, m/0, m/0', m/0'/0'/0', m/44'/0'/0'/0/{0,1}, m/49', m/84', m/86')
across 5 salts, plus scrypt at three parameter sets, each key also tested at its
secp256k1 mirror across 4 address types.

Validated against **all three official BIP32 spec test vectors** before use.

**New candidate corpus.** A 13-agent workflow generated **2,300** passphrase
candidates across 12 semantic angles (exact sentences, Keiser persona, El
Salvador/Bukele autumn-2021 context, title/masthead, artwork and scrawls,
Fall-2021 news, Bitcoin-culture coinages, numbers/dates, the George Sand hint
itself, puzzle-meta phrasing, token compounds, display type) plus a completeness
critic. Prior corpora were all built before the Issue-24/Fall-2021 correction.

| sweep | keys | result |
|---|---|---|
| hash + mirror over 2,300 new candidates | 184,000 (1,472,000 addresses) | **0** |
| BIP32 + scrypt over the 8,622-phrase corpus | 500,076 | **0** |
| BIP32 + scrypt over the 2,300 new candidates | 133,400 | **0** |
| **total this session** | **817,476** | **0** |

Cumulative across all sessions the text-derived-key hypothesis has now absorbed
well over **7 million** distinct address derivations with zero hits, spanning
plain hashes, iterated hashes, PBKDF2, HMAC, scrypt, WarpWallet, BIP39 seeds,
BIP32 paths, the secp256k1 mirror, and four key involutions.

**Assessment.** The "private key is derived from text in the article" family is
comprehensively dead at every derivation scheme we can construct. Either the key
material is not recoverable from these 1800 px scans, or the mechanism is not a
passphrase at all. The live path remains chain-side.

---

## Tier-1 prior: verified, with a correction

I initially observed that **0 of 1,707** segwit candidates hold exactly
20.00000000 BTC versus **212 of 852** legacy ones, and read that as segwit
holdings never being round. **That was overstated.** On the full 2026 band the
picture is:

| type | in band | whole-BTC | rate |
|---|---|---|---|
| P2PKH | 1,930 | 125 | 6.5% |
| P2SH | 1,147 | 248 | 21.6% |
| segwit | 2,531 | **62** | 2.4% |

Segwit *does* hold round amounts. The reason none survive into the candidate set
is temporal, and it checks out cleanly:

> All **62** segwit whole-BTC addresses in the 2026 band are **absent from the
> 2025-10 snapshot** — so they were funded after October 2025, four years outside
> the puzzle window, and the filter excluded them correctly.

The corrected statement is narrower but still useful: **within the puzzle window,
the population of never-moved exactly-20-BTC wallets is entirely legacy** (68
P2PKH + 144 P2SH). That is a mechanically explained property of the filtered set,
not an artifact, and it is why tier 1 is ranked as it is. Legacy survival through
the 2025-10 filter runs ~55% (68/125 P2PKH, 144/248 P2SH); segwit's is 0/62.

## Corpus extent re-verified

The address corpus was re-probed past its documented end: `xlk` returns 200
(69 MB) and `xll` … `xna` all 404. It genuinely stops at 297 files / 2021-01-17,
so no first-appearance ordering exists past that date. `mountaineerbr`'s variant
is not reachable at that path either. The `T_new` lower bound stands.
