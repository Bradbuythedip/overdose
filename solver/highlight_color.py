#!/usr/bin/env python3
"""
The highlight COLOURS as data. They have only ever been used as a filter.

THE GAP, IN ONE LINE OF EXISTING CODE
`highlight_sequence.py` reads the 38 highlighted runs and groups them:

    "orange": [r for r in runs if r[1] == "orange"],
    "black":  [r for r in runs if r[1] == "black"],
    "white":  [r for r in runs if r[1] == "white"],

Colour selects WHICH runs to read. It is never itself read. So 361 readings
were generated from the highlight text and not one of them used the sequence

    orange black orange orange orange orange orange black ...

as a carrier. That sequence is 38 symbols over a 3-letter alphabet, laid down
deliberately by whoever set the pages.

WHY THE DESIGNER MATTERS
Keiser is a broadcaster; he did not lay out these pages. A designer at the
magazine did, in InDesign, and a designer asked to hide something has exactly
one channel that survives printing and is invisible as content: the attributes
of the decoration. Highlight colour is that channel. So is highlight LENGTH,
and the gaps between highlights.

WHAT IT SWEEPS
  ternary     the colour sequence base-3, both digit assignments and all 6
              permutations of which colour is 0/1/2, forward and reversed
  binary      each colour against the rest (orange=1 else 0, and so on),
              packed big- and little-endian into bytes
  run-length  lengths of consecutive same-colour runs
  lengths     words and characters per highlighted run, as a number sequence
  selection   colour as an instruction: take the first word of an orange run,
              the last of a black, skip white -- all 27 assignments of
              {first, last, whole} to the three colours

Each result is checked against the self-certifying validators (WIF checksum,
BIP-39 checksum, 64 hex chars) AND written out for the funded-address sweep.

  python3 highlight_color.py --selftest
  python3 highlight_color.py --out hlcolor.txt
"""
import argparse, hashlib, itertools, sys

COLORS = ("orange", "black", "white")


def load(path="highlights_ordered.tsv"):
    runs = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3 and p[1] in COLORS:
            runs.append((p[0], p[1], p[2]))
    return runs


def ternary_keys(seq):
    """The colour sequence as a base-3 number, every digit assignment."""
    out = {}
    for perm in itertools.permutations(range(3)):
        m = dict(zip(COLORS, perm))
        for name, s in (("fwd", seq), ("rev", seq[::-1])):
            digits = [m[c] for c in s]
            n = 0
            for d in digits:
                n = n * 3 + d
            label = f"tern_{''.join(str(m[c]) for c in COLORS)}_{name}"
            out[label] = n
            out[label + "_str"] = "".join(str(d) for d in digits)
    return out


def binary_keys(seq):
    """Each colour against the rest, packed into bytes both endiannesses."""
    out = {}
    for c in COLORS:
        bits = [1 if x == c else 0 for x in seq]
        for name, b in (("fwd", bits), ("rev", bits[::-1])):
            s = "".join(str(x) for x in b)
            out[f"bin_{c}_{name}_str"] = s
            n = int(s, 2) if s else 0
            out[f"bin_{c}_{name}"] = n
    return out


def knockout(seq):
    """Collapse white into black. THE PHYSICALLY CORRECT READING.

    All 6 white runs are on page 77, which is printed white-on-dark-brown. A
    black highlight on a dark ground is invisible, so the designer had no
    choice there -- the colour is dictated by the page ground, not selected as
    content. Orange survives on both grounds and IS a choice.

    So the channel is two-state (orange vs knocked-out), not three. Treating
    white as a third symbol reads the printing process as though it were data.
    """
    return ["orange" if c == "orange" else "knock" for c in seq]


def binary_ok(seq):
    """orange=1, knockout=0, in reading order."""
    return "".join("1" if c == "orange" else "0" for c in knockout(seq))


def runlengths(seq):
    out, cur, n = [], None, 0
    for c in seq:
        if c == cur:
            n += 1
        else:
            if cur is not None:
                out.append(n)
            cur, n = c, 1
    if cur is not None:
        out.append(n)
    return out


def selections(runs):
    """Colour as an instruction. 27 assignments of {first,last,whole}."""
    modes = ("first", "last", "whole", "skip")
    out = {}
    for combo in itertools.product(modes, repeat=3):
        rule = dict(zip(COLORS, combo))
        words = []
        for _pg, col, txt in runs:
            m = rule[col]
            t = txt.split()
            if not t or m == "skip":
                continue
            if m == "first":
                words.append(t[0])
            elif m == "last":
                words.append(t[-1])
            else:
                words += t
        if words:
            out["sel_" + "".join(c[0] for c in combo)] = words
    return out


