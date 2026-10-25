# Feature Request: FR-1152 `--token-usage` counts thinking tokens

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-10-25
**First consumer / first event:** game-engine's stage 5 graph for *A Voyage to Arcturus* chapter I
(`workflows/chapter-embellish`, prompt 317 in game-engine): its cost record must give "tokens, thinking tokens and
dollars per step" for one Opus 5.5 plan call at effort `low`, run right after this merges. Today the runner can only
estimate thinking tokens (game-engine's `chapter-text` subtracts the answer's length over four from the output
tokens).
**Research:** in-body Alternatives Considered table (FR-889 style); no `research.sh` run.
**Prior art:** [FR-231-model-provider-timing-comparison.md](FR-231-model-provider-timing-comparison.md) — added the
`--timing` callback beside the token one; this FR extends the token callback only;
[FR-1151-anthropic-effort.md](FR-1151-anthropic-effort.md) — the `effort` setting whose thinking this counts;
[FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md) — turning thinking off; its first consumer
estimated thinking tokens by subtraction, which this FR replaces with the provider's own count.
REQ-YG-064 (CAP-17, `fr: legacy`) is the token tracker's requirement; it has no FR file.
No rejected FR covers this territory.

## Summary

`TokenUsageCallbackHandler` also sums `usage_metadata["output_token_details"]["reasoning"]`, the thinking tokens
LangChain normalises from each provider (Anthropic's `output_tokens_details.thinking_tokens`). `summary()` gains
`total_reasoning_tokens`, and the `--token-usage` line adds `, N thinking` after its existing text.

## Value Statement

Graph authors paying for thinking (Opus 5.5's adaptive thinking, any `thinking_budget`) see how many of their output
tokens it took, from the provider's count instead of a guess.

## Problem

1. `token_tracker.py` reads `input_tokens` and `output_tokens` from `usage_metadata` and nothing else.
2. `langchain_anthropic` 1.7.x puts the thinking count in `usage_metadata["output_token_details"]["reasoning"]`
   (`chat_models.py` ~L2975: "reported by Anthropic via `output_tokens_details.thinking_tokens`"). The live FR-1151
   call shows the raw field: `'output_tokens_details': {'thinking_tokens': 0}`.
3. Thinking tokens are billed inside `output_tokens`, so a graph run's output count cannot be split into thinking and
   answer from the CLI today.

## Ideal Result

`yamlgraph graph run … --token-usage` prints `📊 Token usage: 1200 in / 800 out (1 call), 650 thinking`, and
`TokenUsageCallbackHandler.summary()["total_reasoning_tokens"]` is 650; a provider that reports none adds 0.
Everything already printed stays byte-identical up to the closing parenthesis.

## Planned Operations

```yaml
probes:
  - "the usage_metadata of one fake AIMessage with output_token_details.reasoning (offline)"
branches:
  - "a provider puts reasoning outside output_token_details → not counted; recorded, not guessed"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits: ["judge", "CI", "the operator's pre-approved merge on green"]
commands:
  - JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-1152-thinking-tokens-in-token-usage.md
  - pytest -q --no-cov tests/unit/test_fr027_execution_safety.py tests/unit/test_fr1152_thinking_tokens.py
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

1. `yamlgraph/utils/token_tracker.py`: `total_reasoning_tokens`, summed in `on_llm_end` from
   `(usage.get("output_token_details") or {}).get("reasoning", 0)`; `summary()` adds the key.
2. `yamlgraph/cli/graph_run_helpers.py`: the printed line appends `, {N} thinking` after `(… calls)` when
   `total_reasoning_tokens > 0`; with 0 the line is unchanged.
3. REQ-YG-064's description names the thinking count; CAP-17's `fr:` gains `FR-1152`; `ARCHITECTURE.md` regenerated.
4. Changelog fragment `type: feat`, `req: REQ-YG-064`; a diary entry.

## Alternatives Considered

**is_this_a_graph:** no — one more field summed in a callback.

| # | Solution class | Precedent | Disposition |
|---|---|---|---|
| A | **Sum LangChain's normalised `output_token_details.reasoning`** (chosen) | the tracker already reads `usage_metadata`, "provider-independent" (its docstring) | One field, every provider LangChain normalises |
| B | Read Anthropic's raw `response_metadata.usage.output_tokens_details.thinking_tokens` | — | Rejected: provider-specific, at the boundary LangChain already normalises |
| C | Leave it to consumers (a callback of their own, or the subtraction estimate) | game-engine `chapter-text` estimates | Rejected: every consumer re-derives a number the provider already sends |
| D | Print the thinking count always, `0 thinking` included | — | Rejected: changes the line for every run that has no thinking |

## Acceptance Criteria

- [ ] AC-01: two fake LLM results with `output_token_details: {reasoning: 30}` and `{reasoning: 12}` give
  `summary()["total_reasoning_tokens"] == 42`; input, output and call counts unchanged.
- [ ] AC-02: a result without `output_token_details` (or without `reasoning`) adds 0 and does not raise.
- [ ] AC-03: the printed line with reasoning tokens ends `(2 calls), 42 thinking`; with none it is byte-identical to
  today's.
- [ ] AC-04: tests in `tests/unit/test_fr1152_thinking_tokens.py` under `REQ-YG-064`, committed failing (RED) before
  the code (GREEN), the RED output in the FR.
- [ ] AC-05: REQ-YG-064 and CAP-17 updated, `ARCHITECTURE.md` regenerated, `req_coverage.py --strict` exits 0;
  changelog fragment; diary with a **Seed:**.
- [ ] AC-06: `pre-commit run --files <changed files>` passes apart from any `SKIP=pytest`, recorded with its commit
  and reason in the PR body; no `--no-verify`; no `Co-authored-by` trailer.
