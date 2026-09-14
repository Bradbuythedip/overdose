#!/bin/bash
cd /home/user/overdose/solver
while pgrep -f "names/names_all.txt" >/dev/null; do sleep 15; done
python3 try_phrases.py --in names/names_wave3.txt --label wave3-nohd --no-hd > names/wave3_nohd.out 2> names/wave3_nohd.err
python3 try_phrases.py --in names/names_wave5.txt --label wave5-nohd --no-hd > names/wave5_nohd.out 2> names/wave5_nohd.err
python3 try_phrases.py --in names/names_tier1.txt --label tier1-nohd --no-hd > names/tier1_nohd.out 2> names/tier1_nohd.err
