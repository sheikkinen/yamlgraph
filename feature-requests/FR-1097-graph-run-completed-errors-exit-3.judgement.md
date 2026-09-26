# Judgement: FR-1097 `graph run` exits 3 when a completed run recorded untolerated errors

**Verdict:** APPROVED WITH REVISIONS — the split non-stream status primitive is sound and feasible, but authority activates only after the FR validates current-run error entries at the tally boundary and records the operator's exit-code decision for non-raising LLM/copilot guard halts.

**Reviewed against:** `feature-requests/FR-1097-graph-run-completed-errors-exit-3.md`; `feature-requests/FR-1083-exit-code-reflects-errors.md`; `feature-requests/FR-1083-exit-code-reflects-errors.judgement.md`; `feature-requests/FR-1066-exit-code-reflects-errors.md`; `feature-requests/FR-1066-exit-code-reflects-errors.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `docs/issues-2026-09-24.md`; `ARCHITECTURE.md`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/cli/helpers.py`; `yamlgraph/compile/map_contract.py`; `yamlgraph/error_handlers.py`; `yamlgraph/models/schemas.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/storage/export.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/utils/guard_runtime.py`; `yamlgraph/utils/route_log.py`; `scripts/author.sh`; `scripts/judge.sh`; `scripts/outsider.sh`; `scripts/research.sh`; `scripts/review.sh`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and the first consumer is concrete: the cited run lost four branches, retained the failures, emitted output, and exited 0 (`FR-1097:8-12`; `docs/issues-2026-09-24.md:43-101`). The inherited substitute research remains substantive, and this refile dispositions both the rejected predecessor and the SPLIT judgement rather than silently reviving them (`FR-1097:13-38`; `FR-1083.judgement:11-15`).

| Criterion | Finding |
|---|---|
| Scope | The refile obeys the split: it limits implementation to non-stream completion and explicitly leaves `_run_streaming` to FR-1098 (`FR-1097:171-176`, `322-329`; `FR-1083.judgement:19-23`). |
| Consistency | Output, export, route-log, JSON, and exit ordering now share one tally and leave graph state untouched (`FR-1097:137-170`, `265-272`). The two remaining inconsistencies are bounded by R-1 and R-2. |
| Measurability | AC-01 through AC-13 define observable exit codes, streams, files, counts, state cardinality, caller behavior, requirement coverage, and documentation (`FR-1097:235-294`). |
| Feasibility | The cited seams exist: `PipelineError` is a Pydantic model (`schemas.py:31-43`), `errors` is an add-reducer (`state_builder.py:69-71`), output and exports occur after invocation (`graph_commands.py:204-247`), and `RouteRun` is mutable within its context (`route_log.py:83-198`). |
| Architecture alignment | Classification belongs at the CLI presentation boundary, while tolerance is normalized where each typed error enters state; this follows the repository's boundary law and three-layer architecture (`FR-1097:96-140`, `181-182`; `.github/copilot-instructions.md:45-61`; `ARCHITECTURE.md:31-59`). |
| Single responsibility | Typed tolerance, delta-only skip updates, invocation baselining, output projection, route counts, and named caller handling are all necessary parts of one process-status contract. Streaming status is correctly separate (`FR-1097:94-179`, `314-329`). |
| Strategic classification | This is a **framework primitive**: the caller census names more than three independent consumers, and the defect occurs at the common `graph run` boundary rather than in one example (`FR-1097:184-233`). |
| Testability | Direct RED witnesses exist for clean, tolerated, mixed, raised, interrupted, exported, route-logged, historical, map, and caller outcomes (`FR-1097:237-294`). R-1 and R-2 add the two missing boundary witnesses. |

The strongest case against the proposal is that FR-677 already offers graph-level `verify`. The FR answers it: verification is opt-in, has no census adoption for this check, and `on_fail: halt` raises before normal output and exports, so it cannot provide the default completed-with-errors contract (`FR-1097:33-38`; `FR-677:58-73`). The baseline design also correctly avoids timestamp inference: it measures the checkpoint and imported prefixes before invocation, then tallies the reducer delta (`FR-1097:116-140`).

