#!/usr/bin/env python3
"""
salvador_seed.py -- NON-checksummed seeds with 'El Salvador' as the wallet passphrase.

HYPOTHESIS (setter-psychology lens, Oct/Nov 2021, Word manuscript -> designer)
Keiser controls WORDS and sentence order; "private keyS" from a 2011-era
bitcoiner means a seed phrase; "'El Salvador' is a clue" is the literal 25th
word -- the BIP-39 / Electrum wallet passphrase.  A showman typing one of his
own sentences into a wallet as a seed would not get a checksum-valid BIP-39
mnemonic (1 in 16 at best, and most of his words are not in the list at all),
but Electrum's BIP-39 option and several web tools proceed past the "checksum
failed" warning and derive from PBKDF2-HMAC-SHA512(sentence, 'mnemonic'+pw)
regardless.  Every earlier sweep in this repo applied its passphrases ONLY to
checksum-valid mnemonics (bip39_sweep, seed_windows, emph_seed, sand_sentences)
or to Electrum-version-valid windows, and kdf_sweep used 'El Salvador' as a raw
PBKDF2 salt taken directly as a private key -- never 'mnemonic'+pw as a BIP-32
seed.  So the most literal reading of the clue has never been executed.

UNITS
  (a) every sentence, printed line, paragraph, page, the whole article and every
      highlight run (all lengths; the 12/15/18/21/24-word ones are HIGH-PRIOR
      and get the full path set), plus the four setter-shaped named units.
  (b) every contiguous 12- and 24-word window (optionally 15/18/21) of the
      prose, under two tokenisations (hyphenated compounds joined / split).
  (c) each of the above in reversed word order (mirror); (a) also char-reversed.
NORMALISATIONS  wallet-style (lowercase, [a-z0-9 ] only, single spaces) and
                as printed (case + punctuation kept, single spaces); (a) also
                letters-only.
SEEDS (no wordlist / checksum / seed-version gate at all)
  H.bip39_seed(text, pw)      = PBKDF2-HMAC-SHA512(NFKD text, 'mnemonic'+pw, 2048)
  H.electrum_v2_seed(text,pw) = PBKDF2-HMAC-SHA512(norm text, 'electrum'+norm pw, 2048)
  pw in 14 variants of El Salvador / Bukele / Overdose / title / author / 20.
PATHS  H.quick_paths() (40 paths x 5 script types) for everything; high-prior
       units get H.default_paths() + Electrum m/0/0-9, m/1/0-1, m/0'/0/0-9,
       m/0'/1/0-1 (96 paths).
ORACLE 1.72M Apr-2023 rich list (immediate) + 56.8M full funded index (batched).

CONTROLS (all must PASS before the null means anything)
  C1 BIP-39 vector 'abandon x11 about' -> m/44'/0'/0'/0/0 = 1LqBGSKu... via the
     same hd_addrs path used by the sweep.
  C2 bip39_seed(vector,'TREZOR').hex() == BIP-39 spec vector c55257c3... (proves
     the 'mnemonic'+passphrase concatenation).
  C3 oracle sees the genesis coinbase; full index calibrated.
  C4 pipeline positives: a synthetic transcript with FOUR planted,
     checksum-INVALID word runs (a 12-word sentence, a 24-word run buried
     mid-sentence, a 12-word sentence printed in reverse order, and the same
     12-word sentence read as printed with punctuation) is pushed through the
     identical unit -> window -> normalisation -> seed -> HD -> oracle code,
     with the independently computed expected addresses (hashlib + hd_sweep,
     not harness) injected as oracle targets.  Each must fire with the matching
     private key, at the family that is supposed to catch it, and at a path
     that only the full path set contains for the high-prior one.

  python3 wf/salvador_seed.py --controls-only
  python3 wf/salvador_seed.py --lengths 12,24            (primary run)
  python3 wf/salvador_seed.py --lengths 15,18,21 --windows-only
"""
import os, re, sys, time, hashlib, argparse, unicodedata
from multiprocessing import get_context

HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.path.dirname(HERE)
sys.path.insert(0, SOLVER)
sys.path.insert(0, HERE)
import numpy as np
import harness as H
import index_oracle as IO
from hd_sweep import derive as hd_derive, addr_p2pkh, addr_p2wpkh, addr_p2sh_p2wpkh
from coincurve import PrivateKey
from sand_sentences import split_sentences

