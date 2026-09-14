#!/usr/bin/env python3
"""Candidates that carry real line breaks -- the blocks AS SET on the page.
Uses try_phrases.run and the same IndexOracle + positive control, because a
one-per-line file cannot carry an embedded newline."""
import sys, re
sys.path.insert(0, "/home/user/overdose/solver")
import continuous_solver as CS
from try_phrases import run

R  = "The economy of love is infinitely more efficient than hate and war."
A1, A3, A4, A5 = "BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", "MAX KEISER", "OVERDOSE"
A2L = ["EVERY SINGLE ONE OF",
       "THE BITCOIN WANNABES — BCH, BSV, ETH, XRP,",
       "ADA, AND 12,000 OTHER SHITCOINS, PLUS FIAT",
       "MONEY AND GOLD — IS FACING THE IGNOMINIOUS",
       "FATE OF DEMONETIZATION VERSUS BITCOIN."]
A2Lh = [l.replace("—", "-") for l in A2L]
R_L1, R_L2 = "The economy of", "love is infinitely more efficient than hate and war."
HL = [l.rstrip("\n").split("\t")[2] for l in
      open("/home/user/overdose/solver/highlights_ordered.tsv", encoding="utf-8")
      if not l.startswith("#") and l.count("\t") >= 2]

def ns(s): return re.sub(r"[ \t]+", "", s)
C = []
def add(*ss):
    for s in ss:
        if s and s.strip(): C.append(s)

for nl in ("\n", "\r\n", "\n\n"):
    add(R + nl + R, R.lower() + nl + R.lower(), R.upper() + nl + R.upper())
    add(nl.join([R] * 3))
    add(R_L1 + nl + R_L2, R_L2 + nl + R_L1,
        (R_L1 + nl + R_L2).lower(), (R_L2 + nl + R_L1).lower())
    add(nl.join(A2L), nl.join(A2Lh), nl.join(A2L).lower(), nl.join(A2Lh).lower())
    add(nl.join(reversed(A2L)), nl.join(reversed(A2Lh)))
    add(nl.join([A1, A3]), nl.join([A1, A3, A4]), nl.join([A5, A1, A3, A4]),
        nl.join([A1] + A2L + [A3, A4]), nl.join([A5, A1] + A2L + [A3, R, A4]),
        nl.join([A1, A3, A4, A5]), nl.join([A5, A1, A2L[0], A3, A4]))
    add(nl.join([A1, " ".join(A2L), A3, A4]),
        nl.join([A1, " ".join(A2Lh), A3, A4]),
        nl.join([A1, " ".join(A2Lh), A3, R, A4]).lower())
    add(nl.join([R] + [A1, A3, A4, A5]), nl.join([A1, A3, A4, A5] + [R]))
    add(nl.join(HL), nl.join(HL).lower(), nl.join(HL + [R]))
    add(nl.join([R, A1, A3, A4, A5, R]))
    for s in (R, A1, A3, A4, A5):
        add(nl.join(s.split()), nl.join(s.split()).lower())
    add(R + nl, nl + R, R + nl + nl + R, "\t".join([R, R]))
    add(R + nl + R + nl, nl.join([R, R, A4]), nl.join([A4, R, R]))
    add(nl.join([R, "78", R]), nl.join([R, A5, R]), nl.join([A5, R, R, A4]))

seen, P = set(), []
for s in C:
    if s not in seen:
        seen.add(s); P.append(s)
orc = CS.IndexOracle()
if not orc.ready:
    sys.exit(f"no oracle: {orc.why}")
if not orc.control():
    sys.exit("POSITIVE CONTROL FAILED")
sys.stderr.write(f"  [newline] control OK, {len(P)} phrases\n")
hits, n = run(P, orc, "newline", hd=True)
sys.stderr.write(f"\n  [newline] {n:,} scriptPubKeys, {len(hits)} hit(s)\n")
for p, dn, st, bal in hits:
    print(f"HIT\t{bal}\t{dn}\t{st}\t{p!r}")
if not hits:
    sys.stderr.write("  [newline] no hit\n")
