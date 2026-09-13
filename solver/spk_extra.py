#!/usr/bin/env python3
"""
The script types every sweep in this project has been missing.

WHAT WAS COVERED
full_sweep.spks_for_key derives exactly five scriptPubKeys per private key:
P2PKH compressed, P2PKH uncompressed, P2WPKH, P2SH-P2WPKH, P2TR. All five are
"address-shaped" single-key forms.

WHAT WAS NOT, AND THE CONTROL THAT SHOWS IT
Bare P2PK — a raw pubkey output, `<len> <pubkey> OP_CHECKSIG` — is not an
address at all, and it is missing from BOTH derivation and index. Measured
three ways against the offline index:

    block 1 coinbase P2PK (unspent 50 BTC)   NOT in index
    the same key as P2PKH                    FUNDED 1.35248007 BTC
    a P2SH control                           FUNDED 20.00000000 BTC

So the index is address-derived. If the prize sits in a bare P2PK output, no
sweep in this project could ever have found it, whatever the derivation — and
that is a limit of the data source, not something more compute fixes. It is
also a low-probability region: P2PK fell out of use for payments around 2012,
and a wallet funded 2021-2023 would not use it. Recorded as unfalsifiable-here
rather than as covered.

P2SH and P2WSH outputs ARE in the index, so everything wrapped in them is
reachable, and that is what this module adds:

    p2sh_p2pk        P2SH(<pk> CHECKSIG)              compressed + uncompressed
    p2sh_p2pkh       P2SH(DUP HASH160 <h> EQUALVERIFY CHECKSIG)
    p2sh_ms_1of1     P2SH(1 <pk> 1 CHECKMULTISIG)     compressed + uncompressed
    p2sh_ms_1of2_cu  P2SH(1 <pk_c> <pk_u> 2 CHECKMULTISIG)
    p2sh_ms_2of2_cu  P2SH(2 <pk_c> <pk_u> 2 CHECKMULTISIG)
    p2wsh_p2pk       P2WSH(<pk> CHECKSIG)
    p2wsh_ms_1of1    P2WSH(1 <pk> 1 CHECKMULTISIG)
    p2sh_p2wsh_*     P2SH(P2WSH(...)) for both of the above

ON "KEYS, PLURAL" AND MULTISIG
Keiser said keys plural, which invites a multisig reading. It is worth being
clear that real k-of-n multisig with several distinct hidden keys makes the
puzzle HARDER, not easier: the address depends on every key and their exact
order, so every extraction has to be right simultaneously and nothing is
verifiable until all of them are. Such a scheme cannot be brute-forced from one
correct fragment. What IS testable is the degenerate family above, where the
whole redeemScript is a function of a single key — 1-of-1, and the pairings a
setter might build from one key's own compressed and uncompressed forms. Those
are enumerated; genuine multi-key multisig is not, and cannot be.

  python3 spk_extra.py --selftest
"""
import hashlib
import sys

from coincurve import PrivateKey

from hd_sweep import h160


def _push(b):
    """Minimal push opcode for a data element of this length."""
    n = len(b)
    if n < 0x4c:
        return bytes([n]) + b
    if n <= 0xff:
        return b"\x4c" + bytes([n]) + b
    raise ValueError("push too long for this use")


def p2sh(script):
    return b"\xa9\x14" + h160(script) + b"\x87"


def p2wsh(script):
    return b"\x00\x20" + hashlib.sha256(script).digest()


def sc_p2pk(pub):
    return _push(pub) + b"\xac"


def sc_p2pkh(pub):
    return b"\x76\xa9\x14" + h160(pub) + b"\x88\xac"


def sc_multisig(k, pubs):
    if not 1 <= k <= len(pubs) <= 15:
        raise ValueError("bad multisig shape")
    out = bytes([0x50 + k])
    for p in pubs:
        out += _push(p)
    return out + bytes([0x50 + len(pubs)]) + b"\xae"


