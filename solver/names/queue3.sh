#!/bin/bash
cd /home/user/overdose/solver
while pgrep -f "label tier1-HD" >/dev/null; do sleep 10; done
python3 try_phrases.py --in names/names_tier2.txt --label tier2-HD > names/tier2_hd.out 2> names/tier2_hd.err
