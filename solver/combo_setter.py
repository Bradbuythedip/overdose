#!/usr/bin/env python3
"""
LENS: puzzle-setter / steganographer. How a columnist who says "El Salvador is a clue",
cites George Sand's alternate-line letters and links a mirror-writing paper would USE the two
8-digit serials CL 76841714 A and KB 46279860 as a KEY TO THE TEXT rather than as a thing to
hash, and the material strings that fall out. Digit streams used throughout: A=76841714,
B=46279860, AB, BA and their digit interleave IL. ADDS (tag prefixes in brackets): [a1z] A1Z26
readings -- singles (0-based, 1-based, 0 dropped), digit pairs/triples/quads mod 26 (76 84 17
14 -> XFQN, 46 27 98 60 -> TATH), every legal A1Z26 parse of each serial (7|6|8|4|17|14 ...),
upper and lower, and wrapped in the serial letters (CL..A, KB..); [asc] ASCII-code readings --
decimal pairs (76='L', 84='T', 46='.', 98='b', 60='<') as printable-only strings, as mixed
ASCII/A1Z26 strings (LTQN, .Ab<), as raw bytes, the hex-pair bytes likewise, and every parse of
each 8-digit serial into 1-3 digit codes 0..127 as bytes and printable projections; [t9]
phone-keypad letter SETS ([PQRS][MNO][TUV][GHI]..., space- and bare-joined, 1/0 kept or dropped),
first/second/last-letter picks, the clue words ENCODED on the keypad (OVERDOSE -> 68373673,
SALVADOR -> 72582367, ELSALVADOR -> 3572582367, ...) concatenated with each serial and, where
8 digits, digit-wise sum/diff/xor mod 10 against A and B; [vig][cae][rail][col][scy] the digits
as a numeric Vigenere key (per-digit shifts, encrypt and decrypt), the pair-mod-26 and pair-
letter keys, the serial letters CLAKB/KBCLA as a letter key, Caesar shifts by every digit present
and by the digit sums (38->12, 42->16, 80->2) and values mod 26 (14, 16, 4, 12, 2), rail fence
with 2/4/6/7/8/9 rails, irregular columnar transposition keyed by A/B/AB/BA and scytale widths
2-9 -- all applied to the pull-quote, the BITCOIN IS TOXIC AF headline, the OVERDOSE masthead,
the byline, the MAX KEISER sign-off, the X FUCK ALL X scribble, the folio, El Salvador, George
Sand, mirror, Nayib Bukele, the 38 highlighted runs individually and their ordered concatenation,
colour subsets, initials and first words; [str] the digits as a skip/stride key (count d, take
one; cyclic) over the article words, the highlighted words, the page-72 words and the letters of
the article / highlights / pull-quote, both bases, first 12 / 24 picks and the initials of the
whole walk; [perm] the digits as a permutation key over the 38 highlighted phrases -- digit,
pair and cumulative indices into the list, columnar reordering (which is the stable sort by
cyclic digit) and its reverse, emitted as phrases, first words and initials; [ptr] digit groups as page:line:word and
page:paragraph:word pointers into pages 72 and 75-79 (group shapes 1/2-digit page, 1/2-digit
line, 1/2-digit word; page maps as-printed 2-digit, 7d, 72+d, body index, mod), and [xptr] the
two serials combined as ONE pointer -- A picks the line and B the word (and vice versa), digit-
wise and pair-wise, per page and over all body lines, plus A-pair line / B-pair column letters;
[nth] the cyclic digits as an Nth-letter selector over the highlight phrases, the lines of each
page and the words of the pull-quote / display strings; [cidx] the digits as letter and word
indices into the clue words and display strings ("El Salvador"[7,6,8,4,...]); [sand] the George
Sand device keyed by the serial -- lines at the cumulative digit positions, every-other-line
starting at each serial digit, every d-th line, per page and over the body, as whole lines and
as Musset first-words; [poly] 5x5 and 6x6 Polybius readings of the digit pairs, plain and keyed
on ELSALVADOR; [date] the pairs as dates (7/6/84, 1/7/14, 4/6/27, 9/8/60) in US, UK, ISO,
compact and month-name forms, the pairs as years (1976 1984 2017 2014 / 1946 1927 1998 1960),
the serials and their sum/difference as Unix epochs (76841714 -> 1972-06-08), each crossed with
"El Salvador"; [geo] the serials as coordinates (76.841714 / 46.279860, signs, N/E/S/W, and
El Salvador placements such as 13.76841714, -88.46279860), as strings only; [il] the serials
interleaved letter by letter with El Salvador / OVERDOSE / mirror / George Sand / Max Keiser /
Bukele / bitcoin, both orders, and the three-way word/A/B interleaves. SPECULATIVE (kept because
they are cheap, not because a setter is likely to have used them): the ASCII parses, the 6x6
Polybius, the scytale and rail decrypt directions, the mixed ASCII/A1Z26 strings, the geo
variants, the epoch dates. DELIBERATELY OMITTED because an existing module covers it: numeric
arithmetic, plain string recombination, concatenation with the clue words, the digits as flat
indices into article words / lines / characters / page 72 and the BIP-39-index readings
(serial_combine numeric/string/text_index/discovery); clue phrase x serial concatenations
(clue_serial); the serial digits as per-page and global indices into words / lines / sentences /
paragraphs / characters with first-letter and Nth-character extraction (index_cipher); Vigenere
/ Beaufort / autokey / running-key keyed on clue WORDS and article words over the whole article
(classical_cipher, cipher_mine); the alphabet positions of the serial letters (serial_combine
string_forms); rot180 / mirror readings (mirror_serial); the display strings themselves and
their pairings (page_furniture); page-72 text x serial (page72); banknote semantics
(combo_numismatic); wallet encodings (combo_walletformats); RNG seeding (serial_entropy); the
global alternate-line Sand readings from line 1 and 2 (gen_sand, clue_serial). Also omitted on
purpose: the full T9 product expansions (1,296 + 3,888 uppercase strings) -- they would push
this module past the 8,000-form threshold above which serial_combine stops giving plugin
material its HD seeds, for a family with no dictionary to select from; the letter SETS are
emitted instead.

  python3 combo_setter.py
"""
import datetime, itertools, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
A_D, B_D = "76841714", "46279860"
A_STR, B_STR = "CL76841714A", "KB46279860"
AB, BA = A_D + B_D, B_D + A_D


