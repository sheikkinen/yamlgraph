# Reflection: FR-383 Copilot Node Backend API Fallback — Watcher2 Sanity Check

**Date:** 2026-05-14
**FR:** FR-383 — Copilot node `backend: api` fallback
**Reviewer:** watcher2 (post-validate sanity check)

## What Happened

FR-383 adds a `backend: api` execution path to `type: copilot` nodes so
reasoning-only steps can run through `execute_prompt()` instead of always
spawning the Copilot CLI subprocess. The implementation was reviewed
post-validation.

Key deliverables verified:
- `copilot_node.py` now branches on `backend` value at node creation time.
- `copilot_runtime.py` (new, 192 lines) extracts CLI-specific helpers cleanly,
  leaving the node orchestration file focused on routing logic.
- `linter/patterns/copilot.py` gains backend-aware checks: `W-COPILOT-API-MODEL`
  (no model signal) and `E-COPILOT-API-FLAGS` (CLI-only flags in API mode).
- All 7 acceptance criteria confirmed implemented and tested.
- 13 new acceptance tests pass; 3726 unit tests pass with no regressions.

## Trap

**`downstream_fix` near-miss.** The module-level `load_prompt` alias in
`copilot_node.py` carries the comment "Backward-compatible patch target for
tests mocking prompt loading." The word "Backward-compatible" signals the
spirit of reluctance-to-refactor the doctrine forbids — even though it doesn't
trigger the pre-commit gate (case mismatch, hyphen vs. space). The actual
pattern is a legitimate test-seam, but the naming betrays the trap: a shim was
added to keep external tests passing rather than moving the patch target to the
new canonical location (`copilot_runtime.py`).

## Root Cause

Tests historically patched `yamlgraph.node_factory.copilot_node.load_prompt`.
When CLI logic was extracted to `copilot_runtime.py`, the `load_prompt` symbol
moved. Rather than updating every test mock to point at the new module, an
alias was re-exported from `copilot_node.py` with a compat comment. The
extraction was structurally correct; the comment was the tell.

## What Worked

- **Boundary decomposition was clean.** `_execute_cli` lives in `copilot_runtime.py`;
  `_execute_api` lives inline in `copilot_node.py`; the node factory routes
  between them. No cross-contamination.
- **Behavioral assertions prevail.** Tests assert `mock_run.assert_not_called()`,
  `output.backend == "api"`, and `output.session_id is None` — not implementation
  internals.
- **Lint rules are early-exit for API backend.** `return issues` after backend
  checks prevents applying CLI-specific session-flag rules to API-mode nodes,
  avoiding false positives cleanly.
- **All 7 AC satisfied.** Traceability from FR → test → code is intact.

## Seed

Seed: When a module is extracted for separation of concerns but a symbol alias is
re-exported for test-seam compatibility, what would a "boundary inventory" step
look like that inventories all mock patch targets at refactor time — so the
re-export can be eliminated before it hardens into permanent compat debt?
