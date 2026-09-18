#!/usr/bin/env python3
"""
Geometric and cipher readings of the OVERDOSE text block, scored and swept.

RULES (all on article.load(): printed lines per page, sentences, paragraphs)
  columns    the k-th character of every printed line (k = 1..40), per page and
             for the whole column; the k-th character counted from the line END
  diagonals  character (i, i+o) down the lines, both slopes, offsets -20..20
  kth word   the k-th word of every line (k = 2..8): the words, and their initials
  punctuation commas / periods / dashes / quotes per line, sentence, paragraph
             as digit strings
  cipher     every acrostic string (line / sentence / paragraph initials and
             finals, highlight-run initials, first-word initials) decoded under
             Caesar 1..25, Atbash, and Vigenere with the clue words (EL SALVADOR,
             OVERDOSE, KEISER, MAX KEISER, BUKELE, SAND, GEORGE SAND, LEONARDO,
             MIRROR, BITCOIN, SATOSHI, TOXIC) -- and scored for English against
             a shuffled baseline; anything that beats its baseline is reported.
Every string is also emitted as material for the index sweep (HD seeds on).

  python3 reading_scavenge.py            # forms count + selftest
  python3 reading_scavenge.py --report   # the English-scored decodes
"""
import re, sys, random, itertools

KEYS = ["ELSALVADOR", "OVERDOSE", "KEISER", "MAXKEISER", "BUKELE", "SAND", "GEORGESAND", "LEONARDO", "MIRROR",
        "BITCOIN", "SATOSHI", "TOXIC", "SALVADOR", "NAYIB"]
A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _units():
    import article
    lines, sents, paras = article.load()
    raw = open("article_transcript.txt", encoding="utf-8").read()
    pages = {}
    cur = None
    for l in raw.splitlines():
        m = re.match(r"^=== PAGE (\d+)", l)
        if m: cur = int(m.group(1)); pages[cur] = []; continue
        if cur and l.strip() and not l.startswith("#"): pages[cur].append(l.rstrip())
    L = [l for l in lines if l.strip()]
    return L, list(sents), list(paras), pages

def _vocab():
    from mnemonic import Mnemonic
    import article
    lines, sents, paras = article.load()
    v = set(Mnemonic("english").wordlist)
    v |= {re.sub(r"[^a-z]", "", w.lower()) for w in " ".join(paras).split()}
    v |= set("the and for are but not you all any can had her was one our out day get has him his how man new now old see two way who boy did its let put say she too use key keys bitcoin satoshi private seed phrase word words hidden mirror sand salvador overdose keiser toxic money fiat gold".split())
    return {w for w in v if len(w) >= 3}

def english_score(s, vocab):
    s = re.sub(r"[^a-z]", "", s.lower())
    n = len(s)
    if n < 6: return 0.0
    best = [0] * (n + 1)
    for i in range(1, n + 1):
        best[i] = best[i - 1]
        for k in range(3, min(12, i) + 1):
            if s[i - k:i] in vocab: best[i] = max(best[i], best[i - k] + k)
    return best[n] / n

def caesar(s, k): return "".join(A[(A.index(c) + k) % 26] if c in A else c for c in s)
def atbash(s): return "".join(A[25 - A.index(c)] if c in A else c for c in s)
def vig(s, key, sign=-1):
    out, j = [], 0
    for c in s:
        if c in A:
            out.append(A[(A.index(c) + sign * (A.index(key[j % len(key)]))) % 26]); j += 1
        else: out.append(c)
    return "".join(out)

