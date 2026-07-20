#!/usr/bin/env bash
set -euo pipefail

ROUTE_FILE="outputs/routes/route_overlay_cli_demo.route.jsonl"
OUT_DIR="examples/route_overlay_cli/outputs"

mkdir -p outputs/routes
mkdir -p "$OUT_DIR"

echo "[1/2] Generate route log with router demo"
YAMLGRAPH_ROUTE_LOG="$ROUTE_FILE" \
  yamlgraph graph run examples/demos/router/graph.yaml \
  --var topic="route overlay cli demo" \
  --var style="concise" \
  --full

echo "[2/2] Render authored + overlay artifacts with mmdc"
python examples/route_overlay_cli/cli.py render \
  --graph examples/demos/router/graph.yaml \
  --route "$ROUTE_FILE" \
  --out-dir "$OUT_DIR" \
  --format svg

echo "Done. Artifacts in $OUT_DIR"
