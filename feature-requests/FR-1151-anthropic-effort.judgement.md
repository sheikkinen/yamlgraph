# Judgement: FR-1151 An `effort` setting for Anthropic llm nodes

**Prior art:** [FR-1151-anthropic-effort.md](FR-1151-anthropic-effort.md) — the FR this judgement rules on, not precedent; dismissed; its own Prior art line dispositions FR-1146, FR-071, FR-1148, FR-1056, FR-1144, FR-455 and FR-1150. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the field path is correct, the precedent is dispositioned and the library surface is real, but the FR never states what setting `effort` does to `thinking` (langchain injects adaptive thinking behind a profile gate the FR does not mention) and it reintroduces its own Problem #2 — a key accepted by the schema and silently dropped — on race and router-race nodes. Authority activates when R-1..R-7 are folded into the FR file.

**Reviewed against:** `feature-requests/FR-1151-anthropic-effort.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (Scripture); `CLAUDE.md`; cited prior art `feature-requests/FR-1148-anthropic-thinking-off.md` (Probe A table L101-105, alternative G L239, Out of scope L243-245), and the existence of `FR-071-thinking-budget-graph-level.md`, `FR-455-reasoning-model-temperature-guard.md`, `FR-1056-deepseek-thinking-off.md`, `FR-1144-race-node-thinking-budget.md`, `FR-1146-anthropic-temperature-deprecated.md`, `FR-1150-llm-providers-split.md` (no `FR-1151-*.judgement.md` exists — this is round 1 under FR-1022); code cited by the FR: `yamlgraph/utils/llm_factory.py`, `yamlgraph/utils/llm_providers.py`, `yamlgraph/utils/anthropic_thinking.py`, `yamlgraph/utils/llm_bounds.py`, `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/node_factory/base.py`, `yamlgraph/node_factory/race_node.py`, `yamlgraph/node_factory/router_race_node.py`, `yamlgraph/models/node_schema.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/executor.py`, `yamlgraph/executor_base.py`, `yamlgraph/linter/checks_providers.py`, `tests/unit/test_fr715_prompt_request.py`, `scripts/size_gate.py`, `scripts/req_coverage.py`, `scripts/check_changelog_req.py`, `capabilities/CAP-28-graph-level-thinking-budget.yaml`, `reference/graph-yaml.md`; and the cited library surface `langchain_anthropic/chat_models.py` (L885-897, L1229-1252, L1316-1318, L1495-1538, L1622-1669).

## What is sound

- **The library claim checks out.** `ChatAnthropic.reasoning_effort: Literal["max","xhigh","high","medium","low"] | None = Field(default=None, alias="effort")` exists at `chat_models.py:1229-1232`, and `_get_request_payload` folds it into `output_config["effort"]` at L1636-1638/1656-1657. The FR quotes the field and its location accurately.
- **The "no edit to `anthropic_thinking.py`" claim is verified, not assumed.** `dispatch_provider` forwards `**kwargs` to the factory (`llm_providers.py:362-364`), `_create_anthropic_llm` copies them into `anthropic_kwargs` and hands them to `ChatAnthropic` through `_bounded` (`anthropic_thinking.py:51-62`), and `_bounded` only *adds* timeout/retries — it strips nothing (`llm_bounds.py:56-85`). A `reasoning_effort` kwarg therefore reaches the constructor untouched. Solution 4 is implementable exactly as written.
- **AC-02's "absent means unchanged" is structurally true**: no kwarg means no `output_config` branch and no adaptive-thinking branch (both gated on `self.reasoning_effort` / `reasoning_effort_applied`, L1633-1669). No existing test should move.
- **Prior art is genuinely dispositioned.** FR-1148 L239 rejects effort-mapping "for this FR — a new config surface (effort) belongs in its own FR" and L243 lists it Out of scope; FR-1146 defers the same surface. This FR is the named successor, not a re-entry into rejected territory (FR-737 satisfied). No rejected FR covers it.
- **The field path mirrors `thinking_budget` layer for layer** — schema (`node_schema.py:82-85`, `graph_schema.py:115-124`), node resolution (`llm_nodes.py:125-128`, `:160`, `:363`), request (`executor_base.py:63`, `executor.py:57/88/129/209`), factory + cache key (`llm_factory.py:218-234`). Commandment 4 is honoured; there is nothing to invent.
- **AC-07 is already mechanically enforced** by `tests/unit/test_fr715_prompt_request.py::TestSignatureParity` (set equality of `execute_prompt` params and `PromptRequest` fields) — a real gate, not an aspiration.
- **AC-10's "class marker" works**: `scripts/req_coverage.py:127-141` applies class-level `@pytest.mark.req` decorators to every test method.
- **The size-gate pressure is named honestly up front.** `llm_nodes.py` is exactly 449 lines against `LIMIT = 450` (`scripts/size_gate.py:25`) — one line of headroom, and the FR says so and plans an offset instead of discovering it mid-flight.
- **Research substance (FR-890).** The in-body table gives five genuinely distinct solution classes (named field / generic passthrough / overload an existing field / mirror the API dict / all providers at once), each with a repo-precedent line or an explicit absence, and answers `is_this_a_graph`. It clears the substance bar, though it preserves no disagreement — see the recommendation below.

## Required revisions

### R-1: State what `effort` does to `thinking`, and pin it with an AC

The FR's Summary says "absent, the request is unchanged" but never says what the request becomes when `effort` IS present. `chat_models.py:1659-1669` injects `payload["thinking"] = {"type": "adaptive", "display": "summarized"}` when effort was applied, `thinking` was not explicitly set, **and** `"xhigh" in _reasoning_effort_levels(self.profile)` (L885-897) — a profile-data gate the FR does not mention anywhere. The first consumer's exact case (`claude-opus-5-5`, `effort: low`, no `thinking_budget`) therefore has an unstated second effect on the request.

Fold both of these:

1. Amend the Summary and Ideal Result to read, in substance: "when `effort` is set and the node sets no `thinking_budget`, the request additionally carries whatever `thinking` `langchain_anthropic` injects — `{"type": "adaptive", "display": "summarized"}` on models whose profile declares the `xhigh` level (`chat_models.py:1659-1669`), and nothing on models whose profile does not. yamlgraph neither adds nor suppresses this."
2. Add AC-16 (below): the offline payload probe for `claude-opus-5-5` + `effort: low` with no `thinking_budget` asserts the **observed** `thinking` value verbatim and the FR records it. Whatever the installed profile data yields is the accepted answer — the AC exists to make the behaviour recorded rather than discovered in production.

### R-2: Refuse `effort` where it would be silently dropped

`NodeConfig` (`node_schema.py:73`) is one model for every node type, and `candidates` is one of its fields (L128-131). Adding `effort` there makes `effort: low` schema-valid on a `race` node and on a `router` node with `candidates:` — both of which resolve their own config (`race_node.py:344-348`, `router_race_node.py:67-71`) and would drop it without a word. That is this FR's own Problem #2 reborn at a different node type, and it is not closed by anything in the current plan.

Add to Proposed Solution 1 and implement: a `model_validator(mode="after")` on `NodeConfig` that raises when `effort` is set and (`type` is not `llm`/`router`, **or** `candidates` is not None), with a message naming `effort`, the node type, and that `effort` is supported on `llm` nodes and `router` nodes without `candidates`. Witnessed by AC-17.

This is a schema-layer change, inside D-1 — it does **not** authorize touching `race_node.py` or `router_race_node.py`.

### R-3: Document the reach of `defaults.effort`, and witness it

`defaults` are shared by every node, so a graph with `defaults.effort: high` and a race node must still load (refusing it would break a legitimate `llm`-node author). Fold the asymmetry into the docs instead of leaving it to be found:

1. `reference/graph-yaml.md`: in the race-node table (the `thinking_budget` row at L1032 is the model), add an `effort` line stating that race and router-race candidates never receive `effort`, and that `defaults.effort` reaches only `llm` and candidate-less `router` nodes.
2. Add AC-18: a graph with `defaults.effort` and a race node loads and compiles; the race candidates are built without any effort kwarg.

### R-4: The provider refusal must be on the *resolved* provider

AC-03 as written (`create_llm(provider="openai", effort="low")`) only proves the literal-argument case. `create_llm` resolves the provider from the argument, then `PROVIDER` env, then the default (`llm_factory.py:151-161`) — a graph that omits `provider` runs on whatever `PROVIDER` is set in the operator's environment, so the loud refusal must fire on the resolved value or it will not fire at all for the most common graph shape.

Amend AC-03 and add AC-19 (below): with `provider=None` and `PROVIDER` set to a non-Anthropic provider in the environment, `create_llm(effort="low")` raises `ValueError` naming `effort` and that resolved provider, before any client is constructed.

### R-5: Bound the `node_or_default` extraction

Solution 6 is a refactor carried by a feature FR purely to buy size-gate headroom. Constrain it so it cannot grow:

- `node_or_default(node_config, defaults, key)` lands in `yamlgraph/node_factory/base.py` (currently 90 lines) and has exactly two call sites: the `thinking_budget` resolution and the new `effort` resolution, both in `llm_nodes.py`.
- Behaviour is identical to the current code, including an explicit node `0`/falsy value winning over a default (`llm_nodes.py:126-128` is the reference semantics).
- `race_node.py:347-348`'s duplicate walrus resolution is **not** migrated in this FR.
- The existing `thinking_budget` tests are the witness that the extraction changed nothing; they must pass unmodified. Any test edit to those files is a defect, not a refactor.

### R-6: Name the REQ bookkeeping exactly

AC-12 says "CAP-28 holds the new REQ" without saying what else moves. Fold:

- `capabilities/CAP-28-graph-level-thinking-budget.yaml` gains the new `REQ-YG-XXX` entry (with its own `modules:` list), and its `fr:` line gains `FR-1151` alongside `FR-071, FR-1148`. Its `description:`/`name:` must stop claiming the CAP is only about `thinking_budget`.
- The changelog fragment's `req:` names the **new** REQ, never `REQ-YG-083`. Note for the enforcer: CAP-28 becomes a multi-REQ CAP, so `scripts/check_changelog_req.py` moves this fragment from the mechanical path to the LLM semantic check (`check_changelog_req.py:287-319`) — a `deferred` result when the model is unavailable is not a pass; record which it was.

### R-7: Bind AC-11 to an honest record

Add to AC-11: the live call's provider, model, `usage` and block types are pasted verbatim into the FR. If `ANTHROPIC_API_KEY` or access to `claude-opus-5-5` is unavailable on the executing host, AC-11 is recorded in the FR as **owed**, naming the blocker — it is never satisfied by a reconstructed or simulated transcript, and the PR body repeats the owed status. The offline payload probes (AC-01/02/08/16) are not a substitute and do not close it.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/models/node_schema.py` — `effort` field on `NodeConfig` + the node-type/candidates refusal validator (R-2) |
| D-2 | `yamlgraph/models/graph_schema.py` — `defaults.effort` validator, mirroring `validate_defaults_thinking_budget` |
| D-3 | `yamlgraph/node_factory/llm_nodes.py` — `LLMNodeConfig.effort`, node-over-defaults resolution, pass to `execute_prompt` |
| D-4 | `yamlgraph/node_factory/base.py` — `node_or_default` helper, two call sites (R-5) |
| D-5 | `yamlgraph/executor_base.py` — `PromptRequest.effort`; `yamlgraph/executor.py` — `execute_prompt` parameter, `_get_llm` → `create_llm(effort=...)` |
| D-6 | `yamlgraph/utils/llm_factory.py` — `create_llm(effort=...)`, resolved-provider refusal (R-4), cache key, `reasoning_effort` kwarg into the factory call |
| D-7 | `tests/unit/test_fr1151_anthropic_effort.py` — the RED-then-GREEN witnesses |
| D-8 | `reference/graph-yaml.md` (defaults table, `llm` node table, race table note, example comment); `capabilities/CAP-28-*.yaml`; regenerated `ARCHITECTURE.md`; `changelog/unreleased/fr-1151-anthropic-effort.md`; `docs/diary/` entry |

