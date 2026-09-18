# Judgement: FR-1050 `loop_limits` must bind or fail compilation

**Prior art:** `FR-1050-loop-limits-bind-or-fail.md` — the FR this judgement
renders (its own subject, not a competing proposal).
`FR-677-verification-first-class-dsl.md` — the compile-time support-matrix
precedent this judgement holds the FR to, for guards rather than loop limits.
`027-execution-safety-guards.md` — the P0 whose partial delivery created the
inert entries; this judgement freezes the scope that finishes it.
`FR-706-race-timeout-loop-liveness.md` — the last change to the race counter,
which left it unread. None is a duplicate: no prior judgement freezes scope or
gates for loop-limit binding.

**Verdict:** APPROVED WITH REVISIONS — the invariant and standalone `race` fix are sound; authority activates only after R-1 through R-4 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1050-loop-limits-bind-or-fail.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `feature-requests/FR-172-loop-exit-target.md`; `feature-requests/FR-630-loop-exits-end-bug.md`; `feature-requests/FR-706-race-timeout-loop-liveness.md`; `feature-requests/REJECTED-fix-philosopher-copilot-nodes.md`; `yamlgraph/constants.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/pipeline_template.py`; `yamlgraph/interactive_tool.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/node_factory/router_race_node.py`; `yamlgraph/node_factory/control_nodes.py`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/node_factory/copilot_node.py`; `yamlgraph/tools/agent.py`; `yamlgraph/tools/nodes.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/utils/guard_runtime.py`; `yamlgraph/routing.py`; `yamlgraph/linter/checks.py`; `yamlgraph/linter/checks_semantic.py`; `examples/demos/multi-turn/graph.yaml`; `examples/demos/book-summary/graph.yaml`; `capabilities/CAP-17-execution-safety-guards.yaml`; `ARCHITECTURE.md`; `reference/development-operations.md`.

## What is sound

1. **Scope:** The FR targets one invariant: a declared graph-level `loop_limits` entry must either enforce a visit bound or stop compilation. Adding enforcement only to standalone `race` and rejecting unresolved semantics elsewhere is smaller and safer than inventing behavior for `interrupt`, `map`, or `subgraph` (FR lines 91-97, 138-157, 204-212).
2. **Consistency:** The summary, value statement, migration analysis, and deferred work consistently distinguish newly live `race` bounds from inert unsupported entries (FR lines 38-48, 191-202). The revisions below remove two implementation-level contradictions without changing that intent.
3. **Measurability:** The proposed behavior is observable through compilation errors, candidate-call counts, loop-state deltas, and compiled routing walks (FR lines 159-187). These are direct assertions rather than aspirational outcomes.
4. **Feasibility:** The existing guard support matrix establishes the compile-error pattern (`yamlgraph/compile/node_compiler.py:49-60,358-366`), while standalone `race` already maintains the counter immediately before candidate execution (`yamlgraph/node_factory/race_node.py:366-375`). The change is technically local once validation is placed before graph-shape transforms.
5. **Architecture alignment:** Compile-time rejection follows FR-677 and the repository law to normalize at the boundary. Existing W012 only checks key presence (`yamlgraph/linter/checks_semantic.py:299-320`), so moving truth to compilation correctly avoids an advisory-only fix.
6. **Single responsibility:** Runtime enforcement for standalone `race`, compile-time rejection for unsupported declarations, and migration of now-invalid examples all serve the same bind-or-fail contract. Interrupt semantics and direct-edge traversal are explicitly deferred (FR lines 138-157).
7. **Strategic classification:** **Framework primitive.** This tightens an existing execution-safety primitive used across at least nine cited graphs and affects every authored node type, rather than adding a one-off example convention (FR lines 79-97; `capabilities/CAP-17-execution-safety-guards.yaml:1-5,39-48`).
8. **Testability:** RED tests can be written for standalone `race`, each supported type, every rejected type, dangling keys, macro-node declarations, and loop-exit routing. The revised criteria below remove the circular and factually incorrect portions of the current test plan.

## Required revisions

### R-1: Validate the complete authored `loop_limits` map before expansion

Replace the node-by-node-only validation design with a boundary check that iterates every graph-level `loop_limits` entry against the **raw authored node map before `interactive_tool` and `pipeline` expansion**. It must reject:

- a key that names no authored node, closing the compile-time hole currently covered only by linter E008 (`yamlgraph/linter/checks_semantic.py:67-72`);
- every authored node type outside the supported set; and
- the expansion-only `interactive_tool` and `pipeline` types.

The current proposed check at `compile_node` cannot satisfy the FR's invariant for dangling keys because compilation iterates nodes, not limit entries (`yamlgraph/compile/node_compiler.py:299-330`). It also cannot see macro nodes because both transforms delete the authored node before compilation (`yamlgraph/compile/graph_loader.py:160-171`; `yamlgraph/interactive_tool.py:38-55,83-107`; `yamlgraph/compile/pipeline_template.py:90-107,126-130`). Fold `interactive_tool` and `pipeline` into the problem inventory, support classification, error tests, and migration statement. Preserve `interactive_tool.max_iterations` behavior; this FR governs graph-level `loop_limits`, not that macro's internal generated `loop_limit`.

### R-2: Remove the `router_race_node.py` implementation change

Rewrite Move 1 and AC-02 so only standalone `type: race` gains a new check. A router with `candidates` already executes the normal `llm`/`router` check before incrementing and before dispatching to `_execute_router_race` (`yamlgraph/node_factory/llm_nodes.py:303-309,337-342`). `_execute_router_race` receives the already incremented counter and contains no increment of its own (`yamlgraph/node_factory/router_race_node.py:33-40,102-105,129-132`). Adding the proposed second check there would test the incremented value and can suppress the Nth permitted execution. Retain a router-with-candidates regression test proving candidates are not fired after exhaustion, but explicitly authorize no production change in `router_race_node.py`.

### R-3: Replace the circular drift test with an exhaustive classification contract

Replace the claim that enforcement is "discovered from the code" and the one-node derivation in Move 3. Compilation with `loop_limits` is itself gated by the proposed support set, so it cannot independently discover support.

Define two disjoint explicit classifications whose union equals the complete `NodeType` universe (`yamlgraph/constants.py:10-27`): supported and unsupported. The test must fail when a new enum value is unclassified. Parameterize compile rejection over the unsupported set, including expansion-only types, and parameterize execution-at-limit over every supported runtime type. The supported behavioral test must assert `_loop_limit_reached`, unchanged `_loop_counts`, and zero underlying work/candidate calls. This makes either drift direction fail without pretending the maintained classification is inferred.

### R-4: Add repository-required traceability, documentation, and migration evidence

Replace AC-10's direct `CHANGELOG.md` update with a fragment under `changelog/unreleased/`; the CI contract requires a fragment and validates its requirement reference (`reference/development-operations.md:98-100`). Add a new requirement under existing `CAP-17`, regenerate/update `ARCHITECTURE.md`, tag every new test with that requirement, and run `python scripts/req_coverage.py --strict`; REQ-YG-057 currently promises only tool, python, and passthrough enforcement (`capabilities/CAP-17-execution-safety-guards.yaml:39-46`; `ARCHITECTURE.md:791-794`).

Document the supported/rejected node types in `reference/graph-yaml.md`. Because AC-07 materially changes two demo `graph.yaml` files, require the graph-authoring route and its `tmp/draft-authoring-report.md` witness, plus refreshed `demo-output.log` files for both changed demos; the demo gate requires output evidence for modified demo directories (`reference/development-operations.md:100-101`). Add the required `docs/diary/` Distill entry with a **Seed:** and retain the FR implementation log.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Pre-expansion validation of every graph-level `loop_limits` key and exhaustive node-type classification in `yamlgraph/compile/` plus the minimal shared constants needed by that boundary |
| D-2 | Standalone `race` pre-execution limit enforcement in `yamlgraph/node_factory/race_node.py` |
| D-3 | Focused RED/GREEN and regression coverage in a dedicated FR-1050 unit-test module, including supported, unsupported, dangling, macro-node, router-with-candidates, W012, and `loop_exits` cases |
| D-4 | Removal of the five inert entries from `examples/demos/multi-turn/graph.yaml` and `examples/demos/book-summary/graph.yaml`, with honest comments and refreshed demo evidence |
| D-5 | `reference/graph-yaml.md`, `capabilities/CAP-17-execution-safety-guards.yaml`, generated requirement documentation, changelog fragment, FR implementation log, and Distill diary entry |

Not authorized: runtime loop-limit semantics for `interrupt`, `map`, `subgraph`, `tool_call`, `agent`, `copilot`, `verify`, `interactive_tool`, or `pipeline`; changes to direct-edge loop-exit traversal; changes to W012 behavior; changes to `interactive_tool.max_iterations`; production changes in `router_race_node.py`; changes in the csap repository; or implementation of NC-522.

## Revised acceptance criteria

- [ ] AC-01: RED first: a compiled standalone `race` node with a graph-level limit is driven past the limit; on current main the candidate is called, and after the fix the candidate is not called.
- [ ] AC-02: Standalone `race` calls `check_loop_limit` before incrementing `_loop_counts`; exhaustion returns exactly `{"_loop_limit_reached": True, "current_step": <node>}`, leaves the counter unchanged, and fires no candidate.
- [ ] AC-03: A router with `candidates` retains its existing outer `llm`/`router` loop-limit behavior: exhaustion occurs before `_execute_router_race`, leaves the counter unchanged, and fires no candidate. `yamlgraph/node_factory/router_race_node.py` has no production change.
- [ ] AC-04: Before macro expansion, compilation iterates every graph-level `loop_limits` entry. A missing node key raises `GraphConfigError` naming the key; an unsupported node raises `GraphConfigError` naming the node, type, and sorted supported set.
- [ ] AC-05: Unsupported-type rejection is asserted per classification entry, including `interrupt`, `map`, `tool_call`, `agent`, `copilot`, `verify`, `subgraph`, `interactive_tool`, and `pipeline`.
- [ ] AC-06: `LOOP_LIMIT_SUPPORTED_TYPES` and `LOOP_LIMIT_UNSUPPORTED_TYPES` are disjoint and their union equals the complete `NodeType` enum. Adding a new node type without classification fails the test.
- [ ] AC-07: Each supported type (`llm`, `router`, `python`, `tool`, `passthrough`, `race`) compiles and is behaviorally exercised at exhaustion; each test asserts the limit flag, unchanged counter, and zero underlying work calls.
- [ ] AC-08: An exhausted standalone `race` reaches its declared `loop_exits` target through the existing routing seam in a compiled walk.
- [ ] AC-09: A cycle whose only declared bound is unsupported fails compilation; W012 is not modified and cannot provide false reassurance for that graph.
- [ ] AC-10: The five inert in-repo entries are removed from `examples/demos/multi-turn/graph.yaml` and `examples/demos/book-summary/graph.yaml` through the graph-authoring route. Each graph records that the removed bound was never live, both demos have refreshed `demo-output.log`, and `tmp/draft-authoring-report.md` records lint/smoke outcomes honestly.
- [ ] AC-11: `reference/graph-yaml.md` documents the supported and rejected types. `CAP-17` gains a requirement for bind-or-fail loop limits, generated requirement documentation is updated, all new tests carry its `@pytest.mark.req(...)`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, `ruff check yamlgraph/`, and validation of every graph under `graphs/`, `examples/`, and `projects/` pass.
- [ ] AC-13: A `changelog/unreleased/` fragment references the new requirement; the FR records implementation status, decisions, and deviations; and a `docs/diary/` Distill entry includes a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 and the revised acceptance criteria into `feature-requests/FR-1050-loop-limits-bind-or-fail.md` before writing production code. | GATE |
| C-2 | Preserve RED→GREEN history: commit the failing standalone-race witness before the implementation commit. | GATE |
| C-3 | Validate authored `loop_limits` before `interactive_tool` and `pipeline` erase their source node identities; do not substitute a compiler-loop check that misses dangling or macro-node keys. | GATE |
| C-4 | Do not add a second loop-limit check inside `_execute_router_race`; its caller already checks and increments. | GATE |
| C-5 | Route both demo graph migrations through `scripts/author.sh` and judge completion by `tmp/draft-authoring-report.md`, not adapter exit status. | GATE |
| C-6 | Keep all deferred runtime semantics and cross-repository csap changes outside this implementation. | GATE |

Authority granted: after the FR incorporates R-1 through R-4, implement pre-expansion bind-or-fail validation, standalone `race` enforcement, the two in-repo migrations, and only the tests and documentation enumerated above.
