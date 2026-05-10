# Feature Request: FR-362 Copilot instrumentation process-mining POC

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-10

## Summary

Instrument one two-phase Copilot run (`plan` -> resumed `implement`) against the Minesweeper target and extract normalized process events that reveal which execution steps are deterministic enough for YAMLGraph workflow generation.

## Value Statement

Maintainers gain concrete, local evidence of Copilot execution behavior (steps, retries, validation gates, diffs) so future automation can promote stable phases into explicit YAMLGraph nodes instead of relying on opaque agent transcripts.

## Problem

Copilot implementation behavior is currently spread across transient sources (CLI output, logs, OTel spans, session markdown, git diff). We can inspect results manually, but we cannot reliably answer:

1. What sequence of actions actually happened in `plan` and `implement`?
2. Which steps repeated despite `--resume`?
3. Which phases are stable enough to codify as `python`/`tool`/`agent`/`router` nodes?

Without a minimal extraction contract, process-mining remains anecdotal and non-repeatable.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Session continuation is already a proven pattern.**
   - `yamlgraph/node_factory/copilot_node.py` supports `--resume` and session handoff.
   - `examples/demos/session-continuation/graph.yaml` and `examples/bugfix/graph.yaml` already model multi-phase continuation.
2. **Minesweeper is a stable smoke-test target.**
   - `feature-requests/FR-082-minesweeper-game.md` is implemented and provides known acceptance shape.
3. **Sensitive local artifact storage already has an approved boundary.**
   - `.gitignore` excludes `outputs/`, allowing raw run artifacts to stay local-only.
4. **Problem is not solved yet in this worktree.**
   - No `scripts/copilot_instrument.sh`.
   - No `scripts/extract_copilot_events.py`.
   - No committed process-mining findings document for this POC.
5. **Issue source alignment.**
   - GitHub issue #362 explicitly requests these three deliverables and points to this FR path.
   - `.chaplain/processing/gh-362.md` is absent in this worktree; issue #362 body is used as source-of-truth topic input.

## Objectives

1. Capture a reproducible two-phase Copilot run with durable local artifacts.
2. Convert raw artifacts into normalized JSONL process events with a typed boundary model.
3. Document what was learned and which YAMLGraph node types are candidates for future codification.

## Constraints

1. **Single responsibility:** local instrumentation POC only.
2. **No framework integration in this FR:** no changes to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult`.
3. **Safety boundary:** `copilot_instrument.sh` creates and runs inside a disposable worktree. Do not push or merge FROM that disposable instrumentation worktree. The script and extractor themselves ARE committed to the feature branch and merged normally.
4. **Data boundary:** raw OTel/log/session/diff artifacts remain local under gitignored output paths.
5. **Judgeability:** acceptance criteria must be mechanically testable, and RED tests must fail before implementation.

## Proposed Solution

Deliver exactly three planning targets:

1. **Run script**: `scripts/copilot_instrument.sh`
   - Creates disposable worktree.
   - Runs `plan` and resumed `implement`.
   - Captures per-phase artifacts:
     - prompt
     - stdout JSONL
     - stderr log
     - `--share` markdown
     - OTel JSONL
     - Copilot debug logs
     - git status and diff snapshots
2. **Extractor**: `scripts/extract_copilot_events.py`
   - Reads one run directory.
   - Emits normalized JSONL events from at least:
     - OTel span artifacts
     - git diff artifacts
   - Validates event shape with Pydantic model.
3. **Findings doc**: `docs/copilot-instrumentation-poc.md`
   - Summarizes observed event sequence and repeated phases.
   - Identifies candidate YAMLGraph node classes (`llm`, `agent`, `python`, `tool`, `map`, `router`, `copilot`) for follow-up FR scope.

## In Scope

1. Local POC script(s), extractor, and findings documentation.
2. Unit-level RED tests that define expected deliverable contracts.
3. Manual local run procedure and artifact directory contract.

## Out of Scope

1. CI automation of live Copilot runs.
2. Changes to YAMLGraph runtime node behavior.
3. Automatic conformance scoring engine.
4. Remote telemetry export.

## Acceptance Criteria

- [x] `scripts/copilot_instrument.sh` exists with documented usage for `plan` and resumed `implement` phases.
- [x] Run artifacts are written to `outputs/copilot-instrumentation/<run-id>/...` and include OTel JSONL, CLI JSONL output, `--share` markdown, stderr logs, and git diff/status snapshots.
- [x] Script enforces disposable worktree usage and includes cleanup steps.
- [x] `scripts/extract_copilot_events.py` exists and emits JSONL events from a run directory.
- [x] Extracted events validate against a Pydantic model with at least: `case_id`, `phase`, `event_type`, `timestamp`, `summary`.
- [x] Extractor handles at minimum OTel span data and git diff-derived events.
- [x] `docs/copilot-instrumentation-poc.md` exists and records findings + candidate YAMLGraph node types.
- [x] No changes are made to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult` in this FR.

## Failing Acceptance Tests (RED)

Planned RED test artifact:

- `tests/unit/test_fr362_copilot_instrumentation_poc_red.py`

Planned RED tests (all expected to fail before implementation):

1. `test_instrument_script_exists_and_defines_two_phase_contract`
   - Assert `scripts/copilot_instrument.sh` exists.
   - Assert script text contains phase labels (`plan`, `implement`) and `--resume` usage.
2. `test_extractor_exists_and_emits_pydantic_valid_events`
   - Import `scripts/extract_copilot_events.py` entry point.
   - Run against minimal synthetic run fixture.
   - Assert JSONL output rows parse as event model instances.
3. `test_findings_doc_exists_with_required_sections`
   - Assert `docs/copilot-instrumentation-poc.md` exists.
   - Assert required headings: `Captured Artifacts`, `Observed Event Sequence`, `Candidate Node Types`, `Next FR`.

Required test markers:

- `@pytest.mark.req("REQ-YG-105")` on session-resume contract tests.
- `@pytest.mark.req("REQ-YG-047")` on observability/extraction contract tests.

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr362_copilot_instrumentation_poc_red.py -q --no-cov
```

## Alternatives Considered

1. **Use only `--share` markdown as evidence**
   - Rejected: insufficient granularity for process-mining event sequence.
2. **Use only git diff/status**
   - Rejected: captures outcome, not step-by-step execution semantics.
3. **Instrument `type: copilot` runtime directly first**
   - Rejected for this scope: framework changes should follow POC evidence.
4. **Remote OTel collector first**
   - Rejected: unnecessary risk and complexity before local proof-of-value.

## Related

- Issue #362: <https://github.com/sheikkinen/yamlgraph/issues/362>
- `feature-requests/FR-082-minesweeper-game.md`
- `feature-requests/FR-168-cross-graph-session-continuity.md`
- `feature-requests/FR-274-copilot-session-id-extraction.md`
- `examples/demos/session-continuation/graph.yaml`
- `examples/bugfix/graph.yaml`
- `yamlgraph/node_factory/copilot_node.py`
