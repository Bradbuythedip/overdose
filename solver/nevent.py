CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def bech32_decode(bech):
    bech = bech.strip()
    pos = bech.rfind('1')
    hrp, data = bech[:pos], bech[pos+1:]
    dec = [CHARSET.find(c) for c in data]
    assert all(d >= 0 for d in dec), "bad charset"
    return hrp, dec[:-6]   # drop checksum

def convertbits(data, frombits, tobits, pad=True):
    acc = 0; bits = 0; ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    return ret

NEVENT = "nevent1qqsz6u7hzvsatm5r9uts7sxuqfvpyuv25ee6ffav7r94xyn98uk3ysqpzpmhxue69uhkummnw3ezuamfdejsdzqq47"
hrp, data5 = bech32_decode(NEVENT)
raw = bytes(convertbits(data5, 5, 8, False))
print("hrp:", hrp, " tlv bytes:", len(raw))

TLV = {0: "event id", 1: "relay", 2: "author pubkey", 3: "kind"}
i = 0
while i < len(raw):
    t = raw[i]; l = raw[i+1]; v = raw[i+2:i+2+l]; i += 2 + l
    name = TLV.get(t, f"type{t}")
    if t in (0, 2):
        print(f"{name:14s}: {v.hex()}")
    elif t == 1:
        print(f"{name:14s}: {v.decode('ascii', 'replace')}")
    elif t == 3:
        print(f"{name:14s}: {int.from_bytes(v,'big')}")
    else:
        print(f"{name:14s}: {v.hex()}")
