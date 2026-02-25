#!/usr/bin/env bash
# Build script for YAMLGraph Development Pipeline eBook
# FR-100: Renders Markdown chapters to HTML (and PDF if LaTeX available)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for pandoc
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc not found. Install with: brew install pandoc"
    exit 1
fi

# Create dist directory
mkdir -p dist

# Concatenate chapters with page breaks
echo "Concatenating chapters..."
cat \
    00-introduction.md \
    <(echo -e "\n\n---\n\n") \
    01-doctrine.md \
    <(echo -e "\n\n---\n\n") \
    02-precommit-gates.md \
    <(echo -e "\n\n---\n\n") \
    03-chaplain-pipeline.md \
    <(echo -e "\n\n---\n\n") \
    04-inquisitor.md \
    <(echo -e "\n\n---\n\n") \
    05-diary-system.md \
    > dist/combined.md 2>/dev/null || {
        echo "Warning: Some chapter files are missing. Run the authoring pipeline first:"
        echo "  yamlgraph graph run examples/ebook/graph.yaml --var output_dir=docs/ebook --var date=\"\$(date +%Y-%m-%d)\" --full"
        exit 1
    }

# Build HTML with standalone styling
echo "Building HTML..."
pandoc dist/combined.md \
    -o dist/yamlgraph-dev-pipeline.html \
    --standalone \
    --toc \
    --toc-depth=2 \
    --metadata title="YAMLGraph Development Pipeline" \
    --css=https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css \
    -V lang=en

echo "✓ HTML: dist/yamlgraph-dev-pipeline.html"

# Try to build PDF if LaTeX is available
if command -v pdflatex &> /dev/null || command -v xelatex &> /dev/null; then
    echo "Building PDF..."
    pandoc dist/combined.md \
        -o dist/yamlgraph-dev-pipeline.pdf \
        --toc \
        --toc-depth=2 \
        --metadata title="YAMLGraph Development Pipeline" \
        --pdf-engine=xelatex 2>/dev/null || {
            echo "⚠ PDF build failed (LaTeX errors). HTML is available."
        }
    [ -f dist/yamlgraph-dev-pipeline.pdf ] && echo "✓ PDF: dist/yamlgraph-dev-pipeline.pdf"
else
    echo "⚠ PDF skipped (LaTeX not installed)"
fi

# Cleanup
rm -f dist/combined.md

echo "Done!"
