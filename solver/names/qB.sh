#!/bin/bash
cd /home/user/overdose/solver
while pgrep -f "names/names_more.txt" >/dev/null; do sleep 15; done
python3 try_phrases.py --in names/names_wave4.txt --label wave4-nohd --no-hd > names/wave4_nohd.out 2> names/wave4_nohd.err
python3 try_phrases.py --in names/names_prio.txt --label prio-nohd --no-hd > names/prio_nohd.out 2> names/prio_nohd.err
python3 try_phrases.py --in names/names_tier2.txt --label tier2-nohd --no-hd > names/tier2_nohd.out 2> names/tier2_nohd.err
