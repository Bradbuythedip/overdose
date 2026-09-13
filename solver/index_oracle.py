#!/usr/bin/env python3
"""
Offline balance oracle over address_map.bin (56.8M funded scripthashes).

WHY: every chain lookup so far needed network (blockstream/Alchemy), and this
sandbox's egress policy blocks every Bitcoin API host. But address_map.bin is
a complete local snapshot: 132-byte header + 40-byte records of
sha256(scriptPubKey) || balance_sats, sorted by scripthash. That is a full
offline oracle for "is this address funded, and with how much".

Design: load the first 8 bytes of each scripthash into a sorted uint64 numpy
array (454 MB) and use vectorized searchsorted. An 8-byte prefix over 56.8M
records has a false-positive rate of ~3e-12; every prefix hit is re-verified
against the full 32 bytes on disk before being reported.

The byte-order convention (plain sha256 vs Electrum's reversed) is NOT assumed
-- it is determined empirically by probing known-funded addresses, and the
module refuses to answer queries until a positive control has passed.
"""
import hashlib, os, sys

import numpy as np

MAP = "/tmp/address_map.bin"
NPY = "/tmp/address_map_prefix.npy"
HDR = 132
REC = 40

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


# ---------- address -> scriptPubKey ----------
def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def _bech32_polymod(values):
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if ((top >> i) & 1) else 0
    return chk


def _hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convertbits(data, frm, to, pad=True):
    acc = bits = 0
    ret = []
    maxv = (1 << to) - 1
    for v in data:
        acc = (acc << frm) | v
        bits += frm
        while bits >= to:
            bits -= to
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (to - bits)) & maxv)
    elif not pad and (bits >= frm or ((acc << (to - bits)) & maxv)):
        return None
    return ret


def bech32_decode(addr):
    """Return (witver, program_bytes) or None."""
    a = addr.lower()
    pos = a.rfind("1")
    if pos < 1 or pos + 7 > len(a):
        return None
    hrp, data_part = a[:pos], a[pos + 1:]
    try:
        data = [BECH32_CHARSET.index(c) for c in data_part]
    except ValueError:
        return None
    const = _bech32_polymod(_hrp_expand(hrp) + data)
    if const not in (1, 0x2BC830A3):          # bech32 / bech32m
        return None
    witver = data[0]
    prog = _convertbits(data[1:-6], 5, 8, False)
    if prog is None:
        return None
    return witver, bytes(prog)


def spk_from_address(addr):
    """scriptPubKey bytes for any mainnet address type, or None."""
    if addr.startswith(("bc1", "BC1")):
        d = bech32_decode(addr)
        if not d:
            return None
        witver, prog = d
        op = 0x00 if witver == 0 else 0x50 + witver
        return bytes([op, len(prog)]) + prog
    try:
        raw = b58decode(addr)
    except ValueError:
        return None
    if len(raw) != 25:
        return None
    body, chk = raw[:21], raw[21:]
    if hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4] != chk:
        return None
    ver, h160 = body[0], body[1:]
    if ver == 0x00:
        return b"\x76\xa9\x14" + h160 + b"\x88\xac"
    if ver == 0x05:
        return b"\xa9\x14" + h160 + b"\x87"
    return None


# ---------- scriptPubKey -> scripthash (convention resolved at runtime) ----------
def sh_plain(spk):
    return hashlib.sha256(spk).digest()


def sh_reversed(spk):
    return hashlib.sha256(spk).digest()[::-1]


