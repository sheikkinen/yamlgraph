# Feature Request: FR-457 Eval Cherry-Pick and Model Refresh

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-05-24

## Summary

Extend `eval.sh` to accept optional model labels as CLI args for cherry-picking which models to test. Update the MODELS array: replace outdated `gpt-4o` with `gpt-5.3-codex`.

## Value Statement

Full eval runs 10 models at 300s timeout each — up to 50 minutes. Cherry-picking allows re-testing specific failed models or evaluating new models without re-running the entire suite.

## Problem

1. No way to run eval for a subset of models. Re-testing sonnet after the timeout increase requires running all 10.
2. `gpt-4o` is outdated. The Chaplain planner uses `gpt-5.3-codex` — this is the relevant OpenAI model to evaluate.

## Proposed Solution

### 1. Cherry-Pick via CLI Args

```bash
# Current usage (unchanged — runs all models):
./eval.sh feature-requests/FR-452.md

# New: optional label filter after FR path:
./eval.sh feature-requests/FR-452.md anthropic-sonnet mistral-large openai-codex
```

Implementation: capture remaining args after `$1`, skip models whose label isn't in the list (if non-empty).

### 2. Update MODELS Array

Replace:
```
"openai|gpt-4o|openai-4o|OPENAI_API_KEY"
```
With:
```
"openai|gpt-5.3-codex|openai-codex|OPENAI_API_KEY"
```

## Acceptance Criteria

- [ ] `./eval.sh <fr>` with no extra args runs all models (backward compatible)
- [ ] `./eval.sh <fr> label1 label2` runs only matching labels
- [ ] Non-matching labels are silently skipped with a log line
- [ ] `gpt-4o` replaced with `gpt-5.3-codex` in MODELS array
- [ ] Report includes only the models that were run

## Related

- FR-453 — Parent eval harness
- FR-454 — Timeout config (already enforced)
