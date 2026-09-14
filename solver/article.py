#!/usr/bin/env python3
"""
The article transcript, parsed. STDLIB ONLY — no crypto, no numpy, nothing.

WHY THIS FILE EXISTS
The transcript loader lived in gen_priority_addrs.py, which imports coincurve at
module level because it also derives addresses. Anything wanting only the TEXT
therefore dragged in an elliptic-curve library, and the continuous solver's
chain-free families — whose entire point is that they need no curve, no index
and no network — crashed on a machine without coincurve installed.

A module that parses text should cost nothing to import. This one imports re and
sys.

  python3 article.py --selftest
"""
import re, sys

PATH = "article_transcript.txt"


def load(path=PATH):
    """(lines, sentences, paragraphs) in print order.

    Comment lines are dropped, page markers split the file, and a blank line is
    the author's paragraph break.
    """
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    lines, sents, paras = [], [], []
    for _num, body in zip(it, it):
        for block in re.split(r"\n\s*\n", body):
            ls = [l.strip() for l in block.splitlines() if l.strip()]
            if not ls:
                continue
            lines.extend(ls)
            flat = " ".join(ls)
            paras.append(flat)
            for s in re.split(r"(?<=[.!?])\s+", flat):
                if len(re.findall(r"[A-Za-z]", s)) > 1:
                    sents.append(s.strip())
    return lines, sents, paras


def words(path=PATH):
    _l, _s, paras = load(path)
    return re.findall(r"[A-Za-z0-9$%'-]+", " ".join(paras))


def selftest():
    ok = True
    l, s, p = load()
    sys.stderr.write(f"  {len(l)} lines, {len(s)} sentences, {len(p)} "
                     f"paragraphs, {len(words())} words\n")
    ok &= len(l) > 100 and len(s) > 50 and len(p) > 8 and len(words()) > 1000
    body = " ".join(p)
    ok &= "10years" in body
    sys.stderr.write(f"  carries the corrected '10years' spelling: "
                     f"{'OK' if '10years' in body else 'FAIL'}\n")
    ok &= "# CORRECTION" not in body
    sys.stderr.write(f"  comment lines stripped: "
                     f"{'OK' if '# CORRECTION' not in body else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)
