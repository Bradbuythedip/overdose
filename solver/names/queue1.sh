#!/bin/bash
cd /home/user/overdose/solver
# wait for the first no-hd pass to finish
while pgrep -f "label names-nohd" >/dev/null; do sleep 10; done
python3 try_phrases.py --in names/names_wave3.txt --label wave3-nohd --no-hd > names/wave3_nohd.out 2> names/wave3_nohd.err
