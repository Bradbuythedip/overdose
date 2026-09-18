#!/usr/bin/env bash
# Overdose puzzle -- one dispatcher for the network/analysis tools.
# Reads the endpoint from $ESPLORA (fall back to blockstream). Never hardcodes
# a key: export it yourself, e.g.
#     export ESPLORA="https://bitcoin-mainnet.g.alchemy.com/v2/YOUR_KEY"
# For the tracer use blockstream -- it needs /address/{a}/txs, which Alchemy
# does not serve.
set -euo pipefail
cd "$(dirname "$0")"
P="./.venv/bin/python"; [ -x "$P" ] || P="python3"
ESPLORA="${ESPLORA:-https://blockstream.info/api}"

usage() {
  cat <<USAGE
usage: ./run.sh <command> [args]

  trace                 crawl the 3 candidates' funders; the same-wallet test
                        (uses blockstream regardless of \$ESPLORA -- needs /address/txs)
  claim <addr>...       vet claimed prize address(es): valid? reachable? funded?
  everfunded            rebuild the shortlist and ask "ever funded" (uses \$ESPLORA)
  sigreuse <rawtxhex>.. recover a key from ECDSA nonce reuse across given txs
  snowflake <tweetid>.. date a tweet from its ID (offline)
  lowentropy            test the low-entropy key-value space vs the tx addresses
  ideas <file> [--hd]   YOUR phrases (one per line) -> addresses -> "ever funded" (\$ESPLORA)
  control <text.txt>    run the Issue-24 device battery on a sibling Keiser column
  combine               the two serials combined every way vs the local oracle (slow)
  selftest              run every tool's offline selftest

  endpoint: \$ESPLORA = $ESPLORA
USAGE
}

cmd="${1:-}"; shift || true
case "$cmd" in
  trace)      exec "$P" trace.py --base https://blockstream.info/api --loop --max-depth 6 ;;
  claim)      exec "$P" claim_check.py "$@" --base "$ESPLORA" ;;
  everfunded) "$P" shortlist_everfunded.py --out everfunded_shortlist.txt
              exec "$P" everfunded.py --addresses everfunded_shortlist.txt \
                   --base "$ESPLORA" --auto --workers 8 --cache everfunded_cache.jsonl ;;
  sigreuse)   for t in "$@"; do "$P" sig_reuse.py --tx "$t"; done ;;
  snowflake)  exec "$P" snowflake.py "$@" ;;
  lowentropy) exec "$P" lowentropy.py --max-int "${1:-3000000}" ;;
  ideas)      f="${1:?phrase file}"; shift || true
              "$P" ideas.py --phrases "$f" --out ideas_addrs.txt "$@"
              exec "$P" everfunded.py --addresses ideas_addrs.txt \
                   --base "$ESPLORA" --auto --workers 8 --cache everfunded_cache.jsonl ;;
  control)    exec "$P" control_corpus.py --text "${1:?plain-text file of the column}" ;;
  combine)    exec "$P" serial_combine.py --loop ;;
  selftest)   for m in trace claim_check everfunded shortlist_everfunded \
                        sig_reuse snowflake lowentropy decoys ideas control_corpus serial_combine; do
                echo "== $m"; "$P" "$m.py" --selftest 2>&1 | tail -1; done ;;
  *)          usage; exit 1 ;;
esac
