# What the pages show when you open them (2026-09-14)

Five observations from viewing the seven page images directly, and what each
one turned out to be worth.

## 1. Page 79's body text really is on a curved baseline

Confirmed visually. The first paragraph arcs across the page — the lines bow,
so a line-finder grouping glyphs by shared horizontal `y` cannot group them.
`looking_at_the_pages.md` measured the consequence: **15% of that page's glyphs
were recovered**, against 61% for the article overall.

That page is the conclusion. Every glyph-level conclusion in this repo rests on
a corpus that barely contains it.

## 2. Bold appears as long contiguous RUNS, not word alternation

This looked at first like a word-level cipher. It is not. On p79:

```
...to fully express ourselves individually in a cyber
sea of billions of souls all looking to connect   <- bold ends here
and express love for each other and the cost...   <- regular
```

A single bold run spanning two and a half lines, ending mid-line at "connect".
The same shape appears in the closing block: `have been living in here`,
`We've seen some shit.`, `as Bitcoin conquers fear and hate and replaces it
with peace and love.`

So **bold runs are a separate emphasis channel from the colour highlights**.
`highlights_ordered.tsv` catalogued the orange and black backgrounds; the bold
runs are unbacked and were never catalogued as runs.

Within a run, per-character weight varies — `star`**`ve`**, `con`**`que`**`st`
— and that is the font, not a message. `bold_cipher_resolved.md` established it
with a test rather than an eye: P(bold | character) is 0.158 for `c` and 0.476
for `a`, chi-square 93.9 on df 22, p ~ 5e-11. Eyeballing stroke weight at 3x
zoom reproduces the illusion and settles nothing.

## 3. The letter-tracked passage on p77 is justification

```
energy supply. Shitcoins,  fiat  and  gold  will
starve  to  death  as  the  result  of  Bitcoin's
insatiable  conquest  of  all  available  energy.
```

Visibly wider tracking than the text around it — and the lines are flush to
both margins. It is a short line stretched to fill the measure, the same
mechanism `looking_at_the_pages.md` identified behind the six wide gaps.

## 4. The banknote on p73 is printed mirrored

`100 DOLLARS` and `THE UNITED STATES OF AMERICA` both read backwards on the
page. That is where the mirror hypothesis came from, and it is real — though
`mirror_serial_closed.md` has since exhausted the mirrored serial across fast
hashes, stretched KDFs, direct and HD derivation, all 25 script forms.

## 5. The transcript contains only body copy

The finding that actually produced new material. `article_transcript.txt` holds
pages 75-79 body text and nothing else. Printed on the pages and never swept:

| where | text |
|---|---|
| p73/74 | the `OVERDOSE` display masthead, `with Max Keiser`, `@ANNABELLEBAZ` |
| p77 | a painted `SHIT`, white on the dark ground |
| p78 | a black scribble reading `X FUCK ALL X`, with the article's pull-quote reversed out in white inside it — the **third** printing of "The economy of love is infinitely more efficient than hate and war" |
| p79 | the handwritten `MAX KEISER` signature, a heart between the words, a drawn Bitcoin symbol |
| every page | the orange `OVERDOSE` running head, the vertical `Bitcoin Magazine \| El Salvador` folio, page numbers 73-79 |

`FUCK ALL` and `@ANNABELLEBAZ` are confirmed absent from the transcript.
`SHIT` is present, but only inside "We've seen some shit."

`page_furniture.py` builds 9,830 candidates from all of it — every case,
spacing and reversal variant, every cross-group pairing, each page's furniture
in reading order.

```
1,720,250 scriptPubKeys, 0 hits
```

## Status

Nothing here solved it. Two of the five observations were dead ends that
*looked* like channels (the bold alternation, the tracked passage), and saying
so is the point: both would have consumed days if chased on appearance rather
than measured. The third produced genuinely untested material, and it is now
tested.
