#!/usr/bin/env python3
"""
Famous keys that are funded but are NOT anybody's secret. Filter them.

WHY THIS EXISTS
The first non-empty .hits file this project has produced reads:

    HIT  330  bip39:m/86'/0'/0'/0/0  p2tr
         abandon abandon ... abandon about

That is the canonical BIP-39 zero-entropy test vector -- the mnemonic for
entropy 0x00000000000000000000000000000000, present in every wallet test suite
ever written. Its addresses hold dust because people mis-send to them
constantly. 330 satoshis is 0.0000033 BTC.

It appeared because a typography bit-channel produced an all-zero bit run.
ANY degenerate channel does: all-zeros, all-ones, a constant byte, a short
repeated pattern. The oracle answers "is this funded", and these are funded, so
they register as hits and look exactly like a solve.

Nothing here is a vulnerability or a target -- these are public test vectors
with dust balances, and the point of the module is to STOP reporting them.

  python3 decoys.py --selftest
"""
import hashlib, sys

# entropies that any broken or degenerate derivation lands on
DEGENERATE_ENTROPY = [bytes(n) for n in (16, 24, 32)]
DEGENERATE_ENTROPY += [b"\xff" * n for n in (16, 24, 32)]
DEGENERATE_ENTROPY += [bytes([i]) * 16 for i in (0x01, 0x55, 0xaa)]

# published test vectors and the most-swept brainwallet phrases
DECOY_PHRASES = {
    "abandon " * 11 + "about",
    "abandon " * 23 + "art",
    "legal winner thank year wave sausage worth useful legal winner thank yellow",
    "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
    "zoo " * 11 + "wrong",
    "correct horse battery staple",
    "satoshi nakamoto", "password", "123456", "bitcoin", "test", "hello world",
    "ER8FT+HFjk0",                       # the WarpWallet published vector
}

# degenerate private keys
DECOY_KEYS = {bytes(32), bytes([1]) + bytes(31), b"\xff" * 32,
              bytes(31) + bytes([1]),
              hashlib.sha256(b"").digest(),
              hashlib.sha256(b"0").digest(),
              hashlib.sha256(b"1").digest()}

# a balance this small is dust, not a 20 BTC prize
DUST_SATS = 100_000          # 0.001 BTC


def normal(s):
    return " ".join(str(s).lower().split())


def is_decoy_phrase(p):
    n = normal(p)
    if n in {normal(x) for x in DECOY_PHRASES}:
        return "published test vector or canonical brainwallet"
    w = n.split()
    if len(w) >= 12 and len(set(w)) <= 2:
        return "degenerate mnemonic (<=2 distinct words)"
    return None


def is_decoy_key(k):
    if k in DECOY_KEYS:
        return "degenerate private key"
    if len(set(k)) <= 1:
        return "constant-byte private key"
    return None


def classify(phrase=None, key=None, balance=None):
    """(is_decoy, reason). A hit that trips ANY of these is not a solve."""
    if phrase is not None:
        r = is_decoy_phrase(phrase)
        if r:
            return True, r
    if key is not None:
        r = is_decoy_key(key)
        if r:
            return True, r
    if balance is not None and balance < DUST_SATS:
        return True, (f"dust: {balance} sats = {balance/1e8:.8f} BTC, and the "
                      f"prize is 20 BTC")
    return False, ""


def selftest():
    ok = True
    d, why = classify(phrase="abandon " * 11 + "about", balance=330)
    ok &= d
    sys.stderr.write(f"  the zero-entropy mnemonic is a decoy ({why}): "
                     f"{'OK' if d else 'FAIL'}\n")
    d2, why2 = classify(phrase="They are the sum of all our neuroses.",
                        balance=2_000_000_000)
    ok &= not d2
    sys.stderr.write(f"  an article phrase holding 20 BTC is NOT a decoy: "
                     f"{'OK' if not d2 else 'FAIL — would suppress a solve'}\n")
    d3, _w = classify(balance=330)
    ok &= d3
    sys.stderr.write(f"  330 sats alone is dust: {'OK' if d3 else 'FAIL'}\n")
    d4, _w = classify(balance=2_000_000_000)
    ok &= not d4
    sys.stderr.write(f"  2,000,000,000 sats is not dust: "
                     f"{'OK' if not d4 else 'FAIL'}\n")
    d5, _w = classify(key=bytes(32))
    ok &= d5
    sys.stderr.write(f"  an all-zero private key is a decoy: "
                     f"{'OK' if d5 else 'FAIL'}\n")
    d6, _w = classify(phrase="zoo " * 11 + "zoo")
    ok &= d6
    sys.stderr.write(f"  a 1-distinct-word mnemonic is degenerate: "
                     f"{'OK' if d6 else 'FAIL'}\n")
    # THE IMPORTANT NEGATIVE: the filter must not eat a real 12-word phrase
    d7, _w = classify(phrase="witch collapse practice feed shame open despair "
                             "creek road again ice least",
                      balance=2_000_000_000)
    ok &= not d7
    sys.stderr.write(f"  a genuine 12-distinct-word mnemonic at 20 BTC "
                     f"survives: {'OK' if not d7 else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    sys.stderr.write("\n  SELFTEST\n")
    sys.exit(0 if selftest() else 1)
