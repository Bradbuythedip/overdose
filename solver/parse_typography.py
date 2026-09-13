#!/usr/bin/env python3
"""
Turn the sibling session's vision typography JSONs into a clean per-WORD bit string.

Those JSONs (solver/wf/typography_p*.json on branch claude/funny-clarke-reawl6)
mark bold inline with ** **, including SUB-WORD runs like

    but **Ge**org**e** C**li**nton   and   c**e**ntra**l** **b**an**ke**rs

The sub-word marks must not be used. Measured across all five pages, the
letters they select are wildly non-uniform — v 12.7%, i 10.5%, l 9.1%, u 8.5%,
d 8.3%, e 8.3% against a 0.4%, c 0.5%, n 0.6%, o 0.8%, t 1.1%, a ~30x spread.
Narrow heavy-stemmed letters get called bold an order of magnitude more often
than round open ones, which is glyph identity, not weight. It is the same
artifact this session found by pixel measurement and the sibling found in its
own per-letter classifier; a vision model reproduces it because the distressed
typewriter face genuinely looks that way.

So a word counts as bold only if EVERY one of its characters is inside a bold
run. Partial words are recorded separately and excluded.

Two readings are emitted, since a Bacon cipher could use either convention:
  bold  — only whole-word bold
  emph  — bold OR sitting inside a highlight bar ([O:...] orange, [B:...] black)

  python3 parse_typography.py --dir /tmp/sib --out /tmp/sib_bits
"""
import argparse, glob, json, os, re, sys

WORDCH = re.compile(r"[A-Za-z0-9$%'-]")


def parse_line(marked, mode):
    """Yield (word, bold) walking the line char by char with a bold flag."""
    s = marked.replace("~~", "")
    bars = []

    def grab(m):
        bars.append(m.group(2))
        return "\x01%d\x01" % (len(bars) - 1)

    s = re.sub(r"\[([OB]): (.+?)\]", grab, s)
    out = []

    def walk(text, inbar):
        bold = False
        cur, curbold = "", True
        i = 0
        while i < len(text):
            if text.startswith("**", i):
                bold = not bold
                i += 2
                continue
            if text[i] == "\x01":
                j = text.index("\x01", i + 1)
                if cur:
                    out.append((cur, curbold))
                    cur, curbold = "", True
                walk(bars[int(text[i + 1:j])], True)
                i = j + 1
                continue
            c = text[i]
            if WORDCH.match(c):
                cur += c
                # a word is bold only if EVERY character of it is bold
                curbold = curbold and (bold or (inbar and mode == "emph"))
            else:
                if cur:
                    out.append((cur, curbold))
                    cur, curbold = "", True
            i += 1
        if cur:
            out.append((cur, curbold))

    walk(s, False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp/sib")
    ap.add_argument("--out", default="/tmp/sib_bits")
    a = ap.parse_args()

    for mode in ("bold", "emph"):
        bits, words = [], []
        for f in sorted(glob.glob(os.path.join(a.dir, "typography_p*.json"))):
            for ln in json.load(open(f))["lines"]:
                for w, b in parse_line(ln["marked"], mode):
                    words.append(w)
                    bits.append("1" if b else "0")
        s = "".join(bits)
        n = s.count("1")
        with open(f"{a.out}_{mode}.txt", "w") as fh:
            fh.write(s)
        sys.stderr.write(f"{mode:5}: {len(s)} words, {n} whole-word set "
                         f"({n/max(len(s),1)*100:.1f}%) -> {a.out}_{mode}.txt\n")
        sys.stderr.write("       bold words: "
                         + " ".join(w for w, c in zip(words, s) if c == "1")[:150]
                         + "\n")


if __name__ == "__main__":
    main()
