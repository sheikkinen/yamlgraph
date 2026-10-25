# Feature Request: FR-1151 An `effort` setting for Anthropic llm nodes

**Priority:** HIGH
**Type:** Feature
**Status:** Approved with revisions (R-1..R-7 folded), in enforcement
**Requested:** 2026-10-25
**First consumer / first event:** game-engine's stage 5 graph for *A Voyage to Arcturus*
(`prompts/317-arcturus-chapter-embellish.md` in game-engine, step 2): one `llm` node, `claude-opus-5-5` at
effort `low`, planning chapter I's cut scenes, run as soon as this merges. Today the node cannot ask for low effort:
yamlgraph sends no `output_config`, and an `effort:` key on the node is silently ignored.
**Research:** in-body Alternatives Considered table (FR-889 style) with precedent per class; no `research.sh` run.
**Prior art:** [FR-1146-anthropic-temperature-deprecated.md](FR-1146-anthropic-temperature-deprecated.md) — its
Out of scope records that the new Anthropic models take "`thinking.type.adaptive` and `output_config.effort`" and
that this "needs its own FR (new config surface: adaptive + effort)"; this is that FR, for effort;
[FR-071-thinking-budget-graph-level.md](FR-071-thinking-budget-graph-level.md) — the `thinking_budget` field this
follows field for field (defaults and node, node over defaults, in the cache key, refused on other providers);
[FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md) — `thinking_budget: 0`; this FR leaves it
alone and composes with it; [FR-1056-deepseek-thinking-off.md](FR-1056-deepseek-thinking-off.md) — DeepSeek's
effort enum, reached through `thinking_budget: 0`; distinguished: no new field, DeepSeek only;
[FR-1144-race-node-thinking-budget.md](FR-1144-race-node-thinking-budget.md) — carried `thinking_budget` to race
nodes and listed Azure/OpenAI `reasoning_effort` out of scope; this FR is Anthropic only and `llm` nodes only;
[FR-455-reasoning-model-temperature-guard.md](FR-455-reasoning-model-temperature-guard.md) — OpenAI reasoning
models and temperature; dismissed, no effort surface;
[FR-1150-llm-providers-split.md](FR-1150-llm-providers-split.md) — put the Anthropic factory in
`anthropic_thinking.py` so this FR grows that module, not `llm_providers.py`.
No rejected FR covers this territory.

## Summary

Add an optional `effort` field (`low`, `medium`, `high`, `xhigh`, `max`) to graph `defaults` and to `llm` nodes.
On the `anthropic` provider it is sent as `output_config.effort`; absent, the request is unchanged; on any other
provider it is an error before any request. When `effort` is set and the node sets no `thinking_budget`, the request additionally carries whatever
`thinking` `langchain_anthropic` injects: `{"type": "adaptive", "display": "summarized"}` on models whose
profile declares the `xhigh` level (`chat_models.py:1659-1669`), nothing on the others. yamlgraph neither adds
nor suppresses it.

## Value Statement

Graph authors on Claude Opus 5.5 and the other adaptive-thinking models get the one control those models have over
how much they think and spend, which today they cannot reach from YAML at all.

## Problem

1. `create_llm(provider, model, temperature, max_tokens, thinking_budget)` is the whole surface
   (`yamlgraph/utils/llm_factory.py`); nothing else reaches `ChatAnthropic`. `output_config` is never sent.
2. A node key `effort: low` is accepted (the node schema allows extra keys) and dropped without a word.
3. On `claude-opus-5-5` and `claude-fable-5*` effort is the only thinking control: FR-1148's Probe A shows both
   refuse `thinking.type.disabled` with `Use "thinking.type.adaptive" and "output_config.effort" to control thinking
   behavior`, and `thinking_budget ≥ 1024` (`type: enabled`) is refused on them too (FR-1146's side probe;
   `langchain_anthropic` 1.7.0 raises on `claude-opus-5*` with `enabled`).