TRANSCRIPT = os.path.join(SOLVER, "article_transcript.txt")
HIGHLIGHTS = os.path.join(SOLVER, "highlights_ordered.tsv")
NON_BODY = {"bitcoin is toxic af", "max keiser"}
SEED_LENS = (12, 15, 18, 21, 24)

PW_BIP39 = ["", "El Salvador", "ElSalvador", "elsalvador", "el salvador", "EL SALVADOR",
            "Salvador", "Bukele", "Nayib Bukele", "Overdose", "OVERDOSE",
            "Bitcoin Is Toxic AF", "Max Keiser", "20"]
# Electrum lower-cases / NFKD-normalises the passphrase itself, so dedupe on that.
PW_ELECTRUM = list(dict.fromkeys(H.electrum_normalize(p) for p in PW_BIP39))

NAMED = [
    "The economy of love is infinitely more efficient than hate and war.",
    "Love opens up the collective unconscious and our joint inner cosmic being.",
    "(Sorry Bhutan, you fell for that snake oil salesmen over at XRP.",
    "Happy to share it all with you — the agony and ecstasy — as Bitcoin conquers fear and hate and replaces it with peace and love.",
]

QUICK_PATHS = H.quick_paths()
# index-0 receive address of every wallet type: what a wallet shows first
MINI_PATHS = ["m/44'/0'/0'/0/0", "m/49'/0'/0'/0/0", "m/84'/0'/0'/0/0", "m/86'/0'/0'/0/0",
              "m/0/0", "m/0'/0/0", "m/0", "m"]
FULL_PATHS = list(dict.fromkeys(
    H.default_paths()
    + [f"m/0/{i}" for i in range(10)] + ["m/1/0", "m/1/1"]
    + [f"m/0'/0/{i}" for i in range(10)] + ["m/0'/1/0", "m/0'/1/1"]))


# ------------------------------------------------------------------ parsing --
def parse_transcript(text):
    """[(pageno, [paragraph, ...])], paragraph = [(lineno, text), ...]"""
    lines = text.split("\n")
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


def load_highlights(path=HIGHLIGHTS):
    out = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or "\t" not in line:
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            out.append((p[0].strip(), p[1].strip(), p[2].strip()))
    return out


# ------------------------------------------------------------ tokenisation --
ALNUM = re.compile(r"[A-Za-z0-9]")


def raw_tokens(s):
    return s.split()


def word_index(raw, hyphen_split):
    """Return list of word tokens plus, per word, the raw index it came from.
    Standalone dashes / pure punctuation are not words."""
    words, ridx = [], []
    for i, t in enumerate(raw):
        if not ALNUM.search(t):
            continue
        if hyphen_split and re.search(r"[A-Za-z0-9][-–][A-Za-z0-9]", t):
            for part in re.split(r"[-–]", t):
                if ALNUM.search(part):
                    words.append(part)
                    ridx.append(i)
        else:
            words.append(t)
            ridx.append(i)
    return words, ridx


def n_words(s, hyphen_split=False):
    return len(word_index(raw_tokens(s), hyphen_split)[0])


def norm_wallet(words):
    ws = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
    return " ".join(w for w in ws if w)


def norm_letters(words):
    ws = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
    return " ".join(w for w in ws if w)


def norm_printed(raw_slice):
    return " ".join(raw_slice)


def texts_for_unit(s, deep):
    """All (dir, norm, text) readings of one unit string."""
    raw = raw_tokens(s)
    out = []
    seen = set()

    def add(d, n, t):
        t = " ".join(t.split())
        if t and t not in seen:
            seen.add(t)
            out.append((d, n, t))

    for hs in (False, True):
        words, ridx = word_index(raw, hs)
        if not words:
            continue
        printed = norm_printed(raw[ridx[0]:ridx[-1] + 1]) if not hs else " ".join(words)
        for d, ws, pr in (("fwd", words, printed),
                          ("rev", words[::-1], " ".join(printed.split()[::-1]))):
            add(d, "wallet", norm_wallet(ws))
            add(d, "printed", pr)
            if deep:
                add(d, "letters", norm_letters(ws))
        if deep:
            add("mirror", "wallet", norm_wallet(words)[::-1])
            add("mirror", "printed", printed[::-1])
    return out


