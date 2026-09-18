#!/usr/bin/env python3
"""
Candidates from the newly recovered record, plus the one refuted-but-unswept
reading: cheap, low prior, and never in any candidate file.

From the research pass (window/clue_ledger.md, 2026-09-18 additions):
  - the ONE sentence the publisher itself quoted from the piece (tweet
    1492561542751137793, 2022-02-12), in the tweet's social form and the
    printed two-sentence form
  - Keiser's own launch captions: "2012 vs 2021" (2021-11-11), "Bitcoin Is
    Toxic AF" with straight and curly quotes, "The original toxic
    maximalist", "10 yrs in the game" (2021-11-19)
From the interpretation pass: the material bracketed by the two body-copy
occurrences of "El Salvador" (lines 51 and 64) in char / line / sentence /
word framings and its in-bracket Sand and Musset sub-readings. The fit critic
refuted it as what Keiser meant (27/80) and the research pass showed the
'El Salvador is a clue' tweet was a reply quip; it is swept because the
coverage skeptic confirmed it was never emitted and it costs nothing.
"""
import re

PUB_TWEET = ("Our imaginations & inventiveness have been euthanized by the rancid catnip of fiat money. "
             "#Bitcoin puts an end to the paper chase Manhattan bank money laundering lobotomy.")
PUB_PRINT = ("Our imaginations and inventiveness have been euthanized by the rancid catnip of fiat money. "
             "Fortunately, bitcoin puts an end to the paper chase Manhattan Bank money laundering lobotomy.")
CAPTIONS = ["2012 vs 2021", "2012vs2021", "2012 2021", "20122021", "2012-2021", "2021 vs 2012", "2012 vs. 2021",
            "Bitcoin Is Toxic AF", "\"Bitcoin Is Toxic AF\"", "“Bitcoin Is Toxic AF”", "Bitcoin is toxic AF",
            "The original toxic maximalist", "the original toxic maximalist", "10 yrs in the game", "10 years in the game",
            "toxic maximalist", "toxic Bitcoin maximalism", "toxic #Bitcoin maximalism", "Read my OVERDOSE column",
            "Read my piece in @BitcoinMagazine", "Use Promo Code ORANGEPILL for 21% Off", "21% Off", "ORANGEPILL 21",
            "Who is The Banana Republic Now, Biatch?", "Buy Love, Sell Fear", "Bitcoin Is A Mirror That Reveals All",
            "Bitcoin is a mirror", "#Bitcoin is mirror", "Bitcoin is a mirror that reveals all"]


def _variants(tag, s, out):
    forms = {"": s, "/lower": s.lower(), "/upper": s.upper(),
             "/nopunct": re.sub(r"[^\w\s]", "", s), "/nopunct_lower": re.sub(r"[^\w\s]", "", s).lower(),
             "/nospace": re.sub(r"\s+", "", s), "/nospace_lower": re.sub(r"\s+", "", s).lower(),
             "/alpha_lower": re.sub(r"[^a-z]", "", s.lower())}
    for k, v in forms.items():
        if v: out.append((tag + k, v))


def forms():
    out = []
    _variants("pub/tweet", PUB_TWEET, out); _variants("pub/print", PUB_PRINT, out)
    _variants("pub/print_s1", PUB_PRINT.split(". ")[0] + ".", out)
    _variants("pub/print_s2", PUB_PRINT.split(". ")[1], out)
    for i, c in enumerate(CAPTIONS): _variants(f"caption/{i}", c, out)
    import article
    lines, sents, paras = article.load(); flat = " ".join(paras)
    occ = list(re.finditer(r"El Salvador", flat))
    if len(occ) == 2:
        m0, m1 = occ
        words = flat.split()
        w0 = len(flat[:m0.start()].split()); w1 = len(flat[:m1.start()].split())
        L = [l for l in lines if l.strip()]
        li = [i for i, l in enumerate(L) if "El Salvador" in l]
        si = [i for i, s_ in enumerate(sents) if "El Salvador" in s_]
        span_lines = L[li[0] + 1:li[1]]
        base = {
            "es/between/chars": flat[m0.end():m1.start()].strip(),
            "es/between/chars_incl": flat[m0.start():m1.end()],
            "es/between/lines": " ".join(span_lines),
            "es/between/lines_incl": " ".join(L[li[0]:li[1] + 1]),
            "es/between/lines_nl": "\n".join(span_lines),
            "es/between/sents": " ".join(sents[si[0] + 1:si[1]]),
            "es/between/sents_incl": " ".join(sents[si[0]:si[1] + 1]),
            "es/between/words": " ".join(words[w0 + 2:w1]),
            "es/between/words_incl": " ".join(words[w0:w1 + 2]),
            "es/between/sand_odd": " ".join(span_lines[0::2]),
            "es/between/sand_even": " ".join(span_lines[1::2]),
            "es/between/first_words": " ".join(l.split()[0] for l in span_lines if l.split()),
            "es/between/last_words": " ".join(l.split()[-1] for l in span_lines if l.split()),
            "es/between/initials": "".join(l.strip()[0] for l in span_lines if l.strip()),
            "es/between/sent_first_words": " ".join(s_.split()[0] for s_ in sents[si[0] + 1:si[1]] if s_.split()),
        }
        for t, v in base.items():
            _variants(t, v, out)
            _variants(t + "/+ES", v + " El Salvador", out)
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq


def selftest():
    F = forms(); tags = [t for t, _ in F]; d = dict(F)
    ok = len(set(tags)) == len(tags) and all(v for _, v in F)
    ok &= "pub/tweet" in d and d["pub/tweet"].startswith("Our imaginations &")
    ok &= any(t == "es/between/lines" for t in tags) and len(d.get("es/between/lines", "").split()) > 80
    print(f"  {len(F)} forms; span between the El Salvadors = {len(d.get('es/between/lines','').split())} words")
    return bool(ok)


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
