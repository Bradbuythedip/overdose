#!/usr/bin/env python3
"""
The highlight runs used as a KEY into the text, not as content.

highlight_sequence.py read the 38 highlighted runs themselves (whole, per
colour, odd/even, first/last words, acrostic). Nothing has used them as a
pointer: the word immediately AFTER each run, the word BEFORE it, the n-th
word after it where n is the run's own length, the run lengths (words and
letters) as digit strings and as wordlist indices (English/Spanish/French/
Italian, every 12-24 window), the sentence each run ends, and the same for
the 44 all-caps words and the 5 quotation marks.
"""
import re

def _runs():
    import article
    lines, sents, paras = article.load()
    flat = " ".join(paras); words = flat.split()
    low = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
    runs = []
    for l in open("highlights_ordered.tsv", encoding="utf-8"):
        if l.startswith("#") or not l.strip(): continue
        p = l.rstrip("\n").split("\t")
        if len(p) < 3: continue
        hw = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in p[2].split()]
        hw = [w for w in hw if w]
        if not hw: continue
        for i in range(len(low) - len(hw) + 1):
            if low[i:i + len(hw)] == hw:
                runs.append((i, i + len(hw), p[2])); break
    return words, sents, runs

def forms():
    from mnemonic import Mnemonic
    WL = {l: Mnemonic(l).wordlist for l in ("english", "spanish", "french", "italian")}
    words, sents, runs = _runs()
    out = []
    def add(t, v):
        v = (v or "").strip()
        if v: out.append((t, v))
    after = [words[e] for s, e, _ in runs if e < len(words)]
    before = [words[s - 1] for s, e, _ in runs if s > 0]
    nth = [words[e - 1 + (e - s)] for s, e, _ in runs if e - 1 + (e - s) < len(words)]
    after2 = [" ".join(words[e:e + 2]) for s, e, _ in runs]
    for nm, seq in (("after", after), ("before", before), ("nth_after", nth), ("after2", after2)):
        v = " ".join(seq); add(f"hl/{nm}", v); add(f"hl/{nm}/lower", v.lower())
        add(f"hl/{nm}/clean", " ".join(re.sub(r"[^A-Za-z]", "", w) for w in seq))
        add(f"hl/{nm}/initials", "".join(w[0] for w in seq if w))
        for k in (12, 15, 18, 21, 24):
            for i in range(0, len(seq) - k + 1):
                add(f"hl/{nm}/w{k}@{i}", " ".join(re.sub(r"[^A-Za-z]", "", w).lower() for w in seq[i:i + k]))
    lens_w = [e - s for s, e, _ in runs]; lens_c = [len(re.sub(r"[^A-Za-z]", "", t)) for _, _, t in runs]
    starts = [s for s, _, _ in runs]; ends = [e for _, e, _ in runs]
    for nm, seq in (("len_words", lens_w), ("len_chars", lens_c), ("starts", starts), ("ends", ends), ("gaps", [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)])):
        add(f"hl/{nm}/digits", "".join(str(n) for n in seq)); add(f"hl/{nm}/spaced", " ".join(str(n) for n in seq))
        add(f"hl/{nm}/mod10", "".join(str(n % 10) for n in seq))
        for lang, wl in WL.items():
            for base in (0, 1):
                ws = [wl[(n - base) % 2048] for n in seq]
                for k in (12, 15, 18, 21, 24):
                    for i in range(0, len(ws) - k + 1):
                        add(f"hl/{nm}/{lang}/b{base}/w{k}@{i}", f"mn:{lang}:" + " ".join(ws[i:i + k]))
        # the words at those indices
        add(f"hl/{nm}/as_word_index", " ".join(words[n % len(words)] for n in seq))
        add(f"hl/{nm}/as_word_index_b1", " ".join(words[(n - 1) % len(words)] for n in seq))
    # sentences that end a run / contain a run start
    flat = " ".join(words); pos = 0; sent_of = []
    bounds = []
    for s_ in sents:
        i = flat.find(s_, pos); bounds.append((i, i + len(s_))); pos = i + len(s_) if i >= 0 else pos
    char_of_word = []; c = 0
    for w in words: char_of_word.append(c); c += len(w) + 1
    def sent_idx(wi):
        ch = char_of_word[min(wi, len(words) - 1)]
        for k, (a, b) in enumerate(bounds):
            if a <= ch < b: return k
        return None
    si = [sent_idx(s) for s, _, _ in runs]; si = [k for k in si if k is not None]
    add("hl/sentences_joined", " ".join(sents[k] for k in dict.fromkeys(si)))
    add("hl/sentence_indices", "".join(str(k) for k in si)); add("hl/sentence_first_words", " ".join(sents[k].split()[0] for k in si))
    # all-caps words: the word after each
    caps_after = [words[i + 1] for i, w in enumerate(words[:-1]) if len(re.sub(r"[^A-Za-z]", "", w)) >= 2 and re.sub(r"[^A-Za-z]", "", w).isupper()]
    add("caps/after", " ".join(caps_after)); add("caps/after/initials", "".join(w[0] for w in caps_after))
    # quotation marks: the quoted spans and the words after each closing quote
    q = re.findall(r"[\"“]([^\"”]{1,120})[\"”]", flat)
    add("quotes/spans", " | ".join(q)); add("quotes/joined", " ".join(q))
    for i, s_ in enumerate(q): add(f"quotes/{i}", s_)
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    words, sents, runs = _runs()
    F = forms(); tags = [t for t, _ in F]
    print(f"  {len(runs)} highlight runs located in the text; {len(F)} forms")
    return len(runs) >= 30 and len(set(tags)) == len(tags) and all(v for _, v in F)

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
