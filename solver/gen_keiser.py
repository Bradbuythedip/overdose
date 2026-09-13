#!/usr/bin/env python3
"""
A Max Keiser biographical / rhetorical corpus, built from research.

Every corpus in this repo so far was drawn from the ARTICLE. But a
puzzle-setter picking a memorable passphrase is at least as likely to reach for
something personal as for a line of his own column -- and Keiser's Dec 2022
tweet says he hid keys "in the text" of his column plural, across issues, which
suggests a reusable personal key rather than one derived per-article.

Facts sourced by search (see window/keiser_research.md for provenance):
  full name        Timothy Maxwell Keiser
  born             23 January 1960, New Rochelle, New York
  wife             Stacy Herbert, runs El Salvador's Bitcoin Office
  Hollywood Stock Exchange, co-founded 1998, sold to Cantor Fitzgerald 2001
  Karmabanque; Keiser Report on RT, Sept 2009 - Feb 2022
  buying bitcoin since 2011; senior bitcoin adviser to Nayib Bukele

  python3 gen_keiser.py --out /tmp/keiser.txt
"""
import argparse, itertools, re, sys

NAMES = [
    "Timothy Maxwell Keiser", "Timothy Keiser", "Maxwell Keiser", "Max Keiser",
    "MaxKeiser", "maxkeiser", "Max", "Keiser", "Tim Keiser",
    "Stacy Herbert", "StacyHerbert", "Max and Stacy", "Max & Stacy",
    "Max Keiser Stacy Herbert", "Stacy", "Herbert",
]

WORKS = [
    "Keiser Report", "KeiserReport", "The Keiser Report",
    "Hollywood Stock Exchange", "HSX", "Karmabanque", "KarmaBanque",
    "Orange Pill", "The Orange Pill", "Orange Pill Podcast",
    "The Truth About Markets", "Resonance FM", "Russia Today", "RT",
    "StartCoin", "StartJOIN", "Bitcoin Capital", "Cantor Fitzgerald",
    "Overdose", "OVERDOSE", "Bitcoin Magazine", "El Salvador Issue",
]

PLACES = [
    "New Rochelle", "New Rochelle New York", "New York", "El Salvador",
    "San Salvador", "Bitcoin Beach", "El Zonte", "Volcano Bonds",
    "Volcano Energy", "Bitcoin Office", "Nayib Bukele", "Bukele",
]

SLOGANS = [
    "Buy silver crash JP Morgan", "Buy silver, crash JP Morgan",
    "crash JP Morgan buy silver", "We are all Satoshi", "we are all satoshi",
    "Genocidal loan sharks", "genocidal loan sharks",
    "Death to the dollar", "hyperbitcoinization", "Hyperbitcoinization",
    "Toxic Bitcoin Maximalist", "toxic maximalist",
    "Only put money in the banking system that you can afford to lose",
    "Gold is the currency of kings; silver is the currency of gentlemen; "
    "barter is the currency of peasants; but debt is the currency of slaves",
    "Bitcoin is the currency of resistance",
    "Did I mention how good it feels to be a bitcoin millionaire",
    "Bitcoin fixes this", "BITCOIN FIXES ALL THIS",
    # the Keiser Report's own on-air tagline
    "Markets! Finance! Scandal!", "Markets Finance Scandal",
    "Markets! Finance! Scandal", "markets finance scandal",
    # verified his, 2010-2012 campaign (cyber hornets is Saylor's, excluded)
    "Crash JP Morgan Buy Silver", "Crash JP Morgan, Buy Silver",
    "CRASH JP MORGAN BUY SILVER", "buysilvercrashjpmorgan",
]

DATES = [
    "23 January 1960", "January 23 1960", "January 23, 1960", "23/01/1960",
    "01/23/1960", "1960-01-23", "23011960", "01231960", "19600123",
    "230160", "012360", "600123", "1960", "1998", "2001", "2009", "2011",
    "2022", "2023",
]

NUMBERS = [
    "20", "20 BTC", "20BTC", "220000", "400000", "100000", "28000000",
    "2200000", "21000000", "1494",
]


def variants(s):
    s = s.strip()
    if not s:
        return []
    out = {s, s.lower(), s.upper(), s.title()}
    nop = re.sub(r"[^\w\s]", "", s)
    out |= {nop, nop.lower(), nop.upper()}
    tight = re.sub(r"\s+", "", s)
    out |= {tight, tight.lower(), tight.upper()}
    out.add(s[::-1])
    out.add(s.lower()[::-1])
    return [x for x in out if 3 <= len(x) <= 200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    base = set()
    for group in (NAMES, WORKS, PLACES, SLOGANS, DATES, NUMBERS):
        base.update(group)

    # name x date and name x number pairings -- the classic personal passphrase
    for n in NAMES:
        for d in DATES + NUMBERS:
            for sep in ("", " ", "-", "_"):
                base.add(n + sep + d)
                base.add(d + sep + n)
    # name x place
    for n in NAMES[:9]:
        for p in PLACES:
            base.add(n + " " + p)
            base.add(p + " " + n)

    out = set()
    for s in base:
        out.update(variants(s))
    out = {x for x in out if 3 <= len(x) <= 200}

    with open(a.out, "w", encoding="utf-8") as f:
        for p in sorted(out):
            f.write(p + "\n")
    sys.stderr.write(f"{len(base):,} base -> {len(out):,} Keiser phrases -> {a.out}\n")


if __name__ == "__main__":
    main()
