#!/usr/bin/env python3
"""
Think like the man, not like the text.

WHAT EVERY PASS HERE HAS ASSUMED
That the key is DERIVED from the article — hashed, ciphered, indexed out of
the printed words. Three sessions, ~150M derivations, nothing.

But Keiser is not a cryptographer, he is a broadcaster. "I have hidden private
keys in the text" is as easily read as "the text tells you what the passphrase
is" — and a passphrase a showman would actually remember is one of HIS OWN
lines, not a 7-gram of his prose.

THE GAP THIS CLOSES
`grep -ril "honey badger"` over every corpus in this repo returns nothing.
Max Keiser coined "Bitcoin is the honey badger of money". It is his most
quoted sentence. And the article contains the word **honey-badgering** —
"since I started honey-badgering him to buy some at $1 back in 2011" — which
is the text pointing directly at it. Same for the silver campaign he is
famous for, and for "Death to the Fed". None were ever tested.

So this is the persona corpus: his coinages, his campaigns, his shows, the
people and places he is bound to, and the article's own phrases crossed with
them. It is small — a few thousand strings — because that is the point. A
brainwallet is memorable or it is useless.

  python3 keiser_persona.py --selftest
  python3 keiser_persona.py --out keiser_persona.txt
"""
import argparse, itertools, sys

COINAGES = [
    "Bitcoin is the honey badger of money",
    "bitcoin is the honey badger of money",
    "the honey badger of money", "honey badger of money",
    "honey badger", "honeybadger", "Honey Badger", "HONEY BADGER",
    "Honey Badger of Money", "HONEY BADGER OF MONEY",
    "honey-badgering", "honeybadgering",
]
CAMPAIGNS = [
    "Buy silver, crash JP Morgan", "buy silver crash jp morgan",
    "Crash JP Morgan Buy Silver", "CRASH JP MORGAN, BUY SILVER",
    "crash jpmorgan", "buy silver", "Death to the Fed", "death to the fed",
    "DEATH TO THE FED", "Scammers gonna scam", "We are all Satoshi",
    "we're all Satoshi", "Stacking sats", "stack sats",
    "Gold and silver are money", "Bitcoin is a Trojan horse",
]
SHOWS = [
    "Keiser Report", "The Keiser Report", "KEISER REPORT",
    "Max Keiser", "MAX KEISER", "Max and Stacy", "Stacy Herbert",
    "Max Keiser and Stacy Herbert", "Orange Pill", "The Orange Pill",
    "ORANGEPILL", "orangepill", "Hollywood Stock Exchange",
    "Karmabanque", "Max Keiser Report",
]
PLACES = [
    "El Salvador", "el salvador", "EL SALVADOR", "El Zonte", "Bitcoin Beach",
    "Nayib Bukele", "Bukele", "volcano bonds", "Volcano Bond", "Chivo",
    "chivo wallet", "Bitcoin City", "Conchagua",
]
ARTICLE = [
    "Bitcoin Is Toxic AF", "BITCOIN IS TOXIC AF", "bitcoin is toxic af",
    "OVERDOSE", "Overdose", "overdose", "Toxic Bitcoin Maximalist",
    "Go Bitcoin Toxic Maximalist", "the love economy", "peace and love economy",
    "war and violence economy", "MAX KEISER", "MAX ♡ KEISER",
    "MAX HEART KEISER", "MAX LOVE KEISER", "right there in the Genesis Block",
    "The numbers don't lie", "BITCOIN FIXES ALL THIS", "Full Stop",
    "Keep your dignity", "Don't fall for shitcoinery",
]
JOINERS = ["", " ", "-", "_", ".", "20", "21", "2021", "20BTC", "20 BTC"]


def corpus(cross=True):
    base = COINAGES + CAMPAIGNS + SHOWS + PLACES + ARTICLE
    out = list(base)
    for s in base:
        out += [s.lower(), s.upper(), s.replace(" ", ""),
                s.lower().replace(" ", ""), s.replace(" ", "")[::-1]]
    if cross:
        # the clue names one of these explicitly; crossing it with the
        # coinages is the cheapest way to honour "El Salvador is a clue"
        for a, b in itertools.product(COINAGES[:6], PLACES[:6]):
            for j in JOINERS:
                out.append(a + j + b)
                out.append(b + j + a)
        for a in COINAGES[:6]:
            for j in JOINERS:
                out.append(a + j + "CL76841714A")
                out.append(a + j + "76841714")
    seen, uniq = set(), []
    for s in out:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def selftest():
    c = corpus()
    ok = True
    for must in ("Bitcoin is the honey badger of money", "honey badger",
                 "Buy silver, crash JP Morgan", "Death to the Fed"):
        good = must in c
        ok &= good
        sys.stderr.write(f"  {must!r:40} present: {'OK' if good else 'FAIL'}\n")
    ok &= len(c) > 500
    sys.stderr.write(f"  {len(c):,} distinct strings\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="keiser_persona.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not selftest():
        sys.exit("corpus is missing its own anchors; refusing")
    if a.selftest:
        return
    c = corpus()
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c):,} strings -> {a.out}\n")


if __name__ == "__main__":
    main()
