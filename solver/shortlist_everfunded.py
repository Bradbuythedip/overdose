#!/usr/bin/env python3
"""
The highest-prior candidates, as ADDRESSES, for the ever-funded question.

WHY THIS EXISTS
Every null in this project is ambiguous. `hist_index.py` states it exactly:
"the two oracles are two instants, not an interval." `address_map.bin` answers
"holds coins today"; the rich list answers "held a large balance in April
2023". Neither answers "was ever funded", so a null cannot distinguish

    the derivation is wrong
    the derivation is RIGHT and the address was never funded, or was swept
    before both snapshots

and the second is the most likely history for a magazine-printed key.

`everfunded.py` resolves it against an Esplora endpoint, verified by its own
live control: sha256("correct horse battery staple") received 15.9472 BTC and
holds 0 — invisible to both offline indices. It needs one HTTP call per
address, so it cannot run across 150M candidates. It can run across a few
thousand.

WHAT GOES IN
Only strings a person would actually choose. Not n-grams, not edit-neighbours,
not machine-generated permutations — those exist because they are cheap
offline, and they are exactly what should NOT consume a rate-limited endpoint.

  the article's quotable lines: the pull-quote printed three times, the
    headline, the sign-off, the highlighted runs
  Keiser's own coinages
  both banknote serials and the district code
  the cover strings and the page-72 display type
  the composite per-page assemblies

through the five standard script forms each.

  python3 shortlist_everfunded.py --selftest
  python3 shortlist_everfunded.py --out everfunded_shortlist.txt
"""
import argparse, hashlib, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

QUOTABLE = [
    "The economy of love is infinitely more efficient than hate and war.",
    "The economy of love is infinitely more efficient than hate and war",
    "BITCOIN IS TOXIC AF", "Bitcoin is toxic AF",
    "BITCOIN FIXES ALL THIS",
    "Go Bitcoin Toxic Maximalist", "Keep your dignity.",
    "Don't fall for shitcoinery.",
    "toxicity is Layer 1 of the protocol", "Layer 1",
    "the Layer 1 of the whole Satoshi experience",
    "right there in the Genesis Block",
    "It's the freaking UTXO ghetto up in here, y'all.",
    "A monetary defibrillator to the treasure chest.",
    "It's a stun gun to the genitals.",
    "We've seen some shit.", "the agony and ecstasy",
    "Everyone will live their own experience in the rabbit hole.",
    "We are getting our souls back and our minds.",
    "Stacy and I have been living in here for 10 years.",
    "MAX KEISER", "Max Keiser", "OVERDOSE", "Overdose",
    "with Max Keiser", "THE EL SALVADOR ISSUE", "El Salvador",
    "FUCK ALL", "X FUCK ALL X", "@ANNABELLEBAZ",
    "CL76841714A", "76841714", "KB46279860", "46279860", "L12",
    "074820403884", "Display Until Feb 23, 2022",
    "165 WESTERN UNION LOCATIONS IN PALESTINE",
    "572 WESTERN UNION LOCATIONS IN EL SALVADOR",
]


def forms(p):
    yield p
    yield p.upper()
    yield p.lower()
    yield p.replace(" ", "")
    yield p.rstrip(".")


def addresses(phrases):
    """(address, label) for the five standard script forms of each phrase."""
    from hd_sweep import direct_keys
    from full_sweep import spks_for_key
    import index_oracle as IO
    out = []
    want = ("p2pkh_c", "p2pkh_u", "p2wpkh", "p2sh_p2wpkh", "p2tr")
    for p in phrases:
        for hname, k in direct_keys(p).items():
            if not (0 < int.from_bytes(k, "big") < CURVE_N):
                continue
            for st, spk in spks_for_key(k):
                if st not in want:
                    continue
                a = spk_to_addr(spk)
                if a:
                    out.append((a, f"{p[:44]}|{hname}|{st}"))
    return out


def spk_to_addr(spk):
    """scriptPubKey -> address. Inverse of index_oracle.spk_from_address."""
    B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def b58c(payload):
        d = payload + hashlib.sha256(
            hashlib.sha256(payload).digest()).digest()[:4]
        n = int.from_bytes(d, "big")
        s = ""
        while n:
            n, r = divmod(n, 58)
            s = B58[r] + s
        return "1" * (len(d) - len(d.lstrip(b"\x00"))) + s

    if len(spk) == 25 and spk[:3] == b"\x76\xa9\x14":
        return b58c(b"\x00" + spk[3:23])
    if len(spk) == 23 and spk[:2] == b"\xa9\x14":
        return b58c(b"\x05" + spk[2:22])
    if len(spk) in (22, 34) and spk[0] in (0x00, 0x51):
        import index_oracle as IO
        return _bech32(0 if spk[0] == 0x00 else 1, spk[2:])
    return None


def _bech32(witver, prog):
    CH = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    from index_oracle import _bech32_polymod, _hrp_expand, _convertbits
    data = [witver] + _convertbits(list(prog), 8, 5)
    const = 1 if witver == 0 else 0x2BC830A3
    pm = _bech32_polymod(_hrp_expand("bc") + data + [0] * 6) ^ const
    chk = [(pm >> 5 * (5 - i)) & 31 for i in range(6)]
    return "bc1" + "".join(CH[d] for d in data + chk)


def selftest():
    ok = True
    # the round trip must hold, or every address below is wrong
    from index_oracle import spk_from_address
    for a in ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
              "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r",
              "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"):
        spk = spk_from_address(a)
        back = spk_to_addr(spk)
        good = back == a
        ok &= good
        sys.stderr.write(f"  {a[:26]:26} round-trips: "
                         f"{'OK' if good else 'FAIL -> ' + str(back)}\n")
    n = len(list(forms("x")))
    sys.stderr.write(f"  {len(QUOTABLE)} quotable strings x {n} forms\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="everfunded_shortlist.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("address encoding is wrong; every address would be wrong")
    if a.selftest:
        return

    ph = sorted({f for p in QUOTABLE for f in forms(p) if f})
    addrs = addresses(ph)
    seen, rows = set(), []
    for ad, lab in addrs:
        if ad not in seen:
            seen.add(ad)
            rows.append((ad, lab))
    with open(a.out, "w", encoding="utf-8") as fh:
        for ad, _l in rows:
            fh.write(ad + "\n")
    with open(a.out + ".labels", "w", encoding="utf-8") as fh:
        for ad, lab in rows:
            fh.write(f"{ad}\t{lab}\n")
    sys.stderr.write(f"\n  {len(ph)} phrase forms -> {len(rows):,} distinct "
                     f"addresses -> {a.out}\n"
                     f"  labels -> {a.out}.labels\n\n"
                     f"  next, ON A MACHINE WITH NETWORK:\n"
                     f"    python3 everfunded.py --addresses {a.out} "
                     f"--base https://blockstream.info/api\n")


if __name__ == "__main__":
    main()
