#!/usr/bin/env python3
"""
LENS: numismatist / Bureau of Engraving and Printing production expert. Reads CL 76841714 A
(L12) and KB 46279860 as BANKNOTE DATA and pairs what they mean with the serials. ADDS: (1) BEP
production coordinates of each serial under the modern 3,200,000-note run of 100,000
32-subject sheets -- CL: run 25 (76,800,001-80,000,000), sheet 41,714, position A1; KB: run 15
(44,800,001-48,000,000), offset 1,479,860, sheet 79,860, position G2 letter-fastest or D3
number-fastest -- plus the older 6,400,000-note convention (runs 13 / 8, KB at H1 / B4), as
strings, as pairs and as 32-byte raw scalars; (2) the exact series with their signature pairs --
Series 2001 = Rosario Marin / Paul H. O'Neill (high confidence), Series 2006A = Anna Escobedo
Cabral / Henry M. Paulson Jr. (high confidence; 2006A kept the 2006 pair) -- the KB names with
the KB serial, both notes' names with the joined pair, and the cross-note pairs (Marin Cabral,
O'Neill Paulson); (3) Friedberg numbers Fr. 2177-L / Fr. 2181-B (LOW confidence, from memory);
(4) the K series letter was used only for Series 2006A, which exists only as a $100, so the KB
note is a second Franklin and $200 / two-hundred forms are added; (5) the legends actually
printed on the 1996-2006A $100 (legal-tender clause, Treasury-seal text and 1789, THE FEDERAL
RESERVE SYSTEM, USA 100, the two office titles) with the KB serial and the pair; (6) the
pre-1996 single-letter district style (L76841714A, B46279860); (7) star / replacement forms;
(8) the pair read as ONE banknote record -- prefix letters together, digits together, suffix,
district and series appended -- with its reversal, rot180 and mirror readings via
mirror_serial's tables; (9) collector catalogue lines per note and for the pair. Each per-note
token is paired with its own note's digits and full serial (joins "", " ", "-", plus the
lower-cased no-space brainwallet form) and with CL76841714AKB46279860; pair tokens with the
joined serials in both orders. OMITS, because already swept: the bare series years, district
names / numbers and the $100 / Franklin / In God We Trust / Federal Reserve Note / Independence
Hall vocabulary x the six digit-forms (serial_combine.string_forms -- that vocabulary is
snapshotted below as SC_WORDS and those exact pairings are skipped statically, without
importing that module); every signatory-name variant and every legend x the CL serial / its
digits / L12 / 2001 (note_signatures); KB46279860 + a suffix letter and the page-72 text
(page72); reversal / rot180 / mirror of each serial alone (mirror_serial, serial2_exhaust);
numeric arithmetic on the serials and the BFS closure (serial_combine). Dropped after review as
filler or wrong for this note: generic BEP glossary words (quadrant, check letter, face plate
...), the naive C=Philadelphia / K=Dallas misreading, E PLURIBUS UNUM and Washington D.C.
(not printed on the 1996-2006A $100), and BIP-32 path: values (outside the plugin contract).
SPECULATIVE families: Friedberg numbers, plate-position ordering, the 6.4M-run variant, the
star forms, raw-int keys. Imports: stdlib and mirror_serial only.
"""
import itertools, sys, time
import mirror_serial as MS          # stdlib-only repo module: rot180 / mirror tables

A_L, A_D, A_S, A_DIST, A_SER = "CL", "76841714", "A", "L12", "2001"
B_L, B_D, B_DIST, B_SER = "KB", "46279860", "B2", "2006A"
A_STR, B_STR = "CL76841714A", "KB46279860"
A_SP, B_SP = "CL 76841714 A", "KB 46279860"
AB_D, BA_D = A_D + B_D, B_D + A_D
AB_S, BA_S = A_STR + B_STR, B_STR + A_STR
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
STAR = "★"

RUN, SHEETS = 3_200_000, 100_000          # modern 32-subject run: 100,000 sheets
RUN_OLD, SHEETS_OLD = 6_400_000, 200_000  # older 32-subject convention
POS = "ABCDEFGH"

