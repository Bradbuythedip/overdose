#!/bin/bash
cd /home/user/overdose/solver
# wait for the names_all no-hd pass to drain, then run the deduped master pass
while pgrep -f "names/names_all.txt" >/dev/null; do sleep 10; done
python3 try_phrases.py --in names/master_remaining.txt --label master-nohd --no-hd \
  > names/master_nohd.out 2> names/master_nohd.err