`langchain_anthropic` 1.7.0 already has the field: `ChatAnthropic(reasoning_effort=...)` (alias `effort`),
`Literal["max", "xhigh", "high", "medium", "low"]`, which sets `output_config.effort` and, when `thinking` is not
set, defaults `thinking` to `{"type": "adaptive", "display": "summarized"}` (its docstring, `chat_models.py`
~L1229-1250).

## Ideal Result

`effort: low` on an `llm` node (or in `defaults`) makes its Anthropic request carry `output_config.effort: "low"`;
omitting it changes nothing in any request; naming it with another provider, or with a value outside the five,
fails before any request with a message naming the field. When `effort` is set and the node sets no `thinking_budget`, the request additionally carries whatever
`thinking` `langchain_anthropic` injects: `{"type": "adaptive", "display": "summarized"}` on models whose
profile declares the `xhigh` level (`chat_models.py:1659-1669`), nothing on the others. yamlgraph neither adds
nor suppresses it. On a race node, or a router node with `candidates:`, `effort` is refused at load: those nodes would drop it.

## Planned Operations

```yaml
probes:
  - "the request payload of ChatAnthropic(model='claude-opus-5-5', reasoning_effort='low'): output_config and thinking (offline, _get_request_payload)"
  - "wc -l of every touched module before and after (llm_nodes.py is 449)"
  - "one live call: create_llm(provider='anthropic', model='claude-opus-5-5', effort='low').invoke(<short prompt>) — usage and block types recorded (≈ $0.01)"
branches:
  - "effort with thinking_budget ≥ 1024 on a claude-opus-5* model → langchain's own ValueError stands; recorded, not wrapped"
  - "a touched module would exceed 450 lines → the offset of Proposed Solution 6, nothing else"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits:
  - "judge"
  - "CI"
  - "producer's reviewer, then the operator's merge decision"
commands:
  - JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-1151-anthropic-effort.md
  - pytest -q --no-cov tests/unit/test_fr1151_anthropic_effort.py tests/unit/test_thinking_budget.py tests/unit/test_fr715_prompt_request.py tests/unit/test_llm_node_phases.py tests/unit/test_fr1028_provider_model_override.py
  - PYTHONUTF8=1 python scripts/size_gate.py
  - lint-imports
  - python scripts/req_coverage.py --strict
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

The field follows `thinking_budget` (FR-071) through every layer, and stops at `llm` nodes.

1. **Schema.** `yamlgraph/models/node_schema.py`: `effort: Literal["low", "medium", "high", "xhigh", "max"] | None`
   on the node config, and a `model_validator(mode="after")` that refuses `effort` when the node type is not `llm`
   or `router`, or when `candidates` is set, naming `effort`, the node type, and where `effort` is supported (R-2). `yamlgraph/models/graph_schema.py`: a `defaults.effort` validator with the same five values.
2. **Node resolution.** `yamlgraph/node_factory/llm_nodes.py`: `LLMNodeConfig.effort`, node over defaults, passed to
   `execute_prompt`.
3. **Request.** `yamlgraph/executor_base.py`: `PromptRequest.effort`; `yamlgraph/executor.py`: the `execute_prompt`
   parameter (signature parity with `PromptRequest`, FR-715) and `_get_llm` → `create_llm(effort=...)`.
4. **Factory.** `yamlgraph/utils/llm_factory.py`: `create_llm(..., effort=None)`. Set with a *resolved* provider
   (argument, then `PROVIDER`, then the default) other than `anthropic` → `ValueError` naming `effort` and that
   provider, before any client is built (R-4). In the cache key. When set, `_cached_or_create`
   passes `reasoning_effort=effort` in the factory kwargs, which `_create_anthropic_llm` hands to `ChatAnthropic`
   unchanged (no edit to `anthropic_thinking.py`).
5. **Absent means unchanged.** No `effort` → no `reasoning_effort` kwarg → no `output_config` and no change to
   `thinking`; every existing test passes unchanged.
6. **The size gate.** `llm_nodes.py` is 449 lines and needs three more (field, resolution, call). Offset: the
   four-line `thinking_budget` resolution (`node_config.get(...)`, then `defaults` when `None`) and the new
   `effort` resolution both go through one helper `node_or_default(node_config, defaults, key)` in
   `yamlgraph/node_factory/base.py` (90 lines), same semantics (an explicit node `0` wins over a default;
   `llm_nodes.py:126-128` is the reference). Exactly two call sites, both in `llm_nodes.py`; `race_node.py`'s
   resolution is not migrated; the existing `thinking_budget` tests pass unmodified (R-5).
7. **Composition, recorded not wrapped.** `effort` with `thinking_budget: 0` on Sonnet 5.5 sends both
   (`thinking: between_tools` is explicit, so langchain's adaptive default does not apply). `effort` with
   `thinking_budget ≥ 1024` on `claude-opus-5*` is refused by `langchain_anthropic` itself; yamlgraph does not
   repeat that rule. Which models accept which effort level is the API's to answer (a 400), not a table here.
8. **Docs and registry.** `reference/graph-yaml.md`: the defaults table, the `llm` node table and the example
   comment, and the race table: race and router-race candidates never receive `effort`, and `defaults.effort`
   reaches only `llm` and candidate-less `router` nodes (R-3). CAP-28 gains a new REQ with its own `modules:`, its
   `fr:` gains `FR-1151`, and its name and description stop claiming it is only `thinking_budget`;
   `ARCHITECTURE.md` regenerated. Changelog fragment `type: feat` with `req:` the new REQ, never `REQ-YG-083`;
   `check_changelog_req.py`'s result (pass, or deferred to its LLM check) recorded (R-6).

**Out of scope:** race and router-race nodes (`race_node.py` is at 450 lines; FR-1144's route), the async
executor path (it carries no `thinking_budget` either), OpenAI/Azure `reasoning_effort`, Google `thinking_level`,
a linter rule (the schema refuses bad values; the factory refuses other providers), any change to
`thinking_budget`'s meaning.

## Alternatives Considered

**is_this_a_graph:** no — one optional field carried to a constructor argument.

| # | Solution class | Precedent | Disposition |
|---|---|---|---|
| A | **A named `effort` field, Anthropic only, `llm` nodes** (chosen) | FR-071's `thinking_budget` field path; FR-1146's deferral names this surface | The smallest surface the first consumer needs; refused loudly elsewhere |
| B | A generic `model_kwargs:` passthrough on nodes | — | Rejected: an unvalidated door to every provider's constructor; typos and wrong-provider keys would reach the API or vanish |
| C | Map `thinking_budget` values to effort levels | FR-1056 mapped `0` to DeepSeek's enum | Rejected: one field with two meanings by model; `thinking_budget ≥ 1024` already has a meaning on older models |
| D | An `output_config:` dict field mirroring the API | — | Rejected: exposes `format` too, which structured output already owns (FR-998) |
| E | Effort for every reasoning provider at once (OpenAI, Azure, Google) | FR-1144 kept Azure out for want of a witness | Rejected: no consumer and no probe for the others |

## Acceptance Criteria

Revised by judgement ([FR-1151-anthropic-effort.judgement.md](FR-1151-anthropic-effort.judgement.md)):

- [ ] AC-01: `create_llm(provider="anthropic", model="claude-opus-5-5", effort="low")` → the offline request payload has `output_config == {"effort": "low"}`.
- [ ] AC-02: the same without `effort` → no `output_config` key and `llm.thinking is None` (unchanged).
- [ ] AC-03: `create_llm(provider="openai", effort="low")` raises `ValueError` naming `effort` and `openai`, before any client is built.
- [ ] AC-04: `effort` is in the cache key: `low` and `high` give different instances; two `low` calls the same.
- [ ] AC-05: an `llm` node with `effort: low`, and one with `defaults.effort: high` and no node value, resolve to `low` and `high` in `LLMNodeConfig` and reach `execute_prompt` (mocked).
- [ ] AC-06: `effort: lowest` on a node, and in `defaults`, are refused by the schema naming the five values.
- [ ] AC-07: `execute_prompt`'s parameters equal `PromptRequest`'s fields (`tests/unit/test_fr715_prompt_request.py` passes with `effort` in both, unmodified).
- [ ] AC-08: `thinking_budget: 0` with `effort: low` on `claude-sonnet-5-5` → payload `thinking == {"type": "between_tools"}` and `output_config == {"effort": "low"}`.
- [ ] AC-09: every touched module ≤ 450 lines; `PYTHONUTF8=1 python scripts/size_gate.py` exits 0; no BASELINE entry added.
- [ ] AC-10: new tests in `tests/unit/test_fr1151_anthropic_effort.py`, class marker for the new REQ; committed failing (RED) before the code (GREEN), the RED output pasted into the FR.
- [ ] AC-11: one live call on `claude-opus-5-5` at effort `low`; provider, model, `usage` and block types pasted verbatim — or the AC recorded as **owed** with its blocker named, in both the FR and the PR body (R-7). No simulated transcript.
- [ ] AC-12: `reference/graph-yaml.md` (defaults table, `llm` node table, example comment) documents `effort`; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` exits 0.
- [ ] AC-13: `changelog/unreleased/fr-1151-anthropic-effort.md` with `type: feat` and `req:` naming the new REQ; the `check_changelog_req.py` result (pass or deferred) recorded.
- [ ] AC-14: `lint-imports` passes; `pre-commit run --files <changed files>` passes apart from any `SKIP=pytest`, recorded with its commit and reason in the PR body.
- [ ] AC-15: a `docs/diary/` reflection with a **Seed:**; no `--no-verify`; no `Co-authored-by` trailer.
- [ ] AC-16 (R-1): offline payload for `claude-opus-5-5` + `effort: low` + no `thinking_budget` asserts the observed `thinking` value verbatim, and the FR records it together with the profile gate (`chat_models.py:1659-1669`) that produced it; the Summary and Ideal Result state the rule.
- [ ] AC-17 (R-2): `effort` on a `race` node, and on a `router` node with `candidates:`, are refused at load by `NodeConfig` with a message naming `effort` and the node type; `effort` on an `llm` node and on a candidate-less `router` node still loads.
- [ ] AC-18 (R-3): a graph with `defaults.effort` plus a race node loads and compiles, and the race candidates are constructed with no effort kwarg; `reference/graph-yaml.md`'s race table says so.
- [ ] AC-19 (R-4): with `provider=None` and `PROVIDER` set to a non-Anthropic provider in the environment, `create_llm(effort="low")` raises `ValueError` naming `effort` and the resolved provider, before any client is constructed.
- [ ] AC-20 (R-6): `capabilities/CAP-28-*.yaml` holds the new REQ, its `fr:` list includes `FR-1151`, and its name/description no longer claim the CAP is only `thinking_budget`.