# (series, Treasurer of the United States, Secretary of the Treasury)
SIGS = {"2001": ("Rosario Marin", "Paul H. O'Neill"),
        "2006A": ("Anna Escobedo Cabral", "Henry M. Paulson Jr.")}
FRIEDBERG = {"A": "2177-L", "B": "2181-B"}     # low confidence, from memory

# which serial forms each token family is paired with
A_FORMS, B_FORMS = [A_D, A_STR], [B_D, B_STR]
PAIR_FORMS = [AB_S]                  # per-note tokens x the joined pair
PAIR_FORMS_X = [AB_S, AB_D, BA_S]    # pair tokens: both digit-only and KB-first too

# ---- static snapshot of what serial_combine.string_forms() already emits, so those exact
# strings are not re-emitted here WITHOUT importing that module: its `letters` / `series` /
# `district` / `note` vocabulary x its six digit-forms, its clue words x its six pair forms,
# its partsA x partsB x ten separators (each in both orders, joins "" and " "), and its
# mirror-family outputs of the joined digits. Compared lower-cased because it also emits
# .lower() / .upper() of every string.
SC_WORDS = (
    "CL", "KB", "CLKB", "KBCL", "CLAKB", "CLA KB", "CKLB", "CL KB", "CL A KB", "CLA", "LB", "CK",
    "L12 B2", "L12B2", "L B", "12 2", "122", "212", "1202", "0212", "3 12 1 11 2", "3121112",
    "03 12 01 11 02", "0312011102", "3-12-1-11-2",
    "2001", "2006", "2006A", "20012006", "2001 2006", "20062001", "2006 2001", "Series 2001",
    "Series 2006A", "2001 2006A",
    "San Francisco", "New York", "San Francisco New York", "New York San Francisco",
    "Federal Reserve Bank of San Francisco", "Federal Reserve Bank of New York", "L12", "B2",
    "12", "2", "twelve", "two", "L 12 B 2",
    "100", "$100", "one hundred dollars", "Franklin", "Benjamin Franklin", "Federal Reserve Note",
    "In God We Trust", "United States of America", "The United States of America",
    "Independence Hall", "hundred", "twenty", "20")
SC_FORMS = (A_D, B_D, AB_D, A_D + " " + B_D, AB_S, A_STR + " " + B_STR)
SC_CLUES = ("El Salvador", "el salvador", "ELSALVADOR", "OVERDOSE", "Overdose", "Max Keiser",
            "Bukele", "bitcoin", "Bitcoin", "mirror", "George Sand", "20 BTC", "20BTC",
            "Bitcoin Magazine", "Issue 24", "24", "72", "79", "7279")
SC_CLUE_FORMS = (AB_D, A_D + " " + B_D, AB_S, A_STR + " " + B_STR, BA_D, BA_S)
SC_PARTS_A = (A_STR, A_D, A_L + A_D, A_D + A_S, A_SP, A_DIST + A_D, A_D + A_DIST)
SC_PARTS_B = (B_STR, B_D, B_SP, B_L)
SC_SEPS = ("", " ", "-", "/", "\n", "_", ".", ",", "|", "+")


def _sc_snapshot():
    S = set()
    for words, ds in ((SC_WORDS, SC_FORMS), (SC_CLUES, SC_CLUE_FORMS)):
        for w in words:
            S.add(w)
            for d in ds:
                for jn in ("", " "):
                    S.add(w + jn + d); S.add(d + jn + w)
    for x in SC_PARTS_A:
        for y in SC_PARTS_B:
            for sep in SC_SEPS:
                S.add(x + sep + y); S.add(y + sep + x)
    S |= {MS.rot180(A_D) + MS.rot180(B_D), MS.rot180(AB_D), MS.mirror(AB_D), MS.mirror(AB_S),
          AB_D[::-1], BA_D[::-1], A_D[::-1] + B_D[::-1], B_D[::-1] + A_D[::-1]}
    return {s.lower() for s in S}


# exact strings other modules already ran through the full stack, which a family below would
# otherwise re-emit: page72 / serial2_exhaust (KB + suffix letter and its reversal) and
# mirror_serial (the CL serial's own mirror family).
KNOWN_SWEPT = {"kb46279860a", "46279860a", "a06897264bk", "a41714867lc", "41714867",
               "a 41714867 lc"}
