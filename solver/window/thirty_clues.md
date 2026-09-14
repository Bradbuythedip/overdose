# Thirty new measured clues from the scan (2026-09-14)

Clue-discovery pass over `solver/scan/Scan1.pdf`. Every entry is a measured,
reproducible fact about the artefact, not a hypothesis. Each was grepped
against the 45 existing docs (`solver/*.md`, `solver/window/*.md`, ~5,562
lines) before being counted; terms returning hits were discarded.

Reproduce with `python3 extract_scan.py --dpi 400 --out /tmp/sc400` and
`pymupdf`.

---

## A. Scan structure and provenance

**1. The pages were scanned out of order, in swapped pairs.**
`extract_scan.py:38` — `PAGE_MAP = {0:73, 1:72, 2:74, 3:75, 4:77, 5:76, 6:79, 7:78}`.
Scan order is **73, 72, 74, 75, 77, 76, 79, 78**. Every pair after the first is
transposed. Anyone indexing the PDF as `printed = 72 + pdf_index` mislabels six
of eight pages — a trap this pass fell into and had to correct.

**2. Every bilevel layer is exactly 400 dpi; every colour layer exactly 200 dpi.**
From `page.get_image_rects(xref)`, dividing pixel size by placed size in points.
All 27 bilevel regions return 400.0/400.0; all 8 colour layers return
200.0/200.0. No page deviates.

**3. The document holds 35 embedded images, unevenly distributed.**
Per printed page: 72:4, 73:5, 74:2, 75:5, 76:3, **77:1**, 78:6, **79:9**.

**4. Page 77 carries exactly one image and zero OCR characters.**
It is the dark-brown page; white-on-dark gives the scanner no black-on-white
layer to separate.

**5. Page 74 has no bilevel mask either, and only 9 OCR characters.**
It is the full-bleed photograph of Keiser. Two images total: colour layer plus
a folio strip.

**6. Page 79 is the most segmented page in the document:** 9 images, of which 7
are sub-page regions.

**7. Three image pairs occupy byte-identical placement rectangles.**
p79 xref 62/63 (56x128), p79 xref 64/65 (1736x172), p78 xref 75/76 (72x2648).

**8. Each such pair is a solid plate plus a content mask.**
Measured ink fractions: xref 65 is **100.0%** ink against xref 64's 94.6%;
xref 76 is 99.5% against xref 75's 91.2%. 4.4-9.4% of pixels differ. This is
how the scanner encodes knockout (white-on-dark) type: one solid plate, one
content layer.

**9. Folios alternate by parity, confirming recto/verso.**
Folio strips sit at x 519-562 pt on odd pages (73, 75, 79) and x 49-94 pt on
even pages (74, 76, 78). Odd = right, even = left.

**10. The rotated sidebar sits on the opposite edge from the folio.**
Tall thin regions (aspect 0.04-0.22): p72 xref19 and p78 xref77 at the RIGHT
edge (x>589 pt); p75 xref36, p79 xref59/61 at the LEFT edge (x<16 pt). Even
pages sidebar-right, odd pages sidebar-left — the mirror of clue 9.

**11. Scanner and producer identify the capture device.**
`creator: 'Canon '`, `producer: ' '` (blank), `format: PDF 1.3`, 85 xrefs,
0 embedded files, no encryption.

**12. The scan was made 2026-09-13 at 20:01:34, UTC-05:00.**
`creationDate: D:20260913200134-05'00'`, `modDate` empty.

**13. All eight pages are US Letter with rotation flag zero.**
MediaBox `Rect(0,0,612,792)` on every page, `rotation=0` — yet the content is
180° rotated, so the rotation is physical, not a PDF attribute.

**14. Bilevel masks store ink as the LIGHT class, not the dark one.**
p75's mask is 93.8% dark / 6.2% light; ink is the 6.2% minority, i.e. white.
Any reuse that assumes `pixel < 128 == ink` inverts these masks.

**15. The scanner extracted individual display elements as their own regions.**
Page 72's "572 / WESTERN UNION / LOCATIONS IN / EL SALVADOR" block is a
standalone 1080x868 bilevel image (xref 18), separate from the page mask.

---

## B. Colour

