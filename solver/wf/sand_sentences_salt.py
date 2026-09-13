#!/usr/bin/env python3
"""
Extension of sand_sentences.py: the same alternate-sentence / sentence-edge
readings as brainwallet passphrases with "El Salvador" (assumption 5: a
literal string) PREFIXED or SUFFIXED, through the 7 fast hashes x 5 script
types and the batched oracle. Control: a planted reading whose salted sha256
address is injected as a target must be reached by the same loop.
"""
import os, re, sys, hashlib, time, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import harness as H
import sand_sentences as S
from hd_sweep import direct_keys

SALTS = ["El Salvador", "ElSalvador", "el salvador", "elsalvador", "EL SALVADOR", "ELSALVADOR"]


def salted(phrase):
    for s in SALTS:
        for sep in ("", " "):
            yield f"{s}{sep}{phrase}", f"pre:{s!r}{sep!r}"
            yield f"{phrase}{sep}{s}", f"suf:{sep!r}{s!r}"


def readings_of(units, tag):
    out = {}
    for direction in ("fwd", "rev"):
        uu = units if direction == "fwd" else units[::-1]
        t = f"{tag}:{direction}"
        for pname, sel in S.parity_readings(uu):
            if len(sel) < 2:
                continue
            out[f"{t}:{pname}"] = " ".join(sel)
            out[f"{t}:{pname}:initial_words"] = " ".join(S.first_word(u) for u in sel)
            out[f"{t}:{pname}:final_words"] = " ".join(S.last_word(u) for u in sel)
        out[f"{t}:full:initial_words"] = " ".join(S.first_word(u) for u in uu)
        out[f"{t}:full:final_words"] = " ".join(S.last_word(u) for u in uu)
        out[f"{t}:full:initial_letters"] = "".join(S.first_letter(u) for u in uu)
    return out


def sweep(readings, sink, seen):
    n = 0
    for rname, text in readings.items():
        for fname, p in S.forms(text).items():
            if not p:
                continue
            for sp, stag in salted(p):
                if sp in seen:
                    continue
                seen.add(sp)
                n += 1
                for hname, k in direct_keys(sp).items():
                    sink.n_keys += 1
                    for typ, a in H.addrs_for_priv(k).items():
                        sink.check(f"brain+salt:{hname}:{stag}:{fname}:{rname}", a, k, None, typ)
    sink.flush()
    return n


def main():
    t0 = time.time()
    O = H.Oracle()
    # ---- control: planted units, expected address computed directly with hashlib ----
    units, _ = S.build_control_units()
    lit = " ".join(re.sub(r"[^A-Za-z0-9 ]", "", " ".join(units[0::2])).split()).lower()
    exp = H.addrs_for_priv(hashlib.sha256(("El Salvador " + lit).encode()).digest())["p2pkh_c"]
    exp2 = H.addrs_for_priv(hashlib.sha256((lit + "elsalvador").encode()).digest())["p2wpkh"]
    cs = S.Sink(O, {exp: "salt_prefix_ctrl", exp2: "salt_suffix_ctrl"}, quiet=True)
    sweep(readings_of(units, "CTRL:A:ALL"), cs, set())
    ok = "salt_prefix_ctrl" in cs.ctrl and "salt_suffix_ctrl" in cs.ctrl
    print(f"CONTROL {'PASS' if ok else 'FAIL'}: planted odd-sentence reading with 'El Salvador ' prefix -> {exp} "
          f"{'reached' if 'salt_prefix_ctrl' in cs.ctrl else 'MISSED'}; with 'elsalvador' suffix -> {exp2} "
          f"{'reached' if 'salt_suffix_ctrl' in cs.ctrl else 'MISSED'}", flush=True)
    if ok:
        print("   via", cs.ctrl["salt_prefix_ctrl"][0][0][:100])

    # ---- real article ----
    pages = S.load_pages()
    sink = S.Sink(O)
    seen = set()
    nphr = 0
    for us, fn in (("A", S.units_A), ("B", S.units_B), ("P", S.units_P)):
        allu = []
        for pno, paras in pages:
            u = fn(paras)
            allu += u
            nphr += sweep(readings_of(u, f"REAL:{us}:p{pno}"), sink, seen)
        nphr += sweep(readings_of(allu, f"REAL:{us}:ALL"), sink, seen)
        print(f"  unit set {us} done: {nphr:,} salted phrases so far, {sink.n_addr:,} addresses", flush=True)
    print(f"STATS: salted phrases {nphr:,}, keys {sink.n_keys:,}, addresses checked {sink.n_addr:,} "
          f"(full index {sink.n_full:,})")
    print("HITS:", len(sink.hits))
    for h in sink.hits:
        print("  ", h)
    print(f"elapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
