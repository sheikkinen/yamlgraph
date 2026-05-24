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
echo "  --var fr_path=\"$FR_PATH\" --full" | tee -a "$LOG"
yamlgraph graph run examples/demos/judge/graph.yaml \
  --var fr_path="$FR_PATH" --full 2>&1 | tee -a "$LOG"

# Extract the structured verdict JSON from the graph output
python3 -c "
import json, re, sys

log = open('$LOG').read()
# Find the last JSON block in the output (the verdict dict)
matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', log)
for m in reversed(matches):
    try:
        obj = json.loads(m)
        if 'verdict' in obj or 'overall_verdict' in obj:
            json.dump(obj, sys.stdout, indent=2)
            print()
            with open('$VERDICT', 'w') as f:
                json.dump(obj, f, indent=2)
                f.write('\n')
            print(f'Verdict saved to $VERDICT', file=sys.stderr)
            sys.exit(0)
    except json.JSONDecodeError:
        continue
print('No verdict JSON found in output', file=sys.stderr)
sys.exit(1)
" 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