# ------------------------------------------------------------------ units --
def build_units(text, highlights):
    """[(kind, tag, text, high_prior)]"""
    pages = parse_transcript(text)
    units = []
    page_texts = []
    for pg, paras in pages:
        ptexts = []
        for para in paras:
            ptxt = " ".join(t for _, t in para)
            ptexts.append(ptxt)
            units.append(("para", f"p{pg}:para@L{para[0][0]}", ptxt))
            for ln, t in para:
                units.append(("line", f"p{pg}:L{ln}", t))
            for k, s in enumerate(split_sentences(ptxt)):
                units.append(("sent", f"p{pg}:para@L{para[0][0]}:s{k}", s))
        page_texts.append(" ".join(ptexts))
        units.append(("page", f"p{pg}", page_texts[-1]))
    units.append(("article", "all", " ".join(page_texts)))
    for pg, colour, t in highlights:
        units.append(("hl", f"p{pg}:{colour}", t))
    for k, t in enumerate(NAMED):
        units.append(("named", f"named{k}", t))
    out = []
    for kind, tag, t in units:
        wc = {n_words(t, False), n_words(t, True)}
        high = kind == "named" or bool(wc & set(SEED_LENS))
        out.append((kind, tag, t, high))
    return out, pages


def window_texts(pages, lengths):
    """Contiguous L-word windows over the whole prose stream, both
    tokenisations, fwd + rev, wallet + printed.  Yields (tag, text)."""
    raw = []
    for pg, paras in pages:
        for para in paras:
            for ln, t in para:
                raw += raw_tokens(t)
    seen = set()
    for hs in (False, True):
        words, ridx = word_index(raw, hs)
        for L in lengths:
            for i in range(0, len(words) - L + 1):
                ws = words[i:i + L]
                if hs:
                    pr = " ".join(ws)
                else:
                    pr = norm_printed(raw[ridx[i]:ridx[i + L - 1] + 1])
                for d, w2, p2 in (("fwd", ws, pr), ("rev", ws[::-1], " ".join(pr.split()[::-1]))):
                    for nm, t in (("wallet", norm_wallet(w2)), ("printed", p2)):
                        t = " ".join(t.split())
                        if t and t not in seen:
                            seen.add(t)
                            yield (f"win:L{L}:w{i}:{'hsplit' if hs else 'hjoin'}:{d}:{nm}", t)


# ------------------------------------------------------------------ worker --
SMALL = set()
TARGETS = {}
FULL = None
FULLP = None
USE_FULL = True


def _worker_init():
    global FULL, FULLP
    if USE_FULL and os.path.exists(IO.MAP):
        FULL = IO.Oracle(verbose=False)
        if not FULL.calibrate():
            FULL = None
        else:
            FULLP = FULL.prefix.astype(np.uint64)     # native, one-time per worker


def _lookup_full(rows):
    """rows: [(label, path, typ, addr, privhex)] -> those funded in the 56.8M index."""
    if FULL is None or not rows:
        return []
    spks, keep = [], []
    for r in rows:
        spk = IO.spk_from_address(r[3])
        if spk is not None:
            spks.append(spk)
            keep.append(r)
    hs = [FULL.sh(s) for s in spks]
    keys = np.frombuffer(b"".join(h[:8] for h in hs), dtype=">u8").astype(np.uint64)
    lo = np.searchsorted(FULLP, keys, side="left")
    hi = np.searchsorted(FULLP, keys, side="right")
    out = []
    for j in np.nonzero(hi > lo)[0]:
        j = int(j)
        for i in range(int(lo[j]), int(hi[j])):
            sh, bal = FULL._record(i)
            if sh == hs[j]:
                out.append(keep[j] + (f"full:{bal}",))
                break
    return out


def work(chunk):
    """chunk: [(label, text, scheme, pw, pathset)] -> (n_seeds, n_addrs, hits)"""
    n_seeds = n_addr = 0
    hits, buf = [], []
    for label, text, scheme, pw, pathset in chunk:
        seed = H.bip39_seed(text, pw) if scheme == "bip39" else H.electrum_v2_seed(text, pw)
        rows = H.hd_addrs(seed, {"full": FULL_PATHS, "quick": QUICK_PATHS, "mini": MINI_PATHS}[pathset])
        n_seeds += 1
        lab = f"{scheme}|pw={pw!r}|{label}"
        for p, t, a, priv in rows:
            if a is None:
                continue
            n_addr += 1
            if a in SMALL:
                hits.append((lab, p, t, a, priv.hex(), "richlist"))
            elif a in TARGETS:
                hits.append((lab, p, t, a, priv.hex(), "CTRL-TARGET:" + TARGETS[a]))
            elif FULL is not None:
                buf.append((lab, p, t, a, priv.hex()))
    hits += _lookup_full(buf)
    return n_seeds, n_addr, hits


