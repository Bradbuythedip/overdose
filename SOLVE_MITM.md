# `solve_mitm.py` — offline meet-in-the-middle solver

One file, no network, no repository, no 56.8M-address index. Copy it anywhere
with Python 3.8+ and run it.

```bash
python3 solve_mitm.py --selftest                      # always run this first
python3 solve_mitm.py scan --targets targets_20btc.txt
```

`pip install coincurve` makes it ~500x faster. Without it the bundled
pure-Python curve is used automatically, and `--pure` forces it either way so
you can cross-check the fast path against the slow one.

## What the "middle" actually buys you

The hypothesis is a two-component key — Keiser said key**s**, plural, "in the
text" — combined as `priv = a + b (mod n)`. That is the one combination that
factors through the curve:

```
pub = (a + b)G = aG + bG
```

so each half becomes a curve point **once**, and pairs are then combined with a
point **addition** instead of a fresh scalar multiplication. An addition costs
about 1% of a multiplication.

Whether you get a *true* meet-in-the-middle depends on what you know:

| mode | you know | cost | genuine MITM? |
|---|---|---|---|
| `scan` | candidate **addresses** | \|A\|+\|B\| mults, then \|A\|×\|B\| additions | **no** |
| `mitm` | the target **public key** | \|A\|+\|B\| operations | **yes** |
| `combine` | addresses; non-additive combos | full derivation per pair | no |

`scan` cannot meet in the middle because hashes are not invertible — you only
get the point-addition speedup. `mitm` is the real 2^2n → 2^n break: since
`aG = P − bG`, you build a table of `P − bG` over all `b` and look up `aG` for
each `a`.

**For the Overdose prize, `scan` is the mode that applies today.** The prize
address has never spent, so no public key has ever been revealed. `mitm` is
included and tested because the moment any candidate address spends, its public
key is published and the search collapses from a product to a sum.

This tool does not pretend `scan` is a cryptographic break. It isn't.

## Inputs

- `--targets FILE` — candidate addresses, one per line. `targets_20btc.txt`
  ships with 158: the enumerated addresses holding ~20 BTC that are in the
  publication window, plus the legacy-P2PKH and tier-1 subsets.
- `--left FILE` / `--right FILE` — your own component halves, one phrase per
  line. Omit them to use the built-in clue-derived sets (the banknote serial
  `CL76841714A`, its mirror-written form `A41714867LC` as printed on page 73,
  the district `L12`, and the column's anchor phrases).
- `--types` — comma-separated from `p2pkh_c,p2pkh_u,p2wpkh,p2sh_p2wpkh,p2tr`.
- `--checkpoint FILE` / `--resume` — for long runs.

Hits print immediately and append to `hits.txt` as JSON with the private key in
hex and both WIF forms. **Verify any hit independently before acting on it.**

## Controls

`--selftest` runs 12 checks and the tool refuses to run if any fails, because a
null from a broken pipeline is worthless:

- RIPEMD-160 against a published vector (hashlib drops it when OpenSSL 3 ships
  without the legacy provider, so a pure-Python one is bundled)
- a known brainwallet address, both compressed and uncompressed
- bech32 and bech32m encoding
- **Taproot odd-Y `lift_x`** — BIP-340 always takes the even-Y point, so an
  odd-Y pubkey must be negated before tweaking. This implementation originally
  skipped that and produced the wrong address for exactly half of all keys; the
  vector is pinned and cross-checked against an independently validated
  implementation (199/199 agreement)
- `aG + bG == (a+b)G`, and `(a+b)G − bG == aG`
- a **planted split** recovered end-to-end by both `scan` and `mitm`
- a **negative control**: an unrelated target must not be found

The self-test writes nothing to `hits.txt`, so its planted controls can never be
mistaken for a real result.
