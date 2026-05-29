#!/bin/bash
set -euo pipefail

# Usage: ./demo.sh <path-to-fr-file>
if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <path-to-feature-request.md>"
  echo ""
  echo "Run the FR enforcer agent and save structured result to result.json."
  exit 1
fi

FR_PATH="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"
RESULT="$SCRIPT_DIR/result.json"

cd "$PROJECT_ROOT"
source .env 2>/dev/null || true

export PROVIDER="${PROVIDER:-anthropic}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-4-6}"

yamlgraph graph run examples/demos/enforcer/graph.yaml \
  --var fr_path="$FR_PATH" --json 2>>"$LOG" | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('implementation_result')
if not isinstance(result, dict):
    print('No structured result in output', file=sys.stderr)
    sys.exit(1)
json.dump(result, sys.stdout, indent=2)
print()
with open('$RESULT', 'w') as f:
    json.dump(result, f, indent=2)
    f.write('\\n')
print(f'Result saved to $RESULT', file=sys.stderr)
" 2>&1 | tee -a "$LOG"

echo -e "\\n✓ Graph execution completed successfully" | tee -a "$LOG"