SWEPT = _sc_snapshot() | KNOWN_SWEPT


def _sc_covered(v):
    """True when serial_combine.string_forms() (or the modules above) already emits v."""
    return v.lower() in SWEPT


def production(serial, run=RUN, sheets=SHEETS):
    """BEP production coordinates of a serial number under a run/sheet convention."""
    n = int(serial) - 1
    r, off = divmod(n, run)
    pos, sh = divmod(off, sheets)
    return {"run": r + 1, "run0": r, "start": r * run + 1, "end": (r + 1) * run,
            "off": off + 1, "sheet": sh + 1, "posidx": pos,
            "pos": f"{POS[pos % 8]}{pos // 8 + 1}",       # A1,B1,..,H1,A2,..
            "pos_alt": f"{POS[pos // 4]}{pos % 4 + 1}"}   # A1,A2,A3,A4,B1,..


PA, PB = production(A_D), production(B_D)
PA_OLD, PB_OLD = production(A_D, RUN_OLD, SHEETS_OLD), production(B_D, RUN_OLD, SHEETS_OLD)


def note_tokens():
    """(note, group, token, own): what each note's serial identifies. own=True pairs the token
    with that note's own digits / full serial as well as with the joined pair; the CL note's
    signatories are pair-only because note_signatures already crossed every name variant with
    the CL serial, its digits, L12 and 2001."""
    tA, sA = SIGS["2001"]; tB, sB = SIGS["2006A"]
    T = []
    def add(note, g, own, *xs):
        for x in xs: T.append((note, g, x, own))
    # ---- CL 76841714 A: Series 2001 (series letter C), district L12 San Francisco
    add("A", "series", True, "Series C", "Series 2001", "SERIES 2001", "2001", "C 2001")
    add("A", "sig", False, tA, sA, "Marin", "O'Neill", "ONeill", "Paul O'Neill",
        "Marin O'Neill", "O'Neill Marin", "Marin ONeill", f"{tA} {sA}")
    add("A", "district", True, "L 12", "Twelfth District", "12th District",
        "Twelfth Federal Reserve District", "FRB San Francisco", "San Francisco 12",
        "L12 San Francisco")
    add("A", "prod", True, f"run {PA['run']}", str(PA['run']), str(PA['run0']), str(PA['sheet']),
        f"sheet {PA['sheet']}", PA['pos'], f"position {PA['pos']}", str(PA['start']),
        f"run {PA['run']} sheet {PA['sheet']} {PA['pos']}",
        f"{PA['run']}/{PA['sheet']}/{PA['pos']}", f"{PA['run']}-{PA['sheet']}-{PA['pos']}",
        f"run {PA_OLD['run']}", f"{PA['start']}-{PA['end']}")
    add("A", "fr", True, f"Fr. {FRIEDBERG['A']}", FRIEDBERG['A'],
        f"Fr.{FRIEDBERG['A'].replace('-', '')}", FRIEDBERG['A'].split("-")[0])
    add("A", "block", True, "CL-A", "CL..A")
    # ---- KB 46279860: Series 2006A (series letter K), district B2 New York
    add("B", "series", True, "Series 2006A", "SERIES 2006A", "2006A", "Series K", "K 2006A")
    add("B", "sig", True, tB, sB, "Cabral", "Paulson", "Anna Cabral", "Henry Paulson",
        "Hank Paulson", "Cabral Paulson", "Paulson Cabral", f"{tB} {sB}")
    add("B", "district", True, "B 2", "B2", "New York", "Second District", "2nd District",
        "Second Federal Reserve District", "FRB New York", "New York 2", "B2 New York",
        "Federal Reserve Bank of New York")
    add("B", "prod", True, f"run {PB['run']}", str(PB['run']), str(PB['run0']), str(PB['sheet']),
        f"sheet {PB['sheet']}", str(PB['off']), PB['pos'], PB['pos_alt'],
        f"position {PB['pos']}", str(PB['start']),
        f"run {PB['run']} sheet {PB['sheet']} {PB['pos']}",
        f"{PB['run']}/{PB['sheet']}/{PB['pos']}", f"{PB['run']}-{PB['sheet']}-{PB['pos']}",
        f"{PB['run']}/{PB['sheet']}/{PB['pos_alt']}", f"run {PB_OLD['run']}",
        f"{PB['start']}-{PB['end']}")
    add("B", "fr", True, f"Fr. {FRIEDBERG['B']}", FRIEDBERG['B'],
        f"Fr.{FRIEDBERG['B'].replace('-', '')}", FRIEDBERG['B'].split("-")[0])
    add("B", "block", True, "KB-A", "KB..A")
    return T


