# Mirror-writing vision scan results (2026-09-13)

## Trigger
User relayed Keiser's explicit clue:
- Tweet [1632391507008278528](https://x.com/maxkeiser/status/1632391507008278528) (5 Mar 2023)
  quoting the paper "Mirror writing: neurological reflections on an unusual
  phenomenon" (Della Sala & Cubelli 2007, PMC2117809).
- @NachoKeysBTC (Jun 2026) claimed possible BIP-84 address `bc1q3e...6gvskf`.

## Method
Generated 35 image variants (7 article pages × 5 transformations):
- horizontal mirror (flipH) — for Leonardo-da-Vinci-style right-to-left text
- vertical flip (flipV) — for upside-down text
- 180° rotation
- inverted (grayscale + color-inverted) — for faint bleed-through
- flipH + inverted — for mirror-written bleed-through from reverse side

Vision agent on each variant looked for (a) text that reads meaningfully
ONLY in the transformed orientation, and (b) Bitcoin address / key material.

## Results

**0 hidden Bitcoin address / key candidates found across all 35 scans.**

Trivial content-reversal (already known):
- p74 inverted: OVERDOSE header, page number 74, "Bitcoin Magazine | El Salvador"
  sidebar rotated 90°, dollar bill serial CL76841714A / L12 on floating $100 bill
- p76 inverted: faint unresolved bleed-through in middle of page
- p78 180°: "The economy of love is infinitely more efficient than hate and war"
  — the white-on-black text inside the FUCK ALL scribble/stamp

**No Leonardo-style mirror script anywhere in the article.**
**No bech32 address strings anywhere in the article** (no `bc1q...` visible in any variant).
**No hex private key strings visible.**

## Conclusion

The mirror-writing hint does NOT resolve into concrete new content in the phone-scan
JPEGs (1830–1870 px wide, ~2400 px tall). Three remaining possibilities:

1. **The mirror signal is below the JPEG noise floor.** Needs 600+ dpi professional
   print scans (same limitation as the per-char bolding analysis).
2. **Mirror writing is a METAPHOR** in Keiser's rhetoric — not literal reflected text.
   Sibling branch already tested the cryptographic "secp256k1 mirror" (k ↔ n−k
   negation) across 5.4M brainwallet variants → 0 hits, ruling out the most
   obvious metaphorical reading.
3. **The mirror content is in a specific graphical element** (the dollar bill,
   pill photograph orientation, or the graffiti) at a resolution the JPEGs
   preserve poorly. Bill serial CL76841714A tested as brainwallet by both
   branches (2 sessions × 30+ variants, 4,642 keys total) → 0 hits.