def extract():
    L, S, P, pages = _units()
    out = []
    def add(t, v):
        v = (v or "").strip()
        if len(v) >= 3: out.append((t, v))
    blocks = {"all": L}
    blocks.update({f"p{p}": ls for p, ls in pages.items()})
    for bn, ls in blocks.items():
        for k in range(1, 41):
            add(f"col/{bn}/k{k}", "".join(l[k - 1] for l in ls if len(l) >= k))
            add(f"col/{bn}/end{k}", "".join(l[-k] for l in ls if len(l) >= k))
            add(f"col/{bn}/k{k}/alpha", "".join(c for c in (l[k - 1] for l in ls if len(l) >= k) if c.isalpha()))
        for o in range(-20, 21):
            add(f"diag/{bn}/down/o{o}", "".join(l[i + o] for i, l in enumerate(ls) if 0 <= i + o < len(l)))
            add(f"diag/{bn}/up/o{o}", "".join(l[len(l) - 1 - i - o] for i, l in enumerate(ls) if 0 <= len(l) - 1 - i - o < len(l)))
        for k in range(2, 9):
            ws = [l.split()[k - 1] for l in ls if len(l.split()) >= k]
            add(f"kword/{bn}/k{k}", " ".join(ws))
            add(f"kword/{bn}/k{k}/initials", "".join(w[0] for w in ws))
    for uname, U in (("line", L), ("sent", S), ("para", P)):
        for ch, nm in ((",", "comma"), (".", "period"), ("-", "dash"), ('"', "quote"), ("'", "apos"), ("?", "q")):
            add(f"punct/{uname}/{nm}", "".join(str(u.count(ch) % 10) for u in U))
        add(f"punct/{uname}/words_mod10", "".join(str(len(u.split()) % 10) for u in U))
    # acrostics to decode
    acros = {
        "line_initials": "".join(l.strip()[0] for l in L), "line_finals": "".join(re.sub(r"[^A-Za-z]", "", l)[-1:] for l in L),
        "sent_initials": "".join(s.strip()[0] for s in S), "para_initials": "".join(p.strip()[0] for p in P),
        "para_finals": "".join(re.sub(r"[^A-Za-z]", "", p)[-1:] for p in P),
        "line_first_word_initials": "".join(l.split()[0][0] for l in L if l.split()),
        "line_last_word_initials": "".join(l.split()[-1][0] for l in L if l.split()),
    }
    try:
        hl = [l.rstrip("\n").split("\t")[2] for l in open("highlights_ordered.tsv", encoding="utf-8") if not l.startswith("#") and l.strip() and len(l.split("\t")) >= 3]
        acros["highlight_initials"] = "".join(h.strip()[0] for h in hl if h.strip())
        acros["highlight_word_initials"] = "".join(w[0] for h in hl for w in h.split())
    except OSError:
        pass
    decodes = []
    for an, s in acros.items():
        s = re.sub(r"[^A-Za-z]", "", s).upper()
        add(f"acro/{an}", s)
        for k in range(1, 26): decodes.append((f"acro/{an}/caesar{k}", caesar(s, k)))
        decodes.append((f"acro/{an}/atbash", atbash(s)))
        for key in KEYS:
            decodes.append((f"acro/{an}/vig-{key}", vig(s, key, -1)))
            decodes.append((f"acro/{an}/vig+{key}", vig(s, key, +1)))
            decodes.append((f"acro/{an}/beaufort-{key}", "".join(A[(A.index(key[j % len(key)]) - A.index(c)) % 26] for j, c in enumerate(s))))
    for t, v in decodes: add(t, v)
    return out, decodes

def forms():
    out, _ = extract()
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def report():
    vocab = _vocab(); random.seed(7)
    out, decodes = extract()
    scored = []
    for t, v in out:
        if not re.search(r"[A-Za-z]{6,}", v.replace(" ", "")): continue
        sc = english_score(v, vocab)
        letters = re.sub(r"[^a-z]", "", v.lower())
        base = sum(english_score("".join(random.sample(letters, len(letters))), vocab) for _ in range(12)) / 12
        scored.append((sc - base, sc, base, t, v))
    scored.sort(reverse=True)
    print("top English-scored extractions (score, shuffled baseline, tag, text):")
    for d, sc, base, t, v in scored[:25]:
        print(f"  +{d:.2f}  {sc:.2f} vs {base:.2f}  {t:40s} {v[:90]}")
    print(f"\n{len(scored)} strings scored; {sum(1 for d,*_ in scored if d > 0.25)} beat their baseline by > 0.25")

def selftest():
    F = forms(); tags = [t for t, _ in F]
    ok = len(set(tags)) == len(tags) and all(v for _, v in F) and len(F) > 1500
    ok &= caesar("ABC", 1) == "BCD" and atbash("ABC") == "ZYX" and vig(vig("HELLO", "KEY", +1), "KEY", -1) == "HELLO"
    print(f"  {len(F)} forms")
    return bool(ok)

if __name__ == "__main__":
    if "--report" in sys.argv: report()
    else: print(len(forms()), "forms; selftest", selftest())
