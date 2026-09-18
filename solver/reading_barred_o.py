#!/usr/bin/env python3
"""
The barred 'o' of "love" in the scribbled pull-quote (p78), read every way.

The scavenger's glyph measurement: in the white-on-scribble printing of the
pull-quote on page 78 the second letter of "love" is a ring with a horizontal
bar through its centre that exits right into the 'v', present in the Canon
scan and in the phone photo; the other three o's of that printing and the
body printing's "love" are clean rings. Designer's mark or knock-out
rasterisation accident cannot be decided at 200-215 dpi. Readings a
typewriter-style overstrike supports: delete the letter, substitute 0 / e /
o-slash / theta, mark the word, mark the letter position (word 4, letter 2;
the quote's 14th letter), remove every o, and the four-line layout of the
scribble printing itself. Sent through the full stack (7 hashes, 5 seeds x 72
paths, 25 scripts). Prior: low; cost: none.
"""
Q = "The economy of love is infinitely more efficient than hate and war."
LINES4 = ["The economy of", "love is infinitely", "more efficient than", "hate and war."]

def _variants(base):
    v = {}
    v["quote"] = base
    v["del"] = base.replace("love", "lve"); v["sub0"] = base.replace("love", "l0ve"); v["sube"] = base.replace("love", "leve")
    v["subO"] = base.replace("love", "lOve"); v["slash"] = base.replace("love", "løve"); v["theta"] = base.replace("love", "lθve")
    v["strike"] = base.replace("love", "l̶o̶ve".replace("̶o̶", "o̶")); v["dash"] = base.replace("love", "l-ve")
    v["allo_del"] = base.replace("o", ""); v["allo_0"] = base.replace("o", "0"); v["allo_slash"] = base.replace("o", "ø")
    v["love_only"] = "love"; v["lve"] = "lve"; v["l0ve"] = "l0ve"; v["leve"] = "leve"; v["lOve"] = "lOve"; v["love_slash"] = "løve"
    v["loeve"] = "loeve"; v["lo-ve"] = "lo-ve"; v["ove"] = "ove"; v["lv"] = "lv"
    v["marked_o"] = "o"; v["word4"] = "4"; v["w4l2"] = "42"; v["w4l2sp"] = "4 2"; v["letter14"] = "14"; v["o_is_15"] = "15"
    v["love14"] = "love 14"; v["love42"] = "love 4 2"; v["love15"] = "love 15"
    v["nolove"] = base.replace("love ", "").replace("love", "")
    v["upto_love"] = "The economy of love"; v["from_love"] = "love is infinitely more efficient than hate and war."
    v["lines4"] = "\n".join(LINES4); v["lines4_sp"] = " / ".join(LINES4)
    for i, l in enumerate(LINES4): v[f"line{i}"] = l
    v["frame"] = "X FUCK ALL X"; v["frame_quote"] = "X FUCK ALL X " + base; v["quote_frame"] = base + " X FUCK ALL X"
    v["fuck_all"] = "FUCK ALL"; v["fuckall_love"] = "FUCK ALL love"
    return v

def forms():
    out = []
    for k, s in _variants(Q).items():
        for suf, t in (("", s), ("/lower", s.lower()), ("/upper", s.upper()), ("/nopunct", "".join(c for c in s if c.isalnum() or c.isspace())),
                       ("/nospace", "".join(s.split())), ("/nospace_lower", "".join(s.split()).lower())):
            out.append((k + suf, t))
    seen, uniq = set(), []
    for t, v in out:
        if v and v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); d = dict(F); tags = [t for t, _ in F]
    return len(set(tags)) == len(tags) and d.get("del") == "The economy of lve is infinitely more efficient than hate and war." and d.get("sub0", "").count("l0ve") == 1

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
