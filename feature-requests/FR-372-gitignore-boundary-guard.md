# Feature Request: FR-372 gitignore boundary guard for pre-commit

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-12

## Summary

Add a pre-commit guard that blocks staged changes to any `.gitignore` file unless an explicit, documented, human-intent bypass path is used.

## Value Statement

Repository maintainers keep ignore-boundary changes rare, visible, and deliberate, reducing accidental privacy/safety boundary drift from routine automation and agent flows.

## Problem

Issue #372 requests a safety gate after the incident documented in `docs/diary/2026-05-12-private-repo-dataloss-recovery.md`.

Today, `.gitignore` can be modified in normal commit flow with no dedicated guard. In this repository, ignore rules define boundary behavior for sensitive and local-only artifacts (for example `tmp/`, `.chaplain/processing/`, `.chaplain/failed/`, `projects/`, generated logs). A casual ignore-rule change can silently alter what is tracked, exposed, or excluded.

The requested behavior is to make `.gitignore` changes exceptional rather than impossible.

## Research Findings

1. **Problem is not solved currently.**
   - `.pre-commit-config.yaml` has many local enforcement hooks, but none block `.gitignore` edits.

2. **Established in-repo pattern exists for staged-file guards.**
   - `scripts/check_demo_proof.sh` uses `git diff --cached --name-only` and emits clear, actionable failure output.
   - This is a direct prior-art pattern for a file-boundary pre-commit gate.

3. **Established test strategy exists for hook + script + config coupling.**
   - `tests/unit/test_ci_demo_proof_gate.py` validates shell behavior in temp repos plus pre-commit registration.
   - `tests/unit/test_precommit_hooks.py` validates hook contract semantics and failure messaging.

4. **Boundary-risk precedent is explicit in repository doctrine.**
   - `docs/diary/2026-05-12-private-repo-dataloss-recovery.md` identifies workspace/repository boundary confusion and untracked-file loss risk.

5. **Scope can remain local and minimal.**
   - The change is confined to pre-commit infrastructure (`scripts/`, `.pre-commit-config.yaml`, tests, docs), with no YAMLGraph runtime or graph execution impact.

## Objectives

1. Block commits that stage `.gitignore` changes by default.
2. Provide an explicit non-`--no-verify` bypass path for intentional human changes.
3. Explain *why* the guard exists in failure output, including diary reference.
4. Preserve normal commit flow when no `.gitignore` files are staged.

## Constraints

- Scope limited to local hook infrastructure and directly coupled tests/docs.
- Guard should match any staged `.gitignore` path (root and nested), not only root.
- Bypass must require explicit intent and be documented; `--no-verify` is not an allowed documented path.
- No changes to watcher FSM behavior, YAML graph contracts, or core runtime modules.

## Proposed Solution

### 1. Add a dedicated pre-commit script

Create `scripts/check_gitignore_boundary.sh`:

- Read staged paths via `git diff --cached --name-only --diff-filter=ACMR`.
- Detect staged `.gitignore` paths with `(^|/)\.gitignore$`.
- Exit `0` when none are staged.
- On match, fail with clear boundary-warning text and diary reference.
- Print a documented explicit bypass command that does not use `--no-verify`.

### 2. Register as a local pre-commit hook

Add hook in `.pre-commit-config.yaml`:

- `id: gitignore-boundary-guard`
- `entry: scripts/check_gitignore_boundary.sh`
- `language: script`
- `stages: [pre-commit]`
- `pass_filenames: false`

### 3. Define explicit bypass contract

Bypass is accepted only when explicit intent is present, for example:

```bash
YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1 \
YAMLGRAPH_GITIGNORE_REASON="FR-372 adjust ignore boundary for <reason>" \
git commit
```

Guard behavior for bypass:

- Allow only when both env vars are set.
- Require non-empty reason containing a trace token (`FR-` or `gh-`).
- Emit a visible warning that bypass was used.
- If bypass flag is set without valid reason, fail closed.

### 4. Document operator usage

Document the guard purpose and bypass contract in reference docs (`reference/break-glass.md` or equivalent enforcement reference) and link the incident diary.

## Acceptance Criteria

- [x] **AC-01:** Staged root `.gitignore` change fails pre-commit by default.
- [x] **AC-02:** Staged nested `.gitignore` change (for example `.chaplain/.gitignore`) fails pre-commit by default.
- [x] **AC-03:** Commits with no staged `.gitignore` files pass this guard.
- [x] **AC-04:** Failure output explains ignore-boundary risk and cites `docs/diary/2026-05-12-private-repo-dataloss-recovery.md`.
- [x] **AC-05:** Guard is registered as `gitignore-boundary-guard` in `.pre-commit-config.yaml` at `pre-commit` stage.
- [x] **AC-06:** Documented bypass path works only with explicit `YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1` and valid `YAMLGRAPH_GITIGNORE_REASON`.
- [x] **AC-07:** Bypass flag without valid reason fails (no silent pass).
- [x] **AC-08:** Focused unit tests are added for script behavior and hook registration.
- [x] **AC-09:** Reference documentation includes the bypass contract and explicitly disallows `--no-verify` as the normal path.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr372_gitignore_boundary_guard.py`

Test cases:

1. `test_ac01_root_gitignore_staged_fails`
2. `test_ac02_nested_gitignore_staged_fails`
3. `test_ac03_non_gitignore_commit_passes`
4. `test_ac04_failure_output_mentions_boundary_and_diary`
5. `test_ac05_hook_registered_in_precommit_config`
6. `test_ac06_explicit_bypass_with_reason_passes`
7. `test_ac07_bypass_without_reason_fails`

RED command:

```bash
pytest tests/unit/test_fr372_gitignore_boundary_guard.py -q --no-cov
```

Additional RED evidence (current codebase lacks guard):

```bash
rg -n "gitignore-boundary-guard|check_gitignore_boundary" .pre-commit-config.yaml scripts/
```

## Alternatives Considered

1. **Root `.gitignore` only**
   - Rejected: nested `.gitignore` files also alter boundary behavior.

2. **CI-only protection**
   - Rejected: too late; local pre-commit is the earliest boundary gate.

3. **No bypass (immutable `.gitignore`)**
   - Rejected: legitimate maintenance changes exist; intent should be explicit, not impossible.

4. **Rely on human review only**
   - Rejected: does not prevent accidental or agent-authored boundary drift before review.

## Related

- Issue: <https://github.com/sheikkinen/yamlgraph/issues/372>
- Diary incident: `docs/diary/2026-05-12-private-repo-dataloss-recovery.md`
- Hook prior art: `.pre-commit-config.yaml`, `scripts/check_demo_proof.sh`
- Test prior art: `tests/unit/test_ci_demo_proof_gate.py`, `tests/unit/test_precommit_hooks.py`
- Topic path requested by task: `.chaplain/processing/gh-372.md` (not present in this worktree)
- Canonical drafting source used: GitHub issue #372 body