# ------------------------------------------------------------------ jobs --
def make_jobs(units, pages, lengths, do_units, do_windows, job_filter=None, win_paths="quick"):
    """Yield (label, text, scheme, pw, pathset), deduped on (text, scheme, pw)."""
    seen = set()
    stats = {"unit_texts": 0, "window_texts": 0, "jobs": 0, "units": len(units),
             "high_prior_units": sum(1 for u in units if u[3]), "windows": 0}
    make_jobs.stats = stats

    def emit(label, text, pathset):
        for scheme, pws in (("bip39", PW_BIP39), ("electrum", PW_ELECTRUM)):
            key_text = H.electrum_normalize(text) if scheme == "electrum" else text
            for pw in pws:
                k = hashlib.blake2b(f"{scheme}\x00{pw}\x00{key_text}".encode(), digest_size=16).digest()
                if k in seen:
                    continue
                seen.add(k)
                stats["jobs"] += 1
                yield (label, text, scheme, pw, pathset)

    if do_units:
        for kind, tag, s, high in units:
            for d, nm, t in texts_for_unit(s, deep=True):
                if job_filter and not job_filter(t):
                    continue
                stats["unit_texts"] += 1
                yield from emit(f"{kind}:{tag}:{d}:{nm}:[{t}]", t, "full" if high else "quick")
    if do_windows:
        for tag, t in window_texts(pages, lengths):
            stats["windows"] += 1
            if job_filter and not job_filter(t):
                continue
            stats["window_texts"] += 1
            yield from emit(f"{tag}:[{t}]", t, win_paths)
    make_jobs.stats = stats


def chunks(it, n):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def run_jobs(job_iter, procs, chunk=40, log=None, label=""):
    t0 = time.time()
    tot_seeds = tot_addr = 0
    hits = []
    ctx = get_context("fork")
    with ctx.Pool(procs, initializer=_worker_init) as pool:
        for k, (ns, na, hs) in enumerate(pool.imap_unordered(work, chunks(job_iter, chunk))):
            tot_seeds += ns
            tot_addr += na
            for h in hs:
                hits.append(h)
                msg = "HIT " + "\t".join(str(x) for x in h)
                print(msg, flush=True)
                if log:
                    log.write(msg + "\n"); log.flush()
            if k % 200 == 0 and k:
                msg = f"  [{label}] {tot_seeds:,} seeds  {tot_addr:,} addrs  {time.time()-t0:.0f}s"
                print(msg, flush=True)
                if log:
                    log.write(msg + "\n"); log.flush()
    return tot_seeds, tot_addr, hits, time.time() - t0


# -------------------------------------------------------------- controls --
def _indep_bip39(text, pw):
    return hashlib.pbkdf2_hmac("sha512", unicodedata.normalize("NFKD", text).encode(),
                               b"mnemonic" + unicodedata.normalize("NFKD", pw).encode(), 2048)


def _indep_electrum(text, pw):
    def n(x):
        x = unicodedata.normalize("NFKD", x).lower()
        x = "".join(c for c in x if not unicodedata.combining(c))
        return " ".join(x.split())
    return hashlib.pbkdf2_hmac("sha512", n(text).encode(), b"electrum" + n(pw).encode(), 2048)


