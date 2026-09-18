#!/usr/bin/env python3
"""
Sand and Musset on PRINTED line breaks -- the only literary test still open.

WHY THIS AND NOTHING ELSE
Keiser named one device: "Like George Sand's hidden cryptography, I have hidden
private keys in the text", and specified "have you ever picked up a PHYSICAL
COPY". The Sand-Musset letters are an exchange of two rules:

    Sand    read every other PRINTED line
    Musset  read the FIRST WORD of each PRINTED line

Both are destroyed by reflow. Web text has no print line breaks, so running
them on a web transcript tests nothing -- and the web text of the two later
OVERDOSE columns is exactly what the repo already ran the battery on. What was
never available for those columns is their PRINT line breaks.

THE DISCIPLINE THIS TOOL ENFORCES
It does not hash anything by default. It EXTRACTS the readings, scores them
against a shuffled-line null, and PRINTS them to be read. A reading earns a
derivation only by being a grammatical English instruction; that gate is a
human call, and `--derive` is the separate, deliberate second step. Mass
hashing of another column is the dry well this is built to avoid.

INPUT
A PDF with a real text layer (the print pamphlet), or a line-faithful text
file. PDF lines are recovered from glyph baselines and grouped into columns by
x-position, because a two-column page read straight across yields interleaved
nonsense -- the failure mode that would quietly break the whole test.

  python3 print_musset.py --selftest
  python3 print_musset.py --pdf buy_love_sell_fear.pdf
  python3 print_musset.py --text article_transcript.txt
"""
import argparse, os, re, shutil, statistics, sys, random

STOP_OPENERS = {"the", "a", "an", "of", "and", "to", "in", "is", "was", "that",
                "it", "for", "on", "with", "as", "at", "by", "from", "but"}
IMPERATIVES = {"buy", "sell", "read", "take", "use", "find", "look", "go",
               "send", "spend", "hold", "keep", "open", "close", "start",
               "stop", "add", "sum", "count", "reverse", "mirror", "write",
               "hide", "seek", "follow", "skip", "join", "split", "type",
               "enter", "make", "give", "get", "put", "turn", "flip", "sign",
               "check", "trust", "verify", "love", "fear", "remember"}


# ---------------------------------------------------------------- extraction
def lines_from_pdf(path, col_gap=60.0):
    """Printed lines in reading order, columns kept separate.

    Four backends, tried in order of how well they preserve the thing this
    whole test depends on -- the printed line break. No single PDF library is
    universally installed, and the test is worthless if it cannot run."""
    for fn in (_pdf_fitz, _pdf_plumber, _pdf_pdftotext, _pdf_pypdf):
        try:
            lines = fn(path, col_gap)
        except ImportError:
            continue
        except FileNotFoundError:
            continue
        except Exception as e:
            sys.stderr.write(f"  {fn.__name__}: {e!r}\n")
            continue
        if lines and len(lines) >= 20:
            sys.stderr.write(f"  line extraction: {fn.__name__} "
                             f"({len(lines)} printed lines)\n")
            return lines
    raise SystemExit(
        "no usable PDF text backend.\n"
        "  Install ONE of these, then re-run:\n"
        "    pip install pymupdf          # best: real glyph baselines\n"
        "    pip install pdfplumber       # also has coordinates\n"
        "    sudo apt install poppler-utils   # pdftotext -layout\n"
        "    pip install pypdf            # last resort\n"
        "  If the file is a scan with no text layer, none of them will help:\n"
        "  this test needs real line breaks, and OCR would invent them.")


def _pdf_fitz(path, col_gap):
    import fitz
    doc = fitz.open(path)
    out = []
    for page in doc:
        d = page.get_text("dict")
        spans = []
        for blk in d.get("blocks", []):
            for ln in blk.get("lines", []):
                for sp in ln.get("spans", []):
                    t = sp.get("text", "")
                    if t.strip():
                        x0, y0, x1, y1 = sp["bbox"]
                        spans.append((x0, x1, round(y1, 1), t))
        if not spans:
            continue
        xs = sorted(s[0] for s in spans)
        cuts, prev = [], xs[0]
        for x in xs[1:]:
            if x - prev > col_gap:
                cuts.append((prev + x) / 2)
            prev = x
        def col_of(x):
            return sum(1 for c in cuts if x > c)
        rows = {}
        for x0, x1, y, t in spans:
            rows.setdefault((col_of(x0), y), []).append((x0, t))
        for (c, y) in sorted(rows, key=lambda k: (k[0], k[1])):
            parts = [t for _x, t in sorted(rows[(c, y)])]
            s = re.sub(r"\s+", " ", "".join(parts)).strip()
            if s:
                out.append(s)
    return out


