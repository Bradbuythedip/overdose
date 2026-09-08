# Runbook — finishing the window scan from a machine with Bitcoin network access

The sandbox that produced this could not reach **any** Bitcoin data source
(Alchemy, blockstream, mempool, blockchair all return HTTP 403 at CONNECT from
the org egress proxy; only `github.com`, `*.githubusercontent.com` and the
package registries are allowed). Everything that could be done offline **is**
done; what remains needs your laptop.

Design rationale: `solver/DESIGN_window_scan.md`.

---

## What is already done (offline, in-repo)

| artifact | what it is |
|---|---|
| `window/Tnew_b1_19.5_20.5.tsv` | **3,448** scripthashes — the FR2 band, minus everything provably out of scope. **Start here.** |
| `window/Tnew_exact_20.tsv` | 795 — the exactly-20.00000000 subset (hand this to the parallel session; it cuts their 962 by 17%) |
| `window/Tnew_b2_39.0_41.0.tsv` | 1,093 — two ~20 BTC outputs paid to one address in one tx |
| `window/Tnew_b3_58.5_61.5.tsv` | 575 — three such outputs |
| `window/resolved_*.tsv` | 3,345 ~20 BTC addresses recovered in plaintext, all with pre-2021 history ⇒ excluded. Includes `1xxxtzAkynEy8PTvj7bPvcP1Suveibc7j`. |

**Where the numbers come from.** 56,795,328 funded scripthashes in
`address_map.bin` (snapshot 2025-10-11) → **5,745** hold 19.5–20.5 BTC today →
subtract the 2,297 that already appear in the 784-million-address blockchair
corpus (which ends 2021-01-17) → **3,448 remain**.

**Why the subtraction loses nothing.** A wallet funded in-window with
`tx_count == 1` has its *only* transaction after 2022-10. If it appeared in a
pre-2021 corpus it had a transaction before 2021, so `tx_count ≥ 2` — it fails
FR3 anyway. So every FR3-satisfying window wallet survives the subtraction.

---

## Step 0 — verify FR1 (block range) — 20 seconds

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

## Path A — recommended. Minutes, not hours.

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

## Path B — fallback, and an independent cross-check of Path A

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
