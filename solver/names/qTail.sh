#!/bin/bash
cd /home/user/overdose/solver
while ps -p 16526 >/dev/null 2>&1; do sleep 20; done
python3 try_phrases.py --in names/names_tail.txt --label tail-nohd --no-hd \
  > names/tail_nohd.out 2> names/tail_nohd.err