## Judgement fold (2026-10-25)

Round 1, `JUDGE_BACKEND=claude bash scripts/judge.sh`: APPROVED WITH REVISIONS. Folded:

| # | Revision | Where folded |
|---|---|---|
| R-1 | What `effort` does to `thinking` | Summary, Ideal Result; AC-16 |
| R-2 | Refuse `effort` where it would be dropped | Proposed Solution 1; AC-17 |
| R-3 | The reach of `defaults.effort` | Proposed Solution 8; AC-18 |
| R-4 | Refuse on the resolved provider | Proposed Solution 4; AC-19 |
| R-5 | Bound the `node_or_default` extraction | Proposed Solution 6 |
| R-6 | The REQ bookkeeping | Proposed Solution 8; AC-13, AC-20 |
| R-7 | AC-11 run or owed, never simulated | AC-11 |

**The judge's questions, answered (technical choices are the enforcer's [M], within the producer's budget):**
(1) Spend: one live `claude-opus-5-5` call at about $0.01, on the key in this checkout's `.env`, which served
FR-1148's probes; inside the Arcturus budget. (2) R-2 stays a load-time error: the FR's premise is that a dropped
key is the defect, and no existing graph sets `effort` (it did nothing before this FR).

## Addendum 2026-10-25: Problem 2 corrected by probe