def interleave(x, y):
    out = []
    for i in range(max(len(x), len(y))):
        if i < len(x): out.append(x[i])
        if i < len(y): out.append(y[i])
    return "".join(out)


IL = interleave(A_D, B_D)
STREAMS = [("A", A_D), ("B", B_D), ("AB", AB), ("BA", BA), ("IL", IL)]
FOUR = STREAMS[:4]

DISPLAY = [
    ("pullquote", "The economy of love is infinitely more efficient than hate and war."),
    ("headline", "BITCOIN IS TOXIC AF"),
    ("masthead", "OVERDOSE"),
    ("byline", "with Max Keiser"),
    ("signoff", "MAX KEISER"),
    ("scribble", "X FUCK ALL X"),
    ("folio", "Bitcoin Magazine | El Salvador"),
    ("elsalvador", "El Salvador"),
    ("georgesand", "George Sand"),
    ("mirror", "mirror"),
    ("bukele", "Nayib Bukele"),
    ("volcano", "Volcano Bonds"),
]
CLUE_WORDS = ["El Salvador", "ElSalvador", "ELSALVADOR", "OVERDOSE", "Overdose", "mirror",
              "MIRROR", "George Sand", "GeorgeSand", "Max Keiser", "MaxKeiser", "Bukele",
              "bitcoin", "Bitcoin"]
T9_WORDS = ["OVERDOSE", "SALVADOR", "ELSALVADOR", "MIRROR", "GEORGESAND", "SAND", "MAXKEISER",
            "KEISER", "BUKELE", "BITCOIN", "TOXIC", "LOVE"]

KEYPAD = {"2": "ABC", "3": "DEF", "4": "GHI", "5": "JKL", "6": "MNO", "7": "PQRS",
          "8": "TUV", "9": "WXYZ"}
L2K = {l: k for k, ls in KEYPAD.items() for l in ls}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


# ---------------------------------------------------------------- text helpers
def W(s):
    return re.findall(r"[A-Za-z0-9$%']+", s)


def letters(s):
    return "".join(c for c in s if c.isalpha())


def first_alpha(s):
    for c in s:
        if c.isalpha(): return c
    return ""


def a1(n):
    """1-based A1Z26 with wrap: 1->A .. 26->Z, 27->A, 0->Z."""
    return chr(65 + (n - 1) % 26)


def digits(s):
    return [int(c) for c in s]


def pairs_of(d):
    return [int(d[i:i + 2]) for i in range(0, len(d) - 1, 2)]


def dw(x, y, op):
    return "".join(str(op(int(p), int(q)) % 10) for p, q in zip(x, y))


def keypad(word):
    return "".join(L2K[c] for c in word.upper() if c in L2K)


def _read(name):
    return open(os.path.join(HERE, name), encoding="utf-8").read()


def _pages():
    """printed page -> (lines, paragraphs) for 72 and 75-79, in print order."""
    raw = re.sub(r"^#.*$", "", _read("article_transcript.txt"), flags=re.M)
    parts = re.split(r"^=== PAGE (\d+).*?===$", raw, flags=re.M)
    it = iter(parts[1:])
    pages = {}
    for num, body in zip(it, it):
        lines, paras = [], []
        for block in re.split(r"\n\s*\n", body):
            ls = [l.strip() for l in block.splitlines() if l.strip()]
            if ls:
                lines.extend(ls); paras.append(" ".join(ls))
        pages[int(num)] = (lines, paras)
    try:
        import page72
        L = list(page72.LINES)
    except Exception:
        L = ["NUMBERS", "165 WESTERN UNION LOCATIONS IN PALESTINE",
             "572 WESTERN UNION LOCATIONS IN EL SALVADOR"]
    pages[72] = (L, [l for l in L if len(l.split()) >= 4])
    return dict(sorted(pages.items()))


def _highlights():
    out = []
    for l in _read("highlights_ordered.tsv").splitlines():
        if l.startswith("#") or not l.strip(): continue
        p = l.split("\t")
        if len(p) >= 3 and p[2].strip(): out.append((int(p[0]), p[1].strip(), p[2].strip()))
    return out


_CTX = None


def ctx():
    global _CTX
    if _CTX is None:
        pages = _pages()
        H = _highlights()
        body_lines = [l for pg, (ls, _) in pages.items() if pg != 72 for l in ls]
        body_paras = [p for pg, (_, ps) in pages.items() if pg != 72 for p in ps]
        flat = " ".join(body_paras)
        hl_all = " ".join(t for _, _, t in H)
        _CTX = {
            "pages": pages, "H": H, "lines": body_lines, "paras": body_paras,
            "words": W(flat), "letters": letters(flat),
            "hlwords": W(hl_all), "hlletters": letters(hl_all), "hl_all": hl_all,
            "p72words": W(" ".join(pages[72][0])),
        }
    return _CTX


# ---------------------------------------------------------------- cipher helpers
def _shift(c, k):
    if "a" <= c <= "z": return chr((ord(c) - 97 + k) % 26 + 97)
    if "A" <= c <= "Z": return chr((ord(c) - 65 + k) % 26 + 65)
    return c


def caesar(text, k):
    return "".join(_shift(c, k) for c in text)


def vigenere(text, shifts, sign=1):
    out, i = [], 0
    for c in text:
        if c.isalpha():
            out.append(_shift(c, sign * shifts[i % len(shifts)])); i += 1
        else:
            out.append(c)
    return "".join(out)


def _rail_pattern(n, r):
    idx, i, d = [], 0, 1
    for _ in range(n):
        idx.append(i)
        if i == 0: d = 1
        elif i == r - 1: d = -1
        i += d
    return idx


