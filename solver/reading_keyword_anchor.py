#!/usr/bin/env python3
"""
Theme words as anchors: the word after / before every occurrence of the
column's key nouns, and the two capitalisation streams of Bitcoin/bitcoin.

"El Salvador" was tried as a position marker (reading_quick.py). The same
device for the words the column is actually about -- love (11x), bitcoin/
Bitcoin (30x, whose capitalisation is the one 30-bit channel the author
controls), peace, war, hate, fear, money, gold, fiat, toxic, energy -- was
not. For each anchor: the next word, the previous word, the next two words,
in print order, as phrases, as initials, and as every 12-24 window of the
wordlist words among them. For Bitcoin/bitcoin the two capitalisation streams
are read separately: if the capital letter marked the following word, the
17 words after 'Bitcoin' are the message.
"""
import re

ANCHORS = ["love", "bitcoin", "peace", "war", "hate", "fear", "money", "gold", "fiat", "toxic", "energy", "shitcoin", "economy", "efficient"]

def forms():
    import article
    from mnemonic import Mnemonic
    WL = set(Mnemonic("english").wordlist)
    lines, sents, paras = article.load(); words = " ".join(paras).split()
    clean = lambda w: re.sub(r"[^A-Za-z']", "", w)
    out = []
    def add(t, v):
        v = (v or "").strip()
        if v: out.append((t, v))
    def emit(tag, seq):
        if not seq: return
        add(f"{tag}", " ".join(seq)); add(f"{tag}/lower", " ".join(seq).lower())
        add(f"{tag}/clean", " ".join(clean(w) for w in seq)); add(f"{tag}/initials", "".join(clean(w)[:1] for w in seq if clean(w)))
        ws = [clean(w).lower() for w in seq if clean(w).lower() in WL]
        for k in (12, 15, 18, 21, 24):
            for i in range(0, len(ws) - k + 1): add(f"{tag}/w{k}@{i}", " ".join(ws[i:i + k]))
    for a in ANCHORS:
        idx = [i for i, w in enumerate(words) if clean(w).lower().startswith(a)]
        emit(f"{a}/after", [words[i + 1] for i in idx if i + 1 < len(words)])
        emit(f"{a}/before", [words[i - 1] for i in idx if i > 0])
        emit(f"{a}/after2", [" ".join(words[i + 1:i + 3]) for i in idx])
        emit(f"{a}/after_skip1", [words[i + 2] for i in idx if i + 2 < len(words)])
        add(f"{a}/positions", " ".join(str(i) for i in idx)); add(f"{a}/count", str(len(idx)))
    cap = [i for i, w in enumerate(words) if clean(w).startswith("Bitcoin")]
    low = [i for i, w in enumerate(words) if clean(w).startswith("bitcoin")]
    emit("Bitcoin_cap/after", [words[i + 1] for i in cap if i + 1 < len(words)]); emit("bitcoin_low/after", [words[i + 1] for i in low if i + 1 < len(words)])
    emit("Bitcoin_cap/before", [words[i - 1] for i in cap if i > 0]); emit("bitcoin_low/before", [words[i - 1] for i in low if i > 0])
    emit("Bitcoin_cap/after2", [" ".join(words[i + 1:i + 3]) for i in cap]); emit("bitcoin_low/after2", [" ".join(words[i + 1:i + 3]) for i in low])
    # the sentence each capitalised Bitcoin sits in: first word
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); d = dict(F); tags = [t for t, _ in F]
    ok = len(set(tags)) == len(tags) and all(v for _, v in F) and "love/after" in d
    print("  love/after ->", d.get("love/after", "")[:120]); print("  Bitcoin_cap/after ->", d.get("Bitcoin_cap/after", "")[:120]); print("  bitcoin_low/after ->", d.get("bitcoin_low/after", "")[:120])
    return bool(ok)

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
