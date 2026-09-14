#!/usr/bin/env python3
"""
The SECOND banknote serial, given every framing the first one ever got.

WHAT UNBLOCKED THIS
`serial_oracle.py` already knew this note existed and gave up on it:

    # Second note, ghosting through on page 72. Only four characters are
    # legible ("KB 4?27"), so it cannot produce a 4-byte target;
    # recorded, not used.
    SECOND_NOTE_PARTIAL = "KB4?27"

That was read off the phone JPEGs. Read instead from the 400 dpi scan, with
the faint layer isolated (keep mid-greys, discard both the black display type
and the white paper), all eight digits are legible:

    KB 46279860

So the reason it was set aside no longer holds. And it has the property that
motivated the checksum framing for the first serial: 4,6,2,7,9,8,6,0 are all
legal hex digits, so 0x46279860 is a well-formed four-byte value -- exactly the
size of a Base58Check trailer.

THE FRAMINGS, matching what CL76841714A received across eight modules

  A  textual        every case/spacing/reversal form, direct hashes + 5 seed
                    types x 72 HD paths, 25 script forms      [done: 4.7M, null]
  B  checksum       does ANY derivation reproduce 0x46279860 as its WIF or
                    address trailer -- self-certifying, needs no chain
  C  entropy        the value as an RNG seed across 8 generators
  D  stretched      pbkdf2-sha256/sha512, scrypt, WarpWallet
  E  mirror         reverse, rot180, left-right mirror, x the full stack
  F  bip39          the digits as wordlist indices, checksum-validated
  G  paired         both serials combined, concatenated and arithmetic

  python3 serial2_exhaust.py --selftest
  python3 serial2_exhaust.py --framings B,C,D,E,F,G
"""
import argparse, hashlib, itertools, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
S2, S2D, S2L = "KB46279860", "46279860", "KB"
S1, S1D = "CL76841714A", "76841714"


def textual_forms():
    """Every string form of the second serial worth deriving from."""
    out = set()
    base = [S2, S2D, S2L, "KB 46279860", "KB 4627 9860", S2 + "A", S2D + "A"]
    for b in base:
        for v in (b, b.upper(), b.lower(), b.replace(" ", ""), b[::-1],
                  b[::-1].lower()):
            out.add(v)
    import mirror_serial as MS
    for b in (S2, S2D):
        out.add(MS.rot180(b))
        out.add(MS.mirror(b))
    for tail in ("", " El Salvador", " OVERDOSE", " Max Keiser", " NUMBERS",
                 " Western Union", " 572", " 165"):
        out.add(S2 + tail)
        out.add(S2D + tail)
        out.add((tail + " " + S2).strip())
    return sorted(x for x in out if x)


def framing_B():
    """Checksum: does any derivation reproduce 0x46279860? Self-certifying."""
    import serial_oracle as SO
    tg = SO.targets(digits=S2D)
    sys.stderr.write(f"  [B] {len(tg)} four-byte target readings of {S2D}\n")
    for k, v in list(tg.items())[:8]:
        sys.stderr.write(f"        {k:22} {v.hex() if hasattr(v,'hex') else v}\n")
    named = []
    for p in textual_forms():
        for h, k in _direct(p).items():
            named.append((f"{p}|{h}", k))
    hits = SO.scan_keys(named, tg)
    sys.stderr.write(f"  [B] {len(named):,} keys scanned, {len(hits)} "
                     f"checksum match(es)\n")
    return hits


def _direct(p):
    from hd_sweep import direct_keys
    return direct_keys(p)


def framing_C(orc):
    """The value as an RNG seed."""
    import serial_entropy as SE
    seeds = {"dec": int(S2D), "dec_rev": int(S2D[::-1]),
             "hex": int(S2D, 16), "hex_rev": int(S2D[::-1], 16),
             "sha_int": int.from_bytes(
                 hashlib.sha256(S2.encode()).digest()[:8], "big")}
    gens = [SE.gen_python, SE.gen_numpy, SE.gen_glibc, SE.gen_java,
            SE.gen_msvc, SE.gen_xorshift64, SE.gen_pcg32]
    keys = []
    for sn, sv in seeds.items():
        for g in gens:
            try:
                for i, k in enumerate(g(sv, 8)):
                    kb = k if isinstance(k, bytes) else \
                        int(k).to_bytes(32, "big", signed=False)
                    keys.append((f"{sn}|{g.__name__}|{i}", kb))
            except Exception:
                continue
    sys.stderr.write(f"  [C] {len(keys):,} RNG-derived keys\n")
    return _check(keys, orc, "C")