def pair_tokens():
    """(group, token): facts about the two notes TOGETHER."""
    tA, sA = SIGS["2001"]; tB, sB = SIGS["2006A"]
    T = []
    def add(g, *xs):
        for x in xs: T.append((g, x))
    add("series", "Series 2001 Series 2006A", "2001 2006A", "C K", "CK", "Series C Series K")
    add("sig", "Marin O'Neill Cabral Paulson", "Cabral Paulson Marin O'Neill", "Marin Cabral",
        "O'Neill Paulson", "Cabral Marin", "Paulson O'Neill", f"{tA} {tB}", f"{sA} {sB}")
    add("district", "L B", "LB", "L12 B2", "12 2", "Twelfth Second", "12th 2nd",
        "San Francisco New York", "New York San Francisco")
    add("prod", f"{PA['run']} {PB['run']}", f"{PA['run']}{PB['run']}", f"{PB['run']}{PA['run']}",
        f"{PA['run0']} {PB['run0']}", str(PA['run'] + PB['run']),
        f"{PA['sheet']} {PB['sheet']}", f"{PA['sheet']}{PB['sheet']}",
        f"{PB['sheet']}{PA['sheet']}", str(PA['sheet'] + PB['sheet']),
        f"{PA['pos']} {PB['pos']}", f"{PA['pos']}{PB['pos']}", f"{PA['pos']} {PB['pos_alt']}",
        f"{PA['pos']}{PB['pos_alt']}", f"run {PA['run']} run {PB['run']}",
        f"{PA['run']}/{PA['sheet']}/{PA['pos']} {PB['run']}/{PB['sheet']}/{PB['pos']}")
    add("fr", f"Fr. {FRIEDBERG['A']} Fr. {FRIEDBERG['B']}", "2177 2181",
        f"{FRIEDBERG['A']} {FRIEDBERG['B']}")
    add("denom", "$100 $100", "100 100", "Franklin Franklin", "two Franklins", "$200",
        "two hundred dollars", "TWO HUNDRED DOLLARS", "two Benjamins", "CL-A KB-A", "CLA KBA")
    return T


# legends printed on the Series 1996-2006A $100 (note_signatures already crossed the first
# five, plus Franklin / Independence Hall / San Francisco, with the CL forms; here they meet
# the KB serial and the pair). E PLURIBUS UNUM and Washington, D.C. are NOT on this note.
LEGENDS = ["THE UNITED STATES OF AMERICA", "FEDERAL RESERVE NOTE",
           "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE", "ONE HUNDRED DOLLARS",
           "IN GOD WE TRUST", "Treasurer of the United States", "Secretary of the Treasury",
           "THE DEPARTMENT OF THE TREASURY 1789", "THE FEDERAL RESERVE SYSTEM", "USA 100"]
LEGEND_FORMS = [B_STR, B_D, AB_S, AB_D]


