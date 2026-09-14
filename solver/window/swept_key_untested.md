# The swept-key hypothesis was never tested (2026-09-14)

`window/everfunded_results.md` concludes:

> Generic dictionary phrases are funded at roughly **0.33%** in this sample
> (52 of 15,672). The article's own text is at **0%** across 89,733
> addresses ... So for the phrase space tested, "someone already solved it and
> took the coins" is now the *less* supported reading, not the more supported
> one.

That is load-bearing. "Swept years ago" is one of only three live explanations
for every null this project has produced, and the repo has been treating it as
ruled out. It is not ruled out. The comparison is confounded twice, and neither
confound has anything to do with this article.

## Confound 1 — word count

Of the ~25 distinct ever-funded phrases, **23 are single words**: `the`,
`Bitcoin`, `Money`, `1`, `42`, `you`, `mike`, `love`, `michael`, and ten more
sharing the identical `0.00005460` sprayer amount. The remaining two are
`Satoshi Nakamoto` and the Genesis coinbase string — the two most famous
strings in Bitcoin. **Not one hit is prose.**

| corpus | single-word phrases |
|---|---|
| generic | 1,908 of 7,823 — **24.4%** |
| article | 144 of 22,655 — **0.6%** |

So 0.33% is a rate for a population the article barely contains, applied to a
population that is almost entirely multi-word prose. That is not a surprise
about this article; it is how brainwallet crackers work. They walk dictionaries
and famous quotes. They do not enumerate arbitrary 7-word spans of arbitrary
prose, because that space is unbounded.

## Confound 2 — derivations per phrase

The rate is computed **per address**. But a cracker cracks a **phrase**: if it
knows the phrase, it tries every common derivation. Counting addresses inflates
whichever corpus had more derivations applied — and that is the article's:

```
generic corpora    15,672 addresses /  7,823 phrases =  2.0 per phrase
article priority   44,957 addresses / 22,473 phrases =  2.0 per phrase
article deep       44,777 addresses /    454 phrases = 98.6 per phrase
```

Counted per address, the article's single-word sample looks like 2,523.
Counted per phrase it is **144**. A 17x inflation of the apparent sample size,
entirely from re-deriving the same phrases.

I made this error myself while checking the first one: stratifying by word
count but still counting addresses gave `p = 1.07e-10` and looked like a
dramatic real finding. It was an artifact of the second confound.

## With both removed

| stratum | generic | article | expected | observed | Fisher p |
|---|---|---|---|---|---|
| single word | 23 / 1,908 = 1.21% | 0 / 144 | **1.74** | 0 | **0.402** |
| multi-word | 0 / 5,915 = 0.00% | 0 / 22,511 | 0 | 0 | **1.000** |
| *(unstratified, per address, as the repo frames it)* | 50 / 15,672 | 0 / 89,734 | 286 | 0 | 3.8e-42 |

Sensitivity to the exact single-word hit count, which the results doc lists
somewhat loosely: p ranges 0.25–0.41 over 21–25 hits. Never significant.

**Not one stratum shows a difference.**

## What this actually means

Two separate things, and conflating them is what produced the wrong conclusion.

1. **The sweep had almost no power.** It could expect ~1.7 hits if the article's
   phrases were funded at exactly the generic rate. Observing 0 against an
   expectation of 1.7 is unremarkable. A null from an underpowered test is not
   a null — this repo has written that sentence before.

2. **In the prose stratum the test is impossible, not merely weak.** The
   *generic* base rate for multi-word non-famous phrases is itself **zero**
   (0 of 5,915). There is no signal to compare the article against, at any
   sample size. Adding a million more article n-grams would not change this.

So the ever-funded oracle, which was built specifically to answer "was this
swept", **cannot answer it for prose phrases**. That is a limit of the method,
not a result about the puzzle.

## What is still true

Everything factual in `everfunded_results.md` stands:

- 290,893 addresses evaluated against real chain history
- 57 ever-funded, every one attributed, every one generic
- the `0.00005460` sprayer identified across eleven addresses
- no article-specific reading has ever received a satoshi

What does not stand is the *inference* drawn from the last line. "No
article-specific reading has ever received a satoshi" is exactly what you
expect whether or not the puzzle is real, because no comparable generic prose
phrase has either.

## Consequence for strategy

The three explanations for this project's nulls are unchanged in their
standing:

1. the key is outside the derivation space tested
2. the key was found and swept
3. there is no key

The ever-funded work did not demote (2). It remains as live as it was before
the oracle was built. Reproduce with `stratified_everfunded.py`.
