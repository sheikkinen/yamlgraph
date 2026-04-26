# Feature Request: FR-288 watcher2 hook preflight gate — guard enforcement infrastructure

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-26

## Summary

Add an explicit git-hook integrity gate to watcher2 preflight so the daemon refuses to process inbox items when local hook enforcement is disabled or broken.

## Value Statement

Watcher2 operators get fail-closed protection for enforcement infrastructure, preventing silent bypass of pre-commit and commit-msg gates.

## Problem

`core.hooksPath` was set to an empty value in local git config, which disabled hooks without visible failure. As a result, commits bypassed pre-commit and commit-msg validation and watcher2 continued operating as if enforcement was active.

Current gap:

1. `.chaplain/lib/watcher/preflight.sh` validates branch/worktree/python state but does not validate hook configuration.
2. `.chaplain/watcher2.sh` depends on preflight to block unsafe cycles; without a hook check, the guardrail itself can be bypassed silently.
3. `.chaplain/README.md` documents hooks as required, but no executable check enforces that requirement.

## Objectives

1. Detect hook-path misconfiguration before watcher2 runs plan/enforce steps.
2. Verify required hooks (`pre-commit`, `commit-msg`) exist and are executable.
3. Fail closed with actionable error messages when hook integrity is broken.

## Constraints

- Scope is limited to watcher2 shell orchestration under `.chaplain/`; no YAMLGraph runtime changes.
- Keep checks local and deterministic (git config + filesystem); do not require network calls.
- Preserve existing watcher2 control flow: failed preflight must stop the cycle and route through existing failure handling.
- Do not add expensive preflight work (e.g., `pre-commit run --all-files`) in this FR.

## Research Findings

- `preflight()` currently checks main branch, pulls latest, prunes worktrees, and validates editable install; it has no hook validation.
- Watcher2 already has a strict preflight boundary (`if ! preflight; then handle_failure "preflight"`), so hook checks can be added with minimal orchestration changes.
- Existing watcher shell guards use explicit return codes and clear logs (`dedup_gate`, `worktree_setup`), which is the right pattern for this gate.
- `.chaplain/README.md` already claims hooks are required, confirming documentation/behavior drift that this FR should close.

## Proposed Solution

Implement hook integrity validation inside `preflight.sh` and keep watcher2 orchestration unchanged except for consuming clearer preflight failures.

### 1. Add hook validation to `.chaplain/lib/watcher/preflight.sh`

Add a focused helper (or inline preflight block) that:

1. Reads local `core.hooksPath` with `git config --local --get core.hooksPath`.
2. Accepts only:
   - unset `core.hooksPath`, or
   - explicit default path to repo hooks (`.git/hooks` with optional trailing slash).
3. Fails preflight when `core.hooksPath` is empty or points elsewhere.
4. Resolves the actual hooks directory (`git rev-parse --git-path hooks`) and verifies:
   - `pre-commit` exists and is executable,
   - `commit-msg` exists and is executable.
5. Logs concrete remediation commands on failure:
   - `git config --local --unset core.hooksPath`
   - `pre-commit install`
   - `pre-commit install --hook-type commit-msg`

### 2. Keep watcher2 fail-closed behavior at existing boundary

Reuse current watcher2 flow:

- `preflight` returns non-zero on hook validation failure.
- watcher2 calls `handle_failure "preflight"` and refuses to process the topic further.
- No plan/enforce steps run when hook integrity fails.

### 3. Update watcher2 operator docs

Update `.chaplain/README.md` preflight section to describe:

- hook-path validation contract,
- required hook files and execute-bit requirement,
- failure behavior and remediation commands.

## Acceptance Criteria

- [ ] **AC-01:** `preflight.sh` validates `core.hooksPath` before reporting "Preflight complete".
- [ ] **AC-02:** `preflight.sh` fails when `core.hooksPath` is explicitly empty.
- [ ] **AC-03:** `preflight.sh` fails when `core.hooksPath` is set to a non-default location.
- [ ] **AC-04:** `preflight.sh` verifies `pre-commit` and `commit-msg` exist and are executable in the resolved hooks directory.
- [ ] **AC-05:** Hook validation failures emit actionable remediation commands in logs.
- [ ] **AC-06:** On hook validation failure, watcher2 does not execute plan/research/acceptance/judge/enforce steps for that cycle.
- [ ] **AC-07:** Existing behavior is unchanged when hooks are correctly configured and executable.
- [ ] **AC-08:** Unit tests are added in `tests/unit/test_fr288_watcher2_hook_preflight_gate.py` covering misconfigured hooksPath, missing/non-executable hooks, and healthy pass-through.
- [ ] **AC-09:** `.chaplain/README.md` is updated with the enforced hook preflight contract.

## Alternatives Considered

1. **Run `pre-commit run --all-files` in preflight:** Rejected. Too expensive for every cycle and conflates integrity checks with full lint/test execution.
2. **Rely on CI/PR checks only:** Rejected. Detects violations too late and does not protect local watcher2 automation.
3. **Check only hook file existence (ignore executable bit):** Rejected. Non-executable hooks are effectively disabled and must fail the gate.

## Related

- Issue #235
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/preflight.sh`
- `.chaplain/README.md`
- `.chaplain/lib/watcher/dedup_gate.sh`
- `.chaplain/lib/watcher/worktree_setup.sh`
