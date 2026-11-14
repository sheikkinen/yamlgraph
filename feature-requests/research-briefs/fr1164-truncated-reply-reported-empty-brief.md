# Problem brief: a reply cut off by the output-token limit is reported as empty or as a parse error

**Prior art:** FR-998 (structured-output policy, `invoke_structured`);
FR-464 (`response_format` rejection fallback with JSON extraction);
FR-679 (sync and async share `attempt_structured_invoke`); FR-071 / FR-230
(thinking budget); FR-1148 (Anthropic thinking off switch; its probe saw
`stop_reason=max_tokens`, thinking-only content and zero text);
FR-1152 (reasoning tokens counted in the usage summary as part of output);
FR-027 (max_tokens wiring); FR-465 (proposed: empty safety-blocked replies).

## Problem statement

Every LLM node call returns through `attempt_structured_invoke`
(`yamlgraph/executor_base.py`) or the race node
(`yamlgraph/node_factory/race_node.py`). For a plain-text call the code
returns `normalize_content(response.content)` and discards the message's
`response_metadata`. Nothing in the regular LLM path reads the provider's
stop reason (`stop_reason` for Anthropic, `finish_reason` for
OpenAI-compatible providers and Google). The only stop-reason check in the
package is in the opencode Copilot runtime.

When the reply hits the output-token limit:

- plain text: the node returns the cut-off text as a normal answer; if the
  model spent the whole limit thinking, `normalize_content` drops the
  thinking blocks and returns `""`;
- `parse_json: true`: `extract_json` returns the unparseable text
  unchanged, so the cut-off text flows downstream as the answer;
- structured output: the error is whatever the provider SDK or LangChain
  parser raises; `PipelineError` keeps only `str(e)`, so the stop reason is
  never named and the message may show an empty or partial body.

Models that think by default (Claude Sonnet 5.5 thinks unless turned off;
Opus 5.5 and Fable 5.x cannot turn it off; Gemini 3.5 Flash reasons) spend
part of `max_tokens` on thinking before any visible text. A limit sized for
the answer alone is therefore exhausted by thinking, and the result is an
empty or cut-off answer with no hint that the limit, or thinking, was the
cause. The usage metadata of the same response already carries
`output_token_details.reasoning`.

The question: where should yamlgraph detect that a reply stopped on the
output-token limit, and what must the resulting error or record contain so
that the cause (limit, thinking share) is visible?

## Classification

judgement/analysis/generation

## Constraints

- Normalize at the boundary where provider output enters (`the_one_law`);
  one shared check, not one per node type (`partial_remediation`).
- Provider factory only; no provider-specific imports in node code. The
  stop-reason vocabulary differs per provider and must be classified at
  one place.
- Sync and async share `attempt_structured_invoke` (FR-679); the race node
  has its own invoke path.
- No silent fallback (Commandment 6). Hidden reasoning text must not be
  copied into errors or state.
- Retrying with the same limit reproduces the same truncation; retry
  classification (`is_retryable`) must not loop on it.
- Providers that return no stop reason (local servers, Replicate) must keep
  working.
- TDD without network: fake `AIMessage` with `response_metadata` and
  `usage_metadata`.

## Witnessed incidents

- `examples/dungeon_master/chapter_close.yaml` comment: gemini-3.5-flash
  "spends hidden thinking tokens from the completion budget BEFORE emitting
  JSON. A 2000 cap was exhausted entirely by reasoning (~1921 tok observed
  in LangSmith), leaving "text": "" → empty ledger." The graph was patched
  locally with `max_tokens: 8000` and `thinking_budget: 512`.
- FR-1148 probe: Anthropic reply with `stop=max_tokens`, thinking-only
  blocks and zero visible text.
- 2026-11-14 operator report: "When a model's reply is cut off, the error
  shows nothing, so the reply looks empty" and "The model's thinking counts
  toward each item's token limit, so a small limit cuts the answer short."
