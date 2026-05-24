#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"
VERDICT="$SCRIPT_DIR/judgement.json"

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <path-to-feature-request.md>"
  echo ""
  echo "Run the FR judge agent and save structured verdict to judgement.json."
  echo ""
  echo "Example:"
  echo "  $0 feature-requests/FR-448-agent-structured-output.md"
  exit 1
fi

FR_PATH="$1"

cd "$PROJECT_ROOT"

echo "yamlgraph graph run examples/demos/judge/graph.yaml \\" | tee "$LOG"
echo "  --var fr_path=\"$FR_PATH\" --json" | tee -a "$LOG"
yamlgraph graph run examples/demos/judge/graph.yaml \
  --var fr_path="$FR_PATH" --json 2>>"$LOG" | \
python3 -c "
import json, sys

data = json.load(sys.stdin)
verdict = data.get('verdict')
if not isinstance(verdict, dict):
    print('No structured verdict in output', file=sys.stderr)
    sys.exit(1)
json.dump(verdict, sys.stdout, indent=2)
print()
with open('$VERDICT', 'w') as f:
    json.dump(verdict, f, indent=2)
    f.write('\n')
print(f'Verdict saved to $VERDICT', file=sys.stderr)
" 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
