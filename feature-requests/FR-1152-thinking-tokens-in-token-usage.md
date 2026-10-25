# Feature Request: FR-1152 `--token-usage` counts thinking tokens

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved with revisions (R-1..R-8 folded), in enforcement
**Requested:** 2026-10-25
**First consumer / first event:** game-engine's stage 5 graph for *A Voyage to Arcturus* chapter I
(`workflows/chapter-embellish`, prompt 317 in game-engine): its cost record must give "tokens, thinking tokens and
dollars per step" for one Opus 5.5 plan call at effort `low`, run right after this merges. Today the runner can only
estimate thinking tokens (game-engine's `chapter-text` subtracts the answer's length over four from the output
tokens). The runner reads the printed `--token-usage` line from the console (not `--json`, not
`summary()` in Python).
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
`total_reasoning_tokens`, and the `--token-usage` line adds `, N thinking` after its existing text. The thinking
count is a part of the output count, never added to it (`chat_models.py` ~L2974: "a decomposition of
`output_tokens` (not additive)"); `total_tokens` stays input plus output. Naming rule: the public dict key follows
LangChain's normalised field (`reasoning`); the human-facing label follows the provider's term (`thinking`).

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
   `(usage.get("output_token_details") or {}).get("reasoning") or 0` (a `None` counts 0, R-3); `summary()` adds the
   key, a contract change for a consumer comparing the dict whole: the two exact-dict assertions in
   `tests/unit/test_fr027_execution_safety.py` (L1128, L1143) gain `"total_reasoning_tokens": 0`, and nothing else in
   that file changes (R-1). `total_tokens` is unchanged; the docstring states the decomposition (R-2).
2. `yamlgraph/cli/graph_run_helpers.py`: the printed line appends `, {N} thinking` after `(… calls)` when
   `total_reasoning_tokens > 0`; with 0 the line is unchanged.
3. REQ-YG-064's description names the thinking count as part of the output count; REQ-YG-064's and CAP-17's
   `modules:` gain `cli/graph_run_helpers`; CAP-17's `fr:` reads `legacy, FR-1152` (as CAP-08 and CAP-03 do);
   `ARCHITECTURE.md` regenerated (R-7).
5. Observed in `langchain-anthropic` 1.7.0 (local) and 1.7.6 (CI, FR-1151); a version or provider that omits
   `output_tokens_details` contributes 0. No dependency floor changes (R-5).
4. Changelog fragment `type: feat`, `req: REQ-YG-064`; a diary entry.

## Alternatives Considered

**is_this_a_graph:** no — one more field summed in a callback.

| # | Solution class | Precedent | Disposition |
|---|---|---|---|
| A | **Sum LangChain's normalised `output_token_details.reasoning`** (chosen) | the tracker already reads `usage_metadata`, "provider-independent" (its docstring) | One field, every provider LangChain normalises |
| B | Read Anthropic's raw `response_metadata.usage.output_tokens_details.thinking_tokens` | — | Rejected: provider-specific, at the boundary LangChain already normalises |
| C | Leave it to consumers (a callback of their own, or the subtraction estimate) | game-engine `chapter-text` estimates | Rejected: every consumer re-derives a number the provider already sends |
| D | Print the thinking count always, `0 thinking` included | — | Rejected: changes the line for every run that has no thinking |

## Out of scope

- `--json` output: it carries no token usage today (`_print_json_result`), and this FR adds none.
- `yamlgraph bench`: it sums input and output tokens only (`bench_commands.py`) and is not changed.
- The async run path.
- Dollar figures: the first consumer prices tokens itself.

## Acceptance Criteria

Revised by judgement ([FR-1152-thinking-tokens-in-token-usage.judgement.md](FR-1152-thinking-tokens-in-token-usage.judgement.md)):

- [ ] AC-01: two fake LLM results with `output_token_details: {reasoning: 30}` and `{reasoning: 12}` give `summary()["total_reasoning_tokens"] == 42`; input, output and call counts unchanged.
- [ ] AC-02: a result without `output_token_details`, and one with `output_token_details` lacking `reasoning`, each add 0 and do not raise.
- [ ] AC-03: the printed line with reasoning tokens ends `(2 calls), 42 thinking`; with a zero count the full line equals today's string character for character (assert the literal, not a prefix).
- [ ] AC-04: tests in `tests/unit/test_fr1152_thinking_tokens.py`, each carrying a `@pytest.mark.req("REQ-YG-064")` **decorator** (module-level `pytestmark` is not counted by `scripts/req_coverage.py`); committed failing (RED) before the code (GREEN), the RED output pasted into the FR.
- [ ] AC-05: REQ-YG-064's description names the thinking count and says it is part of the output count; REQ-YG-064's `modules:` and CAP-17's `modules:` both include `cli/graph_run_helpers`; CAP-17's `fr:` reads `legacy, FR-1152`; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` exits 0; changelog fragment `type: feat`, `req: REQ-YG-064`; diary with a **Seed:**.
- [ ] AC-06: `pre-commit run --files <changed files>` passes apart from any `SKIP=pytest`, recorded with its commit and reason in the PR body; no `--no-verify`; no `Co-authored-by` trailer.
- [ ] AC-07 (R-1): `tests/unit/test_fr027_execution_safety.py:1128` and `:1143` include `"total_reasoning_tokens": 0` in their expected dicts and pass; the rest of the file is unmodified; the FR records that `summary()` gained a key.
- [ ] AC-08 (R-2): with `reasoning: 30` and `output_tokens: 80` on one result, `summary()["total_tokens"] == summary()["total_input_tokens"] + 80` — the thinking count is not added to the total; the handler docstring states the decomposition.
- [ ] AC-09 (R-3): a result whose `output_token_details` is `{"reasoning": None}` adds 0 and does not raise.
- [ ] AC-10 (R-4): one live call whose `message.usage_metadata` is pasted verbatim into the FR with `output_token_details["reasoning"] > 0`, and whose printed `--token-usage` line is pasted with it — or the AC recorded as **owed** in the FR and the PR body with the blocker named. No simulated transcript.
- [ ] AC-11 (R-5): the FR names the `langchain-anthropic` version in which `chat_models.py`'s reasoning normalisation was observed, states that versions or providers omitting `output_tokens_details` contribute 0, and states that no dependency floor changes.
- [ ] AC-12 (R-6): the FR carries an **Out of scope** section naming `--json`, `bench`, and the async path, and its first-consumer paragraph names the surface the game-engine runner reads.

## Judgement fold (2026-10-25)

Round 1, `JUDGE_BACKEND=claude bash scripts/judge.sh`: APPROVED WITH REVISIONS. Folded: R-1 (the two exact-dict
assertions), R-2 (decomposition, not addition), R-3 (`None` counts 0), R-4 (AC-10, one live call that thinks),
R-5 (versions, no floor change), R-6 (Out of scope; the surface the runner reads), R-7 (REQ and CAP modules, `fr:`
form), R-8 (the naming rule), each where its text says.

**The judge's questions, answered (technical, the enforcer's [M], within the producer's budget):** (1) AC-10's
spend: one Haiku 4.5 call with `thinking_budget: 1024`, about a cent. (2) The printed line keeps the accepted format
`, N thinking`; the docstring and REQ-YG-064 say the count is inside `out`. (3) Dollars stay outside yamlgraph.