def rail_enc(s, r):
    if r < 2 or r >= len(s): return None
    pat = _rail_pattern(len(s), r)
    return "".join(s[j] for row in range(r) for j in range(len(s)) if pat[j] == row)


def rail_dec(s, r):
    if r < 2 or r >= len(s): return None
    pat = _rail_pattern(len(s), r)
    order = sorted(range(len(s)), key=lambda j: (pat[j], j))
    out = [None] * len(s)
    for pos, j in enumerate(order): out[j] = s[pos]
    return "".join(out)


def col_order(key):
    return sorted(range(len(key)), key=lambda i: (key[i], i))


def columnar_enc(seq, key):
    """Irregular columnar transposition of a sequence (str or list); returns a list."""
    n = len(key)
    cols = [list(seq[i::n]) for i in range(n)]
    return [x for i in col_order(key) for x in cols[i]]


def columnar_dec(seq, key):
    n = len(key); L = len(seq)
    rows, extra = divmod(L, n)
    lens = [rows + (1 if i < extra else 0) for i in range(n)]
    cols, p = [None] * n, 0
    for i in col_order(key):
        cols[i] = list(seq[p:p + lens[i]]); p += lens[i]
    return [cols[i][r] for r in range(rows + 1) for i in range(n) if r < len(cols[i])]


def scytale(s, w):
    return "".join(s[i::w] for i in range(w))


def a1z26_parses(d, zero_is_z=False, cap=64):
    res = []

    def rec(i, acc):
        if len(res) >= cap: return
        if i == len(d): res.append(acc); return
        for L in (1, 2):
            t = d[i:i + L]
            if len(t) < L or (L == 2 and t[0] == "0"): continue
            v = int(t)
            if 1 <= v <= 26: rec(i + L, acc + chr(64 + v))
            elif v == 0 and zero_is_z and L == 1: rec(i + 1, acc + "Z")
    rec(0, "")
    return res


def ascii_parses(d, lo=0, hi=127, cap=400):
    res = []

    def rec(i, acc):
        if len(res) >= cap: return
        if i == len(d): res.append(bytes(acc)); return
        for L in (1, 2, 3):
            t = d[i:i + L]
            if len(t) < L or (L > 1 and t[0] == "0"): continue
            v = int(t)
            if lo <= v <= hi: rec(i + L, acc + [v])
    rec(0, [])
    return res


POLY5 = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
POLY6 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def keyed_square(key, alphabet):
    out = []
    for c in key.upper() + alphabet:
        if c == "J" and len(alphabet) == 25: c = "I"
        if c in alphabet and c not in out: out.append(c)
    return "".join(out)


# ---------------------------------------------------------------- families
def fam_a1z26(put):
    for nm, d in STREAMS:
        base = {
            "single1": "".join(a1(int(c)) for c in d),
            "single0": "".join(chr(65 + int(c)) for c in d),
            "single1_drop0": "".join(a1(int(c)) for c in d if c != "0"),
        }
        for k in (2, 3, 4):
            grp = [d[i:i + k] for i in range(0, len(d) - k + 1, k)]
            base[f"g{k}_mod26_1"] = "".join(a1(int(g)) for g in grp)
            base[f"g{k}_mod26_0"] = "".join(chr(65 + int(g) % 26) for g in grp)
        for i, p in enumerate(a1z26_parses(d)): base[f"parse{i}"] = p
        for i, p in enumerate(a1z26_parses(d, zero_is_z=True)): base[f"parse0z{i}"] = p
        for k, v in base.items():
            put(f"a1z:{k}:{nm}", v); put(f"a1z:{k}:{nm}:lower", v.lower())
        # wrapped in the serial letters, as a setter would keep the note's shape
        wrap = {"A": ("CL", "A"), "B": ("KB", ""), "AB": ("CL", "A KB"), "BA": ("KB", " CLA")}
        if nm in wrap:
            pre, suf = wrap[nm]
            for k in ("single1", "g2_mod26_1", "parse0"):
                if k in base:
                    put(f"a1z:{k}:{nm}:wrapped", (pre + base[k] + suf).strip())
    put("a1z:whole_mod26_1", a1(int(A_D)) + a1(int(B_D)))          # N P
    put("a1z:whole_mod26_0", chr(65 + int(A_D) % 26) + chr(65 + int(B_D) % 26))  # O Q


def fam_ascii(put):
    for nm, d in STREAMS:
        pr = pairs_of(d)
        put(f"asc:pairs_printable:{nm}", "".join(chr(v) for v in pr if 32 <= v < 127))
        put(f"asc:pairs_mixed:{nm}", "".join(chr(v) if 32 <= v < 127 else a1(v) for v in pr))
        put(f"asc:pairs_bytes:{nm}", "hex:" + bytes(pr).hex())
        hb = bytes.fromhex(d)
        put(f"asc:hexpairs_printable:{nm}", "".join(chr(v) for v in hb if 32 <= v < 127))
        put(f"asc:hexpairs_mixed:{nm}", "".join(chr(v) if 32 <= v < 127 else a1(v) for v in hb))
        if nm in ("A", "B"):
            for i, bs in enumerate(ascii_parses(d)):
                put(f"asc:parse{i}_bytes:{nm}", "hex:" + bs.hex())
                s = "".join(chr(v) for v in bs if 32 <= v < 127)
                if len(s) >= 2: put(f"asc:parse{i}_printable:{nm}", s)
        else:
            for i, bs in enumerate(ascii_parses(d, 32, 126, cap=64)):
                put(f"asc:pparse{i}:{nm}", bs.decode("ascii"))