def spks_extra(priv32):
    """(script_type, scriptPubKey) for the wrapped forms, single-key only."""
    try:
        sk = PrivateKey(priv32)
    except Exception:
        return []
    pub = sk.public_key
    pc = pub.format(compressed=True)
    pu = pub.format(compressed=False)

    out = []
    for tag, pk in (("c", pc), ("u", pu)):
        s_pk = sc_p2pk(pk)
        s_ms = sc_multisig(1, [pk])
        out.append((f"p2sh_p2pk_{tag}", p2sh(s_pk)))
        out.append((f"p2sh_p2pkh_{tag}", p2sh(sc_p2pkh(pk))))
        out.append((f"p2sh_ms1of1_{tag}", p2sh(s_ms)))
        out.append((f"p2wsh_p2pk_{tag}", p2wsh(s_pk)))
        out.append((f"p2wsh_ms1of1_{tag}", p2wsh(s_ms)))
        out.append((f"p2sh_p2wsh_p2pk_{tag}", p2sh(p2wsh(s_pk))))
        out.append((f"p2sh_p2wsh_ms1of1_{tag}", p2sh(p2wsh(s_ms))))
    # pairings a setter could build from ONE key's two encodings
    for k in (1, 2):
        s = sc_multisig(k, [pc, pu])
        out.append((f"p2sh_ms{k}of2_cu", p2sh(s)))
        out.append((f"p2wsh_ms{k}of2_cu", p2wsh(s)))
        s2 = sc_multisig(k, [pu, pc])
        out.append((f"p2sh_ms{k}of2_uc", p2sh(s2)))
    return out


def selftest():
    """Wrapper machinery must reproduce a known P2SH-P2WPKH address, script
    encodings must match hand-computed bytes, and P2PK must be shown absent
    from the index while its P2PKH twin is present."""
    ok = True
    from index_oracle import Oracle, spk_from_address

    # 1. The P2SH wrapper, validated end-to-end against a published vector.
    #    BIP-143's key gives P2SH-P2WPKH 37VucYSaXLCAsxYyAPfbSi9eh4iEcbShgf.
    k = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000001")
    pc = PrivateKey(k).public_key.format(compressed=True)
    want = spk_from_address("3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN")
    got = p2sh(b"\x00\x14" + h160(pc))
    sys.stderr.write(f"  P2SH(P2WPKH) for privkey=1 -> {got.hex()}\n")
    sys.stderr.write(f"  expected from address        {want.hex() if want else None}\n")
    ok &= (want == got)
    sys.stderr.write(f"  P2SH wrapper: {'OK' if want == got else 'FAIL'}\n")

    # 2. Script encodings, hand-checked.
    ms = sc_multisig(1, [pc])
    exp = bytes([0x51]) + bytes([len(pc)]) + pc + bytes([0x51]) + b"\xae"
    sys.stderr.write(f"  1-of-1 multisig script: "
                     f"{'OK' if ms == exp else 'FAIL'} ({ms[:4].hex()}...)\n")
    ok &= ms == exp
    pk = sc_p2pk(pc)
    ok &= pk == bytes([len(pc)]) + pc + b"\xac"
    sys.stderr.write(f"  P2PK script: {'OK' if pk[-1] == 0xac else 'FAIL'}\n")
    wsh_ok = p2wsh(ms)[:2] == bytes([0x00, 0x20]) and len(p2wsh(ms)) == 34
    sys.stderr.write(f"  P2WSH is 0x0020||sha256(script): "
                     f"{'OK' if wsh_ok else 'FAIL'}\n")
    ok &= wsh_ok

    # 3. The blind spot, demonstrated rather than asserted.
    o = Oracle(verbose=False)
    if o.calibrate():
        PUB1 = bytes.fromhex(
            "0496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be6"
            "3c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342"
            "c858ee")
        spks = [sc_p2pk(PUB1),
                spk_from_address("12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX")]
        d = dict(o.contains_spks(spks))
        sys.stderr.write(f"  block1 P2PK in index: "
                         f"{'yes' if 0 in d else 'NO (blind spot confirmed)'}\n")
        sys.stderr.write(f"  block1 P2PKH in index: "
                         f"{'yes ' + format(d[1]/1e8, '.8f') + ' BTC' if 1 in d else 'NO'}\n")
        ok &= (0 not in d) and (1 in d)

    n = len(spks_extra(k))
    sys.stderr.write(f"  {n} extra scriptPubKeys per key\n")
    ok &= n >= 20
    sys.stderr.write("  SELFTEST " + ("PASS\n" if ok else "FAIL\n"))
    return ok


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)
