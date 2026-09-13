#!/usr/bin/env python3
"""
sand_sentences.py -- Keiser's manuscript "lines" are SENTENCES.

HYPOTHESIS (setter-psychology lens)
Keiser writes broadcast-style, one sentence per line, and hands a Word file to
a Bitcoin Magazine designer who then chooses the printed line breaks.  So the
"George Sand" alternate-LINE cipher he alludes to would live in alternate
SENTENCES of his manuscript, not in the designer's printed lines -- and the
"private keyS" would be sentence-edge words (a 12-word seed) or the
alternate-sentence text itself (a brainwallet / Electrum text seed) with
"El Salvador" as the wallet passphrase.

gen_sand.py and column_cipher.py both operated on PRINTED lines; sentence
first/last words were only ever swept as brainwallet strings, never as
BIP-39 / Electrum / WIF sources and never in parity subsets or paragraph units.

WHAT THIS DOES
  Units:  A = strict sentences (split after [.!?] + optional closing "/')
          B = sentences, but the p75 verse lines (file lines 32-42) and the
              p77 all-caps block (103-107) are their own units
          P = paragraphs (blank-line separated)
  Scopes: whole article + each of p75..p79; forward + reversed unit order.
  Readings: odd units, even units, every 3rd at offsets 0/1/2 (space-joined);
            unit-initial words, unit-final words, unit-initial letters.
  (a) print alternate-unit readings; englishness_z + OPERATION-MATCHED null
      (same parity extraction on 30 unit-shuffled copies) -> rank
  (b) brainwallet fast hashes (7 x 5 script types) on every concatenation in
      as-is / lower / upper / no-punct / no-space / reversed forms -> oracle
  (c) sentence-edge word sequences (initial, final, interleaved edges, two
      zig-zags) x (full, odd, even, 3rd@k) x (fwd, rev) x (A, B, P):
        BIP-39 exact and 4-letter-prefix filters -> 12/15/18/21/24 windows ->
        checksum -> HD quick paths x passphrase list -> oracle
        Electrum v2 seed-version on raw contiguous windows (12/13 primary,
        3..24 all) -> m/0/i, m/1/i, m/0'/0/i, m/0'/1/i x passphrases -> oracle
        old Electrum 12-windows of old-list words -> stretched key -> oracle
  (d) unit-initial / unit-final letter strings, both directions, 3 cases ->
      sliding WIF / BIP38 / mini checksum windows
  Controls: synthetic unit lists pushed through the SAME functions must
      recover externally-known addresses (BIP-39 vector, Electrum test-suite
      vectors, old-Electrum vector, bitcoin-wiki WIF, Casascius mini vector,
      and the sha256 brainwallet of the planted odd-sentence message), and the
      null machinery must rank a planted odd-parity message first.

  python3 wf/sand_sentences.py            (from solver/)
"""
import os, re, sys, random, hashlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.path.dirname(HERE)
sys.path.insert(0, SOLVER)
import harness as H
from hd_sweep import direct_keys
from englishness import letters as eng_letters

TRANSCRIPT = os.path.join(SOLVER, "article_transcript.txt")
NON_BODY = {"bitcoin is toxic af", "max keiser"}
VERSE_LINES = set(range(32, 43)) | set(range(103, 108))   # 1-indexed transcript lines

PASSPHRASES = ["", "El Salvador", "ElSalvador", "el salvador", "elsalvador", "EL SALVADOR",
               "ELSALVADOR", "El salvador", "Salvador", "salvador", "SALVADOR",
               "Overdose", "OVERDOSE", "overdose", "Bitcoin Is Toxic AF", "BITCOIN IS TOXIC AF",
               "Max Keiser", "maxkeiser", "MaxKeiser", "Stacy", "20", "Bitcoin", "bitcoin",
               "mirror", "George Sand", "Toxic", "toxic", "TOXIC", "Bukele"]

RNG = random.Random(20260913)


