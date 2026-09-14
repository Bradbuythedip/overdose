#!/usr/bin/env python3
"""
Exhaust the KEYWORD SPACE of the article's classical ciphers.

WHAT classical_cipher.py SETTLED, AND WHAT IT LEFT OPEN
That script ran Vigenere, Beaufort and autokey over the article keyed on 20
hand-picked clue words and reported the best englishness at z = +3.45, against
a scorer its own control proves would have read a correct decryption at about
+20. That is a powered null and those 20 keywords are dead.

But 20 keywords is not the keyword space. If Keiser keyed a cipher on a word,
the word is far likelier to be IN THE COLUMN than in a list I guessed. This
sweeps every word of the article, every adjacent word pair and triple joined,
the cover strings and the banknote serial — tens of thousands of keys — across
the same ciphers and scopes.

THE NULL IS THE SWEEP ITSELF
A shuffle null asks "is this text more English than its own letters
rearranged". That is not the operation being performed. The operation is
"decrypt this text with some key", so the null is the score distribution of
that same operation under every OTHER key — which a sweep of this size
produces for free, at no extra cost and with no modelling assumption. Each
key's z is measured against the empirical mean and sd of its own (scope,
cipher) cell.

THE NORMAL APPROXIMATION IS NOT A USABLE YARDSTICK HERE, AND THAT MATTERS
The first version of this script judged the best key against the expected
maximum of N standard normal draws — +3.38 for 2,511 keys. Six cells beat it
and it printed "SOMETHING EXCEEDS THE NULL". All six were noise. The trigram
rate is a heavily right-skewed count statistic, so its maximum runs far above
the Gaussian prediction: shuffling every key's letters, which preserves length
and letter composition and destroys only word identity, produces maxima of
+8.6 to +16.4. The real keys reach +7.3 — BELOW every null draw.

So the null is generated, not assumed. It costs a dozen extra sweeps and it is
the difference between this script reporting a discovery and reporting the
truth.

POWER CONTROL
A known plaintext is encrypted under a key that is in the search set and
injected as an extra scope. If the sweep does not recover that key at the top
of its cell, the sweep is underpowered and its nulls mean nothing; the script
says so and refuses to report them as negative.

  python3 cipher_mine.py --selftest
  python3 cipher_mine.py
"""
import argparse, os, re, sys

import numpy as np

from englishness import TRIGRAMS, letters

A = ord("a")


def trigram_table():
    """Boolean lookup over all 17,576 three-letter windows.

    Only the 3-character entries of TRIGRAMS can ever match a 3-character
    window, so the longer entries in that set are inert in englishness.score
    and dropping them changes nothing. selftest asserts the equivalence rather
    than asserting the reasoning.
    """
    t = np.zeros(26 ** 3, dtype=bool)
    for g in TRIGRAMS:
        if len(g) == 3:
            a, b, c = (ord(ch) - A for ch in g)
            t[a * 676 + b * 26 + c] = True
    return t


TBL = trigram_table()


def to_ints(s):
    return np.frombuffer(letters(s).encode(), dtype=np.uint8).astype(np.int16) - A


def rate(arr):
    """Trigram rate of each row of a (K, N) int array of 0..25."""
    if arr.shape[1] < 3:
        return np.zeros(arr.shape[0])
    idx = arr[:, :-2] * 676 + arr[:, 1:-1] * 26 + arr[:, 2:]
    return TBL[idx].sum(axis=1) / (arr.shape[1] - 2)


def decrypt_batch(text, keys, lens, cipher):
    """(K, N) plaintexts for K keys against one text. keys is (K, Lmax)."""
    n = len(text)
    pos = np.arange(n)
    # gather each key's stream position: keys[k, pos % len_k]
    col = pos[None, :] % lens[:, None]
    tiled = np.take_along_axis(keys, col, axis=1)
    if cipher == "vigenere":
        return (text[None, :] - tiled) % 26
    if cipher == "vigenere_enc":
        return (text[None, :] + tiled) % 26
    if cipher == "beaufort":
        return (tiled - text[None, :]) % 26
    raise ValueError(cipher)


CIPHERS = ("vigenere", "vigenere_enc", "beaufort")