def _pdf_plumber(path, col_gap):
    """pdfplumber: words with x/top, grouped into lines then columns."""
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            if not words:
                continue
            xs = sorted(w["x0"] for w in words)
            cuts, prev = [], xs[0]
            for x in xs[1:]:
                if x - prev > col_gap:
                    cuts.append((prev + x) / 2)
                prev = x
            def col_of(x):
                return sum(1 for c in cuts if x > c)
            rows = {}
            for w in words:
                rows.setdefault((col_of(w["x0"]), round(w["top"], 0)), []).append((w["x0"], w["text"]))
            for k in sorted(rows, key=lambda k: (k[0], k[1])):
                s_ = re.sub(r"\s+", " ", " ".join(t for _x, t in sorted(rows[k]))).strip()
                if s_:
                    out.append(s_)
    return out


def _pdf_pdftotext(path, col_gap):
    """poppler's pdftotext -layout: keeps line breaks and column geometry."""
    import subprocess, tempfile
    exe = shutil.which("pdftotext")
    if not exe:
        raise ImportError("pdftotext not installed")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t:
        tmp = t.name
    try:
        subprocess.run([exe, "-layout", "-enc", "UTF-8", path, tmp],
                       check=True, capture_output=True, timeout=180)
        raw = open(tmp, encoding="utf-8", errors="replace").read()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    out = []
    for ln in raw.splitlines():
        # -layout pads columns with runs of spaces; split them back apart so a
        # two-column page does not read across the gutter.
        for part in re.split(r"\s{%d,}" % 6, ln):
            s_ = part.strip()
            if s_ and not re.fullmatch(r"[\f\s]*", s_):
                out.append(re.sub(r"\s+", " ", s_))
    return out


def _pdf_pypdf(path, col_gap):
    """pypdf: text with line breaks, no coordinates. Last resort."""
    from pypdf import PdfReader
    out = []
    for page in PdfReader(path).pages:
        for ln in (page.extract_text() or "").splitlines():
            s_ = re.sub(r"\s+", " ", ln).strip()
            if s_:
                out.append(s_)
    return out


def lines_from_text(path):
    """A line-faithful text file: one printed line per line, markers dropped."""
    out = []
    for raw in open(path, encoding="utf-8", errors="replace"):
        s = raw.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#") or s.startswith("==="):
            continue
        out.append(s.strip())
    return out


# ---------------------------------------------------------------- readings
def readings(lines):
    """The Sand-Musset exchange, plus the near neighbours of each rule."""
    L = [l for l in lines if l.strip()]
    words = [l.split() for l in L]
    r = {}
    r["musset_first_word"] = " ".join(w[0] for w in words if w)
    r["musset_first_word_clean"] = " ".join(re.sub(r"[^A-Za-z'’-]", "", w[0])
                                            for w in words if w and re.sub(r"[^A-Za-z'’-]", "", w[0]))
    r["musset_last_word"] = " ".join(w[-1] for w in words if w)
    r["musset_first_letter"] = "".join(l[0] for l in L)
    r["musset_last_letter"] = "".join(re.sub(r"[^A-Za-z]", "", l)[-1:] for l in L
                                      if re.sub(r"[^A-Za-z]", "", l))
    r["sand_odd_lines"] = " ".join(L[0::2])
    r["sand_even_lines"] = " ".join(L[1::2])
    r["sand_odd_first_words"] = " ".join(w[0] for w in words[0::2] if w)
    r["sand_even_first_words"] = " ".join(w[0] for w in words[1::2] if w)
    r["second_word"] = " ".join(w[1] for w in words if len(w) > 1)
    return r


# ---------------------------------------------------------------- scoring
def _vocab():
    v = set()
    for p in ("/usr/share/dict/words",):
        if os.path.exists(p):
            v |= {w.strip().lower() for w in open(p, errors="ignore") if len(w.strip()) > 2}
    try:
        from mnemonic import Mnemonic
        v |= set(Mnemonic("english").wordlist)
    except Exception:
        pass
    v |= {"a", "i", "is", "it", "of", "to", "in", "on", "at", "by", "we", "be",
          "do", "go", "up", "my", "me", "no", "so", "if", "or", "as", "an"}
    return v


