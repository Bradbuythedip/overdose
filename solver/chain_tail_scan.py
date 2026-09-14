#!/usr/bin/env python3
"""
The 136,917 blocks nobody scanned, and the question they can actually answer.

THE GAP
window/onchain_marker_scan.md and STATUS.md both record the on-chain marker
scan as covering "blocks 0-829,999". That was never a decision — it is exactly
where the data source stops. cirosantilli/bitcoin-inscription-indexer serves
data/out/0000.txt through 0829.txt and nothing after; 0830.txt is a 404,
confirmed by binary search. Meanwhile the chain is at 966,916.

    scanned      0 .. 829,999
    UNSCANNED    830,000 .. tip        136,917 blocks, roughly Feb 2024 to now

Nobody noticed the chain had moved on. And that window is not arbitrary: the
announcement was March 2023 (~block 780,000), so the scanned range covers only
the first year after it. If somebody solved this puzzle and swept the prize,
the most likely time is inside the unscanned part.

TWO THINGS THIS LOOKS FOR

  1. TEXT. ASCII runs embedded in any script — outputs, inputs, witnesses —
     matching the puzzle's vocabulary. A solver boasting, Keiser marking the
     wallet, anyone naming the serial.

  2. A FULL OUTPUT — the one that matters. Any output paying exactly
     20.00000000 BTC, or within 19.9-20.1. The prize, if it exists and is
     unspent, is an address HOLDING that, and Tnew_exact_20.tsv is a SNAPSHOT:
     anything funded after it was taken is simply absent from every list this
     project has. Each hit is marked known or NEW against those 795.

  3. A SPEND of one of the 795. window/Tnew_exact_20.tsv holds 795
     scripthashes that each held exactly 20.00000000 BTC. A raw block does not
     say what an input spent, so a scripthash cannot be matched directly — but
     a standard spend REVEALS ITS PUBKEY in the scriptSig or witness. From the
     pubkey this reconstructs every script form, hashes each, and checks the
     795. If one of those addresses was emptied in this window, that is a
     direct observation of the swept-key hypothesis rather than an inference
     about it, and swept_key_untested.md says that hypothesis is still open.

This needs an endpoint that serves getblockhash/getblock. It cannot run in the
container it was written in — the network policy answers 403 for the Alchemy
host — so the parsing and detection logic is tested offline against synthetic
blocks instead, and the live run belongs on a machine with access.

  python3 chain_tail_scan.py --selftest
  python3 chain_tail_scan.py --rpc "$B" --start 830000
"""
import argparse, hashlib, json, os, re, sys, time

ASCII_RUN = re.compile(rb"[\x20-\x7e]{16,}")

# Keywords tiered by how often they occur for reasons unrelated to this puzzle.
# The first live run matched "overdose" in block 830,200 — an Atomicals realm
# registration, CBOR {"bitworkc":"3165","request_realm":"overdose"}, somebody
# claiming the NAME. One hit per 200 blocks extrapolates to ~685 across the
# window, which would bury anything real. "overdose" is an ordinary English
# word and a desirable short name; so are most of the others.
SPECIFIC = [                      # effectively zero false-positive rate
    "cl76841714a", "76841714", "41714867", "annabellebaz",
    "orangepill", "honey badger", "honeybadger", "toxic af",
    "bitcoin is toxic", "george sand", "max keiser", "stacy herbert",
]
GENERIC = [                       # real words; need corroboration
    "keiser", "overdose", "orange pill", "el salvador", "elsalvador",
    "bukele", "20 btc", "20btc", "bitcoin magazine", "satoshi experience",
]
KEYWORDS = SPECIFIC + GENERIC     # kept for the selftest and --all

# Protocol envelopes that mint names and text for their own reasons. A generic
# keyword appearing inside one of these is a name, not a message.
# Deliberately NOT "ord" — it is a substring of word, record, according, order,
# and would suppress ordinary English containing a real message. Suppression has
# to be narrower than detection or the filter becomes the bug.
PROTOCOL_NOISE = ["request_realm", "bitworkc", "request_subrealm", "atomicals",
                  "request_container", "request_dmitem", "text/plain;charset",
                  "application/json", "brc-20", '"op":"', '"tick":',
                  "ord\x01", "mint_ticker"]


