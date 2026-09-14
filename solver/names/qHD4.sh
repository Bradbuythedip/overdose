#!/bin/bash
cd /home/user/overdose/solver
while ps -eo args --no-headers | grep -q "[h]dcore3a-HD"; do sleep 20; done
python3 try_phrases.py --in names/names_tail.txt --label tail-HD \
  > names/tail_hd.out 2> names/tail_hd.err
