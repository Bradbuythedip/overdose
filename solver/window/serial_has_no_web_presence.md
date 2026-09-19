# Searching the web for the serials: closed, and why it was never going to work (2026-09-19)

Recorded so nobody runs it again.

## What was searched

| query | result |
|---|---|
| `"CL76841714A"` | **1 hit: this repo's own PR #8.** Nothing else |
| `"76841714"` bare | machine part numbers, Polish patents, trademark ranges. Nothing related |
| `"KB46279860"` / `"46279860"` | **1 hit: this repo's own PR #8.** Nothing else |
| serial + stock-photo framings (Alamy/iStock/Shutterstock/Vista) | generic "flying $100" listings, no serial match |
| serial + prop-money framings | prop-money vendors, no serial match |
| Where's George + serial | the site, not the note |
| Issue 24 masthead / art director / photo credit | Behance 133310833 (the **cover**) and retail listings only |

## Why a null here carries almost no information

The test is **asymmetric**: a hit would have been decisive, a miss tells you
nothing. Circulating banknote serials are essentially never indexed on the
public web. Stock-photo listings describe the *subject* ("one hundred dollar
bill curled up") and never transcribe the serial. So the two live hypotheses —

- (a) the designer pulled a stock/archive photo of a real $100, or
- (b) Keiser photographed a note he owned

— predict **exactly the same result**: no hits. The search cannot separate them
and should not be read as favouring either.

## Self-contamination

Both serials now return this repository as their top result. The project has
become the internet's only source on these strings, so future searches will
keep surfacing our own notes. Any apparent "corroboration" found this way is
circular.

## What the note itself does establish

Reading the large cutout on p74 directly from `IMG_6245.jpeg` at 8x rather than
searching for it:

| observation | consequence |
|---|---|
| top legend reads `FEDERAL RESERVE NOTE`; Federal Reserve eagle seal present | **genuine currency, not prop money.** Prop notes carry "FOR MOTION PICTURE USE ONLY" and deliberately fictitious serials — that would have killed the branch outright |
| serial district letter `L` matches the printed district badge `L12` | internally consistent — San Francisco, 12th district. A fabricated serial need not agree with its seal; this one does |
| pre-2013 design (centred oval portrait, no blue 3D ribbon); `C` = Series 2001 | the photographed note is old-style |

The Series 2001 dating is **weak** evidence about when the photo was taken, and
should not be pushed: $100 notes have the longest service life of any US
denomination (roughly two decades), so an old-style note in a 2021 wallet is
entirely ordinary. It does not establish that the image is archival.

What it does confirm is that the object is a real banknote, photographed — which
is consistent with the p74 spread being a **photo composite**, and with the
finding in `what_keiser_controlled.md` that one cutout was duplicated with
rotations across the spread.

## The one index not yet checked

**wheresgeorge.com** is the only public database that indexes circulating US
banknote serials by number. It is blocked by this container's egress proxy.
Anyone with a browser can check `76841714` there in under a minute. A hit would
return an entry date and city for the physical note, which would be real
provenance evidence.

Prior probability is low — Where's George entries skew heavily to $1 notes — so
this is a cheap long shot, not a plan.

## The test that would actually settle provenance

A **reverse image search** on the p74 banknote cutout, which this container
cannot perform (no image search, and every image host is blocked). That, or the
P6 email to the Issue 24 interior designer. The Behance gallery is the cover
only; the interior credit is on the printed masthead, which is in the physical
issue.
