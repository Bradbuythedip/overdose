# Runbook — the last step

**Status: the scan is done offline. 2,559 candidates are resolved to plaintext
addresses; the top tier is 68.** All that remains is dating them, which needs
one cheap address query each.

The sandbox that produced this cannot reach any Bitcoin data source (Alchemy,
blockstream, mempool, blockchair all return HTTP 403 at CONNECT from the org
egress proxy; only `github.com`, `*.githubusercontent.com` and the package
registries are allowed). Everything that could be done without them **is** done.

Design rationale, including the second iteration that resolved scripthashes to
addresses entirely offline: `solver/DESIGN_window_scan.md`.

---

## Run this first — 68 addresses, about a minute

```bash
cd solver
python3 address_check.py --addrs window/candidates_p2pkh_exact20.txt \
                         --out window_resolved.tsv
python3 resolve_and_rank.py --from-tsv window_resolved.tsv \
                         --out /tmp/window_candidates.tsv --all
```

`address_check.py` fills in, per address: `chain_stats` (FR3 — must be
`tx_count == 1`, `spent_txo_sum == 0`), the funding txid, its block height and
timestamp (FR1 — the window filter), and the funded value (FR2).
`resolve_and_rank.py` then applies the window filter and the attribution
ranking. Drop `--all` to keep only in-window rows.

Then widen as far as you care to:

```bash
python3 address_check.py --addrs window/candidates_exact20.txt --out r2.tsv   # 212
python3 address_check.py --addrs window/candidates_all.txt     --out r3.tsv   # 2,559
```

`address_check.py` is resumable — re-running skips what is already in `--out` —
so an interrupted 2,559-address run costs nothing to restart.

## Candidate files

| file | n | what |
|---|---|---|
| `window/candidates_p2pkh_exact20.txt` | **68** | tier 1: exactly 20.00000000 BTC, legacy P2PKH. **Start here.** |
| `window/candidates_exact20.txt` | 212 | tiers 1–2: exactly 20.00000000 BTC, any type |
| `window/candidates_all.txt` | 2,559 | every candidate in [19.5, 20.5] BTC |
| `window/candidates_resolved.tsv` | 2,559 | the same, with balance, script type and tier |
| `window/Tnew_*.tsv` | | the scripthash sets these came from |
| `window/resolved_*.tsv` | 3,345 | pre-2021 ~20 BTC addresses — excluded, kept for audit |

Every candidate already satisfies: holds 19.5–20.5 BTC, did not exist before
2021-01-17, and has not moved between the 2025-10 and 2026-08 snapshots. The
only untested requirement is **when** it was funded.

---

## Then: funding source on whatever survives (FR5)

The vanity-prefix signal is exhausted — no Keiser-related token appears in any
of the 2,559 addresses. So attribution has to come from the money.

```bash
A=<surviving_address>
curl -s https://blockstream.info/api/address/$A/txs/chain \
  | jq -r '.[-1] | {txid, time:.status.block_time,
                    inputs:[.vin[].prevout.scriptpubkey_address],
                    outputs:[.vout[]|{addr:.scriptpubkey_address, btc:(.value/100000000)}]}'
```

An input tracing to an exchange withdrawal in Oct 2022 – Mar 2023, to Bitcoin
Magazine, or to an address Keiser has posted publicly is the hit.

---

## Optional — verify the block range (only needed for Path B)

```bash
for h in 755999 756000 781999 782000 782500; do
  hash=$(curl -s https://blockstream.info/api/block-height/$h)
  ts=$(curl -s https://blockstream.info/api/block/$hash | jq -r .timestamp)
  echo "$h  $(date -u -d @$ts '+%Y-%m-%d %H:%M UTC')"
done
```

Expect ≈ 2022-10-01 near 756000 and ≈ 2023-03-30 near 782000. If 782000 lands
*before* 2023-04-01, widen `--end` until the timestamp crosses it — the block
count is only an estimate and must be confirmed, not assumed.

Same check over Alchemy (block-based, no address index):

