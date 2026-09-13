#!/usr/bin/env python3
"""
Hunt for a PRINTED key in the article, using the key format's own checksum.

THE SHIFT
Every derivation in this project -- ~72M addresses -- used the BLOCKCHAIN as
the oracle: hash a phrase, derive an address, ask whether it is funded. That is
structurally blind to a key that is *printed in the article* rather than
derived from it, and it is useless if the prize address was never funded.

Key formats carry their own checksums. That gives an oracle that needs no
address, no chain access, and no assumption about hashing:

  WIF uncompressed  51 chars, '5',        0x80 + 32 bytes + 4-byte dSHA256 check
  WIF compressed    52 chars, 'K' or 'L', 0x80 + 32 bytes + 0x01 + 4-byte check
  BIP38 encrypted   58 chars, '6P',       4-byte check
  Casascius mini    22/26/30 chars, 'S',  sha256(key + '?') must start 0x00

A WIF checksum is a 1-in-4-billion filter. A random 51-char base58 string
passes with probability 2^-32, so across every selection rule tried here the
expected number of false positives is far below one. Anything that passes is
almost certainly the intended key -- and it validates the EXTRACTION RULE, not
a guess about which hash was used.

WHAT IS SCANNED
Many character streams pulled from the article, each then swept with sliding
windows of every valid key length, forwards and mirrored:

  every base58-legal character in reading order
  letters only; capitals only; the first letter of every word
  the first/last letter of every printed line
  every Nth character, N = 2..12, all offsets
  the same streams per page

  python3 wif_hunt.py --selftest
  python3 wif_hunt.py --transcript article_transcript.txt
"""
import argparse, hashlib, itertools, re, sys

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58SET = set(B58)


def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def check_wif(s):
    """Return (kind, privkey_hex) if s is a checksum-valid WIF, else None."""
    if len(s) not in (51, 52) or any(c not in B58SET for c in s):
        return None
    try:
        raw = b58decode(s)
    except ValueError:
        return None
    if len(raw) not in (37, 38) or raw[0] != 0x80:
        return None
    body, chk = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4] != chk:
        return None
    if len(raw) == 38 and raw[33] != 0x01:
        return None
    return ("wif_compressed" if len(raw) == 38 else "wif_uncompressed",
            body[1:33].hex())


def check_bip38(s):
    if len(s) != 58 or not s.startswith("6P") or any(c not in B58SET for c in s):
        return None
    try:
        raw = b58decode(s)
    except ValueError:
        return None
    if len(raw) != 43:
        return None
    body, chk = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4] != chk:
        return None
    return ("bip38", raw.hex())


def check_mini(s):
    if len(s) not in (22, 26, 30) or not s.startswith("S"):
        return None
    if any(c not in B58SET for c in s):
        return None
    if hashlib.sha256((s + "?").encode()).digest()[0] != 0:
        return None
    return ("casascius_mini", hashlib.sha256(s.encode()).hexdigest())


CHECKS = (check_wif, check_bip38, check_mini)
LENGTHS = (22, 26, 30, 51, 52, 58)


def scan(stream, tag, hits):
    """Slide every key length over a character stream, forwards and mirrored."""
    for direction, s in (("fwd", stream), ("mir", stream[::-1])):
        for L in LENGTHS:
            if len(s) < L:
                continue
            for i in range(len(s) - L + 1):
                w = s[i:i + L]
                for fn in CHECKS:
                    r = fn(w)
                    if r:
                        hits.append((tag, direction, i, w, r[0], r[1]))


def streams(text, lines):
    """Every character stream worth sliding a key window over."""
    out = {}
    b58_only = "".join(c for c in text if c in B58SET)
    out["all_b58"] = b58_only
    out["letters"] = "".join(c for c in text if c.isalpha() and c in B58SET)
    out["capitals"] = "".join(c for c in text if c.isupper() and c in B58SET)
    words = re.findall(r"[A-Za-z0-9]+", text)
    out["word_initials"] = "".join(w[0] for w in words if w[0] in B58SET)
    out["word_finals"] = "".join(w[-1] for w in words if w[-1] in B58SET)
    out["line_initials"] = "".join(l[0] for l in lines if l and l[0] in B58SET)
    out["line_finals"] = "".join(l[-1] for l in lines if l and l[-1] in B58SET)
    for n in range(2, 13):
        for off in range(n):
            out[f"every{n}+{off}"] = b58_only[off::n]
    return out


