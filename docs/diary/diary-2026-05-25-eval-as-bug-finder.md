# Diary: Eval Harness as Bug Finder — FR-455/456/458/459

**Date:** 2026-05-25
**FRs:** FR-455, FR-456, FR-458, FR-459
**REQs:** REQ-YG-422, REQ-YG-100

## Summary

What started as "run the eval harness against FR-452" became four enforced
bugfixes. The multi-model eval didn't just measure judge quality — it
stress-tested the structured output pipeline across 10 providers and found
two real bugs (FR-458, FR-459) that only manifested in specific
provider×schema combinations.

## Key Insight: Eval as Fuzzer

The eval harness is accidentally a fuzzer. Each model exercises different
code paths through the structured output fallback chain:

```
extract_json (cheap) → with_structured_output (expensive)
  → function_calling retry (FR-458) → model_construct lenient (FR-456) → raise
```

- **Codex (gpt-5.3-codex):** Hit OpenAI strict schema rejection
  (`invalid_json_schema` / `additionalProperties`) — a path no other model
  triggered. FR-458 added `method="function_calling"` retry.
- **DeepSeek:** Returned prose instead of JSON. Unlike Anthropic's content-block
  issue (FR-449), DeepSeek simply ignored the schema instruction. FR-459
  added explicit JSON output instruction to the judge prompt.
- **Haiku:** Returned an ERROR — structured output schema too complex for the
  smaller model. No fix needed; model limitation.
- **Inception Mercury:** Worked perfectly — cheapest model that passed.

Without the eval harness running all 10 models, these bugs would have been
discovered in production, one user at a time.

## Traps Encountered

### 1. Jinja2/format() Brace Collision

**Trap:** `downstream_fix` — JSON code blocks in YAML prompts with literal
`{` characters crash when `str.format()` processes them.

The executor uses two template engines: `str.format()` for simple `{variable}`
substitution and Jinja2 for `{{ variable }}` syntax. Detection is in
`executor_base.py:68` — presence of `{{` or `{%` triggers Jinja2.

When FR-459 added JSON schema examples to the prompt, the `{` in
`{"verdict": "APPROVE"}` was interpreted as a format field. Fix: describe
the schema as prose ("a JSON object with field verdict...") without literal
braces.

**Heuristic:** In YAML prompts processed by `str.format()`, never use literal
braces. If you need JSON examples, either switch to Jinja2 (add `{{ }}`) or
describe the schema in prose.

### 2. Model Severity Calibration

**Trap:** `plausible_wrong_answer` — gpt-5.4-mini and Sonnet found the same
two blocking issues (heredoc feasibility, missing RED tests) but reached
different verdicts (REJECT vs AMEND).

The difference is calibration, not analysis. Mini treats unresolved questions
as fatal; Sonnet treats them as amendable. For a judge evaluating FRs, AMEND
is more appropriate — it says "fix these specific things" rather than "start
over." REJECT should be reserved for fundamentally misguided proposals.

**Observation:** Smaller models are harsher judges. They lack the nuance to
distinguish "needs revision" from "fundamentally broken." This makes them
good pre-screeners (fast, catches obvious issues) but poor final judges.

### 3. Timeout as False Negative

The first gpt-5.4-mini run timed out at 300s (default `EVAL_TIMEOUT`). The
JSON file contained an error stub, and the comparison report crashed trying
to parse it. The model was actively working — reading files, running tests —
just slow on first invocation. Rerun with `EVAL_TIMEOUT=600` completed in 25s.

**Heuristic:** First-run latency ≠ model speed. Cold starts, rate limits,
and connection setup inflate the first call. Always retry a timeout before
classifying a model as too slow.

## Model Quality Stratification (FR-452 eval)

| Tier | Models | Verdict | Depth |
|------|--------|---------|-------|
| Gold | Sonnet | AMEND | REQ IDs, commit hashes, file paths, severity tiers |
| Silver | Codex, Flash, Pro, Mistral, Mercury, DeepSeek | APPROVE | Reasonable but less actionable |
| Bronze | gpt-5.4-mini | REJECT | Correct blockers, wrong severity |
| Fail | Grok (REJECT, shallow), Haiku (ERROR) | — | Unusable for this task |

Sonnet at 97s is 4x slower than Mini at 25s but produces dramatically more
actionable output. For a judge role where the verdict drives enforcement
decisions, depth > speed.

## Process Observation

Four FRs (455, 456, 458, 459) were discovered, judged, enforced via TDD,
and pushed in a single session. The pipeline worked as designed:

1. Eval revealed bug → 2. FR written → 3. Judged (self-evident scope) →
4. RED test → 5. GREEN fix → 6. Commit → 7. Push

The constraint "no fix without a failing test" (Scripture #7) forced each
fix to be minimal and provable. FR-458's three tests (invalid_json_schema,
additionalProperties, non-schema error propagation) took longer to write
than the two-line fix, but they define the contract permanently.

## Fixes Applied

| FR | Fix | Tests |
|----|-----|-------|
| FR-455 | Strip temperature for reasoning models (o1/o3/o4) | 3 tests |
| FR-456 | `model_construct` lenient fallback when `parsed` is dict | 2 tests |
| FR-458 | `method="function_calling"` retry on strict schema error | 3 tests |
| FR-459 | JSON output instruction in judge prompt (brace-free) | Eval-verified |

## Seed

The eval harness found bugs that unit tests missed because unit tests mock
the LLM. Could the eval harness be promoted from "demo validation" to
"integration test gate" — a CI step that runs a subset of models on every
PR touching `executor.py` or `agent.py`? The cost is ~$0.10/model/run;
the value is catching provider-specific regressions before merge.
