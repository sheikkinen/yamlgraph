#!/usr/bin/env bash
set -euo pipefail

# Restyle every prompt in a file to a single target art style.
#
# Usage:
#   ./run.sh <input_file> "<target style>"
#
# Examples:
#   ./run.sh ~/Documents/prompts/sketches-2026-07-27.txt \
#     "John William Waterhouse, Pre-Raphaelite oil painting"
#
#   PROVIDER=mistral ./run.sh prompts.txt "Ukiyo-e woodblock print"
#
# The provider is pinned to Mistral on the graph node; a MISTRAL_API_KEY in
# .env (repo root) is loaded automatically if present. Output is a timestamped
# outputs/image_pipeline/<ts>/prompts.txt, one restyled prompt per line.

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input_file> \"<target style>\"" >&2
  exit 1
fi

INPUT_FILE="$1"
TARGET_STYLE="$2"
GRAPH="examples/style_convert/graph.yaml"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE" >&2
  exit 1
fi

# Resolve to an absolute path so the graph can read it regardless of CWD.
INPUT_FILE="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"

# Load repo-root .env (MISTRAL_API_KEY etc.) if available.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "$REPO_ROOT/.env"
  set +a
fi

echo "=== Converting styles in ${INPUT_FILE} -> ${TARGET_STYLE} ==="
yamlgraph graph run "$GRAPH" \
  --var input_file="$INPUT_FILE" \
  --var target_style="$TARGET_STYLE" \
  --full
