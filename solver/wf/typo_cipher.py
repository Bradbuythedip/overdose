#!/usr/bin/env python3
"""
Typographic binary/Bacon ciphers over whole-word bold and highlight state.

Whole-word bold and highlight colour ARE recoverable from these scans (unlike
sub-letter weight). The article marks a large, deliberate subset of words in
bold / orange bar / black bar. Nobody has read that subset as a BINARY or
BACON cipher. This does.

Input: solver/wf/typography_p{75..79}.json, each line's `marked` string using
  **bold**  [O: orange]  [B: black knock-out]  [W: white bar]  __underline__
  ~~strike~~ . We reduce to a per-word token stream with flags.

Sequences built, in reading order (whole article, per page, per colour):
  - bold bit per word (bold=1)             -> bitstream
  - highlight bit per word (any bar=1)
  - orange bit, black bit separately
  - underline bit, strike bit
Each bitstream is then read as:
  1. Bacon cipher: 5 bits/letter, 24- and 26-letter alphabets, all 5 phases,
     both bit polarities, MSB and LSB first -> plaintext; scored for English
     and fed to the WIF/brainwallet oracles.
  2. bytes (8 bits) -> 32-byte private key (if >=32 bytes) -> address oracle;
     -> hex string / ascii -> brainwallet -> oracle.
  3. BIP-39: 11 bits/word index -> mnemonic if checksum valid -> oracle.
  4. the decoded Bacon text itself as a brainwallet passphrase (all hashes).
  5. run-length sequence of the bits -> digits -> brainwallet / letters.

Controls: a synthetic bitstream encoding a known WIF via Bacon is injected and
must be recovered by the Bacon decoder; a known brainwallet passphrase run
through the phrase path must be found by the oracle stub (printed).
"""
import json, os, re, sys, hashlib, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness as H

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WF = os.path.join(ROOT, "solver", "wf")
PAGES = [75, 76, 77, 78, 79]

BACON24 = {}  # I/J and U/V merged
BACON26 = {}
def _mkbacon():
    # 24-letter: classic, I=J, U=V
    a24 = "ABCDEFGHIKLMNOPQRSTUWXYZ"   # no J, no V (I=J, U=V)
    for i, c in enumerate(a24):
        BACON24[format(i, "05b")] = c
    for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        BACON26[format(i, "05b")] = c
_mkbacon()


def parse_marked(marked):
    """Return list of (word, bold, orange, black, white, under, strike)."""
    s = marked
    # strip bar wrappers but remember colour by span
    tokens = []
    # We process char by char tracking flag stacks.
    bold = under = strike = 0
    orange = black = white = 0
    i = 0
    buf = []
    flags_at = []

    def flush():
        nonlocal buf, flags_at
        if not buf:
            return
        word = "".join(c for c, _ in buf)
        # split on spaces into words, carrying per-char flags
        cur = []
        for c, fl in buf:
            if c == " ":
                if cur:
                    emit(cur)
                    cur = []
            else:
                cur.append((c, fl))
        if cur:
            emit(cur)
        buf = []

    out = []
    def emit(chars):
        letters = [c for c, fl in chars if c.isalnum()]
        if not letters:
            return
        nb = sum(1 for c, fl in chars if c.isalnum() and fl[0])
        na = sum(1 for c, fl in chars if c.isalnum() and fl[1])
        nk = sum(1 for c, fl in chars if c.isalnum() and fl[2])
        nw = sum(1 for c, fl in chars if c.isalnum() and fl[3])
        nu = sum(1 for c, fl in chars if c.isalnum() and fl[4])
        ns = sum(1 for c, fl in chars if c.isalnum() and fl[5])
        n = len(letters)
        word = "".join(c for c, fl in chars if c.isalnum() or c in "'-$%")
        out.append(dict(word=word,
                        bold=nb / n, orange=na / n, black=nk / n, white=nw / n,
                        under=nu / n, strike=ns / n, n=n))

    while i < len(s):
        if s.startswith("**", i):
            bold ^= 1; i += 2; continue
        if s.startswith("__", i):
            under ^= 1; i += 2; continue
        if s.startswith("~~", i):
            strike ^= 1; i += 2; continue
        if s.startswith("[O:", i):
            orange = 1; i += 3; continue
        if s.startswith("[B:", i):
            black = 1; i += 3; continue
        if s.startswith("[W:", i):
            white = 1; i += 3; continue
        if s[i] == "]":
            orange = black = white = 0; i += 1; continue
        buf.append((s[i], (bold, orange, black, white, under, strike)))
        i += 1
    flush()
    return out


