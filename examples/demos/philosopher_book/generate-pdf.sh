#!/usr/bin/env bash
# Generate book.pdf from book.md (final/ folder)
# Usage: ./generate-pdf.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FINAL_DIR="$SCRIPT_DIR/final"
BOOK_MD="$FINAL_DIR/book.md"
BOOK_PDF="$FINAL_DIR/book.pdf"
CLEAN_MD="$(mktemp /tmp/book_clean.XXXXXX.md)"
PAGED_MD="$(mktemp /tmp/book_paged.XXXXXX.md)"
FINAL_MD="$(mktemp /tmp/book_final.XXXXXX.md)"
HEADER_TEX="$(mktemp /tmp/book_header.XXXXXX.tex)"

trap 'rm -f "$CLEAN_MD" "$PAGED_MD" "$FINAL_MD" "$HEADER_TEX"' EXIT

echo "→ Cleaning Unicode symbols..."
sed 's/→/->/g; s/✗/x/g; s/❌/[FAIL]/g' "$BOOK_MD" > "$CLEAN_MD"

echo "→ Injecting page breaks before chapters..."
python3 - << PYEOF
with open('$CLEAN_MD') as f:
    lines = f.readlines()
out = []
first_h1 = True
for line in lines:
    if line.startswith('# '):
        if first_h1:
            first_h1 = False
        else:
            out.append('\n\\\\newpage\n\n')
    out.append(line)
with open('$PAGED_MD', 'w') as f:
    f.writelines(out)
PYEOF

echo "→ Building YAML front matter..."
python3 - << PYEOF
with open('$PAGED_MD') as f:
    content = f.read()
lines = content.split('\n')
rest = '\n'.join(lines[25:])
yaml_front = """---
title: "The Anatomy of the Wrong Fix: A Field Guide to Cognitive Traps in AI-Assisted Development"
author: "Claude Sonnet 4.6 — AI assistant, Copilot CLI runtime, VS Code"
date: "May 2026"
---

> *The fix was applied at the point of pain.*
> *The cause persisted at the point of entry.*
> *The investigation began with the symptom.*
> *It ended there too.*

"""
with open('$FINAL_MD', 'w') as f:
    f.write(yaml_front + rest)
PYEOF

echo "→ Writing LaTeX header..."
cat > "$HEADER_TEX" << 'TEXEOF'
\usepackage{etoolbox}
\pretocmd{\tableofcontents}{\clearpage}{}{}
TEXEOF

echo "→ Rendering PDF..."
pandoc "$FINAL_MD" \
  -o "$BOOK_PDF" \
  --pdf-engine=xelatex \
  -H "$HEADER_TEX" \
  -V geometry:margin=1in \
  -V fontsize=10pt \
  -V linestretch=1.3 \
  -V mainfont="Palatino" \
  -V monofont="Courier New" \
  -V colorlinks=true \
  -V linkcolor=black \
  --toc --toc-depth=1 \
  -V 'toc-title=Contents'

SIZE=$(du -h "$BOOK_PDF" | cut -f1)
echo "✓ Done: $BOOK_PDF ($SIZE)"
