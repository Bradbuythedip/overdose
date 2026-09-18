#!/usr/bin/env python3
"""
LENS: numismatist / Bureau of Engraving and Printing production expert. Reads the two
serials CL 76841714 A (L12) and KB 46279860 as BANKNOTE DATA and combines what they mean
with the serials themselves. ADDS: (1) BEP production numbers derived from each serial --
run number under the modern 3,200,000-note run (CL: run 25, starts 76,800,001; KB: run 15,
starts 44,800,001), offset in run, sheet number on a 100,000-sheet run (41714 / 79860),
32-subject plate position (CL: A1 under both position orderings; KB: G2 letter-fastest or
D3 number-fastest), the older 6,400,000-note convention (runs 13/8, KB at H1/B4), run
serial ranges, and all of these as strings, as combined pairs, as 32-byte raw keys and
as BIP-32 path components; (2) the exact series with their signature pairs -- Series 2001
= Rosario Marin / Paul H. O'Neill (high confidence), Series 2006A = Anna Escobedo Cabral
/ Henry M. Paulson Jr. (high confidence; 2006A kept the 2006 signatures) -- paired with
the KB serial and with BOTH serials, and the cross-note pairs (Marin Cabral, O'Neill
Paulson); (3) Friedberg catalogue numbers Fr. 2177-L / Fr. 2181-B (LOW confidence, from
memory); (4) the K prefix was used only for Series 2006A, which exists only as a $100,
so the KB note is treated as a second Franklin and $200 / two-hundred forms are added;
(5) legends not yet crossed with KB or with the pair: the legal-tender clause, Treasurer /
Secretary titles, Treasury-seal text and 1789, FEDERAL RESERVE SYSTEM, USA 100, E PLURIBUS
UNUM, Washington D.C., BEP / FW / Fort Worth, 32-subject and run-size constants; (6) the
naive district misreading of the series letters (C3 Philadelphia, K11 Dallas); (7) the
pre-1996 single-letter district style (L76841714A, B46279860); (8) star / replacement
forms (* and U+2605 in place of the suffix); (9) the pair read as ONE banknote record
(prefix letters together, digits together, suffix, district and series appended), its
reversals, and rot180 / mirror readings of the letters+digits together via mirror_serial;
(10) catalogue-entry strings per note and for the pair. Every token is paired with
76841714 / 46279860 / CL76841714A / KB46279860 and the two joined serials, both orders,
with "", " " and "-" joins, plus lower/upper variants. OMITS, because already swept:
bare series years, district names/numbers, $100 / Franklin / In God We Trust / Federal
Reserve Note / Independence Hall and alphabet positions x the six digit-forms
(serial_combine.string_forms); signatories x the CL serial / L12 / series and legends x
the CL serial (note_signatures); KB+suffix-letter and page-72 text (page72); rot180 /
mirror of each serial alone (mirror_serial, serial2_exhaust); numeric arithmetic on the
serials and BFS closure (serial_combine). Exact duplicates of those modules' outputs are
removed at build time. SPECULATIVE families: Friedberg numbers, plate-position ordering,
the 6.4M-run variant, path: forms, naive-district misreads, raw-int keys.
"""
import itertools, sys, time

A_L, A_D, A_S, A_DIST, A_SER = "CL", "76841714", "A", "L12", "2001"
B_L, B_D, B_DIST, B_SER = "KB", "46279860", "B2", "2006A"
A_STR, B_STR = "CL76841714A", "KB46279860"
A_SP, B_SP = "CL 76841714 A", "KB 46279860"
AB_D, BA_D = A_D + B_D, B_D + A_D
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
STAR = "★"

RUN, SHEETS = 3_200_000, 100_000          # modern 32-subject run: 100,000 sheets
RUN_OLD, SHEETS_OLD = 6_400_000, 200_000  # older 32-subject convention
POS = "ABCDEFGH"

# (series, Treasurer of the United States, Secretary of the Treasury)
SIGS = {"2001": ("Rosario Marin", "Paul H. O'Neill"),
        "2006A": ("Anna Escobedo Cabral", "Henry M. Paulson Jr.")}