# A third class, discovered by a "false positive". Block 830,776 carries
# "Bitcoin Magazine The Inscription Issue" — the publisher inscribing a whole
# issue onto Bitcoin as an Ordinal. That is not a puzzle hit, but it matters:
# if issue 24, the El Salvador issue, was ever inscribed, then the canonical
# digital text of the Overdose column is ON CHAIN. That would replace
# article_transcript.txt, a human transcription, with the publisher's own
# bytes — and would retire the transcription-error hypothesis outright instead
# of merely bounding it the way edit1 does.
PUBLISHER = ["bitcoin magazine", "bitcoinmagazine", "btc media", "btcmedia"]
ISSUE_HINTS = ["el salvador", "issue 24", "issue24", "overdose",
               "inscription issue", "the el salvador issue", "volume", "vol."]


# THE ONE THAT MATTERS. The prize, if it exists and is unspent, is an address
# HOLDING 20 BTC — not one that was emptied. window/Tnew_exact_20.tsv already
# lists 795 such addresses, but it is a SNAPSHOT: an address funded after it was
# taken is simply absent. 136,917 unscanned blocks is exactly where a
# newly-funded 20 BTC output would be sitting, unseen by every list this project
# has ever built.
#
# The first version of this scanner read each output's value and discarded it,
# then hunted for SPENDS of the old snapshot. It walked past the answer to look
# for evidence the answer was gone.
PRIZE_SATS = 2_000_000_000                 # 20.00000000 BTC
BAND_LO, BAND_HI = 1_990_000_000, 2_010_000_000    # 19.9 .. 20.1


def classify_value(value):
    """(report?, tag) for an output's value. Exact first, near-miss second."""
    if value == PRIZE_SATS:
        return True, "EXACT_20"
    if BAND_LO <= value <= BAND_HI:
        return True, "NEAR_20"
    return False, ""


def classify_publisher(text):
    """(report?, matched) for a Bitcoin Magazine artifact worth collecting."""
    s = text.lower()
    pub = [w for w in PUBLISHER if w in s]
    if not pub:
        return False, []
    hints = [w for w in ISSUE_HINTS if w in s]
    return True, pub + hints


def classify(text):
    """(report?, matched, reason) for one embedded ASCII run.

    A specific term stands alone. A generic one has to be corroborated — by a
    specific term, or by another generic term — and is discarded outright if it
    sits inside a naming-protocol envelope, because there it is a claimed name
    rather than a sentence.
    """
    s = text.lower()
    spec = [w for w in SPECIFIC if w in s]
    gen = [w for w in GENERIC if w in s]
    if spec:
        return True, spec + gen, "specific"
    if not gen:
        return False, [], ""
    noise = [p for p in PROTOCOL_NOISE if p in s]
    if noise:
        return False, gen, f"protocol envelope ({noise[0]})"
    if len(gen) >= 2:
        return True, gen, "two generic terms"
    return False, gen, "single generic term, uncorroborated"


class Sink:
    """Writes each finding to TSV and/or JSON Lines.

    JSON LINES, not one JSON array. This scan runs for hours over 136,917
    blocks and is resumable; an array would have to be closed at the end, so a
    Ctrl-C or a dropped endpoint would leave a truncated file that no parser
    accepts. One complete object per line survives interruption, appends on
    resume, and collapses to an array with `jq -s .` whenever you want one.
    """

    def __init__(self, tsv=None, jsonl=None):
        self.t = open(tsv, "a", encoding="utf-8") if tsv else None
        self.j = open(jsonl, "a", encoding="utf-8") if jsonl else None

    def write(self, rec, tsv_cols):
        if self.t:
            self.t.write("\t".join(str(c) for c in tsv_cols) + "\n")
            self.t.flush()
        if self.j:
            self.j.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.j.flush()

    def close(self):
        for f in (self.t, self.j):
            if f:
                f.close()