# ------------------------------------------------------------------ parsing --
def load_pages(path=TRANSCRIPT):
    """[(pageno, [paragraph, ...])], paragraph = [(lineno, text), ...]"""
    lines = open(path, encoding="utf-8").read().split("\n")
    pages, cur, para = [], None, []
    for i, raw in enumerate(lines, 1):
        if raw.startswith("#"):
            continue
        m = re.match(r"=== PAGE (\d+)", raw)
        if m:
            if cur is not None:
                if para:
                    cur[1].append(para)
                    para = []
                pages.append(cur)
            cur = (int(m.group(1)), [])
            continue
        if cur is None:
            continue
        t = raw.strip()
        if not t:
            if para:
                cur[1].append(para)
                para = []
            continue
        if t.lower() in NON_BODY:
            continue
        para.append((i, t))
    if cur is not None:
        if para:
            cur[1].append(para)
        pages.append(cur)
    return pages


SENT_RE = re.compile(r'\S.*?[.!?]["\')]*(?=\s|$)', re.S)


def split_sentences(text):
    text = " ".join(text.split())
    out, pos = [], 0
    for m in SENT_RE.finditer(text):
        assert not text[pos:m.start()].strip()
        out.append(m.group().strip())
        pos = m.end()
    rest = text[pos:].strip()
    if rest:
        out.append(rest)
    return out


def units_A(paras):
    u = []
    for para in paras:
        u += split_sentences(" ".join(t for _, t in para))
    return u


def units_B(paras):
    u = []
    for para in paras:
        run = []
        for ln, t in para:
            if ln in VERSE_LINES:
                if run:
                    u += split_sentences(" ".join(run))
                    run = []
                u.append(t)
            else:
                run.append(t)
        if run:
            u += split_sentences(" ".join(run))
    return u


def units_P(paras):
    return [" ".join(" ".join(t for _, t in para).split()) for para in paras]


# ------------------------------------------------------------ word helpers --
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’$%-]*")


def toks(u):
    return WORD_RE.findall(u)


def first_word(u):
    t = toks(u)
    return t[0] if t else ""


def last_word(u):
    t = toks(u)
    return t[-1] if t else ""


def first_letter(u):
    m = re.search(r"[A-Za-z0-9]", u)
    return m.group() if m else ""


def last_letter(u):
    m = re.search(r"[A-Za-z0-9](?=[^A-Za-z0-9]*$)", u)
    return m.group() if m else ""


def norm(w):
    return re.sub(r"[^a-z]", "", w.lower())


PREFIX4 = {}
for _w in H.BIP39:
    PREFIX4.setdefault(_w[:4], _w)
assert len(PREFIX4) == 2048, "BIP-39 4-letter prefixes must be unique"


def bip39_prefix(w):
    if len(w) < 4:
        return w if w in H.BIP39_SET else None
    return PREFIX4.get(w[:4])


# --------------------------------------------------------------------- sink --
class Sink:
    """Every address the pipelines produce passes through here: oracle lookup
    plus a control-target lookup so a synthetic run can prove reach."""

    def __init__(self, oracle, targets=None, quiet=False):
        self.O = oracle
        self.targets = dict(targets or {})
        self.quiet = quiet
        self.n_addr = 0
        self.n_keys = 0
        self.hits = []
        self.ctrl = {}

    def check(self, tag, addr, priv=None, path=None, typ=None):
        self.n_addr += 1
        if addr in self.targets:
            self.ctrl.setdefault(self.targets[addr], []).append((tag, path, typ, addr))
        if self.O.funded(addr):
            row = (tag, path, typ, addr, priv.hex() if priv else None)
            self.hits.append(row)
            if not self.quiet:
                print("HIT", row, flush=True)

    def rows(self, tag, rows):
        for p, t, a, priv in rows:
            self.n_keys += 1
            self.check(tag, a, priv, p, t)


# ------------------------------------------------------- (b) brainwallets --
def forms(s):
    s = " ".join(s.split())
    out = {"asis": s, "lower": s.lower(), "upper": s.upper()}
    np_ = " ".join(re.sub(r"[^A-Za-z0-9 ]", "", s).split())
    out["nopunct"] = np_
    out["nopunct_lower"] = np_.lower()
    out["nospace"] = re.sub(r"\s+", "", s)
    out["nospace_lower"] = out["nospace"].lower()
    out["nopunct_nospace_lower"] = re.sub(r"\s+", "", np_).lower()
    out["reversed"] = s[::-1]
    out["reversed_lower"] = s[::-1].lower()
    return out


