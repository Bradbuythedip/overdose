# Keiser Overdose Puzzle Solver

Tooling for testing brainwallet-style cipher hypotheses against the
Bitcoin Magazine "Overdose" article (Max Keiser, Orange Party Issue, Fall 2022).
Per Keiser, a 20 BTC private key is encoded in the article text.

## Files
- `check.py`            — local brainwallet candidate checker (queries blockstream esplora; needs internet)
- `intersect.py`        — offline checker: derives addresses and intersects against a hosted snapshot
- `gen_candidates.py`   — base candidate set (highlights + memes)
- `gen_candidates2.py`  — expanded (n-grams, case variants, sentences, ~6.1K candidates)
- `gen_candidates3.py`  — alt cipher hypotheses (caps, acrostics, dollar amts, years, graffiti)
- `candidates_all.txt`  — merged corpus (6,578 unique phrases)
- `derived.tsv`         — every (phrase, hash_kind, addr_type, address) derived (≈52K rows)
- `intersect_hits.tsv`  — header only (0 hits against the 336K snapshot)

## Address derivation
For each candidate phrase `p`, the script derives 8 addresses:
- `sha256(p)`  → P2PKH compressed / uncompressed / P2WPKH bech32 / P2SH-P2WPKH
- `sha256(sha256(p))` → same 4 variants

Test vector verified: `correct horse battery staple` → `1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T`.

## Snapshot used
`/tmp/snapshot.txt` is the union of two GitHub-hosted rich-address dumps
(`Pymmdrza/Rich-Address-Wallet`, `Ranamom/Rich-Of-Crypyto`) — 336,813 unique
addresses. This is roughly 0.7% of the ~50M ever-funded BTC addresses, so a
miss is not conclusive.

## Status
0 hits with 6,578 candidates × 8 derivations against the partial snapshot.

## Next steps (run off-sandbox)
1. Re-run `check.py candidates_all.txt` from a host with outbound HTTPS — this
   queries blockstream.info esplora directly for every derived address.
2. OR download a full UTXO-set snapshot (~50M addresses, ~1.5 GB) from
   `https://addresses.loyce.club/` and re-run `intersect.py` against it.
3. Expand candidates further: BIP-39 mnemonic guesses, Vigenère-decoded
   acrostic strings, and pixel-level steganography on the JPEGs.