def fam_t9(put):
    for nm, d in STREAMS:
        sets = [KEYPAD.get(c, "") for c in d]
        nz = [s for s in sets if s]
        put(f"t9:sets_space:{nm}", " ".join(nz))
        put(f"t9:sets_bracket:{nm}", "".join(f"[{s}]" for s in nz))
        put(f"t9:sets_concat:{nm}", "".join(nz))
        put(f"t9:sets_keep01:{nm}", " ".join(KEYPAD.get(c, c) for c in d))
        put(f"t9:sets_keep01_concat:{nm}", "".join(KEYPAD.get(c, c) for c in d))
        for pick, name in ((0, "first"), (1, "second"), (2, "third"), (-1, "last")):
            v = "".join(s[pick] for s in nz)
            put(f"t9:{name}:{nm}", v); put(f"t9:{name}:{nm}:lower", v.lower())
        put(f"t9:first_keep01:{nm}", "".join(KEYPAD[c][0] if c in KEYPAD else c for c in d))
    for w in T9_WORDS:
        k = keypad(w)
        put(f"t9:word:{w}", k)
        for nm, d in FOUR:
            put(f"t9:word+{nm}:{w}", k + d); put(f"t9:{nm}+word:{w}", d + k)
            put(f"t9:word_{nm}_sp:{w}", k + " " + d); put(f"t9:{nm}_word_sp:{w}", d + " " + k)
        if len(k) == 8:
            for nm, d in (("A", A_D), ("B", B_D)):
                for on, op in (("sum", lambda p, q: p + q), ("diff", lambda p, q: p - q),
                               ("rdiff", lambda p, q: q - p), ("xor", lambda p, q: p ^ q)):
                    put(f"t9:dw{on}:{w}:{nm}", dw(k, d, op))
            put(f"t9:il:{w}", interleave(k, A_D) + interleave(k, B_D))


def _texts():
    c = ctx(); H = c["H"]
    T = [(f"h{i:02d}", t, False) for i, (_, _, t) in enumerate(H)]
    T += [(k, v, True) for k, v in DISPLAY]
    T.append(("hl_all", c["hl_all"], True))
    T.append(("hl_initials", "".join(first_alpha(t) for _, _, t in H), True))
    T.append(("hl_firstwords", " ".join(W(t)[0] for _, _, t in H if W(t)), True))
    for colour in ("orange", "black", "white"):
        T.append((f"hl_{colour}", " ".join(t for _, col, t in H if col == colour), True))
    return T


VIG_KEYS = {
    "A": digits(A_D), "B": digits(B_D), "AB": digits(AB), "BA": digits(BA), "IL": digits(IL),
    "A26": [v % 26 for v in pairs_of(A_D)], "B26": [v % 26 for v in pairs_of(B_D)],
    "AB26": [v % 26 for v in pairs_of(AB)],
    "Aletter": [(v - 1) % 26 for v in pairs_of(A_D)],      # X F Q N as a Vigenere key, A=0
    "Bletter": [(v - 1) % 26 for v in pairs_of(B_D)],      # T A T H
    "CLAKB": [2, 11, 0, 10, 1], "KBCLA": [10, 1, 2, 11, 0],
}
CAESAR = sorted({1, 2, 4, 6, 7, 8, 9} | {38 % 26, 42 % 26, 80 % 26} |
                {int(A_D) % 26, int(B_D) % 26, (int(A_D) + int(B_D)) % 26,
                 int(AB) % 26, int(BA) % 26})
RAILS = [2, 4, 6, 7, 8, 9]
COL_KEYS = {"A": digits(A_D), "B": digits(B_D), "AB": digits(AB), "BA": digits(BA)}


def fam_ciphers(put):
    for tn, text, full in _texts():
        L = letters(text)
        vk = VIG_KEYS if full else {k: VIG_KEYS[k] for k in ("A", "B", "AB")}
        for kn, shifts in vk.items():
            put(f"vig:enc:{kn}:{tn}", vigenere(text, shifts, 1))
            put(f"vig:dec:{kn}:{tn}", vigenere(text, shifts, -1))
        for k in (CAESAR if full else (12, 16, 2, 14)):
            put(f"cae:+{k}:{tn}", caesar(text, k))
            if full: put(f"cae:-{k}:{tn}", caesar(text, -k))
        for r in (RAILS if full else (2,)):
            e = rail_enc(L, r)
            if e: put(f"rail:enc{r}:{tn}", e)
            if full:
                dd = rail_dec(L, r)
                if dd: put(f"rail:dec{r}:{tn}", dd)
        for kn, key in (COL_KEYS.items() if full else (("A", COL_KEYS["A"]), ("B", COL_KEYS["B"]))):
            put(f"col:enc:{kn}:{tn}", "".join(columnar_enc(L, key)))
            if full: put(f"col:dec:{kn}:{tn}", "".join(columnar_dec(L, key)))
        if full:
            for w in RAILS:
                put(f"scy:enc{w}:{tn}", scytale(L, w))
                put(f"scy:dec{w}:{tn}", "".join(columnar_dec(L, list(range(w)))))


def fam_stride(put):
    c = ctx()
    wt = [("words", c["words"]), ("hlwords", c["hlwords"]), ("p72words", c["p72words"])]
    lt = [("letters", c["letters"]), ("hlletters", c["hlletters"]),
          ("pqletters", letters(DISPLAY[0][1]))]
    for nm, d in STREAMS:
        steps = [int(x) or 10 for x in d]
        for base in (0, 1):
            def walk(seq):
                out, p, k = [], 0, 0
                while True:
                    p += steps[k % len(steps)]; k += 1
                    if p - base >= len(seq): return out
                    out.append(seq[p - base])
            for tn, seq in wt:
                w = walk(seq)
                if not w: continue
                put(f"str:{tn}:{nm}:b{base}:w12", " ".join(w[:12]))
                put(f"str:{tn}:{nm}:b{base}:w24", " ".join(w[:24]))
                put(f"str:{tn}:{nm}:b{base}:initials", "".join(x[0] for x in w))
            for tn, seq in lt:
                w = "".join(walk(seq))
                if not w: continue
                put(f"str:{tn}:{nm}:b{base}:c32", w[:32])
                put(f"str:{tn}:{nm}:b{base}:c64", w[:64])


