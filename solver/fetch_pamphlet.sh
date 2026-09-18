#!/usr/bin/env bash
# Try to fetch the print pamphlet of a later OVERDOSE column, and REFUSE to
# leave a file behind that is not a real PDF.
#
# This runs on YOUR machine because the solver container is egress-blocked
# from every bitcoinmagazine host. If all of these fail, the page is behind a
# bot-check and you need a browser -- see the instructions it prints.
#
#   ./fetch_pamphlet.sh                     # Buy Love, Sell Fear
#   ./fetch_pamphlet.sh --inspect           # what does the page actually offer?
#   ./fetch_pamphlet.sh <url> <outfile>     # any direct URL you find
set -uo pipefail
cd "$(dirname "$0")"

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
ART="https://bitcoinmagazine.com/print/buy-love-sell-fear-bitcoin-magazine-withdrawal-issue"
# Found by --inspect on the article page: the "download" link does not point at
# a PDF on the magazine's host, it points at a Mailchimp landing page.
DL="https://mailchi.mp/bitcoinmagazine.com/buylovesellfear"
PREVIEW="https://bitcoinmagazine.com/wp-content/uploads/2024/11/keiser_preview.jpg"
OUT="${2:-buy_love_sell_fear.pdf}"

is_pdf () { [ -s "$1" ] && [ "$(head -c 5 "$1")" = "%PDF-" ]; }

try () {  # url outfile
  echo "  -> $1"
  curl -sSL --compressed -A "$UA" -H 'Accept: application/pdf,*/*' \
       --max-time 90 -o "$2.part" "$1" 2>/dev/null || return 1
  if is_pdf "$2.part"; then mv "$2.part" "$2"; return 0; fi
  rm -f "$2.part"; return 1
}

if [ "${1:-}" = "--inspect" ]; then
  TARGET="${2:-$ART}"
  echo "== saving $TARGET and listing everything that could be the print edition"
  curl -sSL --compressed -A "$UA" --max-time 90 "$TARGET" -o article_page.html
  echo "  saved article_page.html ($(wc -c < article_page.html) bytes)"
  echo
  echo "-- any .pdf anywhere in the HTML:"
  grep -oiE '[^"'"'"' (]+\.pdf' article_page.html | sort -u | head -20 || echo "   none"
  echo
  echo "-- iframes / embedded viewers (issuu, flipbook, scribd, drive, yumpu):"
  grep -oiE '<iframe[^>]+src="[^"]+"' article_page.html | head -10 || true
  grep -oiE 'https?://[^"'"'"' ]*(issuu|flipbook|scribd|yumpu|drive\.google|dropbox|calameo)[^"'"'"' ]*' article_page.html | sort -u | head -10 || echo "   none"
  echo
  echo "-- links whose text or href mentions download / print / issue / pdf:"
  grep -oiE '<a[^>]+href="[^"]+"[^>]*>[^<]{0,60}' article_page.html \
    | grep -iE 'download|print|issue|pdf|magazine/[0-9]|store' | sort -u | head -20 || echo "   none"
  echo
  echo "-- og:image / cover art (a print facsimile often ships as page images):"
  grep -oiE '<meta[^>]+(og:image|twitter:image)[^>]+>' article_page.html | head -5 || true
  echo
  echo "  Send me the output above. If there is no PDF and no viewer, this"
  echo "  column has no print edition online and test B cannot run on it."
  exit 0
fi

if [ $# -ge 1 ]; then
  echo "== direct URL"
  if try "$1" "$OUT"; then echo "  OK -> $OUT ($(wc -c < "$OUT") bytes)"; exit 0; fi
  echo "  that URL did not return a PDF"; exit 1
fi

echo "== 0. the download landing page found on the article"
if curl -sSL --compressed -A "$UA" --max-time 90 "$DL" -o dl_page.html 2>/dev/null; then
  echo "  fetched $DL ($(wc -c < dl_page.html) bytes)"
  grep -oiE 'https?://[^"'"'"' )]+\.pdf' dl_page.html | sort -u > /tmp/dl_pdfs.txt || true
  if [ -s /tmp/dl_pdfs.txt ]; then
    echo "  PDF link(s) on the download page:"; cat /tmp/dl_pdfs.txt
    while read -r u; do try "$u" "$OUT" && { echo "  OK -> $OUT ($(wc -c < "$OUT") bytes)"; exit 0; }; done < /tmp/dl_pdfs.txt
  else
    echo "  no direct .pdf on the download page (it is probably an email form)."
    echo "  Inspect it yourself:  ./fetch_pamphlet.sh --inspect '$DL'"
    echo "  If it asks for an email, submit one -- the PDF arrives by mail."
  fi
else
  echo "  could not fetch the download page"
fi

echo
echo "== 0b. the print preview image (may show the printed column itself)"
if curl -sSL --compressed -A "$UA" --max-time 90 "$PREVIEW" -o keiser_preview.jpg 2>/dev/null \
   && [ -s keiser_preview.jpg ]; then
  echo "  saved keiser_preview.jpg ($(wc -c < keiser_preview.jpg) bytes) -- open it:"
  echo "  if it shows the PRINTED column, its line breaks are the ones the test needs,"
  echo "  and a careful transcription of them feeds ./run.sh musset <file>.txt"
else
  rm -f keiser_preview.jpg
  echo "  preview not fetched"
fi

echo
echo "== 1. looking for a PDF link on the article page"
PAGE=$(curl -sSL --compressed -A "$UA" --max-time 90 "$ART" 2>/dev/null || true)
if [ -n "$PAGE" ]; then
  echo "$PAGE" | grep -oiE 'https?://[^"'"'"' )]+\.pdf' | sort -u | head -10 > /tmp/pdflinks.txt || true
  if [ -s /tmp/pdflinks.txt ]; then
    echo "  candidate PDF links found:"; cat /tmp/pdflinks.txt
    while read -r u; do try "$u" "$OUT" && { echo "  OK -> $OUT"; exit 0; }; done < /tmp/pdflinks.txt
  else
    echo "  no .pdf link in the page HTML"
  fi
else
  echo "  could not load the article page (bot-check or network)"
fi

echo
echo "== could not fetch a PDF automatically."
cat <<'EOS'

  Do it by hand, and mind WHICH artifact you take:

  1. Open in a browser:
     https://bitcoinmagazine.com/print/buy-love-sell-fear-bitcoin-magazine-withdrawal-issue
  2. Look for the magazine's own download / "read the print edition" control.
     Save that file as  buy_love_sell_fear.pdf  in this directory.
  3. Run:  ./run.sh musset buy_love_sell_fear.pdf

  DO NOT use File > Print > Save as PDF on the web article. That produces a
  valid PDF whose line breaks are the browser's reflow, not the typesetter's.
  The test would run on lines that were never printed and the answer would
  mean nothing. print_musset.py warns when it sees that shape, but the only
  real fix is to take the right file.

  If no print PDF exists for this column, this test cannot be run on it.
  The alternative is a line-faithful transcription of the printed column --
  one printed line per text line -- which the tool accepts directly:
     ./run.sh musset buy_love_sell_fear.txt
EOS
exit 1