FRIEDBERG = {"A": "2177-L", "B": "2181-B"}     # low confidence, from memory

# the six serial forms every token is paired with
SERIAL_FORMS = [A_D, B_D, A_STR, B_STR, A_STR + B_STR, AB_D]


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


def _names(full):
    parts = full.replace(" Jr.", "").split()
    sur = parts[-1]
    out = [full, sur, f"{parts[0]} {sur}"]
    if "'" in sur: out.append(sur.replace("'", ""))
    if len(parts) == 3 and "." not in parts[1]: out.append(f"{parts[1]} {sur}")
    return out


def tokens():
    """(group, token) numismatic facts about the notes."""
    T = []
    def add(g, *xs):
        for x in xs: T.append((g, x))
    tA, sA = SIGS["2001"]; tB, sB = SIGS["2006A"]
    # ---- the CL note: Series 2001, district L12 San Francisco
    add("A.series", "Series 2001", "SERIES 2001", "Series C")
    add("A.sig", *_names(tA), *_names(sA), "Marin O'Neill", "O'Neill Marin",
        "Marin ONeill", f"{tA} {sA}", f"{sA} {tA}")
    add("A.district", "L 12", "SAN FRANCISCO", "Twelfth District", "12th District",
        "Twelfth Federal Reserve District", "FRB San Francisco", "San Francisco 12",
        "L12 San Francisco", "Federal Reserve Bank of San Francisco California")
    add("A.prod", f"run {PA['run']}", str(PA['run']), str(PA['run0']), str(PA['sheet']),
        f"sheet {PA['sheet']}", PA['pos'], f"position {PA['pos']}", str(PA['start']),
        f"run {PA['run']} sheet {PA['sheet']} {PA['pos']}",
        f"{PA['run']}/{PA['sheet']}/{PA['pos']}", f"{PA['run']}-{PA['sheet']}-{PA['pos']}",
        f"run {PA_OLD['run']}", f"{PA['start']}-{PA['end']}")
    add("A.fr", f"Fr. {FRIEDBERG['A']}", f"Fr {FRIEDBERG['A']}", FRIEDBERG['A'],
        FRIEDBERG['A'].replace("-", ""), f"Fr.{FRIEDBERG['A'].replace('-', '')}")
    add("A.block", "CL-A", "CL..A", "CL A block", "block A")
    # ---- the KB note: Series 2006A, district B2 New York
    add("B.series", "Series 2006A", "SERIES 2006A", "2006A", "Series K")
    add("B.sig", *_names(tB), *_names(sB), "Hank Paulson", "Cabral Paulson",
        "Paulson Cabral", f"{tB} {sB}", f"{sB} {tB}")
    add("B.district", "B 2", "NEW YORK", "Second District", "2nd District",
        "Second Federal Reserve District", "FRB New York", "New York 2", "B2 New York",
        "Federal Reserve Bank of New York New York")
    add("B.prod", f"run {PB['run']}", str(PB['run']), str(PB['run0']), str(PB['sheet']),
        f"sheet {PB['sheet']}", str(PB['off']), PB['pos'], PB['pos_alt'],
        f"position {PB['pos']}", str(PB['start']),
        f"run {PB['run']} sheet {PB['sheet']} {PB['pos']}",
        f"{PB['run']}/{PB['sheet']}/{PB['pos']}", f"{PB['run']}-{PB['sheet']}-{PB['pos']}",
        f"{PB['run']}/{PB['sheet']}/{PB['pos_alt']}", f"run {PB_OLD['run']}",
        PB_OLD['pos'], PB_OLD['pos_alt'], f"{PB['start']}-{PB['end']}")
    add("B.fr", f"Fr. {FRIEDBERG['B']}", f"Fr {FRIEDBERG['B']}", FRIEDBERG['B'],
        FRIEDBERG['B'].replace("-", ""), f"Fr.{FRIEDBERG['B'].replace('-', '')}")
    add("B.block", "KB-A", "KB..A")
    # ---- shared: denomination, legends, motto, seal text, BEP conventions
    add("denom", "ONE HUNDRED DOLLARS", "One Hundred Dollars", "ONE HUNDRED", "100 DOLLARS",
        "hundred dollar bill", "$100 bill", "C-note", "C note", "Benjamin", "Benjamins",
        "Ben Franklin", "$200", "200", "TWO HUNDRED DOLLARS", "two hundred dollars",
        "Franklins", "two Franklins", "two hundred")
    add("legend", "FEDERAL RESERVE NOTE", "THE UNITED STATES OF AMERICA",
        "UNITED STATES OF AMERICA", "IN GOD WE TRUST",
        "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE",
        "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS PUBLIC AND PRIVATE", "LEGAL TENDER",
        "Treasurer of the United States", "Secretary of the Treasury",
        "THE DEPARTMENT OF THE TREASURY", "THE DEPARTMENT OF THE TREASURY 1789", "1789",
        "FEDERAL RESERVE SYSTEM", "THE FEDERAL RESERVE SYSTEM", "INDEPENDENCE HALL",
        "USA 100", "USA100", "E PLURIBUS UNUM", "WASHINGTON, D.C.", "Washington DC",
        "Washington, D.C.")
    add("bep", "Bureau of Engraving and Printing", "BEP", "FW", "Fort Worth", "32-subject",
        "32", str(RUN), f"{RUN:,}", str(SHEETS), "96000000", str(RUN_OLD), "star note",
        "replacement note", "Friedberg", "FRN", "Federal Reserve Notes", "series letter",
        "district letter", "check letter", "quadrant", "face plate", "back plate")
    # ---- the two notes together
    add("pair", "Series 2001 Series 2006A", "2001 2006A", "Marin O'Neill Cabral Paulson",
        "Cabral Paulson Marin O'Neill", "Marin Cabral", "O'Neill Paulson", "Cabral Marin",
        "Paulson O'Neill", f"{tA} {tB}", f"{sA} {sB}", "San Francisco New York",
        "New York San Francisco", "L12 B2", "Twelfth Second", "12th 2nd",
        f"{PA['run']} {PB['run']}", f"{PA['run']}{PB['run']}", f"{PB['run']}{PA['run']}",
        f"{PA['run0']} {PB['run0']}", f"{PA['run']}+{PB['run']}", str(PA['run'] + PB['run']),
        f"{PA['sheet']} {PB['sheet']}", f"{PA['sheet']}{PB['sheet']}",
        f"{PB['sheet']}{PA['sheet']}", str(PA['sheet'] + PB['sheet']),
        f"{PA['pos']} {PB['pos']}", f"{PA['pos']}{PB['pos']}", f"{PA['pos']} {PB['pos_alt']}",
        f"{PA['pos']}{PB['pos_alt']}", f"run {PA['run']} run {PB['run']}",
        f"Fr. {FRIEDBERG['A']} Fr. {FRIEDBERG['B']}", "2177 2181", "CL-A KB-A", "CLA KBA",
        "$100 $100", "100 100", "Franklin Franklin", "C K", "CK", "L B", "LB")
    # ---- the naive reading: both prefix letters as districts
    add("naive", "Philadelphia", "Dallas", "C3", "K11", "Philadelphia Dallas", "C3 K11",
        "Philadelphia San Francisco Dallas New York", "C3 L12 K11 B2", "3 12 11 2", "312112")
    return T


