# Watcher2 CI Remediation Demo

This demo showcases the new CI remediation functionality in Watcher2 (FR-279).

## What This Demonstrates

The watcher2 pipeline now includes self-healing CI remediation that can automatically fix common mechanical failures:

- **Python syntax errors** (IndentationError, SyntaxError)
- **Missing changelog fragments** in `changelog/unreleased/`
- **Missing diary entries** in `docs/diary/`
- **Pre-commit hook failures**

## How CI Remediation Works

1. **Wait Logic Fixed**: `wait_ci.sh` now correctly waits for all IN_PROGRESS checks to complete before evaluating FAILURE
2. **Remediation Loop**: When CI fails, watcher2.sh attempts up to 2 remediation cycles
3. **Copilot Diagnosis**: The `step-ci-remediate.yaml` graph invokes a copilot node to read CI logs and apply fixes
4. **Auto-commit**: Fixed code is automatically committed and pushed for re-verification

## Demo Graph

This demo simulates the CI remediation process by:
- Creating mock CI failure logs
- Running the remediation graph
- Showing the diagnosis and fix process

## Files

- `graph.yaml` - Demo graph that simulates CI remediation
- `prompts/simulate-ci-failure.yaml` - Creates mock CI failure scenarios
- `prompts/demonstrate-remediation.yaml` - Shows the remediation process

## Usage

```bash
yamlgraph graph run examples/demos/watcher2-ci-remediation/graph.yaml \
  --var failure_type="syntax" \
  --full
```

Where `failure_type` can be:
- `syntax` - Python syntax error
- `changelog` - Missing changelog fragment
- `diary` - Missing diary entry
- `precommit` - Pre-commit hook failure
