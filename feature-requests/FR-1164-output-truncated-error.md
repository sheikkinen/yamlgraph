# Feature Request: FR-1164 Report replies cut off by the output-token limit, with the thinking share

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-11-14
**First consumer / first event:** the next map run where a model that
thinks by default (Claude Sonnet 5.5, Opus 5.5, Gemini 3.5 Flash) hits a
small per-item `max_tokens`. Today the item returns `""` or a cut-off
answer as a success, or a parser error with an empty body. After this FR
the item fails with "stopped at the output-token limit … N of M output
tokens were thinking".
**Research:** [FR-1164.research.md](FR-1164.research.md)
(brief: `research-briefs/fr1164-truncated-reply-reported-empty-brief.md`)
**Prior art:** FR-998 (structured-output policy; this FR adds a check
inside its `invoke_structured`/`ainvoke_structured`, no second policy
surface). FR-464 (JSON-extraction fallback; its re-invoke gets the same
check). FR-679 (sync and threaded async share `attempt_structured_invoke`;
the check lives there once). FR-1148 (its probe recorded
`stop=max_tokens` with thinking-only content; that FR turned thinking off,
this FR reports the case for models that cannot). FR-1152 (sums reasoning
tokens in the usage summary; this FR reads the same field per call).
FR-071/FR-230 (thinking budget). FR-465 (proposed: empty safety-blocked
replies; different stop reason, not covered here). Retrieval hits FR-736,
FR-931, FR-948, FR-959, FR-1060 share only vocabulary and are dismissed.

## Summary

Read the provider's stop reason at the one place every LLM node call
returns, and raise a typed `OutputTruncatedError` when the reply stopped on
the output-token limit. The message names the stop reason, the output
token count, how many of those were thinking, and how much visible text
came back. This also covers the operator's third finding: thinking counts
toward `max_tokens`, so a small limit cuts the answer short. The error
makes that cause visible; the reference docs state the shared budget.

## Value Statement

Operators see "the limit was hit, and thinking used most of it" instead of
an empty answer that looks like a success or a parse error that shows
nothing.

## Problem

- `attempt_structured_invoke` (`yamlgraph/executor_base.py`) returns
  `normalize_content(response.content)` for plain calls and drops
  `response_metadata`. `normalize_content` keeps text blocks only, so a
  thinking-only reply becomes `""`.
- With `parse_json: true`, `extract_json` returns unparseable text
  unchanged (`yamlgraph/utils/json_extract.py`): a cut-off JSON body flows
  downstream as the answer.
- Structured calls go through `invoke_structured`
  (`yamlgraph/utils/structured_output.py`), which returns only the parsed
  model; on a cut-off reply the parser error is all that remains, and
  `PipelineError` keeps `str(e)`.
- The race node (`yamlgraph/node_factory/race_node.py`) has its own
  `ainvoke` and the same blind spot.
- No stop-reason check exists in the LLM path (the only one is in
  `copilot_runtime_opencode.py`).
- Witnessed: `examples/dungeon_master/chapter_close.yaml` records a
  gemini-3.5-flash call where "a 2000 cap was exhausted entirely by
  reasoning (~1921 tok observed in LangSmith), leaving "text": "" → empty
  ledger". FR-1148's probe recorded the Anthropic equivalent.
- Thinking is part of `max_tokens` on Anthropic and part of the output
  limit on OpenAI reasoning models. Models that think by default spend it
  without any `thinking_budget` in the graph. The reference docs describe
  `max_tokens` and `thinking_budget` separately and never say they share
  one budget.

## Ideal Result

No LLM reply that stopped on the output-token limit is ever treated as a
finished answer. The failure names the limit and the thinking share, at the
node that made the call, on every provider that reports a stop reason.

## Planned Operations

```yaml
probes:
  - "live Haiku 4.5 call with max_tokens=16, plain and structured (json_schema), read raw response_metadata and the exception text — confirms the Anthropic stop_reason key and what the structured path raises today (cost < $0.01)"
  - "read langchain-openai / langchain-google-genai response_metadata keys in the installed packages — confirms finish_reason values 'length' and 'MAX_TOKENS'"
  - "grep tests for with_structured_output mocks — counts the tests that the include_raw change touches"
branches:
  - "more than 30 tests mock with_structured_output().invoke returning a model → add a shared test helper that wraps the return in {raw, parsed, parsing_error}; never a production shim that accepts both shapes"
  - "a provider in the probe reports truncation under a key not listed here → add it to the one classifier table, with a test"
delegations:
  - "research.sh: 1 run (done)"
  - "judge.sh: 1 run"
waits:
  - "judge"
commands:
  - scripts/judge.sh
  - pytest tests/unit/test_fr1164_output_truncated.py tests/unit/test_fr998_structured_output.py
  - yamlgraph graph run examples/demos/hello/graph.yaml
```

