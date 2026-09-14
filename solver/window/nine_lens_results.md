# The nine-lens workflow, and what two lenses found (2026-09-14)

Nine independent attack lenses, each generating candidates AND self-testing
them against the 56M funded-address index, with an adversarial verification
stage for anything claiming a hit.

```
confirmed:      []          no hits survived verification
brokenControl:  []          every lens ran a valid test, control firing
agents: 10, done 9, error 1      4.5 hours, 1.47M subagent tokens, 645 tool calls
```

One lens (`lennon`, the 1969 Amsterdam bed-in) **failed on a content filtering
policy**, not on the puzzle. That axis is untested, and saying so matters more
than the tidy total.

## Genesis lens — 85,782 candidates, 87,803,775 scriptPubKeys, null

Page 78 says the fact is "observable by anyone choosing to see it, right there
in the Genesis Block", which is the nearest thing to an instruction in the
piece. What it established:

- The coinbase headline is **exactly 12 whitespace-separated tokens** — the
  shape of a BIP-39 mnemonic. But none of its words are in the BIP-39 wordlist,
  so it cannot be a checksummed mnemonic; it can only act as a raw seed, which
  was covered and is null.
- 164 **real** BIP-39 mnemonics built from genesis material as entropy — block
  hash BE/LE, merkle root BE/LE, pubkey x, both hash160s, sha256 of the
  coinbase in three renderings, the packed nonce‖timestamp‖bits‖version quad —
  all swept through 72 HD paths. The lens called this "the construction I would
  have bet on", and it is now excluded.
- A construction worth keeping even though null: the coinbase **template**
  re-instantiated with the magazine's own material —
  `The Times 07/Sep/2021 BITCOIN IS TOXIC AF`,
  `The Times 03/Jan/2009 Bukele on brink of second bailout for the IMF`.
- Its own conclusion: the article gives **no numeric anchor** tying "Genesis
  Block" to any offset or selection rule. The sentence is rhetorical. Genesis
  is a thematic nod, not a pointer to bytes.

## Numbers lens — 44,516 candidates, 107,046,450 scriptPubKeys, null

This one **corrected the brief I gave it**, which is the most useful thing any
lens did.

I supplied a 20-item numeral inventory. Verified against the transcript rather
than trusted, the printed order is **23 items**, and my version had three
errors and three omissions:

| | |
|---|---|
| missed | p75 contains **three** "Layer 1" occurrences, not the one I listed |
| wrong order | "Forty years of dumb post-1971" — 40 **precedes** 1971; I had it after |
| wrong order | 2017 precedes 12,000; I had them swapped |
| omitted | "near zero" (p79), the ordinal "first" x3, "EVERY SINGLE ONE OF" (p77) |

And a genuine coincidence, reported with its own base rate:

> The extended inventory concatenates to **exactly 64 decimal digits** —
> `2008111401971101201114220000100000620171120001511852519501196910` — every
> digit valid hex, and read as a 32-byte big-endian integer it is below the
> curve order. A syntactically perfect private key.
>
> Given a dedicated full-HD pass: **null**. And the lens measured the base
> rate itself: of 128 include/exclude combinations of the optional inventory
> groups, **2 land on exactly 64 digits (1.6%)**. A mild coincidence with real
> researcher degrees of freedom, not evidence.

That is exactly the discipline this project needs — a striking number found,
its null computed, and the finding retired by its own author.

## Composite assembly — 1,135 candidates, 10,413,625 scriptPubKeys, null

Separate from the workflow. Keiser said "hidden private key**s**" — plural.
Every sweep had read that as "several independent keys, find any one". The
other reading is that the key is **assembled**, one fragment per page.

Nine fragment kinds (first/last highlight, first/last line, first/last word,
page number, largest numeral, all-caps display string), each taken once per
page and concatenated in page order and reverse, plus the **cover** as key
material for the first time — UPC `074820403884`, `$12.99US`,
`Display Until Feb 23, 2022`, `THE EL SALVADOR ISSUE`.

Mixing kinds across pages was deliberately not done: 9^5 is 59k combinations of
mostly nonsense, and a setter assembling fragments uses the same rule on every
page.

## Also verified positively

`article_transcript.txt` line counts match the **printed** line counts exactly
on all five pages — 33 / 31 / 32 / 23 / 26. A shared Grok transcript had
claimed "Sand's cipher uses the printed typeset lines, not the stitched
sentences", implying our line-based ciphers might have run on reconstructed
sentences. They did not. Every line-based cipher ran on the correct lines.
