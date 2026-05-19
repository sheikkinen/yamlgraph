# Feature Request: FR-412 watcher2 micro-remediation fast path before validate gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-19

## Summary

Add a cheap pre-gate remediation path in watcher2 so post-enforce flow runs deterministic micro-steps (changelog + commit-title repair) before invoking expensive `validate_fix`. Keep `validate_fix` as fallback for complex or unexpected failures.

## Value Statement

Watcher operators get faster, lower-cost iterations because common deterministic failures are repaired before the Opus-backed remediation session is used.

## Problem

Current watcher2 v2 flow always enters `validate_fix` immediately after `enforce_session`, even on runs that only need small deterministic repairs:

```text
enforce_session -> validate_fix -> sanity_check -> validate_gate -> done
```

`validate_fix` currently runs a Copilot session configured with `claude-opus-4.6`, while `validate_gate` already performs deterministic checks for commit title, branch freshness, pre-commit, and diary parity. This makes common mechanical failures expensive and can amplify retry-loop latency.

## Research Findings

1. **Topic file missing in this worktree snapshot.**
   Requested source `.chaplain/processing/gh-412.md` is absent; GitHub issue #412 was used as canonical topic input.

2. **`validate_fix` is unconditional on happy path today.**
   `.chaplain/config/watcher-pipeline-v2.yaml` routes `enforce_session --enforce_done--> validate_fix`.

3. **`validate_gate` already owns deterministic CI-parity checks.**
   `.chaplain/actions/validate_gate_action.py` enforces pre-commit, title contract, branch freshness, and diary parity with bounded retries.

4. **Deterministic changelog generation already exists as reusable action.**
   `.chaplain/actions/changelog_gen_action.py` can generate missing fragments from FR metadata, but is not wired into current `watcher-pipeline-v2.yaml`.

5. **Prior art exists for deterministic pre-fix optimization.**
   FR-283 and FR-198 (legacy watcher2 runtime) used deterministic pre-processing to reduce expensive remediation churn.

6. **Current architecture contract to preserve.**
   `ARCHITECTURE.md` REQ-YG-318 defines validate split ownership (`validate_fix` remediation + deterministic `validate_gate`); this change must preserve gate semantics and bounded retry behavior.

## Objectives

1. Remove unconditional entry into expensive `validate_fix` on the first post-enforce pass.
2. Pre-solve two high-frequency deterministic failures before gate validation:
   - missing changelog fragment
   - invalid commit title contract
3. Preserve `validate_fix` as fallback for failures not solved by micro-steps.
4. Keep existing deterministic gate behavior and retry ceiling intact.

## Constraints

1. Minimal scope: only **two** micro-steps (changelog + commit title) in this FR.
2. No weakening of `validate_gate` contracts or retry limits.
3. No new external dependencies.
4. Micro-steps must be idempotent and safe on repeated retries.
5. Preserve existing terminal/error semantics (`error -> failed`, bounded `fix_needed` loop).

## Proposed Solution

### FSM flow update

```text
setup -> plan -> capture_fr -> judge -> enforce_session
                                             | enforce_done
                                             v
                                      micro_changelog
                                             | changelog_done
                                             v
                                       micro_title
                                             | title_done
                                             v
                                       sanity_check
                                             | pass/warn
                                             v
                                      validate_gate -> done
                                             | fix_needed
                                             v
                                         validate_fix
                                             | validate_done
                                             v
                                       sanity_check (loop)
```

> **Design note — event names must be explicit in YAML config.**
> `micro_changelog` emits `changelog_done` on success and `error` on failure (routes to `validate_fix`).
> `micro_title` emits `title_done` on success and `error` on failure (routes to `validate_fix`).
> These names must appear verbatim in the updated `watcher-pipeline-v2.yaml` events and transitions.

### In scope

1. Add `micro_changelog` state after `enforce_session` using existing `changelog_gen` action.
2. Add `micro_title` state after `micro_changelog` using deterministic bash remediation (amend latest commit title when contract is violated, including `feat` + `FR-XXX` rule).
3. Route micro-step failures to `validate_fix` fallback (not direct terminal failure) so existing heavy remediation remains safety net.
4. Remove direct happy-path transition from `enforce_session` to `validate_fix`.
5. Add focused unit acceptance tests for the new FSM contract and action wiring.

### Out of scope (explicitly deferred)

1. Micro rebase step.
2. Micro ruff auto-fix step.
3. Diary micro-writer step.
4. Req-coverage marker auto-injection.
5. Changing `validate_fix` model selection or prompt ownership boundaries.

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` defines `micro_changelog` and `micro_title` states.
- [x] **AC-02:** Happy-path transition is `enforce_session -> micro_changelog -> micro_title -> sanity_check -> validate_gate -> done`.
- [x] **AC-03:** Direct transition `enforce_session -> validate_fix` is removed from happy path.
- [x] **AC-04:** `validate_gate --fix_needed--> validate_fix` remains unchanged as fallback loop.
- [x] **AC-05:** `micro_changelog` uses deterministic `changelog_gen` action and is idempotent (no duplicate fragment generation on retries).
- [x] **AC-06:** `micro_title` performs deterministic commit-title contract repair (Conventional Commit + `feat` requires `FR-XXX`) via amend when needed.
- [x] **AC-07:** Each micro-step has independent timeout and explicit failure routing to `validate_fix`.
- [x] **AC-08:** `validate_gate` check set and `max_attempts` contract remain unchanged.
- [x] **AC-09:** New/updated tests are requirement-tagged and requirement traceability docs are updated (`ARCHITECTURE.md` + `scripts/req_coverage.py`).
- [x] **AC-10:** Chaplain pipeline documentation is updated for new post-enforce flow.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py`

Planned RED tests:

1. `test_ac01_adds_micro_changelog_and_micro_title_states`
2. `test_ac02_routes_happy_path_through_micro_steps_before_sanity_and_gate`
3. `test_ac03_removes_direct_enforce_to_validate_fix_happy_path_edge`
4. `test_ac04_preserves_validate_gate_fix_needed_fallback_to_validate_fix`
5. `test_ac05_micro_changelog_uses_changelog_gen_action_contract`
6. `test_ac06_micro_title_action_repairs_title_contract_deterministically`
7. `test_ac07_micro_steps_have_independent_timeouts_and_fallback_error_routes`
8. `test_ac08_validate_gate_contract_unchanged_after_micro_step_insertion`

RED command:

```bash
pytest tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py -q --no-cov
```

## Alternatives Considered

1. **Keep current `enforce_session -> validate_fix` ordering**
   Rejected: preserves unnecessary Opus invocations for deterministic failures.

2. **Implement all proposed micro-steps in one FR (changelog/title/rebase/ruff/diary/req-markers)**
   Rejected: too broad for a single-responsibility change and increases regression risk.

3. **Move micro-remediation into `validate_gate_action.py`**
   Rejected: mixes deterministic judgement with mutating repair side effects, weakening separation of concerns.

4. **Only downgrade `validate_fix` model cost tier**
   Rejected: lowers unit cost but does not remove avoidable invocation volume.

## Related

- Issue #412: <https://github.com/sheikkinen/yamlgraph/issues/412>
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/actions/validate_gate_action.py`
- `.chaplain/actions/changelog_gen_action.py`
- `.chaplain/graphs/watcher-enforce/validate-session.yaml`
- `feature-requests/FR-316-watcher2-validate-split-fix-gate.md`
- `feature-requests/FR-390-watcher-validate-fix-context-and-sanity-timeout.md`
- `ARCHITECTURE.md` (REQ-YG-318)