```bash
export ALCHEMY=https://bitcoin-mainnet.g.alchemy.com/v2/YOUR_KEY
H=$(curl -s -X POST $ALCHEMY -H 'content-type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"getblockhash","params":[756000]}' | jq -r .result)
curl -s -X POST $ALCHEMY -H 'content-type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getblock\",\"params\":[\"$H\",1]}" \
  | jq '{height:.result.height, time:.result.time}'
```

---

## Path A — scripthash route (superseded by address_check.py, kept as a cross-check)

Asks an Electrum server for the history of each of the 3,448 scripthashes.
Exactly one history entry ⇒ funded once, never spent (FR3); its height gives
the funding date (FR1); its tx gives the address and value (FR2).

```bash
cd solver
python3 electrum_sweep.py --targets window/Tnew_b1_19.5_20.5.tsv --out window_raw.tsv
python3 resolve_and_rank.py --electrum window_raw.tsv --out /tmp/window_candidates.tsv
```

Add `--all` to `resolve_and_rank.py` to keep out-of-window rows (marked
`in_window=no`) instead of dropping them.

Repeat for the two/three-output bands if you want full coverage:

```bash
python3 electrum_sweep.py --targets window/Tnew_b2_39.0_41.0.tsv --out window_raw_b2.tsv
```

If the default server list is unreachable, force one:
`--server fulcrum.sethforprivacy.com:50002`.

---

## Path B — full block walk (independent cross-check; hours, ~45 GB)

The literal brief: walk every block in the window. Uses `getblock` **verbosity
0** (raw hex, ~1.7 MB/block) rather than verbosity 2 (~7 MB/block) — a ~4×
transfer cut — and parses locally. ~26,000 blocks ≈ 45 GB, so budget hours.
Resumable: re-running skips heights already written.

```bash
python3 alchemy_window_scan.py --selftest           # no network; must print SELFTEST PASS
python3 alchemy_window_scan.py \
    --rpc $ALCHEMY --start 756000 --end 782000 \
    --targets window/Tnew_b1_19.5_20.5.tsv \
    --out window_outputs.tsv --threads 8
python3 resolve_and_rank.py --from-tsv window_outputs.tsv --out /tmp/window_candidates.tsv
```

Rows with `in_target_set=YES` are already FR4-confirmed. Path A and Path B
should agree; disagreement means one of them is wrong and is worth chasing.

---

## Step 3 — confirm each finalist against primary sources (FR3 + FR5)

Do this per surviving address. Never trust the index snapshot alone.

```bash
A=<candidate_address>

# FR3: the fingerprint — must be tx_count 1, spent_txo_sum 0
curl -s https://blockstream.info/api/address/$A | jq '.chain_stats'

# FR5: who funded it — exchange? Bitcoin Magazine? a Keiser-known address?
curl -s https://blockstream.info/api/address/$A/txs/chain \
  | jq -r '.[0] | {txid, time:.status.block_time,
                   inputs:[.vin[].prevout.scriptpubkey_address],
                   outputs:[.vout[]|{addr:.scriptpubkey_address, btc:(.value/100000000)}]}'
```

A funding input tracing to an exchange withdrawal in Oct 2022 – Mar 2023, or to
an address Keiser has publicly posted, is the strong hit.

---

## Output

`/tmp/window_candidates.tsv`, sorted best-attribution first:

```
address  funding_txid  block_height  block_time  value_sats
value_btc  block_time_iso  script_type  in_window  keiser_score  signals
```

`signals` shows the score breakdown (e.g.
`vanity-prefix:keiser(+180);exact-20.00000000(+40);legacy-p2pkh(+10);near-tweet:0d(+17)`)
so every ranking is auditable rather than a bare number.

---

## Known limitations

- If the puzzle wallet has been **swept**, FR3 excludes it by definition and
  neither this scan nor the parallel exact-20 scan will find it.
- `Tnew` is a superset: it also holds wallets funded 2021-01-18 → 2025-10
  outside the window. Path A's height filter is what narrows it.
- Attribution scoring is a heuristic ranking, not evidence. Step 3 against
  primary sources is what actually confirms a candidate.
