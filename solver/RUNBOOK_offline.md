# Offline runbook — pull the data, find the address, and where GPU actually helps

Everything here runs on your machine. The sandbox that produced the candidate
lists cannot reach any Bitcoin data source (Alchemy, blockstream, mempool,
blockchair, huggingface, ghcr blobs all 403 at CONNECT), so these are the steps
it could not run.

Ordered cheapest-first. **Step 1 alone may end this.**

---

## TL;DR — the honest read on GPU

GPU brute force is the wrong tool for this puzzle, and it is worth being clear
why before you spend money on it.

| what you'd GPU | search space | verdict |
|---|---|---|
| Raw 256-bit private keys | 2^256 | Impossible. 10^12 keys/s still needs > age of universe. |
| Bounded key range (BitCrack/Kangaroo style) | 2^n for small n | N/A — we have no bounded range and no known pubkey. |
| Brainwallet phrases from the article | ~10^6–10^9 realistic | **CPU already finishes this in minutes-to-hours.** GPU buys ~10–50×, which turns 2 hours into 5 minutes. Marginal. |
| Every 12-word subset of the 240 BIP-39 words in the article | C(240,12) ≈ 10^19 | Intractable on any hardware. |

The bottleneck for brainwallet search is **secp256k1 point multiplication**, not
SHA-256. `brainflayer` with libsecp256k1 already does ~100–200K keys/s/core.
Eight cores ≈ 1M keys/s ≈ 10^9 candidates in about 17 minutes. That covers the
entire plausible phrase space derived from a 7-page article.

**Spend your compute on Step 1 and Step 2 (chain-side identification), not on
grinding keys.** Step 4 is there if you want it anyway.

---

## Step 1 — Date the candidates (minutes, no API, no GPU)

The single highest-value step. `ghcr.io/shlima/fortune` bundles an **April-2023**
snapshot of P2PKH addresses. Any candidate present in it was funded before
April 2023 — i.e. inside the Sept-2021 → Mar-2023 puzzle window. Absent means
funded after the announcement, and it is excluded.

```bash
git clone https://github.com/Bradbuythedip/overdose.git
cd overdose
git checkout claude/bitcoin-puzzle-solver-FyDgY

# pull the April-2023 dataset out of the docker image
docker pull ghcr.io/shlima/fortune:latest
cid=$(docker create ghcr.io/shlima/fortune:latest)
docker cp "$cid:/addresses/Bitcoin/2023/04" ./apr2023
docker rm "$cid"
ls -la ./apr2023     # p2pkh_Rich_Max_{1,10,100,1000,10000,100000}.txt
```

If the path differs inside the image:

```bash
docker run --rm --entrypoint sh ghcr.io/shlima/fortune \
  -c 'find / -name "p2pkh_Rich_Max*" 2>/dev/null'
```

A 20-BTC address lives in the `Max_100` bucket. Intersect:

```bash
tr -d '\r' < apr2023/p2pkh_Rich_Max_100.txt | sort -u > apr2023.sorted
sort -u solver/window/candidates_p2pkh_exact20_67.txt > tier1.sorted

echo "tier-1 funded BEFORE Apr-2023 (IN WINDOW):"
comm -12 tier1.sorted apr2023.sorted | tee tier1_in_window.txt | wc -l

echo "tier-1 funded AFTER Apr-2023 (excluded):"
comm -23 tier1.sorted apr2023.sorted | wc -l
```

Anything in `tier1_in_window.txt` holds exactly 20.00000000 BTC, is legacy
P2PKH, did not exist before 2021-01-17, existed by April 2023, and has never
moved. That is a very tight fingerprint.

---

## Step 2 — Confirm on-chain and get funding dates (~1 minute)

```bash
# needs the balance index; ~2.3 GB
curl -L -o address_map.bin.gz \
  https://github.com/seed-safe/btc-balance/releases/download/v0.1.0/address_map.bin.gz
gunzip address_map.bin.gz

cd solver
python3 address_check.py --addrs ../tier1_in_window.txt --out window_resolved.tsv
```

Output columns:

```
address  script_type  funding_txid  block_height  block_time  value_sats  tx_count  funded_sats  spent_sats  fr3_pass
```

Keep rows where **`fr3_pass == YES`** (funded once, never spent) and
`block_height` is in **695000–781000** (Sept 2021 → 4 Mar 2023).

Then the swept-wallet check — catches the case where someone solved it after
March 2023 and emptied the wallet, which would make every current-balance
filter blind:

```bash
python3 apr2023_analysis.py --apr2023 ../apr2023/p2pkh_Rich_Max_100.txt \
                            --index ../address_map.bin
```

---

## Step 3 — Do the same for the bech32 pool (NEW — was missed by all prior scans)

Every earlier chain-side scan filtered addresses to `^1` and skipped segwit
entirely. Given the BIP-84 hint, run these too:

```bash
# those files are address,balance CSV — strip the balance column first
cut -d',' -f1 solver/window/current_exact20_bc1q_2026-09-13.tsv > bc1q_addrs.txt   # 44 P2WPKH
cut -d',' -f1 solver/window/current_exact20_bc1p_2026-09-13.tsv > bc1p_addrs.txt   # 18 Taproot
cut -d',' -f1 solver/window/current_exact20_p2sh_2026-09-13.tsv > p2sh_addrs.txt   # 248 P2SH

cd solver
python3 address_check.py --addrs ../bc1q_addrs.txt --out bc1q_resolved.tsv
python3 address_check.py --addrs ../bc1p_addrs.txt --out bc1p_resolved.tsv
python3 address_check.py --addrs ../p2sh_addrs.txt --out p2sh_resolved.tsv
```

