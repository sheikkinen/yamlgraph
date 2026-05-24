# Feature Request: FR-453 Judge Model Evaluation Harness

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Partially Enforced (Step 1 complete, Step 2 pending)
**Effort:** 0.5 days
**Requested:** 2026-05-24

## Summary

Create a model evaluation harness (`examples/demos/judge/eval.sh`) that runs the judge demo across multiple LLM providers and models, comparing structured verdict quality.

**Judgement amendment:** Remove hardcoded `model: claude-sonnet-4-6` from the judge `graph.yaml`. Let the model resolution chain fall through to `PROVIDER` and `{PROVIDER}_MODEL` env vars. The eval script sets env vars per run — no `yq` patching, no temp files, no dependency on external tools.

## Value Statement

Developers can benchmark provider/model suitability for the judge role with a single command, producing a comparison report that informs model selection for CI gates, Chaplain pipelines, and ad-hoc review.

## Problem

The judge demo hardcodes `model: claude-sonnet-4-6` in its node config. This blocks the model resolution chain from reaching `PROVIDER` / `{PROVIDER}_MODEL` env vars. The fix is simple: remove the hardcoded `model:` line. Then `eval.sh` just sets env vars per run.

Resolution chain (from `agent.py`): `node_config.model` → `defaults.model` → `prompt_config.model` → `{PROVIDER}_MODEL` env → hardcoded default.

With `model:` removed from node config, step 1 is empty, and the chain falls through to env vars.

## Environment

### Available API Keys (.env)

| Provider | Key | Default Model |
|----------|-----|---------------|
| anthropic | `ANTHROPIC_API_KEY` | `claude-haiku-4-5` |
| openai | `OPENAI_API_KEY` | `gpt-4o` |
| google | `GOOGLE_API_KEY` | `gemini-2.0-flash` |
| mistral | `MISTRAL_API_KEY` | `mistral-large-latest` |
| deepseek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| xai | `XAI_API_KEY` | `grok-4-1-fast-reasoning` |
| inception | `INCEPTION_API_KEY` | `mercury-2` |
| replicate | `REPLICATE_API_TOKEN` | `ibm-granite/granite-4.0-h-small` |

### Not Available

| Provider | Reason |
|----------|--------|
| azure | No `AZURE_AI_API_KEY` set |
| vertex | No `GOOGLE_CLOUD_PROJECT` set (needs ADC, not just API key) |
| lmstudio | Local server, no `LMSTUDIO_BASE_URL` set |

### Provider Constraints

The judge agent uses `with_structured_output()` for the `JudgeVerdict` schema. Not all providers handle structured output equally:

- **Strong structured output**: anthropic, openai, google — native tool/schema support
- **Variable structured output**: mistral, deepseek, xai — may need JSON retry fallback
- **Unlikely to work**: replicate, inception — limited structured output support via LangChain

## Proposed Solution

### Step 1: Remove Hardcoded Model from Judge Graph

In `examples/demos/judge/graph.yaml`, remove `model: claude-sonnet-4-6` from the judge node. The node becomes:

```yaml
nodes:
  judge:
    type: agent
    prompt: judge
    temperature: 0
    tools: [read_file, search, list_dir, git_log, run_tests]
    max_iterations: 12
    state_key: verdict
```

Without `model:` or `provider:` in node config, the resolution chain falls through to:
- `PROVIDER` env var (default: `anthropic`)
- `{PROVIDER}_MODEL` env var (e.g. `ANTHROPIC_MODEL`, default: `claude-haiku-4-5`)

The `demo.sh` should set `PROVIDER=anthropic ANTHROPIC_MODEL=claude-sonnet-4-6` to preserve the current default behavior.

### Step 2: eval.sh — Env Var Loop

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/eval-results"
FR_PATH="${1:-feature-requests/FR-452-standalone-planner-demo.md}"

mkdir -p "$RESULTS_DIR"

# Model configurations: provider|model|label
MODELS=(
  "anthropic|claude-sonnet-4-6|anthropic-sonnet"
  "anthropic|claude-haiku-4-5|anthropic-haiku"
  "openai|gpt-4o|openai-4o"
  "openai|o4-mini|openai-o4-mini"
  "google|gemini-2.5-flash|google-flash"
  "google|gemini-2.5-pro|google-pro"
  "mistral|mistral-large-latest|mistral-large"
  "deepseek|deepseek-chat|deepseek"
  "xai|grok-4-1-fast-reasoning|xai-grok"
)

cd "$PROJECT_ROOT"
source .env