def brain_check(sink, tag, phrase, seen):
    for fname, p in forms(phrase).items():
        if not p or p in seen:
            continue
        seen.add(p)
        for hname, k in direct_keys(p).items():
            sink.n_keys += 1
            for t, a in H.addrs_for_priv(k).items():
                sink.check(f"brain:{hname}:{fname}:{tag}", a, k, None, t)


# ------------------------------------------------------------ (c) seeds --
def bip39_windows(sink, tag, words, seen, pws=PASSPHRASES):
    """words: normalized lowercase list already filtered/mapped to BIP-39."""
    n = nv = 0
    for L in (12, 15, 18, 21, 24):
        for i in range(0, len(words) - L + 1):
            ws = words[i:i + L]
            n += 1
            if not H.bip39_valid(ws):
                continue
            nv += 1
            m = " ".join(ws)
            for pw in pws:
                key = (m, pw)
                if key in seen:
                    continue
                seen.add(key)
                sink.rows(f"bip39:{tag}:w{i}+{L}|pw={pw!r}|{m}", H.bip39_addrs(m, pw))
    return n, nv


def electrum_v2_windows(sink, tag, words, seen, pws=PASSPHRASES, lengths=range(3, 25)):
    n = nv = 0
    for L in lengths:
        for i in range(0, len(words) - L + 1):
            phrase = " ".join(words[i:i + L])
            n += 1
            kind = H.electrum_v2_type(phrase)
            if not kind:
                continue
            nv += 1
            for pw in pws:
                key = (phrase, pw)
                if key in seen:
                    continue
                seen.add(key)
                sink.rows(f"electrum_v2:{kind}:{tag}:w{i}+{L}|pw={pw!r}|{phrase}",
                          H.electrum_v2_addrs(phrase, pw, 5 if pw == "" else 3))
    return n, nv


def electrum_old_windows(sink, tag, words, seen):
    n = 0
    for i in range(0, len(words) - 12 + 1):
        ws = words[i:i + 12]
        key = tuple(ws)
        if key in seen:
            continue
        seen.add(key)
        n += 1
        sink.rows(f"electrum_old:{tag}:w{i}|{' '.join(ws)}", H.electrum_old_addrs(ws, 5))
        sink.rows(f"electrum_old:{tag}:w{i}|{' '.join(ws)}", H.electrum_old_addrs(ws, 2, change=True))
    return n


# ---------------------------------------------------------- (d) letters --
def key_format_windows(sink, tag, s, seen, found):
    n = 0
    for L, fn in ((51, H.wif_check), (52, H.wif_check), (58, H.bip38_check),
                  (22, H.mini_check), (26, H.mini_check), (30, H.mini_check)):
        for i in range(0, len(s) - L + 1):
            w = s[i:i + L]
            if (w, L) in seen:
                continue
            seen.add((w, L))
            n += 1
            r = fn(w)
            if not r:
                continue
            kind, payload = r
            found.append((tag, i, kind, w))
            print(f"KEYFORMAT {kind} in {tag} at {i}: {w}", flush=True)
            if kind in ("wif_c", "wif_u", "mini"):
                priv = payload if kind != "mini" else payload
                for t, a in H.addrs_for_priv(priv).items():
                    sink.check(f"{kind}:{tag}:{i}:{w}", a, priv, None, t)
            else:
                sink.check(f"bip38:{tag}:{i}:{w}", "(bip38-encrypted, no address)")
    return n


# ---------------------------------------------------- (a) null-cipher test --
def parity_readings(units):
    yield "odd", units[0::2]
    yield "even", units[1::2]
    for k in range(3):
        yield f"3rd@{k}", units[k::3]


def z_of(text):
    s = eng_letters(text)
    if len(s) < 30:
        return float("nan")
    return H.englishness_z(s)[0]


def parity_null_test(units, tag, n_shuf=30, print_full=False, out=sys.stdout):
    res = []
    for pname, sel in parity_readings(units):
        if len(sel) < 3:
            continue
        real = " ".join(sel)
        zr = z_of(real)
        k, off = (2, 0) if pname == "odd" else (2, 1) if pname == "even" else (3, int(pname[-1]))
        nulls = []
        for _ in range(n_shuf):
            sh = units[:]
            RNG.shuffle(sh)
            nulls.append(z_of(" ".join(sh[off::k])))
        rank = 1 + sum(1 for z in nulls if z >= zr)
        mean = sum(nulls) / len(nulls)
        res.append((tag, pname, len(sel), zr, mean, max(nulls), rank))
        out.write(f"  [{tag}] {pname:6} n={len(sel):3d} z={zr:+6.1f}  null mean={mean:+6.1f} "
                  f"max={max(nulls):+6.1f}  rank {rank}/{n_shuf + 1}\n")
        if print_full:
            out.write(f"    >> {real}\n")
    return res


