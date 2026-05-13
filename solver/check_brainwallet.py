#!/usr/bin/env python3
"""
Brainwallet checker.

Reads candidate passphrases (one per line) from argv[1] or stdin, derives
multiple Bitcoin addresses for each phrase, and queries blockstream.info to
see whether any of them have ever received funds.

Address variants per phrase:
    sha256(phrase)        -> compressed P2PKH      (1...)
    sha256(phrase)        -> uncompressed P2PKH    (1...)
    sha256(phrase)        -> compressed P2WPKH     (bc1q...)
    sha256(sha256(phrase))-> compressed P2PKH      (1...)
    sha256(sha256(phrase))-> uncompressed P2PKH    (1...)
    sha256(sha256(phrase))-> compressed P2WPKH     (bc1q...)
"""

import sys
import os
import time
import json
import hashlib
import urllib.request
import urllib.error

import base58
from ecdsa import SigningKey, SECP256k1

HITS_PATH = "/home/user/overdose/solver/hits.tsv"
ESPLORA_BASE = "https://blockstream.info/api/address/"
MIN_INTERVAL = 0.22  # seconds between API calls -> < 5 req/s
TIMEOUT = 15


# ---------------------------------------------------------------------------
# bech32 (BIP-0173) - reference implementation, condensed
# ---------------------------------------------------------------------------
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= GEN[i]
    return chk


def _bech32_hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _bech32_create_checksum(hrp, data):
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _bech32_encode(hrp, data):
    combined = data + _bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join(BECH32_CHARSET[d] for d in combined)


def _convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def segwit_encode(hrp, witver, witprog):
    ret = _bech32_encode(hrp, [witver] + _convertbits(list(witprog), 8, 5))
    return ret


# ---------------------------------------------------------------------------
# Bitcoin address helpers
# ---------------------------------------------------------------------------
def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def ripemd160(b: bytes) -> bytes:
    h = hashlib.new("ripemd160")
    h.update(b)
    return h.digest()


def hash160(b: bytes) -> bytes:
    return ripemd160(sha256(b))


def privkey_to_pubkey(priv32: bytes):
    """Return (compressed_pubkey, uncompressed_pubkey)."""
    # ecdsa requires 1 <= secret < N
    n = SECP256k1.order
    secret = int.from_bytes(priv32, "big")
    if secret == 0 or secret >= n:
        return None, None
    sk = SigningKey.from_string(priv32, curve=SECP256k1)
    vk = sk.get_verifying_key()
    point = vk.pubkey.point
    x = point.x()
    y = point.y()
    x_bytes = x.to_bytes(32, "big")
    y_bytes = y.to_bytes(32, "big")
    prefix = b"\x03" if (y & 1) else b"\x02"
    compressed = prefix + x_bytes
    uncompressed = b"\x04" + x_bytes + y_bytes
    return compressed, uncompressed


def p2pkh_address(pubkey_bytes: bytes) -> str:
    h = hash160(pubkey_bytes)
    payload = b"\x00" + h
    checksum = sha256(sha256(payload))[:4]
    return base58.b58encode(payload + checksum).decode()


def p2wpkh_address(compressed_pubkey: bytes) -> str:
    h = hash160(compressed_pubkey)
    return segwit_encode("bc", 0, h)


def derive_addresses(phrase: str):
    """
    Yield (variant_label, address) tuples for a phrase.

    Variants:
        sha256_p2pkh_c, sha256_p2pkh_u, sha256_p2wpkh,
        dsha256_p2pkh_c, dsha256_p2pkh_u, dsha256_p2wpkh
    """
    encoded = phrase.encode("utf-8")
    priv_single = sha256(encoded)
    priv_double = sha256(priv_single)

    for label_prefix, priv in (("sha256", priv_single), ("dsha256", priv_double)):
        comp, uncomp = privkey_to_pubkey(priv)
        if comp is None:
            continue
        yield (f"{label_prefix}_p2pkh_c", p2pkh_address(comp))
        yield (f"{label_prefix}_p2pkh_u", p2pkh_address(uncomp))
        yield (f"{label_prefix}_p2wpkh", p2wpkh_address(comp))


# ---------------------------------------------------------------------------
# Blockstream API
# ---------------------------------------------------------------------------
_last_call_ts = [0.0]


def _rate_limit():
    now = time.monotonic()
    delta = now - _last_call_ts[0]
    if delta < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - delta)
    _last_call_ts[0] = time.monotonic()


def fetch_address(address: str, retries: int = 1):
    """
    Return dict with funded_sats, spent_sats, tx_count, or None on hard failure.
    """
    url = ESPLORA_BASE + address
    attempt = 0
    while True:
        _rate_limit()
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "brainwallet-check/1.0"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
            cs = data.get("chain_stats", {}) or {}
            ms = data.get("mempool_stats", {}) or {}
            funded = int(cs.get("funded_txo_sum", 0)) + int(ms.get("funded_txo_sum", 0))
            spent = int(cs.get("spent_txo_sum", 0)) + int(ms.get("spent_txo_sum", 0))
            tx_count = int(cs.get("tx_count", 0)) + int(ms.get("tx_count", 0))
            return {"funded": funded, "spent": spent, "tx_count": tx_count}
        except (urllib.error.URLError, urllib.error.HTTPError,
                TimeoutError, json.JSONDecodeError, OSError) as e:
            if attempt >= retries:
                print(f"[error] {address}: {e}", file=sys.stderr)
                return None
            backoff = 1.5 * (attempt + 1)
            print(f"[warn] {address}: {e}; retry in {backoff:.1f}s",
                  file=sys.stderr)
            time.sleep(backoff)
            attempt += 1


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def iter_phrases(source):
    for raw in source:
        line = raw.rstrip("\n").rstrip("\r")
        if not line:
            continue
        yield line


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        phrases = list(iter_phrases(open(path, "r", encoding="utf-8")))
    else:
        phrases = list(iter_phrases(sys.stdin))

    total = len(phrases)
    print(f"[info] {total} candidate phrases", file=sys.stderr)

    hits = 0
    checked = 0

    # Append mode so multiple runs accumulate; create file if missing.
    new_file = not os.path.exists(HITS_PATH)
    hits_f = open(HITS_PATH, "a", encoding="utf-8")
    if new_file:
        hits_f.write("phrase\taddress_type\taddress\tfunded_sats\tspent_sats\ttx_count\n")
        hits_f.flush()

    try:
        for phrase in phrases:
            for variant, address in derive_addresses(phrase):
                info = fetch_address(address)
                if info is None:
                    continue
                if info["funded"] > 0:
                    line = (f"{phrase}\t{variant}\t{address}\t"
                            f"{info['funded']}\t{info['spent']}\t{info['tx_count']}")
                    print(line, flush=True)
                    hits_f.write(line + "\n")
                    hits_f.flush()
                    hits += 1
            checked += 1
            if checked % 100 == 0:
                print(f"[progress] checked {checked}/{total}, {hits} hits",
                      file=sys.stderr)
        print(f"[done] checked {checked}/{total}, {hits} hits", file=sys.stderr)
    finally:
        hits_f.close()


if __name__ == "__main__":
    main()
