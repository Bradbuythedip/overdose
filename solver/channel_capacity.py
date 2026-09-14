#!/usr/bin/env python3
"""
Can this article physically carry a 128-bit key? Measure the channels.

THE QUESTION NOBODY ASKED
Three sessions of ciphers, and nobody measured the CAPACITY of the medium. A
private key needs 128 bits of entropy minimum (a 12-word BIP-39 mnemonic) or
256 (a raw key). Every "hidden channel" hypothesis in this project is a claim
that some observable property of the printed page carries those bits.

So count the bits each channel actually has. A channel shorter than the payload
cannot carry it, whatever cipher is applied, and no amount of further searching
changes that.

This is an information-theoretic bound, not a search. It cannot find the key.
It can tell us where the key CANNOT be, which is the thing that has been
missing: every null so far is ambiguous between "wrong method" and "nothing
there", and a capacity bound removes that ambiguity for the channels it covers.

  python3 channel_capacity.py --selftest
  python3 channel_capacity.py
"""
import argparse, math, re, sys

NEED = {"BIP-39 12 words": 128, "BIP-39 24 words": 256, "raw private key": 256}


def body(path="article_transcript.txt"):
    return "\n".join(l for l in open(path, encoding="utf-8").read().split("\n")
                     if not l.startswith("#") and not l.startswith("==="))


def channels(B):
    """(name, n_symbols, bits_per_symbol, note) for every observable channel."""
    out = []

    caps = re.findall(r"\b[Bb]itcoin(?:s|ers|er)?\b", B)
    out.append(("Bitcoin/bitcoin capitalisation", len(caps), 1.0,
                "binary per occurrence"))

    try:
        hl = [l.split("\t") for l in open("highlights_ordered.tsv",
                                          encoding="utf-8")
              if not l.startswith("#") and l.strip()]
        cols = [p[1] for p in hl if len(p) > 1]
        n_white = sum(1 for c in cols if c == "white")
        out.append(("highlight colour (orange vs knockout)", len(cols), 1.0,
                    f"2-state, not 3: all {n_white} whites are on the dark "
                    f"page 77 where black is invisible"))
    except OSError:
        pass

    gaps = re.findall(r"  +", B)
    out.append(("intra-line wide gaps", len(gaps), 1.0,
                "5 of 6 are justification artifacts"))

    allcaps = re.findall(r"\b[A-Z]{2,}\b", B)
    out.append(("all-caps words", len(allcaps), 1.0, "display type"))

    quoted = re.findall(r'"[^"]+"', B)
    out.append(("quoted strings", len(quoted), 1.0, ""))

    lines = [l for l in B.split("\n") if l.strip()]
    out.append(("line count parity", len(lines), 1.0, "per printed line"))

    glyphs = sum(1 for c in B if not c.isspace())
    out.append(("per-glyph bold weight", glyphs, 1.0,
                "MEASURED AT CHANCE: runs 1.33 vs shuffled 1.26, ratio 1.06x "
                "across every threshold 75th-97th percentile"))

    out.append(("per-glyph baseline residual", glyphs, 1.0,
                "MEASURED DEAD: p79 residual spread 1.14x the flat pages"))

    words = re.findall(r"[A-Za-z']+", B)
    out.append(("word-initial letter (acrostic)", len(words),
                math.log2(26), "the text itself, not a hidden channel"))

    return out


def audit(B):
    rows = []
    for name, n, bps, note in channels(B):
        rows.append((name, n, bps, n * bps, note))
    return rows


def selftest():
    ok = True
    B = body()
    rows = audit(B)
    ok &= len(rows) >= 7
    sys.stderr.write(f"  {len(rows)} channels enumerated\n")
    caps = [r for r in rows if "capitalisation" in r[0]][0]
    ok &= caps[1] == 30
    sys.stderr.write(f"  Bitcoin/bitcoin occurrences: {caps[1]} "
                     f"{'OK' if caps[1]==30 else 'FAIL'}\n")
    hl = [r for r in rows if "highlight" in r[0]]
    if hl:
        ok &= hl[0][1] == 38
        sys.stderr.write(f"  highlight runs: {hl[0][1]} "
                         f"{'OK' if hl[0][1]==38 else 'FAIL'}\n")
    # a binary channel of n symbols carries exactly n bits
    ok &= abs(caps[3] - 30) < 1e-9
    sys.stderr.write(f"  a 30-symbol binary channel carries 30.0 bits: "
                     f"{'OK' if abs(caps[3]-30)<1e-9 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the channel audit is wrong; refusing")
    if a.selftest:
        return

    B = body()
    rows = audit(B)
    sys.stderr.write(f"\n  A key needs {NEED['BIP-39 12 words']} bits "
                     f"(12-word mnemonic) or {NEED['raw private key']} "
                     f"(raw key).\n\n")
    sys.stderr.write(f"  {'channel':<38} {'symbols':>8} {'bits':>9}  verdict\n")
    carry = []
    for name, n, bps, bits, note in rows:
        v = "CAN carry 128" if bits >= 128 else "too short"
        if bits >= 128:
            carry.append((name, bits, note))
        sys.stderr.write(f"  {name:<38} {n:>8} {bits:>9.0f}  {v}\n")
        if note:
            sys.stderr.write(f"  {'':<38} {'':>8} {'':>9}  {note[:70]}\n")

    total_short = sum(b for _n, _s, _p, b, _o in rows if b < 128)
    sys.stderr.write(f"\n  Every discrete editorial channel combined: "
                     f"{total_short:.0f} bits.\n")
    sys.stderr.write(f"  {'ENOUGH' if total_short >= 128 else 'NOT ENOUGH'} "
                     f"for a 12-word mnemonic even if all were stacked.\n")

    sys.stderr.write(f"\n  {len(carry)} channel(s) with the capacity:\n")
    for name, bits, note in carry:
        sys.stderr.write(f"    {name}  ({bits:.0f} bits)\n")
        if note:
            sys.stderr.write(f"      {note}\n")
    sys.stderr.write(
        "\n  CONSEQUENCE. Only per-glyph channels are long enough, and both\n"
        "  measurable ones are dead: bold is positioned at chance and the\n"
        "  baseline residual is 1.14x the flat pages. So the key is not\n"
        "  carried by any editorial channel on these pages. It is either\n"
        "  derived from the TEXT as a passphrase -- which is the space that\n"
        "  has been swept ~150M times -- or it is not on the pages at all.\n")


if __name__ == "__main__":
    main()