def fam_perm(put):
    H = [t for _, _, t in ctx()["H"]]; n = len(H)

    def emit(tag, sel):
        if not sel: return
        put(tag + ":phrases", " ".join(sel))
        put(tag + ":firstwords", " ".join(W(s)[0] for s in sel if W(s)))
        put(tag + ":initials", "".join(first_alpha(s) for s in sel))
    for nm, d in FOUR:
        sing = digits(d); pr = pairs_of(d); cum = list(itertools.accumulate(sing))
        for base in (0, 1):
            for sn, seq in (("d1", sing), ("d2", pr), ("cum", cum)):
                emit(f"perm:idx:{nm}:{sn}:b{base}", [H[(i - base) % n] for i in seq])
        emit(f"perm:columnar:{nm}", columnar_enc(H, sing))
        emit(f"perm:columnar_dec:{nm}", columnar_dec(H, sing))
        # a stable sort by the cyclic digit IS the columnar reordering above; only its reverse is new
        emit(f"perm:stablesort_desc:{nm}", [H[i] for i in sorted(range(n), key=lambda i: (-sing[i % 8], i))])


def _page_maps(pd):
    pages = sorted(ctx()["pages"])
    if pd == 2:
        return {"as2": lambda p: p if p in pages else None,
                "mod": lambda p: pages[p % len(pages)]}
    body = [p for p in pages if p != 72]
    return {"7d": lambda p: int("7" + str(p)) if int("7" + str(p)) in pages else None,
            "72+d": lambda p: 72 + p if 72 + p in pages else None,
            "idx": lambda p: pages[p % len(pages)],
            "body": lambda p: body[p % len(body)]}


def fam_pointer(put):
    pages = ctx()["pages"]
    shapes = [(1, 1, 1), (2, 1, 1), (1, 2, 1), (2, 2, 2), (2, 2, 1), (1, 1, 2), (2, 1, 2)]
    for nm, d in STREAMS:
        for pd, ld, wd in shapes:
            g = pd + ld + wd
            groups = [d[i:i + g] for i in range(0, len(d) - g + 1, g)]
            for mn, mp in _page_maps(pd).items():
                for unit in ("line", "para"):
                    for base in (0, 1):
                        sel = []
                        for grp in groups:
                            pg = mp(int(grp[:pd]))
                            if pg is None: continue
                            items = pages[pg][0 if unit == "line" else 1]
                            if not items: continue
                            li = (int(grp[pd:pd + ld]) - base) % len(items)
                            ws = W(items[li])
                            if not ws: continue
                            sel.append(ws[(int(grp[pd + ld:]) - base) % len(ws)])
                        if not sel: continue
                        tag = f"ptr:{nm}:{pd}{ld}{wd}:{mn}:{unit}:b{base}"
                        put(tag + ":words", " ".join(sel))
                        if len(sel) >= 3: put(tag + ":initials", "".join(x[0] for x in sel))


def fam_xpointer(put):
    c = ctx(); pages = c["pages"]
    targets = [(f"p{pg}", ls) for pg, (ls, _) in pages.items()] + [("body", c["lines"])]
    combos = [("A/B", A_D, B_D), ("B/A", B_D, A_D)]
    for tn, lines in targets:
        n = len(lines)
        for cn, x, y in combos:
            for gn, xs, ys in (("d1", digits(x), digits(y)), ("d2", pairs_of(x), pairs_of(y))):
                for base in (0, 1):
                    sel, lets = [], []
                    for li, wi in zip(xs, ys):
                        line = lines[(li - base) % n]
                        ws = W(line)
                        if ws: sel.append(ws[(wi - base) % len(ws)])
                        L = letters(line)
                        if L: lets.append(L[(wi - base) % len(L)])
                    tag = f"xptr:{tn}:{cn}:{gn}:b{base}"
                    put(tag + ":words", " ".join(sel))
                    put(tag + ":initials", "".join(w[0] for w in sel))
                    put(tag + ":letters", "".join(lets))


def fam_nth(put):
    c = ctx()
    targets = [("hl", [t for _, _, t in c["H"]]), ("pqwords", W(DISPLAY[0][1])),
               ("headwords", W("BITCOIN IS TOXIC AF with Max Keiser MAX KEISER")),
               ("hlwords", c["hlwords"]), ("lines", c["lines"])]
    targets += [(f"p{pg}lines", ls) for pg, (ls, _) in c["pages"].items()]
    for tn, items in targets:
        for nm, d in FOUR:
            key = digits(d)
            for base in (0, 1):
                out = []
                for i, it in enumerate(items):
                    L = letters(it)
                    if L: out.append(L[(key[i % len(key)] - base) % len(L)])
                put(f"nth:{tn}:{nm}:b{base}", "".join(out))


def fam_clueidx(put):
    texts = [(w, w) for w in CLUE_WORDS] + [(k, v) for k, v in DISPLAY if k not in
                                            ("elsalvador", "georgesand", "mirror", "masthead")]
    for tn, t in texts:
        L = letters(t); ws = W(t)
        for nm, d in FOUR:
            for base in (0, 1):
                put(f"cidx:{tn}:{nm}:d1:b{base}", "".join(L[(int(x) - base) % len(L)] for x in d))
                put(f"cidx:{tn}:{nm}:d2:b{base}", "".join(L[(p - base) % len(L)] for p in pairs_of(d)))
                if len(ws) >= 4:
                    put(f"cidx:{tn}:{nm}:words:b{base}", " ".join(ws[(int(x) - base) % len(ws)] for x in d))


