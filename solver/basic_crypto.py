#!/usr/bin/env python3
"""
The simple operations a non-expert reaches for, which this project never swept.

THE GAP
`hd_sweep.direct_keys` is the derivation path EVERY sweep here uses, and it
holds seven hashes: sha256, dsha256, sha512 halves, sha3_256, blake2b and a
keccak variant. All modern, all cryptographer's choices.

Max Keiser is a broadcaster. Someone in 2021 wanting to turn a phrase into a
key, without knowing what a KDF is, reaches for **md5** or **sha1** — the two
hashes a non-specialist has actually heard of. Neither has ever been in the
main derivation path. `grep` finds them only in isolated one-off scripts
(serial_oracle.py, kdf_sweep.py), never crossed with the phrase corpus.

Caesar shifts are absent from the repo entirely, and ROT13 is the one cipher
everyone knows.

WHAT THIS ADDS

  pre-transforms applied to the phrase before hashing
    identity, reverse, ROT-1..25, atbash, case variants, strip spaces,
    strip punctuation, base64, hex, and the serial appended/prepended

  key derivations that are NOT in direct_keys
    md5 doubled and md5-padded to 32 bytes
    sha1 padded, and sha1(sha1) concatenated
    ripemd160 padded
    sha256 XOR the banknote serial

Deliberately NOT a search for cryptographic strength. These constructions are
all weak, which is the point: a weak construction is what an amateur produces,
and a printed puzzle wants a key its author can regenerate.

  python3 basic_crypto.py --selftest
  python3 basic_crypto.py --scope distinguished
  python3 basic_crypto.py --scope all
"""
import argparse, base64, hashlib, itertools, string, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SERIAL, DIGITS = "CL76841714A", "76841714"
LOWER, UPPER = string.ascii_lowercase, string.ascii_uppercase


def rot(s, n):
    out = []
    for c in s:
        if c in LOWER:
            out.append(LOWER[(LOWER.index(c) + n) % 26])
        elif c in UPPER:
            out.append(UPPER[(UPPER.index(c) + n) % 26])
        else:
            out.append(c)
    return "".join(out)


def atbash(s):
    out = []
    for c in s:
        if c in LOWER:
            out.append(LOWER[25 - LOWER.index(c)])
        elif c in UPPER:
            out.append(UPPER[25 - UPPER.index(c)])
        else:
            out.append(c)
    return "".join(out)


def pre_transforms(p):
    """Every simple textual mangling, named."""
    yield "id", p
    yield "rev", p[::-1]
    yield "atbash", atbash(p)
    yield "upper", p.upper()
    yield "lower", p.lower()
    yield "title", p.title()
    yield "swapcase", p.swapcase()
    yield "nospace", p.replace(" ", "")
    yield "alnum", "".join(c for c in p if c.isalnum())
    yield "b64", base64.b64encode(p.encode()).decode()
    yield "hex", p.encode().hex()
    yield "serial_suf", p + SERIAL
    yield "serial_pre", SERIAL + p
    yield "digits_suf", p + DIGITS
    for n in range(1, 26):
        yield f"rot{n}", rot(p, n)


