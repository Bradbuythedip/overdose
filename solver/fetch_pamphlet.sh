#!/usr/bin/env bash
# Try to fetch the print pamphlet of a later OVERDOSE column, and REFUSE to
# leave a file behind that is not a real PDF.
#
# This runs on YOUR machine because the solver container is egress-blocked
# from every bitcoinmagazine host. If all of these fail, the page is behind a
# bot-check and you need a browser -- see the instructions it prints.
#
#   ./fetch_pamphlet.sh                     # Buy Love, Sell Fear
#   ./fetch_pamphlet.sh <url> <outfile>     # any direct URL you find
set -uo pipefail
cd "$(dirname "$0")"

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
ART="https://bitcoinmagazine.com/print/buy-love-sell-fear-bitcoin-magazine-withdrawal-issue"
OUT="${2:-buy_love_sell_fear.pdf}"

is_pdf () { [ -s "$1" ] && [ "$(head -c 5 "$1")" = "%PDF-" ]; }

try () {  # url outfile
  echo "  -> $1"
  curl -sSL --compressed -A "$UA" -H 'Accept: application/pdf,*/*' \
       --max-time 90 -o "$2.part" "$1" 2>/dev/null || return 1
  if is_pdf "$2.part"; then mv "$2.part" "$2"; return 0; fi
  rm -f "$2.part"; return 1
}

if [ $# -ge 1 ]; then
  echo "== direct URL"
  if try "$1" "$OUT"; then echo "  OK -> $OUT ($(wc -c < "$OUT") bytes)"; exit 0; fi
  echo "  that URL did not return a PDF"; exit 1
fi

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
