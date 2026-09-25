# Feature Request: `graph lint --build` — opt-in check that the graph compiles

**Priority:** MEDIUM
**Type:** Bug / Linter completeness
**Status:** Proposed
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
(`yamlgraph/linter/graph_linter.py#L81-L106`). Errors raised later, inside
`compile_graph`, are still invisible to lint. This FR extends FR-842's
message-parity rule (exception text kept verbatim) to the build step.
[FR-718](FR-718-edge-compiler-decomposition.md) (Completed). It turned a
condition on a fan-out list from "silently dropped" into a raise. That is
the error the first consumer hits.

## Summary

Add a `--build` flag to `graph lint`. With it, lint also builds the graph the
same way `graph run` does, and reports any build exception as one lint error
with the exception text unchanged. Without it, lint behaves exactly as today
and imports no graph-declared Python. Add a repository test that records the
build outcome of every tracked graph.

## Value Statement

A graph author or CI job that trusts a graph can learn, without calling any
LLM, whether `graph run` would get past compilation. Broken tracked graphs are
found by CI, not by the next user.

## Problem

- Plain lint runs `validate_config` first
  (`yamlgraph/linter/graph_linter.py#L128-L130`), then only static checks.
  No linter module imports Python or calls `compile_graph` (no
  `importlib`, `load_python_function` or `compile_graph` in
  `yamlgraph/linter/`, searched 2026-09-25).
- `graph run` lints first (`yamlgraph/cli/graph_commands.py#L62-L100`), then
  loads and compiles (`yamlgraph/cli/graph_commands.py#L164-L175`). Errors
  raised by `compile_graph` therefore reach the user only at run time.
- Building imports graph-declared Python. `compile_graph` loads Python tools
  through `load_python_function` (`yamlgraph/compile/graph_loader.py#L294-L301`),
  as do map sub-nodes (`yamlgraph/compile/map_compiler.py#L288`) and tool
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
  excluding `prompts/`, finds 202 files (2026-09-25).

## Human decision needed

- **May plain `graph lint` import and execute graph-declared Python, or is
  building opt-in (`graph lint --build`) on graphs the user trusts?**
  Suggested default: **opt-in**. Reasons: (1) lint is run on graphs a user
  has not decided to run — PR review, CI over contributed graphs, the
  `graph run` gate itself — and plain lint executes no Python today;
  (2) CLAUDE.md states only YAML config is trusted; (3) the
  [FR-1069](FR-1069-lint-builds-graph.md) header records the operator
  choosing opt-in on 2026-09-25, and this FR asks the judge to confirm that
  record carries over rather than treating it as settled. If the human
  chooses default-on instead, the Ideal Result below changes to "`lint`
  passes ⇒ builds", the `--build` flag is dropped, and AC-02 is inverted.

## Ideal Result

`graph lint --build` passes ⇒ `graph run` gets past compilation, with no LLM
call. Plain `graph lint` keeps its current promise and never runs
graph-declared Python. Every tracked graph has a recorded build outcome, and
CI fails when an outcome changes.

## Proposed Solution

1. **Build check.** New function in `yamlgraph/linter/` that runs
   `load_graph_config(path)`, `compile_graph(config)` and
   `StateGraph.compile()` with no checkpointer, so lint never opens a
   checkpointer backend. Any exception becomes one error-level issue with
   the next free E-code and `str(exc)` as the message.
2. **Flag.** `lint_graph(..., build: bool = False)` calls the build check
   last, only when `build` is true, and skips it when an earlier E000 is
   present (the build would fail for the same reason). `graph lint` gains
   `--build` next to `--json` (`yamlgraph/cli/__init__.py#L194-L205`),
   threaded through `cmd_graph_lint` (`yamlgraph/cli/graph_validate.py#L233`).
   The `graph run` lint gate is unchanged; run compiles right after it anyway.
3. **Build census test.** A committed census file lists every tracked graph
   (the 202-file rule above) with one outcome: `builds`, `broken: FR-NNNN`,
   or `needs: <extra>` (an optional dependency named in `pyproject.toml`).
   The test runs `graph lint --build` per graph in a subprocess, so imported
   modules and their side effects do not leak into other tests. It asserts
   the actual outcome equals the recorded one. A `needs:` graph is skipped
   with that reason only when the extra is missing, and must build when it
   is present. Untracked graphs are out of the census by construction.
   A new tracked graph without a census row fails the test.
4. **Docs.** `reference/graph-yaml.md` or the linter reference names
   `--build`, what it executes, and when to use it.

## Acceptance Criteria

- [ ] AC-01 (RED): `graph lint --build examples/demos/safety-guards/graph.yaml`
  reports one error whose message equals the `ValueError` text raised by
  `yamlgraph/compile/edge_compiler.py#L38-L43`, unchanged.
- [ ] AC-02 (trust boundary): a test fixture graph declares a Python tool
  whose module writes a sentinel file at import time. Plain `graph lint`
  leaves no sentinel; `graph lint --build` creates it.
- [ ] AC-03: plain `graph lint` output and exit code are identical before and
  after the change on the same fixture set.
- [ ] AC-04: `--build` with an earlier E000 reports the E000 only, not a
  second build error.
- [ ] AC-05: the census file exists, covers every tracked graph by the rule
  in Proposed Solution 3, and this FR records its counts per outcome and the
  names of every `broken:` and `needs:` row.
- [ ] AC-06: the census test fails when a tracked graph's build outcome
  differs from its row, and when a tracked graph has no row.
- [ ] AC-07: `--json` output includes the build error in the same issue
  shape as other errors.
- [ ] AC-08: new REQ in a capability file, tests tagged,
  `python scripts/req_coverage.py --strict` passes, changelog fragment, FR
  implementation record, diary entry.

## Alternatives Considered

Solution classes (chosen: 1):

1. **Opt-in `lint --build` that runs the real build path, plus a census
   test.** Chosen. It reuses the one compiler, so there is no second grammar,
   and the import risk is taken only when the user asks for it.
2. **Build by default in plain lint.** Rejected pending the human decision.
   It gives the stronger promise, but it executes Python on every lint,
   including the `graph run` gate and review of untrusted graphs.
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
for safety-guards; each `broken:` census row names its own FR). Changing the
`graph run` lint gate. Running any node or LLM call. The pure-classifier
check in class 3.

## Related

- Split from: [FR-1069](FR-1069-lint-builds-graph.md)
- Sibling: [FR-1087](FR-1087-safety-guards-demo-repair.md)
- Extends: [FR-842](FR-842-lint-compile-validation-parity.md)
- Error source: [FR-718](FR-718-edge-compiler-decomposition.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D10, §7 G
