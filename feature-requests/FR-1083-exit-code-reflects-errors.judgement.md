# Judgement: FR-1083 `graph run` exit code reflects recorded errors

**Prior art:** `FR-1083-exit-code-reflects-errors.md` is the FR judged here; FR-1066 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** SPLIT — the non-stream completed-result contract is sound, but changing a streaming error event from exit 0 to exit 1 is an independent bug on a different execution path; neither concern has implementation authority under FR-1083, and each must re-enter the pipeline separately.

**Reviewed against:** `feature-requests/FR-1083-exit-code-reflects-errors.md`; `feature-requests/FR-1066-exit-code-reflects-errors.md`; `feature-requests/FR-1066-exit-code-reflects-errors.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `docs/issues-2026-09-24.md`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/error_handlers.py`; `yamlgraph/models/schemas.py`; `yamlgraph/storage/export.py`; `yamlgraph/utils/route_log.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and witnessed: the recorded run lost four branches, retained the failures in `state.errors`, emitted success output, and exited 0 (`docs/issues-2026-09-24.md:43-101`; `feature-requests/FR-1083-exit-code-reflects-errors.md:8-12`). The refile answers FR-1066's central defects: it inventories completed and raising paths, distinguishes author-tolerated failures at construction, preserves output and exports before exit 3, and gives JSON and `run_end` one tally definition (`FR-1083:90-136`, `149-204`, `263-300`).

The substitute research is substantive enough for the local research gate. It compares six genuine solution classes, preserves dissent, cites existing verification and map policy, and answers `is_this_a_graph` (`FR-1083:304-338`). The strongest case against the proposal is that FR-677 already provides graph-level verification; the FR disposes it with two material differences: it is opt-in with no census adoption, and `on_fail: halt` prevents the completed output/export contract (`FR-1083:315-325`; `FR-677:58-73`).

The non-stream concern is a **framework primitive**: scripts, CI jobs, the FSM runner, and example launchers all consume the process status, while no existing default abstraction reports completed recorded errors at the CLI boundary (`FR-1083:8-12`, `215-233`). A defaulted `PipelineError.tolerated` field, delta-only reducer updates, a typed tally, and counts stored on the active `RouteRun` are feasible with the cited seams (`schemas.py:31-43`; `error_handlers.py:230-264`; `graph_commands.py:186-247`; `route_log.py:83-205`). The tolerance and double-count fixes are coupled to truthful exit status rather than separate product concerns.

## Required revisions

### R-1: Split streaming crash status from completed-result status

Re-file the non-stream contract without the `--stream` behavior change in Proposed Solution item 6, H-4, and AC-06 (`FR-1083:206-209`, `254-255`, `280-281`). That FR may document that exit 3 is unavailable in message streaming because no final state is exposed, but it must not modify `_run_streaming`.

File the current streaming defect separately: an emitted error event currently prints an error and returns success, while the proposed one-line exit-1 change neither computes nor consumes the final-state tally (`graph_commands.py:50-52`, `183-185`; `FR-1083:206-209`). The streaming FR owns success/error-event exit behavior and its tests; it must not add exit 3 without first defining a final-state source.

### R-2: Obtain and fold the three remaining operator decisions

Replace H-1 through H-3 and every conditional acceptance clause with recorded answers to these explicit questions:

1. **Artifact-verified adapters:** when `graph run` returns 3, must `author.sh`, `judge.sh`, `research.sh`, `review.sh`, and `outsider.sh` stop immediately, or explicitly accept 3 and continue to their existing artifact-validation verdict? Name the selected behavior for each adapter; the existing statement that 3 is a hard stop "unless handled explicitly" does not select between those outcomes (`FR-1083:43-45`, `221-225`, `237-242`).
2. **Warnings:** does guard or verify `on_fail: warn` mean tolerated exit status, or does it make a completed run exit 3? Apply the answer to P8, the tally, stderr, JSON, route log, and tests (`FR-1083:115`, `243-246`).
3. **Historical errors:** does process status describe only errors created by this invocation, or every error in the final state, including imported and checkpoint-retained entries? If invocation-only is selected, specify one normalization/validation boundary and tests for both `--import-state` and an existing `--thread`; the current AC-11 covers only imported state (`FR-1083:166-172`, `247-252`, `294-295`).

No enforcer may infer these product decisions from the suggested defaults.

### R-3: Keep CLI metadata out of graph state and exports

Replace the instruction to attach `_error_count` and `_tolerated_error_count` to `result` (`FR-1083:191-195`). `_print_json_result` serializes the result dictionary directly, and `--export-state` later serializes the same dictionary without filtering underscore-prefixed keys (`graph_run_helpers.py:71-75`, `268-289`; `storage/export.py:52-70`, `97-113`). Mutating `result` would therefore make CLI metadata part of exported and subsequently imported graph state, contradicting the FR's boundary claim.

Pass the single `ErrorTally` separately to the JSON output projection and construct a serialized output copy containing the two metadata keys; pass the untouched graph result to both export paths. Add an assertion that stdout JSON contains both counts while `--export-state` and configured exports contain neither CLI metadata key.

### R-4: Reconcile the map witness with FR-1073

Delete the claim that the same map failure behaves identically before and after FR-1073 and correct AC-01(b) (`FR-1083:51-57`, `263-266`). FR-1073's absent `min_success` means fraction `1.0`; one non-tolerated branch failure writes a `PipelineError` and then raises `MapCompletenessError`, so that run exits 1 rather than completing with exit 3 (`FR-1073:147-150`, `175`, `179-195`).

Make FR-1073 a prerequisite for the non-stream refile, consistent with the cited plan's A-before-B order (`docs/issues-2026-09-24.md:597-604`). Use a two-item map with one success, one non-tolerated failure, and integer `min_success: 1` as the completed map witness: the threshold is met, final `state.errors` has one entry, and the CLI exits 3. Add the complementary unmet-threshold assertion that `MapCompletenessError` exits 1 and emits no completed-run tally.

### R-5: Complete the caller census before authority

Replace the aggregate row "18 shell scripts under `examples/`" with all 18 paths and a per-file current control-flow finding and chosen exit-3 treatment (`FR-1083:233`). AC-09 cannot defer that scope discovery to the implementation record while the FR simultaneously claims a complete caller table (`FR-1083:215-233`, `288-290`). Mark each caller as unchanged, explicitly handles 3, or stops on any non-zero; only the named "handles 3" rows may be edited by the core FR.

### R-6: Make every acceptance criterion unconditional and boundary-specific

Rewrite the acceptance list after R-1 through R-5 so no item contains "if H-4 accepted," "with H-1's decision," "per H-3," or an unnamed future inventory (`FR-1083:280`, `288-295`). State whether AC-02's two tolerated failures occur in one graph, and test both text and JSON projections without relying on import errors or missing fixtures. Keep the RED/GREEN commit requirement and requirement markers from repo doctrine.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New FR: non-stream `graph run` completed-result tally, typed tolerance, truthful 0/1/3 status, stderr summary, JSON projection, `run_end` counts, delta-only skip update, named caller migration, documentation, tests, changelog, implementation record, and diary |
| D-2 | New FR: streaming error-event exit status in `_run_streaming`, with successful-stream and error-event tests and scoped documentation |

Not authorized under FR-1083: implementation of either deliverable; OTel outcome changes; map failure-channel, naming, retry, or `min_success` changes; changing LLM/copilot guard-halt semantics; creating `PipelineError` records for `tool_call` envelopes; graph-level error thresholds; exit 3 in streaming mode; mutating final graph state with CLI tally keys; editing unnamed callers; CI, hook, judge-doctrine, or review-doctrine changes.

## Revised acceptance criteria

### Non-stream completed-result FR

- [ ] AC-01: After FR-1073 is merged, a two-item map with one successful item, one non-tolerated failed item, and integer `min_success: 1` completes, writes one current-invocation `PipelineError`, emits its normal output and exports, and exits 3; an unmet threshold raises `MapCompletenessError`, exits 1, and emits no completed-run tally.
- [ ] AC-02: Stable completed paths P1 and P5 each exit 3 in text and JSON modes; stderr names the node and message, and JSON reports `_error_count: 1`.
- [ ] AC-03: One graph containing both a failing LLM `on_error: skip` path and a failing Python `on_error: skip` path exits 0, reports `_error_count: 0` and `_tolerated_error_count: 2`, and records exactly two errors.
- [ ] AC-04: A mixed graph with one untolerated and one tolerated error exits 3, reports counts 1 and 1, and lists only the untolerated entry in the bounded detail list.
- [ ] AC-05: Top-level Python and LLM `on_error: fail` exceptions exit 1 with no completed-run tally. An export failure after a completed graph also exits 1.
- [ ] AC-06: JSON interrupts exit 1; a text interrupt resumed to a completed untolerated error exits 3; ending the text prompt with empty input exits 0.
- [ ] AC-07: For a completed-error run using configured export and `--export-state`, stdout is emitted and both files exist before exit 3. Stdout JSON contains both tally keys; neither exported state nor configured export contains those CLI metadata keys.
- [ ] AC-08: `run_end.error_count` and `run_end.tolerated_error_count` equal the JSON projection for untolerated, tolerated, mixed, and clean completed runs.
- [ ] AC-09: One P5 error followed by one Python skip failure leaves exactly two `state.errors` entries, proving delta-only reducer updates.
- [ ] AC-10: Tests implement the operator-selected historical-error rule for both `--import-state` and an existing checkpoint thread, including a current error after historical entries and malformed imported `PipelineError` data.
- [ ] AC-11: The FR names every repository caller and its treatment of exit 3; tests or shell assertions cover each modified caller, and unchanged rows are justified by their visible control flow.
- [ ] AC-12: `reference/getting-started.md` documents non-stream exit codes 0/1/3, the selected tolerated/warn/history rules, the two JSON metadata keys, and the absence of exit 3 in message streaming.
- [ ] AC-13: A capability/REQ record and requirement-marked RED tests exist; strict requirement coverage and the full unit suite pass; the changelog fragment, FR implementation record, and diary entry with **Seed:** are committed.

### Streaming error-status FR

- [ ] AC-S01: A successful message stream exits 0; a stream that emits an error event exits 1 after printing the error; no final-state count or exit 3 is claimed.
- [ ] AC-S02: Documentation scopes the streaming status contract separately from non-stream completed-result status.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1083 grants no implementation authority; both concerns must be filed and judged separately. | GATE |
| C-2 | The three operator answers in R-2 must be committed into the non-stream FR before it is judged. | GATE |
| C-3 | FR-1073 must be merged before enforcing the map-based non-stream acceptance witness. | GATE |
| C-4 | The complete caller census must be part of the FR before implementation begins; no unnamed caller edits are allowed. | GATE |
| C-5 | Any changes to the artifact-verifying author, judge, research, review, or outsider scripts require explicit human review as enforcement-infrastructure changes. | GATE |
| C-6 | Tests must be committed RED before production changes and GREEN afterward, with requirement markers and no conditional acceptance language. | GATE |

Authority granted: none under FR-1083; authority may be sought separately for the corrected non-stream primitive and the streaming crash-status fix after the applicable revisions are committed.
