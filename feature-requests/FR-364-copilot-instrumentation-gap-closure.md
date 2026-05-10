# Feature Request: FR-364 close Copilot instrumentation process-mining contract gaps

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-10

## Summary

Close the FR-362 follow-up gaps in local Copilot instrumentation by hardening runner flags/env, expanding the normalized event schema, extracting semantic events from captured spans, and adding deterministic tests/docs for the judged contract.

## Value Statement

Maintainers get instrumentation artifacts that are consistently captured and directly useful for process mining, so conformance analysis is based on stable semantic events instead of manual span archaeology.

## Problem

Issue #364 reports that FR-362 delivered a useful POC but left key contract gaps:

1. `scripts/copilot_instrument.sh` does not pass required instrumentation flags (`--output-format json`, `--log-dir`, `--log-level debug`).
2. OTel content-capture env vars are not enforced in the runner (`COPILOT_OTEL_EXPORTER_TYPE=file`, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`).
3. `scripts/extract_copilot_events.py` only emits coarse event types (`otel_span`, `git_diff`) and a thin schema.
4. Event model lacks `source`, `success`, and `details`.
5. Tests do not cover the judged follow-up boundaries (runner flags/env, semantic extraction, expanded schema, deterministic conformance reporting).
6. Runner captures only post-phase git snapshots (`git-status.txt`, `git-diff.patch`) and not explicit before/after phase snapshots.

## Research: Existing Patterns, Evidence, and Gaps

1. **Current runner contract is minimal and incomplete for the follow-up ask.**
   - `scripts/copilot_instrument.sh` currently builds Copilot commands with `--silent`, `--allow-all-tools`, `--allow-all-paths`, `--share`, and optional `--resume`.
   - It exports only `COPILOT_OTEL_FILE_EXPORTER_PATH` and does not set exporter-type/content-capture env vars.
2. **Current extractor boundary is intentionally coarse (FR-362) and needs the follow-up extension.**
   - `scripts/extract_copilot_events.py` model fields are only `case_id`, `phase`, `event_type`, `timestamp`, `summary`.
   - Event classes currently emitted are only `otel_span` and `git_diff`.
3. **In-repo findings already identify `report_intent` as deterministic phase signal.**
   - `docs/copilot-instrumentation-poc.md` records `report_intent` spans as phase markers and explicitly recommends adding semantic event extraction (`phase_marker`, `test_run`, `lint_run`, `file_create`, `file_edit`, `failure`).
4. **Coverage gap is real in current tests.**
   - `tests/unit/test_fr362_copilot_instrumentation_poc_red.py` validates only FR-362 minimal contract and does not assert follow-up requirements from issue #364.
5. **Problem is not solved elsewhere in this worktree.**
   - No other Copilot instrumentation runner/extractor implements the missing flags/env, expanded schema, or semantic event extraction contract.

## Objectives

1. Make runner instrumentation output deterministic and complete for process-mining analysis.
2. Promote normalized event schema from coarse summary rows to machine-usable semantic records.
3. Extract high-signal semantic events from captured telemetry without adding live-runtime dependencies.
4. Define strict RED acceptance tests for all judged follow-up boundaries.

## Constraints

1. **Single responsibility:** close FR-362 follow-up contract gaps only.
2. **Scope boundary:** limit changes to:
   - `scripts/copilot_instrument.sh`
   - `scripts/extract_copilot_events.py`
   - `docs/copilot-instrumentation-poc.md`
   - `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py`
   - `capabilities/CAP-145-copilot-instrumentation-gap-closure.yaml` *(required — see constraint 6)*
3. **No YAMLGraph runtime changes:** no edits under `yamlgraph/` for this FR.
4. **No new dependencies:** use stdlib + existing project dependencies only.
5. **Deterministic testability:** all acceptance criteria must be assertable with synthetic fixtures (no live Copilot required).
6. **Capability registry:** REQ-YG-340..346 must be registered in a new capability file (`capabilities/CAP-145-copilot-instrumentation-gap-closure.yaml`) before merging, or `req_coverage.py` flags them as phantom IDs and the pre-commit gate fires.

## Proposed Solution

### In scope

1. **Runner command contract hardening (`copilot_instrument.sh`)**
   - Add required flags to each Copilot invocation:
     - `--output-format json`
     - `--log-dir <phase_dir>/logs`
     - `--log-level debug`
   - Keep existing two-phase `plan` + resumed `implement` flow.
2. **OTel boundary normalization in runner**
   - Export and enforce:
     - `COPILOT_OTEL_EXPORTER_TYPE=file`
     - `COPILOT_OTEL_FILE_EXPORTER_PATH=<phase_dir>/otel.jsonl`
     - `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`
3. **Before/after git snapshots per phase**
   - Capture explicit pre-phase and post-phase snapshots:
     - `git-status-before.txt`, `git-diff-before.patch`
     - `git-status-after.txt`, `git-diff-after.patch`
4. **Expanded normalized event model (`extract_copilot_events.py`)**
   - Add required stable fields:
     - `source` (artifact origin: otel/git)
     - `success` (boolean outcome when derivable)
     - `details` (typed dict for structured payload)
5. **Semantic event extraction**
   - Emit semantic events when observably derivable:
     - `phase_marker` (from `report_intent` span arguments)
     - `test_run` (bash spans containing pytest commands)
     - `lint_run` (bash spans containing ruff/yamlgraph lint commands)
     - `file_create` / `file_edit` (tool spans)
     - `failure` (failed command/tool spans)
     - `retry` (repeated command/tool after a failure on same target)
6. **Documentation boundary clarity**
   - Update `docs/copilot-instrumentation-poc.md` to explicitly separate:
     - raw telemetry spans/log artifacts
     - normalized semantic events
   - Add deterministic conformance-table output contract (columns + ordering rule).
7. **RED acceptance tests for follow-up contract**
   - Add a dedicated FR-364 RED test module with synthetic OTel fixtures and static runner assertions.

### Out of scope

1. CI execution of live Copilot instrumentation runs.
2. Automatic YAMLGraph workflow generation from extracted events.
3. Changes to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult`.

## Requirement IDs (planned)

| REQ ID | Maps to |
| --- | --- |
| REQ-YG-340 | Runner includes required instrumentation flags and phase log directory contract |
| REQ-YG-341 | Runner enforces file-export OTel and message-content capture env vars |
| REQ-YG-342 | Runner emits explicit before/after git snapshots per phase |
| REQ-YG-343 | Event schema includes `source`, `success`, `details` |
| REQ-YG-344 | Extractor emits semantic event classes from observable telemetry patterns |
| REQ-YG-345 | Conformance-table output is deterministic and testable |
| REQ-YG-346 | Docs distinguish raw telemetry artifacts from normalized semantic events |

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-340):** `scripts/copilot_instrument.sh` includes `--output-format json`, `--log-dir`, and `--log-level debug` in both plan and resumed implement Copilot commands.
- [x] **AC-02 (REQ-YG-341):** runner explicitly sets `COPILOT_OTEL_EXPORTER_TYPE=file` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` for phase execution.
- [x] **AC-03 (REQ-YG-342):** each phase directory contains explicit before/after git snapshots (`git-status-before.txt`, `git-diff-before.patch`, `git-status-after.txt`, `git-diff-after.patch`).
- [x] **AC-04 (REQ-YG-343):** `extract_copilot_events.py` event model includes `source`, `success`, and `details` in emitted JSONL.
- [x] **AC-05 (REQ-YG-344):** extractor emits semantic event types (`phase_marker`, `test_run`, `lint_run`, `file_create`, `file_edit`, `failure`, `retry`) when corresponding evidence exists in telemetry fixtures.
- [x] **AC-06 (REQ-YG-345):** extractor (or companion formatter in same script scope) produces deterministic conformance-table output ordering for the same input fixture.
- [x] **AC-07 (REQ-YG-346):** `docs/copilot-instrumentation-poc.md` explicitly documents raw artifact layer vs normalized semantic event layer.
- [x] **AC-08:** FR-364 RED tests are present and fail before implementation for the intended reasons.
- [x] **AC-09 (registry):** `capabilities/CAP-145-copilot-instrumentation-gap-closure.yaml` exists and registers REQ-YG-340..346; `python scripts/req_coverage.py` reports no phantom IDs for this FR.

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py`

