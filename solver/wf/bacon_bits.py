#!/usr/bin/env python3
"""
Every reading of the whole-word typographic bit string, against both oracles.

Input: the clean per-word bit strings produced by parse_typography.py from the
vision typography (1,282 words, 430 whole-word bold = 33.5%). Whole-word bold
is the one typographic signal that survives ~215 dpi: per-CHARACTER calls track
glyph identity, not weight, as established independently three ways.

Readings tested, for bold and emph, whole article and per page, forward and
mirrored (the "mirror writing" clue), both bit polarities:
  1. Bacon decode -> plaintext: 24- and 26-letter alphabets, all 5 phases,
     MSB and LSB first. Decoded text is scored for English, WIF-checked, and
     run through the brainwallet hashes.
  2. bits -> bytes -> every sliding 32-byte private key window at every one of
     the 8 bit phases.
  3. bits -> 11-bit BIP-39 word indices -> checksum-valid mnemonics -> HD.
  4. the bit string itself, its hex, and its run-length sequence, as passphrases.

Oracles: the April-2023 rich list (in memory) AND the full 56.8M funded index.
Controls printed at the end: a Bacon round trip, a known brainwallet address
recovered by the same phrase path, and the oracle finding the genesis coinbase.
"""
import os, sys, itertools, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from hd_sweep import direct_keys

BACON24 = "ABCDEFGHIKLMNOPQRSTUWXYZ"      # i/j, u/v share
BACON26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

O = H.Oracle(use_full=False)        # in-memory rich list; full index batched later
HITS = []
N = {"addr": 0, "phrase": 0, "key": 0}
BEST = []
PENDING = []                        # (tag, priv) queued for the batched full-index pass


def check_priv(tag, k):
    N["key"] += 1
    PENDING.append((tag, k))
    for t, a in O.check_priv(k):
        N["addr"] += 1
        HITS.append((tag, t, a, k.hex()))
        print("*** HIT(richlist)", tag, t, a, k.hex(), flush=True)


def flush_full_index():
    """One vectorized pass over the full 56.8M index for everything queued."""
    full = H.full_index()
    if full is None:
        print("full index unavailable; rich-list results only")
        return
    from index_oracle import spk_from_address
    B = 20000
    for s in range(0, len(PENDING), B):
        chunk = PENDING[s:s + B]
        spks, meta = [], []
        for tag, k in chunk:
            for t, a in H.addrs_for_priv(k).items():
                spk = spk_from_address(a)
                if spk is not None:
                    spks.append(spk)
                    meta.append((tag, t, a, k))
        for j, bal in full.contains_spks(spks):
            tag, t, a, k = meta[j]
            HITS.append((tag, t, a, k.hex(), bal))
            print(f"*** HIT(fullindex) {tag} {t} {a} {k.hex()} {bal/1e8:.8f} BTC", flush=True)
        print(f"  full-index batch {s//B + 1}: {len(spks)} scriptPubKeys checked", flush=True)


def check_phrase(tag, s):
    s = s.strip()
    if not (3 <= len(s) <= 4000):
        return
    N["phrase"] += 1
    for name, k in direct_keys(s).items():
        check_priv(f"{tag}|{name}", k)


def check_wif(tag, s):
    import re
    for m in re.findall(r"[1-9A-HJ-NP-Za-km-z]{51,52}", s):
        r = H.wif_check(m)
        if r:
            HITS.append((tag, "WIF", m, r[1].hex()))
            print("*** HIT WIF", tag, m, r[1].hex(), flush=True)


def bacon(bits, alpha, phase, msb):
    out = []
    for i in range(phase, len(bits) - 4, 5):
        g = bits[i:i + 5]
        if not msb:
            g = g[::-1]
        v = int("".join(map(str, g)), 2)
        out.append(alpha[v] if v < len(alpha) else "?")
    return "".join(out)


def to_bytes(bits):
    return bytes(int("".join(map(str, bits[i:i + 8])), 2)
                 for i in range(0, len(bits) - 7, 8))