def build_control_transcript():
    """Real transcript with four checksum-INVALID plants. Returns (text, targets,
    expectations) where targets maps address -> control name and expectations
    maps control name -> (priv_hex, family_regex)."""
    text = open(TRANSCRIPT, encoding="utf-8").read()
    plants = {}
    # P1: 12-word sentence, all 'abandon' (bip39_valid == False), on its own line.
    s1 = "Abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon."
    assert "Keep your dignity." in text
    text = text.replace("Keep your dignity.", s1, 1)
    w1 = norm_wallet(s1.split())
    assert not H.bip39_valid(w1.split())
    # bip39, pw 'El Salvador', wallet-norm, path present in quick set
    seed = _indep_bip39(w1, "El Salvador")
    priv = hd_derive(seed, "m/84'/0'/0'/0/0")
    plants["P1-bip39-wallet-quickpath"] = (addr_p2wpkh(PrivateKey(priv).public_key.format(True)), priv.hex(), r"^bip39\|pw='El Salvador'\|(sent|line)")
    # same unit, as printed (capital A + period), pw 'Overdose', path only in the FULL set
    seed = _indep_bip39(s1, "Overdose")
    priv = hd_derive(seed, "m/44'/0'/1'/0/2")
    plants["P1-bip39-printed-fullpath"] = (addr_p2pkh(PrivateKey(priv).public_key.format(True)), priv.hex(), r"^bip39\|pw='Overdose'\|(sent|line).*:printed:")
    # same unit, Electrum scheme, pw 'el salvador', m/0/0
    seed = _indep_electrum(w1, "El Salvador")
    priv = hd_derive(seed, "m/0/0")
    plants["P1-electrum-m/0/0"] = (addr_p2pkh(PrivateKey(priv).public_key.format(True)), priv.hex(), r"^electrum\|pw='el salvador'\|(sent|line)")
    # P2: 24-word run buried mid-sentence on p78 (no sentence/line boundary matches it)
    animals = ("zebra yak xray whale vulture unicorn tiger snake rabbit quail panda otter "
               "newt moose lion koala jaguar iguana hippo gecko falcon eagle dingo cat")
    assert len(animals.split()) == 24 and not H.bip39_valid(animals.split())
    old = "and gallons of iced espresso. The numbers don't lie."
    assert old in text
    text = text.replace(old, f"and gallons of {animals} espresso. The numbers don't lie.", 1)
    seed = _indep_bip39(animals, "Bukele")
    priv = hd_derive(seed, "m/49'/0'/0'/0/1")
    plants["P2-window24-bip39"] = (addr_p2sh_p2wpkh(PrivateKey(priv).public_key.format(True)), priv.hex(), r"^bip39\|pw='Bukele'\|win:L24:")
    # P3: 12-word sentence printed in REVERSE order; expected on the forward (un-mirrored) reading
    fwd = "volcano bond lava mining geothermal energy surplus bitcoin treasury nation state sovereign"
    assert not H.bip39_valid(fwd.split())
    s3 = " ".join(fwd.split()[::-1]).capitalize() + "."
    old = "Don't believe me?"
    assert old in text
    text = text.replace(old, s3, 1)
    seed = _indep_bip39(fwd, "20")
    priv = hd_derive(seed, "m/44'/0'/0'/0/0")
    plants["P3-mirror-bip39"] = (addr_p2pkh(PrivateKey(priv).public_key.format(True)), priv.hex(), r"^bip39\|pw='20'\|(sent|line).*:rev:wallet:")
    # P4: 12-word window straddling a printed line break, hyphen-JOINED tokenisation, 'printed' norm, pw ''
    # (uses the real text: the window containing 'honey-badgering')
    targets = {v[0]: k for k, v in plants.items()}
    return text, targets, plants


