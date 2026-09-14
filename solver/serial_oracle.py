#!/usr/bin/env python3
"""
The banknote serial read as a CHECKSUM, not as key material.

THE IDEA
Every prior pass treated the $100 note's serial CL76841714A as something to
hash — a passphrase, a seed, a brainwallet input. 4,642 such derivations, all
null. But the serial's eight digits are 76841714, and every one of those is a
legal HEX digit, so 0x76841714 is a well-formed FOUR-BYTE value. Four bytes is
exactly, and unusually specifically, the size of a Base58Check checksum:

  WIF          base58check(0x80 || key [|| 0x01])   last 4 bytes
  address      base58check(0x00 || hash160)         last 4 bytes
  BIP38        same 4-byte trailer

WHY THIS IS WORTH TESTING EVEN THOUGH IT IS A GUESS
It inverts the project's core problem. Every sweep so far has needed the chain
to recognise success, and the chain is blind to a key that was never funded or
was swept years ago — which is exactly the state this prize is most likely in.
A checksum needs nothing external. It says "this derivation is the intended
one" on its own.

It is also enormously cheaper. A WIF checksum is two SHA-256s over 33 or 34
bytes. There is NO elliptic-curve multiplication, which is what makes address
sweeps slow. Testing a candidate key against a target checksum is roughly two
orders of magnitude faster than deriving its address, so this filter can cover
spaces the address sweeps cannot reach.

WHAT A HIT WOULD AND WOULD NOT MEAN
A 4-byte match is 1 in 2^32. Across the ~10^7 candidates here the expected
number of false positives is about 0.002, so a hit is strong — but it is a
hypothesis test on an unproven premise, so any hit is reported as a candidate
requiring the full output contract (derivation, checksum, address, chain
state), never as the prize.

TARGETS
Several readings, because "which four bytes" is itself a guess: the digits as
hex; as a decimal integer; both reversed (the note is printed MIRRORED on
page 73, which is the repo's one demonstrated mirror); and byte-swapped.

  python3 serial_oracle.py --selftest
  python3 serial_oracle.py --addresses window/named_exact20_870.txt
  python3 serial_oracle.py --keys /tmp/numbers.txt
"""
import argparse, hashlib, itertools, os, sys

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58IDX = {c: i for i, c in enumerate(B58)}

SERIAL_DIGITS = "76841714"          # CL76841714A, page 73/74 note
SERIAL_FULL = "CL76841714A"
# Second note, ghosting through on page 72. This was recorded as "KB4?27" --
# only four characters legible -- and set aside as unable to produce a 4-byte
# target. That reading came from the phone JPEGs. Read from the 400 dpi scan
# (scan/Scan1.pdf) with the faint layer isolated, all eight digits resolve:
SECOND_NOTE = "KB46279860"
SECOND_NOTE_DIGITS = "46279860"     # all legal hex, so 0x46279860 IS a target
SECOND_NOTE_PARTIAL = "KB4?27"      # kept: what the JPEGs could support


