# Diary: FR-368 watcher2 Multi-Project Routing — Watcher2 Sanity Check

**Date:** 2026-05-11
**FR:** FR-368 — Chaplain Multi-Project MVP: ninchat_voice Routing
**Reviewer:** watcher2 post-validate sanity check

## What Happened

FR-368 adds a second intake lane (`.chaplain/inbox/ninchat_voice/`) alongside the root yamlgraph lane, wires a Pydantic manifest schema for project-specific execution policy, and propagates all contract fields (branch_prefix, work_dir, test_cmd, precommit_config, fr_template, architecture_doc) end-to-end through dispatcher → worktree_setup → plan → validate_gate → capture_fr.

Scope is proportional: 9 acceptance criteria, 728 insertions, 10 passing tests. No dead weight found.

## Trap

**infrastructure_self_exempt** in miniature: the inbox dispatch was previously a bash one-liner inside the dispatcher YAML (`ls -1 {inbox_dir}/*.md | head -1`). Replacing it with a dedicated Python module (`dispatch_topic.py`) is the correct boundary normalization — external intake routing belongs at a typed, testable boundary, not in a shell glob. The trap was avoided: the implementation normalized at entry, not downstream.

A subtler trap was **placeholder_leakage**: when the pipeline's context template `{project}` is not substituted (e.g., pipeline config bug), it would propagate the literal string `{project}` into validate_gate. The `_is_placeholder()` guard addresses this at the validate_gate boundary — correct normalization at the right place.

## Root Cause of Prior Coupling

Single-project coupling was implicit: bash globs hardcoded to one inbox, branch prefix hardcoded in shell, FR capture hardcoded to `feature-requests/FR-*.md`. Each site was independently brittle — no shared contract. The fix (Pydantic `ProjectContext` as a shared type flowing through the pipeline) resolves this systematically.

## What Worked

- **Normalize at the boundary:** `project_contract.py` enforces the manifest schema at load time; placeholder detection guards the validate_gate at runtime. Both are correct boundary choices.
- **TDD structure is clear:** 10 tests map 1:1 to ACs; all green; RED precondition for AC-09 is explicit (`pytest.raises(FileNotFoundError)`).
- **yamlgraph fallback preserved:** `yamlgraph_project_context()` returns well-typed defaults, so the existing lane is untouched at the contract level.

## Concerns (non-blocking)

1. **No `logs/` evidence:** No `fsm-pipeline-*.log` was present in the worktree — end-to-end execution was not captured. Tests verify structural behavior but a live pipeline run has not been logged.
2. **`test_ac05a` checks a source literal:** Asserting `'["pre-commit", "run", "--all-files"]'` exists in the file source is an implementation-detail assertion; a minor fragility if the code is reformatted.
3. **`.chaplain/inbox/ninchat_voice/` not committed:** The directory is created lazily by `dispatch_topic.py`; no `.gitkeep` is committed. Functionally sound but invisible to `git ls-files`.

## Seed

If `dispatch_topic.py` is the canonical routing boundary, should the watcher2 FSM express project routing as an explicit state transition (e.g., `routing_yamlgraph` vs `routing_ninchat_voice`) rather than opaque context keys, so pipeline state diagrams become self-documenting?