**Not authorized:** `yamlgraph/utils/anthropic_thinking.py` (the effort kwarg rides `**kwargs`; no edit is needed and none is permitted); `race_node.py` / `router_race_node.py` (including migrating their `thinking_budget` resolution to the new helper); `executor_async.py` and `execute_prompt_async`; a new linter check or W-code; OpenAI/Azure `reasoning_effort`, Google `thinking_level`, DeepSeek effort; any change to `thinking_budget`'s meaning, its validators, or its existing tests; wrapping, re-implementing or pre-empting langchain's own model/effort/thinking refusals (`chat_models.py:1495-1538`) — a 400 or a langchain `ValueError` stands and is recorded; a `model_kwargs`/`output_config` passthrough (alternatives B and D, rejected); any new module.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No file in the "Not authorized" list is edited — in particular `anthropic_thinking.py`, `race_node.py`, `router_race_node.py`, `executor_async.py` | GATE |
| C-2 | `thinking_budget` semantics are unchanged and its existing tests pass **unmodified**; a needed edit to them means the refactor (R-5) broke behaviour | GATE |
| C-3 | RED commit (failing tests, `SKIP=pytest`) precedes the GREEN commit; `git log` shows both (Commandment 7) | GATE |
| C-4 | Every touched module ≤ 450 lines with no new `BASELINE` entry in `scripts/size_gate.py` (R-5's offset is the only sanctioned relief; if it is insufficient, stop and return to the Judge rather than baselining or splitting a module) | GATE |
| C-5 | yamlgraph adds no rule of its own about which model accepts which effort/thinking combination; langchain's `ValueError` and the API's 400 propagate unwrapped and are recorded | GATE |
| C-6 | No `--no-verify`, no `Co-authored-by` trailer; multi-line commit messages via `./tmp/msg.txt` | GATE |
| C-7 | AC-11 is reported as run-with-output or owed-with-blocker; "verified" is not written for a probe that did not execute (Commandment 6) | GATE |
| C-8 | The FR file is updated with implementation status, the recorded probe outputs, and any deviation, before the PR is opened | GATE |
| C-9 | The enforcer stops at a review-ready PR; merge is the human's decision (Submit rite) | GATE |

### Questions for the human (not absorbed)

1. **Spend.** AC-11 authorizes one live `claude-opus-5-5` call at ≈ $0.01 on whatever key the executing host holds. Confirm the spend and that an Anthropic key is actually available here; if not, AC-11 ships owed (R-7).
2. **Hardness of R-2.** The revision makes `effort:` on a race / router-race node a **load-time error**, matching this FR's premise that a silently dropped key is the defect. If you would rather it be a lint warning (W-code) so existing graphs cannot break, say so — that choice changes D-1 and would need a linter deliverable this judgement does not authorize.

### Recommendations (separate FRs — not authorized here)

- Carry `effort` to race and router-race candidates, the way FR-1144 carried `thinking_budget`. This FR deliberately refuses it instead; the successor FR has an obvious shape and a named precedent.
- Migrate `race_node.py:347-348`'s duplicate node-over-defaults resolution onto `node_or_default` once the helper exists.
- `thinking_budget`'s linter checks (`checks_providers.py`, W071-*) have no effort analogue — e.g. `effort` on a model whose profile lacks the level. Worth a check only once a second consumer exists.
- Research-method note (advisory, no revision): the alternatives table disposes of five real classes but records no disagreement between them — every row is a clean rejection. The next FR in this line would be stronger for preserving one genuine two-sided argument (`forced_opposite`).

Authority granted: once R-1..R-7 are folded into `feature-requests/FR-1151-anthropic-effort.md`, implement the optional `effort` field (`low|medium|high|xhigh|max`) on graph `defaults` and on `llm`/candidate-less `router` nodes, carried through node resolution, `PromptRequest`/`execute_prompt`, and `create_llm` into `ChatAnthropic(reasoning_effort=...)` — refused loudly on any other resolved provider and on any node type that would drop it — with the tests, docs, CAP-28 REQ, changelog fragment and diary entry listed above, and nothing else.