Same filter: `fr3_pass == YES` and `block_height` in 695000–781000.

---

## Step 4 — Mass brainwallet search (optional; this is the compute-heavy part)

Only worth doing if Steps 1–3 leave nothing. The tool is `brainflayer` — it
tests passphrases against a bloom filter of target addresses.

### Build

```bash
sudo apt install -y build-essential libssl-dev libgmp-dev
git clone --recursive https://github.com/ryancdotorg/brainflayer.git
cd brainflayer && make
```

### Build the bloom filter from every funded Bitcoin address

```bash
# full current snapshot: 56.2M addresses with any balance
curl -L -o Latest_Bitcoin_Addresses.tsv.gz \
  https://github.com/Pymmdrza/Rich-Address-Wallet/releases/download/Bitcoin/Latest_Bitcoin_Addresses.tsv.gz

# hash160 list -> bloom filter
zcat Latest_Bitcoin_Addresses.tsv.gz | tr -d '\r' | cut -d',' -f1 \
  | ./hex2blf -t addr /dev/stdin all_addrs.blf
```

Or target only the 435 exact-20-BTC addresses (much tighter, near-zero false
positives):

```bash
cat solver/window/current_exact20_*.tsv | tr -d '\r' | cut -d',' -f1 \
  | ./hex2blf -t addr /dev/stdin exact20.blf
```

### Run

```bash
# candidate phrases from the article, one per line
./brainflayer -v -b exact20.blf -i candidates.txt -o hits.txt

# with a hash-mode sweep
for mode in sha256 keccak256 sha3 rmd160; do
  ./brainflayer -v -b exact20.blf -t $mode -i candidates.txt -o hits_$mode.txt
done
```

Throughput: ~100–200K keys/s/core. `-t` sets the hash mode; `-x` enables
compressed+uncompressed pubkey variants.

### Generate candidates at scale

The repo already has 8,071 dedup'd phrases at `solver/candidates_v2.txt`. To go
bigger, permute the article's highlighted phrases:

```bash
cd solver
python3 gen_candidates.py  > c1.txt
python3 gen_candidates2.py > c2.txt   # n-grams over the highlight corpus
python3 gen_candidates3.py > c3.txt   # alternate cipher hypotheses
python3 gen_mirror.py      > c4.txt   # mirror-writing transforms
cat c*.txt | sort -u > candidates_big.txt
wc -l candidates_big.txt
```

---

## Step 5 — GPU, if you insist

`brainflayer` is CPU-only. The GPU tools that exist solve a *different* problem
(sequential range search), which does not apply here. But if you want to use a
GPU anyway:

### BitCrack (CUDA) — sequential range, NOT useful for brainwallet

```bash
git clone https://github.com/brichard19/BitCrack.git
cd BitCrack && make BUILD_CUDA=1 COMPUTE_CAP=86    # 86 = RTX 30xx; 89 = 40xx; 90 = H100
./bin/cuBitCrack -i targets.txt -o found.txt --keyspace START:END
```

Only meaningful if you can bound the key range. We cannot — so this will run
forever and find nothing. Included for completeness.

### Kangaroo (CUDA) — needs the public key, which we do not have

```bash
git clone https://github.com/JeanLucPons/Kangaroo.git
cd Kangaroo && make gpu=1 CCAP=86
./kangaroo -gpu in.txt
```

Requires a **known public key** and a bounded interval. The puzzle wallet has
never spent, so its pubkey has never been revealed on-chain. Not applicable.

### The realistic GPU play

If you genuinely want GPU throughput on brainwallet candidates, you need a CUDA
secp256k1 pipeline. `keyhunt` (CPU) and `VanitySearch` (CUDA) are the closest
maintained options, but neither is a drop-in brainwallet cracker. Writing one is
a project, and it buys you ~20× over an 8-core CPU that already finishes the
realistic phrase space in under an hour.

**Recommendation: skip the GPU. Run Steps 1–3.**

---

## What is already ruled out — do not re-run these

Both branches combined:

| attack | scale | result |
|---|---|---|
| brainwallet phrases | 64,568 addresses | 0 |
| brainwallet + secp256k1 mirror (k ↔ n−k) + 4 involutions | 5,433,600 addresses | 0 |
| George Sand positional ciphers, 74 rules × 6 sources | 49,562 keys | 0 |
| banknote serial `CL 76841714 A` | 4,642 keys | 0 |
| dictionary scan (≥7-char words, 344k dict) | 2,559 addresses | 0 |
| literal key strings in body text (BIP38, base58 ≥40, hex ≥32) | 142 lines | none present |
| typographic / per-char bold at 6× zoom | 911 words, 49 agents | 0 |
| highlighted-phrase extraction | 34 phrases, 55 patterns × 3 hashes | 0 |
| first-word / Nth-word / line-length / transposition ciphers | ~4,000 variants | 0 |
| punctuation & spacing cipher | 8 candidates | 0 |
| WarpWallet scrypt | 72 combinations | 0 |
| mirror-writing vision (7 pages × 5 transforms) | 35 agents | 0 |
| binary steg: EOI-trailing, EXIF, COM, APPn, DQT, LSB | 7 pages × 6 techniques | 0 |

The image-side and text-side attack surface is exhausted. Chain-side
identification is the open path.
