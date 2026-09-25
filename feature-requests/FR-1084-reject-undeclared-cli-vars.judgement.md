# Judgement: FR-1084 Reject undeclared CLI variables

**Prior art:** `FR-1084-reject-undeclared-cli-vars.md` is the FR judged here; FR-1067 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** APPROVED WITH REVISIONS — rejecting user-supplied keys at the CLI boundary against the compiled state schema is sound and minimal; authority activates only after the diagnostic contract, census scope, and FR-1088 independence are folded into the FR.

**Reviewed against:** `feature-requests/FR-1084-reject-undeclared-cli-vars.md`; `feature-requests/FR-1067-reject-undeclared-cli-vars.md`; `feature-requests/FR-1067-reject-undeclared-cli-vars.judgement.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.judgement.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `feature-requests/FR-269-cli-inter-run-state-chaining.md`; `feature-requests/FR-688-cli-variables-injection.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-1088-innovation-matrix-repair.md`; `docs/issues-2026-09-24.md`; `ARCHITECTURE.md`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/cli/bench_commands.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/linter/checks_semantic.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and bounded. The cited run lost `domain`, resolved `{state.domain}` to `None`, and produced domain-free output (`docs/issues-2026-09-24.md:60-73`; `FR-1084:9-13`). The current CLI merges imported, file, and command-line values without checking them (`yamlgraph/cli/graph_commands.py:132-147`), while the generated state type is built from base, common, declared, data-file, and node-derived fields (`yamlgraph/models/state_builder.py:174-213`). A refusal before invocation directly prevents the plausible-success failure described by the FR.

The proposed seam conforms to repository architecture: normalize external `--var` and `--var-file` data at the CLI boundary, and derive accepted names from `app.get_input_jsonschema()["properties"]` rather than maintaining a second approximation (`FR-1084:73-83,99-110`). Placement immediately after compilation and before `_build_run_config` dominates stream, synchronous, and asynchronous execution (`FR-1084:102-107`; `yamlgraph/cli/graph_commands.py:173-187`). Exempting imported state preserves the separate inter-run chaining contract, while excluding graph-authored `variables:` and `data_files` keeps this FR focused on user input (`FR-1084:108-110,141-146`; `FR-269:51-99`).

The refile answers the rejected predecessor rather than ignoring it. It replaces the incorrect `input_channels` source with the compiled input JSON schema, adds sync/async/stream and imported-state witnesses, and turns the census contradiction into an explicit exclusion mechanism (`FR-1084:73-83,128-166`; `FR-1067-reject-undeclared-cli-vars.judgement.md:15-21`). Its six substantive alternatives preserve engine-level strictness as dissent, distinguish opt-in E007 linting, cite boundary-validation precedent, and answer `is_this_a_graph` (`FR-1084:170-200`). This is a valid in-body research substitute under the local doctrine and the precedent recognized in `FR-1076-shared-map-reuse-helpers.judgement.md:15`.

Scope is cohesive: runtime validation plus a compatibility census for the same CLI contract. It is not a linter, expression-evaluation, graph-variable, import-state, or benchmark change (`FR-1084:202-218`). Strategic classification is **framework primitive**: it corrects the shared `graph run --var`/`--var-file` contract across three execution modes and the documented invocation corpus, using the existing CLI and compiled-schema seams rather than introducing a new abstraction. The fixture criteria are directly testable once the remaining output and corpus rules below are made deterministic.

## Required revisions

### R-1: Freeze one deterministic validation and diagnostic contract

Replace the singular example at `FR-1084:111-114` with the complete algorithm: compute the union of keys supplied by `file_vars` and `cli_vars`; subtract the compiled input-schema property names; sort all unknown keys lexicographically; and fail once if the result is non-empty. Sort the displayed accepted keys lexicographically and omit underscore-prefixed names from display only, not from validation. State explicitly that schema retrieval or a malformed schema fails loudly through the existing CLI error path; it must not fall back to an independently reconstructed field set.

Freeze one message that applies truthfully to both sources, for example:
`❌ Unknown --var/--var-file state key(s) for pipeline.yaml: domain, typo; accepted keys: declared, inferred_sk`.
In human mode it goes to the existing `error_stream`; in `--json` mode stdout remains empty and the diagnostic goes to stderr, matching `yamlgraph/cli/graph_commands.py:116-138`. Add assertions for one unknown key, multiple keys across both sources, deterministic ordering, hidden accepted names, exit 1, and zero LLM calls.

### R-2: Bound the census so it cannot absorb unrelated repairs

Replace the open-ended "fixed in the same PR" clause at `FR-1084:115-124,147-150` with a frozen row and exclusion contract. Each committed census row must record source file and line, graph path, source kind (`--var` or `--var-file`), extracted key, and `PASS` or `EXCLUDED`. Each exclusion must record the reason and a filed FR number. Define how line continuations, repeated `--var`, referenced `--var-file` files, placeholders, shell variables, missing files, and unresolvable graph paths are classified so the extractor has one deterministic result.

The census may correct only a documentation key typo when the graph's compiled schema makes the intended accepted key unambiguous. Any finding requiring a graph, prompt, runtime, or semantic change must be excluded and filed separately; it is not implementation authority under FR-1084. The committed extracted list and exclusion manifest must be compared byte-for-byte in the test so stale generated evidence fails.

### R-3: Remove FR-1088 as an enforcement dependency

Replace conditional AC-08 (`FR-1084:151-152`) with a census assertion for the current checkout: the documented innovation-matrix invocation is `PASS` when its compiled schema contains `domain`; otherwise it is `EXCLUDED` with FR-1088 and the observed unknown key. FR-1084 must neither wait for FR-1088 nor modify its graph. The declared-input fixture already proves that the command passes after a graph exposes the key (`FR-1084:128-140`); duplicating that proof through a separately proposed graph repair makes this bug fix needlessly order-dependent.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/cli/graph_commands.py`: one compiled-input-schema validator called after `app = graph.compile(...)` and before `_build_run_config` |
| D-2 | Focused FR-1084 CLI tests using temporary graph and variable-file fixtures for unknown, accepted, imported, graph-variable, sync, async, stream, and JSON-output behavior |
| D-3 | Deterministic documented-invocation census test, committed extracted list, and committed exclusion manifest under `tests/fixtures/fr1084/` |
| D-4 | Capability/REQ traceability, changelog fragment, FR implementation record, and diary distillation |

