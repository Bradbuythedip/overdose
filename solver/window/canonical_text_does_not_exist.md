# The canonical digital text does not exist (2026-09-14)

`transcript_diff.py` was built to eliminate the largest remaining uncertainty:
every one of ~150M derivations assumes `article_transcript.txt` is a perfect
transcription, and only two characters' worth of that has ever been verified
against the scan — the line breaks (83 of 95 at offset zero) and the apostrophe
(a straight typewriter U+0027, at 400dpi).

The publisher's own bytes would have settled it. They are not obtainable,
because they are not published.

## Four independent checks, all negative

| check | scope | OVERDOSE found? |
|---|---|---|
| web search, distinctive phrases | `"the mEthereum lab"`, `"A monetary defibrillator to the treasure chest"`, `"UTXO ghetto"` | **no** — zero results anywhere |
| Keiser author archive | saved page, link extraction | **no** — one Keiser article, unrelated |
| **bitcoinmagazine.com sitemap** | **15,064 URLs** | **no** — zero slugs contain "overdose" |
| **Wayback CDX index** | **50,000 URLs** | **no** — zero, including deleted pages |

Every "toxic" match across both indexes is a different author writing about
toxic maximalism (`op-ed-why-bitcoins-toxic-maximalism-makes-sense`,
`how-toxic-bitcoiners-are-protecting-ideals`, and so on). None is Keiser's
column.

The Wayback result is the strongest of the four: its index contains URLs that
have since been **deleted**, so this is not "it was taken down". The column was
never at a bitcoinmagazine.com URL at all.

## A correction to something I said earlier

I wrote that "the Orange Party issue's OVERDOSE column is published digitally"
and used it to argue the El Salvador one probably was too. That was an
over-reading of a search summary: the result described the column's existence,
but the URL it carried was the **issue landing page**
(`/2022-orange-party-issue`), not the column. I have no evidence any OVERDOSE
column has ever had its own URL, and the sitemap says none does.

The `/print/` path is real — `bitcoinmagazine.com/print/bitcoin-is-a-mirror-that-reveals-all`
exists — so the magazine does publish *some* print articles digitally. OVERDOSE
is simply not among them.

## What this settles

**The transcription risk cannot be eliminated. It can only be bounded.**

That is not a dead end, it is a redirect, and it raises the value of the work
already built:

- `mega_solve.py --families edit1_all` enumerates the complete
  single-character-error neighbourhood of every phrase — ~126M candidates,
  every substitution, insertion and deletion over a 77-character alphabet,
  complete by construction rather than sampled. It is the only defence against
  the assumption underneath all 150M derivations, and with no canonical text to
  check against, it is the **only** one.
- `transcript_diff.py` remains useful if the text ever surfaces from another
  route: a back-issue PDF, the digital edition, an inscribed issue (the
  PUBLISHER detector in `chain_tail_scan.py` watches for exactly that), or
  someone else's independent transcription.

## And it explains the clue

> "Have you ever picked up a **physical copy** of @BitcoinMagazine..."

Read here for a long time as a hint that the printed page carries something
digital would lose — typography, layout, a mark. It is simpler and more
literal than that. **There is no digital version.** Not on the publisher's
site, not in the Wayback Machine, not indexed anywhere. Reading the column at
all requires the object.

Which also means no brainwallet cracker has ever ingested these phrases, for
the mechanical reason recorded in `no_digital_footprint.md`: a phrase that was
never digitised cannot be in any cracker's corpus.
