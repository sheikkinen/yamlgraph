# Feature Request: Map Overflow Policy — Typed `on_overflow` Contract

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented (branch `feat/fr939-map-overflow`, 2026-09-26).
Judged APPROVED WITH REVISIONS
(`FR-939-map-overflow-policy.judgement.md`, 2026-08-31). Revisions R-1–R-4
folded below and into the research record. Human review recorded —
operator instruction "worktree enforce 939, 1084, 1085" (2026-09-26);
gate C-1 satisfied, authority active.
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

Research verdict (solution classes in the research record, R-1 fold):
optional typed disposition defaulting to `error`, validated at load,
enforced pre-dispatch. Airflow's `max_map_length` fail-fast is the
external precedent for fail-by-default.

Two distinct configuration paths (judgement R-2 — they resolve
independently):

- **cap:** node `max_items` > graph `config.max_map_items` >
  `DEFAULT_MAX_MAP_ITEMS` (100)
- **policy:** node `on_overflow` > graph `defaults.on_overflow` >
  `"error"`

1. **Schema** — add `on_overflow: Literal["error", "truncate"] | None`
   to `NodeConfig` (`yamlgraph/models/node_schema.py`) and load-time
   Pydantic validation for `defaults.on_overflow` in `GraphConfigSchema`
   (`yamlgraph/models/graph_schema.py` — `defaults` is currently an
   untyped dict whose only value validator covers `thinking_budget`).
   Invalid policy VALUES fail `load_graph_config`; the overflow
   COMPARISON itself is necessarily runtime — `over` resolves from
   state (the research record's load-time claim is corrected per R-1).
2. **Propagation repair (R-3)** — `GraphConfig.max_map_items` is parsed
   (`graph_loader.py:83-85`) but map compilation receives only
   `config.defaults` (`node_compiler.py:173-181`), so the documented
   graph-level cap NEVER reaches `map_edge` today. Pass the
   authoritative graph cap and graph policy into `compile_map_node`
   explicitly; witness must load+compile real YAML with
   `config.max_map_items`, not inject a defaults dict.
3. **Enforcement** — in `map_edge`, when `len(items) > max_items`:
   - `error` (default): raise `ValueError` before constructing any
     `Send`; message carries node name, observed count, configured cap.
   - `truncate`: retain exactly `items[:max_items]` in order, emit one
     WARNING with node name, observed count, cap, proceed.
4. **Docs** — `reference/graph-yaml.md` map section: both paths,
   resolution order, fail-by-default, explicit sampling.

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

Superseded by the judgement's revised criteria (R-4): the frozen
contract is AC-01–AC-14 and gates C-1–C-8 in
`FR-939-map-overflow-policy.judgement.md`. Highlights: `ValueError`
pre-`Send` with node/count/cap as asserted values; policy precedence
witnessed in both directions; invalid values rejected at both schema
levels; end-to-end YAML witness for `config.max_map_items` propagation;
`test_fr027_execution_safety.py` re-pinned to the new contract plus
focused `test_fr939_map_overflow_policy.py`; one new CAP-11 REQ with
`@pytest.mark.req` markers; RED/GREEN separate commits; focused command
`pytest tests/unit/test_fr027_execution_safety.py
tests/unit/test_fr939_map_overflow_policy.py
tests/unit/test_graph_schema.py -q --no-cov`.

## Alternatives Considered

See the research record. Rejected: mandatory field with no default
(subtractionist) — forces a migration edit on every existing map graph
while default `error` already delivers the safety; log-only warning
hardening — leaves the contract out-of-band; deleting the cap — removes
the cost guard FR-027 correctly installed.

## Implementation Record (2026-09-26)

Commits: `71e27513` RED (28 failed / 78 passed on unchanged code, every
failure a missing schema field or `DID NOT RAISE`), `abc27b50` GREEN.

| AC | Evidence |
|----|----------|
| AC-01 | Research record (pre-existing, five classes, `is_this_a_graph`). |
| AC-02 | `NodeConfig.on_overflow: Literal["error","truncate"] \| None`; `GraphConfigSchema.validate_defaults_on_overflow`. `test_ac02_*` load real YAML; `"warn"`, `"ERROR"`, `""`, `1`, `True`, `["error"]` rejected at both levels. |
| AC-03 | `test_ac03_*`: implicit `error`, defaults `truncate`, node overrides default in both directions. |
| AC-04 | `node_compiler._compile_map_node` passes `GraphConfig.max_map_items` as `graph_max_items`; `test_ac04_config_max_map_items_*` go through `load_graph_config` + `compile_graph`; node cap overrides graph cap; built-in 100. |
| AC-05 | `resolve_items` raises under `error`; the FR-1073 dispatch node calls it before the router builds any `Send`. `test_ac05_overflow_raises_before_any_sub_node_runs` counts zero sub-node calls end to end. |
| AC-06 | Message `Map node '<name>': <n> items exceed max_items=<cap> (on_overflow: error)…`; asserted as values. |
| AC-07 | Exact prefix at the Send level and end to end (3 sub-node calls); exactly one WARNING (dispatch node only; the router resolves with `warn=False`). |
| AC-08 | 0, 1 and cap-sized inputs × {implicit, error, truncate}: one Send per item in order, no warning. |
| AC-09 | FR-027 `TestMapMaxItems`: truncation declared explicitly; `test_defaults_max_map_items_is_not_a_cap_seam` pins the retired seam; `test_map_edge_default_100_cap[None]` pins fail-by-default. |
| AC-10 | REQ-YG-699 in CAP-11; `req_coverage.py --strict` 424/424. |
| AC-11 | Separate RED and GREEN commits (above). |
| AC-12 | Focused command: 106 passed, 2 skipped. |
| AC-13 | `reference/graph-yaml.md` (config table, map table, Overflow paragraph with sampling example); changelog `fr-939-map-overflow-policy.md`; diary `diary-2026-09-26-reflection-fr-939-the-inert-cap.md`. |
| AC-14 | Diff limited to the frozen surfaces plus `vulture_whitelist.py` (framework-invoked validator, sibling convention) and `docs/confessions.md` (hook-regenerated line anchor). |

**Decisions.**
- The graph policy is passed explicitly as `graph_on_overflow`
  (from `GraphConfig.defaults`), matching the judgement's "pass the cap
  and policy explicitly"; `compile_map_node` no longer reads cap from
  `defaults`.
- `NodeConfig.on_overflow` is a one-line field: `node_schema.py` sits
  against the FR-716 `< 400` split gate (now 398).
- `node_compiler.py` grew 2 lines (448 / 450 cap).

**Deviations.**
- The RED end-to-end truncate witness compared raw collected values;
  FR-1073 collects `{_map_index, value}` records, so GREEN corrected the
  assertion (order by index, compare values). Contract unchanged.
- `yamlgraph/schemas/graph-v1.json` (hand-maintained IDE schema,
  `additionalProperties: true`) not updated — outside the frozen scope and
  it does not reject the new key.

**Behaviour change for existing graphs.** Seven demo graphs declare
`config.max_map_items` (50–1000). Before this change the value was dropped
and every map was capped at 100 with a log-only warning; now the declared
cap applies, and any list over it raises unless the graph opts into
`truncate`. Demo graphs were not edited (not authorized).

## Related

- `FR-936-map-node-hardening.md` (SPLIT parent) and its judgement (D-2)
- `027-execution-safety-guards.md` (superseded disposition)
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` (component D, first consumer)
- 2026-09-25: first in the order of `docs/issues-2026-09-24.md` §7 (fix F);
  required before any paid run of [FR-1065](FR-1065-resumable-map-investigation.md);
  [FR-1070](FR-1070-innovation-matrix-repair.md) depends on it.