def catalogue_entries():
    """Per-note catalogue lines a collector would write, and the pair joined."""
    tA, sA = SIGS["2001"]; tB, sB = SIGS["2006A"]
    A, B = [], []
    for s in (A_STR, A_SP):
        A += [f"$100 Series 2001 San Francisco {s}",
              f"Series 2001 $100 Federal Reserve Note San Francisco L12 {s}",
              f"{s} L12 Series 2001 Marin O'Neill",
              f"{s} Series 2001 L12 San Francisco $100 Marin O'Neill Fr. {FRIEDBERG['A']}",
              f"Fr. {FRIEDBERG['A']} {s}", f"2001 L12 {s} Marin O'Neill 100",
              f"{s} 2001 12 {PA['pos']} {PA['sheet']} {PA['run']}",
              f"{s} {tA} {sA}", f"{tA} {sA} {s}", f"{s} Marin O'Neill", f"Marin O'Neill {s}"]
    for s in (B_STR, B_SP):
        B += [f"$100 Series 2006A New York {s}",
              f"Series 2006A $100 Federal Reserve Note New York B2 {s}",
              f"{s} B2 Series 2006A Cabral Paulson",
              f"{s} Series 2006A B2 New York $100 Cabral Paulson Fr. {FRIEDBERG['B']}",
              f"Fr. {FRIEDBERG['B']} {s}", f"2006A B2 {s} Cabral Paulson 100",
              f"{s} 2006A 2 {PB['pos']} {PB['sheet']} {PB['run']}",
              f"{s} {tB} {sB}", f"{tB} {sB} {s}", f"{s} Cabral Paulson", f"Cabral Paulson {s}"]
    out = list(A) + list(B)
    for x, y in zip(A, B):
        for j in (" ", "\n", "; ", " / ", ""):
            out.append(x + j + y); out.append(y + j + x)
    return out


