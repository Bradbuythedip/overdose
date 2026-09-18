#!/usr/bin/env python3
"""Verbatim candidate strings written by the photo-rebus scavenger (p74: Keiser aiming a pistol, bills from the muzzle; p73: capsules and a flipped note), swept with the full stack."""
C = ['NOT in candidates*.txt / gen_keiser / keiser_persona (grep 0)', 'in candidates', 'in keiser_persona/gen_keiser', 'not found in repo candidate lists (grep 0)', 'trivial; index_cipher covers small indices', 'index_cipher/serial_combine cover line indices (not re-run here)', 'trivial', 'already swept', 'sentence swept (179 variants); line and paragraph likely covered by sentence_cipher/paragraph sweeps -- verify before running', 'not found in repo (novel, weak prior)', 'boustrophedon.py / mirror_text* cover glyph flips; check whether whole-line-order reversal was swept', 'page_furniture.py covers furniture concatenations', 'composite.py covers first/last combinations', 'not found in repo (very weak prior)', "capsule orange-end bearings p73 (deg, 0=right, 90=down): 86.0, 12.6, 318.5, 318.8, 114.7 ; p79: 73.3, 3.3, 312.5, 305.6, 106.0 (p79 = p73 constellation scaled 0.758, rotated -10.1 deg, rms 1.3 px) -> one photo asset placed twice; the pattern is a photographer's drop, not a code", 'no capsule carries an imprint; the brown patch on p73 capsule 4 is an MRC mask artefact (absent in IMG_6244)', 'the man is UPRIGHT (head top y~1295, feet y~3830 at 400 dpi; the "upside down" premise came from the 180-rotated scan). No head-in-the-sand reading exists. Ground is dry grass/scrub, not sand.', 'backgrounds: two different frames of the same scrub hillside (p73 hills are not a mirror of p74 hills: ridge texture differs, NCC 0.60-0.65 either way); a ranch gate, two posts and a utility pole at p74 right; nothing written in either background besides @ANNABELLEBAZ']
import re
def forms():
    out = []
    for i, c in enumerate(C):
        v = c
        out += [(f"r{i}", v), (f"r{i}/lower", v.lower()), (f"r{i}/upper", v.upper()), (f"r{i}/nopunct", re.sub(r"[^\w\s]", "", v)), (f"r{i}/nospace_lower", re.sub(r"\s+", "", v).lower())]
    seen, uniq = set(), []
    for t, v in out:
        if v and v not in seen: seen.add(v); uniq.append((t, v))
    return uniq
def selftest():
    return len(C) > 0
if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
