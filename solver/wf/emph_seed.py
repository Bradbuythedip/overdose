#!/usr/bin/env python3
"""
emph_seed.py -- Author-emphasis words as the seed vocabulary.

HYPOTHESIS (puzzle-setter lens). Keiser controls WORDS and his own emphasis
marks in the Word manuscript; the designer controls printed line breaks and
the ransom-note bars (but reproduces whole-word emphasis). "Hidden private
keyS in the text" from a 2011-era bitcoiner most naturally means a seed
phrase; "'El Salvador' is a clue" reads as a literal wallet passphrase. So:
take every WHOLE-WORD emphasised word (bold >= 1.0, or inside any orange /
black / white bar) in reading order and read that vocabulary -- and its
derived pointer sequences -- as seed material, validated first by the seed
formats' own self-checks (BIP-39 checksum, Electrum seed-version byte,
WIF/BIP38/mini checksums) and only then by the funded-address oracle.

SEQUENCES (whole article and per page; each forward and mirrored):
  emph          every emphasised word          bold_nobar   bold, not in a bar
  nonemph       the complement                 bar_all      any bar
  orange/black/white  per-colour bars          under_strike underlined/struck
  runfirst/runlast    first/last word of each maximal emphasised run
  runfirst_L/runlast_L  same, runs bounded by the printed line
  boldrun_first/last  first/last word of each bold-only run
  before/after  the plain word immediately before/after each run
  sent_emph_first/last  first/last emphasised word of each sentence
  esent_first/last    first/last word of every sentence that carries emphasis
  sent_first/last     first/last word of every sentence (Keiser's "lines")
Emphasis thresholds: w10 (bold>=1.0 or bar), w05 (bold>=0.5 or bar),
any (any bold letter or bar). Page 79 is run three ways: the letter-level
typography_p79.json, the hand-read whole-word list from the task brief, and
omitted entirely.

FAMILIES per sequence:
  (a) BIP-39: filter to the wordlist (exact, and 4-letter-prefix rule; with
      hyphenated words joined and split), windows 12/15/18/21/24, checksum
      -> 8 passphrases x quick_paths -> oracle.
  (b) Electrum v2: contiguous 12/13-word windows (and 14..24) of the
      UNFILTERED sequence, three normalisations -> seed-version byte ->
      8 passphrases x 14 paths -> oracle.
  (c) Old Electrum: filter to the 1626-word list, 12-windows -> stretched
      key -> 5 receive + 5 change addresses -> oracle.
  (d) Printed key: initials (as printed / lower / upper / first two letters)
      -> sliding 51/52 (WIF), 58 (BIP38), 22/26/30 (mini) windows, both
      string directions.
  (e) Fallback: the sequence as a brainwallet phrase (7 hashes x 5 types).

CONTROLS (all must fire before the null means anything):
  (i)   synthetic p75 with 'abandon x11 about' bolded among real lines ->
        1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA must be derived by the pipeline
  (ii)  Electrum test seed injected as 12 bold words -> version 'standard'
        and its m/0/0 address derived through the same path
  (iii) a random WIF spelled as initials of bold words -> recovered by (d)
  (iv)  oracle sees the genesis address
  (v)   old-Electrum 12-word vector injected -> its old/0/0 address derived

Usage: python3 emph_seed.py [--no-old] [--controls-only] [--log FILE]
"""
import os, sys, re, json, time, hashlib, argparse

HERE = os.path.dirname(os.path.abspath(__file__))       # solver/wf
SOLVER = os.path.dirname(HERE)
sys.path.insert(0, SOLVER)
sys.path.insert(0, HERE)
import numpy as np
import harness as H
from typo_cipher import parse_marked

SCRATCH = os.environ.get("EMPH_SCRATCH",
    "/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/emph_seed")
os.makedirs(SCRATCH, exist_ok=True)

PAGES = [75, 76, 77, 78, 79]
PASSPHRASES = ["", "El Salvador", "ElSalvador", "el salvador", "EL SALVADOR",
               "elsalvador", "Overdose", "Max Keiser"]
MODES = ["w10", "w05", "any"]
THR = {"w10": 1.0, "w05": 0.5, "any": 1e-9}
BIP39_LENS = (12, 15, 18, 21, 24)
PREFIX = {}
for _w in H.BIP39:
    PREFIX.setdefault(_w[:4], _w)      # first 4 letters are unique in BIP-39