def selftest():
    ok = True
    runs = load()
    ok &= len(runs) == 38
    seq = [r[1] for r in runs]
    from collections import Counter
    cnt = Counter(seq)
    ok &= cnt["orange"] == 22 and cnt["black"] == 10 and cnt["white"] == 6
    sys.stderr.write(f"  {len(runs)} runs: {dict(cnt)} "
                     f"{'OK' if len(runs)==38 else 'FAIL'}\n")

    t = ternary_keys(["orange", "black", "white"])
    # with orange=0 black=1 white=2 the sequence 0,1,2 is 0*9+1*3+2 = 5
    ok &= t.get("tern_012_fwd") == 5
    sys.stderr.write(f"  ternary orange/black/white = 0/1/2 -> "
                     f"{t.get('tern_012_fwd')} (want 5): "
                     f"{'OK' if t.get('tern_012_fwd')==5 else 'FAIL'}\n")
    b = binary_keys(["orange", "black", "orange"])
    ok &= b["bin_orange_fwd_str"] == "101"
    sys.stderr.write(f"  binary orange-vs-rest of o,b,o -> "
                     f"{b['bin_orange_fwd_str']} (want 101): "
                     f"{'OK' if b['bin_orange_fwd_str']=='101' else 'FAIL'}\n")
    rl = runlengths(["orange", "orange", "black", "orange"])
    ok &= rl == [2, 1, 1]
    sys.stderr.write(f"  run lengths of o,o,b,o -> {rl} (want [2,1,1]): "
                     f"{'OK' if rl==[2,1,1] else 'FAIL'}\n")
    s = selections(runs)
    ok &= len(s) > 50
    sys.stderr.write(f"  {len(s)} colour-as-instruction assignments\n")

    # the actual sequence, printed so a human can look at it
    sys.stderr.write("\n  the sequence, in page and reading order:\n    "
                     + " ".join(c[0].upper() for c in seq) + "\n")
    sys.stderr.write(f"    run lengths: {runlengths(seq)}\n")
    ko = knockout(["orange", "black", "white", "orange"])
    ok &= ko == ["orange", "knock", "knock", "orange"]
    sys.stderr.write(f"  white collapses into knockout: "
                     f"{'OK' if ko[1]==ko[2]=='knock' else 'FAIL'}\n")
    ok &= binary_ok(["orange", "black", "white"]) == "100"
    sys.stderr.write(f"  orange=1, black=white=0: "
                     f"{'OK' if binary_ok(['orange','black','white'])=='100' else 'FAIL'}\n")
    # every white run must be on page 77, or the premise is wrong
    wr = [r[0] for r in runs if r[1] == "white"]
    good = set(wr) == {"77"}
    ok &= good
    sys.stderr.write(f"  all {len(wr)} white runs are on page {set(wr)} "
                     f"(the dark page): {'OK' if good else 'FAIL - premise broken'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="hlcolor.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the colour encoding is wrong; refusing")
    if a.selftest:
        return

    import index_cipher as IC
    runs = load()
    seq = [r[1] for r in runs]
    cands, certified = set(), []

    def add(label, s):
        s = str(s)
        if 0 < len(s) < 4000:
            cands.add(s)
            for kind, val in IC.certify(s):
                certified.append((kind, val, label))
                sys.stderr.write(f"\n  *** SELF-CERTIFYING {kind} from {label}\n"
                                 f"      {val}\n")

    for k, v in ternary_keys(seq).items():
        add(k, v)
    for k, v in binary_keys(seq).items():
        add(k, v)
    # the physically correct 2-state reading, and everything derived from it
    bo = binary_ok(seq)
    add("ok_bits", bo)
    add("ok_bits_rev", bo[::-1])
    add("ok_int", int(bo, 2))
    add("ok_int_rev", int(bo[::-1], 2))
    add("ok_hex", format(int(bo, 2), "x"))
    add("ok_hex_rev", format(int(bo[::-1], 2), "x"))
    for pad in (0, 1):
        b = bo + "0" * ((8 - len(bo) % 8) % 8) if pad else "0" * ((8 - len(bo) % 8) % 8) + bo
        by = int(b, 2).to_bytes(len(b) // 8, "big")
        add(f"ok_bytes_pad{pad}", by.hex())
        add(f"ok_ascii_pad{pad}", "".join(chr(x) if 32 <= x < 127 else "?" for x in by))
    add("ok_runlen", "".join(map(str, runlengths(knockout(seq)))))
    sys.stderr.write(f"\n  orange-vs-knockout bits ({len(bo)}):\n    {bo}\n"
                     f"    as int  {int(bo, 2)}\n"
                     f"    as hex  {format(int(bo, 2), 'x')}\n"
                     f"    runs    {runlengths(knockout(seq))}\n")
    rl = runlengths(seq)
    add("runlen", "".join(map(str, rl)))
    add("runlen_sp", " ".join(map(str, rl)))
    add("runlen_rev", "".join(map(str, rl[::-1])))
    wl = [len(t.split()) for _p, _c, t in runs]
    cl = [len(t) for _p, _c, t in runs]
    for nm, s in (("wordlens", wl), ("charlens", cl)):
        add(nm, "".join(map(str, s)))
        add(nm + "_sp", " ".join(map(str, s)))
        add(nm + "_rev", "".join(map(str, s[::-1])))
    for k, words in selections(runs).items():
        add(k, " ".join(words))
        add(k + "_tight", "".join(words))
        add(k + "_first", "".join(w[0] for w in words if w))
        add(k + "_firstlow", "".join(w[0].lower() for w in words if w))

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(cands)) + "\n")
    sys.stderr.write(f"\n  {len(cands):,} candidates -> {a.out}\n"
                     f"  {len(certified)} self-certifying\n")
    if not certified:
        sys.stderr.write("  No colour reading yields a valid WIF, mnemonic or "
                         "64 hex chars.\n")
    sys.stderr.write(f"  next: python3 try_phrases.py --in {a.out} "
                     f"--label hlcolor\n")


if __name__ == "__main__":
    main()
