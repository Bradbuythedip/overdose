#!/usr/bin/env bash
# Re-run the project's phrase corpora against the EVER-USED oracle.
#
# No new derivations. The same phrases, the same 7 direct hashes x 5 seed types
# x ~360 HD paths x 5 script forms that produced the 69M audited nulls in
# STATUS.md -- judged this time by a detector that can see an address which was
# funded and later emptied. That case is the one STATUS.md calls "the most
# likely history of all" for a magazine-printed key, and it is the one no
# balance snapshot can detect.
#
#   ./run.sh everused-build      # once, first
#   ./resweep.sh                 # this
#
# Every corpus writes its own hits file. EXPECT HITS: generic English phrases
# that brainwallet crackers enumerated years ago are in the ever-used set by
# the thousand. A hit here means "this address existed on chain", not a solve.
# Triage with ./run.sh claim, then everfunded.py for amounts and dates.
set -uo pipefail
cd "$(dirname "$0")"
P="./.venv/bin/python"; [ -x "$P" ] || P="python3"
DIR="${OVERDOSE_EVERUSED:-/tmp/everused}"
OUT="${RESWEEP_OUT:-resweep_hits}"

if [ ! -f "$DIR/manifest.txt" ]; then
  echo "no ever-used index at $DIR" >&2
  echo "build it first:  ./run.sh everused-build" >&2
  exit 1
fi

mkdir -p "$OUT"
echo "== ever-used index: $DIR"
"$P" everused.py --selftest --dir "$DIR" 2>&1 | tail -4 || exit 1

# corpus file : whether to use the full ~360 HD path set (slow) or direct only
CORPORA=(
  "candidates_v2.txt:full"        # STATUS row 1, the original corpus
  "article_transcript.txt:full"   # the article itself, line by line
  "every_nth_full.tsv:direct"     # STATUS row 10, line/column + every-Nth
  "bip39_valid.tsv:full"          # STATUS rows 8-9, checksum-valid mnemonics
  "candidates3.txt:full"          # STATUS row 11, workflow candidates
  "candidates.txt:full"
  "furniture.txt:direct"          # STATUS row 5, page furniture
  "notesig.txt:direct"            # STATUS row 7, banknote
  "composite.txt:full"            # per-page assembled fragments
  "hlcolor.txt:direct"            # STATUS row 4, highlight sequences
  "bargeom.txt:direct"            # bar geometry encodings
  "p72.txt:direct"                # the NUMBERS page
)

total=0
for entry in "${CORPORA[@]}"; do
  f="${entry%%:*}"; mode="${entry##*:}"
  [ -f "$f" ] || { echo "-- $f: absent, skipped"; continue; }
  flag=""; [ "$mode" = "direct" ] && flag="--direct-only"
  echo
  echo "== $f ($(wc -l < "$f") lines, $mode paths)"
  "$P" full_sweep.py --phrases "$f" $flag --everused --everused-dir "$DIR" \
       --out "$OUT/$(basename "$f" | tr '.' '_').tsv" 2>&1 \
     | grep -viE "^ +\(A\)|^ +\(B\)|^ +[0-9a-zA-Z]{20,26} " | tail -6
  n=$(( $(wc -l < "$OUT/$(basename "$f" | tr '.' '_').tsv") - 1 ))
  [ "$n" -lt 0 ] && n=0
  total=$(( total + n ))
  echo "   -> $n hit(s)"
done

echo
echo "================================================================"
echo "  $total hit(s) across all corpora -> $OUT/"
echo
echo "  A hit means the address EXISTS ON CHAIN. It is not a solve."
echo "  Triage, in order:"
echo "    cut -f1 $OUT/*.tsv | sort -u | head            # the phrases"
echo "    ./run.sh claim <address>                       # script type, reachability"
echo "    python3 everfunded.py --addresses <file> --base \$ESPLORA --auto"
echo "  Keep only: funded once or twice, >= 1 BTC, funded Sep 2021 - Mar 2023."
echo "  Anything with many small deposits is a cracker's tip jar."
echo "================================================================"