def tsv_to_json(tsv_path, json_path):
    """Convert a TSV already collected by an earlier run. Nothing is lost."""
    cols = {
        "FULL": ["type", "block", "tag", "value", "scripthash", "spk", "known"],
        "TEXT": ["type", "block", "kind", "why", "matched", "text"],
        "PUBLISHER": ["type", "block", "kind", "matched", "text"],
        "SWEEP": ["type", "block", "scripthash", "pubkey"],
    }
    n = 0
    with open(json_path, "w", encoding="utf-8") as out:
        for line in open(tsv_path, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            names = cols.get(p[0])
            if not names:
                continue
            rec = dict(zip(names, p))
            if "block" in rec:
                rec["block"] = int(rec["block"])
            if "value" in rec:
                rec["value"] = int(rec["value"])
                rec["btc"] = rec["value"] / 1e8
            if "matched" in rec:
                rec["matched"] = rec["matched"].split(",")
            if "known" in rec:
                rec["known"] = rec["known"] == "known"
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def dsha(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def h160(b):
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


def load_targets(path="window/Tnew_exact_20.tsv"):
    """The scripthashes that each held exactly 20 BTC."""
    if not os.path.exists(path):
        return set()
    out = set()
    for line in open(path):
        p = line.split("\t")
        if p and len(p[0]) == 64 and not p[0].startswith("scripthash"):
            out.add(p[0].strip().lower())
    return out


def pubkeys_in(script_sig, witness):
    """Every plausible pubkey revealed by a standard spend.

    A raw block never states what an input spent. But p2pkh puts the pubkey in
    the scriptSig, and p2wpkh / p2sh-p2wpkh put it at the top of the witness,
    so a standard spend hands over the one thing needed to rebuild the script
    it was spending from.
    """
    out = []
    for item in list(witness) + _pushes(script_sig):
        if len(item) in (33, 65) and item[:1] in (b"\x02", b"\x03", b"\x04"):
            out.append(item)
    return out


def _pushes(script):
    """Data pushes in a script, best effort — malformed input yields nothing."""
    out, i = [], 0
    try:
        while i < len(script):
            op = script[i]
            i += 1
            if op < 0x4C:
                out.append(script[i:i + op])
                i += op
            elif op == 0x4C:
                n = script[i]; i += 1
                out.append(script[i:i + n]); i += n
            elif op == 0x4D:
                n = int.from_bytes(script[i:i + 2], "little"); i += 2
                out.append(script[i:i + n]); i += n
            else:
                break
    except Exception:
        pass
    return out


def scripthashes_for_pubkey(pub):
    """Every standard script this pubkey could have been locked behind."""
    hp = h160(pub)
    forms = [b"\x76\xa9\x14" + hp + b"\x88\xac"]          # p2pkh
    if len(pub) == 33:
        wp = b"\x00\x14" + hp
        forms.append(wp)                                   # p2wpkh
        forms.append(b"\xa9\x14" + h160(wp) + b"\x87")     # p2sh-p2wpkh
    forms.append(bytes([len(pub)]) + pub + b"\xac")        # p2pk
    return {hashlib.sha256(f).hexdigest() for f in forms}


class Reader:
    def __init__(self, b):
        self.b, self.i = b, 0

    def take(self, n):
        v = self.b[self.i:self.i + n]
        if len(v) != n:
            raise ValueError("truncated")
        self.i += n
        return v

    def u32(self):
        return int.from_bytes(self.take(4), "little")

    def u64(self):
        return int.from_bytes(self.take(8), "little")

    def varint(self):
        n = self.take(1)[0]
        if n < 0xFD:
            return n
        return int.from_bytes(self.take({0xFD: 2, 0xFE: 4}.get(n, 8)), "little")


def scan_block(raw):
    """Yield (kind, payload) for every script and witness item in a block.

    kind is 'in', 'out' or 'wit' so a hit can be attributed to where it lived.
    """
    r = Reader(raw)
    r.take(80)
    for _ in range(r.varint()):
        r.u32()
        segwit = False
        n_in = r.varint()
        if n_in == 0:
            r.take(1)
            segwit = True
            n_in = r.varint()
        ins = []
        for _j in range(n_in):
            r.take(32); r.u32()
            ss = r.take(r.varint())
            r.u32()
            ins.append(ss)
            yield "in", ss
        for _j in range(r.varint()):
            value = r.u64()
            spk = r.take(r.varint())
            yield "out", (value, spk)
        wits = [[] for _ in ins]
        if segwit:
            for j in range(n_in):
                wits[j] = [r.take(r.varint()) for _ in range(r.varint())]
                for w in wits[j]:
                    yield "wit", w
        r.u32()
        for ss, w in zip(ins, wits):
            yield "spend", (ss, w)


def selftest():
    """Detection logic, proven offline against a block we build ourselves."""
    ok = True

    # a pubkey spend must be recognised and must reconstruct its own scripthash
    from coincurve import PrivateKey
    k = hashlib.sha256(b"tail scan selftest").digest()
    pub = PrivateKey(k).public_key.format(True)
    shs = scripthashes_for_pubkey(pub)
    p2pkh = hashlib.sha256(b"\x76\xa9\x14" + h160(pub) + b"\x88\xac").hexdigest()
    good = p2pkh in shs and len(shs) == 4
    ok &= good
    sys.stderr.write(f"  a pubkey reconstructs {len(shs)} script forms "
                     f"including its own p2pkh: {'OK' if good else 'FAIL'}\n")

    sig = b"\x30" * 71
    ss = bytes([len(sig)]) + sig + bytes([len(pub)]) + pub
    found = pubkeys_in(ss, [])
    good = pub in found
    ok &= good
    sys.stderr.write(f"  pubkey recovered from a p2pkh scriptSig: "
                     f"{'OK' if good else 'FAIL'}\n")
    good = pub in pubkeys_in(b"", [sig, pub])
    ok &= good
    sys.stderr.write(f"  pubkey recovered from a p2wpkh witness:  "
                     f"{'OK' if good else 'FAIL'}\n")

    # embedded text must be found in an output script
    msg = b"OVERDOSE by Max Keiser CL76841714A"
    spk = b"\x6a" + bytes([len(msg)]) + msg
    runs = ASCII_RUN.findall(spk)
    good = any(b"OVERDOSE" in x for x in runs)
    ok &= good
    sys.stderr.write(f"  ASCII run extracted from an OP_RETURN: "
                     f"{'OK' if good else 'FAIL'}\n")
    hits = [w for w in KEYWORDS if w in msg.decode().lower()]
    good = "overdose" in hits and "cl76841714a" in hits
    ok &= good
    sys.stderr.write(f"  keyword match on that run: {hits[:4]} "
                     f"{'OK' if good else 'FAIL'}\n")

    # REGRESSION: the first live run's false positive, block 830,200. An
    # Atomicals realm registration — somebody claiming the NAME "overdose".
    # It must never be reported again.
    atom = "hbitworkcd3165mrequest_realmhoverdoseh"
    rep, got, why = classify(atom)
    ok &= not rep
    sys.stderr.write(f"  block 830,200 Atomicals realm suppressed "
                     f"({why}): {'OK' if not rep else 'FAIL — still reports'}\n")

    # but suppression must not be so wide it eats a real message
    real = "I solved the OVERDOSE puzzle. El Salvador was the clue. Thanks Max."
    rep2, got2, why2 = classify(real)
    ok &= rep2
    sys.stderr.write(f"  a genuine boast still reports ({why2}): "
                     f"{'OK' if rep2 else 'FAIL — over-suppressed'}\n")
    rep3, _g, _w = classify("according to the record, in a word, order restored")
    ok &= not rep3
    sys.stderr.write(f"  ordinary English containing 'ord' is not treated as "
                     f"an ordinals envelope: {'OK' if not rep3 else 'FAIL'}\n")
    rep4, _g, _w = classify("serial CL76841714A appears here")
    ok &= rep4
    sys.stderr.write(f"  a SPECIFIC term reports on its own: "
                     f"{'OK' if rep4 else 'FAIL'}\n")

    bm = "Bitcoin Magazine The Inscription Issue"
    rep5, _g, _w = classify(bm)
    prep, pgot = classify_publisher(bm)
    ok &= (not rep5) and prep
    sys.stderr.write(f"  block 830,776 'Bitcoin Magazine The Inscription "
                     f"Issue': not a puzzle hit ({not rep5}),\n"
                     f"    but IS collected as a publisher artifact "
                     f"({prep}, {pgot}): {'OK' if (not rep5 and prep) else 'FAIL'}\n")
    _p2, g2 = classify_publisher("Bitcoin Magazine Issue 24 The El Salvador Issue")
    ok &= "el salvador" in g2 and "issue 24" in g2
    sys.stderr.write(f"    an issue-24 inscription would be flagged with its "
                     f"hints {g2}: {'OK' if 'issue 24' in g2 else 'FAIL'}\n")

    # THE DETECTOR THAT MATTERS: a block carrying an output of exactly 20 BTC
    # must be caught, with its value read out of the block rather than discarded.
    import sweep as _S
    _out = b"\x00\x14" + b"\x5a" * 20
    _blk = (b"\x00" * 80 + _S.varint(1)
            + _S.Tx([_S.TxIn(b"\x33" * 32, 0, b"\x51", 0xFFFFFFFF)],
                    [_S.TxOut(PRIZE_SATS, _out),
                     _S.TxOut(12345, b"\x00\x14" + b"\x01" * 20)]).ser())
    vals = [pl for kd, pl in scan_block(_blk) if kd == "out"]
    caught = [(v, classify_value(v)) for v, _spk in vals]
    got20 = [c for v, c in caught if c[0] and c[1] == "EXACT_20"]
    ok &= len(vals) == 2 and len(got20) == 1
    sys.stderr.write(f"  a block with a 20.00000000 BTC output: "
                     f"{len(vals)} outputs parsed, {len(got20)} flagged "
                     f"EXACT_20 {'OK' if len(got20)==1 else 'FAIL'}\n")
    ok &= not classify_value(12345)[0]
    ok &= classify_value(1_999_500_000) == (True, "NEAR_20")
    sys.stderr.write(f"  19.995 BTC flagged NEAR_20, dust ignored: "
                     f"{'OK' if classify_value(1_999_500_000)[1]=='NEAR_20' else 'FAIL'}\n")

    t = load_targets()
    sys.stderr.write(f"  {len(t):,} exactly-20-BTC scripthashes loaded as "
                     f"sweep targets\n")
    ok &= len(t) > 700
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default=os.environ.get("B", ""))
    ap.add_argument("--start", type=int, default=830000)
    ap.add_argument("--end", type=int, default=0, help="0 = chain tip")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--out", default="chain_tail_hits.tsv")
    ap.add_argument("--state", default="chain_tail_state.json")
    ap.add_argument("--json", default="chain_tail_hits.jsonl",
                    help="JSON Lines output, one complete object per finding. "
                         "Survives interruption; `jq -s .` makes it an array")
    ap.add_argument("--convert", metavar="TSV",
                    help="convert an existing TSV from a previous run to "
                         "--json and exit")
    ap.add_argument("--verbose", action="store_true",
                    help="also print suppressed matches and why")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    sys.stderr.write("\n  SELFTEST\n")
    if not selftest():
        sys.exit("detection logic fails offline; a null from it would be "
                 "meaningless")
    if a.selftest:
        return
    if a.convert:
        n = tsv_to_json(a.convert, a.json)
        sys.stderr.write(f"\n  {n:,} records: {a.convert} -> {a.json}\n")
        return
    if not a.rpc:
        sys.exit("need --rpc (or $B): an endpoint serving getblockhash/getblock")

    from alchemy_window_scan import RPC
    rpc = RPC(a.rpc)
    targets = load_targets()
    tip = a.end or rpc.batch([("getblockchaininfo", [])])[0]["blocks"]
    start = a.start
    if os.path.exists(a.state):
        try:
            start = max(start, json.load(open(a.state))["next"])
        except Exception:
            pass
    sys.stderr.write(f"\n  blocks {start:,} .. {tip:,} "
                     f"({tip-start+1:,} to go)\n"
                     f"  {len(targets):,} exactly-20 scripthashes watched for "
                     f"a sweep\n\n")

    sink = Sink(a.out, a.json)
    t0, nblk, ntext, nsweep, nsupp, npub = time.time(), 0, 0, 0, 0, 0
    nfull = nnew = 0
    h = start
    try:
        while h <= tip:
            hs = list(range(h, min(h + a.batch, tip + 1)))
            hashes = rpc.batch([("getblockhash", [x]) for x in hs])
            raws = rpc.batch([("getblock", [bh, 0]) for bh in hashes if bh])
            for ht, raw in zip(hs, raws):
                if not raw:
                    continue
                nblk += 1
                try:
                    items = list(scan_block(bytes.fromhex(raw)))
                except Exception as e:
                    sys.stderr.write(f"\n  block {ht}: unparsed ({e})\n")
                    continue
                for kind, payload in items:
                    if kind == "spend":
                        ss, wit = payload
                        for pub in pubkeys_in(ss, wit):
                            hit = scripthashes_for_pubkey(pub) & targets
                            if hit:
                                nsweep += 1
                                for s in hit:
                                    sink.write(
                                        {"type": "SWEEP", "block": ht,
                                         "scripthash": s,
                                         "pubkey": pub.hex()},
                                        ["SWEEP", ht, s, pub.hex()])
                                    sys.stderr.write(
                                        f"\n  *** SWEEP of an exactly-20 "
                                        f"address in block {ht}: {s}\n")
                        continue
                    if kind == "out":
                        value, payload = payload
                        vrep, vtag = classify_value(value)
                        if vrep:
                            nfull += 1
                            sh = hashlib.sha256(payload).hexdigest()
                            known = "known" if sh in targets else "NEW"
                            sink.write(
                                {"type": "FULL", "block": ht, "tag": vtag,
                                 "value": value, "btc": value / 1e8,
                                 "scripthash": sh, "spk": payload.hex(),
                                 "known": known == "known"},
                                ["FULL", ht, vtag, value, sh,
                                 payload.hex(), known])
                            if known == "NEW":
                                nnew += 1
                                sys.stderr.write(
                                    f"\n  >>> {vtag} block {ht}: "
                                    f"{value/1e8:.8f} BTC to a scripthash NOT "
                                    f"in the 795 — {sh[:32]}…\n")
                    for run in ASCII_RUN.findall(payload):
                        txt = run.decode("ascii", "replace")
                        prep, pgot = classify_publisher(txt)
                        if prep:
                            npub += 1
                            sink.write(
                                {"type": "PUBLISHER", "block": ht,
                                 "kind": kind, "matched": pgot,
                                 "text": txt[:400]},
                                ["PUBLISHER", ht, kind, ",".join(pgot),
                                 txt[:200]])
                            sys.stderr.write(f"\n  ~~~ PUBLISHER block {ht} "
                                             f"{pgot}: {txt[:100]}\n")
                        report, got, why = classify(txt)
                        if got and not report:
                            nsupp += 1
                            if a.verbose:
                                sys.stderr.write(f"\n  (suppressed block {ht} "
                                                 f"{got}: {why})\n")
                            continue
                        if report:
                            ntext += 1
                            sink.write(
                                {"type": "TEXT", "block": ht, "kind": kind,
                                 "why": why, "matched": got,
                                 "text": txt[:400]},
                                ["TEXT", ht, kind, why, ",".join(got),
                                 txt[:200]])
                            sys.stderr.write(f"\n  *** TEXT block {ht} "
                                             f"[{kind}] {got} ({why}): "
                                             f"{txt[:110]}\n")
            h = hs[-1] + 1
            json.dump({"next": h}, open(a.state, "w"))
            el = time.time() - t0
            sys.stderr.write(f"\r  {nblk:,} blocks  {ntext} text  "
                             f"{nfull} full({nnew} new)  {nsweep} spent  "
                             f"{npub} pub  {nsupp} supp  "
                             f"{nblk/max(el,1e-9):.1f} blk/s  "
                             f"at {h:,}   ")
            sys.stderr.flush()
    except KeyboardInterrupt:
        sys.stderr.write(f"\n  interrupted at {h:,}; rerun to resume\n")
    finally:
        sink.close()
    sys.stderr.write(f"\n\n  {nblk:,} blocks, {ntext} reportable text "
                     f"hits, {nsupp} suppressed as noise, "
                     f"{npub} Bitcoin Magazine artifacts,\n"
                     f"  {nfull} outputs at ~20 BTC of which {nnew} are NOT in "
                     f"the 795, {nsweep} spends of known ones\n")


if __name__ == "__main__":
    main()
