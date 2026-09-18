#!/usr/bin/env python3
"""
The KB note's SUFFIX LETTER, never transcribed: KB 46279860 ? swept with every
letter a US serial can carry.

At 400 dpi, isolating the faint ink of the ghosted note on page 72 (mid-greys
only), a glyph follows the final 0 in the suffix position: a vertical stem
with a small top serif and a foot at the baseline. It reads as L or I (a
ninth digit is impossible; the suffix is a letter). page72.py recorded the
serial as KB46279860 with no suffix; serial2_exhaust.py guessed 'A'. This
emits the serial with every suffix letter the BEP uses (A-Y, no O or Z), in
the same string forms the first serial received, alone and paired with
CL76841714A, so the reading rests on nothing unread.
"""
LETTERS = [c for c in "ABCDEFGHIJKLMNPQRSTUVWXY"]
D, A = "46279860", "CL76841714A"

def forms():
    out = []
    def add(t, v): out.append((t, v))
    for L in LETTERS:
        base = [f"KB{D}{L}", f"KB {D} {L}", f"KB{D} {L}", f"{D}{L}", f"{D} {L}", f"KB {D[:4]} {D[4:]} {L}",
                f"KB{D}{L} B2", f"KB{D}{L}B2", f"B2 KB{D}{L}", f"KB{D}{L} 2", f"K B {D} {L}"]
        for i, s in enumerate(base):
            add(f"{L}/{i}", s); add(f"{L}/{i}/lower", s.lower())
        for sep in ("", " ", "\n", "-", "/"):
            add(f"{L}/pairAB/{sep!r}", A + sep + f"KB{D}{L}")
            add(f"{L}/pairBA/{sep!r}", f"KB{D}{L}" + sep + A)
        add(f"{L}/digitsAB", "76841714" + D + L); add(f"{L}/digitsBA", D + L + "76841714")
        add(f"{L}/mirror", (f"KB{D}{L}")[::-1]); add(f"{L}/mirrorpair", (A + f"KB{D}{L}")[::-1])
        add(f"{L}/ES", f"El Salvador KB{D}{L}"); add(f"{L}/ES2", f"KB{D}{L} El Salvador")
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq

def selftest():
    F = forms(); tags = [t for t, _ in F]
    return len(set(tags)) == len(tags) and all(v for _, v in F) and ("L/0", "KB46279860L") in F and len(LETTERS) == 24

if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