# ------------------------------------------------------------------ oracle --
def make_oracle():
    """harness.Oracle, with the full-index prefix array converted to native
    uint64 once. The stored array is big-endian ('>u8'); np.searchsorted on a
    non-native array re-converts all 454 MB per call (~340 ms/lookup). Numeric
    order equals byte order, so the conversion preserves the binary search."""
    O = H.Oracle()
    if O.full is not None:
        full = O.full
        native = full.prefix.astype(np.uint64)

        def _lookup_hash(h32, _p=native, _rec=full._record):
            key = np.uint64(int.from_bytes(h32[:8], "big"))
            lo = int(np.searchsorted(_p, key, side="left"))
            hi = int(np.searchsorted(_p, key, side="right"))
            for i in range(lo, hi):
                sh, bal = _rec(i)
                if sh == h32:
                    return bal
            return None
        full._lookup_hash = _lookup_hash
        assert full.balance("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"), "fast lookup broke calibration"
    return O


# ------------------------------------------------------------------ tokens --
MARKUP_RE = re.compile(r"\*\*|__|~~|\+\+|\[O:|\[B:|\[W:|\]|\?\?")


def raw_chunks(marked):
    s = MARKUP_RE.sub("", marked)
    return [c for c in s.split() if any(ch.isalnum() for ch in c)]


def load_lines(lines, page):
    """lines: list of {'line_no','marked'} -> token stream with flags."""
    toks = []
    for ln in lines:
        pt = parse_marked(ln["marked"])
        rc = raw_chunks(ln["marked"])
        if len(pt) != len(rc):
            sys.stderr.write(f"WARN p{page} line {ln['line_no']}: {len(pt)} parsed vs {len(rc)} raw chunks\n")
        for i, t in enumerate(pt):
            r = rc[i] if i < len(rc) else t["word"]
            t["raw"] = r
            t["page"] = page
            t["line"] = ln["line_no"]
            core = r.rstrip("\"'’”)]")
            t["sent_end"] = core[-1:] in ".!?"
            toks.append(t)
    return toks


def load_page_json(path, page):
    return load_lines(json.load(open(path))["lines"], page)


P79_HAND = [
    "To wrap this up, as we move from a [B: **war and violence**]",
    "[B: **economy**] to a peace and love economy, the efficiencies",
    "of love — because bitcoin is [O: **infinitely more efficient**]",
    "[O: **to transact and store wealth in than fiat, shitcoins**]",
    "[O: **or gold**] — the overall energy consumption, even while",
    "Bitcoin makes its 51% attack on global energy supply,",
    "drops by 95% or more. [O: **That's right, Bitcoin will take**]",
    "[O: **all the energy.**] In so doing, our energy consumption",
    "drops to near **zero** because our natural tendency toward",
    "**love** and **peace** gets **monetized** for **the** **first** **time** **in**",
    "**our existence. Poverty disappears because the fear**",
    "**of being poor disappears because Bitcoin allows us**",
    "**to fully express ourselves individually in a cyber**",
    "**sea of billions of souls all looking to connect** and",
    "express love for each other and the cost for this explosion",
    "of peace is the same as a smile — virtually nothing.",
    "Yes, for some, the **Bitcoin rabbit hole** ends up",
    "in John and Yoko's hotel room in Amsterdam",
    "during their 1969 bed-in.",
    "[O: **Everyone will live their own experience in the rabbit hole.**]",
    "[O: **We are getting our souls back and our minds.**]",
    "Stacy and I **have been living** in **here** for 10 years.",
    "**We've seen some shit.** Happy to **share** it **all with** you",
    "— the agony and ecstasy — **as Bitcoin conquers fear**",
    "**and hate and replaces it with peace and love.**",
    "MAX KEISER",
]


def load_all():
    per = {}
    for p in PAGES:
        fp = os.path.join(HERE, f"typography_p{p}.json")
        if os.path.exists(fp):
            per[f"p{p}" if p != 79 else "p79json"] = load_page_json(fp, p)
        else:
            sys.stderr.write(f"typography_p{p}.json missing\n")
    per["p79hand"] = load_lines([{"line_no": i + 1, "marked": m} for i, m in enumerate(P79_HAND)], 79)
    return per


# --------------------------------------------------------------- sequences --
def is_bar(t):
    return t["orange"] > 0 or t["black"] > 0 or t["white"] > 0


def is_emph(t, mode):
    return is_bar(t) or t["bold"] >= THR[mode]