class Oracle:
    def __init__(self, path=MAP, npy=NPY, verbose=True):
        self.path = path
        self.n = (os.path.getsize(path) - HDR) // REC
        self.f = open(path, "rb")
        self.verbose = verbose
        self.prefix = self._load_prefix(npy)
        self.sh = None                     # resolved by calibrate()

    def _load_prefix(self, npy):
        if os.path.exists(npy):
            if self.verbose:
                sys.stderr.write(f"loading prefix index {npy}\n")
            return np.load(npy, mmap_mode="r")
        if self.verbose:
            sys.stderr.write(f"building prefix index over {self.n:,} records "
                             "(one-time, ~1 min)\n")
        out = np.empty(self.n, dtype=">u8")
        self.f.seek(HDR)
        CH = 1 << 20                        # records per chunk
        done = 0
        while done < self.n:
            k = min(CH, self.n - done)
            buf = np.frombuffer(self.f.read(k * REC), dtype=np.uint8)
            buf = buf.reshape(k, REC)[:, :8].copy()
            out[done:done + k] = buf.view(">u8").reshape(k)
            done += k
            if self.verbose and done % (16 << 20) < CH:
                sys.stderr.write(f"  {done:,}/{self.n:,}\n")
        out = out.astype("<u8") if False else out
        np.save(npy, out)
        if self.verbose:
            sys.stderr.write(f"saved {npy}\n")
        return np.load(npy, mmap_mode="r")

    def _record(self, i):
        self.f.seek(HDR + i * REC)
        r = self.f.read(REC)
        return r[:32], int.from_bytes(r[32:40], "little")

    def _lookup_hash(self, h32):
        """Exact lookup of a full 32-byte scripthash -> balance sats or None."""
        key = np.frombuffer(h32[:8], dtype=">u8")[0]
        lo = int(np.searchsorted(self.prefix, key, side="left"))
        hi = int(np.searchsorted(self.prefix, key, side="right"))
        for i in range(lo, hi):
            sh, bal = self._record(i)
            if sh == h32:
                return bal
        return None

    def calibrate(self):
        """Determine the scripthash byte order using known-funded addresses.

        Refuses to proceed unless one convention resolves ALL controls. A null
        from this oracle is meaningless until it has produced a known positive.
        """
        controls = [
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",   # genesis coinbase
            "12ib7dApVFvg82TXKycWBNpN8kFyiAN1dr",   # long-standing large holder
            "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r",   # Bitfinex cold (P2SH)
            "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",  # P2WSH
        ]
        for name, fn in (("sha256", sh_plain), ("sha256-reversed", sh_reversed)):
            got = []
            for a in controls:
                spk = spk_from_address(a)
                got.append(None if spk is None else self._lookup_hash(fn(spk)))
            hits = sum(1 for g in got if g is not None)
            if self.verbose:
                sys.stderr.write(f"  convention {name}: {hits}/{len(controls)} controls found\n")
                for a, g in zip(controls, got):
                    sys.stderr.write(f"    {a[:24]:24} -> "
                                     f"{'MISS' if g is None else f'{g/1e8:.4f} BTC'}\n")
            if hits == len(controls):
                self.sh = fn
                if self.verbose:
                    sys.stderr.write(f"CALIBRATED: scripthash = {name}\n")
                return True
        sys.stderr.write("CALIBRATION FAILED - oracle unusable, refusing to answer\n")
        return False

    def balance(self, addr):
        """Balance in sats for an address, or None if not in the funded set."""
        if self.sh is None:
            raise RuntimeError("oracle not calibrated")
        spk = spk_from_address(addr)
        if spk is None:
            return None
        return self._lookup_hash(self.sh(spk))

    # ---- bulk interface used by the sweep ----
    def contains_spks(self, spks):
        """Vectorized: given a list of scriptPubKey bytes, return list of
        (index, balance) for those present in the funded set."""
        if self.sh is None:
            raise RuntimeError("oracle not calibrated")
        hs = [self.sh(s) for s in spks]
        keys = np.frombuffer(b"".join(h[:8] for h in hs), dtype=">u8")
        lo = np.searchsorted(self.prefix, keys, side="left")
        hi = np.searchsorted(self.prefix, keys, side="right")
        out = []
        for j in np.nonzero(hi > lo)[0]:
            j = int(j)
            for i in range(int(lo[j]), int(hi[j])):
                sh, bal = self._record(i)
                if sh == hs[j]:
                    out.append((j, bal))
                    break
        return out


if __name__ == "__main__":
    o = Oracle()
    if not o.calibrate():
        sys.exit(1)
    for a in sys.argv[1:]:
        b = o.balance(a)
        print(f"{a}\t{'NOT FUNDED' if b is None else f'{b} sats ({b/1e8:.8f} BTC)'}")