def catalogue_entries():
    """Per-note catalogue lines a collector would write, and the pair joined."""
    tA, sA = SIGS["2001"]; tB, sB = SIGS["2006A"]
    s, fa = A_STR, FRIEDBERG['A']
    A = [f"$100 Series 2001 San Francisco {s}",
         f"Series 2001 $100 Federal Reserve Note San Francisco L12 {s}",
         f"{s} L12 Series 2001 Marin O'Neill",
         f"{s} Series 2001 L12 San Francisco $100 Marin O'Neill Fr. {fa}",
         f"Fr. {fa} {s}", f"2001 L12 {s} Marin O'Neill 100",
         f"{s} 2001 12 {PA['pos']} {PA['sheet']} {PA['run']}",
         f"{s} {tA} {sA}", f"{tA} {sA} {s}", f"{s} Marin O'Neill"]
    s, fb = B_STR, FRIEDBERG['B']
    B = [f"$100 Series 2006A New York {s}",
         f"Series 2006A $100 Federal Reserve Note New York B2 {s}",
         f"{s} B2 Series 2006A Cabral Paulson",
         f"{s} Series 2006A B2 New York $100 Cabral Paulson Fr. {fb}",
         f"Fr. {fb} {s}", f"2006A B2 {s} Cabral Paulson 100",
         f"{s} 2006A 2 {PB['pos']} {PB['sheet']} {PB['run']}",
         f"{s} {tB} {sB}", f"{tB} {sB} {s}", f"{s} Cabral Paulson"]
    out = list(A) + list(B)
    for x, y in zip(A, B):
        for j in (" ", "\n", "; ", ""):
            out.append(x + j + y); out.append(y + j + x)
    return out


def single_record():
    """The pair as ONE banknote data record: letters together, digits together, suffix."""
    letters = ["CLKB", "KBCL", "CKLB"]
    base, out = [], []
    for L, sep, suf in itertools.product(letters, ("", " "), ("A", "")):
        # compact digit block; with a spaced record also the two digit groups kept apart
        digits = [AB_D, BA_D] + ([A_D + " " + B_D, B_D + " " + A_D] if sep else [])
        tails = (["L12B2", "20012006A", "L12B220012006A"] if not sep
                 else ["L12 B2", "2001 2006A", "L12 B2 2001 2006A"])
        for D in digits:
            rec = L + sep + D + (sep + suf if suf else "")
            base.append(rec)
            out.append(rec)
            for t in tails:
                out.append(rec + sep + t)
    # the printed field order of each note, concatenated as one line
    for j in (" ", "", " | ", "; "):
        out.append(f"C L {A_D} A L 12 2001{j}K B {B_D} B 2 2006A")
        out.append(f"CL {A_D} A L12{j}KB {B_D} B2")
        out.append(f"CL,{A_D},A,L12,2001,100{j}KB,{B_D},,B2,2006A,100")
    # interleaved character-wise, and letter-sorted
    out += ["".join(a + b for a, b in zip(A_STR, B_STR)) + A_STR[len(B_STR):],
            "BCKL" + AB_D + "A", "BCKL " + AB_D + " A"]
    return base, out


def old_style():
    """Pre-1996 single-letter district serials: the series letter dropped."""
    a = ["L76841714A", "L 76841714 A", "L76841714"]
    b = ["B46279860", "B 46279860", "B46279860A"]
    out = list(a) + list(b)
    for x in a:
        for y in b:
            for j in ("", " ", "-"):
                out.append(x + j + y); out.append(y + j + x)
    out += ["LB" + AB_D + "A", "LB " + AB_D + " A", "L12 76841714 A B2 46279860",
            "L1276841714AB246279860", "12 76841714 A 2 46279860"]
    return out


def star_forms():
    """Replacement-note convention: a star in place of the suffix letter."""
    out = []
    for st in ("*", STAR):
        a = [f"CL76841714{st}", f"CL 76841714 {st}"]
        b = [f"KB46279860{st}", f"KB 46279860 {st}"]
        out += a + b
        for x in a:
            for y in b:
                for j in ("", " "):
                    out.append(x + j + y); out.append(y + j + x)
        out += [f"CL76841714{st}KB46279860", f"CL76841714A KB46279860{st}",
                f"CL76841714AKB46279860{st}", f"star note CL76841714{st}",
                f"KB46279860{st} star note", f"{st}76841714{st}46279860{st}"]
    return out


