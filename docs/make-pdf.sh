#!/usr/bin/env bash
# Regenerate docs/slides.pdf from docs/index.html.
#
# Requirements:
#   - A Chromium/Chrome with --print-to-pdf (set $CHROME, or it auto-detects
#     Google Chrome / a Playwright "Chrome for Testing" / chromium on PATH).
#   - poppler tools: pdfinfo, pdfseparate, pdfunite, pdftoppm.
#
# The deck's @media print rules lay out each slide as one 1280x720 landscape
# page. Headless Chromium appends a trailing blank page; this script strips it
# only if the last page is actually blank.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="file://$DIR/index.html"
OUT="$DIR/slides.pdf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CHROME="${CHROME:-}"
if [ -z "$CHROME" ]; then
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$HOME/Library/Caches/ms-playwright/chromium-"*/chrome-mac-arm64/"Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v google-chrome 2>/dev/null || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
  done
fi
[ -n "$CHROME" ] || { echo "No Chrome/Chromium found; set CHROME=/path/to/chrome" >&2; exit 1; }

"$CHROME" --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=20000 --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer --print-to-pdf="$TMP/full.pdf" "$HTML"

N=$(pdfinfo "$TMP/full.pdf" | awk '/^Pages:/{print $2}')

# Is the last page blank? (low pixel variance => uniform => blank)
pdftoppm -png -r 30 -f "$N" -l "$N" "$TMP/full.pdf" "$TMP/last" >/dev/null 2>&1
LASTPNG=$(ls "$TMP"/last*.png | head -1)
BLANK=$(python3 - "$LASTPNG" <<'PY'
import sys,struct,zlib
d=open(sys.argv[1],'rb').read();pos=8;idat=b''
while pos<len(d):
    ln=struct.unpack('>I',d[pos:pos+4])[0];t=d[pos+4:pos+8]
    if t==b'IDAT':idat+=d[pos+8:pos+8+ln]
    pos+=12+ln
raw=zlib.decompress(idat);s=raw[:80000];m=sum(s)/len(s)
print(1 if sum((b-m)**2 for b in s)/len(s) < 10 else 0)
PY
)
KEEP=$N
[ "$BLANK" = "1" ] && KEEP=$((N-1))

pdfseparate -f 1 -l "$KEEP" "$TMP/full.pdf" "$TMP/pg-%d.pdf"
pdfunite $(for i in $(seq 1 "$KEEP"); do echo "$TMP/pg-$i.pdf"; done) "$OUT"
echo "wrote $OUT ($KEEP pages)"
