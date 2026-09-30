# Judgement: FR-1144 Race Nodes Honour `thinking_budget`

**Verdict:** APPROVED WITH REVISIONS — the correction is narrow, evidenced, and feasible; authority activates only after R-1 through R-3 are folded into the feature request.

**Reviewed against:** `feature-requests/FR-1144-race-node-thinking-budget.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-071-thinking-budget-graph-level.md`; `feature-requests/FR-230-google-vertex-thinking-budget.md`; `feature-requests/FR-232-race-node-type.md`; `feature-requests/FR-272-router-node-race-candidates.md`; `feature-requests/FR-1056-deepseek-thinking-off.md`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/router_race_node.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/utils/llm_providers.py`; `tests/unit/test_race_node.py`; `tests/unit/test_router_race.py`; `reference/graph-yaml.md`; `capabilities/CAP-28-graph-level-thinking-budget.yaml`; `capabilities/CAP-88-google-vertex-thinking-budget.yaml`; `capabilities/CAP-91-race-node-type.yaml`; `capabilities/CAP-122-router-node-race-candidates.yaml`; `capabilities/CAP-273-deepseek-non-thinking.yaml`; `ARCHITECTURE.md`.

## What is sound

The problem is real and located at one construction seam. The regular LLM path resolves node value before graph default (`llm_nodes.py:126-128`), while `_build_candidate_llms` exposes no budget parameter and calls `create_llm` without one (`race_node.py:189-207`). Both direct race execution (`race_node.py:396`) and router-race execution (`router_race_node.py:67-70`) use that helper. The proposed signature extension therefore corrects both paths without introducing another abstraction.

Scope, consistency, and single responsibility are sound. The Ideal Result and Proposed Solution both preserve the existing node-level field and provider meanings (`FR-1144:75-80,104-136`). Per-candidate budgets, prompt metadata, Azure reasoning control, and the downstream csap migration are explicitly dispositioned (`FR-1144:154-175`). No smaller production change would fix both existing callers.

Feasibility and architecture alignment are established by current code. `LLMNodeConfig` already carries the resolved value into router execution (`llm_nodes.py:126-128,160`); `create_llm` already accepts and caches `thinking_budget`; provider dispatch forwards it only to registered thinking factories (`llm_providers.py:371-373`); Vertex consumes it (`llm_providers.py:241-254`) while Azure's constructor does not accept it (`llm_providers.py:46`). The implementation can therefore remain a typed pass-through in the node-factory layer.

The research is substantive enough for authority after revision: the FR names the first consumer, records a four-row observed latency/token probe, dispositions four genuine alternatives, answers `is_this_a_graph`, and distinguishes all cited prior art (`FR-1144:5-33,43-73,154-161`). This is not metric-tooling, so the measurement raw-output gate does not apply.

Strategic classification: **Framework primitive correction**. Race and router-race are existing framework primitives with multiple consumers; this FR repairs their failure to honor an already-supported cross-provider setting. It is not an example or documentation-only pattern.

Most criteria are directly testable, but the current test-file assignment and provider-boundary wording leave two avoidable false-green paths. Those are resolved below.

## Required revisions

### R-1: Add explicit capability and requirement traceability

Add `capabilities/CAP-301-race-node-thinking-budget.yaml` with requirement `REQ-YG-724`. The requirement must state that direct race and router-race nodes resolve `thinking_budget` as node value → graph default → `None`, pass the resolved value to every candidate's `create_llm` call, and preserve existing provider dispatch semantics. Register CAP-301 / REQ-YG-724 in generated `ARCHITECTURE.md`, and require every new test to carry `@pytest.mark.req("REQ-YG-724")`.

Fold these artifacts and `python scripts/req_coverage.py --strict` into the acceptance criteria. The present FR has no requirement mapping despite doctrine requiring every test to link to `ARCHITECTURE.md` (`.github/copilot-instructions.md:170-171`).

### R-2: Assign witnesses to both actual call paths

Replace the single statement requiring tests only in `tests/unit/test_race_node.py` (`FR-1144:149`) with explicit RED witnesses in:

- `tests/unit/test_race_node.py` for direct `type: race` resolution, defaulting, override, and per-candidate forwarding.
- `tests/unit/test_router_race.py` for router-with-`candidates` resolution, defaulting, override, and per-candidate forwarding.

The router path calls the helper from a different module (`router_race_node.py:67-70`); AC-4 cannot be proven by a direct-race test alone.

### R-3: Separate node forwarding from provider dispatch in AC-5

Rewrite AC-5 as two mechanically distinct assertions:

1. A mixed Vertex/Azure race forwards the same resolved `thinking_budget=0` into both candidates' `create_llm` calls and constructs both candidates without error.
2. At the existing provider-dispatch boundary, the Vertex factory receives `thinking_budget=0`, while the Azure factory is invoked without a `thinking_budget` argument.

This preserves the intended behavior visible at `llm_providers.py:371-373` and prevents a test patched only at `create_llm` from claiming that Azure constructor behavior was verified. No provider implementation change is authorized.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/node_factory/race_node.py`: extend `_build_candidate_llms` with the resolved budget and pass it to each `create_llm` call; resolve node → defaults → `None` in `create_race_node` |
| D-2 | `yamlgraph/node_factory/router_race_node.py`: pass `cfg.thinking_budget` to the shared candidate builder |
| D-3 | `tests/unit/test_race_node.py` and `tests/unit/test_router_race.py`: RED-first REQ-YG-724 witnesses |
| D-4 | `capabilities/CAP-301-race-node-thinking-budget.yaml` and regenerated `ARCHITECTURE.md` traceability |
| D-5 | `reference/graph-yaml.md`: add the race-node `thinking_budget` property and node → defaults resolution |
| D-6 | One `changelog/unreleased/` fix fragment for FR-1144 / REQ-YG-724 |
| D-7 | `feature-requests/FR-1144-race-node-thinking-budget.md`: fold revisions and record implementation status, decisions, and deviations |

Not authorized: per-candidate `thinking_budget`; prompt-metadata or graph-metadata resolution; schema changes; linter changes; provider-factory or `create_llm` semantic changes; Azure/OpenAI `reasoning_effort`; new provider mappings; csap configuration or dependency-pin changes; race concurrency, timeout, cancellation, routing, cache, or error-policy changes; new graph or prompt artifacts.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and the revised acceptance criteria into the FR before production implementation begins. | GATE |
| C-2 | Preserve the exact resolution order node value → graph default → `None`; explicit `0` must not be mistaken for absence. | GATE |
| C-3 | Use the existing shared `_build_candidate_llms` seam for both callers; do not duplicate candidate construction or provider logic. | GATE |
| C-4 | Do not modify `create_llm`, provider factories, provider registries, schema, or linter behavior under this authority. | GATE |
| C-5 | Commit failing REQ-YG-724 witnesses before the GREEN implementation, and satisfy targeted tests, the fast unit suite, and strict requirement coverage. | GATE |
| C-6 | Any need for per-candidate budgets, metadata resolution, provider remapping, or linter policy stops enforcement and returns as a separate FR. | GATE |

Authority granted: after R-1 through R-3 are folded, implementation may wire the already-resolved race-node budget through the shared candidate-construction seam, add the frozen witnesses and traceability, and update the named documentation and changelog surfaces.
