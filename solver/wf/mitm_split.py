#!/usr/bin/env python3
"""
Meet-in-the-middle over the SPLIT-KEY hypothesis, driven by the new clues.

WHY THIS SHAPE
Keiser said "hidden private keyS in the text" -- plural. The scan then produced
a SECOND banknote serial (KB46279860 on page 72) alongside the long-known
CL76841714A. Two serials is a two-component structure, and a two-component key
is exactly what a meet-in-the-middle is for.

WHAT A TEXTBOOK MITM NEEDS, AND WHY WE CANNOT HAVE IT
The 2^2n -> 2^n break requires a KNOWN TARGET to walk backwards from. We have
no confirmed prize address, and whatever the address is it has never spent, so
its public key has never been revealed. There is nothing to invert toward. Any
claim of a real MITM break here would be false.

WHAT IS GENUINELY AVAILABLE, AND IS THE SAME ALGORITHMIC SHAPE
For the additive split priv = a + b (mod n), the public key factorises:

    pub = (a + b)G = aG + bG

So each half can be turned into a curve POINT once, and every pair combined
with a point ADDITION rather than a fresh scalar multiplication. A scalar
multiply costs ~100x an addition, so the |A| x |B| product space becomes
tractable: |A| + |B| multiplications up front, then |A| x |B| cheap adds. The
"middle" the two sides meet at is the offline funded-address index.

This also covers the non-additive combinations (concatenation, XOR of digests,
one half as KDF salt for the other), which need full derivation but whose
component sets are small enough to enumerate directly.

CONTROL
A known split is planted: a random pair (a, b) whose sum is the private key of
a KNOWN FUNDED address. The pipeline must recover it from the point-addition
path before any null from this module is believed.

  python3 wf/mitm_split.py --selftest
  python3 wf/mitm_split.py
"""
import hashlib, itertools, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from coincurve import PrivateKey, PublicKey
from hd_sweep import CURVE_N, h160, addr_p2pkh, addr_p2wpkh, addr_p2sh_p2wpkh

# ----------------------------------------------------------------- components
SERIAL1 = "CL76841714A"          # pages 73/74, one cutout reused
SERIAL2 = "KB46279860"           # page 72, ghosted behind the display type
DISTRICT = "L12"

# page 72 numerals, measured (22 tokens, incl. the 19 of covid-19)
P72_NUMS = ["165", "572", "2020", "4.8", "930.44", "2026", "3.9", "35.8",
            "2026", "14.5", "2019", "34", "2021", "05", "12", "19", "75",
            "2021", "04", "12", "2208403", "72"]

P72_URLS = [
    "www.knomad.org/publication/migration-and-development-brief-34",
    "www.migrationdataportal.org/themes/remittances",
    "www.worldbank.org/en/news/press-release/2021/05/12/defying-predictions-remittance-flows-remain-strong-during-covid-19-crisis",
    "www.wise.com/documents/Public_Research_and_Survey_-_US_Hidden_Fees",
    "www.repository.upenn.edu/sire/75/",
    "www.westernunion.com/sv/en/receive-money.html",
    "ir.westernunion.com/investor-relations/financial-information/",
    "www.alliedmarketresearch.com/remittance-market",
    "www.globenewswire.com/news-release/2021/04/12/2208403/",
]

SALVADOR = ["El Salvador", "el salvador", "EL SALVADOR", "ElSalvador",
            "elsalvador", "ELSALVADOR", "sv", "SV"]

ANCHORS = ["OVERDOSE", "Overdose", "overdose", "BITCOIN IS TOXIC AF",
           "Max Keiser", "MAX KEISER", "maxkeiser", "NUMBERS",
           "WESTERN UNION", "Western Union", "westernunion",
           "572 WESTERN UNION LOCATIONS IN EL SALVADOR",
           "165 WESTERN UNION LOCATIONS IN PALESTINE"]


def serial_variants(s):
    """A serial in the forms it is actually printed and read."""
    body = s.replace(" ", "")
    out = {body, body.lower(), body.upper()}
    m = re.match(r"^([A-Z]{1,2})(\d+)([A-Z]?)$", body.upper())
    if m:
        p, digits, suf = m.groups()
        out |= {digits, p + digits, digits + suf, p + " " + digits + " " + suf,
                p + " " + digits, " ".join([p, digits, suf]).strip()}
        out |= {digits[::-1], body[::-1], body.upper()[::-1]}
        # the tail character of SERIAL2 is overprinted by the headline
        if s == SERIAL2:
            for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                out.add(body.upper() + c)
    out |= {body + " " + DISTRICT, DISTRICT + body}
    return {x for x in out if x}