Not authorized: changes to graph or prompt artifacts, including `innovation_matrix`; global strict-state behavior; expression strictness; the E007 implementation or `--gate` default; validation of `--import-state`; adding graph `variables:` to the state schema; `graph bench`; LangGraph patches, shims, or a duplicated accepted-key registry; or repairs to unrelated census findings beyond an unambiguous documentation-only key typo.

## Revised acceptance criteria

- [ ] AC-01 (RED): a temporary fixture graph with declared `state`, an inferred node `state_key`, a graph `variables:` key that is also declared, and a mocked LLM client exits 1 for `--var unknown=x`; the exact diagnostic names `unknown`, lists sorted visible accepted keys, and the mock records zero calls.
- [ ] AC-02: unknown keys split across `--var-file` and `--var` are unioned, deduplicated, sorted, reported in one diagnostic, and exit 1 before `_build_run_config` or graph invocation.
- [ ] AC-03: in human mode the frozen diagnostic is written to the existing `error_stream`; with `--json`, stdout is empty and stderr contains exactly the diagnostic.
- [ ] AC-04: `--var declared=a --var inferred_sk=b --var gv_declared=c` passes validation and the final state contains all three values in synchronous, `--async`, and `--stream` runs.
- [ ] AC-05: on the same fixture, `app.get_input_jsonschema()["properties"]` equals the keys retained when all schema keys plus one non-schema key are supplied through `invoke`, `ainvoke`, and `astream(stream_mode="values")`; the non-schema key is absent in every mode.
- [ ] AC-06: `--import-state` containing `declared` and `other_graph_key` is not validated as user variables; the run succeeds, `declared` reaches state, and the foreign key is absent from the result.
- [ ] AC-07: `--var gv_only=x`, where `gv_only` exists only under graph `variables:`, exits 1 as an unknown state key; an underscore-prefixed schema key remains accepted but is omitted from the displayed accepted-key list.
- [ ] AC-08: the deterministic census covers `README.md`, `reference/**/*.md`, `examples/**/README.md`, and `examples/demos/demo.sh`, joins shell continuations, emits the frozen row shape, and exactly matches the committed extracted list and exclusion manifest.
- [ ] AC-09: every resolvable census row is `PASS` or has a reasoned `EXCLUDED` record with a filed FR number; only an unambiguous documentation key typo may be repaired under this FR.
- [ ] AC-10: the innovation-matrix `--var domain=...` row is `PASS` if the checkout's compiled schema contains `domain`; otherwise it is `EXCLUDED` with FR-1088 and `domain` recorded as the unknown key. No innovation-matrix artifact changes under FR-1084.
- [ ] AC-11: a new capability/REQ entry governs CLI variable validation; every new or changed test function carries its requirement marker; `python scripts/req_coverage.py --strict` passes; and the changelog fragment, FR implementation record, and diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-1084 and obtain human review of this advisory judgement before implementation authority activates. | GATE |
| C-2 | Use only `app.get_input_jsonschema()["properties"]` as the accepted-key source; no duplicated registry, E007 field set, silent fallback, or LangGraph patch. | GATE |
| C-3 | Validate only keys supplied by `--var` and `--var-file`, after compilation and before `_build_run_config`; do not validate imported or graph-authored state layers. | GATE |
| C-4 | Unknown input must exit 1 before sync, async, or stream invocation and before any LLM call; diagnostics must obey the frozen human/JSON stream contract. | GATE |
| C-5 | Census findings must not expand implementation scope: graph, prompt, runtime, and semantic repairs are excluded with filed FRs. | GATE |
| C-6 | Do not modify `innovation_matrix` or depend on FR-1088 landing; its current state is represented by the census contract. | GATE |
| C-7 | RED tests precede GREEN implementation, all affected tests carry the new REQ marker, and the strict requirement-coverage check passes. | GATE |

Authority granted: after all revisions and gates are satisfied, implement the compiled-schema CLI check, its focused tests, the bounded documented-invocation census, and the repository-required traceability artifacts exactly within D-1 through D-4.
