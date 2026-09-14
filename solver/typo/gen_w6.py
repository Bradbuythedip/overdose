#!/usr/bin/env python3
"""Wave 6: the repeated sentence as a remembered catchphrase -- the natural
misquotes and fragments someone would type from memory -- crossed with the
set-apart caps blocks."""
import re, sys, itertools
A1, A3, A4, A5 = "BITCOIN IS TOXIC AF", "BITCOIN FIXES ALL THIS", "MAX KEISER", "OVERDOSE"
def ns(s): return re.sub(r"\s+", "", s)
out = []
def add(*ss):
    for s in ss:
        if s and s.strip() and len(s) < 3900: out.append(s)

VARIANTS = [
 "The economy of love is infinitely more efficient than hate and war.",
 "The economy of love is infinitely more efficient than hate and war",
 "The economy of love is infinitely more efficient than the economy of hate and war.",
 "The economy of love is infinitely more efficient than war and hate.",
 "The economy of love is infinitely more efficient than hate and war!",
 "An economy of love is infinitely more efficient than hate and war.",
 "Economy of love is infinitely more efficient than hate and war.",
 "The economy of love is infinitely more efficient than hate and war. Max Keiser",
 "The economy of love is more efficient than hate and war.",
 "The economy of love is infinitely more efficient.",
 "Love is infinitely more efficient than hate and war.",
 "The economy of love",
 "economy of love",
 "the economy of love is infinitely more efficient than hate and war",
 "THE ECONOMY OF LOVE IS INFINITELY MORE EFFICIENT THAN HATE AND WAR",
 "infinitely more efficient than hate and war",
 "more efficient than hate and war",
 "than hate and war",
 "hate and war",
 "love and peace", "peace and love", "loveandpeace", "peaceandlove",
 "The economy of love is infinitely more efficient than hate and war. "
 "The economy of love is infinitely more efficient than hate and war.",
]
for v in VARIANTS:
    for f in (lambda s: s, str.lower, str.upper, str.title):
        t = f(v)
        add(t, ns(t), re.sub(r"[^\w\s]", "", t).strip(),
            ns(re.sub(r"[^\w\s]", "", t)))
    add(v[::-1], v.lower()[::-1], ns(v).lower()[::-1])
    add("_".join(w.lower() for w in re.findall(r"[A-Za-z0-9]+", v)))
    add("-".join(w.lower() for w in re.findall(r"[A-Za-z0-9]+", v)))
    for b in (A1, A3, A4, A5, "Bitcoin", "bitcoin", "BITCOIN", "Satoshi",
              "El Salvador", "elsalvador", "Bukele", "20 BTC", "20BTC"):
        for j in ("", " ", "-", "_", " | ", ". "):
            add(v + j + b, b + j + v)
            add((v + j + b).lower(), (b + j + v).lower())
            add(ns(v + j + b).lower(), ns(b + j + v).lower())
seen, u = set(), []
for s in out:
    if s not in seen:
        seen.add(s); u.append(s)
sys.stdout.write("\n".join(u) + "\n")
sys.stderr.write(f"wave6: {len(u)}\n")
