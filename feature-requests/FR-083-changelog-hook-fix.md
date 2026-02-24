# Feature Request: Fix CHANGELOG and FR Commit-Msg Hook $0/$1 Bug

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

The `changelog-required` and `feat-requires-fr` pre-commit hooks have never enforced anything due to a bash `$0/$1` positional argument bug. Both hooks use `bash -c '...$1...'` but `bash -c` assigns the first positional argument to `$0`, not `$1` — so the commit message file is never read. Additionally, CHANGELOG.md contains a stale entry for a feature that was implemented then deleted.

## Problem

Six consecutive Inquisitor audits flagged the same CHANGELOG violation without correction. Root cause analysis:

### 1. `bash -c` Positional Argument Bug (both hooks)

Pre-commit passes the commit-msg file as the first argument after the entry command:

```
bash -c 'msg=$(cat "$1"); ...' /path/to/COMMIT_EDITMSG
```

Per bash semantics, `bash -c` assigns the first arg after the script string to `$0` (not `$1`). So `/path/to/COMMIT_EDITMSG` lands in `$0`, `$1` is empty, `cat "$1"` reads nothing, and the hook unconditionally passes.

**Affected hooks:**
- `changelog-required` (`.pre-commit-config.yaml` line 157) — introduced in FR-077
- `feat-requires-fr` (`.pre-commit-config.yaml` line 148) — introduced in FR-038

### 2. Fossilized CHANGELOG Entry

CHANGELOG.md line 14 states:

> `backend: sampling — deferred (raises NotImplementedError)`

This feature was implemented (commit `4152cb1`) then deleted (commit `b7a68f0`). The CHANGELOG was never updated in either direction. The stale entry misleads readers into believing the sampling backend exists in a deferred state.

### 3. Scope Gap

`refactor:` commits that remove features don't trigger any CHANGELOG update requirement. This is a known limitation (noted in FR-077's enforcement matrix) and is deferred — the immediate priority is making the existing hooks work.

## Proposed Solution

### Fix 1: Add `_` placeholder to both hooks

The canonical bash pattern for `bash -c` with positional arguments uses `_` as a placeholder for `$0`:

```yaml
# BEFORE (broken) — $1 is always empty
entry: "bash -c 'msg=$(cat \"$1\"); ...' "

# AFTER (fixed) — _ occupies $0, commit-msg file becomes $1
entry: "bash -c 'msg=$(cat \"$1\"); ...' _"
```

Apply to both hooks:

#### `changelog-required` (line 155–160)

```yaml
- id: changelog-required
  name: feat/fix commits require CHANGELOG.md
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE \"^(feat|fix)(\\(.*\\))?:\" && ! git diff --cached --name-only | grep -qE \"^CHANGELOG\\.md$\"; then echo \"ERROR: feat:/fix: commits must include CHANGELOG.md changes\"; echo \"Add your entry under the current [Unreleased] or version heading.\"; exit 1; fi' _"
  language: system
  stages: [commit-msg]
  always_run: true
```

#### `feat-requires-fr` (line 146–151)

```yaml
- id: feat-requires-fr
  name: feat commits require FR-XXX
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE \"^feat(\\(.*\\))?:\" && ! echo \"$msg\" | grep -qE \"FR-[0-9]+\"; then echo \"ERROR: feat: commits require FR-XXX reference\"; echo \"Example: feat: FR-038 add commit enforcement\"; exit 1; fi' _"
  language: system
  stages: [commit-msg]
  always_run: true
```

### Fix 2: Remove stale CHANGELOG entry

Delete line 14 from CHANGELOG.md:

```diff
-  - `backend: sampling` — deferred (raises `NotImplementedError`, requires MCP loopback)
```

The sampling backend was fully removed; it is not deferred.

### Fix 3: Add hook integration test

Create `tests/unit/test_precommit_hooks.py` that verifies:

1. A `feat:` commit message without CHANGELOG.md staged is rejected
2. A `feat:` commit message with CHANGELOG.md staged is accepted
3. A `chore:` commit message without CHANGELOG.md staged is accepted
4. A `fix:` commit message without CHANGELOG.md staged is rejected
5. A `feat:` commit message without `FR-XXX` is rejected
6. A `feat: FR-083` commit message is accepted

Test approach: extract the bash condition logic into a testable form by invoking the hook entry via subprocess with a temp commit-msg file.

## Acceptance Criteria

- [x] Add `_` placeholder to `changelog-required` hook entry in `.pre-commit-config.yaml`
- [x] Add `_` placeholder to `feat-requires-fr` hook entry in `.pre-commit-config.yaml`
- [x] Remove stale `backend: sampling` entry from CHANGELOG.md line 14
- [x] Add integration test for both commit-msg hooks in `tests/unit/test_precommit_hooks.py`
- [x] Verify hooks reject invalid commits: `echo "feat: test" > /tmp/msg && pre-commit run changelog-required --hook-stage commit-msg --commit-msg-filename /tmp/msg`
- [x] Document fix in `docs/diary.md` with Trap/Heuristic/Seed

## Constraints

- **Minimal change** — append ` _` to each hook's entry string; no structural refactoring
- **Both hooks share the same root cause** — fix both in one pass to avoid a repeat FR
- **No scope expansion** — `refactor:` enforcement is explicitly deferred (per FR-077)
- **Backward compatible** — the `_` placeholder pattern is standard bash; no pre-commit version dependency

## Alternatives Considered

1. **Use `$0` instead of `$1`** — Works but unconventional; readers expect `$1` for positional args. The `_` placeholder is the standard idiom.

2. **Rewrite hooks as Python scripts** — More testable but over-engineered for two one-liner checks. The bash hooks match the pattern established by FR-038.

3. **Remove hooks entirely** — Rejected; CHANGELOG and FR discipline is valuable (Commandment 10). The hooks just need to actually work.

4. **Fix only `changelog-required`** — `feat-requires-fr` has the identical bug. Fixing one without the other would be negligent.

5. **Extend `refactor:` to require CHANGELOG** — Deferred per FR-077. Fix what's broken before expanding scope.

## Related

- FR-077 `changelog-commit-enforcement` — Introduced the `changelog-required` hook (with the bug)
- FR-038 `feat-commit-fr-enforcement` — Introduced the `feat-requires-fr` hook (with the bug)
- `.pre-commit-config.yaml` lines 146–160 — Both affected hooks
- CHANGELOG.md line 14 — Stale sampling backend entry
- Diary entries: 6 Inquisitor audits from 2026-02-24 flagging the same violation
- Heuristic: *"A violation that survives 5 audits is no longer a violation — it is policy"*
- `bash(1)`: *"If the -c option is present … the first argument after the string is assigned to $0"*
