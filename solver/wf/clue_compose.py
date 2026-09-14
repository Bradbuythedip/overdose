#!/usr/bin/env python3
"""
Compose Keiser's three clues as a PROCEDURE, not as three separate hypotheses.

WHY THIS IS NEW
Keiser gave exactly three clues and this project tested each ALONE:

  George Sand's hidden cryptography  -> alternate-line readings      (tested)
  mirror writing (Schott PMC2117809) -> reversal / atbash            (tested)
  "Obviously, 'El Salvador' is a clue" -> passphrase, salt, Vigenere key (tested)

Nobody composed them. A setter who gives three clues usually means them to be
applied in sequence: take alternate lines, read the result in a mirror, key it
on El Salvador. Each stage alone produces garbage, which is exactly why each
was recorded as a null -- a composition is invisible to a search over its parts.

The user has since established from Keiser directly that the prize has NOT been
swept. That kills the oracle-blind-spot branch (window/working_backwards.md J1):
an unswept prize is still funded, so it IS inside the 56.8M currently-funded
index, and a correct derivation WOULD have fired. The answer therefore lies in
J2 (material we never searched) or J3 (derivation we never tried). This module
attacks J3.

It also folds in page 72, which entered the corpus only after the 8-page scan
was found and was absent from every earlier sweep.

  python3 wf/clue_compose.py --selftest
  python3 wf/clue_compose.py
"""
import hashlib, itertools, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H
from hd_sweep import direct_keys, CURVE_N

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLVER = os.path.join(ROOT, "solver")

P72 = ("165 WESTERN UNION LOCATIONS IN PALESTINE "
       "572 WESTERN UNION LOCATIONS IN EL SALVADOR "
       "In 2020, WESTERN UNION GENERATED REVENUE OF $4.8 BILLION "
       "The global REMITTANCE MARKET SIZE is projected to reach "
       "$930.44 BILLION BY 2026 Based on a compound annual growth rate of 3.9% "
       "The global DIGITAL REMITTANCE MARKET is estimated to reach "
       "$35.8 BILLION BY 2026 This is up from $14.5 BILLION BY 2019")

SALVADOR = ["El Salvador", "ElSalvador", "elsalvador", "EL SALVADOR",
            "ELSALVADOR", "el salvador", "sv", "SV", "572"]

A = ord('a')


def body_lines():
    t = open(os.path.join(SOLVER, "article_transcript.txt"),
             encoding="utf-8", errors="replace").read()
    t = t.split("=== PAGE 75")[-1]
    return [l.strip() for l in t.split("\n")
            if l.strip() and not l.startswith("===") and not l.startswith("#")]


def sentences(lines):
    txt = " ".join(lines)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", txt) if s.strip()]


# ------------------------------------------------------------------ SAND ----
def sand(units):
    """Alternate-unit readings: the George Sand device."""
    out = {}
    for step in (2, 3):
        for off in range(step):
            out[f"sand{step}_{off}"] = " ".join(units[off::step])
    out["sand_first_words"] = " ".join(u.split()[0] for u in units if u.split())
    out["sand_last_words"] = " ".join(u.split()[-1] for u in units if u.split())
    out["sand_initials"] = "".join(u.split()[0][0] for u in units if u.split())
    return out


# ---------------------------------------------------------------- MIRROR ----
ATBASH = {chr(A + i): chr(A + 25 - i) for i in range(26)}
FLIP = str.maketrans("bdpqnumw", "dbqpunwm")


def mirror(s):
    letters = "".join(c for c in s.lower() if c.isalpha())
    return {
        "mir_rev": s[::-1],
        "mir_words": " ".join(s.split()[::-1]),
        "mir_eachword": " ".join(w[::-1] for w in s.split()),
        "mir_atbash": "".join(ATBASH.get(c, c) for c in s.lower()),
        "mir_glyph": s.lower().translate(FLIP),
        "mir_letters_rev": letters[::-1],
    }


# -------------------------------------------------------------- SALVADOR ----
def vigenere(text, key, decrypt=True):
    t = [c for c in text.lower() if c.isalpha()]
    k = [c for c in key.lower() if c.isalpha()]
    if not k or not t:
        return ""
    out = []
    for i, c in enumerate(t):
        kv = ord(k[i % len(k)]) - A
        v = ord(c) - A
        out.append(chr(A + ((v - kv) % 26 if decrypt else (v + kv) % 26)))
    return "".join(out)


