# Feature Request: FR-317 Retire Obsolete Watcher2 Components

**Priority:** HIGH
**Type:** Enhancement
**Status:** Draft
**Effort:** 2 days
**Requested:** 2026-05-03

## Summary

Retire watcher2-era chaplain assets that are no longer the operational path, and align prompts, docs, requirement traceability, and tests to the current FSM runtime (`start-system.sh` + dispatcher + pipeline-v2).

## Value Statement

Chaplain maintainers get one truthful architecture surface (FSM runtime) instead of mixed legacy/current paths, reducing false debugging trails and maintenance overhead.

## Problem

Issue #300 is valid in spirit (legacy drift), but codebase research shows the cleanup must be precise:

1. **Runtime entrypoint has moved**: `.chaplain/scripts/start-system.sh` starts `.chaplain/config/watcher-dispatcher.yaml` and `.chaplain/config/watcher-pipeline-v2.yaml`; it does not invoke `.chaplain/watcher2.sh`.
2. **Legacy orchestrator remains**: `.chaplain/watcher2.sh` still exists and references obsolete `step-*.yaml` files.
3. **Not all legacy graph assets are dead**: `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` currently uses `prompts_dir: ../copilot/prompts`, so deleting `.chaplain/graphs/copilot/` requires prompt migration first.
4. **Traceability still encodes old paths**: requirements/capabilities/tests still reference watcher2-era assets (notably REQ-YG-276, REQ-YG-278, REQ-YG-260, REQ-YG-263 and their tied tests).
5. **Some issue-listed cleanup items are already absent** in this worktree (`.chaplain/processing/`, `.chaplain/actions-stub/`, `.chaplain/drafts/`, `.chaplain/inbox-fsm/`, `.chaplain/inbox-integration/`, `.chaplain/inquisitor.log`), so they should not expand implementation scope.

## Research: Existing Patterns and Prior Art

1. **Current operational architecture** already favors FSM startup (`FR-296`, `FR-305`), with tests validating `start-system.sh` and `watcher-pipeline-v2`.
2. **Dead-code retirement precedent** (`FR-278`) shows that removals must include capability, requirement, and test traceability rewiring, not file deletion alone.
3. **Runtime dependency scan** over active chaplain surfaces (`.chaplain/config/`, `.chaplain/actions/`, `.chaplain/lib/watcher/`, `.chaplain/scripts/`) shows no direct dependency on `.chaplain/watcher2.sh` or `.chaplain/graphs/enforce/`.
4. **Coupling scan** shows explicit legacy dependencies in tests/capabilities/docs that must be migrated as part of this FR rather than left broken.

## Objectives

1. Remove obsolete watcher2-era assets with no active architectural role.
2. Preserve current FSM behavior while migrating any still-live prompt dependencies.
3. Reconcile requirement traceability so docs/tests/registry describe the system that actually runs.

## Constraints

1. Preserve dispatcher/pipeline-v2 behavior and action contracts.
2. Keep scope to watcher2-era retirement and directly coupled traceability updates.
3. No speculative cleanup of already-absent artifacts.
4. Fail closed on missing migration targets (no silent fallback to legacy paths).

## Proposed Solution

### In scope

1. Migrate judge prompt dependency off `.chaplain/graphs/copilot/` (update `step-judge-v2.yaml` to a non-legacy prompts path) before deleting legacy graph directory.
2. Migrate any required prompt assets from `.chaplain/graphs/enforce/` to active watcher-era location(s), then remove legacy enforce graph directory.
3. Remove `.chaplain/watcher2.sh` and `.chaplain/test-entry.md`.
4. Update `.chaplain/README.md` and `.chaplain/graphs/philosopher/README.md` to remove legacy instructions/links and anchor runtime usage on `.chaplain/scripts/start-system.sh`.
5. Update coupled requirements/capabilities/tests so removed paths are no longer asserted as canonical behavior.
6. Document forensic/failure workflow mapping after watcher2 removal (where equivalent behavior now lives).

### Out of scope

1. Behavioral redesign of dispatcher/pipeline-v2 flow.
2. Removing `philosopher.sh` or `inquisitor.sh`.
3. New features unrelated to watcher2-era retirement.

## Acceptance Criteria

- [ ] **AC-01:** `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` no longer references `../copilot/prompts`, and required judge prompt content exists at the new active path.
- [ ] **AC-02:** `.chaplain/graphs/copilot/` and `.chaplain/graphs/enforce/` are removed after migration of any still-required prompt artifacts.
- [ ] **AC-03:** `.chaplain/watcher2.sh` and `.chaplain/test-entry.md` are removed.
- [ ] **AC-04:** `.chaplain/README.md` documents `.chaplain/scripts/start-system.sh` as the runtime entrypoint and no longer instructs `.chaplain/watcher2.sh` usage.
- [ ] **AC-05:** `.chaplain/graphs/philosopher/README.md` has no `../copilot/` or `../enforce/` links.
- [ ] **AC-06:** No references to removed paths remain in active chaplain runtime files (`.chaplain/config/`, `.chaplain/actions/`, `.chaplain/lib/watcher/`, `.chaplain/scripts/`, `.chaplain/graphs/watcher-*`).
- [ ] **AC-07:** Requirement/capability traceability for impacted watcher2-era contracts is updated so ARCHITECTURE/capabilities/tests do not point to removed files.
- [ ] **AC-08:** Migration guidance for forensic/failure handling after watcher2 removal is documented in chaplain docs.

## Failing Acceptance Tests (RED)

Expected failing checks before implementation:

```bash
test ! -d .chaplain/graphs/copilot
test ! -d .chaplain/graphs/enforce
test ! -f .chaplain/watcher2.sh
test ! -f .chaplain/test-entry.md
! rg -n 'prompts_dir:\s*\.\./copilot/prompts' .chaplain/graphs/watcher-plan/step-judge-v2.yaml
! rg -n '\.\./(copilot|enforce)/' .chaplain/graphs/philosopher/README.md
! rg -n 'watcher2\.sh' tests/unit/test_chaplain_readme_documentation.py capabilities/CAP-125-pipeline-script-retirement.yaml capabilities/CAP-128-chaplain-documentation.yaml ARCHITECTURE.md
! rg -n '\.chaplain/graphs/(copilot|enforce)' tests/unit/test_acceptance_tests_before_enforce.py tests/unit/test_chaplain_research_step.py tests/unit/test_enforce_simplify.py tests/unit/test_judge_split_verdict.py capabilities/CAP-113-chaplain-research-step.yaml capabilities/CAP-116-acceptance-tests-before-enforce.yaml
```

## Alternatives Considered

1. **Keep legacy files in place with deprecation notes** — Rejected: preserves architecture ambiguity and ongoing traceability drift.
2. **Archive legacy assets under `.chaplain/legacy/`** — Rejected: lowers immediate breakage risk but keeps obsolete contracts alive and prolongs dual-path confusion.
3. **Only remove `watcher2.sh`** — Rejected: leaves legacy graph/test/requirement coupling unresolved.

## Related

- GitHub issue: <https://github.com/sheikkinen/yamlgraph/issues/300>
- `.chaplain/scripts/start-system.sh`
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `feature-requests/FR-278-remove-watcher2-baseline-dead-code.md`
- `tests/unit/test_fr296_watcher_fsm_startup_script.py`