def single_record():
    """The pair as ONE banknote data record: letters together, digits together, suffix."""
    letters = ["CLKB", "CKLB", "KBCL", "KCBL"]
    digits = [AB_D, BA_D, A_D + " " + B_D, B_D + " " + A_D]
    tails = ["", "L12B2", "L12 B2", "2001 2006A", "L12 B2 2001 2006A", "20012006A"]
    base, out = [], []
    for L, D, suf, sep in itertools.product(letters, digits, ("A", ""), ("", " ")):
        rec = L + sep + D + (sep + suf if suf else "")
        base.append(rec)
        for t in tails:
            out.append(rec + (sep + t if t else ""))
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


def path_forms():
    """Production coordinates as BIP-32 path components (speculative)."""
    ps = [f"m/44'/0'/0'/0/{PA['sheet']}", f"m/44'/0'/0'/0/{PB['sheet']}",
          f"m/84'/0'/0'/0/{PA['sheet']}", f"m/84'/0'/0'/0/{PB['sheet']}",
          f"m/44'/0'/{PA['run']}'/0/{PA['sheet']}", f"m/44'/0'/{PB['run']}'/0/{PB['sheet']}",
          f"m/{PA['run']}/{PA['sheet']}", f"m/{PB['run']}/{PB['sheet']}",
          f"m/{PA['run']}'/{PA['sheet']}'", f"m/{PB['run']}'/{PB['sheet']}'",
          f"m/{PA['run']}/{PA['sheet']}/{PB['run']}/{PB['sheet']}",
          f"m/{PA['run']}'/{PA['sheet']}'/{PB['run']}'/{PB['sheet']}'",
          f"m/0/{PA['run']}/{PA['sheet']}", f"m/0/{PB['run']}/{PB['sheet']}",
          f"m/2001'/12'/{A_D}'", f"m/2006'/2'/{B_D}'",
          f"m/12/{A_D}/2/{B_D}", f"m/12'/{A_D}'/2'/{B_D}'"]
    return [(f"path:{p}", "path:" + p) for p in ps]


def _already_swept():
    """Exact strings other modules already ran through the full stack."""
    seen = set()
    try:
        import serial_combine as SC
        seen |= set(SC.string_forms())
    except Exception:
        pass
    for modname, fn in (("note_signatures", "build"), ("page72", "build"),
                        ("serial2_exhaust", "textual_forms")):
        try:
            m = __import__(modname)
            seen |= set(getattr(m, fn)())
        except Exception:
            pass
    try:
        import mirror_serial as MS
        seen |= set(MS.readings().values())
    except Exception:
        pass
    return seen


