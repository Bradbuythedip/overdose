# The scoreboard measures the wrong thing (2026-09-13)

This is the most consequential error found in the project, and it is in the
headline claim rather than in any one sweep.

## The claim

`STATUS.md`, above the cumulative table:

> All scored against the full 56,795,328-address funded index via the offline
> oracle, **so a hit would register regardless of balance, spend history or
> funding date.**

That is false. `address_map.bin` is the UTXO set: addresses holding coins
**now**. An address funded in 2021 and swept in 2022 has no entry in it. The
same file says so 100 lines further down, where an earlier session records that
a positive control was invalid "because address_map.bin holds only
currently-funded addresses and every famous brainwallet was swept to zero years
ago (8/8 probed empty)". The document contradicts itself and the scoreboard
rests on the wrong half.

## The supposed fix does not fix it

`hist_index.py` was written to close exactly this gap. Its docstring:

> if anyone cracked this key and swept the 20 BTC at any point ... every sweep
> would report 0 hits even when handed the correct private key. The fix: the
> Pymmdrza/Rich-Address-Wallet dump is an APRIL 2023 snapshot ... So it is a
> record of addresses funded at that time, regardless of what happened since.

The reasoning is half right. A rich list from April 2023 does catch an address
that held a balance **on that date** and is empty today. It cannot catch an
address funded and swept **before** that date, because a drained address has
zero balance and does not appear on a rich list at all.

Its selftest checked three addresses that were funded at snapshot time and
confirmed they were present. It never checked a known-**swept** address, so the
one control that would have exposed the limitation was never run.

## Running that control

32 canonical brainwallet phrases — `satoshi`, `password`, `correct horse
battery staple`, `to be or not to be`, and the rest of the textbook set, every
one of which demonstrably held coins at some point and was drained by
brainwallet crackers years ago — derived to P2PKH in both compressed and
uncompressed form:

```
64 addresses
  present in CURRENT index (holds coins now):        0
  present in HISTORICAL index (held coins Apr 2023): 0
  GENESIS control                                    present in both
```

Zero of sixty-four. The two indices are two **instants**, not an interval.

| oracle | actually answers |
|---|---|
| `address_map.bin` | "holds coins today" |
| `hist_index` (Apr-2023 rich list) | "held a top-1M balance in April 2023" |
| neither | **"was ever funded"** |

## What this does to every result in this project

Every "0 funded hits" in this repo — on the order of 150 million derived
addresses — must be restated:

> No derivation from these pages produces an address that holds coins today, or
> that held a large balance in April 2023.

It does **not** say, and this repo cannot say with the data it has, that no
derivation produces an address that was ever funded.

That distinction is not academic here, because the scenario it fails to cover
is the *most likely one*. A key printed in a magazine is weak by construction:
the serial reading is ~26.6 bits, a brainwallet phrase from the article is a
dictionary attack, and automated brainwallet crackers sweep new brainwallets
within seconds of funding. If Keiser derived the prize from anything in this
column, the overwhelmingly probable history is that it was drained long before
the March 2023 tweet claiming "nobody's figured it out yet" — and by
construction, we would see exactly what we see: nulls everywhere.

Every negative in this project is therefore consistent with three states we
still cannot separate:

1. the key never existed
2. it existed and was never funded
3. **it was funded and swept before April 2023** — untested, and the most
   probable of the three

## What would actually close it

A true ever-funded set needs every output ever created, not a balance snapshot.
That means a full chain scan (or an ever-used-address dump), neither of which
is in this tree and neither of which is reachable without network access. The
2.2M lines of embedded chain text used for the OP_RETURN scan are text from
blocks, not an address set, and do not substitute.

The one oracle here that is genuinely chain-independent is the **format
checksum** — WIF, BIP38, Base58Check. It certifies a derivation whether or not
the coins are still there, which is why `serial_oracle.py` was built. It only
works when the target checksum is known, which is why it needs something like
the serial to be a real checksum, and that has been tested and is null.

## Corrections applied

- `STATUS.md`: the "regardless of balance, spend history or funding date" claim
  is removed and replaced with what the indices actually answer.
- `hist_index.py`: docstring corrected, and its selftest now includes the
  known-swept brainwallet control, so the module reports its true semantics and
  cannot silently over-claim again.