for entry in "${MODELS[@]}"; do
  IFS='|' read -r provider model label <<< "$entry"
  echo "=== $label ($provider/$model) ==="

  # Check API key
  KEY_VAR="${provider^^}_API_KEY"
  [[ "$provider" == "replicate" ]] && KEY_VAR="REPLICATE_API_TOKEN"
  if [[ -z "${!KEY_VAR:-}" ]]; then
    echo "  SKIP: $KEY_VAR not set"
    echo '{"status":"skipped","reason":"no_api_key"}' > "$RESULTS_DIR/$label.json"
    continue
  fi

  # Set provider + model via env vars — no yq, no temp files
  MODEL_VAR="${provider^^}_MODEL"
  START_TIME=$(date +%s)
  if timeout 120 env PROVIDER="$provider" "$MODEL_VAR=$model" \
    yamlgraph graph run examples/demos/judge/graph.yaml \
    --var fr_path="$FR_PATH" --json 2>"$RESULTS_DIR/$label.stderr" | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
verdict = data.get('verdict', {})
verdict['_meta'] = {'provider': '$provider', 'model': '$model', 'label': '$label'}
json.dump(verdict, sys.stdout, indent=2)
print()
" > "$RESULTS_DIR/$label.json"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    python3 -c "
import json
with open('$RESULTS_DIR/$label.json') as f:
    d = json.load(f)
