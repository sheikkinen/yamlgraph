# Judgement: FR-1086 `graph lint --build` — opt-in check that the graph compiles

**Prior art:** `FR-1086-lint-compile-check.md` is the FR judged here; FR-1069 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** APPROVED WITH REVISIONS — the opt-in compile check is sound, but authority activates only after the FR defines the exact build boundary and makes the repository census executable for bound and environment-dependent graphs.

**Reviewed against:** `feature-requests/FR-1086-lint-compile-check.md`; `feature-requests/FR-1069-lint-builds-graph.md`; `feature-requests/FR-1069-lint-builds-graph.judgement.md`; `feature-requests/FR-1087-safety-guards-demo-repair.md`; `feature-requests/FR-842-lint-compile-validation-parity.md`; `feature-requests/FR-718-edge-compiler-decomposition.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.md`; `docs/issues-2026-09-24.md` section 2 D10 and graph-census method; `examples/demos/safety-guards/graph.yaml`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/repo_census/graph.yaml`; `examples/demos/person_profile_census/graph.yaml`; `examples/demos/pattern_model_census/graph.yaml`; `yamlgraph/linter/graph_linter.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_validate.py`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/edge_compiler.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/tools/tool_builders.py`; `yamlgraph/tools/tool_slots.py`; `yamlgraph/node_factory/base.py`; `pyproject.toml`; `ARCHITECTURE.md`; `CLAUDE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and directly witnessed: FR-1086:9-14 identifies a graph that passes static lint but is rejected by the compiler, and `edge_compiler.py:35-43` contains the cited rejection. Reusing `load_graph_config`, `compile_graph`, and LangGraph compilation rather than duplicating compiler rules follows FR-842's parity-by-construction precedent and the existing load/compile architecture (`graph_loader.py:121-184,333-398`).

The opt-in trust boundary is correct. FR-1086:63-77 shows that building imports graph-declared Python, while FR-1086:6 and 93-97 preserve plain lint as a non-executing operation. AC-02 makes that boundary observable with a real import-time sentinel rather than a mock. The operator decision therefore resolves FR-1069 judgement R-2 without silently broadening ordinary lint.

Scope and responsibility are coherent: the linter/CLI check, its parity tests, and its repository census are one compile-detection concern (FR-1086:40-45,100-123). Demo repair, run-gate changes, node execution, and the narrower edge classifier are explicitly excluded (FR-1086:181-186). This satisfies FR-1069 judgement R-1 and does not require another split.

The in-body research substitute has substance: six distinct solution classes, a preserved pure-classifier dissent, prior-art dispositions, and an explicit negative `is_this_a_graph` answer (FR-1086:148-179). Strategically this is a **framework primitive**: the opt-in lint capability applies to the 202-graph repository corpus and external user graphs, while the real compiler is the only fitting abstraction.

## Required revisions

### R-1: Define the build boundary and compilation inputs exactly

Replace the claims that `--build` works "the same way `graph run` does" and guarantees that run gets past compilation (FR-1086:40-45,93-97) with this exact contract:

> `graph lint --build` succeeds when `load_graph_config` with the supplied compilation inputs, `compile_graph`, and `StateGraph.compile(checkpointer=None)` succeed. It does not construct the configured checkpointer, execute a node, or call an LLM.

This distinction is required because `graph run` passes tool bindings and provider/model overrides, constructs the configured checkpointer, and then compiles with it (`graph_commands.py:156-175`), while the proposed check explicitly omits the checkpointer (FR-1086:100-106).

Add repeatable `--tool SLOT=MANIFEST` support to `graph lint --build`, reuse `parse_tool_bindings`, and pass the result to `load_graph_config`. Reject `--tool` when `--build` is absent so plain lint's contract and output remain unchanged. This is necessary for tracked graphs that declare invocation-time slots, including `corpus_census` (`graph.yaml:46,50`), `repo_census` (`graph.yaml:47,51`), `person_profile_census` (`graph.yaml:49,53,58`), and `pattern_model_census` (`graph.yaml:36,40`). Do not add provider/model override flags under this FR; state explicitly that those execution selections are outside this structural build check.

### R-2: Make the census compare substantive build outcomes

Freeze the census at `tests/fixtures/graph_build_census.yaml` and its test at `tests/unit/test_all_graphs_build.py`. Define the corpus mechanically as git-tracked YAML beneath `examples/`, `graphs/`, and `.chaplain/graphs/` whose parsed top-level `nodes` value is a mapping; exclude paths under any `prompts/` directory. Do not use a text match for `^nodes:` as the source of truth.

Each row must contain a path, an outcome, and optional compilation inputs:

- `builds`, optionally with tracked `bindings` for declared tool slots;
- `broken`, with an owning `FR-NNNN`, exception class, and exact message or an explicitly justified stable message prefix;
- `needs`, with one named `pyproject.toml` extra and the expected missing-dependency exception fingerprint.

Run the dedicated build check in a fresh subprocess with a fixed, documented timeout. Compare the build result itself, not the aggregate exit status of `graph lint --build`: unrelated static lint errors must not turn a compiling graph into a build failure. A `broken` row must fail if the exception fingerprint changes even when the graph remains broken. A `needs` row may skip only when the named extra's requirements are absent; when they are installed, the graph must build. Missing rows, duplicate rows, stale rows, untracked rows, missing binding manifests, timeouts, and outcome/fingerprint drift must all fail the test.

Record the initial counts and every non-`builds` row in FR-1086 before enforcement. Human review of that initial baseline is a GATE because the census becomes repository enforcement.

### R-3: Freeze the lint diagnostic and no-build baseline

Assign the build diagnostic `E015`; "next free E-code" (FR-1086:105-106) is not a stable acceptance contract. Freeze `lint_graph(..., build: bool = False)` as the API default and `--build` as the sole switch that enables it.

Before changing production code, record exact stdout, stderr, exit code, and `LintResult` expectations for fixed clean, warning-only, and E000 fixtures. Replace AC-03's unrepeatable "identical before and after" comparison (FR-1086:133-134) with tests against those committed expectations. The build-error contract is one `E015` issue with `message == str(exc)`; JSON mode must serialize that same issue shape. An existing E000 must suppress loading/building entirely, including tool binding and Python import.

### R-4: Fold the revised criteria and enforcement record into the FR

Replace the current acceptance list with the criteria below, update the FR status to judged with revisions, and preserve the operator's opt-in decision. The implementation record must report the census command, counts, non-building rows, targeted tests, requirement coverage, and full-suite result; it must not claim configured-checkpointer or execution parity.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/linter/build_check.py`, `yamlgraph/linter/graph_linter.py`, and linter exports: opt-in E015 build check |
| D-2 | `yamlgraph/cli/__init__.py` and `yamlgraph/cli/graph_validate.py`: `--build` plus build-only `--tool` bindings |
| D-3 | `tests/unit/test_all_graphs_build.py`, targeted linter/CLI tests, and import-sentinel fixtures |
| D-4 | `tests/fixtures/graph_build_census.yaml`: fingerprinted tracked-graph build baseline |
| D-5 | `reference/graph-yaml.md` or the canonical linter reference: trust boundary, exact build boundary, bindings, and usage |
| D-6 | Capability/REQ record, changelog fragment, FR implementation record, and diary entry |