Problem 2 above says a node key `effort: low` "is accepted (the node schema allows extra keys) and dropped without
a word". That is wrong for nodes. `NodeConfig` is `extra: forbid` (`node_schema.py:267`) and `load_graph_config`
validates every node through it (`validators.validate_config` → `validate_graph_schema`, FR-673). Probe on
`main` at `c0bea5a9`, a one-node graph:

```text
nodes.plan.effort
  Extra inputs are not permitted [type=extra_forbidden, input_value='low', input_type=str]
nodes.plan.output_config
  Extra inputs are not permitted [type=extra_forbidden, input_value={'effort': 'low'}, input_type=dict]
```

The silent drop is real for `defaults` only, which is a free dict: `defaults: {provider: anthropic, effort: low}`
loads, and the value reaches nothing. The FR's design is unchanged. Today a node cannot ask for effort at all, and a
graph-wide `defaults.effort` is ignored. Judgement R-2 still holds: once `effort` is a `NodeConfig` field, a race
node or a router with `candidates:` would accept it and drop it, so the validator stays.

## Implementation status (2026-10-25)

**Probe, offline payloads** (`langchain-anthropic` 1.7.0, before the code):

```text
claude-opus-5-5 output_config= {'effort': 'low'} thinking= <absent>
claude-sonnet-5-5 output_config= {'effort': 'low'} thinking= {'type': 'between_tools'}
claude-haiku-4-5-20251001 output_config= {'effort': 'low'} thinking= <absent>
```

