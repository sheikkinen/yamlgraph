# Judgement: FR-1066 Exit code reflects errors

**Prior art:** the only hit is `FR-1066-exit-code-reflects-errors.md`, the FR this judgement governs; its own prior-art line dispositions FR-677 and FR-827.

**Verdict:** REJECTED — exit status matters, but this newly filed FR lacks substantive research and defines a completion path that existing `on_error: fail` cannot reach.

**Reviewed against:** `feature-requests/FR-1066-exit-code-reflects-errors.md`; `feature-requests/FR-1064-map-branch-contract.md`; `docs/issues-2026-09-24.md`; `yamlgraph/cli/graph_commands.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The witnessed exit-0-with-errors run is concrete (plan section 1.2; FR-1066:8-14), and a distinct completed-with-errors code is mechanically checkable. This is a CLI boundary correction to existing graph execution, with scripts and CI as named consumers (FR-1066:22-42). It need not change every map consumer.

## Required revisions

### R-1: Re-file with research satisfying the active gate

Commit four to six genuine solution classes for signaling partial completion, precedent for each, dissent and an `is_this_a_graph` answer. FR-1066:75-80 lists three rejected variants of one exit-code decision; plan section 7 B identifies the `skip` ambiguity but does not compare solution classes. No authority is possible under the judge doctrine's research gate.

### R-2: Pin reachable exit paths and tolerated-error representation

FR-1066:64-67 proposes a failing `on_error: fail` node as an exit-3 witness, yet a raised failure exits through the existing exception path (`yamlgraph/cli/graph_commands.py:242-266`) as 1. Test a completed graph that returns non-tolerated `errors`, not an uncaught exception; keep crash/refusal at 1. Define a typed tolerated marker where `PipelineError` is constructed rather than changing downstream counting by message text; test mixed tolerated and non-tolerated errors and interrupted/streaming modes. Decide whether JSON `error_count` means all recorded or only exit-affecting errors, and use the same definition in `run_end`.

### R-3: Keep output intact before exit

Define the order of success output, optional exports, telemetry and `sys.exit(3)`; exiting before `_handle_optional_exports` (CLI:243-251) would contradict "completed" and discard outputs. Name the affected shell consumers and require an explicit human decision about whether exit 3 must stop their pipelines (FR-1066:70-72). Do not infer global tolerance from the map's `min_success` alone.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Rejected FR-1066 disposition; researched replacement CLI-status FR |

Not authorized: CLI exit changes, `PipelineError` schema changes, telemetry changes or bulk script rewrites under FR-1066.

## Revised acceptance criteria

- [ ] AC-01: Replacement cites committed substantive research, including dissent and `is_this_a_graph`.
- [ ] AC-02: RED tests distinguish completed non-tolerated errors (3), all-tolerated errors (0), mixed errors (3), uncaught exceptions (1), and interrupts in JSON and text modes.
- [ ] AC-03: The replacement freezes telemetry and JSON count semantics and proves output/export happens before exit 3.
- [ ] AC-04: A named list of script callers records the human-approved treatment of exit 3.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No code changes under this rejected FR; judge a new research-backed FR. | GATE |
| C-2 | A completed-with-errors status cannot be tested with a path that raises before completion. | GATE |

Authority granted: none under FR-1066.
