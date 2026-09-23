# Feature Request: FR-1056 DeepSeek Non-Thinking Mode (`thinking_budget: 0`)

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-23
**First consumer / first event:** any graph node with `provider: deepseek`
(model `deepseek-v4-pro` or `deepseek-flash`) whose author writes
`thinking_budget: 0` to get a fast, cheap, non-reasoning completion — first
event is the next `yamlgraph graph run` against the DeepSeek API, which today
still bills and waits for `high`-effort reasoning on every call.
**Research:** in-body dispositioned alternatives table (FR-889 style) — see
[Alternatives Considered](#alternatives-considered). Each row carries a probe
result, not a prediction: DeepSeek API docs read 2026-09-23 plus two executed
probes against the installed `langchain_openai` 1.4.1.
**Prior art:**
- [FR-071-thinking-budget-graph-level.md](FR-071-thinking-budget-graph-level.md)
  — introduced `thinking_budget` as an Anthropic-only token budget; this FR does
  not change its Anthropic semantics.
- [FR-230-google-vertex-thinking-budget.md](FR-230-google-vertex-thinking-budget.md)
  — same axis, previous extension (`THINKING_PROVIDERS` grew to google/vertex,
  `-1` sentinel admitted). This FR is the third extension, but differs in kind:
  DeepSeek exposes **no token budget at all**, only an effort enum, so only the
  *disable* end of the knob can be honoured honestly.
- [FR-680-provider-dispatch-registry.md](FR-680-provider-dispatch-registry.md) — the `_PROVIDER_FACTORIES` /
  `_THINKING_PROVIDERS` registry this FR edits; unchanged in shape.
- No REJECTED prior art: `grep -il deepseek feature-requests/` returns only
  incidental mentions (FR-809 tool_choice/response_format quirks) — no prior
  proposal on DeepSeek reasoning control.

## Summary

`provider: deepseek` cannot be put into non-thinking mode. DeepSeek enables
thinking **by default** at `high` effort on both current models, and
`yamlgraph` silently discards `thinking_budget` for DeepSeek, so there is no
YAML that turns reasoning off. Map `thinking_budget: 0` to DeepSeek's
`reasoning_effort: "none"`.

## Value Statement

Graph authors on `deepseek-v4-pro` / `deepseek-flash` can turn reasoning off
from YAML, paying for output tokens instead of hidden reasoning tokens on nodes
that do not need a chain of thought.

## Problem

Three facts, each verified today:

1. **DeepSeek thinks by default.** Per the API reference, `model` is one of
   `deepseek-flash` / `deepseek-v4-pro`; thinking mode is "enabled by default,
   with the default effort being `high`". The toggle is
   `reasoning_effort: "none"` (OpenAI format) or
   `extra_body={"thinking": {"type": "disabled"}}`. Default `max_tokens` is 8K
   in non-thinking mode versus 64K in thinking mode — the cost difference is
   not marginal. `temperature` also has **no effect in thinking mode**, so
   every `temperature:` in a DeepSeek graph is currently inert.

2. **`yamlgraph` drops the knob silently.** `deepseek` is absent from
   `_THINKING_PROVIDERS` in `yamlgraph/utils/llm_providers.py`, so
   `dispatch_provider` calls `_create_deepseek_llm(model, temperature, **kwargs)`
   without `thinking_budget`; `_create_deepseek_llm` has no such parameter.
   `thinking_budget: 0` is therefore a **no-op that looks like a setting** —
   the worst shape of failure (`plausible_wrong_answer`).

3. **The only loud path is the wrong one.** `create_llm` raises `ValueError`
   for `thinking_budget >= 1024` on a non-`THINKING_PROVIDERS` provider. So
   large budgets error, and `0` — the one value with an exact DeepSeek meaning
   — is swallowed.

## Ideal Result

A DeepSeek node in a graph obeys the reasoning switch it appears to have:
`thinking_budget: 0` produces a request carrying `reasoning_effort: "none"`,
returning a short non-reasoning completion; omitting `thinking_budget` leaves
DeepSeek's default (thinking on, `high`) untouched. Nothing else about the
`thinking_budget` contract moves — no new YAML field, no per-provider dialect
for graph authors to learn, and no change to what Anthropic/Google/Vertex do
with the same number.

## Proposed Solution

Minimal path back from the ideal: admit `deepseek` to the thinking registry and
honour exactly one value.

### YAML interface (no new field)

```yaml
defaults:
  provider: deepseek
  model: deepseek-v4-pro

nodes:
  extract:
    prompt: extract
    state_key: facts
    thinking_budget: 0        # -> reasoning_effort: "none" (thinking OFF)

  plan:
    prompt: plan
    state_key: plan
    # thinking_budget omitted -> DeepSeek default (thinking ON, effort "high")
```

### Implementation

1. `llm_providers.py`: add `deepseek` to `_THINKING_PROVIDERS` and give
   `_create_deepseek_llm` a `thinking_budget: int | None = None` parameter.
2. In `_create_deepseek_llm`, **only** `thinking_budget == 0` sets
   `reasoning_effort="none"` on `ChatOpenAI`. Any other value (including `-1`
   and positive budgets) is left off the request and logged at DEBUG.
3. `llm_factory.py`: no change to the `>= 1024` guard — DeepSeek stays out of
   `THINKING_PROVIDERS` there, so a DeepSeek node asking for a large token
   budget still fails loudly rather than pretending DeepSeek has token-level
   control. (The two constants are already distinct sets; this FR widens only
   the dispatch-side one.)
4. Cache key already includes `thinking_budget`, so thinking-on and
   thinking-off clients do not alias. No cache change.

### Why positive budgets stay a no-op rather than an error

Repo practice deliberately keeps `thinking_budget` **below 1024** in shared
graph defaults so a graph stays portable when its provider is switched to a
non-thinking provider for fast runs (`examples/dungeon_master/chapter_close.yaml`
uses `thinking_budget: 512`). Raising on any positive budget for DeepSeek would
break that portability cure. Silence for positive values is therefore a
deliberate, documented choice — not an oversight.

## Acceptance Criteria

- [ ] `create_llm(provider="deepseek", thinking_budget=0)` returns a
      `ChatOpenAI` whose request payload contains `reasoning_effort: "none"`
      (asserted via `_get_request_payload`, not via constructor kwargs).
- [ ] `create_llm(provider="deepseek")` (budget omitted) produces a payload
      with **no** `reasoning_effort` key — DeepSeek's default is not disturbed.
- [ ] `create_llm(provider="deepseek", thinking_budget=512)` produces a payload
      with no `reasoning_effort` key and does not raise (portability cure).
- [ ] `create_llm(provider="deepseek", thinking_budget=8000)` still raises
      `ValueError` naming the supported providers (unchanged behaviour).
- [ ] Anthropic / Google / Vertex payload construction is unchanged (existing
      thinking tests stay green).
- [ ] RED commit precedes GREEN commit; tests tagged
      `@pytest.mark.req("REQ-YG-684")`, capability `CAP-273` added.
- [ ] Changelog fragment in `changelog/unreleased/` (`type: fix`,
      `scope: providers`).
- [ ] `reference/graph-yaml.md` `thinking_budget` section documents the DeepSeek
      semantics (0 = off; other values ignored; effort control out of scope).

## Alternatives Considered

<a id="alternatives-considered"></a>

| # | Alternative | Probe / evidence | Disposition |
|---|-------------|------------------|-------------|
| A1 | New `reasoning_effort:` YAML field forwarded to DeepSeek and OpenAI | DeepSeek's enum is `none/low/high/max` with documented remapping (`minimal`→low, `medium`/`xhigh`→high, `ultra`→max); OpenAI's enum differs. A second reasoning knob means two fields answering one question in every graph | **Rejected for this FR.** Solves effort *tuning*, not the reported pain (off). Legitimate follow-up if a graph ever needs `max`. |
| A2 | Map budget ranges to effort buckets (e.g. `<8k`→low, `<32k`→high, else `max`) | Invented thresholds; a token count is not an effort level, and the mapping would silently change meaning per provider | **Rejected.** Fabricated precision; `plausible_wrong_answer` by construction. |
| A3 | Pass `extra_body={"thinking": {"type": "disabled"}}` instead of `reasoning_effort` | Probed `langchain_openai` 1.4.1: `ChatOpenAI` has a first-class `reasoning_effort` field (`Union[str, None]`), and `_get_request_payload` emits `{'model': 'deepseek-v4-pro', 'stream': False, 'temperature': 0.7, 'reasoning_effort': 'none'}` — verbatim, no responses-API rewrite (`_use_responses_api` = False) | **Rejected.** `extra_body` is the documented workaround for SDKs lacking the field; ours has it. |
| A4 | Tell authors to use a separate non-thinking model name | Probed the pricing page: there is no non-thinking model. Both `deepseek-flash` and `deepseek-v4-pro` are listed as "Supports both non-thinking and thinking (default) modes"; the legacy `deepseek-v4-flash*` names are retired and re-routed | **Rejected.** No such model exists. |
| A5 | Do nothing; document that DeepSeek always thinks | Non-thinking mode changes default `max_tokens` from 64K to 8K and makes `temperature` effective; the price table shows output tokens at $1.98/1M peak-off for `deepseek-v4-pro`, and reasoning tokens are output tokens | **Rejected.** The cost and latency are real and per-call. |

## Related

- `yamlgraph/utils/llm_providers.py` — `_create_deepseek_llm`,
  `_THINKING_PROVIDERS`, `dispatch_provider`
- `yamlgraph/utils/llm_factory.py` — `THINKING_PROVIDERS`, the `>= 1024` guard
- `yamlgraph/linter/checks_providers.py` — W071-2 warns only for
  `thinking_budget > 0`, so `0` on DeepSeek does not trip the linter; no linter
  change needed
- DeepSeek docs read 2026-09-23: Thinking Mode guide, Chat Completions API
  reference, Models & Pricing

## Out of Scope (named, not forgotten)

- **Effort control** (`low`/`high`/`max`) — see A1.
- **Stale DeepSeek default model.** `yamlgraph/config.py` defaults
  `DEEPSEEK_MODEL` to `deepseek-chat`, which is not among the two model names
  the current API reference accepts. Suspected 400 on any DeepSeek run that does
  not set `model:` explicitly. Separate defect, separate FR — flagged here so it
  is not lost.
- **`reasoning_content` round-tripping.** DeepSeek returns a 400 when `tools`
  are present and prior-turn `reasoning_content` is not passed back. Affects
  thinking-mode agent loops, not this switch.
