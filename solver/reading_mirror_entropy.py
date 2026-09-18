#!/usr/bin/env python3
"""
The MIRRORED serial as BIP-39 entropy, judged by whether its words are IN THE
MAGAZINE -- a criterion independent of the chain.

The $100 note is printed mirrored on page 73, so the serial a reader sees is
A 41714867 LC; the KB note mirrored reads I 06897264 BK. If Keiser used the
mirrored serial as entropy for a mnemonic and then hid that mnemonic "in the
text", the mnemonic's words should appear in the column far above chance.
This takes every mirror / rot180 form of both serials (and the originals as
controls), extends each to 16 or 32 bytes every way a person would (ASCII,
ASCII doubled, packed digits tiled or padded, the integer, sha256 and its
half), builds the mnemonic in English / Spanish / French / Italian, and counts
how many of its words occur in the article and in the highlighted runs,
against the distribution for random mnemonics. forms() emits the entropies as
'hex:' so the sweep also derives every one (9 passphrases x 72 paths).

  python3 reading_mirror_entropy.py --report
"""
import hashlib, random, re, sys

A_D, B_D, A_STR, B_STR = "76841714", "46279860", "CL76841714A", "KB46279860"
LANGS = ("english", "spanish", "french", "italian")

def sources():
    import mirror_serial as MS
    S = {}
    for nm, s in (("A", A_D), ("B", B_D), ("Astr", A_STR), ("Bstr", B_STR), ("BstrI", B_STR + "I"), ("BstrL", B_STR + "L")):
        S[f"{nm}"] = s
        S[f"{nm}.mirror"] = s[::-1]
        S[f"{nm}.rot180"] = MS.rot180(s)
        S[f"{nm}.mirrorglyph"] = MS.mirror(s)
    S["AB"] = A_D + B_D; S["AB.mirror"] = (A_D + B_D)[::-1]; S["BA.mirror"] = (B_D + A_D)[::-1]
    S["mirA+mirB"] = A_D[::-1] + B_D[::-1]; S["mirB+mirA"] = B_D[::-1] + A_D[::-1]
    S["AB.rot180"] = MS.rot180(A_D + B_D); S["BA.rot180"] = MS.rot180(B_D + A_D)
    S["AstrBstr.mirror"] = (A_STR + B_STR)[::-1]; S["AstrBstr.rot180"] = MS.rot180(A_STR + B_STR)
    return S

def entropies():
    E = []
    for nm, s in sources().items():
        b = s.encode()
        if len(b) in (16, 20, 24, 28, 32): E.append((f"{nm}/ascii", b))
        if len(b) * 2 in (16, 32): E.append((f"{nm}/ascii_x2", b * 2))
        if len(b) * 4 == 32: E.append((f"{nm}/ascii_x4", b * 4))
        E.append((f"{nm}/ascii_rpad16", b[:16].ljust(16, b"\0"))); E.append((f"{nm}/ascii_lpad16", b[-16:].rjust(16, b"\0")))
        d = re.sub(r"\D", "", s)
        if d and len(d) % 2 == 0:
            bcd = bytes.fromhex(d)
            for k in (16 // len(bcd) if len(bcd) and 16 % len(bcd) == 0 else 0, 32 // len(bcd) if len(bcd) and 32 % len(bcd) == 0 else 0):
                if k: E.append((f"{nm}/bcd_x{k}", bcd * k))
            E.append((f"{nm}/bcd_lpad16", bcd[-16:].rjust(16, b"\0"))); E.append((f"{nm}/bcd_rpad16", bcd[:16].ljust(16, b"\0")))
        if d:
            n = int(d)
            E.append((f"{nm}/int16", n.to_bytes(16, "big"))); E.append((f"{nm}/int16le", n.to_bytes(16, "little")))
            E.append((f"{nm}/int32", n.to_bytes(32, "big")))
            try:
                h = int(d, 16); E.append((f"{nm}/hexint16", h.to_bytes(16, "big")))
            except ValueError: pass
        E.append((f"{nm}/sha256", hashlib.sha256(b).digest())); E.append((f"{nm}/sha256_16", hashlib.sha256(b).digest()[:16]))
    seen, uniq = set(), []
    for t, e in E:
        if e not in seen and len(e) in (16, 20, 24, 28, 32): seen.add(e); uniq.append((t, e))
    return uniq

def forms():
    return [(t, "hex:" + e.hex()) for t, e in entropies()]

def report():
    from mnemonic import Mnemonic
    import article
    lines, sents, paras = article.load()
    words = {re.sub(r"[^a-z]", "", w.lower()) for w in " ".join(paras).split()}
    hl = set()
    try:
        for l in open("highlights_ordered.tsv", encoding="utf-8"):
            if not l.startswith("#") and l.strip():
                p = l.rstrip("\n").split("\t")
                if len(p) >= 3: hl |= {re.sub(r"[^a-z]", "", w.lower()) for w in p[2].split()}
    except OSError: pass
    M = {l: Mnemonic(l) for l in LANGS}
    E = entropies(); random.seed(11)
    rows = []
    for t, e in E:
        for lang, m in M.items():
            ws = m.to_mnemonic(e).split()
            inart = sum(1 for w in ws if w in words); inhl = sum(1 for w in ws if w in hl)
            rows.append((inart / len(ws), inart, inhl, len(ws), lang, t, " ".join(ws)))
    # chance: random mnemonics of the same sizes per language
    base = {}
    for lang, m in M.items():
        for n in (12, 24):
            vals = []
            for _ in range(1500):
                ws = m.to_mnemonic(random.randbytes(16 if n == 12 else 32)).split()
                vals.append(sum(1 for w in ws if w in words))
            vals.sort(); base[(lang, n)] = (sum(vals) / len(vals), vals[int(0.99 * len(vals))], vals[-1])
    rows.sort(reverse=True)
    print(f"{len(E)} entropies x {len(LANGS)} languages = {len(rows)} mnemonics; article vocabulary {len(words)} words, {len(hl)} highlighted words")
    print("chance (random mnemonics): mean / 99th pct / max words-in-article:", {f"{l}/{n}": tuple(round(x, 1) for x in v) for (l, n), v in base.items()})
    print("\ntop overlaps:")
    for frac, inart, inhl, n, lang, t, mn in rows[:15]:
        print(f"  {inart:2d}/{n} in article, {inhl} highlighted  {lang:8s} {t:32s} {mn[:80]}")
    m_ctrl = [r for r in rows if r[5].startswith(("A/", "B/", "Astr/", "Bstr/")) and ".mirror" not in r[5] and "rot180" not in r[5]]
    m_mirr = [r for r in rows if ".mirror" in r[5] or "rot180" in r[5] or "mir" in r[5]]
    if m_ctrl and m_mirr:
        print(f"\nmean words-in-article: mirrored/rot180 forms {sum(r[1] for r in m_mirr)/len(m_mirr):.2f} vs original forms {sum(r[1] for r in m_ctrl)/len(m_ctrl):.2f}")

def selftest():
    F = forms(); tags = [t for t, _ in F]
    ok = len(set(tags)) == len(tags) and all(v.startswith("hex:") for _, v in F) and len(F) > 60
    ok &= any(t == "A.mirror/ascii_x2" for t in tags) and dict(F)["A.mirror/ascii_x2"] == "hex:" + (b"41714867" * 2).hex()
    print(f"  {len(F)} entropy forms")
    return bool(ok)

if __name__ == "__main__":
    if "--report" in sys.argv: report()
    else: print(len(forms()), "forms; selftest", selftest())