def fam_sand(put):
    c = ctx()
    targets = [(f"p{pg}", ls) for pg, (ls, _) in c["pages"].items()] + [("body", c["lines"])]
    for tn, lines in targets:
        n = len(lines)

        def emit(tag, sel):
            if not sel: return
            put(tag + ":lines", " ".join(sel))
            put(tag + ":firstwords", " ".join(W(s)[0] for s in sel if W(s)))
            put(tag + ":initials", "".join(first_alpha(s) for s in sel))
        for nm, d in FOUR:
            cum = list(itertools.accumulate(digits(d)))
            emit(f"sand:cum:{tn}:{nm}", [lines[(k - 1) % n] for k in cum])
            emit(f"sand:cum_strict:{tn}:{nm}", [lines[k - 1] for k in cum if 1 <= k <= n])
        for dg in sorted({int(x) for x in AB} - {0}):
            if not (tn == "body" and dg in (1, 2)):      # global alt from 1/2 = the swept Sand reading
                emit(f"sand:alt_from{dg}:{tn}", lines[dg - 1::2])
            if dg >= 2:
                emit(f"sand:every{dg}:{tn}", lines[dg - 1::dg])


def fam_polybius(put):
    squares = {"p5": POLY5, "k5": keyed_square("ELSALVADOR", POLY5),
               "p6": POLY6, "k6": keyed_square("ELSALVADOR", POLY6)}
    sources = {"A": list(zip(digits(A_D)[0::2], digits(A_D)[1::2])),
               "B": list(zip(digits(B_D)[0::2], digits(B_D)[1::2])),
               "AB": list(zip(digits(AB)[0::2], digits(AB)[1::2])),
               "AxB": list(zip(digits(A_D), digits(B_D)))}
    for sq, alpha in squares.items():
        side = 5 if len(alpha) == 25 else 6
        for sn, prs in sources.items():
            for base in (0, 1):
                rc = "".join(alpha[((r - base) % side) * side + (c - base) % side] for r, c in prs)
                cr = "".join(alpha[((c - base) % side) * side + (r - base) % side] for r, c in prs)
                put(f"poly:{sq}:{sn}:b{base}:rc", rc)
                put(f"poly:{sq}:{sn}:b{base}:cr", cr)


def _date_forms(m, d, yy):
    out = []
    years = [1900 + yy, 2000 + yy]
    out += [f"{m}/{d}/{yy:02d}", f"{m:02d}/{d:02d}/{yy:02d}", f"{m}{d}{yy:02d}", f"{m:02d}{d:02d}{yy:02d}",
            f"{d}/{m}/{yy:02d}", f"{d:02d}/{m:02d}/{yy:02d}", f"{m}-{d}-{yy:02d}", f"{m}.{d}.{yy:02d}"]
    for y in years:
        out += [f"{m}/{d}/{y}", f"{m:02d}/{d:02d}/{y}", f"{d}/{m}/{y}", f"{y}-{m:02d}-{d:02d}",
                f"{y}{m:02d}{d:02d}", f"{m:02d}{d:02d}{y}", f"{d:02d}{m:02d}{y}"]
        if 1 <= m <= 12:
            out += [f"{MONTHS[m - 1]} {d}, {y}", f"{d} {MONTHS[m - 1]} {y}"]
        if 1 <= d <= 12:
            out += [f"{y}-{d:02d}-{m:02d}", f"{MONTHS[d - 1]} {m}, {y}", f"{m} {MONTHS[d - 1]} {y}"]
    return list(dict.fromkeys(out))


def fam_dates(put):
    trip = {"A1": (7, 6, 84), "A2": (1, 7, 14), "B1": (4, 6, 27), "B2": (9, 8, 60)}
    prim = {}
    for tn, (m, d, yy) in trip.items():
        fs = _date_forms(m, d, yy)
        prim[tn] = fs
        for i, f in enumerate(fs): put(f"date:{tn}:{i}", f)
        for f in (fs[0], f"{1900 + yy}-{m:02d}-{d:02d}"):
            put(f"date:{tn}:{f}:+ES", f + " El Salvador"); put(f"date:{tn}:{f}:ES+", "El Salvador " + f)
            put(f"date:{tn}:{f}:+OD", f + " OVERDOSE"); put(f"date:{tn}:{f}:+MK", f + " Max Keiser")
    for sep in (" ", "", ", ", "-"):
        put(f"date:A_both:{sep!r}", sep.join((prim["A1"][0], prim["A2"][0])))
        put(f"date:B_both:{sep!r}", sep.join((prim["B1"][0], prim["B2"][0])))
        put(f"date:AB_first:{sep!r}", sep.join((prim["A1"][0], prim["B1"][0])))
        put(f"date:all4:{sep!r}", sep.join(prim[k][0] for k in ("A1", "A2", "B1", "B2")))
        iso = {k: f"{1900 + v[2]}-{v[0]:02d}-{v[1]:02d}" for k, v in trip.items()}
        put(f"date:iso_A_both:{sep!r}", sep.join((iso["A1"], iso["A2"])))
        put(f"date:iso_AB_first:{sep!r}", sep.join((iso["A1"], iso["B1"])))
        put(f"date:iso_all4:{sep!r}", sep.join(iso[k] for k in ("A1", "A2", "B1", "B2")))
    # the pairs as years
    for nm, d in FOUR:
        ys = [(1900 + p if p >= 30 else 2000 + p) for p in pairs_of(d)]
        for sep in (" ", "", ", ", "-"):
            put(f"date:years:{nm}:{sep!r}", sep.join(map(str, ys)))
        put(f"date:years19:{nm}", " ".join(str(1900 + p) for p in pairs_of(d)))
    # the serials as Unix epochs
    for nm, v in (("A", int(A_D)), ("B", int(B_D)), ("A+B", int(A_D) + int(B_D)),
                  ("A-B", int(A_D) - int(B_D)), ("hexA", int(A_D, 16)), ("hexB", int(B_D, 16))):
        t = datetime.datetime.fromtimestamp(v, datetime.timezone.utc)
        put(f"date:epoch:{nm}:date", t.strftime("%Y-%m-%d"))
        put(f"date:epoch:{nm}:datetime", t.strftime("%Y-%m-%d %H:%M:%S"))
        put(f"date:epoch:{nm}:iso", t.strftime("%Y-%m-%dT%H:%M:%SZ"))
        put(f"date:epoch:{nm}:compact", t.strftime("%Y%m%d"))
        put(f"date:epoch:{nm}:us", t.strftime("%-m/%-d/%Y"))
        put(f"date:epoch:{nm}:+ES", t.strftime("%Y-%m-%d") + " El Salvador")


