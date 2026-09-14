#!/usr/bin/env python3
"""Newline-joined name lists cannot be expressed one-per-line, so build them
here and hand them straight to try_phrases.run()."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
os.chdir(os.path.dirname(HERE))

from gen_names import NAMES, PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, EXTRA
import gen_wave3 as W3
import gen_wave5 as W5  # noqa: F401  (import side effect writes its file; harmless)

def nosp(s): return s.replace(" ", "")
ALL_ENT = NAMES + [e[0] for e in EXTRA]

P75 = ["Bitcoin", "Wall Street", "Jamie Dimon", "Vitalik Buterin", "mEthereum", "Satoshi"]
P76 = ["George Clinton", "James Brown", "Martin Luther", "Vatican", "Peter Schiff",
       "Friends", "Manhattan Bank", "El Salvador", "International Monetary Fund",
       "IMF", "Twitter", "Nayib Bukele", "Volcano Bonds", "Mike Novogratz", "Wall Street"]
P77 = ["El Salvador", "Jack Mallers", "Strike", "Bhutan", "XRP", "Roger Ver",
       "Block Size War", "Faketoshi", "London", "Peter McCormack", "BCH", "BSV",
       "ETH", "ADA", "Elvis Costello"]
P78 = ["Michael Saylor", "Nic Carter", "Marty Bent", "America", "Afghanistan",
       "Genesis Block"]
P79 = ["John", "Yoko", "Amsterdam", "Stacy", "Max Keiser"]
CAST_A = ["Satoshi", "Vitalik Buterin", "Jamie Dimon", "Peter Schiff", "Nayib Bukele",
 "Mike Novogratz", "Jack Mallers", "Roger Ver", "Faketoshi", "Peter McCormack",
 "Michael Saylor", "Nic Carter", "Marty Bent", "Stacy Herbert", "Max Keiser",
 "Elvis Costello", "George Clinton", "James Brown", "Martin Luther", "John", "Yoko"]
CAST_B = ["El Salvador", "Bhutan", "Afghanistan", "London", "Amsterdam",
 "Manhattan Bank", "IMF", "International Monetary Fund", "Wall Street", "Vatican",
 "Strike", "XRP", "BCH", "BSV", "ETH", "ADA", "mEthereum"]
ALIAS0 = [v[0] for v in W3.ALIAS.values()]

LISTS = [NAMES, NAMES[::-1], PEOPLE, PLACES, ORGS, BRANDS, SURNAME, FIRST, ALL_ENT,
         PEOPLE + PLACES + ORGS + BRANDS, NAMES + ["Stacy Herbert"],
         ["Overdose"] + NAMES, NAMES + ["Overdose"], ["Max Keiser"] + NAMES,
         P75, P76, P77, P78, P79, P75 + P76 + P77 + P78 + P79,
         CAST_A, CAST_B, CAST_A + CAST_B, CAST_A[::-1], sorted(NAMES), ALIAS0,
         [x.split()[-1] for x in CAST_A], [x.split()[0] for x in CAST_A]]

cands, seen = [], set()
def add(s):
    if s and s not in seen and len(s) < 4000:
        seen.add(s); cands.append(s)

for L in LISTS:
    for nl in ("\n", "\r\n", "\n\n"):
        for form in (L, [x.lower() for x in L], [x.upper() for x in L],
                     [nosp(x) for x in L], [nosp(x).lower() for x in L]):
            add(nl.join(form))
            add(nl.join(form) + nl)
    # tab- and multi-space-joined too (also unrepresentable one-per-line)
    for sep in ("\t", "   ", "  "):
        add(sep.join(L)); add(sep.join(L).lower())

print(f"multiline candidates: {len(cands)}", file=sys.stderr)

import continuous_solver as CS
from try_phrases import run
orc = CS.IndexOracle()
if not orc.ready:
    sys.exit(f"no oracle: {orc.why}")
if not orc.control():
    sys.exit("POSITIVE CONTROL FAILED")
print("control OK", file=sys.stderr)
hits, n = run(cands, orc, "multiline", hd=True)
print(f"\n{n:,} scriptPubKeys, {len(hits)} hit(s)", file=sys.stderr)
for p, dn, st, bal in hits:
    print(f"HIT\t{bal}\t{dn}\t{st}\t{p!r}")
if not hits:
    print("no hit", file=sys.stderr)
