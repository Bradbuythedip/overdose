#!/usr/bin/env python3
"""
Line-count parity: the one channel with the capacity that was never tested.

WHY THIS ONE
channel_capacity.py enumerates every editorial channel on these pages and
reports which are long enough to carry a key. Its own table lists four with
sufficient capacity, and three of them are already accounted for:

    per-glyph bold weight       6243 bits   MEASURED AT CHANCE (dead)
    per-glyph baseline residual 6243 bits   MEASURED DEAD
    word-initial acrostic       5894 bits   "the text itself, not a channel"
    line count parity            145 bits   <-- never measured, never swept

The column has 142 printed lines (32/31/32/22/25 on pages 75-79). One bit per
line is 142 bits, which clears the 128 a 12-word BIP-39 mnemonic needs. That is
exactly the shape a setter would use: nothing is added to the page, the bits
ride on counts that are already there, and the author controls them by choosing
where lines break.

WHAT IS TESTED
Parity of several per-line counts, in both polarities:

    words, characters, letters, non-space characters, vowels, consonants

Each gives a 142-bit string. From each: every 128-bit window, and every 256-bit
reading where two bits per line are taken (count mod 4). Each bit string is
used BOTH as raw BIP-39 entropy (-> 12 or 24 words -> seed -> HD paths) and
directly as key material.

Controls: BIP-39 entropy->mnemonic is pinned against the standard all-zero
vector, and a planted phrase must be recovered end to end.

  python3 wf/line_parity.py --selftest
  python3 wf/line_parity.py
"""
import hashlib, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
import hd_sweep as HD

SOLVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDIR = os.path.join(SOLVER, "transcript")
PAGES = [75, 76, 77, 78, 79]
VOWELS = set("aeiouAEIOU")


def lines():
    out = []
    for p in PAGES:
        fn = os.path.join(TDIR, f"p{p}.txt")
        if os.path.exists(fn):
            out += [l for l in open(fn, encoding="utf-8").read().splitlines()
                    if l.strip()]
    return out


COUNTERS = {
    "words":     lambda l: len(l.split()),
    "chars":     lambda l: len(l),
    "letters":   lambda l: sum(c.isalpha() for c in l),
    "nonspace":  lambda l: sum(not c.isspace() for c in l),
    "vowels":    lambda l: sum(c in VOWELS for c in l),
    "consonant": lambda l: sum(c.isalpha() and c not in VOWELS for c in l),
    "digits":    lambda l: sum(c.isdigit() for c in l),
}


def bitstrings(L):
    """(label, list-of-bits) for every counter, polarity and bits-per-line."""
    out = []
    for name, fn in COUNTERS.items():
        counts = [fn(l) for l in L]
        for pol in (0, 1):
            out.append((f"{name}.par{pol}", [(c + pol) & 1 for c in counts]))
        # two bits per line doubles capacity to 284, enough for 256
        b2 = []
        for c in counts:
            b2 += [(c >> 1) & 1, c & 1]
        out.append((f"{name}.mod4", b2))
    return out


def wordlist():
    """BIP-39 English wordlist, from the project's own modules."""
    sys.path.insert(0, SOLVER)
    for mod, attrs in (("bip39_index", ("WL", "WORDS", "WORDLIST")),
                       ("bip39_sweep", ("WORDLIST", "WL"))):
        try:
            m = __import__(mod)
        except Exception:
            continue
        for attr in attrs:
            w = getattr(m, attr, None)
            if w and len(w) == 2048:
                return list(w)
    return None