def runs_of(flags, toks, line_bounded=False):
    """maximal runs of True in flags -> list of (start, end_exclusive)."""
    out, s = [], None
    for i, f in enumerate(flags):
        brk = line_bounded and i > 0 and (toks[i]["page"], toks[i]["line"]) != (toks[i - 1]["page"], toks[i - 1]["line"])
        if f and s is None:
            s = i
        elif f and brk:
            out.append((s, i)); s = i
        elif not f and s is not None:
            out.append((s, i)); s = None
    if s is not None:
        out.append((s, len(flags)))
    return out


def sentences(toks):
    out, s = [], 0
    for i, t in enumerate(toks):
        if t["sent_end"]:
            out.append((s, i + 1)); s = i + 1
    if s < len(toks):
        out.append((s, len(toks)))
    return out


def build_sequences(toks, mode):
    """name -> list of tokens (reading order)."""
    E = [is_emph(t, mode) for t in toks]
    BN = [(t["bold"] >= THR[mode]) and not is_bar(t) for t in toks]
    S = {}
    S["emph"] = [t for t, e in zip(toks, E) if e]
    S["bold_nobar"] = [t for t, b in zip(toks, BN) if b]
    S["nonemph"] = [t for t, e in zip(toks, E) if not e]
    R = runs_of(E, toks)
    S["runfirst"] = [toks[a] for a, b in R]
    S["runlast"] = [toks[b - 1] for a, b in R]
    S["before"] = [toks[a - 1] for a, b in R if a > 0]
    S["after"] = [toks[b] for a, b in R if b < len(toks)]
    RL = runs_of(E, toks, line_bounded=True)
    S["runfirst_L"] = [toks[a] for a, b in RL]
    S["runlast_L"] = [toks[b - 1] for a, b in RL]
    RB = runs_of(BN, toks)
    S["boldrun_first"] = [toks[a] for a, b in RB]
    S["boldrun_last"] = [toks[b - 1] for a, b in RB]
    sef, sel, esf, esl = [], [], [], []
    for a, b in sentences(toks):
        idx = [i for i in range(a, b) if E[i]]
        if idx:
            sef.append(toks[idx[0]]); sel.append(toks[idx[-1]])
            esf.append(toks[a]); esl.append(toks[b - 1])
    S["sent_emph_first"], S["sent_emph_last"] = sef, sel
    S["esent_first"], S["esent_last"] = esf, esl
    if mode == "w10":   # mode-independent sequences, computed once
        S["bar_all"] = [t for t in toks if is_bar(t)]
        S["orange"] = [t for t in toks if t["orange"] > 0]
        S["black"] = [t for t in toks if t["black"] > 0]
        S["white"] = [t for t in toks if t["white"] > 0]
        S["under_strike"] = [t for t in toks if t["under"] > 0 or t["strike"] > 0]
        SS = sentences(toks)
        S["sent_first"] = [toks[a] for a, b in SS]
        S["sent_last"] = [toks[b - 1] for a, b in SS]
    return S


# ------------------------------------------------------------ normalisers --
def norm_join(w):
    return re.sub(r"[^a-z]", "", w.lower())


def norm_split(w):
    return [x for x in (re.sub(r"[^a-z]", "", p) for p in re.split(r"[-–]", w.lower())) if x]


def norm_typed(raw):
    x = raw.lower().replace("’", "'")
    return re.sub(r"[^a-z0-9'\-]", "", x).strip("'-")


def words_join(seq):
    return [x for x in (norm_join(t["word"]) for t in seq) if x]


def words_split(seq):
    out = []
    for t in seq:
        out += norm_split(t["word"])
    return out


def words_typed(seq):
    return [x for x in (norm_typed(t["raw"]) for t in seq) if x]


def bip39_map(w, rule):
    if w in H.BIP39_SET:
        return w
    if rule == "prefix" and len(w) >= 4 and w[:4] in PREFIX:
        return PREFIX[w[:4]]
    return None


def first_alnum(s):
    for c in s:
        if c.isalnum():
            return c
    return ""


def first_two(s):
    a = [c for c in s if c.isalnum()]
    return "".join(a[:2])


