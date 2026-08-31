# Judgement: FR-944 Map-to-map chaining must deliver true per-branch `_map_index`

**Prior art:** [FR-944-map-to-map-index-attribution.md](FR-944-map-to-map-index-attribution.md) — the FR under judgement (self-reference from the retrieval's noun match); all substantive prior art (FR-467, FR-718, FR-936, FR-943) is dispositioned in the FR's own Prior art line and in "What is sound" below.

**Verdict:** APPROVED WITH REVISIONS - the defect and compiler-boundary correction are sound, but authority activates only after R-1-R-4 make the barrier choice evidence-based, the execution path directly testable, and the requirement and delivery surfaces exact.

**Reviewed against:** `feature-requests/FR-944-map-to-map-index-attribution.md`; `feature-requests/FR-944.research.md`; `feature-requests/FR-467-conditional-edge-to-map-node.md`; `feature-requests/FR-718-edge-compiler-decomposition.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-943-census-row-failure-containment.judgement.md`; `yamlgraph/compile/edge_compiler.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/models/state_builder.py`; `tests/unit/test_fr718_edge_shapes.py`; `tests/unit/test_compile_graph_map.py`; `tests/unit/test_map_node.py`; `tests/unit/test_map_flatten_output.py`; `tests/unit/test_map_node_timeout.py`; `tests/unit/test_state_builder.py`; `tests/unit/test_fr943_census_row_failure_containment.py`; `capabilities/CAP-11-subgraph-map.yaml`; `capabilities/CAP-64-concurrency-safety-map.yaml`; `capabilities/CAP-210-edge-shape-classification.yaml`; `reference/map-nodes.md`; `reference/graph-yaml.md`; `reference/patterns.md`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repository index/status for the FR, research record, and cited `tmp/`/`logs/` evidence paths.

## What is sound

The defect is concrete and located at one compiler seam. `MAP_TO_MAP` currently registers the downstream map's `Send` router directly on the upstream map sub-node, while `map_edge` assigns `_map_index` by locally enumerating the resolved list (`yamlgraph/compile/edge_compiler.py:221-224`; `yamlgraph/compile/map_compiler.py:363-366`). `wrap_for_reducer` then copies that index into both successful and failed branch results, and `sorted_add` relies on it for order (`yamlgraph/compile/map_compiler.py:116-190`; `yamlgraph/models/state_builder.py:37-56`). The stated consequences therefore follow from the cited mechanism rather than from an aggregate symptom.

The proposed boundary is also appropriately small. Existing map-to-node compilation already places a static edge after the map sub-node, and ordinary node-to-map compilation attaches the downstream `Send` router to that node (`yamlgraph/compile/edge_compiler.py:227-237`). A synthetic pass-through between those two existing forms is a plausible way to make `map1 -> map2` follow the already-supported `map1 -> node -> map2` path without changing `map_edge`, reducers, or the FR-943 consumer. Prior art is correctly separated: FR-467 explicitly left map-source conditional behavior outside its scope, FR-718 preserved the classified shape, and FR-943 forbids changing core map machinery inside its demo-scoped authority (`feature-requests/FR-467-conditional-edge-to-map-node.md:94-109,221-229`; `feature-requests/FR-718-edge-compiler-decomposition.md:24-47`; `feature-requests/FR-943-census-row-failure-containment.md:153-175`).

| Criterion | Finding |
|---|---|
| Scope | One `MAP_TO_MAP` compiler handler plus direct witnesses is the smallest complete correction. The non-goals correctly exclude `map_compiler.py`, `sorted_add`, single-map behavior, and the census reducer (`feature-requests/FR-944-map-to-map-index-attribution.md:47-67`). |
| Consistency | The ideal and proposed call-site fix agree, but the FR incorrectly says the data-process and YAMLGraph-native research entries support a barrier. They prescribe index threading through `map_edge`/`sorted_add`, not a join (`feature-requests/FR-944-map-to-map-index-attribution.md:53-65`; `feature-requests/FR-944.research.md:17-18`). Fold R-1. |
| Measurability | Distinct indexes, error attribution, and cardinality are assertable. AC-03 does not specify the independent-list setup needed to expose N x M duplication, AC-04 names a nonexistent `test_fr936*` suite and an open-ended "map compiler tests" set, and AC-05 points only to ignored `tmp/` evidence with no durable command (`feature-requests/FR-944-map-to-map-index-attribution.md:69-76,87-88`). Fold R-2 and R-3. |
| Feasibility | The existing static map-to-node edge and node-to-map conditional edge make the join construction workable in the current architecture, but neither the research record nor an acceptance criterion proves the crucial claim that the generated join runs once on merged state (`yamlgraph/compile/edge_compiler.py:221-237`). Fold R-1 and R-2 before relying on that claim. |
| Architecture alignment | The fix stays in the classified per-shape compiler and reuses existing edge forms instead of adding a node type, config flag, reducer policy, or downstream workaround (`yamlgraph/compile/edge_compiler.py:23-31,221-253`). |
| Single responsibility | Correcting the firing boundary fixes index identity, deterministic reducer ordering, error attribution, and independent-list cardinality as consequences of one map-to-map scheduling defect. No split is required (`feature-requests/FR-944-map-to-map-index-attribution.md:31-45`). |
| Strategic classification | **Framework primitive correction**: this repairs the existing core `MAP_TO_MAP` abstraction and its general ordering, attribution, and fan-out semantics rather than adding consumer-specific behavior (`reference/map-nodes.md:3-12,104-108,381-400,545-547`). |
| Testability | A failing runtime witness can be written from the current criteria, and the wrapper's exact failure envelope is already defined. Complete enforcement tests still require a frozen path assertion, explicit N/M fixtures, and a named requirement owner (`yamlgraph/compile/map_compiler.py:123-190`; `tests/unit/test_fr718_edge_shapes.py:28-65`). Fold R-2-R-4. |

## Required revisions

### R-1: Reconcile and commit the research evidence

Replace the unsupported claim that the barrier join is "the yamlgraph-native-planner and data-process-planner direction." Amend `feature-requests/FR-944.research.md` with a distinct **barrier join** solution class that records:

1. the exact current and candidate scheduling paths;
2. a bounded, LLM-free direct runtime probe demonstrating that a static upstream-sub-node edge reaches one downstream node invocation with the fully reduced state;
3. the observed current and candidate `_map_index` sequences;
4. why this option is preferred over the record's index-threading, deletion, and Airflow-style metadata alternatives; and
5. one unambiguous `is_this_a_graph` answer for the research task.

Embed the probe command/setup and salient output in the committed research record or promote it to a committed test fixture. Do not cite `tmp/map-index-repro/`, `tmp/census-debug-findings.json`, or `logs/fr943-census-rerun.log` as authoritative evidence: all three paths are ignored, and the FR and research files themselves are presently untracked. The revised FR and substantive research record must be committed with the reviewed judgement before authority can activate (`.github/skills/judge-fr/doctrine.md:16-22,118-130`).

### R-2: Freeze the execution-path contract

Replace AC-01-AC-03 with an exact runtime and topology matrix in a new `tests/unit/test_fr944_map_to_map_index.py`:

- **Collected-list chain:** first map processes N=3 inputs; second map reads the first map's collected output; assert the second fan-out occurs once, produces exactly three results, and yields ordered `_map_index == [0, 1, 2]` with values paired to the corresponding inputs.
- **Independent-list chain:** first map processes N=3 inputs; second map reads an independent M=2 list from parent state; assert exactly two downstream results and indexes `[0, 1]`, not N x M results.
- **Error attribution:** the second map raises only for item index 2; assert its collected failure entry has `_map_index == 2`, the expected `_error` text and `_error_type`, and unchanged successful peers.
- **Path witness:** assert compilation routes the upstream map sub-node to the generated join and attaches the downstream conditional `Send` router to the join, with no downstream-map conditional router attached directly to the upstream sub-node.

Freeze the production behavior as one synthetic pass-through join per map-to-map edge, returning `{}` without mutating state. Its downstream map router must execute once after upstream fan-in on merged state. Keep `EdgeShape.MAP_TO_MAP` classification unchanged. If the deterministic generated join name collides with an existing graph node, compilation must fail explicitly naming the map-to-map edge and conflicting synthetic name; add a direct witness for that failure rather than allowing an opaque framework exception.

### R-3: Replace transient and open-ended acceptance gates

Delete the ignored `tmp/map-index-repro` acceptance criterion. The committed runtime tests from R-2 are the durable LLM-free reproduction. Replace the open-ended regression criterion with this exact command:

```bash
pytest \
  tests/unit/test_fr944_map_to_map_index.py \
  tests/unit/test_fr718_edge_shapes.py \
  tests/unit/test_compile_graph_map.py \
  tests/unit/test_map_node.py \
  tests/unit/test_map_flatten_output.py \
  tests/unit/test_map_node_timeout.py \
  tests/unit/test_state_builder.py \
  tests/unit/test_fr943_census_row_failure_containment.py \
  -q --no-cov
```

The new RED runtime witness must be committed before production implementation and must fail because the downstream indexes/path are wrong, not because a fixture, tool, or import is absent. No paid corpus-census rerun is required.

### R-4: Name the requirement and complete the delivery surface

Assign the new witnesses to `REQ-YG-568`, which already owns the `MAP_TO_MAP` edge shape and its compiler in CAP-210. Amend `capabilities/CAP-210-edge-shape-classification.yaml` so REQ-YG-568 additionally requires map-to-map compilation to cross one post-fan-in pass-through before downstream `Send` expansion, preserving one fan-out, true zero-based downstream indexes, deterministic reducer order, and explicit synthetic-name collision failure. Add the new test module to the requirement's modules and regenerate `ARCHITECTURE.md`.

Update `reference/map-nodes.md` with the same user-visible chaining semantics. Add a `fix` changelog fragment carrying `req: REQ-YG-568`, update the FR with implementation status and decisions, and add the required diary reflection. Run `python scripts/req_coverage.py --strict`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/compile/edge_compiler.py` - `MAP_TO_MAP` post-fan-in join compilation and explicit synthetic-name collision error only |
| D-2 | `tests/unit/test_fr944_map_to_map_index.py` - RED/GREEN runtime, path, cardinality, attribution, and collision witnesses |
| D-3 | `capabilities/CAP-210-edge-shape-classification.yaml` and regenerated `ARCHITECTURE.md` - REQ-YG-568 contract and traceability |
| D-4 | `reference/map-nodes.md` - documented map-to-map barrier semantics |
| D-5 | Revised FR and research record, REQ-YG-568 `fix` changelog fragment, implementation record, and diary reflection |

Not authorized: changes to `yamlgraph/compile/map_compiler.py`, `yamlgraph/models/state_builder.py`, `EdgeShape` membership or classification order, map YAML schema, a new node type or public option, FR-943 census code/prompts/contracts, existing graph artifacts, retry/timeout behavior, hooks, CI, judge/review doctrine, or any paid live LLM run.

## Revised acceptance criteria

- [ ] AC-01: The committed research record contains the barrier-join solution class, bounded direct runtime probe and output, contrary-alternative dispositions, and one explicit `is_this_a_graph` answer; no ignored `tmp/` or `logs/` path is treated as authoritative evidence.
- [ ] AC-02: A committed RED test in `tests/unit/test_fr944_map_to_map_index.py` fails on current behavior because the downstream map path/index contract is violated, before any production change is committed.
- [ ] AC-03: For an N=3 chain where map 2 consumes map 1's collected output, map 2 fans out once and returns exactly three ordered results with indexes `[0, 1, 2]` paired to the correct values.
- [ ] AC-04: For an N=3 upstream map and an independent M=2 downstream `over` list, map 2 returns exactly two results with indexes `[0, 1]`, proving no per-upstream-branch N x M fan-out.
- [ ] AC-05: A map-2 exception at downstream index 2 produces the existing `wrap_for_reducer` error envelope with `_map_index == 2`, exact error text/type, and unchanged successful peers.
- [ ] AC-06: The compiled path is upstream sub-node -> generated pass-through join -> downstream conditional `Send` router; no downstream-map conditional router remains directly attached to the upstream sub-node, and the join returns `{}` without state mutation.
- [ ] AC-07: A generated join-name collision fails compilation explicitly naming both the map-to-map edge and conflicting synthetic node name.
- [ ] AC-08: `EdgeShape.MAP_TO_MAP`, `map_edge`, `wrap_for_reducer`, `sorted_add`, and all single-map behavior remain unchanged; the exact R-3 pytest command passes.
- [ ] AC-09: CAP-210 and regenerated `ARCHITECTURE.md` assign the frozen map-to-map behavior and new test module to REQ-YG-568; every new test carries `@pytest.mark.req("REQ-YG-568")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: `reference/map-nodes.md`, the REQ-YG-568 `fix` changelog fragment, FR implementation record, committed research evidence, and diary reflection are delivered.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review must accept this advisory draft, and R-1-R-4 must be folded into the committed FR/research before implementation authority exists. | GATE |
| C-2 | Commit the RED runtime witness before changing production code; a fixture/import failure does not satisfy RED. | GATE |
| C-3 | The downstream map router must fire once on merged post-fan-in state; do not substitute index inheritance or a consumer-specific workaround. | GATE |
| C-4 | Do not modify `map_compiler.py`, `state_builder.py`, classification semantics, census behavior, graph artifacts, or any other excluded surface. | GATE |
| C-5 | Do not use ignored runtime files as acceptance evidence; executable witnesses and research evidence must be committed and reproducible. | GATE |
| C-6 | Preserve REQ-YG-568 traceability and pass both the exact focused regression command and strict requirement coverage. | GATE |

Authority granted: after human acceptance and mechanical folding of R-1-R-4, implementation is authorized only for the frozen post-fan-in `MAP_TO_MAP` join, its explicit collision failure, direct witnesses, REQ-YG-568 traceability, map-node documentation, and required changelog/FR/diary artifacts.
