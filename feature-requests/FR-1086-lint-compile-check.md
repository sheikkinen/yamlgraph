# Feature Request: `graph lint --build` — opt-in check that the graph compiles

**Priority:** MEDIUM
**Type:** Bug / Linter completeness
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1086-lint-compile-check.judgement.md)); R-1–R-4 folded 2026-09-26. Authority active (2026-09-26): human review recorded — operator instruction 'proceed with all fr changes' (2026-09-26). Not yet implemented. The census baseline still needs its own human approval before it becomes enforcement (judgement C-3).
**Human decision (2026-09-25, operator):** suggested default accepted — building is opt-in (`graph lint --build`); plain `graph lint` executes no graph-declared Python.
**Effort:** 1 day
**Requested:** 2026-09-25
**First consumer / first event:** `yamlgraph graph lint --build
examples/demos/safety-guards/graph.yaml`. Today plain `graph lint` on that
file reports 0 errors and 1 warning (W803), run 2026-09-25 in this worktree.
The same graph cannot be compiled: its edge at
`examples/demos/safety-guards/graph.yaml#L81-L83` puts a condition on a
fan-out list, which `yamlgraph/compile/edge_compiler.py#L35-L43` rejects with
a `ValueError`.
**Research:** FR-890 research route not run. Operator decision 2026-09-25
for the FR-1069 refile: "refile. skip research — document as skipped". The
substitute is the in-body Alternatives Considered section below (six solution
classes, one chosen, one preserved dissent, `is_this_a_graph` answered), in
the form FR-1079 and FR-1076 use, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D10.
**Prior art:**
[FR-1069](FR-1069-lint-builds-graph.md) (SPLIT). This is its compile-check
half; the demo repair is [FR-1087](FR-1087-safety-guards-demo-repair.md).
Judgement R-1: this FR holds only the linter/CLI check and the compile
parity test. R-2: the trust boundary is an explicit human decision below, and
the promise is stated for `lint --build`, not for plain `lint`. R-3: six
solution classes, a dissent, `is_this_a_graph`, and a defined policy for
Python imports, optional dependencies and untracked graphs in the repo-wide
test. FR-1069's own text gains no authority here.
[FR-842](FR-842-lint-compile-validation-parity.md) (Enforced). It made lint
run `validate_config` and report rejections as E000
(`yamlgraph/linter/graph_linter.py#L81-L107`). Errors raised later, inside
`compile_graph`, are still invisible to lint. This FR extends FR-842's
message-parity rule (exception text kept verbatim) to the build step.
[FR-718](FR-718-edge-compiler-decomposition.md) (Completed). It turned a
condition on a fan-out list from "silently dropped" into a raise. That is
the error the first consumer hits.

## Summary

Add a `--build` flag to `graph lint`. With it, lint also loads the graph
config, runs `compile_graph`, and runs LangGraph's `compile` with no
checkpointer. Any exception from that build becomes one `E015` lint error
with the exception text unchanged. `--tool SLOT=MANIFEST` supplies tool-slot
bindings for the build. Without `--build`, lint behaves exactly as today and
imports no graph-declared Python. Add a repository test that records the
build outcome of every tracked graph.

## Value Statement

A graph author or CI job that trusts a graph can learn, without calling any
LLM, whether the graph's structure compiles. Broken tracked graphs are found
by CI, not by the next user.

## Problem

- Plain lint runs `validate_config` first
  (`yamlgraph/linter/graph_linter.py#L128-L130`), then only static checks.
  No linter module imports Python or calls `compile_graph` (no
  `importlib`, `load_python_function` or `compile_graph` in
  `yamlgraph/linter/`, searched 2026-09-25).
- `graph run --gate` lints first (`_run_lint_gate`,
  `yamlgraph/cli/graph_commands.py#L62-L100`, called at `#L128-L130`).
  `graph run` then parses tool bindings, loads with provider/model
  overrides, builds the configured checkpointer and compiles with it
  (`yamlgraph/cli/graph_commands.py#L156-L175`). Errors raised by
  `compile_graph` therefore reach the user only at run time.
