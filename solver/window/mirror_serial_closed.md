# The mirrored serial, through the whole stack this time (2026-09-14)

## What was actually true before

"The mirror serial was swept" was being quoted as settled. It was true of a
narrow slice.

`note_check.py` does test `A41714867LC`. But it checks **four script forms** --
P2PKH compressed and uncompressed, P2WPKH, P2SH-P2WPKH -- and **direct hashes
only**. It never touched:

| never tested against a mirrored reading | why it matters |
|---|---|
| P2TR (Taproot) | the article carries a segwit/BIP-84 hint |
| bare P2PK | how an early-era key would have been locked |
| the 20 wrapped/multisig forms in `spk_extra` | |
| **any HD derivation** | no BIP-32/39/44/49/84/86 seed was ever built from a mirrored reading |

That last row is the real gap. Every mirrored reading had only ever been
hashed directly.

## What was run

36 readings x (7 direct hashes + 5 seed types across all 72 HD paths) x 25
script forms.

```
330,300 scriptPubKeys tested, 0 hits
positive control: the oracle finds a known-funded address   OK
```

Three mirror operations, kept distinct because discussion of this puzzle runs
them together:

```
reverse      CL76841714A -> A41714867LC
rotate 180   CL76841714A -> A417148977C     6->9; 2/3/4/5/7 have no rotated digit
mirror L-R   CL76841714A -> A41714867⅃Ɔ     AHIMOTUVWXY018 map to themselves
```

Each also crossed with `OVERDOSE`, `El Salvador`, `Max Keiser`, `20 BTC` and
the district code `L12`, with and without spaces, upper and lower.

The rotation reading is the one `serial_as_checksum.md` argues is optically
impossible, since a `4` and a `7` do not become digits upside down. Swept
anyway: that argument is about what a **reader** sees, and this is about what an
**author** might have typed.

## The stretched family, now also run

`mirror_serial.py` closed the mirrored serial under **fast hashes**. That said
nothing about stretched KDFs, and `kdf_and_keyformats.md` makes the point that
stretching is invisible to a bulk sweep by construction -- that is what
stretching is for. `serial_secret.py` had tested the FORWARD serial as a
passphrase and salt, not the mirrored readings.

36 strings is small enough that the argument does not apply, so the expensive
family was affordable. `mirror_kdf.py`:

```
pbkdf2-hmac-sha256  c = 1000 / 2048 / 4096 / 10000 / 65536, 8 salts
pbkdf2-hmac-sha512  c = 2048 / 4096 / 65536,                8 salts
scrypt              N = 2^12, 2^14
WarpWallet          scrypt N=2^18 XOR pbkdf2 c=2^16,        8 salts

2,664 stretched keys, 66,600 scriptPubKeys, 0 hits
```

Every primitive pinned to a published vector before the sweep, because a
silently-wrong scrypt would make the null worthless:

| vector | result |
|---|---|
| RFC 6070 pbkdf2-sha1, c=1 | OK |
| RFC 7914 scrypt, N=16 | OK |
| WarpWallet `ER8FT+HFjk0` / `7DpniYifN6c` -> `1J32CmwScqhwnNQ77cKv9q41JGwoZe2JYQ` | OK, uncompressed |

Plus the planted-key control through the index, as above.

## Status

**The mirrored serial is exhausted**, across fast hashes and stretched KDFs,
direct and HD derivation, all 25 script forms. Not "tested" -- exhausted.

## Two engineering notes, because the first attempt died of them

- Calling the oracle once per key costs ~329 ms of fixed setup against the
  454 MB memory-mapped prefix index. 13,212 such calls is 72 minutes; the run
  was killed by its own 15-minute timeout a fifth of the way through. Batched
  at 60,000 scriptPubKeys the same work is ~234 us each.
- That killed run was piped through `tail`, which buffers to EOF, so the
  partial output was discarded entirely. A long sweep writes to a file.
