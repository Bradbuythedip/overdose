# The banknote serial is the art director's stock asset. Branch closed. (2026-09-19)

## The finding

**The $100 note bearing serial `CL76841714A` appears on the cover of a
completely unrelated publication designed by the same art director, years
before Bitcoin Magazine Issue 24 existed.**

Source: `evidence/HG-GovtDebt-redact.pdf`, a 12-page portfolio PDF from
`duffferguson.com` — Duff Ferguson, Art Director of Bitcoin Magazine (BTC Inc.)
since September 2017, and therefore art director for Issue 24
(`p6_art_director_identified.md`).

The document is a **"Government Debt Survival Guide"**, a financial-advisor
marketing brochure with the client's branding redacted. It has no Bitcoin
content of any kind: national-debt charts, a gold-standard pitch, a Reagan
quote, gold bars, a silver eagle, a piggy bank.

Its cover carries a curled $100 bill. The serial is `CL 76841714 A`.

Side by side, both legible without interpretation
(`evidence/serial_match_CL76841714A.jpg`):

| panel | source | serial |
|---|---|---|
| A | Bitcoin Magazine Issue 24, p74, the OVERDOSE spread (Fall 2021) | `CL 76841714 A`, district `L12` |
| B | Government Debt Survival Guide, cover | `CL 76841714 A` |

Panel B also resolves the Treasury signature — **Paul H. O'Neill**, Secretary
of the Treasury 2001–2002 — independently confirming the Series 2001 reading
that `serial_oracle.py` decoded from the `C` prefix.

## Why this is decisive

Real banknotes have unique serial numbers. Two photographs showing the same
serial are the same image, or the same physical note. Either way the note
belongs to **the designer's asset library**, not to Max Keiser.

And the chronology is one-directional. The brochure's own content dates it:

- "The U.S. has a national debt of **$20 trillion**" — crossed in Sept 2017
- a US Gross National Debt chart labelled **1972–2016**
- "NerdWallet's **2015** American Household Credit Card Debt Study"
- "**In 2016**, home prices were rising at a rate twice that of inflation"

So the job is **c. 2016–2017**. Issue 24 shipped **Fall 2021**. Keiser first
claimed a hidden key in **December 2022** and pinned 20 BTC to the piece in
**March 2023**.

The image was in Ferguson's library roughly four years before the OVERDOSE
spread, and five to six years before the puzzle was ever mentioned. **It cannot
encode a key for a prize that did not yet exist.**

(The PDF itself was exported 2023-01-16 per its metadata — Illustrator CC 2017
on Windows, converted by Photoshop for Mac. That is the portfolio export date,
not the job date; the job date comes from the content above.)

## What dies

The entire serial branch, on both grounds at once — wrong premise *and* wrong
provenance:

- `serial_oracle.py`, `serial_combine.py`, `clue_serial.py`,
  `serial_text_mine.py`, `serial_bip39_mine.py`, `find_serial_matches.py`,
  `wf/serial_tail.py`
- `window/serial_as_checksum.md`, `serial_deep_dive.md`,
  `mirror_serial_closed.md`, `second_serial.md`
- ~2,297,420 derivations in STATUS.md's banknote row, plus the ~10^8 scripts
  `final_assessment.md` attributes to serial framings

`what_keiser_controlled.md` already showed the branch's *motivation* was
vacuous: "every digit is a legal hex digit, so `0x76841714` is a well-formed
four-byte value" is true of every banknote ever printed, measured at
200,000/200,000. This adds the *provenance*: the digits are an art director's
clip art, reused across unrelated client work.

The second serial, `KB46279860`, ghosting on page 72, is not proven library art
by this document — but p72 is the NUMBERS department page, not Keiser's column,
and the prior just moved a long way.

## What this does NOT do

It does not find a key, and it is not a solve. It removes a hypothesis.

It also **confirms the prediction** `what_keiser_controlled.md` made from the
Thompson audit: P6 was framed there as the question that would decide "whether
~2.3M derivations were aimed at the art department's clip art." They were.

## What it leaves

`what_keiser_controlled.md`'s ranking now has one fewer live visual branch. The
only channel Keiser provably controlled remains the character stream — verified
un-copyedited, and null under every oracle applied to it, chain-based and
checksum-based alike. The live hypothesis is still `final_assessment.md` §5
branch 1: **never funded**.

The one question this document cannot answer, and which is still worth an email
to Ferguson: **did Keiser supply any asset to be set verbatim?** That remains
the only visual channel a setter could have guaranteed would survive
typesetting.
