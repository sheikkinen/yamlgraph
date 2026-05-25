#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"
PLAN_JSON="$SCRIPT_DIR/plan.json"

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <path-to-topic-file>"
  echo ""
  echo "Run the FR planner agent and save structured plan to plan.json."
  echo ""
  echo "Example:"
  echo "  $0 .chaplain/inbox/refactor-state-builder.md"
  exit 1
fi

TOPIC_FILE="$1"

cd "$PROJECT_ROOT"
source .env 2>/dev/null || true

# FR-453: Model set via env vars, not hardcoded in graph.yaml
export PROVIDER="${PROVIDER:-anthropic}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-4-6}"

echo "yamlgraph graph run examples/demos/planner/graph.yaml \\" | tee "$LOG"
echo "  --var topic_file=\"$TOPIC_FILE\" --json" | tee -a "$LOG"

yamlgraph graph run examples/demos/planner/graph.yaml \
  --var topic_file="$TOPIC_FILE" --json 2>>"$LOG" | \
python3 -c "
import json, sys

data = json.load(sys.stdin)
plan = data.get('plan_result')
if not isinstance(plan, dict):
    print('No structured plan in output', file=sys.stderr)
    sys.exit(1)
json.dump(plan, sys.stdout, indent=2)
print()
with open('$PLAN_JSON', 'w') as f:
    json.dump(plan, f, indent=2)
    f.write('\n')
print(f'Plan saved to $PLAN_JSON', file=sys.stderr)
" 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
