# Feature Request: FR-144 Enforce Diary Reflection Content

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a pre-commit hook that rejects commits containing unfilled diary reflection stubs, and modify `finalize_merge.sh` to leave stubs unstaged so enforcement and creation don't conflict.

## Value Statement

The inquisitor stops wasting audit cycles on missing reflections because mechanical enforcement replaces manual discipline — graduating the `audit_as_ritual` trap into a gate.

## Problem

`scripts/finalize_merge.sh` creates diary reflection stubs in `docs/diary/YYYY-MM-DD-reflection-FR-XXX.md` with placeholder text (`[What cognitive trap was encountered?]`, etc.). Nothing enforces that these placeholders get replaced with actual content.

**Evidence of failure:**
- FR-134's stub has been flagged as ⚠ DRIFT in **6+ consecutive audits** (XXVIII–XXXII), explicitly identified as the `audit_as_ritual` trap in Audit XXXII.
- FR-139 and FR-140 have no reflection files at all, flagged in audits XXX–XXXIV.
- The inquisitor detects these gaps every cycle but has no mechanism to block — audits without blocking mechanism = post-mortem before incident.

**Root cause:** Automation of creation ≠ automation of insight. The stub creation is mechanical; the fill step relies on human discipline with no enforcement gate.

**Current state (verified):** Three tracked reflection files contain unfilled placeholders:
- `docs/diary/2026-03-08-reflection-fr-127.md`
- `docs/diary/2026-03-08-reflection-fr-128.md`
- `docs/diary/2026-03-08-reflection-fr-134.md`

Two reflection files are missing entirely:
- FR-139 (no `docs/diary/*reflection*fr-139*` exists)
- FR-140 (no `docs/diary/*reflection*fr-140*` exists)

## Proposed Solution

Two coordinated changes plus remediation of existing debt.

### 1. Pre-commit hook: `diary-reflection-check`

A bash hook that scans all tracked `docs/diary/*reflection*.md` files for unfilled placeholder text. Follows the `forbid-terms` hook pattern (`.pre-commit-config.yaml` lines 89–95).

```yaml
# .pre-commit-config.yaml addition
- repo: local
  hooks:
    - id: diary-reflection-check
      name: diary-reflection-check
      entry: bash -c 'STUBS=$(git ls-files "docs/diary/*reflection*.md" | xargs grep -l "\[What cognitive trap\|\[What lesson\|\[What question" 2>/dev/null); if [ -n "$STUBS" ]; then echo "❌ Unfilled diary reflection stubs:"; echo "$STUBS"; echo "Fill Trap/Heuristic/Seed sections before committing."; exit 1; fi'
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

**Detection pattern:** Any tracked reflection file containing the literal strings `[What cognitive trap`, `[What lesson`, or `[What question` is considered unfilled.

### 2. Modify `finalize_merge.sh`: unstaged stub creation

Change `scripts/finalize_merge.sh` line 97 to **not** include `docs/diary/` in `git add`. The stub file is still created on disk as an untracked local reminder. The operator fills it and commits it — at which point the pre-commit hook validates the content is real.

```bash
# Before (current, line 97):
git add CHANGELOG.md "$FR_PATH" docs/diary/

# After (proposed):
git add CHANGELOG.md "$FR_PATH"
```

Also update the commit message template (line 104) to remove "Diary reflection stub appended" and replace with "Diary reflection stub created (untracked)".

**Why unstaged?** If the stub is committed with placeholders, the pre-commit hook blocks all subsequent commits until it's filled. By leaving it unstaged, `finalize_merge.sh` completes its merge commit cleanly (CHANGELOG + FR status update), and the reflection becomes the implementer's next action.

### 3. Immediate remediation: fill existing stubs

As part of implementation, fill or create the five reflections with genuine cognitive content:

| File | Action |
|------|--------|
| `docs/diary/2026-03-08-reflection-fr-127.md` | Fill (tracked, unfilled) |
| `docs/diary/2026-03-08-reflection-fr-128.md` | Fill (tracked, unfilled) |
| `docs/diary/2026-03-08-reflection-fr-134.md` | Fill (tracked, unfilled) |
| `docs/diary/2026-03-08-reflection-fr-139.md` | Create with content |
| `docs/diary/2026-03-08-reflection-fr-140.md` | Create with content |

**Note:** These require genuine human reflection on the cognitive traps encountered during each FR's implementation. LLM-generated reflections defeat the purpose.

## Acceptance Criteria

- [ ] Pre-commit hook `diary-reflection-check` added to `.pre-commit-config.yaml`
- [ ] Hook detects unfilled placeholder text in tracked `docs/diary/*reflection*.md` files
- [ ] Hook passes when all tracked reflection files have real content (no `[What ...?]` placeholders)
- [ ] `finalize_merge.sh` creates reflection stub as untracked file (no `git add` of `docs/diary/`)
- [ ] `finalize_merge.sh` prints reminder message to fill the reflection
- [ ] FR-127 reflection stub filled with actual content
- [ ] FR-128 reflection stub filled with actual content
- [ ] FR-134 reflection stub filled with actual content
- [ ] FR-139 reflection file created with actual content
- [ ] FR-140 reflection file created with actual content
- [ ] No unfilled reflection stubs remain in tracked files
- [ ] Test added for hook detection logic (script that validates grep pattern catches placeholders and passes on filled content)
- [ ] Pre-commit hook passes on current codebase after remediation

## Alternatives Considered

1. **Gate in `finalize_merge.sh` itself** — Rejected. The script runs at merge time; the implementer hasn't yet had time to reflect. Gating here would block the merge workflow.

2. **Inquisitor auto-fill via LLM** — Rejected. Reflections capture human cognitive traps and insights. LLM-generated reflections defeat the purpose of metacognitive practice.

3. **CI-only enforcement (no pre-commit)** — Rejected. Pre-commit catches the issue locally before push, consistent with the codebase's hook-first enforcement pattern. CI is a second gate, not the primary one.

4. **Grace period mechanism** — Rejected as over-engineering. The unstaged-stub approach naturally provides a grace period: the stub exists locally until the implementer is ready to commit it.

## Related

- **Inquisitor audits:** XXVIII–XXXIV (`docs/diary/`)
- **FR-134:** Diary Folder Refactor (created the stub mechanism)
- **FR-076:** Inquisitor (audit system that detects this gap)
- **Scripture:** Sermon of the Chaplain → Distill step; `audit_as_ritual` trap
- **`scripts/finalize_merge.sh`:** Lines 78–97 (stub creation + git add)
- **`.pre-commit-config.yaml`:** `forbid-terms` hook (lines 89–95, analogous pattern)