**16. Pages 72 and 74 contain zero orange pixels.**
Mask `(R>150)&(40<G<175)&(B<110)&(R-B>70)` over the 200 dpi colour layers:
p72 = 0 px, p74 = 0 px, against 7,732-98,159 px on every other page.

**17. Page 72's paper base is measurably different from every other page.**
Median paper RGB: p72 **(239,240,233)**; all others (246,246,246) to
(253,253,253). Page 72 alone is greener and darker.

**18. The orange ink is one consistent colour across the article.**
Medians: p75 (251,132,61), p76 (250,135,69), p77 (249,133,68), p78 (252,134,66),
p79 (250,137,65) — a spread of 3 in R, 5 in G, 8 in B.

**19. Page 73's orange is the outlier.**
(249,142,86) — G is 5-10 higher and B is 17-25 higher than any article page.
The title-spread orange is a lighter tint than the body highlight bars.

**20. Colour-layer JPEG sizes rank page complexity.**
p74 is the largest at 286,252 bytes (full-bleed photograph) and p78 the
smallest at 123,752.

---

## C. Page 72, the page that exists only in the scan

**21. Page 72 is absent from the phone-photo set entirely.**
The scan covers printed 72-79; `IMG_6244..6250` cover only 73-79. Every
pre-scan transcript, corpus and sweep was blind to it.

**22. Its nine source URLs, transcribed here for the first time.**
Left column:
```
www.knomad.org/publication/migration-and-development-brief-34
www.migrationdataportal.org/themes/remittances
www.worldbank.org/en/news/press-release/2021/05/12/defying-
predictions-remittance-flows-remain-strong-during-covid-19-crisis
www.wise.com/documents/Public_Research_and_Survey_-_US_Hidden_Fees
```
Right column:
```
www.repository.upenn.edu/sire/75/
www.westernunion.com/sv/en/receive-money.html
ir.westernunion.com/investor-relations/financial-information/
www.alliedmarketresearch.com/remittance-market
www.globenewswire.com/news-release/2021/04/12/2208403/
```

**23. One source URL carries El Salvador's ISO country code.**
`westernunion.com/sv/en/receive-money.html` — `sv` is the ISO 3166-1 code for
El Salvador, on the page that also prints EL SALVADOR in display type.

**24. Page 72 prints 21 numerals.**
In order: 165, 572, 2020, 4.8, 930.44, 2026, 3.9, 35.8, 2026, 14.5, 2019, plus
34, 75, 2021, 05, 12, 2021, 04, 12, 2208403 from the URLs, plus the folio 72.

**25. Fifteen of them fall inside the BIP-39 index range (0-2047).**
165, 572, 2020, 2026, 2026, 2019, 34, 75, 2021, 05, 12, 2021, 04, 12, 72.

**26. Page 72's type block is the widest in the document.**
Mask bounding boxes: p72 spans **8.20 x 9.58 in**, against 6.48-7.28 in wide
for every other page. It is the only page whose type runs nearly to the trim.

---

## D. Mask statistics

**27. OCR characters per printed page.**
72:790, 73:83, 74:9, 75:1597, 76:1553, 77:0, 78:1234, 79:1049.

**28. Ink coverage per page mask ranges 2.5x.**
p73 2.53%, p72 2.73%, p78 4.91%, p76 5.40%, p79 5.77%, p75 6.21%.

**29. Text-line counts measured from the 400 dpi masks.**
p72 35, p73 26, p75 34, p76 **49**, p78 35, p79 19. Page 76's 49 exceeds its
transcript line count, because the mask also captures ink the transcript omits.

**30. Page 73 has 39 glyph components against page 75's 1,352.**
Connected components >= 20 px: p73 39, p79 774, p78 869, p76 1266, p72 614,
p75 1352. Page 73 is the title spread and is almost entirely image.

---

## What these do and do not establish

None of these is a key. Clues 1, 14 and 2 are corrections that change how the
source must be handled: the page map is transposed, mask ink is white, and the
bilevel layers are 400 dpi rather than the 300-386 dpi recorded earlier.
Clues 21-26 are new content — page 72's source block had never been read, and
it contributes 21 printed numerals to a project whose numeric corpus was drawn
only from pages 75-79.