# ---------------------------------------------------------- orchestration --
def word_sequences(units):
    """name -> list of printed words (edge words of the units)."""
    fw = [first_word(u) for u in units]
    lw = [last_word(u) for u in units]
    seqs = {}
    for sname, idx in (("full", list(range(len(units)))),
                       ("odd", list(range(0, len(units), 2))),
                       ("even", list(range(1, len(units), 2))),
                       ("3rd@0", list(range(0, len(units), 3))),
                       ("3rd@1", list(range(1, len(units), 3))),
                       ("3rd@2", list(range(2, len(units), 3)))):
        seqs[f"{sname}:initial"] = [fw[i] for i in idx]
        seqs[f"{sname}:final"] = [lw[i] for i in idx]
        seqs[f"{sname}:edges"] = [w for i in idx for w in (fw[i], lw[i])]
        if sname == "full":
            # zig-zags: initial of odd units + final of even units (Sand-like), and the converse
            seqs["zig:init_odd_final_even"] = [fw[i] if i % 2 == 0 else lw[i] for i in idx]
            seqs["zig:final_odd_init_even"] = [lw[i] if i % 2 == 0 else fw[i] for i in idx]
    out = {}
    for name, ws in seqs.items():
        ws = [w for w in ws if w]
        out[f"{name}:fwd"] = ws
        out[f"{name}:rev"] = ws[::-1]
    return out


def analyze(unitsets, sink, label, do_null=True, print_readings=True, out=sys.stdout):
    """unitsets: {('A'|'B'|'P', scope): [units]}  scope 'ALL' or 'p75'..."""
    stats = {"readings": 0, "brain_phrases": 0, "bip39_windows": 0, "bip39_valid": 0,
             "bip39p_windows": 0, "bip39p_valid": 0, "ev2_windows": 0, "ev2_valid": 0,
             "eold_windows": 0, "keyfmt_windows": 0, "keyfmt_found": 0, "sequences": 0}
    seen_brain, seen_b39, seen_ev2, seen_old, seen_kf = set(), set(), set(), set(), set()
    kf_found = []
    null_rows = []

    # ---- (a)+(b): parity readings, printing, null test, brainwallet forms ----
    for (us, scope), units in unitsets.items():
        for direction in ("fwd", "rev"):
            uu = units if direction == "fwd" else units[::-1]
            tag = f"{label}:{us}:{scope}:{direction}"
            if direction == "fwd" and do_null:
                pf = print_readings and (scope == "ALL" or us == "A")
                out.write(f"\n--- parity null test {tag} ({len(uu)} units) ---\n")
                null_rows += parity_null_test(uu, tag, print_full=pf, out=out)
            readings = {}
            for pname, sel in parity_readings(uu):
                if len(sel) < 2:
                    continue
                readings[pname] = " ".join(sel)
                readings[f"{pname}:initial_words"] = " ".join(first_word(u) for u in sel)
                readings[f"{pname}:final_words"] = " ".join(last_word(u) for u in sel)
                readings[f"{pname}:initial_letters"] = "".join(first_letter(u) for u in sel)
            readings["full:initial_words"] = " ".join(first_word(u) for u in uu)
            readings["full:final_words"] = " ".join(last_word(u) for u in uu)
            readings["full:initial_letters"] = "".join(first_letter(u) for u in uu)
            readings["full:final_letters"] = "".join(last_letter(u) for u in uu)
            for rname, text in readings.items():
                stats["readings"] += 1
                brain_check(sink, f"{tag}:{rname}", text, seen_brain)
            # ---- (d) key-format windows over letter strings ----
            for rname in ("full:initial_letters", "full:final_letters",
                          "odd:initial_letters", "even:initial_letters"):
                s = readings.get(rname, "")
                for cname, cs in (("asis", s), ("lower", s.lower()), ("upper", s.upper())):
                    stats["keyfmt_windows"] += key_format_windows(sink, f"{tag}:{rname}:{cname}", cs, seen_kf, kf_found)
    stats["brain_phrases"] = len(seen_brain)

    # ---- (c): sentence-edge word sequences as seed material (ALL scope only:
    #          per-page windows are sub-windows of ALL / ALL-odd / ALL-even) ----
    for (us, scope), units in unitsets.items():
        if scope != "ALL":
            continue
        for sname, ws in word_sequences(units).items():
            stats["sequences"] += 1
            tag = f"{label}:{us}:{sname}"
            nw = [norm(w) for w in ws]
            nw = [w for w in nw if w]
            # BIP-39 exact
            ex = [w for w in nw if w in H.BIP39_SET]
            n, nv = bip39_windows(sink, f"{tag}:exact", ex, seen_b39)
            stats["bip39_windows"] += n
            stats["bip39_valid"] += nv
            # BIP-39 4-letter prefix
            pf = [bip39_prefix(w) for w in nw]
            pf = [w for w in pf if w]
            n, nv = bip39_windows(sink, f"{tag}:prefix4", pf, seen_b39)
            stats["bip39p_windows"] += n
            stats["bip39p_valid"] += nv
            # Electrum v2 on the raw word sequence
            n, nv = electrum_v2_windows(sink, f"{tag}:raw", nw, seen_ev2)
            stats["ev2_windows"] += n
            stats["ev2_valid"] += nv
            # old Electrum
            ol = [w for w in nw if w in H.ELECTRUM_OLD_SET]
            stats["eold_windows"] += electrum_old_windows(sink, f"{tag}:old", ol, seen_old)
    stats["keyfmt_found"] = len(kf_found)
    return stats, null_rows, kf_found