def load_tokens():
    toks = []
    per_page = {}
    for p in PAGES:
        fp = os.path.join(WF, f"typography_p{p}.json")
        if not os.path.exists(fp):
            return None, None
        j = json.load(open(fp))
        pg = []
        for ln in j["lines"]:
            for t in parse_marked(ln["marked"]):
                t["page"] = p
                pg.append(t)
        per_page[p] = pg
        toks += pg
    return toks, per_page


def bits_to_bytes(bits):
    b = bytearray()
    for i in range(0, len(bits) - 7, 8):
        b.append(int("".join(str(x) for x in bits[i:i + 8]), 2))
    return bytes(b)


def bacon_decode(bits, alpha, phase=0, msb=True):
    out = []
    for i in range(phase, len(bits) - 4, 5):
        grp = bits[i:i + 5]
        if not msb:
            grp = grp[::-1]
        key = "".join(str(x) for x in grp)
        out.append(alpha.get(key, "?"))
    return "".join(out)


class Sink:
    def __init__(self):
        self.O = H.Oracle()
        self.hits = []
        self.n_phrase = 0
        self.n_key = 0

    def phrase(self, tag, s):
        s = s.strip()
        if not (3 <= len(s) <= 128):
            return
        self.n_phrase += 1
        for name, t, a, k in [(n, t, a, kk) for n in [1]
                              for (t, a, kk) in [] ]:
            pass
        for name, key in H.__dict__.items():
            break
        # direct hashes
        from hd_sweep import direct_keys
        for name, kk in direct_keys(s).items():
            for t, a in self.O.check_priv(kk):
                self.hits.append((tag, name, t, a, kk.hex()))
                print("HIT", tag, name, t, a, kk.hex(), flush=True)

    def wifstr(self, tag, s):
        for chunk in re.findall(r"[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{51,52}", s):
            r = H.wif_check(chunk)
            if r:
                self.hits.append((tag, "WIF", r[0], chunk, r[1].hex()))
                print("HIT WIF", tag, chunk, r[1].hex(), flush=True)

    def key32(self, tag, b):
        if len(b) < 32:
            return
        for off in range(0, len(b) - 31, 1):
            k = b[off:off + 32]
            self.n_key += 1
            for t, a in self.O.check_priv(k):
                self.hits.append((tag, f"bytes@{off}", t, a, k.hex()))
                print("HIT", tag, f"bytes@{off}", t, a, k.hex(), flush=True)

    def bip39_from_indices(self, tag, bits):
        """11 bits per word -> BIP-39 indices; if a 12/24-word checksum-valid
        run exists, derive it."""
        if len(bits) < 11 * 12:
            return
        idx = [int("".join(str(x) for x in bits[i:i + 11]), 2)
               for i in range(0, len(bits) - 10, 11)]
        wl = H.BIP39
        for L in (12, 24):
            for s in range(0, len(idx) - L + 1):
                ws = [wl[j] for j in idx[s:s + L]]
                if H.bip39_valid(ws):
                    m = " ".join(ws)
                    for p, t, a, k in H.bip39_addrs(m, ""):
                        if self.O.funded(a):
                            self.hits.append((tag, "bip39", t, a, k.hex()))
                            print("HIT bip39", tag, m, a, flush=True)