def run_controls(procs, log):
    ok_all = True

    def report(name, ok, detail=""):
        nonlocal ok_all
        ok_all &= bool(ok)
        msg = f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}"
        print(msg, flush=True)
        if log:
            log.write(msg + "\n"); log.flush()

    vec = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    rows = {(p, t): a for p, t, a, _ in H.hd_addrs(H.bip39_seed(vec, ""), QUICK_PATHS)}
    got = rows.get(("m/44'/0'/0'/0/0", "p2pkh_c"))
    report("C1 BIP-39 vector -> m/44'/0'/0'/0/0 through hd_addrs(quick_paths)",
           got == "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA", got)
    got = H.bip39_seed(vec, "TREZOR").hex()
    exp = ("c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")
    report("C2 bip39_seed(vector,'TREZOR') == BIP-39 spec vector (passphrase concat)", got == exp, got[:32] + "...")
    report("C3a oracle (rich list) sees genesis", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in SMALL)
    fo = IO.Oracle(verbose=False) if os.path.exists(IO.MAP) else None
    cal = bool(fo and fo.calibrate())
    report("C3b full 56.8M index present and calibrated", cal)
    if cal:
        report("C3c full index sees a named exact-20 address via balance()",
               fo.balance("1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t") is not None)
        # and via the vectorised path the workers use
        global FULL, FULLP
        FULL, FULLP = fo, fo.prefix.astype(np.uint64)
        r = _lookup_full([("x", "m", "p2pkh_c", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", ""),
                          ("y", "m", "p2pkh_u", "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T", "")])
        report("C3d worker batch lookup finds genesis and not the swept brainwallet",
               len(r) == 1 and r[0][3].startswith("1A1zP1"), r)
        FULL = FULLP = None

    # C4: planted, checksum-invalid runs through the real pipeline
    text, targets, plants = build_control_transcript()
    global TARGETS
    TARGETS = dict(targets)
    units, pages = build_units(text, load_highlights())
    markers = ("abandon", "zebra", "volcano")
    flt = lambda t: any(m in t.lower() for m in markers)
    jobs = make_jobs(units, pages, (12, 24), True, True, job_filter=flt)
    ns, na, hits, dt = run_jobs(jobs, procs, log=log, label="ctrl")
    st = make_jobs.stats
    report(f"C4 pipeline ran on synthetic transcript ({st['unit_texts']} unit texts, {st['window_texts']} window texts, {ns} seeds, {na:,} addrs, {dt:.0f}s)", ns > 0)
    for name, (addr, privhex, fam) in plants.items():
        got = [h for h in hits if h[3] == addr]
        okp = any(h[4] == privhex and re.search(fam, h[0]) for h in got)
        report(f"C4 {name} -> {addr} fires at expected family with matching priv",
               okp, (got[0][0][:90] + " " + got[0][1]) if got else "MISSED")
    stray = [h for h in hits if not h[5].startswith("CTRL-TARGET")]
    report("C4 no non-control hits on the synthetic transcript (specificity)", not stray, len(stray))
    TARGETS = {}
    return ok_all


# ------------------------------------------------------------------ main --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lengths", default="12,24")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--skip-controls", action="store_true")
    ap.add_argument("--windows-only", action="store_true")
    ap.add_argument("--units-only", action="store_true")
    ap.add_argument("--no-full", action="store_true", help="rich list only (no 56.8M index)")
    ap.add_argument("--paths", default="quick", choices=["quick", "mini"],
                    help="path set for WINDOW jobs (units always get quick, high-prior units full)")
    ap.add_argument("--log", default=os.path.join(HERE, "salvador_seed.log"))
    a = ap.parse_args()
    global SMALL, USE_FULL
    USE_FULL = not a.no_full
    lengths = tuple(int(x) for x in a.lengths.split(","))
    log = open(a.log, "a")
    log.write(f"\n===== run {time.strftime('%Y-%m-%d %H:%M:%S')} lengths={lengths} args={vars(a)} =====\n")

    O = H.Oracle(use_full=False)
    SMALL = O.addrs
    print(f"rich-list oracle: {len(SMALL):,} addresses; quick paths {len(QUICK_PATHS)}, full paths {len(FULL_PATHS)}, mini paths {len(MINI_PATHS)}; "
          f"bip39 pws {len(PW_BIP39)}, electrum pws {len(PW_ELECTRUM)}", flush=True)

    if not a.skip_controls:
        print("=== CONTROLS ===", flush=True)
        ok = run_controls(a.procs, log)
        msg = "CONTROLS " + ("ALL PASS" if ok else "SOME FAILED")
        print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if not ok:
            sys.exit("controls failed; the null would be meaningless -- aborting")
        if a.controls_only:
            return

    print("=== SWEEP ===", flush=True)
    text = open(TRANSCRIPT, encoding="utf-8").read()
    units, pages = build_units(text, load_highlights())
    kinds = {}
    for k, tag, t, high in units:
        kinds.setdefault(k, [0, 0])
        kinds[k][0] += 1
        kinds[k][1] += high
    msg = "units by kind (total, high-prior): " + ", ".join(f"{k}={v[0]}/{v[1]}" for k, v in kinds.items())
    print(msg, flush=True); log.write(msg + "\n")
    for k, tag, t, high in units:
        if high:
            msg = f"  high-prior {k} {tag} [{n_words(t)}w] {t}"
            print(msg, flush=True); log.write(msg + "\n")
    jobs = make_jobs(units, pages, lengths, not a.windows_only, not a.units_only, win_paths=a.paths)
    ns, na, hits, dt = run_jobs(jobs, a.procs, log=log, label="sweep")
    st = make_jobs.stats
    msg = (f"SWEEP DONE lengths={lengths} window_paths={a.paths}: units={st['units']} (high-prior {st['high_prior_units']}), "
           f"unit texts={st['unit_texts']:,}, windows={st['windows']:,} window texts={st['window_texts']:,}, "
           f"jobs={st['jobs']:,}, seeds derived={ns:,}, addresses checked={na:,}, hits={len(hits)}, {dt:.0f}s")
    print(msg, flush=True); log.write(msg + "\n")
    with open(os.path.join(HERE, "salvador_seed_hits.tsv"), "a") as f:
        for h in hits:
            f.write("\t".join(str(x) for x in h) + "\n")
    log.close()


if __name__ == "__main__":
    main()