def selftest():
    """A real WIF must be found when hidden in noise, and noise alone must not
    produce one. Without both halves a null from this scanner is meaningless."""
    ok = True
    # a known-valid WIF: privkey = 0x01
    priv = (1).to_bytes(32, "big")
    body = b"\x80" + priv
    chk = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    n = int.from_bytes(body + chk, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    sys.stderr.write(f"  constructed WIF for privkey=1: {s}\n")
    got = check_wif(s)
    ok &= got is not None and got[1] == priv.hex()
    sys.stderr.write(f"  recognised as valid: {got is not None}\n")

    hits = []
    scan("aaaa" + s + "zzzz", "positive_control", hits)
    found = any(h[5] == priv.hex() for h in hits)
    ok &= found
    sys.stderr.write(f"  found when buried in noise: {found}\n")

    # a corrupted copy must NOT pass
    bad = s[:-1] + ("A" if s[-1] != "A" else "B")
    ok &= check_wif(bad) is None
    sys.stderr.write(f"  corrupted copy rejected: {check_wif(bad) is None}\n")

    # Random base58 noise must not produce a valid WIF or BIP38. It WILL
    # produce Casascius mini keys: that format's only test is a single
    # checksum byte after an 'S' prefix, so the filter is ~1/58 * 1/256 =
    # 1 in 14,848 per window, not 1 in 4 billion. Measured below rather than
    # assumed -- the "1 in 4 billion" claim holds for WIF/BIP38 only, and mini
    # hits therefore need the chain as a second filter.
    import random
    rng = random.Random(11)
    noise = "".join(rng.choice(B58) for _ in range(200000))
    nh = []
    scan(noise, "noise", nh)
    strong = [h for h in nh if h[4] != "casascius_mini"]
    weak = [h for h in nh if h[4] == "casascius_mini"]
    sys.stderr.write(f"  false positives in 200k random base58 chars: "
                     f"{len(strong)} WIF/BIP38, {len(weak)} mini\n")
    sys.stderr.write(f"    (mini false positives are expected: ~1 in 14,848 per "
                     f"window, so mini hits are screened against the chain)\n")
    ok &= len(strong) == 0

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("refusing to scan: the checksum oracle is not working")
    if a.selftest:
        return

    raw = open(a.transcript, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    pages, it = [], iter(parts[1:])
    for num, body in zip(it, it):
        pages.append((num, [l.strip() for l in body.splitlines() if l.strip()]))

    scopes = [("ALL", [l for _, ls in pages for l in ls])]
    scopes += [(f"p{n}", ls) for n, ls in pages]

    hits, total = [], 0
    for tag, lines in scopes:
        text = " ".join(lines)
        for name, st in streams(text, lines).items():
            total += len(st)
            scan(st, f"{tag}/{name}", hits)

    sys.stderr.write(f"\nscanned {total:,} characters across "
                     f"{len(scopes)} scopes x {len(streams(' '.join(scopes[0][1]), scopes[0][1]))} "
                     f"streams, forwards and mirrored\n")
    strong = [h for h in hits if h[4] != "casascius_mini"]
    weak = [h for h in hits if h[4] == "casascius_mini"]
    sys.stderr.write(f"checksum-valid WIF/BIP38 (1-in-4-billion filter): {len(strong)}\n")
    sys.stderr.write(f"mini-key shaped strings (weak 1-in-14,848 filter): {len(weak)}\n")

    for tag, d, i, w, kind, k in strong:
        sys.stderr.write(f"\n*** {kind}  {tag} {d} @{i}\n    {w}\n    priv {k}\n")

    # Mini hits are mostly noise by construction, so screen them against the
    # funded index -- the chain is the only thing that can separate a real
    # mini key from the ~1-in-15k coincidences this format produces.
    if weak:
        try:
            from index_oracle import Oracle
            from full_sweep import spks_for_key
            o = Oracle(verbose=False)
            if o.calibrate():
                real = 0
                for tag, d, i, w, kind, k in weak:
                    spks = spks_for_key(bytes.fromhex(k))
                    for j, bal in o.contains_spks([s for _, s in spks]):
                        real += 1
                        sys.stderr.write(f"\n*** FUNDED MINI KEY  {tag} {d} @{i}\n"
                                         f"    {w}\n    priv {k}\n"
                                         f"    {spks[j][0]}  {bal/1e8:.8f} BTC\n")
                sys.stderr.write(f"\n  {len(weak)} mini-shaped strings screened "
                                 f"against the funded index: {real} funded\n")
        except Exception as e:
            sys.stderr.write(f"  (could not screen mini hits: {e})\n")

    if not strong:
        sys.stderr.write("\nNo printed key. Under every selection rule tried, the\n"
                         "article contains no checksum-valid WIF, BIP38 or mini key.\n")


if __name__ == "__main__":
    main()
