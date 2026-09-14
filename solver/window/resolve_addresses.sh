#!/bin/bash
# DP-R: resolve ~20 BTC scripthashes to plaintext addresses, entirely offline.
#
# The balance index (address_map.bin) is keyed by scripthash and built from
# Bitcoin Core chainstate, so it contains no addresses. This recovers them from
# a separate address+balance corpus published on GitHub releases -- which is
# reachable even when every Bitcoin API is egress-blocked.
#
# The corpus is dated 2026-08; the balance index is 2025-10. That mismatch is
# deliberate: a wallet with tx_count==1 and spent_txo_sum==0 holds a constant
# balance forever, so it MUST appear in the band at both dates. Anything that
# drops out moved, and fails FR3 anyway.
set -euo pipefail
OD=${OD:-/tmp/od}
URL="https://github.com/Pymmdrza/Rich-Address-Wallet/releases/download/Bitcoin/Latest_Bitcoin_Addresses.tsv.gz"

curl -sSL --retry 6 --retry-delay 4 --retry-all-errors -o "$OD/btc_addr_bal.tsv.gz" "$URL"

# all addresses holding 19.5-20.5 BTC in the 2026-08 snapshot
gunzip -c "$OD/btc_addr_bal.tsv.gz" \
  | awk -F, 'NR>1 && $2+0>=19.5 && $2+0<=20.5 {print $1"\t"$2}' > "$OD/band2026_addrs.tsv"
cut -f1 "$OD/band2026_addrs.tsv" > "$OD/band2026_only.txt"

# intersect with T_new (post-2021 scripthashes) using the C sweeper
gcc -O3 -o "$OD/sweep" sweep.c -lcrypto
"$OD/sweep" Tnew_b1_19.5_20.5.tsv < "$OD/band2026_only.txt" > "$OD/resolved_Tnew_2026.tsv"

echo "resolved: $(wc -l < "$OD/resolved_Tnew_2026.tsv") addresses"
