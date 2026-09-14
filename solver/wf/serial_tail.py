#!/usr/bin/env python3
"""
The page-72 serial with its OVERPRINTED digits treated as unknown.

WHY THIS WAS A GAP
KB46279860 is read off page 72's background banknote. At 1200 dpi rendered
straight from the PDF the first six characters -- K B 4 6 2 7 -- are
unambiguous. The last four sit UNDER the "In 2020," / "WESTERN UNION" display
type and were read through it. wf/mitm_split.py swept all 26 trailing LETTERS
of this serial but always held those four digits fixed, so a single misread
digit silently invalidated every derivation built on it.

Here the tail is enumerated instead of assumed: 10^4 tails x the forms a serial
is actually written in.

NOTE ON PROVENANCE (corrects window/page71.md): this banknote is NOT
show-through from page 71. Show-through is mirrored; page 73's OVERDOSE
headline appears on page 72 correctly mirrored, while this note's serial,
its seals and "THIS NOTE IS ... LEGAL TENDER" all read left-to-right. It is
printed artwork on page 72 itself.

  python3 wf/serial_tail.py --selftest
  python3 wf/serial_tail.py
"""
import hashlib, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from hd_sweep import CURVE_N

PREFIX_LETTERS = "KB"
KNOWN = "4627"          # confident digits
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def forms(tail):
    """The written forms of one candidate serial."""
    digits = KNOWN + tail
    body = PREFIX_LETTERS + digits
    out = [digits, body, body.lower()]
    for L in LETTERS:
        out.append(body + L)
    return out


def keys_for(phrase):
    """Brainwallet scalar, plus the raw integer reading for the bare digits."""
    yield hashlib.sha256(phrase.encode()).digest()


def selftest():
    ok = True
    n = len(forms("9860"))
    good = n == 29
    print(f"  29 forms per tail: {'OK' if good else 'FAIL'} ({n})")
    ok &= good
    good = "KB46279860" in forms("9860")
    print(f"  the read serial is covered: {'OK' if good else 'FAIL'}")
    ok &= good
    k = hashlib.sha256(b"correct horse battery staple").digest()
    a = H.addrs_for_priv(k)["p2pkh_u"]
    good = a == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    print(f"  derivation path: {'OK' if good else 'FAIL'} ({a})")
    ok &= good
    o = H.Oracle()
    good = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis:  {'OK' if good else 'FAIL'}")
    ok &= good
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")

    o = H.Oracle(use_full=False)
    from index_oracle import spk_from_address
    full = H.full_index()
    hits, n_keys, t0 = [], 0, time.time()
    PEND = []

    def flush(force=False):
        nonlocal n_keys
        if not PEND or (len(PEND) < 60000 and not force):
            return
        spks, meta = [], []
        for tag, k in PEND:
            for t, ad in H.addrs_for_priv(k).items():
                if o.funded(ad):
                    hits.append((tag, t, ad, k.hex()))
                    print(f"*** HIT(richlist) {tag} {t} {ad} {k.hex()}", flush=True)
                spk = spk_from_address(ad)
                if spk is not None:
                    spks.append(spk); meta.append((tag, t, ad, k))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, t, ad, k = meta[j]
                hits.append((tag, t, ad, k.hex(), bal))
                print(f"*** HIT(fullindex) {tag} {t} {ad} {bal/1e8:.8f} BTC "
                      f"{k.hex()}", flush=True)
        n_keys += len(PEND); PEND.clear()

    for i in range(10000):
        tail = f"{i:04d}"
        for ph in forms(tail):
            for k in keys_for(ph):
                if 0 < int.from_bytes(k, "big") < CURVE_N:
                    PEND.append((ph, k))
        flush()
    flush(force=True)

    print(f"\nkeys {n_keys:,} in {time.time()-t0:.0f}s, "
          f"addresses ~{n_keys*5:,}")
    print("serial-tail hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
