#!/usr/bin/env bash
# FR-453: Multi-model judge evaluation harness
# Runs the judge demo across available LLM providers, comparing structured verdicts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/eval-results"
FR_PATH="${1:-feature-requests/FR-452-standalone-planner-demo.md}"

if [[ ! -f "$PROJECT_ROOT/$FR_PATH" ]]; then
  echo "Usage: $0 <path-to-feature-request.md>"
  echo ""
  echo "Run the judge demo across multiple LLM providers and compare verdicts."
  echo ""
  echo "Example:"
  echo "  $0 feature-requests/FR-452-standalone-planner-demo.md"
  exit 1
fi

mkdir -p "$RESULTS_DIR"
cd "$PROJECT_ROOT"
source .env 2>/dev/null || true

# Model configurations: provider|model|label|api_key_var
MODELS=(
  "anthropic|claude-sonnet-4-6|anthropic-sonnet|ANTHROPIC_API_KEY"
  "anthropic|claude-haiku-4-5|anthropic-haiku|ANTHROPIC_API_KEY"
  "openai|gpt-4o|openai-4o|OPENAI_API_KEY"
  "openai|o4-mini|openai-o4-mini|OPENAI_API_KEY"
  "google|gemini-2.5-flash|google-flash|GOOGLE_API_KEY"
  "google|gemini-2.5-pro|google-pro|GOOGLE_API_KEY"
  "mistral|mistral-large-latest|mistral-large|MISTRAL_API_KEY"
  "deepseek|deepseek-chat|deepseek|DEEPSEEK_API_KEY"
  "xai|grok-4-1-fast-reasoning|xai-grok|XAI_API_KEY"
)

TOTAL=${#MODELS[@]}
CURRENT=0

echo "=== FR-453 Judge Model Evaluation ==="
echo "FR: $FR_PATH"
echo "Models: $TOTAL"
echo ""

for entry in "${MODELS[@]}"; do
  IFS='|' read -r provider model label key_var <<< "$entry"
  CURRENT=$((CURRENT + 1))
  echo "[$CURRENT/$TOTAL] $label ($provider/$model)"

  # Check API key
  if [[ -z "${!key_var:-}" ]]; then
    echo "  SKIP: $key_var not set"
    echo "{\"status\":\"skipped\",\"reason\":\"no_api_key\",\"_meta\":{\"provider\":\"$provider\",\"model\":\"$model\",\"label\":\"$label\"}}" > "$RESULTS_DIR/$label.json"
    continue
  fi

  # Set provider + model via env vars
  MODEL_VAR="$(echo "${provider}" | tr '[:lower:]' '[:upper:]')_MODEL"
  START_TIME=$(date +%s)

  if timeout 120 env PROVIDER="$provider" "${MODEL_VAR}=${model}" \
    yamlgraph graph run examples/demos/judge/graph.yaml \
    --var fr_path="$FR_PATH" --json 2>"$RESULTS_DIR/$label.stderr" | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
verdict = data.get('verdict', {})
if not isinstance(verdict, dict):
    print('No structured verdict in output', file=sys.stderr)
    sys.exit(1)
verdict['_meta'] = {'provider': '$provider', 'model': '$model', 'label': '$label'}
json.dump(verdict, sys.stdout, indent=2)
print()
" > "$RESULTS_DIR/$label.json"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    # Inject timing into result
    python3 -c "
import json
with open('$RESULTS_DIR/$label.json') as f:
    d = json.load(f)
d['_meta']['duration_seconds'] = $DURATION
with open('$RESULTS_DIR/$label.json', 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
"
    VERDICT=$(python3 -c "import json; d=json.load(open('$RESULTS_DIR/$label.json')); print(d.get('verdict','?'))")
    echo "  OK: $VERDICT (${DURATION}s)"
  else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo "  FAIL: timeout or error after ${DURATION}s (see $label.stderr)"
    echo "{\"status\":\"error\",\"reason\":\"timeout_or_crash\",\"_meta\":{\"provider\":\"$provider\",\"model\":\"$model\",\"label\":\"$label\",\"duration_seconds\":$DURATION}}" > "$RESULTS_DIR/$label.json"
  fi
done

# Comparison report
echo ""
echo "=== COMPARISON REPORT ==="
REPORT_SCRIPT=$(cat << 'PYEOF'
import json, glob, os, sys

results_dir = sys.argv[1]
results = []
for f in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
    with open(f) as fh:
        results.append(json.load(fh))

if not results:
    print("No results found.")
    sys.exit(0)

print(f"| {'Label':<20} | {'Verdict':<8} | {'Classification':<25} | {'Time':>5} | {'Criteria':>8} |")
print(f"|{'-'*22}|{'-'*10}|{'-'*27}|{'-'*7}|{'-'*10}|")

from collections import Counter
verdicts = []

for r in results:
    meta = r.get("_meta", {})
    label = meta.get("label", "?")
    status = r.get("status")
    if status in ("skipped", "error"):
        reason = r.get("reason", "")
        duration = meta.get("duration_seconds", "")
        t = f"{duration}s" if duration else ""
        print(f"| {label:<20} | {status:<8} | {reason:<25} | {t:>5} | {'':>8} |")
        continue
    verdict = r.get("verdict", "?")
    classif = r.get("classification", "?")
    duration = meta.get("duration_seconds", "?")
    criteria = r.get("criteria_results", [])
    passed = sum(1 for c in criteria if c.get("passed"))
    total = len(criteria)
    print(f"| {label:<20} | {verdict:<8} | {classif:<25} | {duration:>4}s | {passed}/{total:<5} |")
    verdicts.append(verdict)

if verdicts:
    counts = Counter(verdicts)
    majority = counts.most_common(1)[0]
    print(f"\nConsensus: {majority[0]} ({majority[1]}/{len(verdicts)} models)")
    if len(counts) > 1:
        print(f"Disagreement: {dict(counts)}")
PYEOF
)
python3 -c "$REPORT_SCRIPT" "$RESULTS_DIR" | tee "$RESULTS_DIR/report.txt"

echo ""
echo "Results: $RESULTS_DIR/"