def keyspace(pages, extra=()):
    """Every word, adjacent pair and triple of the article, plus the strings a
    reader of the issue would have in hand."""
    words = []
    for _n, t in pages:
        words += [w for w in re.findall(r"[a-z]+", t.lower()) if 3 <= len(w) <= 20]
    keys = set(words)
    for i in range(len(words) - 1):
        keys.add(words[i] + words[i + 1])
    for i in range(len(words) - 2):
        keys.add(words[i] + words[i + 1] + words[i + 2])
    keys |= {
        "elsalvador", "salvador", "elzonte", "bukele", "nayibbukele",
        "overdose", "maxkeiser", "keiser", "stacyherbert", "mirror",
        "mirrorwriting", "georgesand", "sand", "bitcoin", "toxic",
        "hyperbitcoinized", "volcano", "volcanobonds", "twentybtc", "satoshi",
        "cla", "clbwq", "bitcoinmagazine", "orangepill", "theelsalvadorissue",
        "bitcoinistoxicaf", "twentybitcoin", "monetarydefibrillator",
    }
    keys |= set(extra)
    keys = sorted(k for k in keys if 3 <= len(k) <= 24)
    lens = np.array([len(k) for k in keys], dtype=np.int64)
    lmax = int(lens.max())
    arr = np.zeros((len(keys), lmax), dtype=np.int16)
    for i, k in enumerate(keys):
        arr[i, :len(k)] = to_ints(k)
    return keys, arr, lens


def sweep(scopes, keys, karr, lens, prefix, chunk=4000):
    """Yield (scope, cipher, scores) with scores aligned to keys."""
    for tag, text in scopes:
        t = to_ints(text)[:prefix]
        if len(t) < 200:
            continue
        for c in CIPHERS:
            out = np.empty(len(keys))
            for i in range(0, len(keys), chunk):
                sl = slice(i, i + chunk)
                out[sl] = rate(decrypt_batch(t, karr[sl], lens[sl], c))
            yield tag, c, out


def expected_max_z(n):
    """Expected maximum of n standard normal draws, to the usual approximation."""
    import math
    if n < 2:
        return 0.0
    ln = math.log(n)
    return math.sqrt(2 * ln) - (math.log(ln) + math.log(4 * math.pi)) / (
        2 * math.sqrt(2 * ln))


def shuffled_null(scopes, keys, prefix, draws, seed=11):
    """Max z and max raw rate reachable by keys that are definitely wrong.

    Each draw shuffles the letters WITHIN every key. Length and letter
    composition are preserved exactly; only the identity of the word is
    destroyed. So a difference between this and the real sweep can only be
    attributable to the keys being real words of the article, which is the
    claim under test.
    """
    import random
    rng = random.Random(seed)
    zs, raws = [], []
    for _ in range(draws):
        sh = []
        for k in keys:
            c = list(k)
            rng.shuffle(c)
            sh.append("".join(c))
        lm = max(len(k) for k in sh)
        arr = np.zeros((len(sh), lm), dtype=np.int16)
        for i, k in enumerate(sh):
            arr[i, :len(k)] = to_ints(k)
        ln = np.array([len(k) for k in sh], dtype=np.int64)
        bz, br = -99.0, 0.0
        for _t, _c, sc in sweep(scopes, sh, arr, ln, prefix):
            sd = sc.std(ddof=1)
            if sd:
                bz = max(bz, float(((sc - sc.mean()) / sd).max()))
            br = max(br, float(sc.max()))
        zs.append(bz)
        raws.append(br)
    return zs, raws


