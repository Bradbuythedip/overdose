# The column has never existed digitally (2026-09-14)

Searched the web for the article's most distinctive strings — phrases that
could not plausibly occur by accident:

- `"UTXO ghetto"` with `"monetary defibrillator"`
- `"It's the freaking UTXO ghetto up in here"`
- `"A monetary defibrillator to the treasure chest"`
- `"the mEthereum lab"`
- `"honey-badgering Peter Schiff"`

**Zero hits.** Not on bitcoinmagazine.com, not in an aggregator, not in a
forum, not in a quote. `bitcoinmagazine.com` itself is blocked by this
container's egress proxy, but the searches were not — and a phrase like
"mEthereum lab" appearing nowhere is a strong result regardless of which single
site is reachable.

The Overdose column appears to exist **only in print**.

## Four things that follow

### 1. "Have you ever picked up a PHYSICAL COPY" is literal

That line has been read here as a hint about typography — that the printed page
carries something a digital version would lose. It is simpler than that. There
is no digital version. The text exists nowhere else. Reading it at all requires
the physical object.

### 2. No brainwallet cracker has ever tried these phrases

Crackers ingest digital corpora: Wikipedia, Gutenberg, lyrics, scraped web
text, tweets. A phrase that has never been digitised cannot be in any of them.
So no cracker has ever swept the article's sentences — not because they chose
not to, but because the text was never available to ingest.

This independently confirms `swept_key_untested.md` by a completely different
route. That document showed **statistically** that the 0%-ever-funded rate for
article phrases carries no information (expected 1.74 hits, observed 0,
p = 0.402). This shows the same thing **mechanistically**: the rate was always
going to be 0%, whether or not the puzzle is real, because the phrases were
never in a cracker's input.

Two independent arguments, same conclusion. The article's 0% was never evidence
of anything.

### 3. Our transcript may be the only digital copy that exists

Which makes its accuracy load-bearing with nothing to cross-check it against.
Two characters have been verified against the scan — the line breaks (83 of 95
at offset zero) and the apostrophe (a straight typewriter U+0027 at 400dpi).
Every other character rests on one human's reading.

That raises the value of `mega_solve.py --families edit1_all`, which covers the
complete single-error neighbourhood, rather than lowering it. It is not a
long-shot family; it is the only defence against the one assumption underneath
all 150M derivations.

It also means the publisher's own text would be worth real effort to obtain —
an inscribed issue (see the PUBLISHER detector in `chain_tail_scan.py`), a
back-issue PDF, or the digital edition. That is the single artifact that would
retire the transcription question outright.

### 4. "Nobody has solved it" is weak evidence

Anyone attempting this had to buy the magazine and transcribe it by hand first.
That is a real barrier, and it is a sufficient explanation for the absence of
public solutions without any appeal to the puzzle being unsolvable or fake.

## What this does not establish

Search engines do not index everything, and absence of results is not proof of
absence. For phrases this distinctive it is strong evidence, not certainty. A
direct check of bitcoinmagazine.com from an unblocked network would settle it,
and is worth doing.
