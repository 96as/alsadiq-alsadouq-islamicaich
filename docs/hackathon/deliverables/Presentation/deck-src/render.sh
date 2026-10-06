#!/bin/sh
# Render a pptx in deck-work to PDF and per-slide PNGs inside the throwaway image.
# Usage: sh render.sh <file.pptx> <outdir> [dpi]
set -e
PPTX="$1"
OUT="$2"
DPI="${3:-60}"
# The folder that holds the deck (this script's folder); a Windows path under Git Bash so Docker can mount it.
W="${DECK_WORK:-$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))}"
mkdir -p "$W/$OUT"
rm -f "$W/$OUT"/*.png "$W/$OUT"/*.pdf
MSYS_NO_PATHCONV=1 docker run --rm -v "$W:/work" -w /work deck-render:local sh -c "
  export HOME=/tmp
  soffice --headless --convert-to pdf --outdir /work/$OUT /work/$PPTX >/dev/null 2>&1
  base=\$(basename $PPTX .pptx)
  pdftoppm -png -r $DPI /work/$OUT/\$base.pdf /work/$OUT/s
  pdffonts /work/$OUT/\$base.pdf | sort -u > /work/$OUT/fonts.txt
  ls /work/$OUT | wc -l
"