def production_strings():
    out = []
    for lab, p in (("CL", PA), ("KB", PB)):
        out += [f"run {p['run']} sheet {p['sheet']} position {p['pos']}",
                f"{p['run']} {p['sheet']} {p['pos']}", f"{p['run']}{p['sheet']}{p['pos']}",
                f"{lab} run {p['run']} sheet {p['sheet']} {p['pos']}",
                f"{lab}{p['run']}{p['sheet']}{p['pos']}", f"{p['pos']} {p['sheet']}",
                f"{p['pos']}{p['sheet']}", f"{p['run']} {p['off']}", f"{p['run']}{p['off']:07d}",
                f"{p['start']}-{p['end']}", f"{p['start']} {p['end']}"]
    out += [f"{PA['start']}-{PA['end']} {PB['start']}-{PB['end']}",
            f"CL {PA['start']} A - CL {PA['end']} A", f"KB {PB['start']} - KB {PB['end']}",
            f"CL{PA['start']}A-CL{PA['end']}A", f"KB{PB['start']}-KB{PB['end']}",
            f"{PA['run']} {PA['sheet']} {PA['pos']} {PB['run']} {PB['sheet']} {PB['pos']}",
            f"{PA['run']}{PA['sheet']}{PA['pos']}{PB['run']}{PB['sheet']}{PB['pos']}",
            f"{PA['pos']} {PA['sheet']} {PB['pos']} {PB['sheet']}",
            f"{PA['pos']}{PA['sheet']}{PB['pos']}{PB['sheet']}",
            f"{PA['run']}/{PA['sheet']}/{PA['pos']} {PB['run']}/{PB['sheet']}/{PB['pos']}",
            f"{PA['run']}/{PA['sheet']}/{PA['pos']} {PB['run']}/{PB['sheet']}/{PB['pos_alt']}",
            f"{PA_OLD['run']} {PA_OLD['sheet']} {PA_OLD['pos']} {PB_OLD['run']} {PB_OLD['sheet']} {PB_OLD['pos']}",
            f"{PA['off']} {PB['off']}", f"{PA['off']}{PB['off']}", f"{PB['off']}{PA['off']}",
            f"{A_D} {PA['run']} {PA['sheet']} {PA['pos']} {B_D} {PB['run']} {PB['sheet']} {PB['pos']}",
            f"{A_STR} {PA['pos']} {B_STR} {PB['pos']}", f"{A_STR}{PA['pos']}{B_STR}{PB['pos']}",
            f"{A_STR} {PA['pos']} {B_STR} {PB['pos_alt']}"]
    return out


def raw_int_keys():
    """Production numbers as raw 32-byte scalars (speculative, near-zero entropy)."""
    vals = {"A.run": PA['run'], "A.run0": PA['run0'], "A.sheet": PA['sheet'], "A.off": PA['off'],
            "A.start": PA['start'], "B.run": PB['run'], "B.run0": PB['run0'],
            "B.sheet": PB['sheet'], "B.off": PB['off'], "B.start": PB['start'],
            "runs": int(f"{PA['run']}{PB['run']}"), "runs_rev": int(f"{PB['run']}{PA['run']}"),
            "sheets": int(f"{PA['sheet']}{PB['sheet']}"),
            "sheets_rev": int(f"{PB['sheet']}{PA['sheet']}"),
            "sheets_sum": PA['sheet'] + PB['sheet'], "runs_sum": PA['run'] + PB['run'],
            "run_sheet_A": (PA['run'] << 32) | PA['sheet'],
            "run_sheet_B": (PB['run'] << 32) | PB['sheet'],
            "A_then_B": (PA['sheet'] << 32) | PB['sheet'],
            "posidx_sheets": int(f"{PA['posidx']}{PA['sheet']}{PB['posidx']}{PB['sheet']}"),
            "starts": int(f"{PA['start']}{PB['start']}"),
            "record": int(AB_D + "1"), "record_rev": int(BA_D + "1")}
    out = []
    for k, v in vals.items():
        if 0 < v < N:
            out.append((f"int:{k}={v}", "hex:" + v.to_bytes(32, "big").hex()))
    # the two sheet numbers and run numbers packed as 4-byte words (8 and 16 bytes)
    pk = PA['sheet'].to_bytes(4, "big") + PB['sheet'].to_bytes(4, "big")
    out.append(("int:sheets_be8", "hex:" + pk.hex()))
    out.append(("int:sheets_be8x2", "hex:" + (pk * 2).hex()))
    pk2 = b"".join(x.to_bytes(4, "big") for x in (PA['run'], PA['sheet'], PB['run'], PB['sheet']))
    out.append(("int:run_sheet_be16", "hex:" + pk2.hex()))
    return out


