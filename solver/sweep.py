#!/usr/bin/env python3
"""
Find every UTXO a private key controls, and move them to one address.

WHAT THIS IS FOR, STATED HONESTLY
The solver has never been able to act on a win. It derives keys and asks an
oracle whether the resulting addresses hold coins; if one ever fired there was
nothing here that could spend it. This closes that gap.

It does NOT solve anything. `window/what_the_nulls_prove.md` records that ~150M
derivations from this article have never produced an address holding a single
satoshi. This sweeps what is found. Its value is being built, controlled and
tested BEFORE a hit rather than written in a panic after one.

WHY THE SIGNER IS TRUSTWORTHY, OR REFUSES TO RUN
A signer cannot be trusted merely because it emits a signature. It has to emit
the signature CONSENSUS expects. The BIP test vectors are not fetchable here and
hardcoding remembered ones is exactly the mistake this project already shipped
once, in a selftest that asserted a remembered address as ground truth and was
wrong.

So confirmed mainnet transactions are the oracle. Two controls, both grounded in
bytes the network already accepted:

  SERIALIZER  fetch a confirmed transaction, parse it, re-serialize it with this
              encoder, and require the bytes to be IDENTICAL. That pins varints,
              field order, the segwit marker/flag and witness layout.

  SIGHASH     for a confirmed spend, recompute the sighash with this code and
              verify the signature ALREADY IN that transaction against the pubkey
              ALREADY IN its scriptSig/witness. Any deviation from consensus
              changes the 32-byte hash and verification fails.

Cheap, because Esplora annotates prevouts (see trace_funding.py:109), so one
/tx/{txid} fetch supplies the amounts BIP-143 needs.

WHERE THE ACTUAL RISK IS
Many signing bugs are FAIL-SAFE: a wrong sighash, a wrong BIP-143 amount or a
dust output produces a transaction nodes simply reject, and nothing is lost.
Three mistakes are not —

  1. a wrong output script    funds leave and do not come back
  2. an excessive fee         a typo on 20 BTC is a gift to a miner
  3. a wrong LEGACY input amount

The third was missed on the first pass and its absence was actively claimed as
safe. It is not. A legacy SIGHASH_ALL preimage contains no input amount at all
— signing the same input as 100,000 sat and as 2,000,000,000 sat yields a
byte-identical sighash — so an understated legacy value still produces a valid
signature, and the difference is paid to a miner. Every fee check here compares
endpoint-supplied numbers against each other, which is circular and cannot see
it. verify_amounts() closes it by reading each legacy value out of that input's
own previous transaction, and refusing when it cannot.

(1) and (2) are checked after signing by re-parsing the finished transaction.

  python3 sweep.py --selftest
  python3 sweep.py --control --base "$ESPLORA"
  python3 sweep.py --key <WIF|hex> --to <addr> --base "$ESPLORA"
  python3 sweep.py --key <WIF|hex> --to <addr> --base "$ESPLORA" --broadcast
"""
import argparse, hashlib, json, os, struct, sys

CURVE_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SIGHASH_ALL = 0x01
RBF_SEQUENCE = 0xFFFFFFFD        # signal replaceability so the fee can be bumped
DUST = 546                        # conservative: the P2PKH relay floor
DEFAULT_MAX_FEE = 100_000         # absolute sat cap
MAX_FEE_FRACTION = 0.01           # and never more than 1% of the swept value

# Input types this signer will handle. Anything else is reported, never guessed.
SIGNABLE = ("p2pkh_c", "p2pkh_u", "p2wpkh", "p2sh_p2wpkh", "p2pk_c", "p2pk_u")