Not authorized: building during plain `graph lint`; changing the `graph run` lint gate; constructing or validating configured checkpointers; executing nodes or making LLM calls; repairing safety-guards or any other graph; adding the pure edge-classifier lint check; changing compiler grammar; editing CI workflows; or claiming subprocesses sandbox filesystem or network side effects.

## Revised acceptance criteria

- [ ] AC-01 (RED): `graph lint --build examples/demos/safety-guards/graph.yaml` exits 1 and reports exactly one error-level `E015` whose message equals the `ValueError` text from `edge_compiler.py:38-43`; unrelated warnings may also be present.
- [ ] AC-02: an import-sentinel fixture proves plain `graph lint` leaves the sentinel absent and `graph lint --build` creates it without executing a graph node.
- [ ] AC-03: committed clean, warning-only, and E000 fixtures preserve their frozen plain-lint stdout, stderr, exit code, and `LintResult`; no fixture produces E015 without `build=True`.
- [ ] AC-04: `--build` on an E000 graph reports E000 only and performs no loader binding, graph-declared Python import, compiler call, or LangGraph compile.
- [ ] AC-05: a slot fixture fails closed without a binding and builds with `graph lint --build --tool SLOT=MANIFEST`; `--tool` without `--build` is rejected without importing graph Python.
- [ ] AC-06: the census parser covers exactly the tracked top-level graph corpus, rejects missing/duplicate/stale/untracked rows, and the FR records counts plus every `broken` and `needs` row.
- [ ] AC-07: the census test runs each graph in a bounded fresh subprocess and fails on outcome, exception-class, message-fingerprint, timeout, or binding-manifest drift.
- [ ] AC-08: a `needs` fixture skips only when its named `pyproject.toml` extra is unavailable and must build when that extra is installed.
- [ ] AC-09: a graph with an unrelated static lint error but a successful build is classified `builds`; census classification does not use aggregate lint exit status.
- [ ] AC-10: human and `--json` modes expose E015 through the existing lint issue shape, preserve `str(exc)` unchanged, and exit nonzero on the error.
- [ ] AC-11: documentation states that build imports trusted graph Python, uses supplied tool bindings, compiles with `checkpointer=None`, and neither executes nodes nor guarantees configured-checkpointer initialization.
- [ ] AC-12: new tests carry the new REQ marker; the capability entry, changelog fragment, FR implementation record, and diary entry exist; targeted tests, `python scripts/req_coverage.py --strict`, and the full unit suite pass.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-1086 before any production implementation; authority does not activate from this draft alone. | GATE |
| C-2 | Plain lint must not resolve bindings, import graph-declared Python, or invoke any build step. | GATE |
| C-3 | Human review must approve the initial census baseline and every `broken`/`needs` disposition before it becomes repository enforcement. | GATE |
| C-4 | Every `broken` graph names its own FR; no graph repair is permitted under FR-1086. | GATE |
| C-5 | The build check must stop at `StateGraph.compile(checkpointer=None)` and make no configured-checkpointer, node, or LLM call. | GATE |
| C-6 | The census must compare isolated, fingerprinted build outcomes; aggregate lint exit status is not an acceptable proxy. | GATE |

Authority granted: after R-1 through R-4 are folded and C-3 is satisfied, implement the opt-in E015 in-memory build check, build-only tool bindings, fingerprinted tracked-graph census, tests, and directly related documentation listed in D-1 through D-6.
