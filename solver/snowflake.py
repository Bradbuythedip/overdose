#!/usr/bin/env python3
"""
Date a tweet from its ID. Offline. The clue-hunt rule of evidence.

WHY
Every timing argument about this puzzle has at some point been wrong by
mis-dating a tweet from an article dateline or a screenshot. A tweet's
snowflake ID carries its creation time exactly:

    timestamp_ms = (id >> 22) + 1288834974657

No network, no API, no ambiguity. `SOLVE_PROMPT.md` and `CLUE_HUNT_PROMPT.md`
both require dates derived this way; this is the tool that does it, and it
ships with the five load-bearing tweets so the table in those prompts can be
re-verified by anyone in one command.

  python3 snowflake.py                       # verify the five known tweets
  python3 snowflake.py 1607378060172460032   # date any ID
  python3 snowflake.py --selftest
"""
import argparse, datetime, sys

EPOCH_MS = 1288834974657          # Twitter snowflake epoch, 2010-11-04

# (id, what it is, date the prompts claim) -- the claim is CHECKED, not trusted
KNOWN = [
    (1492173067723886594, "Bukele photographed holding the printed issue", "2022-02-11"),
    (1607378060172460032, "'Like George Sand's hidden cryptography, I have hidden private keys in the text'", "2022-12-26"),
    (1632068898169450497, "'Nobody's figured it out yet, but it's for 20 BTC'", "2023-03-04"),
    (1632391507008278528, "mirror writing, links PMC2117809", "2023-03-05"),
    (1741134493769965603, "'Obviously, El Salvador is a clue.'", "2023-12-30"),
]


def when(snowflake_id):
    ms = (int(snowflake_id) >> 22) + EPOCH_MS
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc)


def selftest():
    ok = True
    # the epoch itself: an ID of 0 is the epoch
    t0 = when(0)
    good = t0.strftime("%Y-%m-%d") == "2010-11-04"
    ok &= good
    sys.stderr.write(f"  id 0 -> {t0:%Y-%m-%d %H:%M:%S} UTC (epoch): "
                     f"{'OK' if good else 'FAIL'}\n")
    # a well-known public tweet: Twitter's first snowflake-era tweets are
    # late 2010; anything decoding outside 2006-2040 is a parse error
    for sid, what, claimed in KNOWN:
        d = when(sid)
        good = d.strftime("%Y-%m-%d") == claimed
        ok &= good
        sys.stderr.write(f"  {sid}  {d:%Y-%m-%d %H:%M} UTC  "
                         f"{'OK' if good else 'MISMATCH vs ' + claimed}\n"
                         f"      {what}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="tweet IDs to date")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.ids:
        sys.stderr.write("\n  SELFTEST (the five load-bearing tweets)\n")
        sys.exit(0 if selftest() else 1)
    for s in a.ids:
        try:
            d = when(s)
        except ValueError:
            print(f"{s}\tNOT AN INTEGER")
            continue
        print(f"{s}\t{d:%Y-%m-%d %H:%M:%S} UTC")


if __name__ == "__main__":
    main()