d['_meta']['duration_seconds'] = $DURATION
with open('$RESULTS_DIR/$label.json', 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
"
    echo "  OK: $(python3 -c "import json; d=json.load(open('$RESULTS_DIR/$label.json')); print(d.get('verdict','?'), '-', d.get('classification','?'), f'({$DURATION}s)')")"
  else
    echo "  FAIL: timeout or error (see $label.stderr)"
    echo "{\"status\":\"error\",\"reason\":\"timeout_or_crash\",\"_meta\":{\"provider\":\"$provider\",\"model\":\"$model\",\"label\":\"$label\"}}" > "$RESULTS_DIR/$label.json"
  fi
done

# Comparison report
echo ""
echo "=== COMPARISON REPORT ==="
python3 << 'REPORT' | tee "$RESULTS_DIR/report.txt"
import json, glob
from collections import Counter

results = []
for f in sorted(glob.glob("$RESULTS_DIR/*.json")):
    with open(f) as fh:
        results.append(json.load(fh))

print(f"| {'Label':<20} | {'Verdict':<8} | {'Classification':<25} | {'Time':>5} | {'Criteria':>8} |")
print(f"|{'-'*22}|{'-'*10}|{'-'*27}|{'-'*7}|{'-'*10}|")
for r in results:
    meta = r.get("_meta", {})
    label = meta.get("label", "?")
    status = r.get("status")
    if status in ("skipped", "error"):
        print(f"| {label:<20} | {status:<8} | {r.get('reason',''):<25} | {'':>5} | {'':>8} |")
        continue
    verdict = r.get("verdict", "?")
    classif = r.get("classification", "?")
    duration = meta.get("duration_seconds", "?")
    criteria = r.get("criteria_results", [])
    passed = sum(1 for c in criteria if c.get("passed"))
    total = len(criteria)
    print(f"| {label:<20} | {verdict:<8} | {classif:<25} | {duration:>4}s | {passed}/{total:<5} |")

verdicts = [r.get("verdict") for r in results if r.get("verdict") and r.get("status") not in ("skipped","error")]
if verdicts:
    counts = Counter(verdicts)
    majority = counts.most_common(1)[0]
    print(f"\nConsensus: {majority[0]} ({majority[1]}/{len(verdicts)} models)")
    if len(counts) > 1:
        print(f"Disagreement: {dict(counts)}")
REPORT
echo ""
echo "Results: $RESULTS_DIR/"
```

No `yq` dependency. No temp files. Just `env PROVIDER=x MODEL_VAR=y yamlgraph graph run ...`.

### Output Structure

```
examples/demos/judge/eval-results/
├── anthropic-sonnet.json     # Full verdict + _meta (timing, provider)
├── anthropic-haiku.json
├── openai-4o.json
├── google-flash.json
├── ...
├── report.txt                # Comparison table
```

### Report Format

```
| Label                | Verdict  | Classification            |  Time | Criteria |
|----------------------|----------|---------------------------|-------|----------|
| anthropic-sonnet     | APPROVE  | framework_primitive       |   45s |    8/8   |
| anthropic-haiku      | APPROVE  | contrib_example           |   22s |    7/8   |
| openai-4o            | AMEND    | framework_primitive       |   38s |    6/8   |
| google-flash         | APPROVE  | contrib_example           |   15s |    8/8   |
| mistral-large        | error    | timeout_or_crash          |       |          |
| deepseek             | APPROVE  | contrib_example           |   28s |    7/8   |
| xai-grok             | APPROVE  | framework_primitive       |   32s |    8/8   |

Consensus: APPROVE (5/7 models)
Disagreement: {'APPROVE': 5, 'AMEND': 1}
```

### Key Metrics

1. **Verdict agreement** — do models reach the same conclusion?
2. **Classification agreement** — framework_primitive vs contrib_example vs pattern_doc
3. **Criteria pass rate** — which criteria do weaker models fail?
4. **Latency** — wall-clock time per model
5. **Structured output success** — can the model produce valid `JudgeVerdict` JSON?

## Acceptance Criteria

- [x] Judge `graph.yaml` has no hardcoded `model:` — uses env var fallthrough *(enforced c84f9cd4)*
- [x] `demo.sh` sets `PROVIDER=anthropic ANTHROPIC_MODEL=claude-sonnet-4-6` to preserve default behavior *(enforced c84f9cd4)*
- [x] Existing judge tests updated to reflect removed `model:` field — `test_no_hardcoded_model` added *(enforced c84f9cd4)*
- [ ] `eval.sh` sets `PROVIDER` and `{PROVIDER}_MODEL` env vars per run — no `yq`, no temp files
- [ ] Skips providers with missing API keys (graceful degradation)
- [ ] 120s timeout per model prevents hangs
- [ ] Each result saved as `eval-results/<label>.json` with `_meta` (provider, model, timing)
- [ ] Comparison report printed to stdout and saved to `eval-results/report.txt`
- [ ] Report includes: verdict, classification, duration, criteria pass rate, consensus
- [ ] Works with at least 5 providers (anthropic, openai, google, deepseek, xai)
- [ ] `eval-results/` added to `.gitignore` (results contain LLM output, not source)

## Alternatives Considered

- **Keep hardcoded model, use `yq` patching** — Original proposal. Rejected at judgement: adds `yq` dependency, temp file management, and complexity. Env var fallthrough uses the existing resolution chain.
- **Modify `--var` to support node config overrides** — Would require framework changes. Env var approach works within existing architecture.
- **Create separate graph YAMLs per model** — Tedious, unmaintainable.
- **Python test harness** — Heavier than needed. Shell + env vars + python one-liners suffices.

## Dependencies

- API keys in `.env` for each provider to test
- FR-450 judge demo (already enforced)
- FR-451 temperature fix (already enforced)

## Related

- FR-450 — Judge demo hardening (the judge being evaluated)
- FR-451 — Temperature zero fix (ensures `temperature: 0` works for all providers)
- FR-452 — Standalone planner demo (good FR to evaluate against)
- `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` — Chaplain judge uses different model than planner (cross-model by design)

## Notes

- The Chaplain pipeline deliberately uses **different models** for plan vs judge (`gpt-5.3-codex` vs `claude-sonnet-4.6`) to avoid anchoring bias. This eval tests whether that intuition holds — do different models produce different verdicts?
- `replicate` and `inception` providers are unlikely to handle `with_structured_output()` well. The eval should gracefully capture and report these failures rather than crash.
- `eval-results/` should be `.gitignore`'d but `report.txt` could optionally be committed as evidence of model selection rationale.

## Judgement

**Verdict:** AMEND → APPROVE (after amendment)

**Date:** 2026-05-24

**Enforcement note:** Step 1 (remove hardcoded model, update demo.sh, update tests) enforced in commit `c84f9cd4` on 2026-05-24. Step 2 (`eval.sh` harness) remains pending. Enforcement was triggered prematurely — the "amend" lifecycle command was misinterpreted as "enforce." See diary entry `diary-2026-05-24-lifecycle-verb-drift.md`.

The original proposal used `yq` to patch a temp copy of `graph.yaml` per model run — adding an external dependency and temp file management. The amendment is simpler: remove `model: claude-sonnet-4-6` from the judge node and let the existing resolution chain (`node_config → defaults → prompt_config → env var → default`) fall through to `PROVIDER` / `{PROVIDER}_MODEL` env vars. The eval script sets these per run.

This requires a minor change to the judge graph (removing one line) and updating `demo.sh` to set env vars explicitly. The change aligns with the framework's design — the resolution chain exists precisely for this use case.

**Classification:** contrib_example — evaluation tooling for the demo series.
