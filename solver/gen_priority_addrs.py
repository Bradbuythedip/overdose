#!/usr/bin/env python3
"""
A RANKED address list for the ever-funded API oracle.

WHY RANKING IS THE WHOLE PROBLEM NOW
everfunded.py works — its control passed against a live endpoint, reporting
sha256("correct horse battery staple") as having received 15.9472 BTC and
holding 0.0000 today, which is precisely the history both offline indices are
blind to. But an API does roughly 345k addresses a day at 4 req/s and this
project has generated ~150M. Dumping them is not an option; choosing is.

THE KEY ECONOMY
The offline sweeps derive ~1,835 addresses per phrase (7 direct key hashes plus
5 seed derivations over 72 HD paths, times 5 script types) because locally that
costs nothing. Over an API it costs everything. But a BRAINWALLET — the
mechanism a non-cryptographer would actually use, and the one Keiser's "hidden
in the text" implies — is just:

    sha256(phrase) -> private key -> P2PKH

Two addresses per phrase, compressed and uncompressed. That is a 900x saving,
and it covers the single most likely derivation completely.

TIERS, most likely first, so an interrupted run has still tested the best
candidates:

  1  the article's own memorable strings: title, byline, headline, every
     sentence, every paragraph, the highlight-bar runs, the isolated bold words
  2  every 2..12 word n-gram of the body, as printed and lowercased
  3  the banknote serial in its readings, and the entropy tilings of it
  4  the whole article as one string, in several joinings

Each address is emitted with its provenance so a hit is attributable, and the
manifest is written alongside the plain list everfunded.py --addresses eats.

  python3 gen_priority_addrs.py --selftest
  python3 gen_priority_addrs.py --max 60000
"""
import argparse, hashlib, re, sys

from coincurve import PrivateKey

from hd_sweep import h160
from everfunded import b58check, b58decode_h160

SERIAL = "CL76841714A"
DIGITS = "76841714"


def addrs_for_phrase(p):
    """The brainwallet reading: sha256 -> P2PKH, both pubkey forms."""
    k = hashlib.sha256(p.encode("utf-8")).digest()
    if not (0 < int.from_bytes(k, "big") <
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141):
        return []
    pub = PrivateKey(k).public_key
    return [b58check(b"\x00" + h160(pub.format(compressed=c)))
            for c in (False, True)]


def load():
    raw = open("article_transcript.txt", encoding="utf-8").read()
    raw = re.sub(r"^#.*$", "", raw, flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    paras, sents, lines = [], [], []
    for _n, body in zip(it, it):
        for block in re.split(r"\n\s*\n", body):
            ls = [l.strip() for l in block.splitlines() if l.strip()]
            if not ls:
                continue
            lines.extend(ls)
            flat = " ".join(ls)
            paras.append(flat)
            for s in re.split(r"(?<=[.!?])\s+", flat):
                if len(re.findall(r"[A-Za-z]", s)) > 1:
                    sents.append(s.strip())
    return lines, sents, paras


def tiers(maxn):
    lines, sents, paras = load()
    words = " ".join(paras).split()
    t = []

    def add(tier, why, phrases):
        for p in phrases:
            p = p.strip()
            if p:
                t.append((tier, why, p))

    add(1, "sentence", sents)
    add(1, "sentence_lower", [s.lower() for s in sents])
    add(1, "paragraph", paras)
    add(1, "line", lines)
    add(1, "furniture", [
        "BITCOIN IS TOXIC AF", "Bitcoin Is Toxic AF", "bitcoin is toxic af",
        "OVERDOSE", "Overdose", "overdose", "MAX KEISER", "Max Keiser",
        "with Max Keiser", "ORANGEPILL", "orangepill",
        "THE EL SALVADOR ISSUE", "El Salvador", "el salvador",
        "The numbers don't lie.", "right there in the Genesis Block.",
        "Look, toxicity is Layer 1 of the protocol.",
        "the Layer 1 of the whole Satoshi experience.",
        "We've seen some shit.", "Don't believe me?",
        "A monetary defibrillator to the treasure chest.",
    ])

    add(3, "serial", [
        SERIAL, SERIAL.lower(), DIGITS, DIGITS[::-1], SERIAL[::-1],
        "L12", "CL 76841714 A", DIGITS + "L12", "CL76841714A L12",
    ])
    # entropy tilings: the digits repeated to fill a 32-byte key
    for src in (DIGITS, DIGITS[::-1]):
        t.append((3, "tiled_hexkey", None))
        t[-1] = (3, "tiled_hexkey:" + src, "\x00HEX" + (src * 8)[:64])

    for n in range(2, 13):
        for i in range(len(words) - n + 1):
            g = " ".join(words[i:i + n])
            t.append((2, f"ngram{n}", g))
            t.append((2, f"ngram{n}_lower", g.lower()))

    add(4, "whole", [" ".join(paras), " ".join(paras).lower(),
                     "\n".join(lines), " ".join(sents)])

    t.sort(key=lambda x: x[0])
    return t[:maxn] if maxn else t


def selftest():
    """Derivation must match everfunded's own control table."""
    from everfunded import SWEPT_CONTROLS
    ok = True
    for p, u, c in SWEPT_CONTROLS:
        got = addrs_for_phrase(p)
        good = got == [u, c]
        ok &= good
        sys.stderr.write(f"  {p!r:34} -> {got[0]} / {got[1]}  "
                         f"{'OK' if good else 'MISMATCH'}\n")
    a = addrs_for_phrase("satoshi")
    ok &= all(b58decode_h160(x) is not None for x in a)
    sys.stderr.write(f"  emitted addresses decode as valid Base58Check: "
                     f"{'OK' if ok else 'FAIL'}\n")
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=60000,
                    help="cap on ADDRESSES emitted (2 per phrase)")
    ap.add_argument("--out", default="everfunded_priority.txt")
    ap.add_argument("--manifest", default="everfunded_priority_manifest.tsv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not selftest():
        sys.exit("derivation disagrees with the control table; refusing")
    if a.selftest:
        return

    seen, rows = set(), []
    for tier, why, p in tiers(0):
        if p is None:
            continue
        if p.startswith("\x00HEX"):
            k = bytes.fromhex(p[4:])
            pub = PrivateKey(k).public_key
            ads = [b58check(b"\x00" + h160(pub.format(compressed=c)))
                   for c in (False, True)]
            label = p[4:]
        else:
            ads = addrs_for_phrase(p)
            label = p
        for ad in ads:
            if ad in seen:
                continue
            seen.add(ad)
            rows.append((tier, why, label[:120], ad))
            if len(rows) >= a.max:
                break
        if len(rows) >= a.max:
            break

    with open(a.out, "w") as fh:
        for _t, _w, _p, ad in rows:
            fh.write(ad + "\n")
    with open(a.manifest, "w", encoding="utf-8") as fh:
        fh.write("tier\twhy\tphrase\taddress\n")
        for t_, w_, p_, ad in rows:
            fh.write(f"{t_}\t{w_}\t{p_}\t{ad}\n")

    bytier = {}
    for t_, _w, _p, _a in rows:
        bytier[t_] = bytier.get(t_, 0) + 1
    sys.stderr.write(f"\n  {len(rows):,} unique addresses -> {a.out}\n")
    for t_ in sorted(bytier):
        sys.stderr.write(f"    tier {t_}: {bytier[t_]:,}\n")
    sys.stderr.write(f"  provenance -> {a.manifest}\n")
    sys.stderr.write(f"  at 4 req/s that is about "
                     f"{len(rows)/4/3600:.1f} hours\n")


if __name__ == "__main__":
    main()
