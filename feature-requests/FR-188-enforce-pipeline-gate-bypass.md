# Feature Request: FR-188 Enforce Pipeline Gate Bypass Fix

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-12

## Summary

The enforce and bugfix pipelines produce PRs missing diary reflections and changelog fragments, causing CI gate failures. Three defects: (1) critique-and-distill prompt outputs diary text but never writes a file, (2) finalize prompt omits changelog fragment creation, (3) CI diary-gate uses case-sensitive grep that misses uppercase `FR-` filenames.

## Value Statement

Pipeline operators get PRs that pass CI gates on first push, eliminating manual fixup of missing diary and changelog files after every automated enforcement run.

## Problem

Three defects allow the enforcer pipeline to bypass CI gates:

### 1. Critique-and-distill prompt generates text, doesn't write files

`examples/enforce/prompts/enforce-critique-and-distill.yaml` instructs the LLM to "generate a diary reflection" and "Output both the critique assessment AND the diary reflection." The diary content appears only in session output — no instruction writes it to `docs/diary/YYYY-MM-DD-reflection-fr-XXX.md`. The file never reaches the git staging area.

### 2. Finalize prompt omits changelog fragment creation

`examples/enforce/prompts/enforce-finalize.yaml` instructs `git add -A` and `git commit` with a `feat(scope): FR-XXX` message, but never creates a changelog fragment in `changelog/unreleased/`. The `changelog-required` commit-msg hook should catch this, but the copilot agent may not recover from the hook failure.

### 3. CI diary-gate uses case-sensitive pattern

`.github/workflows/commitlint.yml` diary-gate job (line 112):

```bash
git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE "docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]"
```

The pattern expects lowercase `fr-` but pipeline output and `finalize_merge.sh` create files with uppercase `FR-` (e.g., `2026-03-12-reflection-FR-188.md`). The case-sensitive `grep -qE` never matches.

### Impact chain

1. Enforce pipeline runs → critique-and-distill outputs diary text to stdout, no file created
2. Finalize phase commits `feat(...)` without changelog fragment → commit-msg hook may fail silently
3. PR pushed → CI diary-gate fails (missing file) or false-fails (case mismatch)
4. Operator must manually create diary + changelog files, defeating the automation purpose

## Proposed Solution

### Fix 1: Update critique-and-distill prompt to write diary file

In `examples/enforce/prompts/enforce-critique-and-distill.yaml`, add explicit file-creation instructions to Part 2:

```yaml
user: |
  ## Part 2: Diary Reflection

  ...existing reflection instructions...

  **WRITE the diary reflection** to a file at:
    docs/diary/YYYY-MM-DD-reflection-fr-XXX.md
  where YYYY-MM-DD is today's date and XXX is the FR number extracted from: {{ fr_path }}

  Use lowercase `fr-` prefix in the filename (e.g., `reflection-fr-188`).

  The file must contain filled Trap, Heuristic, and Seed sections — no placeholder brackets.
  Stage the file with `git add docs/diary/`.
```

### Fix 2: Update finalize prompt to create changelog fragment

In `examples/enforce/prompts/enforce-finalize.yaml`, add changelog creation before the commit step:

```yaml
user: |
  ## Changelog Fragment

  Before committing, create a changelog fragment:

  1. Extract FR number and scope from: {{ fr_path }}
  2. Create `changelog/unreleased/FR-XXX-<slug>.md` with:
     ```
     ---
     type: feat
     scope: <scope>
     ---
     - **FR-XXX <title>**: <one-line summary>
     ```
  3. Stage with `git add changelog/unreleased/`
```

### Fix 3: Fix CI diary-gate case sensitivity

In `.github/workflows/commitlint.yml`, add `-i` flag to make the diary-gate grep case-insensitive:

```bash
# Before:
git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE "docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]"

# After:
git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qiE "docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]"
```

### Fix 4: Apply same fixes to bugfix pipeline

The bugfix pipeline (`examples/bugfix/prompts/`) has identical gaps. Its submit prompt (`bugfix-submit-pr.yaml`) needs the same diary file creation and changelog fragment instructions added.

## Acceptance Criteria

- [ ] `enforce-critique-and-distill.yaml` prompt instructs diary file creation at `docs/diary/YYYY-MM-DD-reflection-fr-XXX.md` with `git add`
- [ ] `enforce-finalize.yaml` prompt instructs changelog fragment creation in `changelog/unreleased/` with `git add`
- [ ] CI diary-gate grep in `.github/workflows/commitlint.yml` uses `-i` flag for case-insensitive matching
- [ ] Bugfix pipeline prompts receive equivalent diary and changelog instructions
- [ ] Existing pre-commit hooks (`diary-reflection-check`, `changelog-required`) continue to function as secondary safety net
- [ ] `yamlgraph graph lint` passes on updated enforce and bugfix graph YAML files
- [ ] Documentation: `reference/release-checklist.md` updated if post-merge finalize steps change

## Alternatives Considered

1. **Auto-generate diary/changelog in `enforce_worktree.sh` (shell layer):** Rejected — violates three-layer separation. File creation belongs in the graph's LLM phase, not the presentation shell script.

2. **Remove `--no-verify` from initial FR commit:** Not the root cause. The `--no-verify` is on a `docs(FR):` commit which doesn't trigger `changelog-required` (only `feat`/`fix` do). The real problem is the `feat`/`fix` commit in the worktree lacking the required files.

3. **Post-merge GitHub Action to auto-create diary/changelog:** Defeats the purpose — diary reflections should be written by the LLM that did the work, not auto-generated after the fact.

## Related

- `examples/enforce/prompts/enforce-critique-and-distill.yaml` — diary generation prompt
- `examples/enforce/prompts/enforce-finalize.yaml` — commit/PR prompt
- `examples/bugfix/prompts/bugfix-submit-pr.yaml` — bugfix commit/PR prompt
- `.github/workflows/commitlint.yml` — CI gates (diary-gate, changelog-gate)
- `.pre-commit-config.yaml` — local hooks (diary-reflection-check, changelog-required)
- `scripts/enforce_worktree.sh` — orchestration shell (line 69: `--no-verify`)
- `scripts/bugfix_worktree.sh` — bugfix orchestration (line 69: `--no-verify`)
- `scripts/finalize_merge.sh` — post-merge manual step (creates diary + changelog on main)
- FR-125: Enforce pipeline finalize (original design)
- FR-149: CI changelog gate
- FR-158: CI diary gate
- FR-179: Append-only changelog fragments
- FR-183: Simplified enforce pipeline (merged critique + distill phase)