# ------------------------------------------------------------------- sink --
class Sink:
    def __init__(self, O, watch=None):
        self.O = O
        self.watch = set(watch or [])
        self.hits = []          # funded
        self.watch_hits = []    # control addresses seen
        self.n_addr = 0
        self.n_keys = 0
        self.seen_mn = set()
        self.seen_el = set()
        self.seen_old = set()
        self.seen_phrase = set()
        self.seen_wif = set()
        self.c = {}

    def bump(self, k, n=1):
        self.c[k] = self.c.get(k, 0) + n

    def addr(self, tag, path, typ, a, priv):
        self.n_addr += 1
        if a in self.watch:
            self.watch_hits.append((tag, path, typ, a))
        if self.O.funded(a):
            self.hits.append((tag, path, typ, a, priv.hex() if isinstance(priv, bytes) else priv))
            print("HIT", tag, path, typ, a, self.hits[-1][4], flush=True)

    def key(self, tag, priv32):
        self.n_keys += 1
        for typ, a in H.addrs_for_priv(priv32).items():
            self.addr(tag, "-", typ, a, priv32)

    # (a) BIP-39
    def bip39(self, tag, words):
        m = " ".join(words)
        if m in self.seen_mn:
            return
        self.seen_mn.add(m)
        self.bump("bip39_unique_valid")
        for pw in PASSPHRASES:
            self.bump("bip39_seeds")
            for p, t, a, k in H.bip39_addrs(m, pw, H.quick_paths()):
                self.addr(f"{tag} BIP39[{m}] pw='{pw}'", p, t, a, k)

    # (b) Electrum v2
    def electrum(self, tag, text, ver):
        if text in self.seen_el:
            return
        self.seen_el.add(text)
        self.bump("electrum_unique_valid")
        for pw in PASSPHRASES:
            self.bump("electrum_seeds")
            for p, t, a, k in H.electrum_v2_addrs(text, pw, 5):
                self.addr(f"{tag} ELECTRUM-{ver}[{text}] pw='{pw}'", p, t, a, k)

    # (c) old Electrum
    def old(self, tag, words):
        key = tuple(words)
        if key in self.seen_old:
            return
        self.seen_old.add(key)
        self.bump("old_unique")
        for ch in (False, True):
            for p, t, a, k in H.electrum_old_addrs(list(words), 5, change=ch):
                self.addr(f"{tag} OLDELECTRUM[{' '.join(words)}]", p, t, a, k)

    # (d) printed key strings
    def keystring(self, tag, s):
        n = len(s)
        for L in (51, 52, 58, 22, 26, 30):
            for i in range(0, n - L + 1):
                sub = s[i:i + L]
                self.bump("key_windows")
                if L in (51, 52):
                    r = H.wif_check(sub)
                    if r:
                        self.bump("wif_valid")
                        if sub not in self.seen_wif:
                            self.seen_wif.add(sub)
                            print("WIF-VALID", tag, sub, r[1].hex(), flush=True)
                            self.hits.append((f"{tag} WIF-checksum-valid", "-", r[0], sub, r[1].hex()))
                            self.key(f"{tag} WIF[{sub}]", r[1])
                elif L == 58:
                    r = H.bip38_check(sub)
                    if r:
                        self.bump("bip38_valid")
                        print("BIP38-VALID", tag, sub, flush=True)
                        self.hits.append((f"{tag} BIP38-checksum-valid", "-", "bip38", sub, r[1].hex()))
                else:
                    r = H.mini_check(sub)
                    if r:
                        self.bump("mini_pass")
                        self.key(f"{tag} MINI[{sub}]", r[1])

    # (e) brainwallet fallback
    def phrase(self, tag, s):
        if not s or s in self.seen_phrase:
            return
        self.seen_phrase.add(s)
        self.bump("phrases")
        for name, t, a, k in self.O.check_phrase_direct(s):
            self.hits.append((f"{tag} DIRECT-{name}[{s[:80]}]", "-", t, a, k))
            print("HIT", tag, name, t, a, k, flush=True)
        self.n_addr += 35


