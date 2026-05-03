# Feature Request: FR-320 Retire validate-fsm-single Harness

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Retire `.chaplain/scripts/validate-fsm-single.sh` and remove its stale references from planning artifacts so the repository reflects the current operational path (`.chaplain/scripts/start-system.sh` + dispatcher + pipeline-v2).

## Value Statement

Chaplain maintainers get one truthful runtime story, reducing false confidence from an uncalled, drifted validation script that no longer matches production behavior.

## Problem

GitHub issue #309 identifies `validate-fsm-single.sh` as a drifted Phase 2 artifact that now misrepresents system health:

1. **Wrong inbox contract in practice:** script hardcodes `.chaplain/inbox-fsm` (`.chaplain/scripts/validate-fsm-single.sh:11`) while the active dispatcher default is `.chaplain/inbox` (`.chaplain/config/watcher-dispatcher.yaml:12`), and `.chaplain/inbox-fsm/` is absent in this worktree.
2. **Bypasses runtime entrypoint:** script invokes `statemachine` directly (`.chaplain/scripts/validate-fsm-single.sh:68`) instead of the canonical startup flow documented in `.chaplain/README.md` (`.chaplain/scripts/start-system.sh`).
3. **Fragile kill-based lifecycle:** completion is inferred via log grep + PID kill loop (`.chaplain/scripts/validate-fsm-single.sh:83-103`) rather than managed startup/shutdown phases.
4. **Error false positives:** log check greps `error|traceback|exception` (`.chaplain/scripts/validate-fsm-single.sh:133`), which can match routine FSM event text (`error` as an event name).
5. **No-op generated topic:** default test text requests `YAMLGraph` -> `YAMLGraph` replacement (`.chaplain/scripts/validate-fsm-single.sh:29`), providing weak signal.
6. **No automation callers:** no references were found in `.github/`, `.pre-commit-config.yaml`, or `scripts/`; usage is documentation-only drift.

## Research: Existing Patterns and Prior Art

1. **Canonical runtime path already exists and is tested.**
   - `.chaplain/README.md` declares `.chaplain/scripts/start-system.sh` as entrypoint.
   - `tests/unit/test_fr296_watcher_fsm_startup_script.py` enforces startup script structure.

2. **Legacy validation narrative remains in planning artifacts.**
   - `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
   - `feature-requests/FR-300-full-pipeline-run-logging-verification.md`
   - `feature-requests/FR-FSM-015-watcher2-pipeline-logging.md`
   - `docs/plan-watcher-fsm.md`
   - `changelog/0.4.74/fr-295-phase2-validation.md`

3. **FR-317 explicitly left this as out of scope.**
   - `feature-requests/FR-317-retire-obsolete-watcher2-components.md` marks removing `validate-fsm-single.sh` as out-of-scope, matching issue #309's request to promote it into a dedicated scope.

4. **Topic source file is missing in this worktree.**
   - Requested source `.chaplain/processing/gh-309.md` is absent; canonical source used for this draft is GitHub issue #309.

## Objectives

1. Remove the obsolete `validate-fsm-single.sh` harness.
2. Remove stale references that present the harness as an active validation path in feature-request/changelog planning artifacts.
3. Keep runtime behavior unchanged by anchoring on existing `start-system.sh` flow.

## Constraints

1. Scope is limited to retirement cleanup and directly coupled references.
2. Do not introduce a new smoke-test harness in this FR (tracked as a separate effort).
3. No dispatcher/pipeline FSM topology changes.
4. Preserve architectural source of truth: `.chaplain/scripts/start-system.sh`.

## Proposed Solution

1. Delete `.chaplain/scripts/validate-fsm-single.sh`.
2. Remove or rewrite stale references to `validate-fsm-single.sh` in:
   - `feature-requests/` planning documents,
   - `changelog/` entries that currently present it as active guidance,
   - `docs/plan-watcher-fsm.md`.
3. Remove directly coupled FR-300 acceptance-test artifact that hard-requires this retired script (`tests/unit/test_fr300_full_pipeline_run_logging_verification.py`) or rewrite it to no longer reference the retired harness.
4. Update `feature-requests/FR-317-retire-obsolete-watcher2-components.md` to cross-reference FR-320 as the in-scope retirement unit.

## Acceptance Criteria

- [x] **AC-01:** `.chaplain/scripts/validate-fsm-single.sh` is removed.
- [x] **AC-02:** `rg -n 'validate-fsm-single\.sh' feature-requests --glob '*.md'` returns no matches (except FR-320 historical mention if retained during drafting).
- [x] **AC-03:** `rg -n 'validate-fsm-single\.sh' changelog --glob '*.md'` returns no matches.
- [x] **AC-04:** `docs/plan-watcher-fsm.md` no longer documents `validate-fsm-single.sh` as a validation path.
- [x] **AC-05:** No test file in `tests/` asserts contracts tied to the retired script path.
- [x] **AC-06:** `.chaplain/README.md` continues to present `start-system.sh` as runtime entrypoint.
- [x] **AC-07:** `feature-requests/FR-317-retire-obsolete-watcher2-components.md` no longer lists `validate-fsm-single.sh` retirement as out-of-scope.

## Failing Acceptance Tests (RED)

Expected to fail before implementation:

```bash
test ! -f .chaplain/scripts/validate-fsm-single.sh
! rg -n 'validate-fsm-single\.sh' feature-requests --glob '*.md'
! rg -n 'validate-fsm-single\.sh' changelog --glob '*.md'
! rg -n 'validate-fsm-single\.sh' docs/plan-watcher-fsm.md
test ! -f tests/unit/test_fr300_full_pipeline_run_logging_verification.py
```

## Alternatives Considered

1. **Patch the script instead of retiring it**
   Rejected: keeps dual runtime surfaces and ongoing drift risk.

2. **Replace with a new `start-system.sh` smoke harness in the same FR**
   Rejected: mixes cleanup with new feature work; separate FR keeps this unit minimal and judgeable.

3. **Keep references for historical narrative only**
   Rejected for planning artifacts that are still consumed operationally; stale guidance should be removed or rewritten to explicit retirement context.

## Related

- GitHub issue #309: <https://github.com/sheikkinen/yamlgraph/issues/309>
- `.chaplain/scripts/validate-fsm-single.sh`
- `.chaplain/scripts/start-system.sh`
- `.chaplain/config/watcher-dispatcher.yaml`
- `feature-requests/FR-317-retire-obsolete-watcher2-components.md`
- `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
- `feature-requests/FR-300-full-pipeline-run-logging-verification.md`
- `changelog/0.4.74/fr-295-phase2-validation.md`