- Building imports graph-declared Python. `compile_graph` loads Python tools
  through `load_python_function` (`yamlgraph/compile/graph_loader.py#L294-L302`),
  as do map sub-nodes (`yamlgraph/compile/map_compiler.py#L276`) and tool
  builders (`yamlgraph/tools/tool_builders.py#L78`). That function runs
  `spec.loader.exec_module` or `importlib.import_module`
  (`yamlgraph/tools/python_tool.py#L123-L134`), so module-level code
  executes. Output-model class paths are imported too
  (`yamlgraph/node_factory/base.py#L40`). CLAUDE.md: "only YAML config is
  trusted".
- No test builds every tracked graph. The only repo-wide graph tests found
  lint generated graphs (`tests/unit/test_fr792_investigation_scaffold.py#L147`)
  or list `graphs/` (`tests/unit/test_fr1014_authoring_proof_dir_graphs.py#L130`).
  `git grep -l '^nodes:'` over tracked `examples/` and `graphs/` YAML,
  excluding `prompts/`, finds 202 files (2026-09-25). That text match is an
  estimate only; the census corpus is defined in Proposed Solution 4.
- Some tracked graphs declare tool slots that must be bound at invocation
  time, so they cannot build without bindings: `corpus_census`
  (`examples/demos/corpus_census/graph.yaml#L46`, `#L50`), `repo_census`
  (`examples/demos/repo_census/graph.yaml#L47`, `#L51`),
  `person_profile_census`
  (`examples/demos/person_profile_census/graph.yaml#L49`, `#L53`, `#L58`),
  `pattern_model_census`
  (`examples/demos/pattern_model_census/graph.yaml#L36`, `#L40`).

## Human decisions

- **2026-09-25, operator — trust boundary:** building is opt-in
  (`graph lint --build`) on graphs the user trusts; plain `graph lint` never
  imports or executes graph-declared Python. Reasons: (1) lint is run on
  graphs a user has not decided to run — PR review, CI over contributed
  graphs, the `graph run --gate` check — and plain lint executes no Python
  today; (2) CLAUDE.md states only YAML config is trusted; (3) the operator
  chose opt-in in the [FR-1069](FR-1069-lint-builds-graph.md) header on
  2026-09-25, and the judgement confirmed it carries over.
- **2026-09-26, operator — judgement review:** reviewed the advisory
  judgement and instructed "proceed with all fr changes". R-1–R-4 are folded
  as written and authority is active under the frozen scope below.
- **Still required (judgement C-3):** human approval of the initial census
  baseline — counts and every `broken` and `needs` row — before the census
  test becomes repository enforcement.

## Ideal Result

`graph lint --build` succeeds when `load_graph_config` with the supplied
compilation inputs, `compile_graph`, and `StateGraph.compile(checkpointer=None)`
succeed. It does not construct the configured checkpointer, execute a node,
or call an LLM. Plain `graph lint` keeps its current promise and never runs
graph-declared Python. Every tracked graph has a recorded, fingerprinted
build outcome, and CI fails when an outcome changes.

## Proposed Solution

1. **Build check.** New `yamlgraph/linter/build_check.py` runs
   `load_graph_config(path, tool_bindings=...)`, `compile_graph(config)` and
   `StateGraph.compile(checkpointer=None)`, so lint never opens a
   checkpointer backend. Any exception becomes one error-level issue with
   code `E015` (E000–E014 are taken) and `message == str(exc)`.
2. **Flag and API.** `lint_graph(..., build: bool = False)` is the API
   default; `--build` is the only switch that enables the build. The build
   runs last. If an earlier E000 is present, it is skipped entirely: no tool
   binding, no graph-declared Python import, no compiler call. `graph lint`
   gains `--build` next to `--json` (`yamlgraph/cli/__init__.py#L194-L205`),
   threaded through `cmd_graph_lint` (`yamlgraph/cli/graph_validate.py#L233`).
   The `graph run` lint gate is unchanged.
3. **Tool bindings.** `graph lint --build` accepts repeatable
   `--tool SLOT=MANIFEST`, parsed with the existing `parse_tool_bindings`
   (`yamlgraph/tools/tool_slots.py#L31`) and passed to `load_graph_config`.
   `--tool` without `--build` is rejected before any graph Python is
   imported, so plain lint's contract and output stay unchanged.
   Provider and model overrides are execution choices and are outside this
   structural build check; no such flags are added.
