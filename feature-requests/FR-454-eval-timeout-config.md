# Feature Request: FR-454 Eval Timeout and Tool Budget

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-24

## Summary

Increase `eval.sh` timeout from 120s to 300s and make it configurable. Optionally allow excluding expensive tools (e.g., `run_tests`) in eval mode to reduce wall-clock time per model.

## Value Statement

FR-453 eval showed 3/9 models (sonnet, 4o, mistral) timed out at 120s while actively investigating — they were killed mid-tool-call, producing no verdict. These are among the most capable models and their verdicts are the most valuable. Increasing timeout recovers them without any framework change.

## Problem

The `eval.sh` timeout of 120s is insufficient for thorough models:

| Model | Tool Calls at Kill | Last Tool | Notes |
|-------|-------------------|-----------|-------|
| anthropic-sonnet | 21 | `run_tests` | Most thorough investigator, killed mid-pytest |
| openai-4o | 6 | `run_tests` | Slow API latency, only 6 calls in 120s |
| mistral-large | 11 | `run_tests` | Moderate depth, killed mid-investigation |

The `run_tests` tool is the bottleneck — `pytest` takes ~20s per invocation, and thorough models call it late in their investigation after reading files and searching.

## Proposed Solution

### 1. Configurable Timeout

```bash
TIMEOUT="${EVAL_TIMEOUT:-300}"
# ...
if timeout "$TIMEOUT" env PROVIDER="$provider" ...
```

Default 300s (5 min). Override via `EVAL_TIMEOUT=600 ./eval.sh`.

### 2. Optional Tool Exclusion (Future)

Not in this FR. If needed later, the graph could accept a `--var skip_tools="run_tests"` and the prompt could conditionally skip tools. But 300s may be sufficient.

## Acceptance Criteria

- [ ] `eval.sh` timeout configurable via `EVAL_TIMEOUT` env var
- [ ] Default timeout increased from 120s to 300s
- [ ] Re-run eval with 300s produces verdicts from sonnet, 4o, and mistral

## Related

- FR-453 — Judge model evaluation harness (parent)
- `examples/demos/judge/eval.sh` — Script to modify
