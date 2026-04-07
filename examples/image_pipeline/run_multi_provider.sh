#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run_multi_provider.sh "your style prompt here"
#   CONCEPTS=5 COUNT=3 ./run_multi_provider.sh "your style prompt here"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"<style prompt>\""
  exit 1
fi

STYLE="$1"
CONCEPTS="${CONCEPTS:-3}"
COUNT="${COUNT:-5}"
GRAPH="examples/image_pipeline/graph.yaml"

for provider in mistral google inception; do
  echo "========================================"
  echo "  PROVIDER: $provider"
  echo "========================================"
  PROVIDER="$provider" yamlgraph graph run "$GRAPH" \
    --var style="$STYLE" \
    --var concepts_count="$CONCEPTS" \
    --var count="$COUNT" \
    --full
  echo
done