## Required revisions

### R-1: Validate every current-run error at the tally boundary

Amend Proposed Solution items 3 and 4 so the tally normalizes **every** entry in `result["errors"][baseline:]` with `PipelineError.model_validate` before reading `tolerated`, `node`, or `message`. Keep the normalized list inside `ErrorTally`; do not mutate `result` or either export.

This is required because the FR carries P15, yet validates only the initial-state prefix and then declares the suffix to be `list[PipelineError]` (`FR-1097:65-69`, `123-140`; `FR-1083:121-122`). The state channel is currently only `Annotated[list, add]`, and a Python node returns an arbitrary result dictionary directly into graph state (`state_builder.py:69-71`; `python_tool.py:311-326`). Construction-site typing therefore does not prove final-slice typing.

Define malformed current-run entries as a contract failure: print an origin-neutral diagnostic such as `invalid result errors[i]`, including the absolute final-list index and validation detail; exit 1 before success output, exports, or a completed-run tally line. Likewise, replace the proposed `--import-state: invalid errors[i]` wording with `invalid initial state errors[i]` unless the implementation actually preserves provenance, because the validated initial state may also come from graph data, a var file, or CLI variables (`graph_commands.py:132-147`; `graph_run_helpers.py:125-138`; `FR-1097:123-127`). Add direct tests for a valid serialized `PipelineError` dictionary in the current-run suffix and for malformed current-run entries with a missing `node` and an unknown `type`.

### R-2: Record the status of non-raising guard halts

Add a fourth explicit operator decision to the FR:

1. **Completed-error semantics (recommended):** an LLM/copilot pre-guard `on_fail: halt` that returns an untolerated `GuardViolation` is a completed run and exits 3 after normal output and exports; reserve "refusal exits 1" for CLI refusals and raised failures.
2. **Refusal semantics:** detect that returned `GuardViolation(on_fail="halt")` in the CLI tally and exit 1 without a completed-run tally.

