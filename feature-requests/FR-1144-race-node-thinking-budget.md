# Feature Request: FR-1144 Race Nodes Honour `thinking_budget`

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (PR pending review) — judged 2026-09-30 APPROVED WITH
REVISIONS; R-1..R-3 folded (see [Judgement fold](#judgement-fold-2026-09-30));
see [Implementation status](#implementation-status-2026-09-30)
**Capability:** CAP-301 / REQ-YG-724
**Requested:** 2026-09-30
**First consumer / first event:** csap (customer-service-agent-platform, the
healthcare voicebot that pins yamlgraph `==0.5.25`). Its `flex_navigator`
graph has 10 `type: race` nodes racing `vertex/gemini-2.5-flash` against
`azure/aaa-gpt-5.4-mini`. The first event is the next caller turn after csap
bumps its pin and sets `thinking_budget: 0` on the race nodes: Gemini then
stops spending ~600 reasoning tokens (~4 s) on every turn.
**Research:** in-body dispositioned alternatives table (FR-889 style). See
[Alternatives Considered](#alternatives-considered). Each row rests on a code
read of `origin/main` 6e11be5f (0.6.2) or on the probe in
[Problem](#problem), not on a prediction.
**`is_this_a_graph`:** No. The change passes one resolved value through at
the client-construction seam. Its witness is a constructor-argument
assertion, not an LLM judgement.
**Prior art:**
- [FR-071](FR-071-thinking-budget-graph-level.md): added `thinking_budget` to
  `llm` nodes and graph `defaults`. Race nodes were never wired to it. This FR
  wires them and does not change what the value means.
- [FR-230](FR-230-google-vertex-thinking-budget.md): made `google`/`vertex`
  accept any non-negative budget, `0` included. That meaning is what this FR
  needs, and it is unchanged.
- [FR-232](FR-232-race-node-type.md) and
  [FR-272](FR-272-router-node-race-candidates.md): created the race node and
  the router-race path. Both build candidates through `_build_candidate_llms`,
  so a single edit fixes both.
- [FR-1056](FR-1056-deepseek-thinking-off.md): mapped `thinking_budget: 0` to
  `reasoning_effort="none"` for DeepSeek. Every provider-side mapping stays as
  it is. This FR only makes race candidates reach those mappings.

## Summary

`_build_candidate_llms` (`yamlgraph/node_factory/race_node.py:189`) calls
`create_llm(temperature=, provider=, model=)` and never passes
`thinking_budget`. It does not read the node, the graph `defaults`, or the
candidate. As a result, every race candidate runs at its provider's default
thinking level. For Gemini 2.5 Flash that level is dynamic thinking. The fix is
to resolve `thinking_budget` the same way `llm` nodes already do (node first,
then `defaults`) and pass it to every candidate.

## Value Statement

Graph authors who use race nodes for latency hedging get the thinking level
they configured. Today a thinking candidate turns a latency race into a
single-provider race without anyone noticing.

## Problem

`llm` nodes resolve `thinking_budget` from the node and then from `defaults`
(`llm_nodes.py:125-128`). `create_race_node` resolves `temperature` the same
way (`race_node.py:343-345`) but has no `thinking_budget` resolution. The node
schema accepts `thinking_budget` on a race node (`NodeConfig.thinking_budget`,
`node_schema.py:82`), so an author who writes it gets no error, and the value
is ignored.

Probe on 2026-09-30, run from the csap checkout on yamlgraph 0.5.25 (the race
path is byte-identical on main): one classification prompt, `temperature=0.0`,
one call per row, built through `create_llm` the way the race node builds its
candidates:

| Candidate | `thinking_budget` | Latency | Output tokens | Reasoning tokens |
|---|---|---|---|---|
| `vertex/gemini-2.5-flash` | not passed (the race path today) | 5.46 s | 601 | 600 |
| `vertex/gemini-2.5-flash` | `0` | 1.13 s | 1 | 0 |
| `azure/aaa-gpt-5.4-mini` | not passed | 1.16 s | 4 | 0 |
| `azure/aaa-gpt-5.4-mini` | `0` | 1.26 s | 4 | 0 |

The Gemini candidate thinks on every race call. That makes it about 4 s slower
than its rival, so the race almost never uses it as a hedge.

## Ideal Result

A race node takes `thinking_budget` from the node, or from the graph
`defaults` when the node has none, and gives it to every candidate. This is the
same resolution order an `llm` node uses. Each provider factory then applies
its existing mapping, and a provider with no thinking control ignores the
value, as it already does for `llm` nodes.

## Planned Operations

```yaml
probes:
  - "read dispatch_provider (llm_providers.py) for how azure/openai/mistral treat thinking_budget=0 — dropped silently confirms no provider-side change"
  - "read create_llm guard (llm_factory.py) for thinking_budget>=1024 with a non-thinking provider — raises means a mixed race with a real budget pre-fails that candidate"
  - "grep tests/unit/test_race_node.py and test_router_race.py for create_llm call assertions — decides whether RED patches create_llm or asserts constructor kwargs"
branches:
  - "thinking_budget>=1024 on a race that has a non-thinking candidate → that candidate pre-fails at construction via the existing pre_errors path, the same outcome as an llm node; add a linter warning only if the judge requires it"
  - "a race test asserts the exact create_llm kwargs → update it to include thinking_budget, never loosen it"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "csap pin bump (owner)"
commands:
  - scripts/judge.sh
  - pytest tests/unit/test_race_node.py tests/unit/test_router_race.py -q --no-cov
  - pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

In `create_race_node`, resolve the value once next to `temperature`:

```python
thinking_budget = node_config.get("thinking_budget")
if thinking_budget is None:
    thinking_budget = defaults.get("thinking_budget")
```

Pass it through `_build_candidate_llms(candidates, temperature,
thinking_budget)` into `create_llm(..., thinking_budget=thinking_budget)`.
Router-race (FR-272) calls the same helper, so it resolves the value the same
way from its router node config and `defaults`.

Author-facing result:

```yaml
defaults:
  thinking_budget: 0          # every llm AND race node, unless overridden

nodes:
  classify_intents:
    type: race
    prompt: classify_intents
    thinking_budget: 0        # or per node
    candidates:
      - { provider: vertex, model: gemini-2.5-flash }
      - { provider: azure,  model: aaa-gpt-5.4-mini }
```

There is no new field. The race node already accepts `thinking_budget`, and
this change makes it take effect.

## Judgement fold (2026-09-30)

| Revision | Disposition |
|---|---|
| R-1 traceability | **Folded.** New `capabilities/CAP-301-race-node-thinking-budget.yaml` owning REQ-YG-724 (both IDs checked free on `origin/main` and all remote branches at fold time; re-check at push). AC-07/AC-08. |
| R-2 witnesses on both call paths | **Folded.** Direct race in `tests/unit/test_race_node.py`, router-race in `tests/unit/test_router_race.py`. AC-04/AC-07. |
| R-3 forwarding vs provider dispatch | **Folded.** AC-5 split into AC-05 (both `create_llm` calls get `0`) and AC-06 (Vertex factory gets `thinking_budget=0`, Azure factory called without it). No provider change authorized. |

Linter coverage: the judge did not ask for it and C-4 forbids it; stays out of scope.

## Acceptance Criteria

- [ ] AC-01: A direct `type: race` node with node-level `thinking_budget: 0` calls `create_llm(..., thinking_budget=0)` once for every candidate.
- [ ] AC-02: A direct race node with no node-level value uses `defaults.thinking_budget`; when both are absent, every candidate call receives `thinking_budget=None`.
- [ ] AC-03: For a direct race node, a node-level value, including explicit `0`, overrides a different graph default.
- [ ] AC-04: A router node with race `candidates` satisfies AC-01 through AC-03 through its `LLMNodeConfig.thinking_budget` value.
- [ ] AC-05: A mixed Vertex/Azure race with `thinking_budget: 0` constructs both candidates and forwards `0` to both `create_llm` calls.
- [ ] AC-06: A provider-dispatch witness proves that Vertex's factory receives `thinking_budget=0` and Azure's factory is called without a `thinking_budget` argument; existing provider semantics remain unchanged.
- [ ] AC-07: RED tests precede GREEN implementation in git history; direct-race tests live in `tests/unit/test_race_node.py`, router-race tests live in `tests/unit/test_router_race.py`, and every new test carries `@pytest.mark.req("REQ-YG-724")`.
- [ ] AC-08: `capabilities/CAP-301-race-node-thinking-budget.yaml` defines REQ-YG-724 with direct-race and router-race resolution/forwarding contracts, `ARCHITECTURE.md` registers both, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: `reference/graph-yaml.md` adds `thinking_budget` to the race properties table and states node value → graph default → `None`, shared across all candidates.
- [ ] AC-10: `pytest tests/unit/test_race_node.py tests/unit/test_router_race.py -q --no-cov` passes.
- [ ] AC-11: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes.
- [ ] AC-12: A `changelog/unreleased/` fragment has `type: fix`, identifies FR-1144 and REQ-YG-724, and describes race and router-race behavior.
- [ ] AC-13: The FR records the folded judgement revisions and, after enforcement, implementation status plus any deviations.

## Implementation status (2026-09-30)

RED `0a8ba253` (10 witnesses + CAP-301 + ARCHITECTURE.md), GREEN `f8903df0`
(production change + changelog fragment).

| AC | Status | Evidence |
|---|---|---|
| AC-01 | met | `TestRaceThinkingBudget::test_resolved_budget_reaches_every_candidate[node-zero]` |
| AC-02 | met | same test, `[defaults]` and `[unset]` (explicit `thinking_budget=None` kwarg) |
| AC-03 | met | same test, `[node-zero-overrides-default]` (0 over 2048) |
| AC-04 | met | `TestRouterRaceThinkingBudget::test_resolved_budget_reaches_every_candidate`, all four cases |
| AC-05 | met | `test_mixed_vertex_azure_zero_constructs_both`: both candidates armed, both `create_llm` calls get `0` |
| AC-06 | met | `test_vertex_factory_gets_zero_azure_factory_gets_none`: real `create_llm`/`dispatch_provider`, patched `_PROVIDER_FACTORIES`; vertex called `(model, 0.0, 0)`, azure `(model, 0.0)` |
| AC-07 | met | RED commit precedes GREEN; all new tests carry `REQ-YG-724` |
| AC-08 | met | `capabilities/CAP-301-race-node-thinking-budget.yaml`; ARCHITECTURE.md regenerated; `req_coverage.py --strict` exit 0 |
| AC-09 | met | `reference/graph-yaml.md` race properties table |
| AC-10 | met | 70 passed |
| AC-11 | met | pre-commit fast unit suite passed on the GREEN commit |
| AC-12 | met | `changelog/unreleased/fr-1144-race-node-thinking-budget.md` |
| AC-13 | met | this section |

Decisions and deviations:

- The resolution in `create_race_node` uses a walrus and the local name
  `budget`. `race_node.py` was 447 lines against the 450 hard gate; the
  `temperature`-style three-line form plus a wrapped call site came to 452.
  The behaviour is identical (explicit `0` is kept, only `None` falls back).
- The RED commit used `SKIP=pytest` per Commandment 7; every other hook ran.
- No other deviation. `create_llm`, provider factories, schema and linter
  are untouched (C-4).

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Per-candidate `thinking_budget` in `candidates[i]` | Rejected for now. The first consumer wants one value for every candidate, and the schema already carries a node-level field. Add it later only if a consumer needs different budgets per candidate. |
| Read `thinking_budget` from prompt YAML `metadata` | Rejected. `prepare_messages` returns only provider and model from prompt metadata, and `llm` nodes don't read a thinking budget there either. Changing that would be a separate, framework-wide FR. |
| Map `thinking_budget: 0` to `reasoning_effort` for `azure` (FR-1056 style) | Out of scope. The probe shows `aaa-gpt-5.4-mini` already returns 0 reasoning tokens by default, so nothing witnesses a problem. Azure also serves non-reasoning deployments that may reject `reasoning_effort`. |
| Fix it in csap by swapping Gemini for a non-thinking model | Rejected. It hides the framework bug from every other race user and drops the provider hedge. |

## Related

- `yamlgraph/node_factory/race_node.py:189` (`_build_candidate_llms`), `:343`
  (temperature resolution)
- `yamlgraph/node_factory/llm_nodes.py:125-128` (reference resolution)
- `yamlgraph/node_factory/router_race_node.py` (shares the helper)
- csap follow-up, not part of this FR: csap writes `thinking_budget: 0` under
  graph `metadata:` and prompt `metadata:`, and yamlgraph reads neither. After
  the pin bump, csap must move the value to `defaults:`.

## Out of Scope (named, not forgotten)

- Azure/OpenAI `reasoning_effort` control (see the table above).
- Linter coverage for race-node `thinking_budget` (not requested by the judge; C-4).