def fam_geo(put):
    a, b = "76.841714", "46.279860"
    a7, b7 = "7.6841714", "4.6279860"
    es = [("13.76841714", "-88.46279860"), ("13.46279860", "-88.76841714"),
          ("13.7684", "-88.4628"), ("13.7684", "-88.4627"), ("13.768417", "-88.462799"),
          ("13.76841714", "-89.46279860"), ("14.76841714", "-88.46279860"),
          ("13.7684171", "-88.4627986"), ("13.768", "-88.462"),
          ("13.76841714", "88.46279860")]
    pairs = [(a, b), (b, a), ("-" + a, b), (a, "-" + b), ("-" + a, "-" + b), ("-" + b, a),
             (a7, b7), (b7, a7), ("-" + a7, b7), (a7, "-" + b7)] + es
    for i, (x, y) in enumerate(pairs):
        for sep in (", ", ",", " ", "/", ";", "\n"):
            put(f"geo:{i}:{sep!r}", x + sep + y)
        put(f"geo:{i}:geo_uri", f"geo:{x},{y}")
        put(f"geo:{i}:+ES", f"{x}, {y} El Salvador")
        put(f"geo:{i}:ES+", f"El Salvador {x}, {y}")
    for x, y in ((a, b), (a7, b7)):
        put(f"geo:NE:{x}", f"{x}N {y}E"); put(f"geo:NW:{x}", f"{x}N {y}W")
        put(f"geo:SE:{x}", f"{x}S {y}E"); put(f"geo:SW:{x}", f"{x}S {y}W")
        put(f"geo:N E:{x}", f"N{x} E{y}"); put(f"geo:N W:{x}", f"N{x} W{y}")
        put(f"geo:deg:{x}", f"{x}° {y}°"); put(f"geo:lat:{x}", f"lat {x} lon {y}")
        put(f"geo:latlon:{x}", f"lat={x}&lon={y}"); put(f"geo:q:{x}", f"{x},{y}")
    put("geo:dms:A", "76°84'17.14\""); put("geo:dms:B", "46°27'98.60\"")
    put("geo:dms:AB", "76°84'17.14\" 46°27'98.60\"")
    put("geo:dms2:A", "7°68'41.714\""); put("geo:dms2:B", "4°62'79.860\"")
    put("geo:elsalvador_capital", "13.6929, -89.2182")
    put("geo:elsalvador_capital+A", "13.6929, -89.2182 76841714")
    put("geo:elsalvador_capital+AB", "13.6929, -89.2182 76841714 46279860")


def fam_interleave(put):
    forms = [("Ad", A_D), ("Bd", B_D), ("AB", AB), ("BA", BA), ("As", A_STR), ("Bs", B_STR),
             ("AsBs", A_STR + B_STR)]
    for w in CLUE_WORDS:
        for fn, s in forms:
            put(f"il:word/{fn}:{w}", interleave(w, s)); put(f"il:{fn}/word:{w}", interleave(s, w))
        wl = w.replace(" ", "")
        if wl != w:
            put(f"il:wordnosp/Ad:{w}", interleave(wl, A_D)); put(f"il:wordnosp/AB:{w}", interleave(wl, AB))
            put(f"il:Ad/wordnosp:{w}", interleave(A_D, wl))
        for order in itertools.permutations(("w", "A", "B")):
            seqs = {"w": w, "A": A_D, "B": B_D}
            out, n = [], max(len(w), 8)
            for i in range(n):
                for k in order:
                    if i < len(seqs[k]): out.append(seqs[k][i])
            put(f"il:3way:{''.join(order)}:{w}", "".join(out))
        # the word's letters as separators between the two serials' digit pairs
        put(f"il:pairs_word:{w}", "".join(p + (w[i] if i < len(w) else "") for i, p in
                                          enumerate(re.findall("..", AB))))


# ---------------------------------------------------------------- API
_CACHE = None


def forms():
    global _CACHE
    if _CACHE is not None:
        return list(_CACHE)
    out, tags, seen = [], set(), set()

    def put(tag, val):
        if tag in tags: raise ValueError(f"duplicate tag {tag!r}")
        tags.add(tag)
        if not val or val in seen: return
        if val.startswith("hex:"):
            h = val[4:]
            if not h or len(h) % 2: return
            bytes.fromhex(h)
        seen.add(val); out.append((tag, val))
    for fam in (fam_a1z26, fam_ascii, fam_t9, fam_ciphers, fam_stride, fam_perm, fam_pointer,
                fam_xpointer, fam_nth, fam_clueidx, fam_sand, fam_polybius, fam_dates, fam_geo,
                fam_interleave):
        fam(put)
    _CACHE = out
    return list(out)