def english_rate(seq, vocab):
    """Fraction of tokens that are dictionary words."""
    toks = [re.sub(r"[^a-z]", "", t.lower()) for t in seq.split()]
    toks = [t for t in toks if t]
    if not toks:
        return 0.0
    return sum(1 for t in toks if t in vocab) / len(toks)


def looks_like_command(seq):
    """Does the reading open like an imperative instruction?

    Keiser's device, if it exists, has to say something a reader can ACT on.
    An English word-rate alone is not that: the first words of any English
    prose are mostly English words. A command starts with a verb."""
    toks = [re.sub(r"[^a-z]", "", t.lower()) for t in seq.split()[:4]]
    toks = [t for t in toks if t]
    if not toks:
        return False, "empty"
    if toks[0] in IMPERATIVES:
        return True, f"opens with the imperative {toks[0]!r}"
    if toks[0] in STOP_OPENERS:
        return False, f"opens with {toks[0]!r}, a function word -- prose, not a command"
    return False, f"opens with {toks[0]!r}, not a known imperative"


def score(lines, trials=200, seed=11):
    """Each reading against a null of the SAME lines in shuffled order.

    The null matters: the first words of real prose are real words, so a high
    English rate proves nothing on its own. Shuffling the line order destroys
    any message while preserving the vocabulary exactly."""
    vocab = _vocab()
    real = readings(lines)
    rnd = random.Random(seed)
    nulls = {k: [] for k in real}
    shuf = list(lines)
    for _ in range(trials):
        rnd.shuffle(shuf)
        for k, v in readings(shuf).items():
            nulls[k].append(english_rate(v, vocab))
    rows = []
    for k, v in real.items():
        obs = english_rate(v, vocab)
        mu = statistics.fmean(nulls[k])
        sd = statistics.pstdev(nulls[k]) or 1e-9
        cmd, why = looks_like_command(v)
        rows.append((k, obs, mu, (obs - mu) / sd, cmd, why, v))
    rows.sort(key=lambda r: -r[3])
    return rows


def report(lines, name, trials=200):
    print(f"\n{'='*74}\n  {name}: {len(lines)} printed lines\n{'='*74}")
    print(f"  first 3 lines as extracted:")
    for l in lines[:3]:
        print(f"    | {l[:68]}")
    rows = score(lines, trials)
    print(f"\n  reading                  eng-rate  null   z      command?")
    for k, obs, mu, z, cmd, why, v in rows:
        print(f"  {k:24s} {obs:5.2f}   {mu:5.2f}  {z:+5.1f}   {'YES' if cmd else 'no'}")
    print(f"\n  THE READINGS, to be read rather than hashed:")
    for k, obs, mu, z, cmd, why, v in rows:
        print(f"\n  -- {k}  [{why}]")
        print(f"     {v[:400]}")
    winners = [r for r in rows if r[4]]
    print(f"\n{'='*74}")
    if winners:
        print("  A reading opens like an imperative. READ IT IN FULL before deriving:")
        for r in winners:
            print(f"    {r[0]}: {r[6][:200]}")
        print("  If it is a grammatical instruction, derive it with --derive.")
    else:
        print("  No reading opens as an English command. By the stated rule this")
        print("  column does not carry a Sand/Musset instruction, and NOTHING")
        print("  should be hashed from it.")
    print("=" * 74)
    return rows