def bip39_idx(tag, bits):
    if len(bits) < 132:
        return
    idx = [int("".join(map(str, bits[i:i + 11])), 2)
           for i in range(0, len(bits) - 10, 11)]
    for L in (12, 24):
        for s in range(len(idx) - L + 1):
            ws = [H.BIP39[j] for j in idx[s:s + L]]
            if H.bip39_valid(ws):
                m = " ".join(ws)
                print("  checksum-valid mnemonic:", m, flush=True)
                for p, t, a, k in H.bip39_addrs(m, ""):
                    N["key"] += 1
                    if O.funded(a):
                        HITS.append((tag, "bip39", a, k.hex()))
                        print("*** HIT bip39", tag, m, a, flush=True)


def run(name, bits):
    for pol, bb in (("pos", bits), ("inv", [1 - b for b in bits])):
        # 1. Bacon
        for an, alpha in (("b24", BACON24), ("b26", BACON26)):
            for ph in range(5):
                for msb in (True, False):
                    txt = bacon(bb, alpha, ph, msb)
                    tag = f"{name}:{pol}:{an}:ph{ph}:{'M' if msb else 'L'}"
                    check_wif(tag, txt)
                    check_phrase(tag, txt)
                    try:
                        z = H.englishness_z(txt)[0]
                        BEST.append((z, tag, txt[:90]))
                    except Exception:
                        pass
        # 2. bytes -> 32-byte key windows, all bit phases
        for order, base in (("fwd", bb), ("rev", bb[::-1])):
            for ph in range(8):
                b = to_bytes(base[ph:])
                for off in range(0, max(0, len(b) - 31)):
                    check_priv(f"{name}:{pol}:{order}:ph{ph}:off{off}", b[off:off + 32])
            check_phrase(f"{name}:{pol}:{order}:hex", to_bytes(base).hex())
        # 3. BIP-39 indices
        bip39_idx(f"{name}:{pol}:bip39idx", bb)
        # 4. bit string / run lengths as passphrases
        check_phrase(f"{name}:{pol}:bitstr", "".join(map(str, bb)))
        rl = [len(list(g)) for _, g in itertools.groupby(bb)]
        check_phrase(f"{name}:{pol}:runs", "".join(map(str, rl)))
        check_phrase(f"{name}:{pol}:runsA", "".join(chr(96 + min(26, x)) for x in rl))


def main():
    t0 = time.time()
    for mode in ("bold", "emph"):
        p = f"/tmp/bits_{mode}.txt"
        if not os.path.exists(p):
            print("missing", p); continue
        s = open(p).read().strip()
        bits = [int(c) for c in s]
        print(f"=== {mode}: {len(bits)} bits, {sum(bits)} set ===", flush=True)
        run(mode, bits)
        run(mode + "_mirror", bits[::-1])
    print(f"\nkeys derived {N['key']}, phrases {N['phrase']}, elapsed {time.time()-t0:.0f}s")
    print(f"batch-checking {len(PENDING)} keys against the full 56.8M index...", flush=True)
    flush_full_index()
    print(f"full-index pass done, elapsed {time.time()-t0:.0f}s")
    # controls
    enc = "".join(format(BACON26.index(c), "05b") for c in "HELLO")
    ok1 = bacon([int(x) for x in enc], BACON26, 0, True) == "HELLO"
    kk = hashlib.sha256(b"correct horse battery staple").digest()
    ok2 = H.addrs_for_priv(kk)["p2pkh_u"] == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    ok3 = O.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"CONTROLS: bacon_roundtrip={ok1} phrase_path_derives_known_addr={ok2} oracle_genesis={ok3}")
    BEST.sort(reverse=True)
    print("\ntop English-trigram z-scores over all Bacon decodes (prose control ~ +70, noise |z|<5):")
    for z, tag, t in BEST[:8]:
        print(f"  z={z:+6.2f}  {tag}  {t}")
    print("HITS:", len(HITS))
    for h in HITS:
        print("  ", h)


if __name__ == "__main__":
    main()