def load_pages(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it, pages = iter(parts[1:]), []
    for num, body in zip(it, it):
        pages.append((num, " ".join(l.strip() for l in body.splitlines()
                                    if l.strip())))
    return pages


def selftest():
    import random
    from englishness import score
    ok = True

    # the vectorized scorer must equal the one the rest of the repo uses
    rng = random.Random(3)
    s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(4000))
    s = s[:2000] + "thenationandtheprotocolforhertheresomething" + s[2000:]
    mine = float(rate(to_ints(s)[None, :])[0])
    theirs = score(letters(s))
    same = abs(mine - theirs) < 1e-12
    ok &= same
    sys.stderr.write(f"  vectorized rate {mine:.8f} == englishness.score "
                     f"{theirs:.8f}: {'OK' if same else 'FAIL'}\n")

    # ciphers must agree with the scalar implementations already in the repo
    import classical_cipher as CC
    plain = "thequickbrownfoxjumpsoverthelazydog" * 20
    key = "elsalvador"
    ct = CC.vigenere(plain, key, decrypt=False)
    ka = np.zeros((1, len(key)), dtype=np.int16)
    ka[0] = to_ints(key)
    la = np.array([len(key)])
    got = decrypt_batch(to_ints(ct), ka, la, "vigenere")[0]
    back = "".join(chr(A + int(v)) for v in got)
    agree = back == plain
    ok &= agree
    sys.stderr.write(f"  vectorized vigenere == classical_cipher.vigenere: "
                     f"{'OK' if agree else 'FAIL'}\n")
    gb = decrypt_batch(to_ints(plain), ka, la, "beaufort")[0]
    bb = "".join(chr(A + int(v)) for v in gb)
    ab = bb == CC.beaufort(plain, key)
    ok &= ab
    sys.stderr.write(f"  vectorized beaufort == classical_cipher.beaufort: "
                     f"{'OK' if ab else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default="article_transcript.txt")
    ap.add_argument("--prefix", type=int, default=1500,
                    help="letters of each scope scored; longer is more stable")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--nulls", type=int, default=12,
                    help="shuffled-key null draws; the verdict rests on these")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("refusing to run: the vectorized core disagrees with the "
                 "scalar implementations it is supposed to replace")
    if a.selftest:
        return

    pages = load_pages(a.transcript)
    keys, karr, lens = keyspace(pages)
    scopes = [("ALL", " ".join(t for _, t in pages))]
    scopes += [(f"p{n}", t) for n, t in pages]

    # POWER CONTROL: a real English plaintext encrypted under a key that is in
    # the search set, injected as its own scope.
    import classical_cipher as CC
    planted_key = keys[len(keys) // 2]
    body = " ".join(t for _, t in pages)
    plant = CC.vigenere(letters(body)[:a.prefix + 50], planted_key,
                        decrypt=False)
    scopes.append(("PLANT", plant))

    sys.stderr.write(f"\n  {len(keys):,} keys x {len(CIPHERS)} ciphers x "
                     f"{len(scopes)} scopes = "
                     f"{len(keys)*len(CIPHERS)*len(scopes):,} decryptions\n")
    sys.stderr.write(f"  power control: scope PLANT is the article encrypted "
                     f"under key {planted_key!r}\n\n")

    best, raws, plant_rank, plant_z = [], [], None, None
    for tag, cipher, sc in sweep(scopes, keys, karr, lens, a.prefix):
        m, sd = sc.mean(), sc.std(ddof=1)
        if sd == 0:
            continue
        z = (sc - m) / sd
        order = np.argsort(z)[::-1]
        if tag != "PLANT":
            raws.append(float(sc.max()))
        if tag == "PLANT" and cipher == "vigenere":
            r = int(np.where(np.array(keys)[order] == planted_key)[0][0])
            plant_rank, plant_z = r + 1, float(z[order[r]])
        best.append((float(z[order[0]]), tag, cipher, keys[order[0]],
                     [(keys[i], float(z[i])) for i in order[:3]]))

    ntr = len(keys)
    ok = plant_rank == 1 and plant_z is not None and plant_z > 20
    sys.stderr.write(f"  POWER CONTROL: planted key ranked {plant_rank} of "
                     f"{ntr:,} at z = {plant_z:+.1f}\n")
    verdict = ("PASS - a correct key is plainly visible in this design"
               if ok else "FAIL - this sweep cannot see a correct key, so "
                          "the nulls below are meaningless")
    sys.stderr.write(f"    {verdict}\n\n")

    best = [b for b in best if b[1] != "PLANT"]
    best.sort(reverse=True)
    top = best[0][0] if best else 0.0
    topraw = max(raws) if raws else 0.0

    nz, nraw = shuffled_null(scopes, keys, a.prefix, a.nulls)
    sys.stderr.write(f"  top cells by best-in-cell z:\n")
    for z, tag, c, k, tops in best[:a.top]:
        sys.stderr.write(f"    {tag:5} {c:13} best z={z:+5.2f} {k!r}\n")
        sys.stderr.write("          runners-up: " + ", ".join(
            f"{kk}({zz:+.2f})" for kk, zz in tops[1:]) + "\n")

    import statistics as st
    sys.stderr.write(
        f"\n  EMPIRICAL NULL, {a.nulls} draws of the same keys with their "
        f"letters shuffled:\n"
        f"    max z    null {st.mean(nz):+.2f} "
        f"(range {min(nz):+.2f}..{max(nz):+.2f})   article keys {top:+.2f}\n"
        f"    max rate null {st.mean(nraw):.5f} "
        f"(range {min(nraw):.5f}..{max(nraw):.5f})   article keys "
        f"{topraw:.5f}\n")
    beat = sum(1 for v in nz if v < top)
    sys.stderr.write(f"    article keys beat {beat} of {a.nulls} null draws\n")
    sys.stderr.write(f"    normal approximation would have predicted "
                     f"{expected_max_z(ntr):+.2f} — it is not applicable to a "
                     f"statistic this skewed\n")

    plain = float(rate(to_ints(scopes[0][1])[None, :a.prefix])[0])
    sys.stderr.write(f"    for scale, real English (the article itself) "
                     f"scores {plain:.5f}\n  ")
    if not ok:
        sys.stderr.write("NO VERDICT: the power control failed\n")
    elif beat > a.nulls * 0.9:
        sys.stderr.write("SOMETHING EXCEEDS THE NULL — inspect by hand\n")
    else:
        sys.stderr.write(
            f"NO KEYWORD IN THE ARTICLE DECRYPTS IT. The best of "
            f"{ntr*len(CIPHERS)*(len(scopes)-1):,} decryptions is at or below "
            f"what shuffled keys reach, and {plain/max(topraw,1e-9):.0f}x short "
            f"of English.\n")


if __name__ == "__main__":
    main()