The current text selects option 1 mechanically by leaving returned halt violations untolerated (`FR-1097:111-113`, `137-146`), while its Summary and Ideal Result say every refusal remains exit 1 (`FR-1097:42-48`, `86-92`). The distinction is observable because LLM pre-guard halt returns an error-state update (`llm_nodes.py:214-221`), whereas graph-level verify halt raises `GuardHaltError` (`guard_runtime.py:228-243`). Fold the selected meaning into Summary, Ideal Result, Proposed Solution, documentation, and one text/JSON acceptance witness. Do not change LLM/copilot guard execution semantics; that remains outside scope (`FR-1097:322-329`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Typed tolerance and tally models: `yamlgraph/models/schemas.py` and a focused CLI tally module or existing CLI helper |
| D-2 | Delta-only skip updates and tolerance construction at the error-producing sites named in Proposed Solution item 1 |
| D-3 | Non-stream baseline, final-slice validation, route-log counts, output/export ordering, stderr summary, and exit 0/1/3 behavior in `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/graph_run_helpers.py`, and `yamlgraph/utils/route_log.py` |
| D-4 | Explicit exit-3 handling only in caller-census rows 19, 24, 25, 27, and 28 |
| D-5 | Requirement-marked tests, capability record, `reference/getting-started.md`, changelog fragment, FR implementation record, and diary entry |

Not authorized: `--stream` behavior or exit 3 in streaming mode; OTel outcome changes; map failure-channel, naming, retry, or `min_success` changes; changing LLM/copilot guard execution semantics; creating `PipelineError` records for `tool_call` envelopes; graph-level thresholds; mutating graph state or exports with CLI tally keys; renaming or migrating arbitrary Python-tool business outputs; editing callers not marked "handles 3"; CI, hook, judge-doctrine, or review-doctrine changes.

## Revised acceptance criteria

- [ ] AC-01: A two-item map with one success, one non-tolerated Python sub-node failure, and integer `min_success: 1` completes, retains exactly one current-invocation `PipelineError` named `_map_<name>_sub`, emits normal output and exports, and exits 3; absent `min_success` raises `MapCompletenessError`, exits 1, and emits no tally line.
- [ ] AC-02: P1 (mocked LLM call failure without `on_error`) and P5 (missing LLM `requires:` key) each exit 3 in text and JSON modes; stderr names the node and message; JSON reports `_error_count: 1`.
- [ ] AC-03: One graph with a failing LLM `on_error: skip` node and a failing Python `on_error: skip` node exits 0, reports `_error_count: 0` and `_tolerated_error_count: 2`, and retains exactly two entries. Guard and verify `on_fail: warn` each exit 0 and increment only the tolerated count.
- [ ] AC-04: A graph with one P5 error and one Python skip failure exits 3, reports counts 1 and 1, and lists only the P5 entry in stderr details.
- [ ] AC-05: Top-level Python default/fail and LLM `on_error: fail` exceptions exit 1 with no tally line; a configured export failure exits 1.
- [ ] AC-06: JSON interrupt exits 1; a text interrupt resumed to a P5 completion exits 3; ending the text interrupt prompt with empty input exits 0.
- [ ] AC-07: For a completed P5 error with configured export, `--export`, and `--export-state`, stdout and both files exist before exit 3. Stdout JSON contains both tally keys; neither export contains either key.
- [ ] AC-08: With route logging enabled, `run_end.error_count` and `run_end.tolerated_error_count` equal the JSON projection for untolerated, tolerated, mixed, and clean completed runs.
- [ ] AC-09: One P5 error followed by one Python skip failure leaves exactly two `state.errors` entries, proving that `build_skip_error_state` returns only its delta.
- [ ] AC-10: Imported and checkpoint-retained historical errors do not affect this invocation's status: clean second runs exit 0, and second runs adding one P5 error exit 3 with `_error_count: 1`. Malformed initial-state entries exit 1 before node execution and identify their index.
- [ ] AC-11: A valid serialized `PipelineError` dictionary created during this invocation is normalized and tallied; malformed current-run entries with a missing `node` and an unknown `type` each exit 1 before success output and exports, identify the final-list index, and emit no completed-run tally line.
- [ ] AC-12: The operator-selected LLM/copilot pre-guard halt policy is asserted in text and JSON modes; the raised side-effect/verify `GuardHaltError` path remains exit 1.
- [ ] AC-13: Caller-census rows 19, 24, 25, 27, and 28 explicitly report rc 3 and continue to the unchanged artifact verdict. Shell assertions prove pass with a valid artifact and exit 65 without one. No other caller is edited.
- [ ] AC-14: `reference/getting-started.md` documents non-stream 0/1/3, skip/warn tolerance, the selected guard-halt rule, invocation-only history, malformed-error behavior, both JSON keys, and the absence of exit 3 in message streaming.
- [ ] AC-15: A capability file defines the new requirement; all new tests carry its `@pytest.mark.req` marker; RED and GREEN commits are separate; strict requirement coverage and the full unit suite pass; changed historical expectations are listed in the FR implementation record; the changelog fragment and diary entry with **Seed:** are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 and the operator answer required by R-2 are folded into the committed FR with no conditional language. | GATE |
| C-2 | Final-state error data must be validated before tally access; malformed entries must fail explicitly rather than be ignored, guessed, or counted through a fallback. | GATE |
| C-3 | No implementation may change streaming, map, guard-execution, tool-call-envelope, OTel, or unnamed-caller behavior. | GATE |
| C-4 | Changes to `author.sh`, `judge.sh`, `research.sh`, `review.sh`, and `outsider.sh` require explicit human review before merge because they are enforcement infrastructure. | GATE |
| C-5 | Tests must be committed RED before production changes and GREEN afterward, with requirement markers and the revised boundary cases above. | GATE |

Authority granted: after R-1 and R-2 are committed, implement only the frozen non-stream completed-result status contract and its five named caller migrations.