def salvador(s):
    out = {}
    for v in SALVADOR:
        out[f"sal_app_{v}"] = s + v
        out[f"sal_pre_{v}"] = v + s
        out[f"sal_appsp_{v}"] = s + " " + v
    for key in ("ELSALVADOR", "elsalvador", "SALVADOR"):
        out[f"sal_vig_{key}"] = vigenere(s, key, True)
        out[f"sal_vigE_{key}"] = vigenere(s, key, False)
    return out


# ----------------------------------------------------------------- driver ---
def compose(base_units, label, sink):
    """Apply the three clue stages in every order, and every subset."""
    stage_sand = sand(base_units)
    for sname, s in stage_sand.items():
        if not (3 <= len(s) <= 4000):
            continue
        sink(f"{label}|{sname}", s)                       # Sand alone
        for mname, m in mirror(s).items():                # Sand -> mirror
            if not (3 <= len(m) <= 4000):
                continue
            sink(f"{label}|{sname}|{mname}", m)
            for vname, v in salvador(m).items():          # Sand -> mirror -> ES
                if 3 <= len(v) <= 4000:
                    sink(f"{label}|{sname}|{mname}|{vname}", v)
        for vname, v in salvador(s).items():              # Sand -> ES
            if not (3 <= len(v) <= 4000):
                continue
            sink(f"{label}|{sname}|{vname}", v)
            for mname, m in mirror(v).items():            # Sand -> ES -> mirror
                if 3 <= len(m) <= 4000:
                    sink(f"{label}|{sname}|{vname}|{mname}", m)


def main():
    selftest_only = "--selftest" in sys.argv
    ok = True
    # controls
    assert vigenere(vigenere("attackatdawn", "LEMON", False), "LEMON", True) == "attackatdawn"
    print("  vigenere round trip: OK")
    assert "".join(ATBASH[c] for c in "abc") == "zyx"
    print("  atbash vector: OK")
    k = hashlib.sha256(b"correct horse battery staple").digest()
    good = H.addrs_for_priv(k)["p2pkh_u"] == "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"
    print(f"  derivation vector: {'OK' if good else 'FAIL'}")
    ok &= good
    o = H.Oracle()
    g = o.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"  oracle genesis: {'OK' if g else 'FAIL'}")
    ok &= g
    print("SELFTEST", "PASS" if ok else "FAIL")
    if selftest_only:
        sys.exit(0 if ok else 1)
    if not ok:
        sys.exit("selftest failed")

    hits, seen, PENDING = [], set(), []
    counts = {"phrases": 0, "keys": 0}

    def flush(force=False):
        if not PENDING or (len(PENDING) < 20000 and not force):
            return
        full = H.full_index()
        from index_oracle import spk_from_address
        spks, meta = [], []
        for tag, key in PENDING:
            for t, ad in H.addrs_for_priv(key).items():
                if o.funded(ad):
                    hits.append((tag, t, ad, key.hex()))
                    print(f"*** HIT(richlist) {tag} {t} {ad}", flush=True)
                spk = spk_from_address(ad)
                if spk is not None:
                    spks.append(spk); meta.append((tag, t, ad, key))
        if full is not None:
            for j, bal in full.contains_spks(spks):
                tag, t, ad, key = meta[j]
                hits.append((tag, t, ad, key.hex(), bal))
                print(f"*** HIT(fullindex) {tag} {t} {ad} {bal/1e8:.8f} BTC", flush=True)
        counts["keys"] += len(PENDING)
        PENDING.clear()

    def sink(tag, phrase):
        if phrase in seen:
            return
        seen.add(phrase)
        counts["phrases"] += 1
        for name, key in direct_keys(phrase).items():
            if 0 < int.from_bytes(key, "big") < CURVE_N:
                PENDING.append((f"{tag}|{name}", key))
        flush()

    t0 = time.time()
    lines = body_lines()
    sents = sentences(lines)
    p72_sents = sentences([P72])
    print(f"\nunits: {len(lines)} printed lines, {len(sents)} sentences, "
          f"{len(p72_sents)} page-72 sentences")

    compose(lines, "lines", sink)
    compose(sents, "sentences", sink)
    compose(p72_sents, "p72", sink)
    compose(lines + p72_sents, "lines+p72", sink)
    flush(force=True)

    print(f"\ndistinct composed phrases : {counts['phrases']:,}")
    print(f"keys derived              : {counts['keys']:,}")
    print(f"addresses checked         : ~{counts['keys']*5:,}")
    print(f"elapsed                   : {time.time()-t0:.0f}s")
    print(f"\nhits: {len(hits)}")
    for h in hits:
        print("  ", h)


if __name__ == "__main__":
    main()