def forms():
    out, vals = [], {}
    def put(tag, v):
        if not v or v in vals: return
        vals[v] = tag; out.append((tag, v))
    def put_cases(tag, v):
        put(tag, v)
        lo, up = v.lower(), v.upper()
        if lo != v: put(tag + "/lower", lo)
        if up != v: put(tag + "/upper", up)
    # 1. every numismatic token x every serial form, both orders, three joins
    for i, (g, t) in enumerate(tokens()):
        for j, s in enumerate(SERIAL_FORMS):
            for k, sep in enumerate(("", " ", "-")):
                f = put_cases if sep != "-" else put
                f(f"tok:{g}:{i}:{j}:{k}:ts", t + sep + s)
                f(f"tok:{g}:{i}:{j}:{k}:st", s + sep + t)
    # 2. catalogue entries
    for i, v in enumerate(catalogue_entries()):
        put_cases(f"cat:{i}", v)
    # 3. single record, its reversals and mirror readings
    base, rec = single_record()
    for i, v in enumerate(rec):
        put_cases(f"record:{i}", v)
    old = old_style()
    for i, v in enumerate(old):
        put_cases(f"oldstyle:{i}", v)
    stars = star_forms()
    for i, v in enumerate(stars):
        put_cases(f"star:{i}", v)
    for i, v in enumerate(production_strings()):
        put_cases(f"prod:{i}", v)
    try:
        import mirror_serial as MS
        mir_src = [A_STR + B_STR, B_STR + A_STR, A_SP + " " + B_SP, B_SP + " " + A_SP,
                   A_STR + " " + B_STR, B_STR + " " + A_STR, A_STR + "KB46279860A",
                   "KB46279860A", "KB 46279860 A"] + base + old[:6] + stars[:8]
        for i, v in enumerate(mir_src):
            put(f"mirror:{i}:rev", v[::-1])
            put(f"mirror:{i}:rot180", MS.rot180(v))
            put(f"mirror:{i}:mirror", MS.mirror(v))
            put(f"mirror:{i}:rot180_nospace", MS.rot180(v).replace(" ", ""))
    except Exception:
        pass
    for tag, v in raw_int_keys(): put(tag, v)
    for tag, v in path_forms(): put(tag, v)
    skip = _already_swept()
    return [(t, v) for t, v in out if v not in skip]


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
    t0 = time.time(); F = forms(); dt = time.time() - t0
    V = {v for _, v in F}
    rep(f"{len(F):,} forms built in {dt:.1f}s (<= 20,000, < 30 s)", 0 < len(F) <= 20000 and dt < 30)
    rep("no empty values", all(v for _, v in F))
    rep("unique tags", len({t for t, _ in F}) == len(F))
    rep("unique values", len(V) == len(F))
    for want in ("CLKB7684171446279860A", "CLKB 76841714 46279860 A L12 B2",
                 "L76841714A B46279860", "CL76841714" + STAR, "CL76841714* KB46279860*",
                 "Rosario Marin KB46279860", "KB46279860-Anna Escobedo Cabral",
                 "Cabral Paulson CL76841714AKB46279860", "Marin Cabral 7684171446279860",
                 "run 25 sheet 41714 position A1", "run 15 sheet 79860 position G2",
                 "A1 41714 G2 79860", "$100 Series 2001 San Francisco CL76841714A",
                 "Fr. 2177-L CL76841714A", "76841714 76800001-80000000",
                 "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE KB46279860",
                 "philadelphia dallas cl76841714akb46279860",
                 "09867294BKA417148977C",            # rot180 of CL76841714AKB46279860
                 "A0986729441714897BK7C",            # rot180 of CLKB7684171446279860A
                 "hex:" + (41714).to_bytes(32, "big").hex(),
                 "hex:" + (4171479860).to_bytes(32, "big").hex(),
                 "path:m/44'/0'/25'/0/41714"):
        rep(f"contains {want!r}", want in V)
    # things other modules already sweep must NOT be re-emitted
    for gone in ("Series 2001 76841714", "San Francisco 7684171446279860", "KB46279860A",
                 "Rosario Marin CL76841714A", "A41714867LC"):
        rep(f"omits already-swept {gone!r}", gone not in V)
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
