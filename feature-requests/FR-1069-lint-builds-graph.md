# Feature Request: `graph lint` builds the graph, not only its config

**Priority:** MEDIUM
**Type:** Bug / Linter completeness
**Status:** SPLIT — [judgement](FR-1069-lint-builds-graph.judgement.md); lint trust boundary and demo repair require separately judged FRs. No implementation authority.
**Human decision (2026-09-25, operator; judgement R-2 / AC-02):** compilation is opt-in via `graph lint --build` on trusted graphs; plain `lint` never imports graph-declared Python. The promise becomes "`lint --build` passes implies the graph builds".
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** `yamlgraph graph lint
examples/demos/safety-guards/graph.yaml`, which reports no issues today while
the graph cannot be compiled (`ValueError: Edge 'review' -> ['revise',
'expand'] has a condition on a parallel fan-out list without type:
conditional`, plan appendix).
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D10.
The FR-890 research route was not run.
**Prior art:** [FR-842-lint-compile-validation-parity.md](FR-842-lint-compile-validation-parity.md)
(Enforced) — made lint run `validate_config` (E000). Edge-shape errors raised
later, inside `compile_graph` / `StateGraph.compile()`, are still invisible to
lint. This FR extends FR-842's parity from "config validates" to "graph
builds".

## Summary

Add a final E-level lint check that builds the graph (`compile_graph(config)`
then `.compile()`) and reports any exception as a lint error; add a
parametrized test that builds every tracked graph in the repository.

## Value Statement

A graph that lint passes can be run; broken demos are found in CI, not by the
next user.

## Problem

`lint_graph` stops at config validation. `compile_graph` raises for edge
shapes that `validate_config` accepts, and nothing in CI builds every graph.

## Ideal Result

`graph lint` passes ⇒ `graph run` reaches its first node.

## Proposed Solution

- New check `E0xx` (next free code) at the end of `lint_graph`: build and
  compile; on exception, one error with the exception text. Skipped when an
  earlier E-level error already failed (the build would fail for the same
  reason).
- `tests/unit/test_all_graphs_compile.py`: parametrized over `git ls-files`
  graph YAMLs (the set `graph list` uses), each built and compiled.
- **Code execution at lint time.** `compile_graph` imports graph-declared
  Python modules (`graph_loader.py#L296`, `map_compiler.py#L288`,
  `tool_builders.py#L78` via `load_python_function`), so their module-level
  code runs. Lint does not import them today. The check is on by default in
  the repository test and behind `--build` on the CLI, pending the judge
  question below.
- Repair `examples/demos/safety-guards` via `scripts/author.sh`: two
  conditional edges (review → revise, review → expand), not a fan-out, because
  `expand` would rerun on every revise pass. Any other graph the new test
  finds broken is repaired the same way or listed as a defect in this FR.

## Acceptance Criteria

- [ ] RED: `graph lint examples/demos/safety-guards/graph.yaml --build` reports the edge error.
- [ ] RED: the parametrized test fails on safety-guards before the repair; green after.
- [ ] The census of build failures over all tracked graphs is recorded in this FR (count and names).
- [ ] Build errors keep the exception text verbatim (FR-842 message-parity precedent).

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Parametrized test only, no lint check | Rejected: user graphs outside the repo still pass lint. |
| Re-implement the edge-shape checks in the linter | Rejected: a second grammar drifts; FR-842's lesson. |
| Build without importing Python modules (stub callables) | Open (judge question): avoids code execution but misses import errors. |

### Questions for the judge

- Should lint build by default (executing graph-declared Python) or only with
  `--build`? Recommended: `--build` opt-in on the CLI, always on in the repo
  test. CLAUDE.md: "only YAML config is trusted".

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 G
- Extends: [FR-842](FR-842-lint-compile-validation-parity.md)