The installed profile data gives `claude-opus-5-5` no `xhigh` level, so langchain's adaptive default
(`chat_models.py:1659-1669`) does not fire: no `thinking` field is sent (AC-16, asserted as observed).

**RED** (`fda8c6f7`, the tests and REQ-YG-725 in CAP-28, no code):

```text
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_effort_reaches_output_config
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_effort_on_another_provider_raises_before_any_client
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_effort_refused_on_the_resolved_provider
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_effort_is_in_the_cache_key
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_effort_with_thinking_off_on_sonnet_5_5
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_opus_5_5_low_effort_thinking_as_observed
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_bad_value_refused_on_a_node
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_bad_value_refused_in_defaults
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_effort_refused_where_it_would_be_dropped[race]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_effort_refused_where_it_would_be_dropped[router-with-candidates]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_effort_accepted_on_llm_and_plain_router[llm]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortSchema::test_effort_accepted_on_llm_and_plain_router[router]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortNodeResolution::test_effort_resolves_and_reaches_execute_prompt[node]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortNodeResolution::test_effort_resolves_and_reaches_execute_prompt[defaults]
FAILED tests/unit/test_fr1151_anthropic_effort.py::TestEffortNodeResolution::test_effort_resolves_and_reaches_execute_prompt[unset]
15 failed, 2 passed in 2.69s
```

The two that pass hold today by design: AC-02 (absent effort leaves the request unchanged) and AC-18 (race
candidates are built without effort).

**GREEN** (`dc9fa4dc`): 17 passed in `test_fr1151_anthropic_effort.py`; `test_thinking_budget.py`,
`test_fr1148_thinking_off_payload.py`, `test_fr715_prompt_request.py`, the race, router-race, llm-node, executor,
schema and JSON-schema suites: 227 passed. Four `test_fr1028_provider_model_override.py` wrapper tests fail on
Windows with and without this change (they need bash).

**AC-11, the live call** (`create_llm(provider="anthropic", model="claude-opus-5-5", effort="low",
max_tokens=1024).invoke("Name three primary colours, one per line, nothing else.")`, key from `.env`, not printed):

```text
provider=anthropic model= claude-opus-5-5
stop_reason= end_turn
usage= {'cache_creation': {'ephemeral_1h_input_tokens': 0, 'ephemeral_5m_input_tokens': 0}, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0, 'inference_geo': 'global', 'input_tokens': 25, 'output_tokens': 13, 'output_tokens_details': {'thinking_tokens': 0}, 'server_tool_use': None, 'service_tier': 'standard', 'speed': 'standard'}
blocks= ['str']
text= 'Red\nBlue\nYellow'
```