# ---------------------------------------------------------- per sequence --
def process_sequence(tag, seq, sink, do_old=True, old_queue=None):
    """Run families (a),(b),(d),(e) on one token sequence; queue (c)."""
    st = dict(len=len(seq))
    # (a) BIP-39 ---------------------------------------------------------
    wj, ws = words_join(seq), words_split(seq)
    st["bip39_words"] = sum(1 for w in wj if w in H.BIP39_SET)
    st["bip39_windows"] = st["bip39_valid"] = 0
    seen_fw = set()
    for rule in ("exact", "prefix"):
        for base in (wj, ws):
            fw = [x for x in (bip39_map(w, rule) for w in base) if x]
            if tuple(fw) in seen_fw:
                continue
            seen_fw.add(tuple(fw))
            for L in BIP39_LENS:
                for i in range(len(fw) - L + 1):
                    win = fw[i:i + L]
                    st["bip39_windows"] += 1
                    if H.bip39_valid(win):
                        st["bip39_valid"] += 1
                        sink.bip39(f"{tag} rule={rule} @{i} L={L}", win)
    # (b) Electrum v2 -----------------------------------------------------
    st["el_win1213"] = st["el_valid1213"] = st["el_win_all"] = st["el_valid_all"] = 0
    seen_base = set()
    for nname, base in (("letters", wj), ("split", ws), ("typed", words_typed(seq))):
        if tuple(base) in seen_base:
            continue
        seen_base.add(tuple(base))
        for L in range(12, 25):
            for i in range(len(base) - L + 1):
                text = " ".join(base[i:i + L])
                st["el_win_all"] += 1
                if L in (12, 13):
                    st["el_win1213"] += 1
                v = H.electrum_v2_type(text)
                if v:
                    st["el_valid_all"] += 1
                    if L in (12, 13):
                        st["el_valid1213"] += 1
                    sink.electrum(f"{tag} norm={nname} @{i} L={L}", text, v)
    # (c) old Electrum: queue unique windows ----------------------------------
    st["old_windows"] = 0
    if do_old:
        seen_fo = set()
        for base in (wj, ws):
            fo = [w for w in base if w in H.ELECTRUM_OLD_SET]
            if tuple(fo) in seen_fo:
                continue
            seen_fo.add(tuple(fo))
            for i in range(len(fo) - 11):
                st["old_windows"] += 1
                key = tuple(fo[i:i + 12])
                if old_queue is not None and key not in old_queue:
                    old_queue[key] = f"{tag} @{i}"
    # (d) printed-key initials -------------------------------------------
    raws = [t["raw"] for t in seq]
    streams = {
        "init_printed": "".join(first_alnum(r) for r in raws),
        "init_word": "".join(t["word"][0] for t in seq if t["word"]),
        "first2_printed": "".join(first_two(r) for r in raws),
    }
    streams["init_lower"] = streams["init_printed"].lower()
    streams["init_upper"] = streams["init_printed"].upper()
    streams["first2_lower"] = streams["first2_printed"].lower()
    k0 = sink.c.get("wif_valid", 0) + sink.c.get("bip38_valid", 0)
    for sname, s in streams.items():
        sink.keystring(f"{tag} {sname}", s)
        sink.keystring(f"{tag} {sname} strrev", s[::-1])
    st["wif_bip38_valid"] = sink.c.get("wif_valid", 0) + sink.c.get("bip38_valid", 0) - k0
    # (e) direct fallback ---------------------------------------------------
    if seq:
        forms = [" ".join(raws), " ".join(t["word"] for t in seq), " ".join(wj), "".join(wj),
                 " ".join(words_typed(seq))]
        forms += [f[::-1] for f in forms]
        for f in forms:
            sink.phrase(f"{tag} direct", f)
    return st


def process_scope(scope, toks, sink, log, do_old=True, old_queue=None, modes=MODES):
    rows = []
    for mode in modes:
        S = build_sequences(toks, mode)
        for name, seq in S.items():
            for d in ("fwd", "rev"):
                s2 = seq if d == "fwd" else seq[::-1]
                tag = f"{scope}/{mode}/{name}/{d}"
                st = process_sequence(tag, s2, sink, do_old, old_queue)
                row = [scope, mode, name, d] + [st[k] for k in ("len", "bip39_words", "bip39_windows", "bip39_valid",
                                                                  "el_win1213", "el_valid1213", "el_win_all", "el_valid_all",
                                                                  "old_windows", "wif_bip38_valid")]
                rows.append(row)
                log.write("\t".join(str(x) for x in row) + "\n")
    log.flush()
    return rows


ROW_HDR = ["scope", "mode", "seq", "dir", "len", "bip39_words", "bip39_windows", "bip39_valid",
           "el_win12_13", "el_valid12_13", "el_win_all", "el_valid_all", "old_windows", "wif_bip38_valid"]