Planned RED tests:

1. `test_ac01_runner_includes_required_output_flags_for_both_phases`
2. `test_ac02_runner_sets_file_export_and_message_capture_env_vars`
3. `test_ac03_runner_contract_includes_before_and_after_git_snapshots`
4. `test_ac04_event_schema_includes_source_success_details`
5. `test_ac05_extracts_phase_marker_from_report_intent_span`
6. `test_ac05_extracts_test_lint_file_and_failure_retry_semantic_events`
7. `test_ac06_conformance_table_output_is_deterministic_for_fixture`
8. `test_ac07_docs_separate_raw_spans_from_normalized_events`

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py -q --no-cov
```

All tests in this module must include `@pytest.mark.req(...)` tags mapped to REQ-YG-340..346.

## Alternatives Considered

1. **Keep FR-362 coarse extractor/event schema and analyze manually**
   - Rejected: does not satisfy issue #364 judged follow-up boundary.
2. **Split runner hardening and extractor semantics into separate FRs**
   - Rejected for this issue: the gap report couples these contracts and asks for one complete closure pass.
3. **Use live Copilot runs in tests**
   - Rejected: non-deterministic and unsuitable for fast CI/unit enforcement.

## Related

- GitHub issue #364: <https://github.com/sheikkinen/yamlgraph/issues/364>
- `feature-requests/FR-362-copilot-instrumentation-process-mining-poc.md`
- `scripts/copilot_instrument.sh`
- `scripts/extract_copilot_events.py`
- `tests/unit/test_fr362_copilot_instrumentation_poc_red.py`
- `docs/copilot-instrumentation-poc.md`

## Topic Source Note

Requested source file `.chaplain/processing/gh-364.md` is not present in this worktree snapshot; GitHub issue #364 content was used as source-of-truth topic input.