def selftest():
    ok = True

    def rep(msg, good):
        nonlocal ok; ok &= bool(good); print(f"  {msg}: {'OK' if good else 'FAIL'}")
    t0 = time.time(); F = forms(); dt = time.time() - t0
    D = dict(F); V = {v for _, v in F}
    rep(f"{len(F)} forms in {dt:.1f}s (<= 20000, < 30 s)", 0 < len(F) <= 20000 and dt < 30)
    rep(f"{len(F)} forms is under the sweep's 8,000-form HD threshold", len(F) <= 8000)
    rep("tags unique", len(D) == len(F))
    rep("no empty values, values unique", all(v for _, v in F) and len(V) == len(F))
    rep("hex: values are even-length hex", all(len(v) > 4 and len(v[4:]) % 2 == 0 and
                                              bytes.fromhex(v[4:]) is not None for v in V if v.startswith("hex:")))
    # A1Z26: 76 84 17 14 -> X F Q N ; 46 27 98 60 -> T A T H
    rep("a1z26 pairs mod 26: A -> XFQN", D.get("a1z:g2_mod26_1:A") == "XFQN")
    rep("a1z26 pairs mod 26: B -> TATH", D.get("a1z:g2_mod26_1:B") == "TATH")
    rep("a1z26 pairs mod 26: AB -> XFQNTATH", D.get("a1z:g2_mod26_1:AB") == "XFQNTATH")
    rep("a1z26 parse 7|6|8|4|1|7|1|4 -> GFHDAGAD", "GFHDAGAD" in V)
    rep("a1z26 parse 7|6|8|4|17|14 -> GFHDQN", "GFHDQN" in V)
    rep("B has no plain A1Z26 parse (trailing 0); zero-as-Z gives DFBGIHFZ",
        a1z26_parses(B_D) == [] and "DFBGIHFZ" in V)
    # ASCII: 76='L' 84='T' ; 46='.' 98='b' 60='<'
    rep("ASCII pairs printable: A -> 'LT', B -> '.b<'",
        D.get("asc:pairs_printable:A") == "LT" and D.get("asc:pairs_printable:B") == ".b<")
    rep("ASCII/A1Z26 mixed: A -> 'LTQN', B -> '.Ab<'",
        D.get("asc:pairs_mixed:A") == "LTQN" and D.get("asc:pairs_mixed:B") == ".Ab<")
    rep("ASCII pair bytes of A = hex:4c54110e", D.get("asc:pairs_bytes:A") == "hex:4c54110e")
    # keypad
    rep("keypad(OVERDOSE) = 68373673, keypad(SALVADOR) = 72582367",
        keypad("OVERDOSE") == "68373673" and keypad("SALVADOR") == "72582367")
    rep("T9 first letters of A = PMTGPG", D.get("t9:first:A") == "PMTGPG")
    rep("T9 sets of A = '[PQRS][MNO][TUV][GHI][PQRS][GHI]'",
        D.get("t9:sets_bracket:A") == "[PQRS][MNO][TUV][GHI][PQRS][GHI]")
    rep("OVERDOSE-keypad + A digit-wise mod 10 = 34114387", D.get("t9:dwsum:OVERDOSE:A") == "34114387")
    # ciphers, hand-computed
    rep("Caesar +12 of the headline = 'NUFOAUZ UE FAJUO MR'", D.get("cae:+12:headline") == "NUFOAUZ UE FAJUO MR")
    rep("Vigenere A-digits on OVERDOSE = VBMVEVTI", D.get("vig:enc:A:masthead") == "VBMVEVTI")
    rep("Vigenere decrypt inverts encrypt", vigenere(vigenere("El Salvador", digits(B_D), 1), digits(B_D), -1) == "El Salvador")
    rep("rail fence 2 of OVERDOSE = OEDSVROE", D.get("rail:enc2:masthead") == "OEDSVROE")
    rep("rail fence round trip", all(rail_dec(rail_enc("THEECONOMYOFLOVE", r), r) == "THEECONOMYOFLOVE" for r in RAILS))
    rep("columnar A on ELSALVADOR = LAADLREOVS", "".join(columnar_enc("ELSALVADOR", digits(A_D))) == "LAADLREOVS")
    rep("columnar round trip (irregular)", all("".join(columnar_dec(columnar_enc(s, k), k)) == s
                                               for s in ("ELSALVADOR", "BITCOINISTOXICAF", "X")
                                               for k in COL_KEYS.values()))
    rep("scytale 4 of OVERDOSE = ODVOESRE", scytale("OVERDOSE", 4) == "ODVOESRE")
    # interleave
    rep("ElSalvador x A = E7l6S8a4l1v7a1d4or", "E7l6S8a4l1v7a1d4or" in V)
    # pointers: page 76, line 8, word 4 (1-based) = 'of'  ("nonsense (and 10years of watching...")
    rep("pointer 76:8:4 (A, shape 2-1-1, as-printed page, 1-based) -> 'of'",
        D.get("ptr:A:211:as2:line:b1:words") == "of")
    p = ctx()["pages"]
    rep("pages 72 and 75-79 loaded with lines", sorted(p) == [72, 75, 76, 77, 78, 79] and all(p[k][0] for k in p))
    rep("38 highlighted runs loaded", len(ctx()["H"]) == 38)
    # pull-quote has 12 words; digits 7 6 8 4 1 7 1 4 pick them 1-based
    rep("pull-quote words by A (1-based) = 'more infinitely efficient love The more The love'",
        D.get("cidx:pullquote:A:words:b1") == "more infinitely efficient love The more The love")
    # Polybius 5x5 plain, 1-based, A pairs (7,6)(8,4)(1,7)(1,4) -> F O B D
    rep("Polybius 5x5 of A pairs = FOBD", D.get("poly:p5:A:b1:rc") == "FOBD")
    # dates and epochs
    rep("dates 7/6/84 and 1984-07-06 present", "7/6/84" in V and "1984-07-06" in V)
    rep("epoch 76841714 -> 1972-06-08", D.get("date:epoch:A:date") == "1972-06-08")
    rep("epoch 46279860 -> 1971-06-20", D.get("date:epoch:B:date") == "1971-06-20")
    rep("years reading of A = '1976 1984 2017 2014'", "1976 1984 2017 2014" in V)
    rep("geo '13.76841714, -88.46279860' present", "13.76841714, -88.46279860" in V)
    rep("geo '76.841714, 46.279860' present", "76.841714, 46.279860" in V)
    # things other modules own must not be re-emitted
    for gone in ("7684171446279860", "El Salvador 76841714", "CL76841714AKB46279860", "A41714867LC",
                 "76841714 46279860", "El Salvador"):
        rep(f"omits already-swept {gone!r}", gone not in V)
    fams = sorted({t.split(":")[0] for t, _ in F})
    rep(f"families present: {' '.join(fams)}",
        set(fams) >= {"a1z", "asc", "t9", "vig", "cae", "rail", "col", "scy", "str", "perm", "ptr",
                      "xptr", "nth", "cidx", "sand", "poly", "date", "geo", "il"})
    print("  SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
