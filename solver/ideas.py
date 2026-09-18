#!/usr/bin/env python3
"""
Test YOUR OWN ideas against the chain: phrases -> addresses -> "was it ever funded".

The offline indices are two snapshots; a key that was funded and swept between
them is invisible to both. everfunded.py asks a live endpoint the right
question, but it needs an address list. This builds one from any phrase file
(one idea per line): 5 case/spacing forms x 7 direct hashes x 5 script types,
plus, with --hd, the BIP-39 and Electrum seeds of each phrase at the wallet
paths people actually use. Then run everfunded on the output (run.sh does both).

  ./run.sh ideas my_ideas.txt          # phrases -> addresses -> ever-funded
  python3 ideas.py --phrases f.txt --out addrs.txt [--hd]
"""
import argparse, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
HD_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0", "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0",
            "m/0/0", "m/0'/0/0", "m/44'/0'/0'/0/1", "m/84'/0'/0'/0/1"]

def build(phrases, hd=False):
    from shortlist_everfunded import forms, spk_to_addr
    from hd_sweep import direct_keys, seeds_from, derive
    from full_sweep import spks_for_key
    want = ("p2pkh_c", "p2pkh_u", "p2wpkh", "p2sh_p2wpkh", "p2tr")
    out, seen = [], set()
    def emit(k, label):
        if not (0 < int.from_bytes(k, "big") < CURVE_N): return
        for st, spk in spks_for_key(k):
            if st not in want: continue
            a = spk_to_addr(spk)
            if a and a not in seen:
                seen.add(a); out.append((a, f"{label}|{st}"))
    for p in phrases:
        for f in dict.fromkeys(forms(p)):
            for hname, k in direct_keys(f).items():
                emit(k, f"{f[:44]}|{hname}")
            if hd:
                for sname, seed in seeds_from(f).items():
                    if sname == "raw": continue
                    for path in HD_PATHS:
                        try: emit(derive(seed, path), f"{f[:44]}|{sname}:{path}")
                        except Exception: pass
    return out

def selftest():
    rows = build(["correct horse battery staple"])
    addrs = {a for a, _ in rows}
    ok = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T" in addrs          # sha256 brainwallet, uncompressed
    sys.stderr.write(f"  'correct horse battery staple' -> its famous uncompressed address is produced: {'OK' if ok else 'FAIL'}\n")
    sys.stderr.write(f"  {len(rows)} addresses from one phrase (5 forms x 7 hashes x 5 scripts, deduped)\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrases"); ap.add_argument("--out", default="ideas_addrs.txt")
    ap.add_argument("--hd", action="store_true", help="also BIP-39 / Electrum seeds at 8 common paths")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest(): sys.exit("derivation is wrong; refusing")
    if a.selftest or not a.phrases: return
    phrases = [l.rstrip("\n") for l in open(a.phrases, encoding="utf-8") if l.strip() and not l.startswith("#")]
    rows = build(phrases, a.hd)
    with open(a.out, "w") as f:
        for addr, _ in rows: f.write(addr + "\n")
    with open(a.out + ".labels", "w") as f:
        for addr, lab in rows: f.write(f"{addr}\t{lab}\n")
    sys.stderr.write(f"  {len(phrases)} phrases -> {len(rows):,} addresses -> {a.out} (+ .labels)\n")

if __name__ == "__main__":
    main()