def _squash(s):
    """The brainwallet habit: lower-case, spaces removed."""
    return s.lower().replace(" ", "")


def forms():
    out, vals = [], {}
    def put(tag, v):
        if not v or v in vals or _sc_covered(v): return
        vals[v] = tag; out.append((tag, v))
    def put_lower(tag, v):
        put(tag, v)
        if v.lower() != v: put(tag + "/l", v.lower())

    def cross(tag, t, serials, joins):
        """token x serial forms, both orders, the given joins, plus the squashed form
        (strings serial_combine.string_forms() already emits are dropped by put())."""
        for j, s in enumerate(serials):
            for jn_i, jn in enumerate(joins):
                put(f"{tag}:{j}:{jn_i}:ts", t + jn + s)
                put(f"{tag}:{j}:{jn_i}:st", s + jn + t)
            put(f"{tag}:{j}:sq:ts", _squash(t + s))
            put(f"{tag}:{j}:sq:st", _squash(s + t))

    # 1. per-note tokens x own serial forms ("", " ", "-") and x the joined pair ("", " ")
    for i, (note, g, t, own) in enumerate(note_tokens()):
        if own:
            cross(f"own:{note}.{g}:{i}", t, A_FORMS if note == "A" else B_FORMS, ("", " ", "-"))
        cross(f"pair:{note}.{g}:{i}", t, PAIR_FORMS, ("", " "))
    # 2. pair tokens x the joined serials (both orders, digits-only too)
    for i, (g, t) in enumerate(pair_tokens()):
        cross(f"both:{g}:{i}", t, PAIR_FORMS_X, ("", " "))
    # 3. printed legends x the KB serial and the pair (" " join and squashed only)
    for i, t in enumerate(LEGENDS):
        cross(f"legend:{i}", t, LEGEND_FORMS, (" ",))
    # 4. catalogue entries, single record, old style, stars, production strings
    for i, v in enumerate(catalogue_entries()): put_lower(f"cat:{i}", v)
    base, rec = single_record()
    for i, v in enumerate(rec): put_lower(f"record:{i}", v)
    old = old_style()
    for i, v in enumerate(old): put_lower(f"oldstyle:{i}", v)
    stars = star_forms()
    for i, v in enumerate(stars): put(f"star:{i}", v)
    for i, v in enumerate(production_strings()): put_lower(f"prod:{i}", v)
    # 5. reversal / rot180 / mirror of the letters+digits of BOTH notes together
    #    (mirror_serial's own readings() cover the CL serial alone; serial_combine covers the
    #    joined digits and mirror(CL76841714AKB46279860) -- those are in KNOWN_SWEPT)
    mir_src = [AB_S, BA_S, A_SP + " " + B_SP, B_SP + " " + A_SP, A_STR + " " + B_STR,
               B_STR + " " + A_STR, A_STR + "KB46279860A"] + base + old[:6] + stars[:8]
    for i, v in enumerate(mir_src):
        put(f"mirror:{i}:rev", v[::-1])
        put(f"mirror:{i}:rot180", MS.rot180(v))
        put(f"mirror:{i}:mirror", MS.mirror(v))
        put(f"mirror:{i}:rot180_nospace", MS.rot180(v).replace(" ", ""))
    # 6. production numbers as raw scalars
    for tag, v in raw_int_keys(): put(tag, v)
    return out