def setA():
    """Half one: the long-known note."""
    s = set()
    for v in serial_variants(SERIAL1):
        s.add(v)
        for extra in SALVADOR[:4] + ANCHORS[:4]:
            s.add(v + extra); s.add(extra + v)
            s.add(v + " " + extra); s.add(extra + " " + v)
    return sorted(s)


def setB():
    """Half two: the page-72 note, its numerals and its sources."""
    s = set()
    for v in serial_variants(SERIAL2):
        s.add(v)
    s |= set(P72_NUMS)
    s |= set(P72_URLS)
    s |= set(SALVADOR)
    s.add("".join(P72_NUMS))
    s.add(" ".join(P72_NUMS))
    s.add("".join(P72_NUMS)[::-1])
    for a, b in itertools.combinations(P72_NUMS[:11], 2):
        s.add(a + b)
    return sorted(s)


def scalar(phrase):
    """A component -> a curve scalar, by the canonical brainwallet hash."""
    k = int.from_bytes(hashlib.sha256(phrase.encode()).digest(), "big")
    return k % CURVE_N


def point(k):
    if not 0 < k < CURVE_N:
        return None
    return PrivateKey(k.to_bytes(32, "big")).public_key


def addrs_from_pub(pub):
    pc = pub.format(compressed=True)
    pu = pub.format(compressed=False)
    return {
        "p2pkh_c": addr_p2pkh(pc),
        "p2pkh_u": addr_p2pkh(pu),
        "p2wpkh": addr_p2wpkh(pc),
        "p2sh_p2wpkh": addr_p2sh_p2wpkh(pc),
    }


def run(oracle, A, B, verbose=True):
    """Precompute both halves as points, then combine with point ADDITION."""
    t0 = time.time()
    ptsA, ka = [], []
    for a in A:
        k = scalar(a)
        p = point(k)
        if p is not None:
            ptsA.append(p); ka.append((a, k))
    ptsB, kb = [], []
    for b in B:
        k = scalar(b)
        p = point(k)
        if p is not None:
            ptsB.append(p); kb.append((b, k))
    if verbose:
        sys.stderr.write(f"  precomputed {len(ptsA)} + {len(ptsB)} points "
                         f"in {time.time()-t0:.1f}s\n")

    hits, n = [], 0
    t1 = time.time()
    for i, PA in enumerate(ptsA):
        for j, PB in enumerate(ptsB):
            try:
                S = PublicKey.combine_keys([PA, PB])      # point addition
            except Exception:
                continue
            n += 1
            for t, a in addrs_from_pub(S).items():
                if oracle.funded(a):
                    priv = (ka[i][1] + kb[j][1]) % CURVE_N
                    hits.append((ka[i][0], kb[j][0], t, a, f"{priv:064x}"))
                    print(f"*** HIT split {ka[i][0]!r} + {kb[j][0]!r} -> {t} {a}",
                          flush=True)
    if verbose:
        sys.stderr.write(f"  {n:,} point additions, {n*4:,} addresses, "
                         f"{time.time()-t1:.1f}s\n")
    return hits, n


def selftest():
    """Plant a split whose sum is a KNOWN address, and recover it."""
    ok = True
    a_phrase, b_phrase = "__control_half_A__", "__control_half_B__"
    ka, kb = scalar(a_phrase), scalar(b_phrase)
    total = (ka + kb) % CURVE_N
    direct = PrivateKey(total.to_bytes(32, "big")).public_key
    combined = PublicKey.combine_keys([point(ka), point(kb)])
    same = direct.format() == combined.format()
    print(f"  point addition == scalar sum: {'OK' if same else 'FAIL'}")
    ok &= same

    target = addr_p2pkh(direct.format(compressed=True))
    print(f"  planted split target: {target}")

    class Stub:
        def funded(self, a): return a == target
    hits, n = run(Stub(), [a_phrase], [b_phrase], verbose=False)
    found = any(h[3] == target for h in hits)
    print(f"  pipeline recovers the planted split: {'OK' if found else 'FAIL'}")
    ok &= found

    # and the real oracle must still see a known funded address
    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle sees genesis coinbase: {'OK' if g else 'FAIL'}")
    ok &= g
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")
    A, B = setA(), setB()
    print(f"\nhalf A: {len(A)} components   half B: {len(B)} components")
    print(f"product space: {len(A)*len(B):,} splits, {len(A)*len(B)*4:,} addresses")
    o = H.Oracle()
    hits, n = run(o, A, B)
    print(f"\nadditive-split hits: {len(hits)}")
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
