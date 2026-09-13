# Stretched KDFs and printed key formats (2026-09-13)

Prompted by a shared Grok transcript. Grok had not solved the puzzle — its own
last line reads *"WarpWallet of the memorable phrases is empty"*, and the
`ER8FT+HFjk0` / `7DpniYifN6c` pair in its code is the **published WarpWallet
test vector**, not a derived answer. But its instinct located a real gap.

## The gap: every prior derivation used a fast hash

All ~69M addresses swept in this repo came from `sha256`, `dsha256`, the two
`sha512` halves, `sha3_256`, `blake2b` and a keccak-ish variant.
`full_sweep.direct_keys()` has no scrypt and no pbkdf2. An earlier session's
notes claim "WarpWallet scrypt" was covered; it is not present in any current
tool, and it was certainly never applied to the article's body prose, which did
not exist in any corpus until today.

This matters structurally, not incidentally. **A deliberately-stretched KDF is
invisible to a bulk sweep by construction** — stretching exists precisely so
that many candidates cannot be tried. So the honest coverage claim was never
"69M addresses"; it was "69M addresses *under fast hashes only*".

## WarpWallet

`warpwallet.py`, per keybase.io/warp:

```
s1   = scrypt (passphrase||0x01, salt||0x01, N=2^18, r=8, p=1, dkLen=32)
s2   = pbkdf2 (passphrase||0x02, salt||0x02, c=2^16, sha256, dkLen=32)
priv = s1 XOR s2
```

Verified against the published test vector before any sweep, and the module
refuses to run if it fails — a silently-wrong scrypt would make every null
worthless:

```
pass ER8FT+HFjk0  salt 7DpniYifN6c
priv 6f2552e159f2a1e1e26c2262da459818fd56c81c363fcc70b94c423def42e59f
->   1J32CmwScqhwnNQ77cKv9q41JGwoZe2JYQ   uncompressed MATCH
1.98 s per derivation
```

338 curated phrases x 12 salts = 4,056 derivations, all five script types
including compressed — which is the case the shared transcript was only just
getting to.

## The stretched family generally

`kdf_sweep.py`: pbkdf2-hmac-sha256 at c = 1000/2048/4096/10000/65536 and
pbkdf2-hmac-sha512 at c = 2048/4096/65536, each across 8 salts, plus scrypt at
N = 2^12 and 2^14 (warpwallet.py covers 2^18). 66 derivations per phrase.

Each primitive pinned to a published vector first, all passing:

| vector | result |
|---|---|
| RFC 6070 pbkdf2-sha1, c=1 | OK |
| RFC 6070 pbkdf2-sha1, c=4096 | OK |
| RFC 7914 scrypt, N=16384 | OK |

Results: 338 curated phrases -> 111,540 addresses -> **0 hits**.
Widened to 1,988 phrase variants -> 656,040 addresses -> (running).

## No key is printed anywhere in the article

Separately, a direct scan of the transcript for every standard printed key
format:

| format | shape | found |
|---|---|---|
| WIF | `5HJK…` 51 ch / `KL…` 52 ch | none |
| BIP38 encrypted | `6P…` 58 ch | none |
| Casascius mini key | `S…` 22/30 ch, sha256(k+"?") starts 0x00 | none |
| bare hex key | 64 hex chars | none |

And the decisive one: **the longest unbroken alphanumeric token in the whole
article is `hyperbitcoinized`, 16 characters.** Every key format needs 22 to 64.

So the key cannot be printed directly in the body text at all. It is a phrase
derivation (swept extensively, now including the stretched family), or it is
assembled across tokens (swept via n-grams, acrostics and column readings), or
it is in the artwork below the ~215 dpi the phone scans preserve, or it is not
on these pages.