def selftest():
    ok = True
    def rep(msg, good):
        nonlocal ok; ok &= bool(good); sys.stderr.write(f"  {msg}: {'OK' if good else 'FAIL'}\n")
    # production numbers, hand-verified: 24 x 3,200,000 = 76,800,000; 76,841,714 - 76,800,000 = 41,714
    rep("CL 76841714 -> run 25, sheet 41714, position A1",
        (PA['run'], PA['sheet'], PA['pos'], PA['pos_alt'], PA['start']) == (25, 41714, "A1", "A1", 76800001))
    # 14 x 3,200,000 = 44,800,000; 46,279,860 - 44,800,000 = 1,479,860 = 14 x 100,000 + 79,860
    rep("KB 46279860 -> run 15, offset 1479860, sheet 79860, position G2 (alt D3)",
        (PB['run'], PB['off'], PB['sheet'], PB['pos'], PB['pos_alt']) == (15, 1479860, 79860, "G2", "D3"))
    rep("6.4M-run convention: CL run 13 A1, KB run 8 H1 (alt B4)",
        (PA_OLD['run'], PA_OLD['pos'], PB_OLD['run'], PB_OLD['pos'], PB_OLD['pos_alt']) == (13, "A1", 8, "H1", "B4"))
    rep("static serial_combine snapshot: covers its word x digit-form, clue x pair and partsA x partsB "
        "strings, not the CL76841714A / KB46279860 pairings this module adds",
        all(_sc_covered(x) for x in ("Series 2001 76841714", "SERIES 200176841714",
                                     "24 CL76841714AKB46279860", "CKLB 76841714 46279860",
                                     "L1276841714|KB", "46279860b2", MS.mirror(AB_S)))
        and not any(_sc_covered(x) for x in ("Series 2001 CL76841714A", "Series 2006A KB46279860",
                                             "series200176841714", "run 25 76841714")))
    t0 = time.time(); F = forms(); dt = time.time() - t0
    V = {v for _, v in F}
    n_plain = sum(1 for _, v in F if not v.startswith("hex:"))
    rep(f"{len(F):,} forms ({n_plain:,} plain text) built in {dt:.1f}s (<= 20,000, < 30 s)",
        0 < len(F) <= 20000 and dt < 30)
    rep(f"plain-text forms stay under serial_combine's 8,000 HD-seed threshold", n_plain < 8000)
    rep("no empty values", all(v for _, v in F))
    rep("unique tags", len({t for t, _ in F}) == len(F))
    rep("unique values", len(V) == len(F))
    rep("only text and hex: values", all(not v.startswith(("path:", "mn:")) for v in V))
    rep("no value in the already-swept snapshot", not any(_sc_covered(v) for v in V))
    for want in ("CLKB7684171446279860A", "CLKB 76841714 46279860 A L12 B2",
                 "L76841714A B46279860", "CL76841714" + STAR, "CL76841714* KB46279860*",
                 "Anna Escobedo Cabral KB46279860", "KB46279860-Anna Escobedo Cabral",
                 "annaescobedocabralkb46279860", "SERIES 2006A KB46279860", "series2006akb46279860",
                 "Series 2001 CL76841714A", "Fr. 2181-B-KB46279860", "KB46279860 run 15",
                 "Cabral Paulson CL76841714AKB46279860", "Marin Cabral 7684171446279860",
                 "Paul H. O'Neill CL76841714AKB46279860", "$200 CL76841714AKB46279860",
                 "KB46279860CL76841714A Series 2001 Series 2006A",
                 "run 25 sheet 41714 position A1", "run 15 sheet 79860 position G2",
                 "A1 41714 G2 79860", "$100 Series 2001 San Francisco CL76841714A",
                 "Fr. 2177-L CL76841714A", "76841714 76800001-80000000",
                 "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE KB46279860",
                 "USA 100 CL76841714AKB46279860",
                 "09867294BKA417148977C",            # rot180 of CL76841714AKB46279860
                 "A0986729441714897BK7C",            # rot180 of CLKB7684171446279860A
                 "hex:" + (41714).to_bytes(32, "big").hex(),
                 "hex:" + (4171479860).to_bytes(32, "big").hex()):
        rep(f"contains {want!r}", want in V)
    # things other modules already sweep must NOT be re-emitted
    for gone in ("Series 2001 76841714", "series 200176841714", "Series 2006A 46279860",
                 "San Francisco 7684171446279860", "New York 46279860", "KB46279860A",
                 "Rosario Marin CL76841714A", "Rosario Marin 76841714", "A41714867LC",
                 "A06897264BK", MS.mirror(AB_S), "24 CL76841714AKB46279860", "46279860b2",
                 "7684171446279860ck", "CKLB 76841714 46279860", "quadrant46279860",
                 "E PLURIBUS UNUM KB46279860", "block A 76841714"):
        rep(f"omits already-swept / dropped {gone!r}", gone not in V)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