**Sizes and gates:** `llm_nodes.py` 448, `executor_base.py` 447, `node_schema.py` 420, `llm_factory.py` 315,
`graph_schema.py` 250, `executor.py` 217, `base.py` 96; `size_gate.py` exit 0, no BASELINE entry. `lint-imports`
3 kept. `req_coverage.py --strict` exit 0 (CAP-28: 2/2 REQs). `check_changelog_req.py`: this fragment
**deferred** (REQ-YG-725 in multi-REQ CAP-28, LLM unavailable locally), not passed (AC-13).

### Deviations from the frozen scope

1. **The line-keyed confessions.** The insertions shifted six hedging ALLOWLIST entries (CONF-240, CONF-243..246,
   CONF-351) and two noqa confessions (`executor_base.py` C901 L199→L201, `llm_nodes.py` C901 L302→L300).
   `scripts/hedging_check.py` and `docs/confessions.md` are re-keyed, as FR-998:166 did; nothing re-described.
   The repo's `noqa_coverage.py --fix` repaired none of them, so the two noqa anchors were moved by hand.
2. **`vulture_whitelist.py`** names `NodeConfig.validate_effort_target`, as for every other Pydantic validator.
   Touching the file ran ruff on it, which failed on `main`'s bare `find_untyped_subschemas` and
   `find_open_objects` (FR-1125, F821); one import line from `yamlgraph.utils.schema_walk` cures it, no `noqa`.
3. **`create_llm`'s complexity.** The effort check took `create_llm` from radon C (20) to D (22), which the gate
   blocks. Both provider checks (the existing `thinking_budget` one, moved verbatim, and the new `effort` one)
   are now `_refuse_unsupported_options` in `llm_factory.py`; `create_llm` is C (17).
4. **The helper's import** in `llm_nodes.py` is `node_or_default as _node_or_default`, the file's own aliased
   style; the plain import, merged by isort, wrapped to five lines and put the file at 451.
5. **`LLMNodeConfig.effort`** is a defaulted field at the end of the dataclass: `test_llm_node_phases.py` builds
   `LLMNodeConfig` directly, and a required field broke eleven of its tests, which C-2's spirit forbids editing.

**Parked (not this FR):** CONF-364 points at `executor_base.py#L172` for `_invoke_llm`, which is not there on
`main`.

## Addendum 2026-10-25: CI's first run

CI's first full run on the PR (`d1c3d56c`, 3.11 and 3.14) failed two tests:

```text
test_fr1151_anthropic_effort.py::TestCreateLLMEffort::test_opus_5_5_low_effort_thinking_as_observed
  AssertionError: assert 'thinking' not in {'model': 'claude-opus-5-5', ..., 'output_config': {'effort': 'low'}, ...}
test_fr716_module_splits.py::TestSplitRelievesGate::test_graph_schema_bisected
  AssertionError: assert 420 < 400
```

1. **AC-16.** CI installs `langchain-anthropic` 1.7.6, whose profile data lists `xhigh` for `claude-opus-5-5`, so
   it sends `thinking: {type: adaptive, display: summarized}` with effort `low`; the local 1.7.0 sends none. The
   observed value is a property of the installed version, not of yamlgraph. The test (`23b68761`) now asserts
   langchain's rule: adaptive exactly when `_reasoning_effort_levels(llm.profile)` holds `xhigh`. The reference
   docs say it depends on the version. `pyproject.toml`'s floor (`>=1.5.1`) needs no change: 1.5.2 already has
   `reasoning_effort` (its wheel, checked).
2. **`node_schema.py` under 400 (FR-716).** The field, the levels and the validator put it at 420. `84a59e05`:
   the levels in `constants.py` (`EffortLevel`, `EFFORT_LEVELS`), the field on one line, and the refusal on race
   nodes and routers with `candidates` as a `GraphConfigSchema` validator, which runs at load in the same call
   (`validate_graph_schema`) and names the node. `node_schema.py` 399, `graph_schema.py` 261. AC-17's tests
   validate the graph instead of building `NodeConfig` directly; the judged behaviour (refused at load) is the
   same. CONF-221 (`constants.py` L48→L53) and CONF-240 (`node_schema.py` L95→L88) re-keyed.
