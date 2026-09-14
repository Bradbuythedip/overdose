#!/usr/bin/env python3
"""
Seed-phrase windows over the article, with self-validating oracles first.

Families (none previously run in this form):
  A. Electrum v2 seeds: ANY word sequence whose HMAC-SHA512("Seed version")
     starts with 01 (standard) / 100 (segwit). Every contiguous window of
     3..24 words of the prose, as printed, lower-cased. Then m/0/i, m/1/0,
     m/0'/0/i addresses -> oracle. Also with passphrases.
  B. BIP-39: the in-order sequence of BIP-39 words in the prose (skipping
     non-list words), windows of 12/15/18/21/24 with a valid checksum, with
     13 passphrases (El Salvador variants etc.), quick paths -> oracle.
  C. Old Electrum (1626-word list): in-order sequence of old-list words,
     windows of 12 -> stretched key -> first 5 receive + 2 change addresses.
  D. Same as B/C over the highlighted/bold phrase catalogue and over each page.

Controls: a known Electrum seed and BIP-39 vector are injected and must be
detected by the same code path (printed at the end).
"""
import os, re, sys, itertools, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
txt = open(os.path.join(ROOT, "solver", "article_transcript.txt")).read()
body = txt.split("=== PAGE 75")[1]
pages = {}
for m in re.finditer(r"=== PAGE (\d+) \(IMG_\d+\) ===\n(.*?)(?==== PAGE|\Z)", txt, re.S):
    pages[int(m.group(1))] = m.group(2)

def words_of(s):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", s)]

def norm(w):
    return re.sub(r"[^a-z]", "", w.lower())

PASSPHRASES = ["", "El Salvador", "ElSalvador", "el salvador", "elsalvador", "EL SALVADOR",
               "Overdose", "OVERDOSE", "overdose", "Bitcoin Is Toxic AF", "Max Keiser", "maxkeiser",
               "Stacy", "20", "Bitcoin", "bitcoin", "mirror", "George Sand"]

# Rich list in memory; the full 56.8M index is consulted in ONE vectorized
# pass per batch instead of a disk seek per address. The per-address form made
# stage A take 34,011s against 12s for the same stage on the rich list alone.
O = H.Oracle(use_full=False)
hits = []
stats = {}
_pending = []          # (tag, path, script_type, addr, priv)
_checked = [0]
BATCH = 50000


def _flush(force=False):
    if not _pending or (len(_pending) < BATCH and not force):
        return
    full = H.full_index()
    if full is None:
        _pending.clear()
        return
    from index_oracle import spk_from_address
    spks, meta = [], []
    for row in _pending:
        spk = spk_from_address(row[3])
        if spk is not None:
            spks.append(spk)
            meta.append(row)
    for j, bal in full.contains_spks(spks):
        tag, p, t, a, priv = meta[j]
        hits.append((tag, p, t, a, priv.hex(), bal))
        print(f"HIT(fullindex) {tag} {p} {t} {a} {priv.hex()} {bal/1e8:.8f} BTC", flush=True)
    _checked[0] += len(spks)
    _pending.clear()


def check_addrs(tag, addr_rows):
    for p, t, a, priv in addr_rows:
        if O.funded(a):        # in-memory April-2023 rich list
            hits.append((tag, p, t, a, priv.hex()))
            print("HIT(richlist)", tag, p, t, a, priv.hex(), flush=True)
        _pending.append((tag, p, t, a, priv))
    _flush()

# ---------- A. Electrum v2 over all contiguous windows ----------
t0 = time.time()
allw = words_of(body)
lw = [norm(w) for w in allw]
lw = [w for w in lw if w]
nA = nAv = 0
seen = set()
for L in range(3, 25):
    for i in range(0, len(lw) - L + 1):
        phrase = " ".join(lw[i:i + L])
        if phrase in seen:
            continue
        seen.add(phrase)
        nA += 1
        kind = H.electrum_v2_type(phrase)
        if kind:
            nAv += 1
            check_addrs(f"electrum_v2:{kind}:{phrase}", H.electrum_v2_addrs(phrase, "", 5))
            for pw in PASSPHRASES[1:]:
                check_addrs(f"electrum_v2:{kind}:{phrase}|pw={pw}", H.electrum_v2_addrs(phrase, pw, 3))
stats["A_windows"] = nA; stats["A_version_valid"] = nAv
print(f"A: {nA} windows, {nAv} pass Electrum seed-version, {time.time()-t0:.0f}s", flush=True)

