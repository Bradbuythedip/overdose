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
    # THE GENESIS COINBASE HEADLINE. The second famous-brainwallet false positive
    # this project produced: the user's everfunded run reported its compressed
    # and uncompressed P2PKH addresses as EVER-FUNDED (11,000 and 3,862,600
    # sats). It is the most-hashed string in Bitcoin's history and sweeper
    # bots empty it in seconds. stream_hits.tsv shows an earlier session had
    # already hit it once. Never again.
    "the times 03/jan/2009 chancellor on brink of second bailout for banks",
    "chancellor on brink of second bailout for banks",
    # and the rest of the canonical brainwallet-cracker wordlist head
    "satoshi", "nakamoto", "you", "me", "i", "a", "abc", "qwerty", "letmein",
    "admin", "secret", "money", "freedom", "hodl", "blockchain", "crypto",
    "the quick brown fox jumps over the lazy dog",
    "to be or not to be", "hello", "love", "god", "sex", "1", "0", "",
}


def looks_like_public_tip_jar(funded_count, funded_sats, balance_sats):
    """Structural rule: a drained public brainwallet, from chain stats alone.

    A LIST of famous phrases is never complete. But every famous brainwallet
    shares a shape on-chain, whatever the phrase: MANY separate deposits (people
    test-sending, bots probing), NEARLY ALL of it swept out again, and only dust
    left. A key someone actually hid holds its funding; a public tip jar does
    not. This needs only the fields everfunded.py already has in hand.
    """
    if funded_count < 3:
        return False
    if funded_sats <= 0:
        return False
    swept_frac = 1.0 - (balance_sats / funded_sats)
    return swept_frac >= 0.95 and balance_sats < DUST_SATS

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
    # A PRESENCE sentinel is not a balance. The ever-used oracle answers "this
    # address has existed on chain" and carries no amount, so it reports None
    # (never 0, which would read as "unfunded"). Guarding on `0 <= balance`
    # keeps such a hit out of the dust branch: filing the one result this
    # project has been structurally unable to see as "dust: 20 BTC prize, this
    # is dust" would be the most expensive misclassification available.
    if balance is not None and 0 <= balance < DUST_SATS:
        return True, (f"dust: {balance} sats = {balance/1e8:.8f} BTC, and the "
                      f"prize is 20 BTC")
    return False, ""


def classify_everfunded(phrase, funded_count, funded_sats, balance_sats):
    """The ONE decision for an ever-funded hit. (is_decoy, reason).

    ORDER MATTERS, and getting it wrong hides the answer. classify()'s dust
    rule is for the CURRENT-BALANCE oracle, where a 0-balance address never
    appears at all. In the ever-funded context balance 0 is not dust -- it is
    what a prize that was funded and then swept looks like, and that is the
    single most important shape this oracle exists to see. So here:

      1. a famous phrase is a decoy regardless of numbers
      2. a many-deposits / nearly-all-swept / dust-left SHAPE is a public tip
         jar regardless of phrase
      3. everything else -- including funded once and swept once -- is a HIT
         to be read by hand

    The dust rule is deliberately NOT applied. The first wiring of record()
    applied classify(balance=bal) first, and a 20 BTC funded-once-swept-once
    case came back "decoy: dust: 0 sats". The selftest had tested the tip-jar
    function directly and never the sequence record() ran. This function IS
    that sequence, so the test and the code cannot diverge.
    """
    r = is_decoy_phrase(phrase)
    if r:
        return True, r
    if looks_like_public_tip_jar(funded_count, funded_sats, balance_sats):
        return True, (f"public tip-jar shape: {funded_count} deposits, "
                      f"{100*(1-balance_sats/max(funded_sats,1)):.0f}% swept, "
                      f"{balance_sats} sats left")
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

    # REGRESSION: the genesis coinbase headline -- the second famous-brainwallet
    # false positive this project produced -- must classify as a decoy in the
    # exact form the transcript and candidate corpora carry it.
    g = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
    d8, why8 = classify(phrase=g)
    ok &= d8
    sys.stderr.write(f"  the genesis coinbase headline is a decoy: "
                     f"{'OK' if d8 else 'FAIL'}\n")

    # the STRUCTURAL rule: a drained public tip jar fires on chain shape alone,
    # with no phrase list at all -- and a held prize does not.
    # 1Nbm3Jo...: 3,862,600 sats received across many deposits, ~0 left
    tj = looks_like_public_tip_jar(funded_count=47, funded_sats=3_862_600,
                                   balance_sats=0)
    ok &= tj
    sys.stderr.write(f"  47 deposits, 100% swept, 0 left -> public tip jar: "
                     f"{'OK' if tj else 'FAIL'}\n")
    held = looks_like_public_tip_jar(funded_count=1, funded_sats=2_000_000_000,
                                     balance_sats=2_000_000_000)
    ok &= not held
    sys.stderr.write(f"  1 deposit of 20 BTC, still held -> NOT a tip jar: "
                     f"{'OK' if not held else 'FAIL — would suppress a solve'}\n")
    # the dangerous middle case: a prize that WAS 20 BTC and got swept once by
    # its rightful solver. One deposit, one sweep. Must NOT be called a tip jar
    # -- funded_count=1 keeps it clear of the many-deposits shape.
    swept_once = looks_like_public_tip_jar(funded_count=1,
                                           funded_sats=2_000_000_000,
                                           balance_sats=0)
    ok &= not swept_once
    sys.stderr.write(f"  20 BTC funded once and swept once -> NOT a tip jar "
                     f"(that is the claimed-prize shape): "
                     f"{'OK' if not swept_once else 'FAIL — would hide the answer'}\n")
    # END-TO-END through the exact function everfunded.record() calls. These
    # are the tests that would have caught the dust-rule bug.
    art = "They are the sum of all our neuroses."
    e1, w1 = classify_everfunded(art, 1, 2_000_000_000, 0)
    ok &= not e1
    sys.stderr.write(f"  EVERFUNDED: 20 BTC funded once, swept once -> HIT "
                     f"(the claimed-prize shape): "
                     f"{'OK' if not e1 else 'FAIL - ' + w1}\n")
    e2, _ = classify_everfunded(art, 1, 2_000_000_000, 2_000_000_000)
    ok &= not e2
    sys.stderr.write(f"  EVERFUNDED: 20 BTC held -> HIT: {'OK' if not e2 else 'FAIL'}\n")
    e3, w3 = classify_everfunded("password", 28099, 35_670_000, 0)
    ok &= e3
    sys.stderr.write(f"  EVERFUNDED: sha256('password') 28,099 deposits -> decoy: "
                     f"{'OK' if e3 else 'FAIL'}\n")
    e4, w4 = classify_everfunded("some novel phrase", 47, 3_862_600, 0)
    ok &= e4 and "tip-jar" in w4
    sys.stderr.write(f"  EVERFUNDED: unknown phrase, 47 deposits 100% swept -> "
                     f"tip jar by shape alone: {'OK' if e4 else 'FAIL'}\n")
    e5, _ = classify_everfunded("some novel phrase", 2, 50_000_000, 0)
    ok &= not e5
    sys.stderr.write(f"  EVERFUNDED: unknown phrase, 2 deposits swept -> HIT "
                     f"(too few deposits to be a tip jar): "
                     f"{'OK' if not e5 else 'FAIL'}\n")

    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    sys.stderr.write("\n  SELFTEST\n")
    sys.exit(0 if selftest() else 1)