# --------------------------------------------------------------- controls --
def synth_page(src_page, edits, name):
    """Copy typography_p{src}.json, replace line texts per edits {line_no: marked}, write to scratch."""
    j = json.load(open(os.path.join(HERE, f"typography_p{src_page}.json")))
    for ln in j["lines"]:
        if ln["line_no"] in edits:
            ln["marked"] = edits[ln["line_no"]]
    fp = os.path.join(SCRATCH, f"{name}.json")
    json.dump(j, open(fp, "w"), indent=1)
    return fp


def run_controls(O, log, do_old):
    res = []
    # (i) BIP-39 vector bolded among real p75 lines (lines 2 and 3 are regular text; nothing emphasised between)
    ab6 = " ".join(["**abandon**"] * 6)
    ab5 = " ".join(["**abandon**"] * 5)
    fp = synth_page(75, {2: f"Here's the bitter truth. {ab6} Bitcoin was not a reaction",
                         3: f"to the Global Financial {ab5} **about** Crisis of 2008. It caused it."},
                    "control_p75_bip39")
    toks = load_page_json(fp, 75)
    target = "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"
    sk = Sink(O, watch=[target])
    process_scope("CTRL-i", toks, sk, log, do_old=False, modes=["w10"])
    ok = any(a == target for _, _, _, a in sk.watch_hits)
    seen = [w for w in sk.watch_hits if w[3] == target][:1]
    res.append(("(i) BIP-39 vector bolded in p75 -> 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA derived", ok, seen))
    # (ii) Electrum v2 vector as 12 consecutive bold words (p76 lines 11-13 are regular)
    ev = "cycle rocket west magnet parrot shuffle foot correct salt library feed song".split()
    b = lambda ws: " ".join(f"**{w}**" for w in ws)
    fp = synth_page(76, {11: f"The collective unconscious, {b(ev[:4])} controlled now by psychotic",
                         12: f"cats, plays \"Friends\" {b(ev[4:8])} reruns all day in our heads.",
                         13: f"Our imaginations {b(ev[8:])} and inventiveness have been euthanized"},
                    "control_p76_electrum")
    toks = load_page_json(fp, 76)
    exp = [a for p, t, a, k in H.electrum_v2_addrs(" ".join(ev), "", 1) if p == "m/0/0" and t == "p2pkh_c"][0]
    sk = Sink(O, watch=[exp])
    process_scope("CTRL-ii", toks, sk, log, do_old=False, modes=["w10"])
    fired = [t for t in sk.seen_el if t == " ".join(ev)]
    ok = bool(fired) and any(a == exp for _, _, _, a in sk.watch_hits)
    res.append((f"(ii) Electrum seed as 12 bold words -> electrum_v2_type=='standard' fired and m/0/0 {exp} derived", ok,
                [w for w in sk.watch_hits if w[3] == exp][:1]))
    # (iii) random WIF spelled as initials of bold words (p77 lines 22-23 regular, adjacent)
    priv = os.urandom(32)
    wif = H.to_wif(priv, True)
    ws = [f"**{c}qz**" for c in wif]
    fp = synth_page(77, {22: "It's a guaranteed, mathematical certainty. " + " ".join(ws[:26]) + " Let me explain",
                         23: "why, and this " + " ".join(ws[26:]) + " might be the first time you're hearing this,"},
                    "control_p77_wif")
    toks = load_page_json(fp, 77)
    sk = Sink(O)
    process_scope("CTRL-iii", toks, sk, log, do_old=False, modes=["w10"])
    ok = wif in sk.seen_wif
    res.append((f"(iii) random WIF {wif} spelled as bold-word initials -> recovered by wif_check with matching priv", ok,
                [(wif, priv.hex())] if ok else []))
    # (iv) oracle genesis
    res.append(("(iv) oracle funded(genesis)", O.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"), []))
    # (v) old Electrum vector as 12 bold words
    ov = H.electrum_old_encode("431a62f1c86555d3c45e5c1e9ab77c8c")
    fp = synth_page(76, {11: f"The collective unconscious, {b(ov[:4])} controlled now by psychotic",
                         12: f"cats, plays \"Friends\" {b(ov[4:8])} reruns all day in our heads.",
                         13: f"Our imaginations {b(ov[8:])} and inventiveness have been euthanized"},
                    "control_p76_old")
    toks = load_page_json(fp, 76)
    exp = H.electrum_old_addrs(ov, 1)[0][2]
    sk = Sink(O, watch=[exp])
    q = {}
    process_scope("CTRL-v", toks, sk, log, do_old=True, old_queue=q, modes=["w10"])
    if tuple(ov) in q:
        sk.old(q[tuple(ov)], ov)
    ok = any(a == exp for _, _, _, a in sk.watch_hits)
    res.append((f"(v) old-Electrum vector as 12 bold words -> old/0/0 {exp} derived", ok,
                [w for w in sk.watch_hits if w[3] == exp][:1]))
    return res


# ------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-old", action="store_true", help="skip old-Electrum stretching")
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--log", default=os.path.join(HERE, "emph_seed.tsv"))
    args = ap.parse_args()
    t0 = time.time()
    O = make_oracle()
    log = open(args.log, "w")
    log.write("\t".join(ROW_HDR) + "\n")

    print("=== CONTROLS ===")
    ctrl = run_controls(O, log, not args.no_old)
    for name, ok, ev in ctrl:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {ev if ev else ''}")
    if not all(ok for _, ok, _ in ctrl):
        print("CONTROL FAILURE -- pipeline not trusted; stopping")
        sys.exit(2)
    if args.controls_only:
        return

    per = load_all()
    for k, v in per.items():
        print(f"  tokens {k}: {len(v)}  emph(w10)={sum(is_emph(t,'w10') for t in v)}  "
              f"bold_nobar(w10)={sum(t['bold']>=1 and not is_bar(t) for t in v)}  bar={sum(is_bar(t) for t in v)}")
    base = per["p75"] + per["p76"] + per["p77"] + per["p78"]
    scopes = [("all+p79json", base + per["p79json"]), ("all+p79hand", base + per["p79hand"]), ("all-no79", base),
              ("p75", per["p75"]), ("p76", per["p76"]), ("p77", per["p77"]), ("p78", per["p78"]),
              ("p79json", per["p79json"]), ("p79hand", per["p79hand"])]
    sink = Sink(O)
    old_queue = {}
    all_rows = []
    print("=== SWEEP (families a,b,d,e) ===")
    for scope, toks in scopes:
        t1 = time.time()
        rows = process_scope(scope, toks, sink, log, do_old=not args.no_old, old_queue=old_queue)
        all_rows += rows
        print(f"  {scope}: {len(rows)} sequences, bip39 windows={sum(r[6] for r in rows)} valid={sum(r[7] for r in rows)}, "
              f"electrum12/13 windows={sum(r[8] for r in rows)} valid={sum(r[9] for r in rows)} (all L: {sum(r[10] for r in rows)}/{sum(r[11] for r in rows)}), "
              f"old windows={sum(r[12] for r in rows)}, wif/bip38 valid={sum(r[13] for r in rows)}  [{time.time()-t1:.0f}s, addrs so far {sink.n_addr}]", flush=True)
    if not args.no_old:
        print(f"=== OLD ELECTRUM: {len(old_queue)} unique 12-word windows ===", flush=True)
        t1 = time.time()
        for n, (key, tag) in enumerate(old_queue.items()):
            sink.old(tag, list(key))
            if (n + 1) % 1000 == 0:
                print(f"  old {n+1}/{len(old_queue)}  {time.time()-t1:.0f}s", flush=True)

    print("=== WHOLE-ARTICLE ROWS, mode w10, forward ===")
    print("\t".join(ROW_HDR))
    for r in all_rows:
        if r[0].startswith("all") and r[1] == "w10" and r[3] == "fwd":
            print("\t".join(str(x) for x in r))
    print("=== TOTALS ===")
    tot = dict(sequences=len(all_rows), bip39_windows=sum(r[6] for r in all_rows), bip39_valid=sum(r[7] for r in all_rows),
               electrum_windows_12_13=sum(r[8] for r in all_rows), electrum_valid_12_13=sum(r[9] for r in all_rows),
               electrum_windows_all=sum(r[10] for r in all_rows), electrum_valid_all=sum(r[11] for r in all_rows),
               old_windows=sum(r[12] for r in all_rows), wif_bip38_valid=sum(r[13] for r in all_rows))
    tot.update(sink.c)
    tot["addresses_checked"] = sink.n_addr
    tot["seconds"] = round(time.time() - t0)
    for k, v in tot.items():
        print(f"  {k}: {v}")
    print(f"HITS: {len(sink.hits)}")
    for h in sink.hits:
        print("  ", h)
    log.write("# TOTALS " + json.dumps(tot) + "\n")
    log.write("# HITS " + json.dumps(sink.hits) + "\n")
    log.close()


if __name__ == "__main__":
    main()