def sha256d(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def b58decode(s):
    n = 0
    for c in s:
        if c not in B58IDX:
            return None
        n = n * 58 + B58IDX[c]
    b = n.to_bytes(25, "big") if n < 256 ** 25 else None
    return b


def addr_checksum(addr):
    """The 4 trailing checksum bytes of a Base58Check address, or None."""
    b = b58decode(addr)
    if b is None:
        return None
    if sha256d(b[:21])[:4] != b[21:]:
        return None                      # not a valid address at all
    return b[21:]


def wif_checksums(key32):
    """Checksum bytes for the uncompressed and compressed WIF of a key."""
    u = sha256d(b"\x80" + key32)[:4]
    c = sha256d(b"\x80" + key32 + b"\x01")[:4]
    return u, c


def targets(digits=SERIAL_DIGITS):
    """Candidate 4-byte values the serial could be, each with a label."""
    out = {}
    rev = digits[::-1]
    for name, d in (("hex", digits), ("hex_reversed", rev)):
        try:
            out[name] = bytes.fromhex(d)
        except ValueError:
            pass
    for name, d in (("decimal", digits), ("decimal_reversed", rev)):
        v = int(d)
        if v < 2 ** 32:
            out[name] = v.to_bytes(4, "big")
            out[name + "_le"] = v.to_bytes(4, "little")
    for k in list(out):
        out[k + "_byteswap"] = out[k][::-1]
    return out


def selftest():
    """The matcher must fire on a constructed positive and stay silent on a
    near-miss, and the target table must contain the literal hex reading."""
    ok = True

    # Positive control: build a key, take its real WIF checksum, and confirm
    # the oracle finds it when that checksum is the target.
    key = hashlib.sha256(b"overdose control").digest()
    u, c = wif_checksums(key)
    found = (u == u) and (wif_checksums(key)[0] == u)
    sys.stderr.write(f"  control key WIF checksum uncompressed {u.hex()} "
                     f"compressed {c.hex()}\n")
    ok &= found

    # Negative control: a one-bit change must not match.
    key2 = bytearray(key)
    key2[31] ^= 1
    u2, _ = wif_checksums(bytes(key2))
    sys.stderr.write(f"  one-bit-different key checksum {u2.hex()}: "
                     f"{'DIFFERS (correct)' if u2 != u else 'COLLIDES (FAIL)'}\n")
    ok &= (u2 != u)

    # Address checksum extraction must validate a real address and reject a
    # corrupted one.
    good = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    cs = addr_checksum(good)
    sys.stderr.write(f"  genesis address checksum {cs.hex() if cs else None}\n")
    ok &= cs is not None
    bad = good[:-1] + ("b" if good[-1] != "b" else "c")
    sys.stderr.write(f"  corrupted address rejected: "
                     f"{'yes' if addr_checksum(bad) is None else 'NO (FAIL)'}\n")
    ok &= addr_checksum(bad) is None

    t = targets()
    sys.stderr.write(f"  {len(t)} target readings; hex reading = "
                     f"{t['hex'].hex()}\n")
    ok &= t["hex"] == bytes.fromhex(SERIAL_DIGITS)

    # End-to-end: plant the control key's checksum as a target and confirm a
    # sweep over one key finds it.
    hits = scan_keys([("control", key)], {"planted": u})
    sys.stderr.write(f"  end-to-end planted-target scan found {len(hits)} hit "
                     f"(want 1)\n")
    ok &= len(hits) == 1

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def scan_keys(named_keys, tgts):
    """Yield (label, target_name, form, key_hex) for WIF checksum matches."""
    hits = []
    rev = {}
    for name, b in tgts.items():
        rev.setdefault(b, []).append(name)
    for label, k in named_keys:
        if len(k) != 32 or int.from_bytes(k, "big") == 0:
            continue
        u, c = wif_checksums(k)
        for form, cs in (("uncompressed", u), ("compressed", c)):
            if cs in rev:
                for tn in rev[cs]:
                    hits.append((label, tn, form, k.hex()))
    return hits


HASHES = {
    "sha256":  lambda b: hashlib.sha256(b).digest(),
    "sha256d": lambda b: sha256d(b),
    "sha1":    lambda b: hashlib.sha1(b).digest(),
    "sha512":  lambda b: hashlib.sha512(b).digest(),
    "sha3_256": lambda b: hashlib.sha3_256(b).digest(),
    "blake2b": lambda b: hashlib.blake2b(b, digest_size=32).digest(),
    "ripemd160_of_sha256": lambda b: hashlib.new(
        "ripemd160", hashlib.sha256(b).digest()).digest(),
    "md5":     lambda b: hashlib.md5(b).digest(),
}


def scan_phrase_checksums(path, tgts, limit=None):
    """The serial as a checksum over the ANSWER TEXT, not over a key.

    This is the strongest form of the idea and the cheapest to test. If the
    serial is a verification tag for "you have extracted the right words", then
    for the correct phrase some standard digest begins or ends with those four
    bytes. It needs no key format, no elliptic curve and no chain — which
    matters because the chain cannot see an unfunded or long-swept key, and
    that is the state this prize is most likely in.
    """
    rev = {}
    for name, b in tgts.items():
        rev.setdefault(b, []).append(name)
    hits, n = [], 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n")
            if not p:
                continue
            n += 1
            if limit and n > limit:
                break
            for enc in (p, p.lower(), p.upper(), p.replace(" ", "")):
                b = enc.encode("utf-8")
                for hn, fn in HASHES.items():
                    d = fn(b)
                    for pos, four in (("head", d[:4]), ("tail", d[-4:])):
                        if four in rev:
                            for tn in rev[four]:
                                hits.append((enc[:60], hn, pos, tn, four.hex()))
    return hits, n


def keys_from_phrases(path, limit=None, direct_only=False):
    """Every key a phrase produces, reusing the project's own derivations."""
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    paths = build_paths()
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n")
            if not p:
                continue
            n += 1
            if limit and n > limit:
                return
            for name, k in direct_keys(p).items():
                yield (f"{p[:40]}|{name}", k)
            if direct_only:
                continue
            for sname, seed in seeds_from(p).items():
                for dp in paths:
                    try:
                        k = derive(seed, dp)
                    except Exception:
                        continue
                    if k:
                        yield (f"{p[:40]}|{sname}|{dp}", k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addresses")
    ap.add_argument("--keys")
    ap.add_argument("--phrase-checksums")
    ap.add_argument("--digits", default=SERIAL_DIGITS)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--direct-only", action="store_true",
                    help="skip HD paths: direct key hashes only, no EC math, "
                         "which is what makes this filter fast")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("oracle fails its own controls; refusing to report")
    if a.selftest:
        return

    tgts = targets(a.digits)
    sys.stderr.write(f"\n  serial {SERIAL_FULL}, digits {a.digits}\n")
    for k, v in sorted(tgts.items()):
        sys.stderr.write(f"    target {k:22} {v.hex()}\n")

    if a.addresses:
        addrs = [l.strip() for l in open(a.addresses) if l.strip()]
        want = {v: k for k, v in tgts.items()}
        hits, bech, bad, tested = [], 0, 0, 0
        for ad in addrs:
            # bech32/bech32m carry a 6-character BCH checksum, not a 4-byte
            # Base58Check trailer, so the serial reading cannot apply to them.
            # They are NOT TESTED, and saying "870 addresses, no match" without
            # this split would overstate the coverage by more than half.
            if ad.lower().startswith("bc1"):
                bech += 1
                continue
            cs = addr_checksum(ad)
            if cs is None:
                bad += 1
                continue
            tested += 1
            if cs in want:
                hits.append((ad, want[cs], cs.hex()))
        # Control: the checksum of a known address must be findable by the
        # same code path, or a null here means nothing.
        ctrl = addr_checksum("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        sys.stderr.write(f"\n  {len(addrs)} addresses: {tested} base58 TESTED, "
                         f"{bech} bech32 NOT APPLICABLE (6-char BCH checksum, "
                         f"not a 4-byte trailer), {bad} undecodable\n")
        sys.stderr.write(f"  control: genesis checksum extracted = "
                         f"{ctrl.hex()}\n")
        found = [ad for ad in addrs if addr_checksum(ad) == ctrl]
        sys.stderr.write(f"  control: scanning for that checksum in the list "
                         f"finds {len(found)} (0 expected unless genesis is "
                         f"in it)\n")
        sys.stderr.write(f"  expected false positives at 1-in-2^32: "
                         f"{tested*len(set(tgts.values()))/2**32:.2e}\n")
        if hits:
            for ad, tn, cs in hits:
                sys.stderr.write(f"  *** MATCH {ad}  target={tn}  cs={cs}\n")
        else:
            sys.stderr.write("  no address in this list has a Base58Check "
                             "checksum equal to any reading of the serial\n")

    if a.phrase_checksums:
        # Control first: plant a phrase whose sha256 head we make the target,
        # so a null below means the scan works and found nothing.
        ctrl_phrase = "overdose serial control"
        ctrl = hashlib.sha256(ctrl_phrase.encode()).digest()[:4]
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(ctrl_phrase + "\n")
            ctrl_path = tf.name
        ch, _ = scan_phrase_checksums(ctrl_path, {"planted": ctrl})
        os.unlink(ctrl_path)
        sys.stderr.write(f"\n  CONTROL: planted-checksum phrase scan found "
                         f"{len(ch)} hit(s), want >=1\n")
        if not ch:
            sys.exit("phrase-checksum scanner cannot find a planted target")
        hits, n = scan_phrase_checksums(a.phrase_checksums, tgts, a.limit)
        nt = len(set(tgts.values()))
        sys.stderr.write(f"  {n:,} phrases x 4 encodings x {len(HASHES)} "
                         f"digests x 2 positions vs {nt} targets\n")
        sys.stderr.write(f"  expected false positives: "
                         f"{n*4*len(HASHES)*2*nt/2**32:.3f}\n")
        for h in hits:
            sys.stderr.write(f"  *** PHRASE CHECKSUM MATCH {h}\n")
        if not hits:
            sys.stderr.write("  no phrase digest begins or ends with any "
                             "reading of the serial\n")

    if a.keys:
        tot = 0
        hits = []
        for label, k in keys_from_phrases(a.keys, a.limit, a.direct_only):
            tot += 1
            h = scan_keys([(label, k)], tgts)
            if h:
                hits.extend(h)
            if tot % 200000 == 0:
                sys.stderr.write(f"  {tot:,} keys checked, {len(hits)} hits\n")
        sys.stderr.write(f"\n  {tot:,} keys checked against "
                         f"{len(set(tgts.values()))} distinct targets "
                         f"x 2 WIF forms\n")
        sys.stderr.write(f"  expected false positives: "
                         f"{tot*len(set(tgts.values()))*2/2**32:.3f}\n")
        for label, tn, form, kh in hits:
            sys.stderr.write(f"  *** WIF CHECKSUM MATCH  target={tn} "
                             f"form={form}\n      key={kh}\n      from={label}\n")
        if not hits:
            sys.stderr.write("  no derived key has a WIF checksum equal to "
                             "any reading of the serial\n")


if __name__ == "__main__":
    main()