def _pad32(b):
    """Stretch a short digest to 32 bytes the way an amateur would: repeat it."""
    return (b * (32 // len(b) + 1))[:32]


def basic_keys(s):
    """Phrase -> 32-byte key, by constructions direct_keys does not cover."""
    b = s.encode("utf-8", "surrogatepass")
    md5 = hashlib.md5(b).digest()
    sha1 = hashlib.sha1(b).digest()
    try:
        rmd = hashlib.new("ripemd160", b).digest()
    except Exception:
        rmd = None
    out = {
        "md5_x2": md5 + md5,                       # 16+16 = 32
        "md5_pad": _pad32(md5),
        "md5_sha256": hashlib.sha256(md5).digest(),
        "sha1_pad": _pad32(sha1),
        "sha1_x2_trunc": (sha1 + sha1)[:32],
        "sha1_sha256": hashlib.sha256(sha1).digest(),
    }
    if rmd:
        out["ripemd_pad"] = _pad32(rmd)
        out["ripemd_sha256"] = hashlib.sha256(rmd).digest()
    # the serial as an XOR mask over the standard brainwallet key
    base = hashlib.sha256(b).digest()
    mask = _pad32(SERIAL.encode())
    out["sha256_xor_serial"] = bytes(x ^ y for x, y in zip(base, mask))
    mask2 = _pad32(DIGITS.encode())
    out["sha256_xor_digits"] = bytes(x ^ y for x, y in zip(base, mask2))
    return out


def phrases(scope):
    import article
    lines, sents, paras = article.load()
    out = list(sents) + list(paras) + list(lines)
    out += ["BITCOIN IS TOXIC AF", "OVERDOSE", "Overdose", "MAX KEISER",
            "Max Keiser", "with Max Keiser", "El Salvador", "ORANGEPILL",
            SERIAL, DIGITS, "L12"]
    try:
        for l in open("highlights_ordered.tsv", encoding="utf-8"):
            if not l.startswith("#") and l.strip():
                p = l.rstrip("\n").split("\t")
                if len(p) >= 3:
                    out.append(p[2])
    except OSError:
        pass
    if scope == "all":
        words = " ".join(paras).split()
        for n in range(2, 9):
            for i in range(len(words) - n + 1):
                out.append(" ".join(words[i:i + n]))
    seen, uniq = set(), []
    for p in out:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def selftest():
    ok = True
    ok &= rot("abc", 13) == "nop" and rot(rot("Hello, World!", 13), 13) == "Hello, World!"
    sys.stderr.write(f"  ROT13 round-trips and preserves punctuation: "
                     f"{'OK' if rot(rot('Hello, World!',13),13)=='Hello, World!' else 'FAIL'}\n")
    ok &= atbash("abc") == "zyx" and atbash(atbash("Max")) == "Max"
    sys.stderr.write(f"  atbash is its own inverse: "
                     f"{'OK' if atbash(atbash('Max'))=='Max' else 'FAIL'}\n")

    k = basic_keys("satoshi")
    ok &= all(len(v) == 32 for v in k.values())
    sys.stderr.write(f"  {len(k)} key constructions, all exactly 32 bytes: "
                     f"{'OK' if all(len(v)==32 for v in k.values()) else 'FAIL'}\n")
    # md5_x2 must genuinely be the digest twice, not a rehash
    m = hashlib.md5(b"satoshi").digest()
    ok &= k["md5_x2"] == m + m
    sys.stderr.write(f"  md5_x2 is the 16-byte digest concatenated with itself: "
                     f"{'OK' if k['md5_x2']==m+m else 'FAIL'}\n")
    # the XOR must actually change the key
    base = hashlib.sha256(b"satoshi").digest()
    ok &= k["sha256_xor_serial"] != base
    sys.stderr.write(f"  the serial XOR changes the standard brainwallet key: "
                     f"{'OK' if k['sha256_xor_serial']!=base else 'FAIL'}\n")

    # these must NOT duplicate what direct_keys already sweeps
    from hd_sweep import direct_keys
    existing = set(direct_keys("satoshi").values())
    overlap = [n for n, v in k.items() if v in existing]
    ok &= not overlap
    sys.stderr.write(f"  no construction duplicates direct_keys "
                     f"({'none' if not overlap else overlap}): "
                     f"{'OK' if not overlap else 'FAIL'}\n")

    t = list(pre_transforms("Max"))
    ok &= len(t) == 39
    sys.stderr.write(f"  {len(t)} pre-transforms per phrase\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=("distinguished", "all"),
                    default="distinguished")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("basic constructions fail their own checks; refusing")
    if a.selftest:
        return

    import continuous_solver as CS
    from full_sweep import spks_for_key
    from spk_extra import spks_extra
    from hd_sweep import direct_keys

    ps = phrases(a.scope)
    sys.stderr.write(f"\n  {len(ps):,} phrases x 39 pre-transforms x "
                     f"~10 constructions\n")
    meta, spks, n = [], [], 0
    orc = CS.IndexOracle()
    hits_total = 0

    def flush():
        nonlocal meta, spks, hits_total
        if not spks:
            return
        for j, bal in orc.check(spks):
            hits_total += 1
            sys.stderr.write(f"\n  *** HIT {bal} :: {meta[j]}\n")
        meta, spks = [], []

    for p in ps:
        for tname, t in pre_transforms(p):
            for kname, k in basic_keys(t).items():
                if not (0 < int.from_bytes(k, "big") < CURVE_N):
                    continue
                n += 1
                for st, spk in list(spks_for_key(k)) + list(spks_extra(k)):
                    meta.append(f"{p[:48]}|{tname}|{kname}|{st}")
                    spks.append(spk)
                if len(spks) >= 60000:
                    flush()
    flush()
    sys.stderr.write(f"\n  {n:,} keys swept, {hits_total} hit(s)\n")
    if not hits_total:
        sys.stderr.write("  no basic construction derives to a funded "
                         "address\n")


if __name__ == "__main__":
    main()