4. **Build census.** Census file `tests/fixtures/graph_build_census.yaml`,
   test `tests/unit/test_all_graphs_build.py`. The corpus is git-tracked YAML
   under `examples/`, `graphs/` and `.chaplain/graphs/` whose parsed
   top-level `nodes` value is a mapping, excluding any path under a
   `prompts/` directory. Each row has a path, an outcome, and optional
   compilation inputs:
   - `builds`, optionally with tracked `bindings` for declared tool slots;
   - `broken`, with an owning `FR-NNNN`, the exception class, and the exact
     message or an explicitly justified stable message prefix;
   - `needs`, with one named `pyproject.toml` extra and the expected
     missing-dependency exception fingerprint.

   The test runs the build check itself (not the aggregate exit status of
   `graph lint --build`) for each graph in a fresh subprocess with a fixed
   timeout documented in the census file. Subprocesses isolate imported
   modules between graphs; they are not a sandbox. Unrelated static lint
   errors never turn a compiling graph into a failure. A `broken` row fails
   if its exception fingerprint changes, even when the graph stays broken.
   A `needs` row may skip only when the named extra's requirements are
   absent, and must build when they are installed. Missing, duplicate,
   stale and untracked rows, missing binding manifests, timeouts, and
   outcome or fingerprint drift all fail the test.
5. **Docs.** `reference/graph-yaml.md` or the canonical linter reference
   states that `--build` imports trusted graph Python, uses the supplied
   tool bindings, compiles with `checkpointer=None`, and neither executes
   nodes nor guarantees that the configured checkpointer initializes.
6. **Plain-lint baseline.** Before any production code changes, commit
   exact stdout, stderr, exit code and `LintResult` expectations for fixed
   clean, warning-only and E000 fixtures; AC-03 tests against them.
7. **Implementation record.** This FR records the census command, counts
   per outcome, every non-`builds` row, the targeted tests, requirement
   coverage, and the full-suite result. It claims no configured-checkpointer
   or execution parity.

## Acceptance Criteria

- [ ] AC-01 (RED): `graph lint --build examples/demos/safety-guards/graph.yaml`
  exits 1 and reports exactly one error-level `E015` whose message equals the
  `ValueError` text from `yamlgraph/compile/edge_compiler.py#L38-L43`;
  unrelated warnings may also be present.
- [ ] AC-02: an import-sentinel fixture proves plain `graph lint` leaves the
  sentinel absent and `graph lint --build` creates it without executing a
  graph node.
- [ ] AC-03: committed clean, warning-only, and E000 fixtures preserve their
  frozen plain-lint stdout, stderr, exit code, and `LintResult`; no fixture
  produces E015 without `build=True`.
- [ ] AC-04: `--build` on an E000 graph reports E000 only and performs no
  loader binding, graph-declared Python import, compiler call, or LangGraph
  compile.
- [ ] AC-05: a slot fixture fails closed without a binding and builds with
  `graph lint --build --tool SLOT=MANIFEST`; `--tool` without `--build` is
  rejected without importing graph Python.
- [ ] AC-06: the census parser covers exactly the tracked top-level graph
  corpus, rejects missing/duplicate/stale/untracked rows, and the FR records
  counts plus every `broken` and `needs` row.
- [ ] AC-07: the census test runs each graph in a bounded fresh subprocess
  and fails on outcome, exception-class, message-fingerprint, timeout, or
  binding-manifest drift.
- [ ] AC-08: a `needs` fixture skips only when its named `pyproject.toml`
  extra is unavailable and must build when that extra is installed.
- [ ] AC-09: a graph with an unrelated static lint error but a successful
  build is classified `builds`; census classification does not use aggregate
  lint exit status.
- [ ] AC-10: human and `--json` modes expose E015 through the existing lint
  issue shape, preserve `str(exc)` unchanged, and exit nonzero on the error.
- [ ] AC-11: documentation states that build imports trusted graph Python,
  uses supplied tool bindings, compiles with `checkpointer=None`, and neither
  executes nodes nor guarantees configured-checkpointer initialization.