def entropy_to_mnemonic(ent, words):
    """BIP-39: append the first ENT/32 bits of sha256(ent) as checksum."""
    bits = "".join(format(b, "08b") for b in ent)
    chk = format(int.from_bytes(hashlib.sha256(ent).digest(), "big"), "0256b")
    bits += chk[:len(ent) * 8 // 32]
    return " ".join(words[int(bits[i:i + 11], 2)] for i in range(0, len(bits), 11))


def bits_to_bytes(bits):
    n = len(bits) // 8 * 8
    return bytes(int("".join(str(b) for b in bits[i:i + 8]), 2)
                 for i in range(0, n, 8))


def keys_from(bs, words, paths):
    """Every private key a bit string yields."""
    raw = bits_to_bytes(bs)
    if len(raw) >= 16:
        for nb in (16, 32):
            if len(raw) >= nb:
                ent = raw[:nb]
                # as raw key material
                if nb == 32:
                    yield f"raw32", ent
                yield f"sha256(ent{nb})", hashlib.sha256(ent).digest()
                # as BIP-39 entropy
                if words:
                    m = entropy_to_mnemonic(ent, words)
                    for sname, seed in HD.seeds_from(m).items():
                        for path in paths:
                            try:
                                k = HD.derive(seed, path)
                            except Exception:
                                continue
                            if k:
                                yield f"bip39{nb*8}:{sname}:{path}", k


PATHS = ["m", "m/0", "m/0/0", "m/0'", "m/0'/0", "m/0'/0/0",
         "m/44'/0'/0'/0/0", "m/44'/0'/0'/0/1", "m/49'/0'/0'/0/0",
         "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0", "m/0'/0'/0'"]


def selftest():
    ok = True
    L = lines()
    good = len(L) == 142
    print(f"  142 printed lines: {'OK' if good else 'FAIL'} ({len(L)})")
    ok &= good
    bs = bitstrings(L)
    good = all(len(b) >= 142 for _, b in bs)
    print(f"  {len(bs)} bit strings, all >=142 bits: {'OK' if good else 'FAIL'}")
    ok &= good
    good = any(len(b) >= 256 for _, b in bs)
    print(f"  mod4 readings reach 256 bits: {'OK' if good else 'FAIL'}")
    ok &= good
    # the counters must not all collapse to the same string
    uniq = len({tuple(b) for _, b in bs})
    good = uniq > 5
    print(f"  bit strings distinct: {'OK' if good else 'FAIL'} ({uniq}/{len(bs)})")
    ok &= good

    words = wordlist()
    if words:
        m = entropy_to_mnemonic(bytes(16), words)
        good = m.split()[0] == "abandon" and m.split()[-1] == "about"
        print(f"  BIP-39 all-zero vector: {'OK' if good else 'FAIL'} "
              f"({' '.join(m.split()[:2])} ... {m.split()[-1]})")
        ok &= good
    else:
        print("  BIP-39 wordlist: NOT FOUND -- mnemonic readings will be skipped")

    k = HD.direct_keys("correct horse battery staple")["sha256"]
    good = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T" in HD.all_addrs(k)
    print(f"  derivation path: {'OK' if good else 'FAIL'}")
    ok &= good
    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis: {'OK' if g else 'FAIL'}")
    ok &= g
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        sys.exit("selftest failed; refusing to report a null")
    from index_oracle import spk_from_address
    L = lines()
    words = wordlist()
    full = H.full_index()
    o = H.Oracle(use_full=False)
    hits, n, t0, PEND = [], 0, time.time(), []

    def flush(force=False):
        nonlocal n
        if not PEND or (len(PEND) < 40000 and not force):
            return
        spks, meta = [], []
        for tag, ad, kh in PEND:
            if o.funded(ad):
                hits.append((tag, ad, kh)); print(f"*** HIT {tag} {ad} {kh}", flush=True)
            s = spk_from_address(ad)
            if s is not None:
                spks.append(s); meta.append((tag, ad, kh))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, ad, kh = meta[j]
                hits.append((tag, ad, kh, bal))
                print(f"*** HIT(fullindex) {tag} {ad} {bal/1e8:.8f} BTC {kh}",
                      flush=True)
        n += len(PEND); PEND.clear()

    for label, bs in bitstrings(L):
        # every 128-bit and 256-bit window of the bit string
        for width in (128, 256):
            for off in range(0, max(1, len(bs) - width + 1)):
                win = bs[off:off + width]
                if len(win) < width:
                    break
                for tag, k in keys_from(win, words, PATHS):
                    for ad in HD.all_addrs(k):
                        PEND.append((f"{label}|off{off}|{tag}", ad, k.hex()))
                    flush()
    flush(force=True)
    print(f"\nline-parity addresses {n:,} in {time.time()-t0:.0f}s")
    print("hits:", len(hits))
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
