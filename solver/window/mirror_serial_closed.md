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

## The boundary that remains

This closes the mirrored serial under **fast hashes**. It says nothing about
stretched KDFs, and `kdf_and_keyformats.md` makes the point that stretching is
invisible to a bulk sweep by construction -- that is what stretching is for.
`serial_secret.py` tested the serial as a BIP-39 passphrase and KDF salt, but
not confirmed for the mirrored readings.

For 36 strings that is cheap: WarpWallet is ~2 s per derivation, so the whole
set across salts is roughly a quarter of an hour. Until it is run, the honest
claim is "the mirrored serial is closed under fast hashes", not "exhausted".

## Two engineering notes, because the first attempt died of them

- Calling the oracle once per key costs ~329 ms of fixed setup against the
  454 MB memory-mapped prefix index. 13,212 such calls is 72 minutes; the run
  was killed by its own 15-minute timeout a fifth of the way through. Batched
  at 60,000 scriptPubKeys the same work is ~234 us each.
- That killed run was piped through `tail`, which buffers to EOF, so the
  partial output was discarded entirely. A long sweep writes to a file.
