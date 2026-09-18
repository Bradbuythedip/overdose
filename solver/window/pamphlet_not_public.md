# The later columns have no public print edition (2026-09-18)

Test B -- Sand/Musset on the PRINT line breaks of a later OVERDOSE column --
needs one artifact: the column as typeset. This records, with the evidence,
that the artifact is not publicly served, so nobody repeats the search.

## What was checked

`fetch_pamphlet.sh` against *Buy Love, Sell Fear* (Withdrawal Issue,
bitcoinmagazine.com/print/buy-love-sell-fear-bitcoin-magazine-withdrawal-issue):

| probe | result |
|---|---|
| `.pdf` anywhere in the article page HTML (535,897 bytes) | **none** |
| the page's "download" control | points at `https://mailchi.mp/bitcoinmagazine.com/buylovesellfear` |
| that Mailchimp page (28,165 bytes) | **no .pdf, no iframe, no viewer** -- an email capture form |
| embedded viewers (issuu / flipbook / scribd / yumpu / drive / calameo) | none on either page |
| the article's own assets | WordPress uploads on bitcoinmagazine.com: `keiser_preview.jpg` plus the usual 300x157 / 696x364 / 768x402 / 803x420 / 1024x535 / 1068x558 size variants. No document asset |
| `images.saymedia-content.com/.image/cs_srgb/MjAxMTQ2NTAyNDEwNjc1OTk0/6-keiser_the_withdrawal_issue.pdf` | **404**, zero-length body, `application/octet-stream`. That combination is exactly what makes Chrome report `ERR_INVALID_RESPONSE` instead of showing a 404 page -- the error that made this URL look promising. Four other transform shapes: 404, 404, 403, 400. The URL is not referenced anywhere in the page HTML |

## Conclusion

*Buy Love, Sell Fear* is published as web text plus a social-card image. Its
print edition is not downloadable. The only route to the typeset column is the
email form, which mails the pamphlet to a subscriber -- a human action, not a
fetch.

This matters beyond one column: it is the same wall as path A. The printed
artifact is a subscriber or purchase object in every case, and no amount of
tooling gets around that.

## What must NOT be done instead

Run the device on the web text. The article's web line breaks are the
browser's reflow; Sand (alternate printed lines) and Musset (first word of each
printed line) would then operate on lines the typesetter never set, and the
result -- positive or negative -- would mean nothing. `print_musset.py` warns on
that shape (median line length over ~75 characters, or a URL/date in the
margins) but the warning is not a licence to proceed.

## The state of the tooling, which is ready

`print_musset.py` is complete and controlled: four PDF backends, a round-trip
test that builds a PDF with known line breaks and asserts they come back
identical, a web-reflow detector, per-reading scoring against the SAME lines
shuffled, and a refusal to derive anything unless a reading opens as an English
imperative. Its control on Issue 24 reproduces the known-broken reading (every
reading within ~0.6 sd of its own null, none imperative), so the extractor
cannot invent a message.

It takes a line-faithful text file as readily as a PDF:

    ./run.sh musset <column>.txt        # one printed line per text line

So a transcription of the printed column -- from the pamphlet, from a photo of
the page, or by hand -- is a complete substitute for the PDF.
