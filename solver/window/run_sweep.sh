#!/bin/bash
# DP6 driver: stream the Qalander corpus, emit target-set hits. Resumable.
BASE="https://raw.githubusercontent.com/Qalander/bitcoin-all-addresses/master"
T=/tmp/od/targets_union.tsv
W=$1; NW=$2
mkdir -p /tmp/od/hits /tmp/od/done
i=0
while read -r f; do
  i=$((i+1))
  [ $(( (i-1) % NW )) -ne "$W" ] && continue
  [ -f "/tmp/od/done/$f" ] && continue
  out=$(curl -sS --retry 6 --retry-delay 3 --retry-all-errors --max-time 3600 \
        "$BASE/$f" 2>/tmp/od/done/$f.curlerr \
        | /tmp/od/sweep "$T" 2>&1 >> "/tmp/od/hits/w$W.tsv")
  rc=$?
  # sweep prints "scanned=N hits=M unparsed=B" on stderr, captured into $out
  if [ $rc -eq 0 ] && [ -s /tmp/od/done/$f.curlerr ]; then rc=9; fi
  if [ $rc -eq 0 ]; then
    echo "$out" > "/tmp/od/done/$f"; rm -f /tmp/od/done/$f.curlerr
    echo "[w$W] $f $out" >> /tmp/od/progress.log
  else
    echo "[w$W] $f FAILED rc=$rc $(cat /tmp/od/done/$f.curlerr 2>/dev/null|head -c200)" >> /tmp/od/progress.log
  fi
done < /tmp/od/files.txt
echo "[w$W] WORKER-COMPLETE" >> /tmp/od/progress.log
