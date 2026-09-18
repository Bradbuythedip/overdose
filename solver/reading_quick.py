#!/usr/bin/env python3
"""
Author-controlled content channels of the column, as key material.

WHAT THIS ANSWERS  "hidden private keys in the text" (Sand) and "encoded" --
the channels a COLUMNIST controls regardless of the designer: paragraph,
sentence and line initials/finals (acrostics), first/last words per unit,
rule-picked BIP-39 words (first / second / last wordlist word of each line,
sentence, paragraph; the highlighted ones; all of them in print order) with
every 12-24 word window emitted so the sweep's checksum test judges it, and
"El Salvador" used as a POSITION MARKER (it occurs exactly twice in the body:
lines 51 and 64, sentences 43 and 48, paragraphs 7 and 8): the sentences,
lines and paragraphs it sits in, the words after it, and those positions
used as indices.

OMITS  whole sentences/lines/n-grams (clue_serial.py, target sweeps), first
word of each line and alternate lines (gen_sand.py, column_cipher.py),
numerals as indices (index_cipher.py).
"""
import re

def _units():
    import article
    lines, sents, paras = article.load()
    L = [l for l in lines if l.strip()]
    words = " ".join(paras).split()
    return L, list(sents), list(paras), words

def _clean(w): return re.sub(r"[^A-Za-z]", "", w)

def forms():
    from mnemonic import Mnemonic
    WL = set(Mnemonic("english").wordlist)
    L, S, P, words = _units()
    out = []
    def add(tag, v):
        v = (v or "").strip()
        if v: out.append((tag, v))
    def variants(tag, v):
        add(tag, v)
        if v != v.lower(): add(tag + "/lower", v.lower())
        if v != v.upper(): add(tag + "/upper", v.upper())
    # acrostics
    for uname, units in (("para", P), ("sent", S), ("line", L)):
        variants(f"acro/{uname}/initials", "".join(u.strip()[0] for u in units if u.strip()))
        variants(f"acro/{uname}/initials_alpha", "".join(c for c in (u.strip()[0] for u in units if u.strip()) if c.isalpha()))
        variants(f"acro/{uname}/finals_alpha", "".join(c for c in (_clean(u.split()[-1])[-1:] for u in units if u.split()) if c))
        variants(f"words/{uname}/first", " ".join(u.split()[0] for u in units if u.split()))
        variants(f"words/{uname}/last", " ".join(u.split()[-1] for u in units if u.split()))
        variants(f"words/{uname}/first_clean", " ".join(_clean(u.split()[0]) for u in units if u.split()))
        variants(f"words/{uname}/last_clean", " ".join(_clean(u.split()[-1]) for u in units if u.split()))
        variants(f"acro/{uname}/second_letters", "".join(u.strip()[1] for u in units if len(u.strip()) > 1))
    # rule-picked BIP-39 words -> every mnemonic-sized window (the sweep checksum-tests them)
    def picked(units, which):
        res = []
        for u in units:
            ws = [_clean(w).lower() for w in u.split()]
            ws = [w for w in ws if w in WL]
            if not ws: continue
            res.append(ws[0] if which == "first" else ws[-1] if which == "last" else (ws[1] if len(ws) > 1 else None))
        return [w for w in res if w]
    seqs = {}
    for uname, units in (("line", L), ("sent", S), ("para", P)):
        for which in ("first", "second", "last"):
            seqs[f"{uname}/{which}"] = picked(units, which)
    seqs["all_in_order"] = [_clean(w).lower() for w in words if _clean(w).lower() in WL]
    try:
        hl = []
        for l in open("highlights_ordered.tsv", encoding="utf-8"):
            if not l.startswith("#") and l.strip():
                p = l.rstrip("\n").split("\t")
                if len(p) >= 3: hl += [_clean(w).lower() for w in p[2].split() if _clean(w).lower() in WL]
        seqs["highlighted"] = hl
    except OSError:
        pass
    for sname, ws in seqs.items():
        add(f"bip39/{sname}/all", " ".join(ws))
        for k in (12, 15, 18, 21, 24):
            for i in range(0, len(ws) - k + 1):
                add(f"bip39/{sname}/w{k}@{i}", " ".join(ws[i:i + k]))
    # El Salvador as a position marker
    flat = " ".join(P)
    for n, m in enumerate(re.finditer(r"El Salvador", flat)):
        after = flat[m.end():].split()
        before = flat[:m.start()].split()
        for k in (1, 2, 3, 4, 5, 6, 8, 10, 12):
            add(f"es/{n}/after{k}", " ".join(after[:k]))
            add(f"es/{n}/before{k}", " ".join(before[-k:]))
        add(f"es/{n}/after_to_period", re.split(r"[.?!]", flat[m.end():])[0])
    for uname, units in (("line", L), ("sent", S), ("para", P)):
        idx = [i for i, u in enumerate(units) if "El Salvador" in u]
        for i in idx:
            add(f"es/{uname}{i}", units[i])
            add(f"es/{uname}{i}/no_es", units[i].replace("El Salvador", "").strip())
            for base in (0, 1):
                j = i + base
                if j < len(words): add(f"es/{uname}{i}/word_b{base}", words[j])
                if j < len(L): add(f"es/{uname}{i}/line_b{base}", L[j])
                if j < len(S): add(f"es/{uname}{i}/sent_b{base}", S[j])
        add(f"es/{uname}_indices", "".join(str(i) for i in idx))
        add(f"es/{uname}_indices_sp", " ".join(str(i) for i in idx))
        add(f"es/{uname}_indices_b1", "".join(str(i + 1) for i in idx))
        add(f"es/{uname}_joined", " ".join(units[i] for i in idx))
    for v in ("42", "42%", "hyperbitcoinized", "42% of the country is now hyperbitcoinized",
              "El Salvador 42", "42 El Salvador", "El Salvador 42%", "trolling the International Monetary Fund",
              "the president of El Salvador", "back in El Salvador", "Meanwhile, back in El Salvador",
              "El Salvador El Salvador", "ElSalvadorElSalvador", "El Salvador 51 64", "El Salvador 7 8",
              "El Salvador 43 48", "5164", "4348", "78", "El Salvador 5164", "El Salvador 4348"):
        variants("es/const/" + v[:24], v)
    # dedupe by value, keep first tag
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen:
            seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); tags = [t for t, _ in F]; d = dict(F)
    ok = len(F) > 500 and len(set(tags)) == len(tags) and all(v for _, v in F)
    ok &= d.get("acro/para/initials") == "BHRTIGGDMHEIWIBTTTYESM"
    ok &= any(t.startswith("es/const/42% of the country") for t in tags)
    ok &= d.get("es/para_indices") == "78" and d.get("es/line_indices") == "5164"
    return bool(ok)

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
