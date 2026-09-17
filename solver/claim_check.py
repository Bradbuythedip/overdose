#!/usr/bin/env python3
"""
Check a claimed prize address. Offline first; network only where it must be.

WHEN TO USE
The clue hunt's question #1 is "has Keiser ever shown the address?" If a
claimed address turns up -- in a tweet, a reply, a forum post, a screenshot --
this is the first thing to run on it, BEFORE anyone gets excited. It answers,
in order:

  1. Is it even a valid Bitcoin address, and of what script type?
     (a typo'd or fabricated address fails here; so does a testnet one)
  2. Is it reachable by ANY derivation this project already has? If a claimed
     address is sha256("some article phrase") we have the key and it is over;
     if it is not reachable by anything, the claim is at least not trivially
     a brainwallet -- consistent with a real hidden key.
  3. Does the offline 56M index show it funded today, and with what?
  4. (network) Has it EVER been funded, per everfunded.py's Esplora client,
     with the decoy/tip-jar classification applied?

Everything through step 3 runs offline. Step 4 needs --base.

  python3 claim_check.py --selftest
  python3 claim_check.py 1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t
  python3 claim_check.py ADDR --base https://blockstream.info/api
"""
import argparse, hashlib, os, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def script_type(addr):
    """('type', spk_bytes) or (None, reason)."""
    from index_oracle import spk_from_address
    spk = spk_from_address(addr)
    if spk is None:
        return None, "not a valid mainnet address (bad checksum, charset, or network)"
    if spk[:3] == b"\x76\xa9\x14":
        return "p2pkh", spk
    if spk[:2] == b"\xa9\x14":
        return "p2sh (p2sh-p2wpkh or script)", spk
    if spk[:2] == b"\x00\x14":
        return "p2wpkh", spk
    if spk[:2] == b"\x00\x20":
        return "p2wsh", spk
    if spk[:2] == b"\x51\x20":
        return "p2tr", spk
    return "other", spk


def reachable(spk, corpus_paths):
    """Is sha256(spk) produced by any phrase in the project's corpora?

    Direct hashes only here -- HD derivation over the full corpus is the job of
    target_sweep.py, which takes a scripthash list. This is the fast first
    pass: if the claimed address is a plain brainwallet of an article phrase,
    it shows up in seconds.
    """
    from hd_sweep import direct_keys
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    target = hashlib.sha256(spk).digest()
    seen = 0
    for path in corpus_paths:
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8", errors="ignore"):
            p = line.rstrip("\n")
            if not p:
                continue
            seen += 1
            for hname, k in direct_keys(p).items():
                if not (0 < int.from_bytes(k, "big") < CURVE_N):
                    continue
                for st, s in list(spks_for_key(k)) + list(spks_extra(k)):
                    if hashlib.sha256(s).digest() == target:
                        return True, f"{path}: {p[:60]!r} via {hname}/{st}", seen
    return False, "", seen


def offline_balance(spk):
    import continuous_solver as CS
    o = CS.IndexOracle()
    if not o.ready:
        return None, o.why
    hits = o.check([spk])
    return (hits[0][1] if hits else 0), ""


def selftest():
    ok = True
    t, spk = script_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    ok &= t == "p2pkh"
    sys.stderr.write(f"  genesis address parses as {t}: {'OK' if t=='p2pkh' else 'FAIL'}\n")
    t2, why = script_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb")
    ok &= t2 is None
    sys.stderr.write(f"  one-character corruption is rejected: "
                     f"{'OK' if t2 is None else 'FAIL'}\n")
    t3, _ = script_type("bc1pmd7qtkz3hmsw7zcvd2l8dqf4eml7u06l7ark09882ucf8slf9j3s4qmn5f")
    ok &= t3 == "p2tr"
    sys.stderr.write(f"  a taproot address parses as {t3}: {'OK' if t3=='p2tr' else 'FAIL'}\n")
    # reachability must FIND a planted brainwallet and NOT find a random one
    import tempfile
    from hd_sweep import direct_keys
    from full_sweep import spks_for_key
    k = direct_keys("claim check plant")["sha256"]
    spk = dict(spks_for_key(k))["p2pkh_c"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("unrelated line\nclaim check plant\n")
        p = f.name
    found, how, _n = reachable(spk, [p])
    ok &= found
    sys.stderr.write(f"  a planted brainwallet address is found reachable: "
                     f"{'OK' if found else 'FAIL'}\n")
    _t, gspk = script_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    found2, _h, _n = reachable(gspk, [p])
    ok &= not found2
    sys.stderr.write(f"  the genesis address is NOT reachable from that corpus: "
                     f"{'OK' if not found2 else 'FAIL'}\n")
    os.unlink(p)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addresses", nargs="*")
    ap.add_argument("--corpus", action="append",
                    default=["article_transcript.txt", "candidates_v2.txt",
                             "furniture.txt", "p72.txt", "composite.txt"],
                    help="phrase files to test reachability against")
    ap.add_argument("--base", default=os.environ.get("ESPLORA", ""),
                    help="Esplora base for the ever-funded check (network)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("address handling is wrong; refusing")
    if a.selftest or not a.addresses:
        return

    for addr in a.addresses:
        print(f"\n== {addr}")
        t, spk = script_type(addr)
        if t is None:
            print(f"   INVALID: {spk}")
            continue
        print(f"   script type      : {t}")
        found, how, n = reachable(spk, a.corpus)
        print(f"   reachable offline: {'YES -- ' + how if found else f'no (checked {n:,} phrases, direct hashes)'}")
        bal, why = offline_balance(spk)
        if bal is None:
            print(f"   offline index    : unavailable ({why})")
        else:
            print(f"   offline index    : {'funded, ' + str(bal) + ' sats' if bal else 'not in the 56M funded set (snapshot 2025-10-11)'}")
        if a.base:
            try:
                import everfunded as EF, decoys
                api = EF.Esplora(a.base) if hasattr(EF, "Esplora") else None
                if api is None:
                    raise RuntimeError("everfunded client not importable here")
                fc, fs, bal2 = api.stats(addr)
                d, why2 = decoys.classify_everfunded(addr, fc, fs, bal2)
                print(f"   ever funded      : {fc} deposits, {fs/1e8:.8f} BTC received, "
                      f"{bal2/1e8:.8f} BTC now  {'[decoy: ' + why2 + ']' if d else ''}")
            except Exception as e:
                print(f"   ever funded      : could not query ({e})")
        else:
            print(f"   ever funded      : (pass --base to ask a live endpoint)")
        if found:
            print("   VERDICT: this address is a plain brainwallet of a known phrase. "
                  "If it is the claimed prize, the key is that phrase -- verify "
                  "its history by hand before anything else.")


if __name__ == "__main__":
    main()
