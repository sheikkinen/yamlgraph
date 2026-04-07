#!/usr/bin/env bash
set -euo pipefail

# Optional: pick provider from env, defaults to google
PROVIDER="${PROVIDER:-mistral}"

# Art movements (from Wikipedia list, curated)
styles=(
  "Ukiyo-e"
  "Vorticism"
)

for style in "${styles[@]}"; do
  echo "=== Running style: ${style} ==="
  PROVIDER="$PROVIDER" yamlgraph graph run examples/image_pipeline/graph.yaml \
    --var style="${style}" \
    --var concepts_count="3" \
    --var count="3" \
    --full
  echo
done
