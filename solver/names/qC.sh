#!/bin/bash
cd /home/user/overdose/solver
# wait for the qB chain to drain
while kill -0 15018 2>/dev/null; do sleep 20; done
python3 try_phrases.py --in names/names_wave6.txt --label wave6-nohd --no-hd > names/wave6_nohd.out 2> names/wave6_nohd.err
