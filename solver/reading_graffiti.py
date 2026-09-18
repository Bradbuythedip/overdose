#!/usr/bin/env python3
"""
The marker strokes of the p78 graffiti read as digits and pointers.

Around the scribbled pull-quote ("X FUCK ALL X") the marker leaves strokes no
transcript records: a "5"- or "S"-shaped squiggle left of "love", a pair
before the right-hand X that reads "15" or "75" (or "1S" / "7S"), and two
drips that could pass for "1" / "!" / "i". Flourishes in all likelihood; this
sweeps the digit strings, their concatenations with the frame text and the
quote, and the pointer readings (page, line, word, letter at those indices)
so the question is closed by measurement rather than taste.
"""
import re

DIGITS = ["5", "15", "75", "1", "51", "515", "5 15", "5 75", "1 5", "7 5", "155", "5151", "1515", "S", "1S", "7S", "S15", "5X", "15X"]
FRAME = ["X FUCK ALL X", "FUCK ALL"]
Q = "The economy of love is infinitely more efficient than hate and war."

def forms():
    import article
    lines, sents, paras = article.load(); L = [l for l in lines if l.strip()]; words = " ".join(paras).split()
    raw = open("article_transcript.txt", encoding="utf-8").read()
    pages, cur = {}, None
    for l in raw.splitlines():
        m = re.match(r"^=== PAGE (\d+)", l)
        if m: cur = int(m.group(1)); pages[cur] = []; continue
        if cur and l.strip() and not l.startswith("#"): pages[cur].append(l.rstrip())
    out = []
    def add(t, v):
        v = (v or "").strip()
        if v: out.append((t, v))
    for d in DIGITS:
        add(f"d/{d}", d)
        for f in FRAME:
            add(f"d/{d}/frame_after", f + " " + d); add(f"d/{d}/frame_before", d + " " + f); add(f"d/{d}/frame_in", f.replace(" X", f" {d} X", 1) if " X" in f else f + d)
        add(f"d/{d}/quote", Q + " " + d); add(f"d/{d}/quote_before", d + " " + Q); add(f"d/{d}/love", "love " + d); add(f"d/{d}/love2", d + " love")
        add(f"d/{d}/nospace", d.replace(" ", ""))
    # pointers
    for n in (5, 15, 75, 1, 51, 515, 155):
        if n <= len(L): add(f"ptr/line{n}", L[n - 1]); add(f"ptr/line{n}/first", L[n - 1].split()[0]); add(f"ptr/line{n}/last", L[n - 1].split()[-1])
        if n <= len(words): add(f"ptr/word{n}", words[n - 1]); add(f"ptr/word{n}_b0", words[n % len(words)])
        if n <= len(sents): add(f"ptr/sent{n}", sents[n - 1])
        if n <= len(paras): add(f"ptr/para{n}", paras[n - 1])
        if n in pages: add(f"ptr/page{n}/first_line", pages[n][0]); add(f"ptr/page{n}/last_line", pages[n][-1]); add(f"ptr/page{n}/first_words", " ".join(l.split()[0] for l in pages[n] if l.split()))
    # line 15 word 5, line 5 word 15, page 75 line 15, page 75 line 5 word 15 ...
    def w(ls, li, wi):
        try: return ls[li - 1].split()[wi - 1]
        except Exception: return None
    add("ptr/l15w5", w(L, 15, 5)); add("ptr/l5w15", w(L, 5, 15)); add("ptr/l5w1", w(L, 5, 1)); add("ptr/l1w5", w(L, 1, 5))
    if 75 in pages:
        add("ptr/p75/l15", pages[75][14] if len(pages[75]) > 14 else None); add("ptr/p75/l5", pages[75][4] if len(pages[75]) > 4 else None)
        add("ptr/p75/l5w15", w(pages[75], 5, 15)); add("ptr/p75/l15w5", w(pages[75], 15, 5)); add("ptr/p75/l1w5", w(pages[75], 1, 5))
    for n in (5, 15, 75):
        add(f"ptr/hl_run{n}", None)
    try:
        hl = [l.rstrip("\n").split("\t")[2] for l in open("highlights_ordered.tsv", encoding="utf-8") if not l.startswith("#") and l.strip() and len(l.split("\t")) >= 3]
        for n in (5, 15):
            if n <= len(hl): add(f"ptr/highlight{n}", hl[n - 1])
    except OSError: pass
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); tags = [t for t, _ in F]
    return len(set(tags)) == len(tags) and all(v for _, v in F) and ("d/15", "15") in F

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