# ---------------------------------------------------------------- controls --
def build_control_units():
    """30 sentences: odd-parity (index 0,2,..) = an English message; even-parity
    = letter-scrambled gibberish. Sentences 0..10 begin 'Abandon', 11 'About'."""
    message = [
        "Abandon all hope of fiat money, the printers are out of ink.",
        "Abandon the central bankers to their burning stake.",
        "Abandon every shitcoin and keep your dignity.",
        "Abandon the paper chase and open your heart to bitcoin.",
        "Abandon fear, because the rabbit hole ends in peace and love.",
        "Abandon the war economy for the economy of love.",
        "Toxic maximalists will inherit the whole earth.",
        "Nothing could be better than this collective panic.",
        "Markets discount everything in advance and they sense the end.",
        "Every wannabe faces the fate of demonetization.",
        "Bitcoin fixes the hate incentive by removing the war incentive.",
        "Poverty disappears because the fear of being poor disappears.",
        "Stacy and I have been living in here for ten years.",
        "We have seen some shit and we are happy to share it.",
        "The private key is hidden in plain sight for the toxic reader.",
    ]
    gib = []
    rng = random.Random(7)
    starts = ["Abandon", "Abandon", "Abandon", "Abandon", "Abandon", "About",
              "Zorblax", "Qwerpt", "Xylth", "Vrmbo", "Ktzpl", "Jjnqw", "Wxyzz", "Ppqqr", "Gghjk"]
    for i in range(15):
        ws = []
        for _ in range(rng.randint(5, 9)):
            ws.append("".join(rng.choice("bcdfghjklmnpqrstvwxz") for _ in range(rng.randint(3, 8))))
        gib.append(starts[i] + " " + " ".join(ws) + ".")
    text = " ".join(s for pair in zip(message, gib) for s in pair)
    units = split_sentences(text)
    assert len(units) == 30, len(units)
    assert [first_word(u).lower() for u in units[:12]] == ["abandon"] * 11 + ["about"]
    odd_msg = " ".join(units[0::2])
    return units, odd_msg