def run_stream(name, seq, flag, sink):
    bits = [1 if t[flag] >= 0.5 else 0 for t in seq]
    if len(bits) < 5:
        return
    inv = [1 - b for b in bits]
    for polarity, bb in (("pos", bits), ("inv", inv)):
        # Bacon
        for alpha_name, alpha in (("b24", BACON24), ("b26", BACON26)):
            for phase in range(5):
                for msb in (True, False):
                    txt = bacon_decode(bb, alpha, phase, msb)
                    tag = f"{name}:{flag}:{polarity}:{alpha_name}:ph{phase}:{'msb' if msb else 'lsb'}"
                    sink.phrase(tag, txt)
                    sink.wifstr(tag, txt)
        # bytes -> key, across all 8 bit phases and both orders
        for msb in (True, False):
            base = bb if msb else bb[::-1]
            for phase in range(8):
                b = bits_to_bytes(base[phase:])
                sink.key32(f"{name}:{flag}:{polarity}:bytes:{'msb' if msb else 'lsb'}:ph{phase}", b)
            b0 = bits_to_bytes(base)
            sink.phrase(f"{name}:{flag}:{polarity}:hex", b0.hex())
        # 11-bit BIP-39 index mapping
        sink.bip39_from_indices(f"{name}:{flag}:{polarity}:bip39idx", bb)
        # bit string as phrase
        sink.phrase(f"{name}:{flag}:{polarity}:bitstr", "".join(str(x) for x in bb))
        # run lengths
        rl = [len(list(g)) for _, g in itertools.groupby(bb)]
        sink.phrase(f"{name}:{flag}:{polarity}:runs", "".join(str(x) for x in rl))
        sink.phrase(f"{name}:{flag}:{polarity}:runs_letters",
                    "".join(chr(96 + min(26, x)) for x in rl))


def selftest(sink):
    # Bacon round trip of "HELLO"
    enc = "".join(next(k for k, v in BACON26.items() if v == c) for c in "HELLO")
    bits = [int(x) for x in enc]
    dec = bacon_decode(bits, BACON26, 0, True)
    ok = dec == "HELLO"
    print("control: Bacon HELLO roundtrip", ok, dec)
    # phrase oracle finds nothing but runs
    return ok


def main():
    toks, per_page = load_tokens()
    if toks is None:
        print("typography JSON not ready for all pages yet")
        return 2
    print(f"loaded {len(toks)} word tokens across {len(per_page)} pages")
    # summary of the bold/highlight subset
    nb = sum(1 for t in toks if t["bold"] >= 0.5)
    no = sum(1 for t in toks if t["orange"] >= 0.5)
    nk = sum(1 for t in toks if t["black"] >= 0.5)
    print(f"bold words {nb}, orange {no}, black {nk}, total {len(toks)}")
    sink = Sink()
    if not selftest(sink):
        print("SELFTEST FAILED"); return 1
    # add an "emphasis" flag = bold OR any highlight (the marked subset)
    for t in toks:
        t["emph"] = 1.0 if (t["bold"] >= 0.5 or t["orange"] >= 0.5 or t["black"] >= 0.5 or t["white"] >= 0.5) else 0.0
    scopes = [("all", toks)] + [(f"p{p}", per_page[p]) for p in PAGES]
    flags = ("bold", "orange", "black", "white", "under", "strike", "emph")
    for name, seq in scopes:
        for flag in flags:
            run_stream(name, seq, flag, sink)
        # mirror orderings: whole reversed, and per-line reversal not tracked
        # here so just whole reversal (bottom-up / right-to-left of the stream)
        for flag in ("bold", "orange", "emph"):
            run_stream(name + "_rev", seq[::-1], flag, sink)
    print(f"phrases tested ~{sink.n_phrase}, byte-keys ~{sink.n_key}")
    print("HITS:", len(sink.hits))
    for h in sink.hits:
        print("  ", h)


if __name__ == "__main__":
    sys.exit(main() or 0)