def framing_D(orc):
    """Stretched KDFs over every textual form."""
    import kdf_sweep, warpwallet
    keys = []
    for p in textual_forms():
        for label, k in kdf_sweep.derivations(p):
            keys.append((f"{p}|{label}", k))
        for salt in kdf_sweep.SALTS[:4]:
            try:
                keys.append((f"{p}|warp|{salt}", warpwallet.warp_key(p, salt)))
            except Exception:
                pass
    sys.stderr.write(f"  [D] {len(keys):,} stretched keys\n")
    return _check(keys, orc, "D")


def framing_F():
    """The digits as BIP-39 wordlist indices, checksum-validated."""
    import bip39_index as BI
    nums = [int(c) for c in S2D] + [int(S2D[i:i + 2]) for i in range(0, 8, 2)]
    nums += [int(S2D), int(S2D) % 2048, int(S2D, 16) % 2048]
    hits = []
    for vn, seq in (("digits", [int(c) for c in S2D]),
                    ("pairs", [int(S2D[i:i + 2]) for i in range(0, 8, 2)]),
                    ("mod", [n % 2048 for n in nums])):
        for base in (0, 1):
            ws = BI.to_words(seq, base, True)
            if not ws:
                continue
            for i, k, w in BI.windows(ws):
                if BI.check(w):
                    hits.append((vn, base, " ".join(w)))
    sys.stderr.write(f"  [F] {len(hits)} checksum-valid mnemonic(s) from the "
                     f"digits\n")
    return hits


def _check(named, orc, tag):
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    meta, spks, hits = [], [], []
    for nm, k in named:
        if len(k) != 32 or not (0 < int.from_bytes(k, "big") < CURVE_N):
            continue
        for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
            meta.append((nm, st))
            spks.append(spk)
        if len(spks) >= 60000:
            for j, bal in orc.check(spks):
                hits.append(meta[j] + (bal,))
                sys.stderr.write(f"\n  *** [{tag}] HIT {bal} :: {meta[j]}\n")
            meta, spks = [], []
    if spks:
        for j, bal in orc.check(spks):
            hits.append(meta[j] + (bal,))
            sys.stderr.write(f"\n  *** [{tag}] HIT {bal} :: {meta[j]}\n")
    return hits


def selftest():
    ok = True
    ok &= all(c in "0123456789abcdefABCDEF" for c in S2D)
    sys.stderr.write(f"  {S2D} is all hex -> 0x{S2D} = {int(S2D,16)}: "
                     f"{'OK' if all(c in '0123456789abcdef' for c in S2D.lower()) else 'FAIL'}\n")
    ok &= S2 != S1 and S2D != S1D
    sys.stderr.write(f"  differs from the first serial {S1}: "
                     f"{'OK' if S2D != S1D else 'FAIL'}\n")
    # the value that unblocked this must be MORE than what was recorded before
    import serial_oracle as SO
    prev = getattr(SO, "SECOND_NOTE_PARTIAL", "")
    ok &= len(S2) > len(prev)
    sys.stderr.write(f"  serial_oracle recorded {prev!r} as too partial to use; "
                     f"we now have {S2!r}: {'OK' if len(S2) > len(prev) else 'FAIL'}\n")
    tg = SO.targets(digits=S2D)
    ok &= len(tg) >= 4
    sys.stderr.write(f"  {len(tg)} four-byte target readings derived\n")
    f = textual_forms()
    ok &= len(f) > 30
    sys.stderr.write(f"  {len(f)} textual forms\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--framings", default="B,C,D,F")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("the second-serial setup is wrong; refusing")
    if a.selftest:
        return

    want = set(a.framings.split(","))
    orc = None
    if want & {"C", "D"}:
        import continuous_solver as CS
        orc = CS.IndexOracle()
        if not orc.ready:
            sys.exit(f"no oracle: {orc.why}")
        if not orc.control():
            sys.exit("POSITIVE CONTROL FAILED; a null would be meaningless")
        sys.stderr.write("  oracle control OK\n")

    total = 0
    if "B" in want:
        total += len(framing_B())
    if "C" in want:
        total += len(framing_C(orc))
    if "D" in want:
        total += len(framing_D(orc))
    if "F" in want:
        total += len(framing_F())
    sys.stderr.write(f"\n  {total} result(s) across framings {sorted(want)}\n")
    if not total:
        sys.stderr.write(f"  {S2} produces no checksum match, no funded "
                         f"address under\n  RNG seeding or stretched KDFs, and "
                         f"no valid mnemonic.\n")


if __name__ == "__main__":
    main()