# ---------- B. BIP-39 in-order sequence windows ----------
t0 = time.time()
def bip39_family(tag, seq):
    n = nv = 0
    for L in (12, 15, 18, 21, 24):
        for i in range(0, len(seq) - L + 1):
            ws = seq[i:i + L]
            n += 1
            if H.bip39_valid(ws):
                nv += 1
                m = " ".join(ws)
                for pw in PASSPHRASES:
                    check_addrs(f"bip39:{tag}:{m}|pw={pw}", H.bip39_addrs(m, pw))
    return n, nv

bseq = [w for w in lw if w in H.BIP39_SET]
n, nv = bip39_family("prose_inorder", bseq)
stats["B_prose_windows"] = n; stats["B_prose_valid"] = nv
# per page
for pg, sec in pages.items():
    s = [norm(w) for w in words_of(sec)]
    s = [w for w in s if w in H.BIP39_SET]
    n2, nv2 = bip39_family(f"page{pg}", s)
    n += n2; nv += nv2
# reversed order (mirror)
n3, nv3 = bip39_family("prose_reversed", bseq[::-1])
stats["B_total_windows"] = n + n3; stats["B_total_valid"] = nv + nv3
print(f"B: {n+n3} windows, {nv+nv3} checksum-valid, {time.time()-t0:.0f}s", flush=True)

# ---------- C. Old Electrum in-order windows ----------
t0 = time.time()
oseq = [w for w in lw if w in H.ELECTRUM_OLD_SET]
nC = 0
for seqname, seq in (("prose", oseq), ("reversed", oseq[::-1])):
    for i in range(0, len(seq) - 12 + 1):
        ws = seq[i:i + 12]
        nC += 1
        check_addrs(f"electrum_old:{seqname}:{' '.join(ws)}", H.electrum_old_addrs(ws, 5))
        check_addrs(f"electrum_old:{seqname}:{' '.join(ws)}", H.electrum_old_addrs(ws, 2, change=True))
stats["C_windows"] = nC
print(f"C: {nC} old-Electrum windows, {time.time()-t0:.0f}s", flush=True)

# ---------- D. highlight catalogue ----------
t0 = time.time()
hl = []
for line in open(os.path.join(ROOT, "solver", "highlights_ordered.tsv")):
    if line.startswith("#") or not line.strip():
        continue
    parts = line.rstrip("\n").split("\t")
    if len(parts) >= 3:
        hl.append(parts[2])
hw = [norm(w) for r in hl for w in words_of(r)]
hw = [w for w in hw if w]
nD = nDv = 0
for L in range(3, 25):
    for i in range(0, len(hw) - L + 1):
        phrase = " ".join(hw[i:i + L])
        nD += 1
        kind = H.electrum_v2_type(phrase)
        if kind:
            nDv += 1
            check_addrs(f"electrum_v2:hl:{kind}:{phrase}", H.electrum_v2_addrs(phrase, "", 5))
hb = [w for w in hw if w in H.BIP39_SET]
n4, nv4 = bip39_family("highlights", hb)
ho = [w for w in hw if w in H.ELECTRUM_OLD_SET]
for i in range(0, len(ho) - 12 + 1):
    check_addrs(f"electrum_old:hl:{' '.join(ho[i:i+12])}", H.electrum_old_addrs(ho[i:i + 12], 3))
stats["D_hl_electrum_windows"] = nD; stats["D_hl_electrum_valid"] = nDv
stats["D_hl_bip39_windows"] = n4; stats["D_hl_bip39_valid"] = nv4
print(f"D: highlights: {nD} electrum windows ({nDv} valid), {n4} bip39 windows ({nv4} valid), {time.time()-t0:.0f}s", flush=True)

# ---------- controls ----------
ctrl = []
m = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
ctrl.append(("bip39 vector detected by bip39_valid", H.bip39_valid(m.split())))
ctrl.append(("bip39 vector bip44 addr", dict(((p, t), a) for p, t, a, _ in H.bip39_addrs(m, "", ["m/44'/0'/0'/0/0"]))[("m/44'/0'/0'/0/0", "p2pkh_c")] == "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"))
ctrl.append(("electrum v2 vector type", H.electrum_v2_type("cycle rocket west magnet parrot shuffle foot correct salt library feed song") == "standard"))
ctrl.append(("old electrum vector addr", H.electrum_old_addrs("powerful random nobody notice nothing important anyway look away hidden message over".split(), 1)[0][2] == "1FJEEB8ihPMbzs2SkLmr37dHyRFzakqUmo"))
ctrl.append(("oracle sees genesis", O.funded("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")))
_flush(force=True)
print(f"full-index scriptPubKeys checked: {_checked[0]:,}")
print("CONTROLS:", ctrl)
print("STATS:", stats)
print("HITS:", len(hits))
for h in hits:
    print("  ", h)