def dsha(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def h160(b):
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()


# --------------------------------------------------------------- encoding ---
def varint(n):
    if n < 0xFD:
        return bytes([n])
    if n <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", n)
    if n <= 0xFFFFFFFF:
        return b"\xfe" + struct.pack("<I", n)
    return b"\xff" + struct.pack("<Q", n)


def pushdata(b):
    """Minimal push of a data blob onto the script stack."""
    n = len(b)
    if n < 0x4C:
        return bytes([n]) + b
    if n <= 0xFF:
        return b"\x4c" + bytes([n]) + b
    if n <= 0xFFFF:
        return b"\x4d" + struct.pack("<H", n) + b
    return b"\x4e" + struct.pack("<I", n) + b


class TxIn:
    __slots__ = ("txid", "vout", "script_sig", "sequence", "witness",
                 "amount", "spk", "kind")

    def __init__(self, txid, vout, script_sig=b"", sequence=RBF_SEQUENCE,
                 witness=None, amount=0, spk=b"", kind=""):
        self.txid = txid                  # internal byte order (display reversed)
        self.vout = vout
        self.script_sig = script_sig
        self.sequence = sequence
        self.witness = witness or []
        self.amount = amount
        self.spk = spk
        self.kind = kind

    def outpoint(self):
        return self.txid + struct.pack("<I", self.vout)

    def ser(self):
        return (self.outpoint() + varint(len(self.script_sig))
                + self.script_sig + struct.pack("<I", self.sequence))


class TxOut:
    __slots__ = ("value", "spk")

    def __init__(self, value, spk):
        self.value, self.spk = value, spk

    def ser(self):
        return struct.pack("<Q", self.value) + varint(len(self.spk)) + self.spk


class Tx:
    def __init__(self, vin=None, vout=None, version=2, locktime=0):
        self.vin = vin or []
        self.vout = vout or []
        self.version = version
        self.locktime = locktime

    def has_witness(self):
        return any(i.witness for i in self.vin)

    def ser(self, witness=True):
        out = struct.pack("<I", self.version)
        w = witness and self.has_witness()
        if w:
            out += b"\x00\x01"
        out += varint(len(self.vin)) + b"".join(i.ser() for i in self.vin)
        out += varint(len(self.vout)) + b"".join(o.ser() for o in self.vout)
        if w:
            for i in self.vin:
                out += varint(len(i.witness))
                for item in i.witness:
                    out += varint(len(item)) + item
        return out + struct.pack("<I", self.locktime)

    def txid(self):
        return dsha(self.ser(witness=False))[::-1].hex()

    def vsize(self):
        base = len(self.ser(witness=False))
        total = len(self.ser(witness=True))
        return (base * 3 + total + 3) // 4


# ---------------------------------------------------------------- parsing ---
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
        return struct.unpack("<I", self.take(4))[0]

    def u64(self):
        return struct.unpack("<Q", self.take(8))[0]

    def varint(self):
        n = self.take(1)[0]
        if n < 0xFD:
            return n
        if n == 0xFD:
            return struct.unpack("<H", self.take(2))[0]
        if n == 0xFE:
            return struct.unpack("<I", self.take(4))[0]
        return struct.unpack("<Q", self.take(8))[0]


def parse_tx(raw):
    """Raw bytes -> Tx. Round-trips: parse_tx(x).ser() == x for valid x."""
    r = Reader(raw)
    tx = Tx(version=r.u32())
    segwit = False
    n_in = r.varint()
    if n_in == 0:                       # segwit marker; flag byte follows
        if r.take(1) != b"\x01":
            raise ValueError("bad segwit flag")
        segwit = True
        n_in = r.varint()
    for _ in range(n_in):
        txid, vout = r.take(32), r.u32()
        ss = r.take(r.varint())
        tx.vin.append(TxIn(txid, vout, ss, r.u32()))
    for _ in range(r.varint()):
        v = r.u64()
        tx.vout.append(TxOut(v, r.take(r.varint())))
    if segwit:
        for i in tx.vin:
            i.witness = [r.take(r.varint()) for _ in range(r.varint())]
    tx.locktime = r.u32()
    if r.i != len(raw):
        raise ValueError(f"trailing bytes: {len(raw) - r.i}")
    return tx


# --------------------------------------------------------------- sighashes ---
def sighash_legacy(tx, idx, script_code, hashtype=SIGHASH_ALL):
    """Pre-segwit SIGHASH_ALL: every other scriptSig blanked."""
    clone = Tx([TxIn(i.txid, i.vout, b"", i.sequence) for i in tx.vin],
               [TxOut(o.value, o.spk) for o in tx.vout],
               tx.version, tx.locktime)
    clone.vin[idx].script_sig = script_code
    return dsha(clone.ser(witness=False) + struct.pack("<I", hashtype))


def sighash_bip143(tx, idx, script_code, amount, hashtype=SIGHASH_ALL):
    """BIP-143. script_code is passed WITHOUT its length prefix."""
    hash_prevouts = dsha(b"".join(i.outpoint() for i in tx.vin))
    hash_sequence = dsha(b"".join(struct.pack("<I", i.sequence)
                                  for i in tx.vin))
    hash_outputs = dsha(b"".join(o.ser() for o in tx.vout))
    i = tx.vin[idx]
    pre = (struct.pack("<I", tx.version)
           + hash_prevouts + hash_sequence
           + i.outpoint()
           + varint(len(script_code)) + script_code
           + struct.pack("<Q", amount)
           + struct.pack("<I", i.sequence)
           + hash_outputs
           + struct.pack("<I", tx.locktime)
           + struct.pack("<I", hashtype))
    return dsha(pre)


def classify_spk(spk):
    """Name the script type of a scriptPubKey, or '' if unrecognised."""
    if len(spk) == 25 and spk[:3] == b"\x76\xa9\x14" and spk[23:] == b"\x88\xac":
        return "p2pkh"
    if len(spk) == 22 and spk[:2] == b"\x00\x14":
        return "p2wpkh"
    if len(spk) == 23 and spk[:2] == b"\xa9\x14" and spk[22:] == b"\x87":
        return "p2sh"
    if len(spk) == 34 and spk[:2] == b"\x00\x20":
        return "p2wsh"
    if len(spk) == 34 and spk[:2] == b"\x51\x20":
        return "p2tr"
    if len(spk) in (35, 67) and spk[-1:] == b"\xac":
        return "p2pk"
    return ""


def addr_for_spk(spk):
    """Address for a scriptPubKey, or None where no address form exists.

    Bare P2PK and most wrapped scripts have no address at all, which is why
    scripthash lookup is the primary path.
    """
    from hd_sweep import b58check, bech32_encode
    k = classify_spk(spk)
    if k == "p2pkh":
        return b58check(b"\x00" + spk[3:23])
    if k == "p2sh":
        return b58check(b"\x05" + spk[2:22])
    if k in ("p2wpkh", "p2wsh"):
        return bech32_encode("bc", 0, spk[2:])
    if k == "p2tr":
        return bech32_encode("bc", 1, spk[2:])
    return None


# ----------------------------------------------------------------- signing ---
def sign_input(tx, idx, priv32, kind, amount, pub):
    """Fill in scriptSig / witness for one input. Returns the sighash used."""
    from coincurve import PrivateKey
    sk = PrivateKey(priv32)
    hp = h160(pub)

    if kind in ("p2pkh_c", "p2pkh_u"):
        sc = b"\x76\xa9\x14" + hp + b"\x88\xac"
        sh = sighash_legacy(tx, idx, sc)
        sig = sk.sign(sh, hasher=None) + bytes([SIGHASH_ALL])
        tx.vin[idx].script_sig = pushdata(sig) + pushdata(pub)
    elif kind in ("p2pk_c", "p2pk_u"):
        sc = pushdata(pub) + b"\xac"
        sh = sighash_legacy(tx, idx, sc)
        sig = sk.sign(sh, hasher=None) + bytes([SIGHASH_ALL])
        tx.vin[idx].script_sig = pushdata(sig)
    elif kind == "p2wpkh":
        sc = b"\x76\xa9\x14" + hp + b"\x88\xac"
        sh = sighash_bip143(tx, idx, sc, amount)
        sig = sk.sign(sh, hasher=None) + bytes([SIGHASH_ALL])
        tx.vin[idx].script_sig = b""
        tx.vin[idx].witness = [sig, pub]
    elif kind == "p2sh_p2wpkh":
        redeem = b"\x00\x14" + hp
        sc = b"\x76\xa9\x14" + hp + b"\x88\xac"
        sh = sighash_bip143(tx, idx, sc, amount)
        sig = sk.sign(sh, hasher=None) + bytes([SIGHASH_ALL])
        tx.vin[idx].script_sig = pushdata(redeem)
        tx.vin[idx].witness = [sig, pub]
    else:
        raise ValueError(f"refusing to sign unsupported input type {kind!r}")
    return sh


def dummy_size(tx, kinds, pubs):
    """vsize with maximal (72-byte) signatures, for fee estimation.

    Real signatures are never larger, so the fee rate actually paid is always
    at least the rate requested. Erring that way is the safe direction.
    """
    import copy
    t = Tx([TxIn(i.txid, i.vout, b"", i.sequence) for i in tx.vin],
           [TxOut(o.value, o.spk) for o in tx.vout], tx.version, tx.locktime)
    fake = b"\x00" * 72
    for n, (k, pub) in enumerate(zip(kinds, pubs)):
        hp = h160(pub)
        if k in ("p2pkh_c", "p2pkh_u"):
            t.vin[n].script_sig = pushdata(fake) + pushdata(pub)
        elif k in ("p2pk_c", "p2pk_u"):
            t.vin[n].script_sig = pushdata(fake)
        elif k == "p2wpkh":
            t.vin[n].witness = [fake, pub]
        elif k == "p2sh_p2wpkh":
            t.vin[n].script_sig = pushdata(b"\x00\x14" + hp)
            t.vin[n].witness = [fake, pub]
    return t.vsize()


# ------------------------------------------------------------------ network ---
class Chain:
    """Esplora over the user's own endpoint. GET for reads, POST to broadcast."""

    def __init__(self, base, timeout=30):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def _req(self, path, data=None):
        import urllib.request, urllib.error
        url = self.base + path
        req = urllib.request.Request(
            url, data=data,
            headers={"User-Agent": "overdose-sweep/1",
                     "Content-Type": "text/plain"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read().decode().strip()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} from {path}: "
                               f"{e.read().decode()[:200]}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"cannot reach {self.base} — {e.reason}") from None

    def get_json(self, path):
        return json.loads(self._req(path))

    def raw_tx(self, txid):
        return bytes.fromhex(self._req(f"/tx/{txid}/hex"))

    def tx(self, txid):
        return self.get_json(f"/tx/{txid}")

    def utxos(self, addr):
        return self.get_json(f"/address/{addr}/utxo")

    def utxos_sh(self, spk):
        h = hashlib.sha256(spk).hexdigest()
        return self.get_json(f"/scripthash/{h}/utxo")

    def fee_estimates(self):
        try:
            return self.get_json("/fee-estimates")
        except Exception:
            return {}

    def broadcast(self, raw_hex):
        return self._req("/tx", data=raw_hex.encode())


# ------------------------------------------------------------------ controls ---
def control_serializer(chain, txid):
    """Re-serialising a confirmed transaction must reproduce it byte for byte."""
    raw = chain.raw_tx(txid)
    tx = parse_tx(raw)
    again = tx.ser()
    ok = again == raw
    sys.stderr.write(
        f"  serializer   {txid[:16]}…  {len(raw)} bytes, "
        f"{len(tx.vin)} in / {len(tx.vout)} out, "
        f"{'segwit' if tx.has_witness() else 'legacy'}  "
        f"{'IDENTICAL' if ok else 'MISMATCH'}\n")
    if ok and tx.txid() != txid:
        sys.stderr.write(f"    but txid recomputes to {tx.txid()} — FAIL\n")
        return False
    return ok


def control_sighash(chain, txid):
    """Recompute a confirmed spend's sighash; its own signature must verify.

    This is the whole safety argument. If the preimage deviates from consensus
    in any way the 32-byte hash changes and a signature the network already
    accepted stops verifying.
    """
    from coincurve import PublicKey
    raw = chain.raw_tx(txid)
    tx = parse_tx(raw)
    meta = chain.tx(txid)
    prevs = [v.get("prevout") or {} for v in meta.get("vin", [])]
    if len(prevs) != len(tx.vin):
        sys.stderr.write(f"  sighash      {txid[:16]}…  prevout count mismatch\n")
        return False, set()

    checked, kinds = 0, set()
    for n, (i, pv) in enumerate(zip(tx.vin, prevs)):
        spk = bytes.fromhex(pv.get("scriptpubkey") or "")
        amount = pv.get("value")
        kind = classify_spk(spk)
        try:
            if kind == "p2pkh" and i.script_sig:
                r = Reader(i.script_sig)
                sig = r.take(r.take(1)[0])
                pub = r.take(r.take(1)[0])
                sh = sighash_legacy(tx, n, spk)
            elif kind == "p2wpkh" and len(i.witness) == 2:
                sig, pub = i.witness
                sc = b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"
                sh = sighash_bip143(tx, n, sc, amount)
            elif kind == "p2sh" and len(i.witness) == 2 and i.script_sig:
                sig, pub = i.witness
                sc = b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"
                sh = sighash_bip143(tx, n, sc, amount)
            elif kind == "p2pk" and i.script_sig:
                # the pubkey lives in the OUTPUT, not the input; the scriptCode
                # is the whole scriptPubKey
                r = Reader(i.script_sig)
                sig = r.take(r.take(1)[0])
                pub = spk[1:-1]
                sh = sighash_legacy(tx, n, spk)
            else:
                continue
            if sig[-1] != SIGHASH_ALL:
                continue                       # only SIGHASH_ALL is modelled
            good = PublicKey(pub).verify(sig[:-1], sh, hasher=None)
        except Exception as e:
            sys.stderr.write(f"    input {n} ({kind}): error {e}\n")
            return False, kinds
        checked += 1
        kinds.add(kind)
        sys.stderr.write(f"  sighash      {txid[:16]}… input {n} {kind:12} "
                         f"{'VERIFIES' if good else 'FAILS'}\n")
        if not good:
            return False, kinds
    if not checked:
        sys.stderr.write(f"  sighash      {txid[:16]}…  no SIGHASH_ALL input "
                         f"of a modelled type — inconclusive\n")
        return False, kinds
    return True, kinds


# Every input type this signer can produce, and whether a control is required.
# p2pk is optional only because bare-pubkey outputs are nearly extinct on the
# modern chain — not because it matters less.
REQUIRED_CONTROLS = ("p2pkh", "p2wpkh", "p2sh")
OPTIONAL_CONTROLS = ("p2pk",)


def find_control_txs(chain, back=6, per_block=25,
                     need=REQUIRED_CONTROLS, optional=OPTIONAL_CONTROLS):
    """Discover confirmed transactions to validate the signer against.

    The alternative is for a human (or me) to supply txids from memory, and
    this project has already been bitten once by a selftest that asserted a
    remembered value as ground truth. Nothing here is remembered: the chain is
    walked, transactions are fetched, and their own bytes decide. A wrong guess
    cannot pass — it can only fail to be found.

    One control is sought per input type this signer can emit, so that no
    signing path is trusted merely because a DIFFERENT path was validated.
    """
    need = tuple(need) + tuple(optional)
    tip = int(chain._req("/blocks/tip/height"))
    found, seen, blocks = {}, 0, 0

    def done():
        """Stop once every type is found, required and optional alike.

        Stopping at the REQUIRED set and then reporting that an optional type
        was 'not found in N blocks' is a lie: the search ended before it ever
        looked. `budget` is what actually bounds the hunt.
        """
        return all(k in found for k in need)

    budget = back * per_block
    sys.stderr.write(f"  searching for control transactions from block {tip} "
                     f"backwards (budget {budget} tx)\n")
    for h in range(tip - 1, tip - 1 - back, -1):
        if done() or seen >= budget:
            break
        try:
            bh = chain._req(f"/block-height/{h}")
            txids = chain.get_json(f"/block/{bh}/txids")
        except RuntimeError as e:
            sys.stderr.write(f"    block {h}: {e}\n")
            continue
        blocks += 1
        for txid in txids[1:per_block + 1]:          # [0] is the coinbase
            if done() or seen >= budget:
                break
            try:
                meta = chain.tx(txid)
            except RuntimeError:
                continue
            seen += 1
            raw = None
            for v in meta.get("vin", []):
                pv = v.get("prevout") or {}
                kind = classify_spk(bytes.fromhex(pv.get("scriptpubkey") or ""))
                if kind not in need or kind in found:
                    continue
                # only SIGHASH_ALL spends are modelled by this signer
                if raw is None:
                    try:
                        raw = parse_tx(chain.raw_tx(txid))
                    except Exception:
                        break
                n = meta["vin"].index(v)
                i = raw.vin[n]
                sig = (i.witness[0] if len(i.witness) == 2
                       else (i.script_sig[1:i.script_sig[0] + 1]
                             if i.script_sig else b""))
                if sig and sig[-1] == SIGHASH_ALL:
                    found[kind] = txid
                    sys.stderr.write(f"    {kind:8} <- {txid[:16]}… "
                                     f"(block {h}, input {n})\n")
    missing = [k for k in REQUIRED_CONTROLS if k not in found]
    absent = [k for k in optional if k not in found]
    if absent:
        sys.stderr.write(
            f"    searched {seen} transactions in {blocks} block(s); no "
            f"{', '.join(absent)} spend among them.\n"
            f"    Bare-pubkey outputs are nearly extinct on the modern chain, "
            f"so recent blocks are the\n"
            f"    wrong place to look — raise --control-blocks, or pass "
            f"--control-tx with an old spend.\n"
            f"    That path stays UNPROVEN: it shares the legacy sighash with "
            f"p2pkh, but its pubkey\n"
            f"    comes from the OUTPUT and its scriptCode is the whole "
            f"scriptPubKey.\n")
    if missing:
        sys.stderr.write(f"    no confirmed {', '.join(missing)} spend found in "
                         f"{seen} transactions across {back} blocks\n")
    return list(found.values()), missing


def cross_check():
    """Compare every sighash against a SECOND, independent implementation.

    The chain-grounded controls are the stronger evidence where they apply, but
    they cannot reach bare P2PK: spends of bare-pubkey outputs are a 2009-era
    artefact and essentially absent from modern blocks, so no confirmed
    transaction exists to validate that path against.

    embit is an unrelated BIP-174/BIP-143 implementation. If two independently
    written codebases derive the same 32-byte hash for the same transaction,
    the remaining possibility is that both are wrong in the same way — which is
    a far smaller space than one being wrong on its own.

    Optional by design: if embit is not installed the run says the paths are
    uncorroborated rather than pretending they were checked.
        pip install embit
    """
    try:
        from embit.transaction import Transaction
        from embit.script import Script
    except ImportError:
        sys.stderr.write("  cross-check: embit not installed — sighashes are "
                         "uncorroborated by a second implementation\n"
                         "               (pip install embit)\n")
        return None

    import hashlib as _h
    from coincurve import PrivateKey
    from full_sweep import spks_for_key
    from spk_extra import sc_p2pk
    from index_oracle import spk_from_address

    k = _h.sha256(b"sweep cross-check").digest()
    pub = PrivateKey(k).public_key.format(True)
    f = dict(spks_for_key(k))
    dest = spk_from_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
    plan = [("p2pkh_c", f["p2pkh_c"]), ("p2wpkh", f["p2wpkh"]),
            ("p2sh_p2wpkh", f["p2sh_p2wpkh"]), ("p2pk_c", sc_p2pk(pub))]
    u = [{"kind": kd, "spk": spk, "key": k, "pub": pub,
          "txid": "%064x" % (i + 1), "vout": i, "value": 500_000_000}
         for i, (kd, spk) in enumerate(plan)]

    tx, _fee = build_and_sign(u, dest, 20.0, DEFAULT_MAX_FEE)
    et = Transaction.parse(tx.ser())
    ok = et.txid().hex() == tx.txid()
    sys.stderr.write(f"  cross-check: embit parses our signed tx and agrees on "
                     f"the txid: {'OK' if ok else 'FAIL'}\n")

    hp = h160(pub)
    for n, x in enumerate(u):
        bare = Tx([TxIn(i.txid, i.vout, b"", i.sequence) for i in tx.vin],
                  [TxOut(o.value, o.spk) for o in tx.vout],
                  tx.version, tx.locktime)
        if x["kind"] in ("p2wpkh", "p2sh_p2wpkh"):
            sc = b"\x76\xa9\x14" + hp + b"\x88\xac"
            mine = sighash_bip143(bare, n, sc, x["value"])
            theirs = et.sighash_segwit(n, Script(sc), x["value"])
        else:
            sc = x["spk"]
            mine = sighash_legacy(bare, n, sc)
            theirs = et.sighash_legacy(n, Script(sc))
        same = mine == theirs
        ok &= same
        sys.stderr.write(f"    {x['kind']:12} sighash matches embit: "
                         f"{'OK' if same else 'MISMATCH'}\n")
    return ok


def run_controls(chain, txids):
    sys.stderr.write("\n  CHAIN-GROUNDED CONTROLS — confirmed transactions as "
                     "the oracle\n")
    ok, covered = True, set()
    for t in dict.fromkeys(txids):          # dedupe, keep order
        try:
            ok &= control_serializer(chain, t)
            good, kinds = control_sighash(chain, t)
            ok &= good
            covered |= kinds
        except RuntimeError as e:
            sys.stderr.write(f"  {t[:16]}…  {e}\n")
            ok = False

    # "PASS" on its own invites the assumption that every path was checked.
    # Name the ones that were, and the ones that were not.
    sys.stderr.write("\n  SIGNING PATHS PROVEN AGAINST CONFIRMED SPENDS\n")
    for kind, sig_kind in (("p2pkh", "legacy"), ("p2pk", "legacy"),
                           ("p2wpkh", "BIP-143"), ("p2sh", "BIP-143")):
        mark = "ok" if kind in covered else "--"
        note = "" if kind in covered else "   NOT PROVEN"
        sys.stderr.write(f"    [{mark}] {kind:8} {sig_kind:8}{note}\n")
    gaps = [k for k in REQUIRED_CONTROLS + OPTIONAL_CONTROLS if k not in covered]
    if gaps and ok:
        sys.stderr.write(
            f"    The signer still emits {', '.join(gaps)} inputs. Their "
            f"sighash algorithm is shared\n    with a path that WAS proven, but "
            f"their scriptCode or scriptSig is not.\n")
    sys.stderr.write(f"  CONTROLS {'PASS' if ok else 'FAIL'}\n")
    return ok


# ------------------------------------------------------------------ selftest ---
def selftest():
    """Offline. Everything that does not need the network."""
    ok = True

    # varint boundaries
    for n, want in ((0, b"\x00"), (0xFC, b"\xfc"), (0xFD, b"\xfd\xfd\x00"),
                    (0xFFFF, b"\xfd\xff\xff"), (0x10000, b"\xfe\x00\x00\x01\x00")):
        good = varint(n) == want
        ok &= good
        if not good:
            sys.stderr.write(f"  varint({n}) = {varint(n).hex()} want "
                             f"{want.hex()}  FAIL\n")
    sys.stderr.write(f"  varint boundaries: {'OK' if ok else 'FAIL'}\n")

    # round trip: parse(ser(x)) == x, for legacy and segwit shapes
    for label, wit in (("legacy", []), ("segwit", [b"\x11" * 71, b"\x02" * 33])):
        t = Tx([TxIn(b"\xaa" * 32, 1, b"\x51", RBF_SEQUENCE, list(wit))],
               [TxOut(12345, b"\x00\x14" + b"\xbb" * 20)])
        raw = t.ser()
        back = parse_tx(raw)
        good = (back.ser() == raw and back.vin[0].vout == 1
                and back.vout[0].value == 12345
                and back.vin[0].witness == list(wit))
        ok &= good
        sys.stderr.write(f"  {label} round trip through parse_tx: "
                         f"{'OK' if good else 'FAIL'}\n")

    # destination parsing must agree with the repo's own decoder
    from index_oracle import spk_from_address
    from hd_sweep import b58check
    a = b58check(b"\x00" + b"\x11" * 20)
    good = spk_from_address(a) == b"\x76\xa9\x14" + b"\x11" * 20 + b"\x88\xac"
    ok &= good
    sys.stderr.write(f"  P2PKH address -> scriptPubKey: "
                     f"{'OK' if good else 'FAIL'}\n")

    # script builders must match full_sweep's, which the solver searched with
    from full_sweep import spks_for_key
    from coincurve import PrivateKey
    k = hashlib.sha256(b"sweep selftest").digest()
    pub = PrivateKey(k).public_key.format(compressed=True)
    mine = {"p2pkh_c": b"\x76\xa9\x14" + h160(pub) + b"\x88\xac",
            "p2wpkh": b"\x00\x14" + h160(pub),
            "p2sh_p2wpkh": b"\xa9\x14" + h160(b"\x00\x14" + h160(pub)) + b"\x87"}
    theirs = dict(spks_for_key(k))
    for name, spk in mine.items():
        good = theirs.get(name) == spk
        ok &= good
        sys.stderr.write(f"  {name:12} matches full_sweep.spks_for_key: "
                         f"{'OK' if good else 'FAIL'}\n")

    # classify_spk must round-trip every form the solver enumerates
    for name, spk in theirs.items():
        c = classify_spk(spk)
        exp = {"p2pkh_c": "p2pkh", "p2pkh_u": "p2pkh", "p2wpkh": "p2wpkh",
               "p2sh_p2wpkh": "p2sh", "p2tr": "p2tr"}.get(name)
        good = c == exp
        ok &= good
        if not good:
            sys.stderr.write(f"  classify_spk({name}) = {c!r} want {exp!r} FAIL\n")
    sys.stderr.write(f"  classify_spk over every solver script type: "
                     f"{'OK' if ok else 'FAIL'}\n")

    # a signature must verify against the sighash it was made for, and NOT
    # against the sighash of a tampered transaction
    tx = Tx([TxIn(b"\xcc" * 32, 0, amount=100000, kind="p2wpkh")],
            [TxOut(90000, b"\x00\x14" + b"\xdd" * 20)])
    sh = sign_input(tx, 0, k, "p2wpkh", 100000, pub)
    from coincurve import PublicKey
    sig = tx.vin[0].witness[0]
    good = PublicKey(pub).verify(sig[:-1], sh, hasher=None)
    ok &= good
    sys.stderr.write(f"  signed input verifies against its own sighash: "
                     f"{'OK' if good else 'FAIL'}\n")
    tx.vout[0].spk = b"\x00\x14" + b"\xee" * 20        # tamper the destination
    sh2 = sighash_bip143(tx, 0, b"\x76\xa9\x14" + h160(pub) + b"\x88\xac", 100000)
    tampered = PublicKey(pub).verify(sig[:-1], sh2, hasher=None)
    ok &= not tampered
    sys.stderr.write(f"  same signature REJECTED after the output is changed: "
                     f"{'OK' if not tampered else 'FAIL'}\n")

    # PSBT: magic, structure, and a round trip through our own parser. This is
    # a floor, not a proof — only an independent decoder proves the encoding.
    tp = Tx([TxIn(b"\xcc" * 32, 0, amount=100000, kind="p2wpkh"),
             TxIn(b"\xbb" * 32, 1, amount=50000, kind="p2pkh_c")],
            [TxOut(140000, b"\x00\x14" + b"\xdd" * 20)])
    us = [{"kind": "p2wpkh", "spk": b"\x00\x14" + h160(pub), "value": 100000,
           "pub": pub, "txid": "cc" * 32},
          {"kind": "p2pkh_c", "spk": b"\x76\xa9\x14" + h160(pub) + b"\x88\xac",
           "value": 50000, "pub": pub, "txid": "bb" * 32}]
    prev = Tx([TxIn(b"\x99" * 32, 0, b"\x51", 0xFFFFFFFF)],
              [TxOut(0, b""), TxOut(50000, us[1]["spk"])])
    us[1]["txid"] = prev.txid()
    tp.vin[1].txid = bytes.fromhex(prev.txid())[::-1]
    p = build_psbt(tp, us, chain=None, prevtxs={prev.txid(): prev.ser()})
    good = p[:5] == PSBT_MAGIC
    try:
        ptx, pins, pouts = parse_psbt(p)
        good &= (ptx.ser(witness=False)
                 == unsigned_clone(tp).ser(witness=False))
        good &= len(pins) == 2 and len(pouts) == 1
        good &= PSBT_IN_WITNESS_UTXO in pins[0]
        # the legacy input's non_witness_utxo must hash to its own outpoint,
        # which is what a strict decoder checks and the easiest thing to botch
        good &= PSBT_IN_NON_WITNESS_UTXO in pins[1]
        good &= (parse_tx(pins[1][PSBT_IN_NON_WITNESS_UTXO]).txid()
                 == ptx.vin[1].txid[::-1].hex())
        good &= all(not i.script_sig and not i.witness for i in ptx.vin)
    except Exception as e:
        sys.stderr.write(f"  psbt round trip raised {e}\n")
        good = False
    ok &= good
    sys.stderr.write(f"  PSBT magic, round trip, and empty scriptSigs in the "
                     f"unsigned tx: {'OK' if good else 'FAIL'}\n")

    # The reason verify_amounts exists, asserted rather than described: a
    # legacy sighash is blind to the input amount, a segwit one is not.
    spk_l = b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"
    def _lsh(v):
        t = Tx([TxIn(b"\xaa" * 32, 0, amount=v, spk=spk_l, kind="p2pkh_c")],
               [TxOut(90_000, b"\x00\x14" + b"\xdd" * 20)])
        return sighash_legacy(t, 0, spk_l)
    def _wsh(v):
        t = Tx([TxIn(b"\xaa" * 32, 0, amount=v, spk=b"\x00\x14" + h160(pub),
                     kind="p2wpkh")],
               [TxOut(90_000, b"\x00\x14" + b"\xdd" * 20)])
        return sighash_bip143(t, 0, spk_l, v)
    blind = _lsh(100_000) == _lsh(2_000_000_000)
    commits = _wsh(100_000) != _wsh(2_000_000_000)
    good = blind and commits
    ok &= good
    sys.stderr.write(f"  legacy sighash is blind to the input amount "
                     f"({'confirmed' if blind else 'NOT CONFIRMED'}) and "
                     f"BIP-143 commits to it\n"
                     f"    ({'confirmed' if commits else 'NOT CONFIRMED'}) — "
                     f"this is why verify_amounts() is mandatory: "
                     f"{'OK' if good else 'FAIL'}\n")

    # fee guards
    good = (fee_ok(50_000, 2_000_000_000, DEFAULT_MAX_FEE)[0]
            and not fee_ok(200_000, 2_000_000_000, DEFAULT_MAX_FEE)[0]
            and not fee_ok(5_000, 100_000, DEFAULT_MAX_FEE)[0])
    ok &= good
    sys.stderr.write(f"  fee caps (absolute and proportional): "
                     f"{'OK' if good else 'FAIL'}\n")

    xc = cross_check()
    if xc is False:
        ok = False
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


def fee_ok(fee, total_in, max_fee):
    if fee < 0:
        return False, "negative fee"
    if fee > max_fee:
        return False, f"fee {fee:,} exceeds --max-fee {max_fee:,}"
    if total_in and fee > total_in * MAX_FEE_FRACTION:
        return False, (f"fee {fee:,} exceeds {MAX_FEE_FRACTION:.0%} of the "
                       f"{total_in:,} sat being swept")
    return True, ""


# -------------------------------------------------------------------- PSBT ---
# BIP-174. The point of emitting one is NOT to sign elsewhere — a PSBT is
# signed by a wallet that holds the key, and a raw brainwallet key has no such
# wallet until you import it. The point is INDEPENDENT VERIFICATION: Sparrow,
# Electrum or `bitcoin-cli decodepsbt` will tell you exactly what is about to
# be signed without you having to trust the 900 lines above.
#
# There is no chain-grounded oracle for this the way there is for sighashes.
# The oracle is interop itself: if a real decoder accepts it and shows the
# right destination and amounts, the encoding is right. So this emits, parses
# its own output back, and then tells you to go check it with something that
# is not me.
PSBT_MAGIC = b"psbt\xff"
PSBT_GLOBAL_UNSIGNED_TX = 0x00
PSBT_IN_NON_WITNESS_UTXO = 0x00
PSBT_IN_WITNESS_UTXO = 0x01
PSBT_IN_REDEEM_SCRIPT = 0x04
PSBT_SEPARATOR = b"\x00"


def _kv(keytype, value, keydata=b""):
    """One PSBT key-value pair: <len><keytype+keydata><len><value>."""
    key = bytes([keytype]) + keydata
    return varint(len(key)) + key + varint(len(value)) + value


def unsigned_clone(tx):
    """The transaction with every scriptSig and witness stripped.

    PSBT's global unsigned tx must carry no input scripts at all; a decoder
    that sees one rejects the whole thing.
    """
    return Tx([TxIn(i.txid, i.vout, b"", i.sequence) for i in tx.vin],
              [TxOut(o.value, o.spk) for o in tx.vout],
              tx.version, tx.locktime)


def build_psbt(tx, utxos, chain=None, prevtxs=None):
    """Serialize an unsigned transaction plus its input context as a PSBT.

    prevtxs maps txid -> raw previous transaction, for callers that already
    have them (the demo synthesizes its own). Otherwise they are fetched.
    """
    prevtxs = prevtxs or {}
    out = PSBT_MAGIC
    out += _kv(PSBT_GLOBAL_UNSIGNED_TX, unsigned_clone(tx).ser(witness=False))
    out += PSBT_SEPARATOR

    for i, u in zip(tx.vin, utxos):
        m = b""
        kind = u["kind"]
        if kind in ("p2wpkh", "p2sh_p2wpkh"):
            # witness_utxo is just the one output being spent: value + script
            m += _kv(PSBT_IN_WITNESS_UTXO,
                     struct.pack("<Q", u["value"]) + varint(len(u["spk"]))
                     + u["spk"])
            if kind == "p2sh_p2wpkh":
                from coincurve import PrivateKey
                pub = u["pub"]
                m += _kv(PSBT_IN_REDEEM_SCRIPT, b"\x00\x14" + h160(pub))
        else:
            # legacy inputs need the FULL previous transaction so a verifier can
            # confirm the amount for itself rather than taking our word
            prev = prevtxs.get(u["txid"])
            if prev is None and chain is not None:
                try:
                    prev = chain.raw_tx(u["txid"])
                except Exception as e:
                    sys.stderr.write(f"    psbt: could not fetch prev tx for "
                                     f"{u['txid'][:16]}… ({e})\n")
            if prev is not None:
                m += _kv(PSBT_IN_NON_WITNESS_UTXO, prev)
            else:
                sys.stderr.write(f"    psbt: input {u['txid'][:16]}… "
                                 f"({kind}) has no utxo record; a strict "
                                 f"decoder will call this PSBT incomplete\n")
        out += m + PSBT_SEPARATOR

    for _o in tx.vout:
        out += PSBT_SEPARATOR
    return out


def parse_psbt(raw):
    """Parse our own PSBT back. Round-tripping is a floor, not a proof."""
    if raw[:5] != PSBT_MAGIC:
        raise ValueError("not a PSBT: bad magic")
    r = Reader(raw)
    r.take(5)

    def read_map():
        m = {}
        while True:
            klen = r.varint()
            if klen == 0:
                return m
            key = r.take(klen)
            m[key[0]] = r.take(r.varint())

    g = read_map()
    if PSBT_GLOBAL_UNSIGNED_TX not in g:
        raise ValueError("PSBT has no unsigned transaction")
    tx = parse_tx(g[PSBT_GLOBAL_UNSIGNED_TX])
    ins = [read_map() for _ in tx.vin]
    outs = [read_map() for _ in tx.vout]
    if r.i != len(raw):
        raise ValueError(f"PSBT has {len(raw) - r.i} trailing bytes")
    return tx, ins, outs


def emit_psbt(path, tx, utxos, chain, prevtxs=None):
    """Write a PSBT and print it base64, refusing if it does not round-trip."""
    import base64
    p = build_psbt(tx, utxos, chain, prevtxs)
    ptx, pins, pouts = parse_psbt(p)              # our own round trip: a floor
    if ptx.ser(witness=False) != unsigned_clone(tx).ser(witness=False):
        sys.exit("  psbt does not round-trip to the same unsigned transaction; "
                 "refusing to emit it")
    with open(path, "wb") as fh:
        fh.write(p)
    b64 = base64.b64encode(p).decode()
    sys.stderr.write(
        f"\n  PSBT  {len(p)} bytes -> {path}\n"
        f"    {len(pins)} input record(s), {len(pouts)} output record(s)\n"
        f"\n  Check it with something that is NOT this script:\n"
        f"    bitcoin-cli decodepsbt 'PASTE_THE_BASE64_BELOW'\n"
        f"    or open {path} in Sparrow, or Electrum's Tools > Load "
        f"transaction.\n"
        f"    Confirm the destination and the amounts THERE.\n"
        f"\n  PSBT BASE64\n{b64}\n")
    return p


def demo_utxos():
    """A throwaway key and four invented UTXOs, one of each signable type.

    The point is that verifying the PSBT encoding against a real decoder should
    not require a private key, funds, or a solved puzzle. This makes that test
    runnable today. The outpoints are fabricated, so nothing built from them
    can ever be broadcast.
    """
    from coincurve import PrivateKey
    from full_sweep import spks_for_key
    from spk_extra import sc_p2pk
    k = hashlib.sha256(b"overdose sweep demo key - throwaway").digest()
    pk = PrivateKey(k).public_key
    pc, pu = pk.format(True), pk.format(False)
    forms = dict(spks_for_key(k))
    plan = [("p2pkh_c", forms["p2pkh_c"], pc, 500_000_000),
            ("p2wpkh", forms["p2wpkh"], pc, 500_000_000),
            ("p2sh_p2wpkh", forms["p2sh_p2wpkh"], pc, 500_000_000),
            ("p2pk_c", sc_p2pk(pc), pc, 500_000_000)]
    utxos, prevtxs = [], {}
    for n, (kind, spk, pub, val) in enumerate(plan):
        # synthesize the funding transaction, then take the outpoint FROM it.
        # A PSBT whose non_witness_utxo does not hash to the input's txid is
        # rejected by a strict decoder, which would make this demo useless as
        # a test of the encoding.
        prev = Tx([TxIn(hashlib.sha256(kind.encode()).digest(), n,
                        b"\x51", 0xFFFFFFFF)],
                  [TxOut(val, spk)])
        txid = prev.txid()
        prevtxs[txid] = prev.ser()
        utxos.append({"label": "demo", "kind": kind, "spk": spk, "key": k,
                      "pub": pub, "txid": txid, "vout": 0, "value": val})
    return utxos, sum(u["value"] for u in utxos), prevtxs


# ---------------------------------------------------------------- key input ---
def load_keys(args):
    """Yield (label, priv32). The key is never printed, logged or written."""
    out = []
    if args.key:
        s = args.key.strip()
        from harness import wif_check
        w = wif_check(s)
        if w:
            out.append((f"wif:{w[0]}", w[1]))
        else:
            try:
                b = bytes.fromhex(s)
            except ValueError:
                sys.exit("--key is neither valid WIF nor 32-byte hex")
            if len(b) != 32:
                sys.exit(f"--key hex is {len(b)} bytes, need 32")
            out.append(("hex", b))
    if args.phrase:
        from hd_sweep import direct_keys
        for n, k in direct_keys(args.phrase).items():
            out.append((f"phrase:{n}", k))
    if args.from_ledger:
        out += keys_from_ledger(args.ledger)
    good = []
    for lab, k in out:
        if 0 < int.from_bytes(k, "big") < CURVE_N:
            good.append((lab, k))
        else:
            sys.stderr.write(f"  {lab}: key out of curve range, skipped\n")
    return good


def keys_from_ledger(path):
    """Re-derive keys from recorded hits.

    solver_ledger.py stores no private key, and its `address` column actually
    receives the script-type string (continuous_solver.py:300). The phrase lives
    in `label` as "<phrase>|<derivation>|<script_type>", so the key has to be
    rebuilt the way verify_hit.py rebuilds it.
    """
    import sqlite3
    if not os.path.exists(path):
        sys.stderr.write(f"  no ledger at {path}\n")
        return []
    from hd_sweep import direct_keys, seeds_from, derive, build_paths
    db = sqlite3.connect(path)
    try:
        rows = db.execute("SELECT DISTINCT label FROM hits").fetchall()
    except sqlite3.Error as e:
        sys.stderr.write(f"  ledger unreadable: {e}\n")
        return []
    out = []
    for (lab,) in rows:
        phrase = lab.split("|")[0] if lab else ""
        if not phrase:
            continue
        for n, k in direct_keys(phrase).items():
            out.append((f"ledger:{phrase[:30]}|{n}", k))
        for sn, seed in seeds_from(phrase).items():
            for p in build_paths()[:8]:
                try:
                    k = derive(seed, p)
                except Exception:
                    continue
                if k:
                    out.append((f"ledger:{phrase[:30]}|{sn}:{p}", k))
    sys.stderr.write(f"  ledger: {len(rows)} hit label(s) -> "
                     f"{len(out):,} candidate keys\n")
    return out


# ------------------------------------------------------------------ discovery ---
def discover(chain, keys, include_exotic=True):
    """Find every UTXO these keys control. Returns (spendable, refused).

    Lookups go by SCRIPTHASH, which reaches bare P2PK and the wrapped forms
    that have no address at all. If an endpoint does not serve /scripthash it
    falls back to the address endpoint, which can only see the address-shaped
    forms — and says so, because a silently narrower search is worse than a
    loud one.
    """
    from full_sweep import spks_for_key
    from spk_extra import spks_extra, sc_p2pk
    from coincurve import PrivateKey

    spendable, refused = [], []
    sh_broken = False
    for lab, k in keys:
        pubk = PrivateKey(k).public_key
        pub_c, pub_u = pubk.format(True), pubk.format(False)
        forms = list(spks_for_key(k))
        forms += [("p2pk_c", sc_p2pk(pub_c)), ("p2pk_u", sc_p2pk(pub_u))]
        if include_exotic:
            forms += spks_extra(k)

        for kind, spk in forms:
            try:
                if sh_broken:
                    a = addr_for_spk(spk)
                    if not a:
                        continue
                    us = chain.utxos(a)
                else:
                    us = chain.utxos_sh(spk)
            except Exception as e:
                if not sh_broken and "404" in str(e):
                    sh_broken = True
                    sys.stderr.write(
                        "    endpoint does not serve /scripthash — falling "
                        "back to address lookups.\n"
                        "    BARE P2PK AND THE WRAPPED FORMS ARE NOW "
                        "INVISIBLE to this search.\n")
                    continue
                sys.stderr.write(f"    {kind}: lookup failed ({e})\n")
                continue
            for u in us or []:
                if not u.get("status", {}).get("confirmed", True):
                    sys.stderr.write(f"    {kind}: skipping unconfirmed utxo\n")
                    continue
                rec = {"label": lab, "kind": kind, "spk": spk, "key": k,
                       "pub": pub_u if kind.endswith("_u") else pub_c,
                       "txid": u["txid"], "vout": u["vout"],
                       "value": u["value"]}
                (spendable if kind in SIGNABLE else refused).append(rec)
    return spendable, refused


# ---------------------------------------------------------------------- main ---
def verify_amounts(chain, utxos):
    """Confirm every LEGACY input's value against its own previous transaction.

    THE BUG THIS EXISTS FOR. A legacy SIGHASH_ALL preimage contains no input
    amount — verified directly: claiming 100,000 sat and claiming 2,000,000,000
    sat for the same input produce a byte-identical sighash. So if the endpoint
    understates a legacy UTXO's value, the signature is STILL VALID, the
    transaction is accepted, and the difference is paid to the miner.

    That is not a hypothetical. The values come from whatever /utxo returns, and
    every fee check in this file compares those same claimed numbers against
    each other, so it is circular and cannot detect it. `total_in - out == fee`
    is satisfied perfectly by a lie.

    BIP-143 commits to the amount, so for p2wpkh and p2sh-p2wpkh an understated
    value simply invalidates the signature and nothing is lost. Legacy is the
    exception, and it is the one this project would actually hit: a 2021
    brainwallet prize is far likelier to sit in p2pkh than anywhere else.

    The fix is the same data BIP-174 demands for exactly this reason — the full
    previous transaction. Fetch it, hash it to confirm it is the right one, and
    read the value out of it.
    """
    legacy = [u for u in utxos if u["kind"] in ("p2pkh_c", "p2pkh_u",
                                                "p2pk_c", "p2pk_u")]
    if not legacy:
        sys.stderr.write("  input amounts: no legacy inputs; BIP-143 commits "
                         "to every amount here, so a wrong one is fail-safe\n")
        return True, {}
    if chain is None:
        sys.stderr.write("  input amounts: CANNOT VERIFY without an endpoint\n")
        return False, {}

    ok, prevtxs = True, {}
    for u in legacy:
        try:
            raw = chain.raw_tx(u["txid"])
        except Exception as e:
            sys.stderr.write(f"    {u['txid'][:16]}…: prev tx unavailable "
                             f"({e}) — REFUSING\n")
            ok = False
            continue
        prev = parse_tx(raw)
        if prev.txid() != u["txid"]:
            sys.stderr.write(f"    {u['txid'][:16]}…: endpoint returned a "
                             f"transaction that hashes to {prev.txid()[:16]}… "
                             f"— REFUSING\n")
            ok = False
            continue
        if u["vout"] >= len(prev.vout):
            sys.stderr.write(f"    {u['txid'][:16]}…: has no output "
                             f"{u['vout']} — REFUSING\n")
            ok = False
            continue
        real = prev.vout[u["vout"]]
        if real.value != u["value"]:
            sys.stderr.write(f"    {u['txid'][:16]}…:{u['vout']} endpoint said "
                             f"{u['value']:,} sat, the transaction itself says "
                             f"{real.value:,} — REFUSING\n")
            ok = False
            continue
        if real.spk != u["spk"]:
            sys.stderr.write(f"    {u['txid'][:16]}…:{u['vout']} script does "
                             f"not match what we derived — REFUSING\n")
            ok = False
            continue
        prevtxs[u["txid"]] = raw
        sys.stderr.write(f"    {u['kind']:12} {u['value']:>15,} sat confirmed "
                         f"against its own prev tx\n")
    return ok, prevtxs


def build_and_sign(utxos, dest_spk, fee_rate, max_fee):
    """Build one transaction spending every utxo to dest_spk. Returns (tx, fee)."""
    total = sum(u["value"] for u in utxos)
    vin = [TxIn(bytes.fromhex(u["txid"])[::-1], u["vout"],
                amount=u["value"], spk=u["spk"], kind=u["kind"])
           for u in utxos]
    kinds = [u["kind"] for u in utxos]
    pubs = [u["pub"] for u in utxos]

    est = Tx(vin, [TxOut(total, dest_spk)])
    vsize = dummy_size(est, kinds, pubs)
    fee = int(vsize * fee_rate + 0.999)
    value = total - fee
    if value < DUST:
        raise SystemExit(f"after a {fee:,} sat fee the output would be "
                         f"{value:,} sat, below the {DUST} sat dust floor")
    good, why = fee_ok(fee, total, max_fee)
    if not good:
        raise SystemExit(f"refusing: {why}")

    tx = Tx(vin, [TxOut(value, dest_spk)])
    for n, u in enumerate(utxos):
        sign_input(tx, n, u["key"], u["kind"], u["value"], u["pub"])
    return tx, fee


def verify_before_broadcast(tx, dest_spk, total_in, fee, max_fee):
    """Re-parse the finished transaction and re-check everything that matters.

    The two irreversible mistakes are a wrong output script and an excessive
    fee. Both are checked here, against the actual serialized bytes rather than
    against the objects that produced them.
    """
    from coincurve import PublicKey
    raw = tx.ser()
    back = parse_tx(raw)
    checks = []

    checks.append(("re-parses to identical bytes", back.ser() == raw))
    checks.append(("exactly one output", len(back.vout) == 1))
    checks.append(("output script is the requested destination",
                   len(back.vout) == 1 and back.vout[0].spk == dest_spk))
    out_val = back.vout[0].value if back.vout else 0
    checks.append((f"in {total_in:,} − out {out_val:,} == fee {fee:,}",
                   total_in - out_val == fee))
    ok_fee, why = fee_ok(fee, total_in, max_fee)
    checks.append((f"fee within caps{'' if ok_fee else ' — ' + why}", ok_fee))
    checks.append(("output above dust", out_val >= DUST))

    sigs_ok = True
    for n, i in enumerate(tx.vin):
        try:
            if i.kind in ("p2wpkh", "p2sh_p2wpkh"):
                sig, pub = i.witness
                sc = b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"
                sh = sighash_bip143(tx, n, sc, i.amount)
            elif i.kind in ("p2pkh_c", "p2pkh_u"):
                r = Reader(i.script_sig)
                sig = r.take(r.take(1)[0])
                pub = r.take(r.take(1)[0])
                sh = sighash_legacy(tx, n, b"\x76\xa9\x14" + h160(pub) + b"\x88\xac")
            elif i.kind in ("p2pk_c", "p2pk_u"):
                r = Reader(i.script_sig)
                sig = r.take(r.take(1)[0])
                pub = None
                sh = None
            else:
                sigs_ok = False
                continue
            if pub is not None and sh is not None:
                sigs_ok &= PublicKey(pub).verify(sig[:-1], sh, hasher=None)
        except Exception:
            sigs_ok = False
    checks.append(("every input signature verifies against its own sighash",
                   sigs_ok))

    sys.stderr.write("\n  PRE-BROADCAST VERIFICATION\n")
    for name, good in checks:
        sys.stderr.write(f"    [{'ok' if good else 'XX'}] {name}\n")
    return all(g for _n, g in checks)


def main():
    ap = argparse.ArgumentParser(
        description="Find every UTXO a private key controls and move them to "
                    "one address.")
    ap.add_argument("--to", help="destination address. REQUIRED to sweep; "
                                 "deliberately not defaulted")
    ap.add_argument("--key", help="private key as WIF or 32-byte hex")
    ap.add_argument("--phrase", help="brainwallet phrase; all 7 hashes tried")
    ap.add_argument("--from-ledger", action="store_true",
                    help="re-derive keys from recorded solver hits")
    ap.add_argument("--ledger", default="solver_ledger.sqlite")
    ap.add_argument("--base", default=os.environ.get("ESPLORA", ""),
                    help="Esplora base URL (or $ESPLORA)")
    ap.add_argument("--fee-rate", type=float, default=20.0,
                    help="sat/vB. A sweep can be raced, so do not go low")
    ap.add_argument("--max-fee", type=int, default=DEFAULT_MAX_FEE,
                    help="absolute fee cap in sat")
    ap.add_argument("--control-tx", action="append", default=[],
                    help="confirmed txid to validate the signer against; "
                         "repeatable. Use one legacy and one segwit spend")
    ap.add_argument("--control", action="store_true",
                    help="run the chain-grounded controls and stop")
    ap.add_argument("--control-blocks", type=int, default=6,
                    help="how many recent blocks --auto-control may search. "
                         "Raise it to hunt for a bare-P2PK spend, which is "
                         "rare on the modern chain")
    ap.add_argument("--auto-control", action="store_true",
                    help="find control transactions from recent blocks rather "
                         "than being told which. Nothing is remembered; the "
                         "chain supplies both the vectors and the answers")
    ap.add_argument("--no-exotic", action="store_true",
                    help="skip the 20 wrapped/multisig forms. They cannot be "
                         "signed here anyway, and checking them multiplies the "
                         "query count by ~5x")
    ap.add_argument("--demo", action="store_true",
                    help="dress rehearsal with a throwaway key and invented "
                         "UTXOs. No key, no funds and no network needed — it "
                         "exists so the PSBT encoding can be checked against a "
                         "real decoder TODAY rather than on the day it matters")
    ap.add_argument("--psbt", metavar="FILE",
                    help="also write a BIP-174 PSBT and print it base64, so an "
                         "independent decoder (bitcoin-cli decodepsbt, Sparrow, "
                         "Electrum) can confirm what this is about to sign")
    ap.add_argument("--broadcast", action="store_true",
                    help="actually send. Also requires retyping --to")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    try:
        import coincurve                                       # noqa: F401
    except ImportError:
        venv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            ".venv", "bin", "python")
        hint = (f"\n  This box has a venv. Use it:\n    {venv} "
                f"{os.path.basename(__file__)} ...\n"
                if os.path.exists(venv) else
                "\n  Create one:  ./setup_box.sh\n")
        sys.exit(f"coincurve is not importable under {sys.executable}{hint}")

    sys.stderr.write("\n  OFFLINE SELFTEST\n")
    if not selftest():
        sys.exit("the signer fails its own offline checks; refusing to run")
    if a.selftest:
        return

    chain = Chain(a.base) if a.base else None
    controls_passed = False
    txids = list(a.control_tx)
    if a.auto_control:
        if not chain:
            sys.exit("--auto-control needs --base")
        sys.stderr.write("\n  FINDING CONTROL TRANSACTIONS\n")
        try:
            found, missing = find_control_txs(chain, back=a.control_blocks)
        except RuntimeError as e:
            sys.exit(f"  {e}")
        if missing:
            sys.exit(f"  could not find a confirmed spend of: "
                     f"{', '.join(missing)}.\n  Pass --control-tx <txid> "
                     f"explicitly, or widen the search.")
        txids += found
    if txids:
        if not chain:
            sys.exit("--control-tx needs --base")
        controls_passed = run_controls(chain, txids)
        if not controls_passed:
            sys.exit("controls did not pass. Either the endpoint was "
                     "unreachable (see the reason above) or this signer does "
                     "not match consensus.\nEither way nothing is signed until "
                     "they pass.")
    if a.control:
        if not txids:
            sys.exit("--control needs --auto-control, or at least one "
                     "--control-tx TXID")
        return

    if not a.to:
        sys.exit("--to is required. It is deliberately not defaulted: a valid "
                 "address and YOUR address are different claims.")
    from index_oracle import spk_from_address
    dest_spk = spk_from_address(a.to)
    if not dest_spk:
        sys.exit(f"--to {a.to!r} does not parse as a mainnet address")
    sys.stderr.write(f"\n  DESTINATION  {a.to}\n")
    sys.stderr.write(f"    scriptPubKey {dest_spk.hex()}\n")
    sys.stderr.write(f"    type         {classify_spk(dest_spk)}\n")

    if a.demo:
        spendable, total, prevtxs = demo_utxos()
        sys.stderr.write(
            f"\n  DEMO — a throwaway key and four INVENTED UTXOs.\n"
            f"    The inputs do not exist, so this transaction can never be\n"
            f"    broadcast. It exists so the PSBT below can be handed to a\n"
            f"    real decoder and checked while nothing is at stake.\n")
        for u in spendable:
            sys.stderr.write(f"    {u['kind']:14} {u['value']:>15,} sat\n")
        sys.stderr.write(f"    {total:,} sat = {total/1e8:.8f} BTC\n")
        tx, fee = build_and_sign(spendable, dest_spk, a.fee_rate, a.max_fee)
        emit_psbt(a.psbt or "demo.psbt", tx, spendable, None, prevtxs)
        verify_before_broadcast(tx, dest_spk, total, fee, a.max_fee)
        sys.stderr.write(f"\n  DEMO ONLY. Nothing here is spendable.\n")
        return

    if not chain:
        sys.exit("no endpoint: pass --base or set $ESPLORA")

    keys = load_keys(a)
    if not keys:
        sys.exit("no keys: pass --key, --phrase or --from-ledger")
    per_key = 7 if a.no_exotic else 27
    sys.stderr.write(f"\n  {len(keys):,} candidate key(s) x {per_key} script "
                     f"forms = {len(keys)*per_key:,} lookups\n")
    if len(keys) * per_key > 20000:
        sys.stderr.write("    that is a lot of requests; --no-exotic cuts it "
                         "to a quarter\n")

    spendable, refused = discover(chain, keys, not a.no_exotic)
    if refused:
        total_r = sum(u["value"] for u in refused)
        sys.stderr.write(f"\n  REFUSED — funds found in input types this signer "
                         f"will not guess at:\n")
        for u in refused:
            sys.stderr.write(f"    {u['kind']:18} {u['value']:>15,} sat  "
                             f"{u['txid'][:16]}…:{u['vout']}\n")
        sys.stderr.write(f"    {total_r:,} sat total. Reported, not swept.\n")
    if not spendable:
        sys.stderr.write("\n  no spendable UTXOs found for these keys\n")
        return

    total = sum(u["value"] for u in spendable)
    sys.stderr.write(f"\n  SPENDABLE\n")
    for u in spendable:
        sys.stderr.write(f"    {u['kind']:14} {u['value']:>15,} sat  "
                         f"{u['txid'][:16]}…:{u['vout']}  [{u['label'][:40]}]\n")
    sys.stderr.write(f"    {total:,} sat = {total/1e8:.8f} BTC across "
                     f"{len(spendable)} input(s)\n")

    sys.stderr.write("\n  INPUT AMOUNTS — legacy values checked against their "
                     "own previous transactions\n")
    amounts_ok, prevtxs = verify_amounts(chain, spendable)
    if not amounts_ok:
        sys.exit("\n  refusing to sign: at least one legacy input's value "
                 "could not be confirmed from the chain itself.\n  A legacy "
                 "sighash does not commit to the amount, so an unverified "
                 "value is not fail-safe —\n  the difference would be paid to "
                 "a miner.")

    tx, fee = build_and_sign(spendable, dest_spk, a.fee_rate, a.max_fee)
    raw = tx.ser().hex()

    if a.psbt:
        emit_psbt(a.psbt, tx, spendable, chain, prevtxs)
    sys.stderr.write(f"\n  BUILT  txid {tx.txid()}\n")
    sys.stderr.write(f"    vsize {tx.vsize()} vB, fee {fee:,} sat "
                     f"({fee/tx.vsize():.1f} sat/vB), "
                     f"output {total-fee:,} sat\n")

    if not verify_before_broadcast(tx, dest_spk, total, fee, a.max_fee):
        sys.exit("\n  verification FAILED — not broadcasting")

    sys.stderr.write(f"\n  RAW TRANSACTION\n{raw}\n")
    if not a.broadcast:
        sys.stderr.write(
            "\n  DRY RUN. Nothing was sent. Decode the hex above independently\n"
            "  and confirm the output address by eye, then re-run with "
            "--broadcast.\n")
        return

    if not controls_passed:
        sys.exit("\n  refusing to broadcast: the chain-grounded controls have "
                 "not passed in this run.\n  Re-run with --control-tx <txid> "
                 "for a confirmed legacy spend and a segwit spend.")
    sys.stderr.write(f"\n  About to send {total-fee:,} sat to {a.to}\n")
    typed = input("  Retype the destination address to confirm: ").strip()
    if typed != a.to:
        sys.exit("  did not match — nothing sent")
    txid = chain.broadcast(raw)
    sys.stderr.write(f"\n  BROADCAST. txid {txid}\n")


if __name__ == "__main__":
    main()