- [ ] AC-12: new tests carry the new REQ marker; the capability entry,
  changelog fragment, FR implementation record, and diary entry exist;
  targeted tests, `python scripts/req_coverage.py --strict`, and the full
  unit suite pass.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/linter/build_check.py`, `yamlgraph/linter/graph_linter.py`, and linter exports: opt-in E015 build check |
| D-2 | `yamlgraph/cli/__init__.py` and `yamlgraph/cli/graph_validate.py`: `--build` plus build-only `--tool` bindings |
| D-3 | `tests/unit/test_all_graphs_build.py`, targeted linter/CLI tests, and import-sentinel fixtures |
| D-4 | `tests/fixtures/graph_build_census.yaml`: fingerprinted tracked-graph build baseline |
| D-5 | `reference/graph-yaml.md` or the canonical linter reference: trust boundary, exact build boundary, bindings, and usage |
| D-6 | Capability/REQ record, changelog fragment, FR implementation record, and diary entry |

Not authorized: building during plain `graph lint`; changing the
`graph run` lint gate; constructing or validating configured checkpointers;
executing nodes or making LLM calls; repairing safety-guards or any other
graph; adding the pure edge-classifier lint check; changing compiler
grammar; editing CI workflows; or claiming subprocesses sandbox filesystem
or network side effects.

Enforcement conditions C-1–C-6 are in the
[judgement](FR-1086-lint-compile-check.judgement.md#conditions-for-enforcement)
and are all GATEs: revisions folded first (C-1, met 2026-09-26); plain lint
resolves no bindings and imports no graph Python (C-2); human approval of
the initial census baseline (C-3); every `broken` row names its own FR and
no graph is repaired here (C-4); the build stops at
`StateGraph.compile(checkpointer=None)` (C-5); the census compares
isolated, fingerprinted build outcomes, never aggregate lint exit status
(C-6).

## Alternatives Considered

Solution classes (chosen: 1):

1. **Opt-in `lint --build` that runs the real build path, plus a census
   test.** Chosen. It reuses the one compiler, so there is no second grammar,
   and the import risk is taken only when the user asks for it.
2. **Build by default in plain lint.** Rejected by the operator's opt-in
   decision (2026-09-25). It gives the stronger promise, but it executes
   Python on every lint, including the `graph run --gate` check and review
   of untrusted graphs.
3. **Call the compiler's pure edge classifier from plain lint.**
   Preserved dissent. `classify_edge`
   (`yamlgraph/compile/edge_compiler.py#L73-L93`) is documented as pure and
   imports nothing. Calling it per edge in plain lint would catch the
   safety-guards error with no trust change at all. It loses because it
   covers one family of build errors; tool-load failures, state-class errors
   and anything else `compile_graph` raises stay invisible. It does not
   compete with the chosen class and could be added alone if the judge
   prefers a narrower FR; this FR does not add it.
4. **Re-implement the build-time checks in the linter.** Rejected: a second
   grammar drifts from the compiler. FR-842 chose to call the loader's own
   validator for this reason.
5. **Build with stubbed Python imports.** Rejected: it needs a second loader
   mode inside the compile path, misses real import errors, and must also
   stub output-model imports (`yamlgraph/node_factory/base.py#L40`).
6. **Build in a sandboxed subprocess by default.** Rejected: a subprocess
   isolates state between tests but does not stop file or network side
   effects, so it would claim a safety it does not give. The census test
   uses subprocesses only for isolation.

`is_this_a_graph`: no. Whether a graph compiles is a deterministic call to
the existing compiler, not a model decision.

## Out of scope

Repairing safety-guards or any other graph ([FR-1087](FR-1087-safety-guards-demo-repair.md)
for safety-guards; each `broken` census row names its own FR). Changing the
`graph run` lint gate. Constructing the configured checkpointer. Provider or
model override flags on lint. Running any node or LLM call. The
pure-classifier check in class 3.

## Related

- Split from: [FR-1069](FR-1069-lint-builds-graph.md)
- Sibling: [FR-1087](FR-1087-safety-guards-demo-repair.md)
- Extends: [FR-842](FR-842-lint-compile-validation-parity.md)
- Error source: [FR-718](FR-718-edge-compiler-decomposition.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D10, §7 G
