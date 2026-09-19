# Is anything hidden in the portfolio PDF? No. (2026-09-19)

`evidence/HG-GovtDebt-redact.pdf` is 31,976,280 bytes for 12 pages, which looks
heavy enough to be worth asking. It is not. The size is fully explained, to
99.94% of the bytes, and the structural checks are clean.

## Byte accounting

Each page is one full-bleed 300 dpi photographic image (2550x3300 = US Letter)
plus a small soft-mask alpha channel.

| component | bytes | share |
|---|---|---|
| 12 main page images, `/DCTDecode` (JPEG) | 31,774,427 | 99.37% |
| 12 `/SMask` alpha channels, `/FlateDecode` | 181,632 | 0.57% |
| **all image streams** | **31,956,059** | **99.94%** |
| everything else: xref, `/ObjStm`, page dicts, XMP packet | 20,221 | 0.06% |

**There are 20,221 bytes in the entire file that are not image data**, and they
are all accounted for as PDF structure. There is no room for a payload.

Average 2.65 MB per page, 2.52 bits per pixel over the main images. That is an
ordinary high-quality print JPEG — an 8.4-megapixel photographic page at
print quality lands exactly there.

## The checks that could have found something

| test | result |
|---|---|
| bytes after the final `%%EOF` | **1** (a single `\r`) |
| trailing data after JPEG `EOI` marker, per page | **0 on all 12** — the same test run on the phone JPEGs in `binary_steg_scan.md` |
| `/EmbeddedFile`, `/Filespec`, `/Names /EmbeddedFiles` | **absent** |
| `/JavaScript`, `/JS`, `/OpenAction`, `/Launch`, `/RichMedia`, `/AcroForm`, `/XFA` | **absent** |
| `/Encrypt` | absent — the file is not encrypted |
| `%%EOF` count | 2, and the first is at offset 449 |

### The two that looked suspicious, and why neither is

**`/EF` appears 3 times.** `/EF` is the embedded-file key of a Filespec
dictionary, so this is worth chasing. All three occurrences sit *inside
compressed image data* — the surrounding bytes are 36–47% printable, i.e. pure
binary noise — and two of them have byte-identical context 6,086 bytes apart,
which is a repeated compression pattern. There is no `/Filespec` and no
`/Names /EmbeddedFiles` anywhere in the file. **False positive.**

**A `%%EOF` at offset 449, long before the end.** That is *linearization*
(fast web view), and it supplies the strongest single check in this list. The
linearization dictionary is the first object in the file:

```
<</Linearized 1 /L 31976280 /O 81 /E 3247223 /N 12 /T 31975878 /H [465 218]>>
```

`/L 31976280` is the total file length **the PDF declares about itself**, and it
equals the actual file size to the byte. `/N 12` matches the 12 pages. Anything
appended after the fact would break that self-declaration.

## A softer corroboration

Per-page image sizes track visual complexity rather than sitting at a uniform
inflated size:

```
p11 4,158,161  gold bars / Reagan page, heavily photographic
p02 3,465,527  banknote-pile photograph
p01 3,227,555  cover: flag, falling notes, gold coins
...
p12   813,606  back cover, largely flat colour
```

A uniform hidden payload would show as a flat floor across pages. It does not.

## Provenance, for the record

```
/Creator      Adobe Illustrator CC 2017 (Windows) 21.0.2
/Producer     Adobe Photoshop for Macintosh -- Image Conversion Plug-in
/CreationDate 2023-01-16 11:42:24 -08:00
/ModDate      2023-01-16 11:42:35 -08:00
```

Eleven seconds between creation and modification is a straight export, not an
edited document. No text layer on any page (0 fonts, 12 chars extracted total),
which is why the pages are flat images: it is a portfolio export of finished
artwork, not a working file.

## Conclusion

The PDF is big because it is twelve print-resolution photographic pages. The
find in it is the one already recorded — the `CL76841714A` banknote on the
cover (`serial_branch_closed_by_reuse.md`) — and that was visible in the
artwork, not hidden in the container.
