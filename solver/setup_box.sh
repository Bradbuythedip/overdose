#!/usr/bin/env bash
# Set up a machine to run the index-backed solver families.
#
# Debian and Ubuntu ship PEP 668 environments where "pip install" is refused
# system-wide. A virtualenv is the supported answer; --break-system-packages is
# not, and can leave the OS python unusable.
#
# The 56.8M-address funded index is a 2.3 GB file that is NOT in this
# repository. This builds the smaller April-2023 rich-list index instead, which
# the solver treats as a DISTINCT oracle: it answers "held a large balance in
# April 2023", never "holds coins today", and results are recorded under their
# own oracle name so the two are never conflated.
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/3  virtualenv =="
python3 -m venv .venv 2>/dev/null || { echo "need python3-venv: sudo apt install python3-venv"; exit 1; }
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet coincurve numpy mnemonic
echo "   installed: coincurve numpy mnemonic"

echo "== 2/3  rich-list dump =="
DUMP="${HOME}/pymmdrza/rich-address-wallet"
if [ ! -d "$DUMP" ]; then
  mkdir -p "$(dirname "$DUMP")"
  git clone --depth 1 https://github.com/Pymmdrza/Rich-Address-Wallet "$DUMP"
else
  echo "   already present at $DUMP"
fi

echo "== 3/3  build the index =="
sed -i "s#^DUMP = .*#DUMP = \"${DUMP}\"#" hist_index.py
./.venv/bin/python hist_index.py --build
./.venv/bin/python hist_index.py

cat <<'MSG'

Done. Run the solver with the venv python:

  ./.venv/bin/python continuous_solver.py --selftest
  ./.venv/bin/python continuous_solver.py --run

The selftest will now name which oracle it got. Check that line: it decides
what every subsequent null in this run actually means.
MSG
