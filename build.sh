#!/bin/zsh
# Compile a LaTeX resume → build/<name>.pdf (+ PNG preview).
#
# Usage:  ./build.sh [path/to/resume.tex]
#         Defaults to inputs/resume.tex; falls back to the shipped example if that
#         doesn't exist yet, so a fresh clone builds something out of the box.
#
# Strips fontawesome5 (which can crash tectonic on some machines) and swaps
# \faExternalLink* → a nearrow arrow so the file still compiles without the font.
# For the final application PDF with real icons, compile the original .tex on Overleaf.
set -e
cd "$(dirname "$0")"

SRC="${1:-inputs/resume.tex}"
if [[ ! -f "$SRC" ]]; then
  SRC="inputs/resume.example.tex"
  echo "No inputs/resume.tex found — building the example ($SRC)."
fi

NAME="$(basename "${SRC%.tex}")"
mkdir -p build

sed -e 's/\\faExternalLink\*/$\\nearrow$/g' \
    -e 's/^\\usepackage{fontawesome5}/%\\usepackage{fontawesome5}/' \
    -e 's/^\\input{glyphtounicode}/%\\input{glyphtounicode}/' \
    -e 's/^\\pdfgentounicode=1/%\\pdfgentounicode=1/' \
    "$SRC" > "build/_preview.tex"

tectonic build/_preview.tex --outdir build >/dev/null 2>&1

mv "build/_preview.pdf" "build/${NAME}.pdf"

# PNG preview: sips on macOS, else pdftoppm if available.
if command -v sips >/dev/null 2>&1; then
  sips -s format png --resampleWidth 1700 "build/${NAME}.pdf" \
       --out "build/${NAME}-preview.png" >/dev/null 2>&1 || true
elif command -v pdftoppm >/dev/null 2>&1; then
  pdftoppm -png -r 150 "build/${NAME}.pdf" "build/${NAME}-preview" >/dev/null 2>&1 || true
fi

echo "→ build/${NAME}.pdf"
