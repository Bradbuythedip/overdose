#!/usr/bin/env python3
"""
Max Keiser's X/Twitter numeric user ID, tested as key material.

THE IDEA
"How to contact Keiser on X" isn't a phrase in the article -- it's a lookup
the reader has to do, like the banknote's serial-as-catalogue-number idea. The
number itself is public, permanent, and specific to him: X account creation
predates Snowflake IDs (introduced late 2010), so pre-2010 accounts like his
(created 2009-02-08) got small sequential integers rather than the ~19-digit
Snowflake IDs everyone gets today. His is 8 digits, verified independently
twice, and roughly consistent with Twitter's user-count growth curve at that
date -- a plausible sanity check, not proof, since a spoofed number would look
the same.

    @maxkeiser numeric user ID: 20374262

Never in article_transcript.txt or any existing candidate corpus. Genuinely
untested.

WHAT IS SWEPT
Every form the two banknote serials were tested in: plain, reversed, as hex,
crossed with the article's anchors and with both serials, plus the handle
itself and its creation date.

  python3 twitter_id.py --selftest
  python3 twitter_id.py --out twitterid.txt
"""
import argparse, itertools, sys

XID = "20374262"
HANDLE = "maxkeiser"
CREATED = "20090208"          # 2009-02-08, verified via two independent lookups

SERIAL1, S1D = "CL76841714A", "76841714"
SERIAL2, S2D = "KB46279860", "46279860"


def variants(s):
    out = {s, s.upper(), s.lower(), s[::-1], "@" + s}
    return {x for x in out if x}


def build():
    out = set()
    for base in (XID, HANDLE, CREATED, "@" + HANDLE, HANDLE + XID,
                 XID + HANDLE, "maxkeiser " + XID, XID + " maxkeiser"):
        out |= variants(base)
        out.add(base.replace(" ", ""))
    # as hex / as an integer transform
    n = int(XID)
    out.add(format(n, "x"))
    out.add(format(n, "X"))
    out.add(str(n)[::-1])
    # crossed with the article's own anchors
    for a in ("OVERDOSE", "Max Keiser", "El Salvador", "20 BTC",
              "Bitcoin Magazine"):
        out.add(f"{a} {XID}")
        out.add(f"{XID} {a}")
        out.add(f"{a}{XID}")
    # crossed with both banknote serials, since all three are "look this up"
    # numbers tied to the puzzle
    for tag in (SERIAL1, S1D, SERIAL2, S2D):
        out.add(f"{XID} {tag}")
        out.add(f"{tag} {XID}")
        out.add(f"{XID}{tag}")
        out.add(f"{tag}{XID}")
        out.add(str(abs(int(tag) - n)) if tag.isdigit() else "")
        out.add(str(int(tag) + n) if tag.isdigit() else "")
    return sorted(x for x in out if 0 < len(x) < 200)


def selftest():
    ok = True
    ok &= XID.isdigit() and len(XID) == 8
    sys.stderr.write(f"  @{HANDLE} numeric ID {XID}: 8 digits "
                     f"{'OK' if len(XID)==8 else 'FAIL'}\n")
    ok &= XID not in (S1D, S2D)
    sys.stderr.write(f"  distinct from both banknote serials: "
                     f"{'OK' if XID not in (S1D,S2D) else 'FAIL'}\n")
    import os
    seen = [f for f in ("article_transcript.txt",)
            if os.path.exists(f) and XID in open(f, encoding="utf-8",
                                                 errors="ignore").read()]
    ok &= not seen
    sys.stderr.write(f"  absent from the article transcript: "
                     f"{'OK' if not seen else 'FAIL'}\n")
    c = build()
    ok &= len(c) > 20
    sys.stderr.write(f"  {len(c)} candidates\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="twitterid.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("bad setup; refusing")
    if a.selftest:
        return
    c = build()
    open(a.out, "w", encoding="utf-8").write("\n".join(c) + "\n")
    sys.stderr.write(f"\n  {len(c)} candidates -> {a.out}\n"
                     f"  next: python3 try_phrases.py --in {a.out} "
                     f"--label xid\n")


if __name__ == "__main__":
    main()