## Proposed Solution

New module `yamlgraph/utils/stop_reason.py`:

```python
TRUNCATED = {"max_tokens", "length", "MAX_TOKENS"}  # anthropic | openai-compatible | google

class OutputTruncatedError(RuntimeError):
    stop_reason: str; output_tokens: int | None; reasoning_tokens: int | None
    visible_chars: int; preview: str  # first 200 visible chars, never thinking text

def ensure_complete(message) -> None:
    """Raise OutputTruncatedError when the message stopped on the output limit."""
```

`ensure_complete` reads `response_metadata["stop_reason"]`, else
`response_metadata["finish_reason"]`; anything outside `TRUNCATED`, or no
key at all, passes. Token counts come from `usage_metadata`
(`output_tokens`, `output_token_details.reasoning`). Message form:

`LLM reply stopped at the output-token limit (stop_reason=max_tokens): 2000 output tokens, 1921 of them thinking; 0 visible characters. Raise max_tokens, or lower thinking_budget where the model allows it.`

Call sites (all of them, `partial_remediation`):

1. `attempt_structured_invoke`: the plain path and the FR-464 fallback
   re-invoke call `ensure_complete(response)` before `normalize_content`.
2. `invoke_structured` / `ainvoke_structured`: bind with
   `include_raw=True`, call `ensure_complete(out["raw"])`, then re-raise
   `out["parsing_error"]` if set, else return `out["parsed"]`. The
   exception type on a non-truncated parse failure stays what it is today.
   `bind_structured_output` (also used by agent finalisation) is unchanged.
3. `race_node._invoke_candidate_async`: both `ainvoke` paths.

`OutputTruncatedError` is not in `RETRYABLE_EXCEPTIONS`: the same limit
reproduces the same cut. Node `on_error` policies apply as for any error.

Docs: `reference/graph-yaml.md`, next to `max_tokens` and
`thinking_budget`: thinking counts toward `max_tokens`; models that think
by default spend it without a `thinking_budget` setting; a cut-off reply
raises `OutputTruncatedError`.

## Acceptance Criteria

- [ ] AC-01: a fake `AIMessage` with `response_metadata={"stop_reason": "max_tokens"}`,
  thinking-only content and `usage_metadata` output 2000 / reasoning 1921
  makes `attempt_structured_invoke` (no output model) raise
  `OutputTruncatedError` whose message contains `max_tokens`, `2000` and
  `1921`.
- [ ] AC-02: the same with `finish_reason: "length"` and with
  `finish_reason: "MAX_TOKENS"`.
- [ ] AC-03: `parse_json` path: truncated reply raises instead of returning
  the text.
- [ ] AC-04: structured path, sync and async: a raw message with
  `stop_reason: max_tokens` raises `OutputTruncatedError`; a raw message
  with `stop_reason: end_turn` and a `parsing_error` re-raises that same
  exception object.
- [ ] AC-05: race node candidate with a truncated reply raises
  `OutputTruncatedError`.
- [ ] AC-06: messages with no stop-reason key, or `end_turn`/`stop`, pass
  unchanged (existing suite green).
- [ ] AC-07: the error message contains no thinking text (assert a sentinel
  string in the thinking block is absent).
- [ ] AC-08: live probe recorded in this FR: Haiku 4.5, `max_tokens=16`,
  plain call raises `OutputTruncatedError` naming `max_tokens`.
- [ ] AC-09: `reference/graph-yaml.md` states that thinking counts toward
  `max_tokens` and names `OutputTruncatedError`.
- [ ] AC-10: RED commit precedes GREEN; unit suite and
  `req_coverage --strict` pass.

## Alternatives Considered

From the research record (four personas converged on the boundary check):

- Classify in the provider factory and attach a normalized field to
  `response_metadata` (os-infra, yamlgraph-native): the factory builds
  clients but never sees responses; the first code that sees every
  response is `attempt_structured_invoke` plus the race node. Chosen
  location is that boundary.
- Carry stop reason and reasoning tokens as state/schema fields through
  every node output (data-process persona, which failed schema validation
  in the run): larger, and a field nobody reads does not stop a cut-off
  answer from passing as finished. Rejected.
- Raise only (subtractionist) vs. warn: warn-only keeps the plausible wrong
  answer (Commandment 6). Raise chosen.
- Validate `thinking_budget` against `max_tokens` at client build: the
  Anthropic API already rejects `budget_tokens >= max_tokens` with a 400,
  and models that think by default have no budget to compare. It does not
  catch the witnessed cases. Rejected; the error message carries the cause.

## Related

- [FR-1164.research.md](FR-1164.research.md)
- [FR-1148](FR-1148-anthropic-thinking-off.md), [FR-1152](FR-1152-thinking-tokens-in-token-usage.md)
