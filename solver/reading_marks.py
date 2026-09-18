#!/usr/bin/env python3
"""
Printed marks the transcript never carried, read as instructions.

From the lossless text masks (forensics, mask-glyph lens): a rule UNDER
"They discount stuff in advance." and under "protocol." on p75; a mid-height
rule THROUGH the whole line "(and 10years of watching Peter Schiff miss buying
bitcoin" on p76, joined to the black 'nonsense' box; and a HEART between MAX and
KEISER in the p79 signature (the transcript has "MAX KEISER"). Readings: the
underlined phrases alone and joined; the struck line alone, the text with it
removed, the text with only it; the signature with the heart in every spelling
(love / loves / heart / <3 / U+2665 / U+2764); the struck line's words as a
pointer (10 years, Peter Schiff). Design elements in all likelihood; swept so
the question is closed.
"""
import re
U1 = "They discount stuff in advance."; U2 = "protocol."
STRUCK = "(and 10years of watching Peter Schiff miss buying bitcoin"

def forms():
    import article
    lines, sents, paras = article.load(); L = [l for l in lines if l.strip()]
    out = []
    def add(t, v):
        v = (v or "").strip()
        if v: out.append((t, v))
    def variants(t, v):
        add(t, v); add(t + "/lower", v.lower()); add(t + "/upper", v.upper()); add(t + "/nopunct", re.sub(r"[^\w\s]", "", v)); add(t + "/nospace_lower", re.sub(r"\s+", "", v).lower())
    for k, v in (("u1", U1), ("u2", U2), ("u12", U1 + " " + U2), ("u21", U2 + " " + U1), ("u1_noperiod", U1.rstrip(".")), ("u2_word", "protocol"),
                 ("struck", STRUCK), ("struck_clean", "and 10 years of watching Peter Schiff miss buying bitcoin"), ("struck_10years", "10years"),
                 ("struck_schiff", "Peter Schiff"), ("struck_schiff2", "Peter Schiff miss buying bitcoin"), ("struck_10y", "10 years of watching Peter Schiff"),
                 ("nonsense", "nonsense"), ("nonsense_struck", "nonsense " + STRUCK), ("struck_nonsense", STRUCK + " nonsense")):
        variants(k, v)
    # the article without the struck line; the struck line's neighbours
    idx = [i for i, l in enumerate(L) if "Peter Schiff" in l]
    for i in idx:
        add("struck/line_exact", L[i]); add("struck/prev_line", L[i - 1] if i else ""); add("struck/next_line", L[i + 1] if i + 1 < len(L) else "")
        add("struck/prev+next", (L[i - 1] if i else "") + " " + (L[i + 1] if i + 1 < len(L) else ""))
        add("article/without_struck", " ".join(l for j, l in enumerate(L) if j != i))
    uidx = [i for i, l in enumerate(L) if "discount stuff" in l or l.strip().endswith("protocol.")]
    add("underlined/lines", " ".join(L[i] for i in uidx)); add("underlined/next_lines", " ".join(L[i + 1] for i in uidx if i + 1 < len(L)))
    for h in ("♥", "❤", "<3", "love", "loves", "heart", "LOVE", "LOVES", "HEART", "♡", "❤️", "x", "+", "&"):
        variants(f"sig/{h}", f"MAX {h} KEISER"); variants(f"sig2/{h}", f"MAX{h}KEISER"); variants(f"sig3/{h}", f"Max {h} Keiser")
    variants("sig/plain", "MAX KEISER"); variants("sig/love_keiser", "love keiser"); variants("sig/max_love", "max love"); variants("sig/maxloveskeiser", "Max loves Keiser")
    variants("sig/keiser_heart", "KEISER ♥"); variants("sig/heart_only", "♥"); variants("sig/max_heart", "MAX ♥")
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); tags = [t for t, _ in F]
    return len(set(tags)) == len(tags) and all(v for _, v in F) and ("sig/♥", "MAX ♥ KEISER") in F

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
