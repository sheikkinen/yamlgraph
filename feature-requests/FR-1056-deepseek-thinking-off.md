# Feature Request: FR-1056 DeepSeek Non-Thinking Mode (`thinking_budget: 0`)

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
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
**`is_this_a_graph`:** No. This is a deterministic one-value mapping at the
provider construction boundary — no per-item model calls, no multi-stage LLM
pipeline, no fan-out. `yamlgraph graph list` holds no graph for provider-client
construction, and none would be appropriate: the work is Python at a seam, and
its witness is a request payload assertion, not an LLM judgement.
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

Frozen by the judgement (2026-09-23), AC-01 … AC-12:

- [x] AC-01: With the LLM cache isolated,
      `create_llm(provider="deepseek", model="deepseek-v4-pro", thinking_budget=0)`
      returns `ChatOpenAI` and `_get_request_payload(...)` contains
      `reasoning_effort == "none"`.
- [x] AC-02: With the cache isolated, the same call with `thinking_budget`
      omitted produces a request payload with no `reasoning_effort` key.
- [x] AC-03: With the cache isolated, the same call with `thinking_budget=512`
      does not raise, produces a payload with no `reasoning_effort` key, and
      emits the specified DEBUG record naming the ignored value and provider.
- [x] AC-04: `create_llm(provider="deepseek", model="deepseek-v4-pro",
      thinking_budget=8000)` raises `ValueError` naming the supported
      token-budget providers; no DeepSeek client is constructed.
- [x] AC-05: Existing Anthropic, Google, and Vertex thinking-budget tests pass
      unchanged in asserted behaviour.
- [x] AC-06: Distinct DeepSeek calls with omitted, zero, and 512 budgets do not
      alias in the client cache.
- [x] AC-07: Every new test carries `@pytest.mark.req("REQ-YG-684")`, and
      `python scripts/req_coverage.py --strict` passes.
- [x] AC-08: `capabilities/CAP-273-deepseek-non-thinking.yaml` exists and
      defines REQ-YG-684; `ARCHITECTURE.md` registers CAP-273 and REQ-YG-684
      with the frozen four-case contract.
- [x] AC-09: `reference/graph-yaml.md` and the `create_llm` `thinking_budget`
      parameter documentation state: DeepSeek zero disables thinking, omission
      preserves the API default, accepted other values are ignored, and effort
      tuning is unsupported.
- [x] AC-10: A `changelog/unreleased/` fragment has `type: fix`,
      `scope: providers`, and identifies FR-1056 / REQ-YG-684.
- [x] AC-11: Git history contains a failing RED test commit before the GREEN
      implementation commit.
- [x] AC-12: The FR records the explicit `is_this_a_graph` disposition and,
      after enforcement, records implementation status and deviations.

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

## Judgement (2026-09-23)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-1056-deepseek-thinking-off.judgement.md](FR-1056-deepseek-thinking-off.judgement.md).

R-1 (`is_this_a_graph` disposition), R-2 (CAP-273 / REQ-YG-684 traceability
frozen into AC-07/AC-08), and R-3 (DEBUG observability + `create_llm` docstring
in AC-03/AC-09) are folded in above. Frozen deliverables D-1 … D-5 and gates
C-1 … C-5 are binding; the not-authorized list stands.

## Implementation Status

**Enforced 2026-09-23** on `feat/fr-1056-deepseek-thinking-off`.

| Deliverable | Landed as |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: `deepseek` added to the dispatch-side `_THINKING_PROVIDERS`; `_create_deepseek_llm` gained `thinking_budget`; `reasoning_effort="none"` set only for `0`, other non-`None` values DEBUG-logged and dropped |
| D-2 | `tests/unit/test_fr1056_deepseek_thinking.py` — 5 tests, keyless, asserting `_get_request_payload` output |
| D-3 | `create_llm` docstring + two `reference/graph-yaml.md` tables |
| D-4 | `capabilities/CAP-273-deepseek-non-thinking.yaml`; `ARCHITECTURE.md` regenerated via `scripts/aggregate_capabilities.py` |
| D-5 | `changelog/unreleased/fr-1056-deepseek-thinking-off.md` (`type: fix`, `scope: providers`) |

**Deviations:** none. The asymmetry required by C-2 is now load-bearing and
commented at `_THINKING_PROVIDERS`: `deepseek` is inside the dispatch registry
and deliberately outside `llm_factory.THINKING_PROVIDERS`, which is what keeps
AC-04 (`>= 1024` raises) true while AC-01 works.

**Verification:** RED `14b1e90c` (2 of 5 failing); GREEN follows. Full fast unit
suite 6897 passed / 61 skipped; `scripts/req_coverage.py --strict` exit 0.
