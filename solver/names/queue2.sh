#!/bin/bash
cd /home/user/overdose/solver
while pgrep -f "label more-nohd" >/dev/null; do sleep 10; done
python3 try_phrases.py --in names/names_wave4.txt --label wave4-nohd --no-hd > names/wave4_nohd.out 2> names/wave4_nohd.err
