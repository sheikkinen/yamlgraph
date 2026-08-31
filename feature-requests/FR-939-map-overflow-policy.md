# Feature Request: Map Overflow Policy — Typed `on_overflow` Contract

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-31
**First consumer / first event:** the fi-catalog pilot (component D,
`docs/plan-web-toolkit.md`) — the first map run whose `over` list
exceeds `max_items`. Today that run silently computes from a truncated
prefix and reports success. Nearer-term: any existing map graph that
crosses its cap gets a log-only warning and a plausible wrong answer.
**Research:** [FR-939-map-overflow-policy.research.md](FR-939-map-overflow-policy.research.md)
(brief `research-briefs/fr939-map-overflow-brief.md`, run 2026-08-31,
personas: os-infra-primitivist, data-process-planner,
yamlgraph-native-planner, subtractionist, librarian)
**Prior art:** `027-execution-safety-guards.md` introduced
truncate-and-warn deliberately as a demo-scale cost guard — this FR
explicitly supersedes that disposition (truncation survives as opt-in).
FR-936 bundled this with three other map concerns and was SPLIT
(`FR-936-map-node-hardening.judgement.md`); this FR is deliverable D-2
and stays inside its fence — no timeout (D-3, `069-map-node-timeout.md`),
input projection (D-1), or retry (D-4) changes. `CAP-11-subgraph-map.yaml`
governs. REJECTED-FR sweep: no prior proposal on overflow disposition.

## Summary

Replace silent truncate-and-warn map overflow with a typed
`on_overflow: error | truncate` contract, validated at graph load,
enforced before the first sub-node executes, defaulting to `error`.

## Ideal Result

A map run can never report success on partial input without the graph
author having explicitly asked for that. Overflow is decided before any
LLM spend, and the error names the node, the observed count, and the
cap — actionable without log archaeology.

## Value Statement

Anyone running a map at production scale stops receiving silently
incomplete results; graphs that deliberately sample keep one explicit
YAML line to say so.

## Problem

`map_edge` (`yamlgraph/compile/map_compiler.py:350-365`) resolves
`max_items` (node) → `defaults.max_map_items` (graph) →
`DEFAULT_MAX_MAP_ITEMS = 100`, then on overflow logs a warning, slices
the list, dispatches the surviving prefix, and the run succeeds. No
state, exit code, or artifact records the drop. At 500k items with the
default cap, the result is computed from 0.02% of the input and labeled
complete — the `plausible_wrong_answer` trap, in violation of
Commandment 6's ban on silent fallbacks.
`tests/unit/test_fr027_execution_safety.py` currently pins this defect
as expected behavior.

## Proposed Solution

Research verdict (5 personas, 3 convergent on schema-data class): typed
disposition field + load-time validation + pre-dispatch enforcement.
Airflow's `max_map_length` fail-fast-at-parse is the external precedent.

1. **Schema** — add `on_overflow: Literal["error", "truncate"]` to the
   map node schema (`yamlgraph/models/node_schema.py`) and
   `defaults.on_overflow` to graph defaults. Default: `error`. Invalid
   values rejected at graph load/validation (Pydantic), not at fan-out.
2. **Enforcement** — in `map_edge`, when `len(items) > max_items`:
   - `error` (default): raise before constructing any `Send`, message
     containing node name, observed count, and configured cap.
   - `truncate`: current behavior — slice, `logger.warning`, proceed.
3. **Resolution order** — node `on_overflow` > graph
   `defaults.on_overflow` > `error`. Cap resolution order unchanged.
4. **Docs** — update the map section of `reference/graph-yaml.md` only.

```yaml
nodes:
  fetch_all:
    type: map
    over: "state.domains"
    max_items: 500000
    on_overflow: error      # default; truncate = explicit sampling
```

Preserved disagreement (research): default `truncate` was argued twice
to avoid breaking existing capped graphs loudly; the subtractionist
argued a mandatory field with no default. Decision: default `error` per
the FR-936 judgement (AC-05) and Commandment 6 — a graph that crosses
its cap today is already producing wrong answers; a loud failure at the
next run is the fix working, not a regression. Graphs that want the old
behavior add one line.

`is_this_a_graph`: no — compile-time contract change inside the
framework's validation and fan-out boundary; all five personas concur.

## Acceptance Criteria

- [ ] AC-1: `on_overflow` validates as `error | truncate` at graph load;
      invalid values fail validation with a clear message (RED first).
- [ ] AC-2: Default `error`: overflow raises before the first sub-node
      call; message contains node name, observed count, configured cap.
- [ ] AC-3: Explicit `truncate` preserves slice-and-warn exactly.
- [ ] AC-4: Tests cover node-level `max_items`, graph-level
      `max_map_items`, within-cap input (no behavior change), invalid
      policy value, and the explicit truncate path
      (judgement AC-06); `tests/unit/test_fr027_execution_safety.py`
      updated to pin the new contract.
- [ ] AC-5: New CAP-11 requirement ID allocated; RED witnesses tagged
      `@pytest.mark.req`; RED and GREEN committed separately.
- [ ] AC-6: `reference/graph-yaml.md` map section documents
      `on_overflow`; changelog fragment in `changelog/unreleased/`;
      diary entry.
- [ ] AC-7: No changes to timeout, retry, payload projection, or
      durability surfaces (judgement C-1/C-6); existing map tests
      otherwise green.

## Alternatives Considered

See the research record. Rejected: mandatory field with no default
(subtractionist) — forces a migration edit on every existing map graph
while default `error` already delivers the safety; log-only warning
hardening — leaves the contract out-of-band; deleting the cap — removes
the cost guard FR-027 correctly installed.

## Related

- `FR-936-map-node-hardening.md` (SPLIT parent) and its judgement (D-2)
- `027-execution-safety-guards.md` (superseded disposition)
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` (component D, first consumer)
