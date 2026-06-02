#!/usr/bin/env bash
# Meta demo — apply a natural-language verb to a code artifact.
#
# Usage:
#   ./demo.sh "explain structure" examples/demos/meta/graph.yaml
#
# With no arguments, runs the headline self-referential case: the demo
# explains its own graph YAML.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"

VERB="${1:-explain structure}"
TARGET="${2:-examples/demos/meta/graph.yaml}"

cd "$PROJECT_ROOT"
source .env 2>/dev/null || true

# Model set via env vars, not hardcoded in graph.yaml
export PROVIDER="${PROVIDER:-anthropic}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-4-6}"

echo "yamlgraph graph run examples/demos/meta/graph.yaml \\" | tee "$LOG"
echo "  --var verb=\"$VERB\" \\" | tee -a "$LOG"
echo "  --var target=\"$TARGET\" --json" | tee -a "$LOG"

yamlgraph graph run examples/demos/meta/graph.yaml \
  --var verb="$VERB" \
  --var target="$TARGET" --json 2>>"$LOG" | \
python3 -c "
import json, sys

data = json.load(sys.stdin)
result = data.get('result')
if not isinstance(result, dict):
    print('No structured MetaResult in output', file=sys.stderr)
    sys.exit(1)
json.dump(result, sys.stdout, indent=2)
print()
" 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
