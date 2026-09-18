#!/usr/bin/env bash
# Fetch both print-preview images and commit them so the solver can SEE them.
# The solver container cannot reach these hosts; the repo is the way in.
set -uo pipefail
cd "$(dirname "$0")"
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
mkdir -p previews

get () { # url outfile
  curl -sSL --compressed -A "$UA" --max-time 90 -o "previews/$2" "$1" 2>/dev/null
  if [ -s "previews/$2" ]; then
    echo "  $2  $(wc -c < "previews/$2") bytes  $(file -b "previews/$2" 2>/dev/null | cut -c1-60)"
  else
    rm -f "previews/$2"; echo "  $2: FAILED"
  fi
}

echo "== fetching print previews"
get "https://bitcoinmagazine.com/wp-content/uploads/2024/11/keiser_preview.jpg" keiser_preview.jpg
get "https://mcusercontent.com/1c17effa0923c7e916d862f99/images/df5fd5fb-5153-5ecc-e66b-4cd5909015f7.jpg" mailchimp_preview.jpg
[ -f keiser_preview.jpg ] && cp -f keiser_preview.jpg previews/ 2>/dev/null

echo
echo "== getting them to the solver"
echo "  Files are in: $(pwd)/previews/"
ls -l previews/*.jpg 2>/dev/null | sed 's/^/    /'
echo
echo "  SIMPLEST: attach those files directly in the chat. No git needed."
echo
echo "  Only if you would rather push them (needs a GitHub token configured):"
echo "    git add -f previews/*.jpg && git commit -m 'print previews' && git push origin master"
echo "  If push asks for a username, you have no credentials set -- use the"
echo "  attach route instead; it is faster and needs nothing."
