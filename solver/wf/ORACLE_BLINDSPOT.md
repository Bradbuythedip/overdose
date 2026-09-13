# The oracle is the bug, not the derivation (2026-09-13)

Three sessions have now derived roughly 100 million addresses from this article
and found nothing. This note argues the search was mis-specified, names the one
query that would settle it, and hands off the two inputs that would.

## The blind spot

Every sweep in this project has asked one of two questions:

| oracle | question it answers |
|---|---|
| `address_map.bin` (56.8M) | is this address funded **now**? |
| Pymmdrza dump (1.72M) | was this address **rich in April 2023**? |

Neither answers the question that matters, and the difference is not academic.

Automated sweeper bots watch the chain and drain any address whose private key
comes from a guessable passphrase, typically within seconds of it being funded.
This is why every famous brainwallet is empty. This repo already measured it
without drawing the conclusion: a "funded brainwallet" positive control had to
be abandoned because **8 of 8 well-known brainwallets probed came back with
zero balance**.

So if Keiser derived the prize key from a phrase in his own text and funded it
in late 2021, the overwhelmingly likely outcome is that the 20 BTC was swept
almost immediately, by a bot, silently. Under that hypothesis:

- the address holds zero today, so `address_map.bin` says **miss**
- it was never a rich-list entry, so the April-2023 dump says **miss**
- and it says **miss when handed the correct private key**

Every "0 hits" in this repo is consistent with the key having been found long
ago. "Nobody's figured it out yet" would still read as true to Keiser, who
would have no reason to check an address he was not watching.

## The query that would settle it

> Did this address **ever** receive coins?

That needs a historical chain index or any block explorer. Both are
unreachable here: every Bitcoin API host is refused at CONNECT (403), and the
only large dataset reachable over the git proxy is a *current-balance* index.
The sibling branch's `hist_index.py` is named for this problem but is built
from the same April-2023 rich list, so it inherits the same blindness.

This is a five-second query for anyone with ordinary internet access.
`wf/handoff_candidates.tsv` contains 130 candidates ready for it: the phrases a
setter would actually reach for from this piece, plus the mirror-writing
variants Keiser's own clue points at, each with its `sha256(passphrase)` private
key and both P2PKH addresses. All 130 are confirmed **not currently funded**,
which under this hypothesis is expected and is not evidence against them.

Check for *any* historical activity, not a balance.

## The input that would unblock the typographic channel

The strongest surviving cipher hypothesis is a per-character weight cipher:
bold and regular as a binary code in the body text. It is untestable here, and
the reason is worth stating precisely, because it points at the fix.

Per-character bold has been shown unrecoverable from these scans three
independent ways:

| method | finding |
|---|---|
| stroke width, per line | bold 3.3-6.4 vs regular 3.3-3.8: overlapping |
| per-letter area, this session | `h`/`d`/`a` called bold 80-91% of the time vs `c`/`k` at 11-12% |
| vision transcripts, sibling session | a 30x spread across letter identities |

All three are measuring the same thing: **glyph identity, not weight**. At
~215 dpi the bold/regular stroke delta in a 10 pt typewriter face is under one
pixel, so narrow heavy-stemmed letters read as "bold" and round open ones do
not, whatever the actual typography.

The repo's standing recommendation has been a 600+ dpi flatbed scan. There is a
strictly better input:

> **The digital edition of Bitcoin Magazine Issue 24 (the El Salvador issue).**

In a PDF the weight of every character is *metadata* -- a font name per text
run -- not ink to be measured. Per-character bold becomes exactly recoverable,
with no threshold, no noise floor, and no detector to validate. It also costs a
subscription rather than physical access to the paper copy and a flatbed
scanner.

The article was print-only; searching for an HTML republication finds nothing,
which is why every session has been reduced to reading pixels.

## What this changes about the conclusion

The honest status is not "the puzzle resists analysis". It is:

1. The text-derived-key space is exhausted **against current-balance oracles**,
   and those oracles cannot see the most likely outcome.
2. The typographic space is exhausted **at whole-word granularity**; the
   per-character channel is untested, not excluded, and needs the PDF.
3. Keiser said key**s**, plural, "in the text" of his column generally.
   Only Issue 24 has ever been examined.

Two cheap external actions - a historical check on 130 addresses, and the
Issue 24 PDF - would close 1 and 2 respectively. Neither needs more compute.