def run_controls(oracle):
    print("\n==================== CONTROLS ====================", flush=True)
    results = []

    def report(name, ok, detail=""):
        results.append((name, ok))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)

    # ---- control 1: synthetic 30-sentence text through the whole pipeline ----
    units, odd_msg = build_control_units()
    # expected brainwallet address of the odd-parity reading, lowercase no-punct
    # form, computed here directly from hashlib (not via the pipeline).
    lit = " ".join(re.sub(r"[^A-Za-z0-9 ]", "", odd_msg).split()).lower()
    k = hashlib.sha256(lit.encode()).digest()
    exp_brain = H.addrs_for_priv(k)["p2pkh_u"]
    targets = {exp_brain: "brain_sha256_odd_message",
               "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA": "bip39_abandon_vector_bip44"}
    sink = Sink(oracle, targets, quiet=True)
    import io
    buf = io.StringIO()
    stats, null_rows, kf = analyze({("A", "ALL"): units}, sink, "CTRL1", do_null=True,
                                   print_readings=False, out=buf)
    print(buf.getvalue())
    report("ctrl1 sentence splitter -> 30 units, initial words abandon x11 about", True)
    report("ctrl1 (b) sha256 of odd-sentence reading reaches expected address",
           "brain_sha256_odd_message" in sink.ctrl,
           (sink.ctrl.get("brain_sha256_odd_message") or [("-",)])[0][0][:90])
    report("ctrl1 (c) initial words abandon x11 about -> 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA",
           "bip39_abandon_vector_bip44" in sink.ctrl,
           (sink.ctrl.get("bip39_abandon_vector_bip44") or [("-",)])[0][0][:110])
    odd_row = [r for r in null_rows if r[1] == "odd"][0]
    report("ctrl1 (a) null machinery ranks planted odd-parity message first",
           odd_row[6] == 1 and odd_row[3] > odd_row[5] + 3,
           f"real z={odd_row[3]:+.1f} null mean={odd_row[4]:+.1f} max={odd_row[5]:+.1f} rank={odd_row[6]}")
    even_row = [r for r in null_rows if r[1] == "even"][0]
    report("ctrl1 (a) gibberish even-parity does NOT rank first (specificity)",
           even_row[6] > 1, f"even z={even_row[3]:+.1f} rank={even_row[6]}")

    # ---- control 2: 4-letter-prefix path ----
    units2 = [f"Abandonment {i} is coming." for i in range(11)] + ["Aboutness is a word."] + \
             ["Keiser says so.", "Stacy agrees."]
    sink2 = Sink(oracle, {"1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA": "prefix"}, quiet=True)
    analyze({("A", "ALL"): units2}, sink2, "CTRL2", do_null=False, print_readings=False, out=io.StringIO())
    report("ctrl2 (c) 4-letter-prefix path (Abandonment x11, Aboutness) -> bip44 vector",
           "prefix" in sink2.ctrl, (sink2.ctrl.get("prefix") or [("-",)])[0][0][:110])

    # ---- control 3: Electrum v2 seeds as sentence-initial words (Electrum
    # test-suite vectors: segwit receive/change, standard change) ----
    seg = "bitter grass shiver impose acquire brush forget axis eager alone wine silver".split()
    std = "cycle rocket west magnet parrot shuffle foot correct salt library feed song".split()
    units3 = [f"{w.capitalize()} is the word." for w in seg] + ["Then a break."] + \
             [f"{w.capitalize()} goes here." for w in std]
    t3 = {"bc1q3g5tmkmlvxryhh843v4dz026avatc0zzr6h3af": "ev2_segwit_recv0",
          "bc1qdy94n2q5qcp0kg7v9yzwe6wvfkhnvyzje7nx2p": "ev2_segwit_change0",
          "1KSezYMhAJMWqFbVFB2JshYg69UpmEXR4D": "ev2_standard_change0"}
    sink3 = Sink(oracle, t3, quiet=True)
    analyze({("A", "ALL"): units3}, sink3, "CTRL3", do_null=False, print_readings=False, out=io.StringIO())
    for name in t3.values():
        report(f"ctrl3 (c) Electrum v2 initial-word window -> {name}", name in sink3.ctrl,
               (sink3.ctrl.get(name) or [("-",)])[0][0][:100])

    # ---- control 4: old Electrum words as sentence-FINAL words ----
    old = "powerful random nobody notice nothing important anyway look away hidden message over".split()
    units4 = [f"The word is {w}." for w in old] + ["The end."]
    sink4 = Sink(oracle, {"1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo": "old_electrum_addr0"}, quiet=True)
    analyze({("A", "ALL"): units4}, sink4, "CTRL4", do_null=False, print_readings=False, out=io.StringIO())
    report("ctrl4 (c) old-Electrum final-word window -> 1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo",
           "old_electrum_addr0" in sink4.ctrl, (sink4.ctrl.get("old_electrum_addr0") or [("-",)])[0][0][:100])

    # ---- control 5: WIF and mini key spelled by unit-initial letters ----
    wif = "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ"   # bitcoin wiki vector
    mini = "S6c56bnXQiBjk9mqSYE7ykVQ7NzrRy"                       # Casascius vector
    units5 = [f"{c}x marks the spot." for c in wif] + ["Break here."] + [f"{c}y is next." for c in mini]
    exp_priv = bytes.fromhex("0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D")
    exp_wif_addr = H.addrs_for_priv(exp_priv)["p2pkh_u"]
    mini_priv = hashlib.sha256(mini.encode()).digest()
    exp_mini_addr = H.addrs_for_priv(mini_priv)["p2pkh_u"]
    sink5 = Sink(oracle, {exp_wif_addr: "wif_vector", exp_mini_addr: "mini_vector"}, quiet=True)
    _, _, kf5 = analyze({("A", "ALL"): units5}, sink5, "CTRL5", do_null=False, print_readings=False, out=io.StringIO())
    wif_rows = [r for r in kf5 if r[2] == "wif_u" and r[3] == wif]
    report("ctrl5 (d) WIF spelled by unit-initial letters -> checksum + priv 0C28FCA3...",
           bool(wif_rows) and H.wif_check(wif)[1] == exp_priv and "wif_vector" in sink5.ctrl,
           f"found at {[r[1] for r in wif_rows]} addr {exp_wif_addr}")
    report("ctrl5 (d) mini key spelled by unit-initial letters -> mini_check + address",
           "mini_vector" in sink5.ctrl, exp_mini_addr)

    # ---- control 6: oracle positive ----
    report("oracle sees genesis coinbase", oracle.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"))
    report("oracle sees a named exact-20 candidate", oracle.funded("1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t"))
    ok = all(r[1] for r in results)
    print(f"CONTROLS {'ALL PASS' if ok else 'SOME FAILED'} ({sum(r[1] for r in results)}/{len(results)})", flush=True)
    return ok, results


# --------------------------------------------------------------------- main --
def main():
    t0 = time.time()
    pages = load_pages()
    unitsets = {}
    for us, fn in (("A", units_A), ("B", units_B), ("P", units_P)):
        allu = []
        for pno, paras in pages:
            u = fn(paras)
            unitsets[(us, f"p{pno}")] = u
            allu += u
        unitsets[(us, "ALL")] = allu
    print("UNIT COUNTS:", {f"{k[0]}:{k[1]}": len(v) for k, v in unitsets.items()})
    print("\n=== A units (strict sentences), numbered ===")
    for i, u in enumerate(unitsets[("A", "ALL")]):
        print(f"  {i:2d} | {first_letter(u)} | {first_word(u):14} .. {last_word(u):14} | {u}")
    print("\n=== B extra units (verse / all-caps lines) ===")
    bset = set(unitsets[("B", "ALL")]) - set(unitsets[("A", "ALL")])
    for u in unitsets[("B", "ALL")]:
        if u in bset:
            print("   ", u)
    print("\n=== P units (paragraphs) ===")
    for i, u in enumerate(unitsets[("P", "ALL")]):
        print(f"  {i:2d} | {first_word(u):12} .. {last_word(u):12} | {u[:90]}...")

    oracle = H.Oracle()
    ok, ctrl = run_controls(oracle)
    if not ok:
        print("CONTROLS FAILED -- nulls below are not admissible", flush=True)

    print("\n==================== REAL ARTICLE ====================", flush=True)
    sink = Sink(oracle)
    stats, null_rows, kf = analyze(unitsets, sink, "REAL", do_null=True, print_readings=True)
    print("\n=== parity null summary (real article) ===")
    null_rows.sort(key=lambda r: -r[3])
    for r in null_rows:
        print(f"  {r[0]:22} {r[1]:6} n={r[2]:3d} z={r[3]:+6.1f} null mean={r[4]:+6.1f} max={r[5]:+6.1f} rank {r[6]}/31")
    print("\nSTATS:", stats)
    print(f"addresses checked: {sink.n_addr:,}   keys derived: {sink.n_keys:,}")
    print("KEYFORMAT FINDS:", kf)
    print("HITS:", len(sink.hits))
    for h in sink.hits:
        print("  ", h)
    print(f"elapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
