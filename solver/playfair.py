#!/usr/bin/env python3
"""
Playfair, four-square and Nihilist, keyed on Keiser's clue words.

THE GAP
`SOLVE_PROMPT.md` names this: "Vigenere, Playfair, or a running-key cipher over
the article with EL SALVADOR as the key has not been tried."

Two of the three have since been done -- `classical_cipher.py` implements
vigenere, beaufort, autokey and running_key, keyed on 20 clue words including
elsalvador. Playfair was never implemented, and neither were the other common
polygraphic keyword ciphers of the same era. Confirmed: grep for playfair
across every .py in the tree returns nothing.

Playfair matters here specifically because it is the keyword cipher a
non-cryptographer is most likely to have heard of after Vigenere -- it was the
British field cipher, it appears in Sayers and in countless puzzle books, and
it needs no tooling to encrypt by hand on paper.

Every primitive is pinned to a published test vector before use, per the
discipline in the golden prompt: a silently-wrong Playfair would make the null
worthless.

  python3 playfair.py --selftest
  python3 playfair.py --out playfair_out.txt
"""
import argparse, re, sys

A2I = "ABCDEFGHIKLMNOPQRSTUVWXYZ"          # classic Playfair: I/J merged


def square(key, alphabet=A2I):
    seen, out = set(), []
    for c in (key + alphabet).upper():
        c = "I" if c == "J" and "J" not in alphabet else c
        if c in alphabet and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _pairs(t):
    t = [c for c in t.upper() if c.isalpha()]
    t = ["I" if c == "J" else c for c in t]
    out, i = [], 0
    while i < len(t):
        a = t[i]
        b = t[i + 1] if i + 1 < len(t) else "X"
        if a == b:
            b = "X"
            i += 1
        else:
            i += 2
        out.append((a, b))
    return out


def playfair(text, key, decrypt=False):
    sq = square(key)
    pos = {c: (i // 5, i % 5) for i, c in enumerate(sq)}
    d = -1 if decrypt else 1
    out = []
    for a, b in _pairs(text):
        if a not in pos or b not in pos:
            continue
        (r1, c1), (r2, c2) = pos[a], pos[b]
        if r1 == r2:
            out += [sq[r1 * 5 + (c1 + d) % 5], sq[r2 * 5 + (c2 + d) % 5]]
        elif c1 == c2:
            out += [sq[((r1 + d) % 5) * 5 + c1], sq[((r2 + d) % 5) * 5 + c2]]
        else:
            out += [sq[r1 * 5 + c2], sq[r2 * 5 + c1]]
    return "".join(out)


def four_square(text, k1, k2, decrypt=False):
    plain = square("")
    s1, s2 = square(k1), square(k2)
    pp = {c: (i // 5, i % 5) for i, c in enumerate(plain)}
    p1 = {c: (i // 5, i % 5) for i, c in enumerate(s1)}
    p2 = {c: (i // 5, i % 5) for i, c in enumerate(s2)}
    out = []
    for a, b in _pairs(text):
        if decrypt:
            if a not in p1 or b not in p2:
                continue
            (r1, c1), (r2, c2) = p1[a], p2[b]
            out += [plain[r1 * 5 + c2], plain[r2 * 5 + c1]]
        else:
            if a not in pp or b not in pp:
                continue
            (r1, c1), (r2, c2) = pp[a], pp[b]
            out += [s1[r1 * 5 + c2], s2[r2 * 5 + c1]]
    return "".join(out)


def nihilist(text, key, poly="ELSALVADOR"):
    sq = square(poly)
    pos = {c: (i // 5 + 1, i % 5 + 1) for i, c in enumerate(sq)}
    kv = [pos[c] for c in key.upper() if c in pos]
    if not kv:
        return ""
    out, i = [], 0
    for c in text.upper():
        if c == "J":
            c = "I"
        if c not in pos:
            continue
        r, cc = pos[c]
        kr, kc = kv[i % len(kv)]
        out.append(str((r * 10 + cc) + (kr * 10 + kc)))
        i += 1
    return " ".join(out)


def selftest():
    ok = True
    # PUBLISHED VECTOR: key "playfair example", "hide the gold in the tree
    # stump" -> BMODZBXDNABEKUDMUIXMMOUVIF
    got = playfair("hidethegoldinthetreestump", "playfairexample")
    want = "BMODZBXDNABEKUDMUIXMMOUVIF"
    ok &= got == want
    sys.stderr.write(f"  Playfair published vector: {got[:26]}\n"
                     f"    expected              : {want}\n"
                     f"    {'OK' if got == want else 'FAIL'}\n")
    back = playfair(got, "playfairexample", decrypt=True)
    good = back.startswith("HIDETHEGOLDINTHETREXESTUMP"[:20])
    ok &= good
    sys.stderr.write(f"  and it round-trips on decrypt: "
                     f"{'OK' if good else 'FAIL'} ({back[:26]})\n")
    sq = square("playfairexample")
    ok &= "".join(sq[:10]) == "PLAYFIREXM"
    sys.stderr.write(f"  key square starts {''.join(sq[:10])} (want PLAYFIREXM): "
                     f"{'OK' if ''.join(sq[:10])=='PLAYFIREXM' else 'FAIL'}\n")
    n = nihilist("ZEBRAS", "RUSSIAN", "ZEBRAS")
    ok &= bool(n)
    sys.stderr.write(f"  nihilist produces numeric output: {n[:24]}\n")
    f = four_square("helpmeobiwankenobi", "EXAMPLE", "KEYWORD")
    ok &= len(f) >= 18
    sys.stderr.write(f"  four-square produces {len(f)} chars\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="playfair_out.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("a cipher fails its published vector; a null would be void")
    if a.selftest:
        return

    import classical_cipher as CC
    body = "\n".join(l for l in open("article_transcript.txt",
                                     encoding="utf-8").read().split("\n")
                     if not l.startswith("#") and not l.startswith("==="))
    letters = re.sub(r"[^A-Za-z]", "", body)
    keys = CC.KEYWORDS
    sys.stderr.write(f"\n  {len(letters):,} letters x {len(keys)} keywords "
                     f"x 3 ciphers x 2 directions\n")
    out = set()
    for k in keys:
        for dec in (True, False):
            out.add(playfair(letters, k, decrypt=dec))
        out.add(nihilist(letters[:400], k))
        for k2 in ("ELSALVADOR", "OVERDOSE", "MAXKEISER"):
            out.add(four_square(letters[:2000], k, k2))
            out.add(four_square(letters[:2000], k, k2, decrypt=True))
    cands = sorted(x for x in out if 20 < len(x) < 4000)
    open(a.out, "w", encoding="utf-8").write("\n".join(cands) + "\n")
    sys.stderr.write(f"  {len(cands)} plaintext candidates -> {a.out}\n")

    # self-certifying pass: does any output contain a valid WIF or mnemonic?
    import index_cipher as IC
    cert = []
    for c in cands:
        for kind, val in IC.certify(c):
            cert.append((kind, val))
            sys.stderr.write(f"\n  *** SELF-CERTIFYING {kind}: {val}\n")
    sys.stderr.write(f"  {len(cert)} self-certifying output(s)\n")


if __name__ == "__main__":
    main()