# ---------------------------------------------------------------- selftest
def selftest():
    ok = True
    w = sys.stderr.write

    def rep(m, good):
        nonlocal ok
        ok &= bool(good)
        w(f"  {m}: {'OK' if good else 'FAIL'}\n")

    lines = ["Buy low and sell high", "love is the only asset", "fear is a liability"]
    r = readings(lines)
    rep("Musset takes the first word of each printed line",
        r["musset_first_word"] == "Buy love fear")
    rep("Sand takes alternate printed lines",
        r["sand_odd_lines"] == "Buy low and sell high fear is a liability")
    cmd, _why = looks_like_command("Buy love fear")
    rep("an imperative opening is recognised as a command", cmd)
    cmd2, _ = looks_like_command("The economy of love is")
    rep("a function-word opening is NOT a command", not cmd2)

    # PDF round trip: build a PDF with KNOWN line breaks, extract it back.
    # Without this the user cannot tell a working backend from one that
    # silently reflows, and a reflowed extraction would fake or destroy a
    # reading either way.
    try:
        import fitz, tempfile
        want = ["Buy low and sell high", "love is the only asset",
                "fear is a liability", "and war is the most expensive",
                "sell everything that is not scarce",
                "fear nothing that you can verify"] * 5
        d = fitz.open()
        pg = d.new_page()
        y = 60
        for ln in want:
            pg.insert_text((60, y), ln, fontsize=9)
            y += 14
            if y > 760:
                pg = d.new_page(); y = 60
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name
        d.save(tmp); d.close()
        got = lines_from_pdf(tmp)
        os.unlink(tmp)
        same = got[:len(want)] == want
        rep(f"a PDF with known line breaks round-trips ({len(got)} lines back)", same)
        if not same:
            w(f"      wanted[0]={want[0]!r}\n      got[0]={got[0] if got else None!r}\n")
    except ImportError:
        w("  (no PDF library here to build a round-trip fixture; install one "
          "before trusting a PDF reading)\n")
    except Exception as e:
        rep(f"PDF round trip (exception {e!r})", False)

    # the control: Issue 24's own line-faithful transcript must reproduce the
    # KNOWN-BROKEN reading. If the extractor were wrong, it could invent one.
    if os.path.exists("article_transcript.txt"):
        a = lines_from_text("article_transcript.txt")
        ra = readings(a)
        rep(f"Issue 24 transcript reads {len(a)} printed lines", len(a) > 120)
        c, _ = looks_like_command(ra["musset_first_word"])
        rep("Issue 24's Musset reading is NOT a command (the known null)", not c)
        w(f"      Issue 24 Musset: {ra['musset_first_word'][:70]}...\n")
    w("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf")
    ap.add_argument("--text")
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--col-gap", type=float, default=60.0)
    ap.add_argument("--derive", action="store_true",
                    help="ONLY after a reading has been read and judged a "
                         "grammatical instruction: derive keys from it")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("line extraction is wrong; a reading from it would be meaningless")
    if a.selftest:
        return
    if not (a.pdf or a.text):
        sys.exit("give --pdf or --text.\n"
                 "  The print pamphlet of a later OVERDOSE column is the input "
                 "this test exists for;\n  a web transcript has no print line "
                 "breaks and tests nothing.")

    if a.pdf:
        lines = lines_from_pdf(a.pdf, a.col_gap)
        name = os.path.basename(a.pdf)
        if len(lines) < 20:
            sys.exit(f"only {len(lines)} lines of text recovered from {a.pdf}. "
                     f"If it is a scan with no text layer, this test cannot run "
                     f"on it -- it needs real line breaks, not OCR guesses.")
    else:
        lines = lines_from_text(a.text)
        name = os.path.basename(a.text)

    rows = report(lines, name, a.trials)

    if a.derive:
        winners = [r for r in rows if r[4]]
        if not winners:
            sys.exit("\n--derive refused: no reading opens as an English command, "
                     "and hashing a column that carries no instruction is the "
                     "dry well this tool exists to avoid.")
        import continuous_solver as CS
        from hd_sweep import direct_keys
        from full_sweep import spks_for_key
        from spk_extra import spks_extra
        orc = CS.IndexOracle()
        if not orc.ready or not orc.control():
            sys.exit(f"no usable oracle ({orc.why}); a null would be void")
        sys.stderr.write(f"\n  deriving {len(winners)} command reading(s) "
                         f"against {orc.name}\n")
        meta, spks = [], []
        for k, obs, mu, z, cmd, why, v in winners:
            for form in (v, v.lower(), v.upper(), re.sub(r"\s+", "", v)):
                for hn, key in direct_keys(form).items():
                    for st, spk in list(spks_for_key(key)) + list(spks_extra(key)):
                        meta.append(f"{k}|{hn}/{st}")
                        spks.append(spk)
        hits = orc.check(spks)
        for j, bal in hits:
            shown = "PRESENT" if bal is None else f"{bal} sats"
            print(f"  *** {orc.name} HIT {shown} :: {meta[j]}")
        print(f"  {len(spks):,} scripts from the command reading(s): "
              f"{len(hits)} hit(s)")


if __name__ == "__main__":
    main()
