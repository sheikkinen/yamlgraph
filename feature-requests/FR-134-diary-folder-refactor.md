# Feature Request: FR-134 Diary Folder Refactor — Replace Single File with Date-Prefixed Entries

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-08

## Summary

Replace the monolithic `docs/diary.md` with a `docs/diary/` folder of date-prefixed entry files, eliminating merge conflicts caused by concurrent appends from `finalize_merge.sh`, `diary_rotate.py`, `inquisitor.sh`, and `examples/shared/diary.py`.

## Value Statement

All pipeline actors (finalize, inquisitor, digest, shared diary tool) gain conflict-free parallel writes, eliminating the recurring stash/pop merge dance that loses local changes.

## Problem

`docs/diary.md` is a merge conflict hotspot. Five independent actors append to the same file:

1. `scripts/finalize_merge.sh` (line 81) — reflection stubs after PR merge
2. `scripts/diary_rotate.py` (line 29) — world digests and git reports from scheduled imports
3. `.chaplain/inquisitor.sh` (lines 23, 61) — audit entries (via copilot tool)
4. `examples/shared/diary.py` (line 13) — formatted diary entries from graph tools
5. `scripts/diary_digest.sh` (line 23) — stages diary changes for commit

The recurring failure mode:
1. Merge PR → pull main
2. `finalize_merge.sh` fails with "Working tree dirty"
3. `git stash` → run finalize → pre-commit modifies files
4. `git push` → `git stash pop` → conflict in `docs/diary.md`
5. `git checkout --ours` → drop stash → **lose local changes**

This is not a one-time annoyance — it happens on nearly every merge cycle because the pre-commit `diary-rotate` hook and the inquisitor post-commit hook both touch the same file.

## Proposed Solution

Replace `docs/diary.md` with `docs/diary/` containing individual entry files:

```
docs/diary/
├── 2026-03-07-reflection-fr-127.md
├── 2026-03-07-reflection-fr-128.md
├── 2026-03-08-world-digest.md
├── 2026-03-08-inquisitor-audit-xxv.md
├── 2026-03-08-inquisitor-audit-xxiv.md
└── ...
```

### Naming Convention

`YYYY-MM-DD-<type>-<id>.md` where:
- `<type>` is one of: `reflection`, `inquisitor-audit`, `world-digest`, `git-report`, `digest`
- `<id>` is context-specific: FR number, audit number (roman numeral lowercase), or omitted

### Script Changes

**1. `scripts/finalize_merge.sh`** (line 81):
```bash
# Before: cat >> docs/diary.md << EOF
# After:
DIARY_ENTRY="docs/diary/$(date +%Y-%m-%d)-reflection-${FR_NUM}.md"
cat > "$DIARY_ENTRY" << EOF
```

**2. `.chaplain/inquisitor.sh`** — three changes:

*SHA extraction (line 23):* Replace single-file scan with filename-sorted multi-file scan:
```bash
# Before:
LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' docs/diary.md 2>/dev/null | head -1)

# After (filename-based sort — stable across git checkout/clone):
LATEST_AUDIT=$(ls docs/diary/*inquisitor-audit* 2>/dev/null | sort -r | head -1)
LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' "$LATEST_AUDIT" 2>/dev/null | head -1)
```

*Record step (line 61):* Update copilot prompt to create a new file instead of appending:
```
Step 4 — Record:
Create a new diary entry file at docs/diary/YYYY-MM-DD-inquisitor-audit-<number>.md
```

*Propose mode (line 78):* Update `Step 1 — Read diary:` to scan `docs/diary/*inquisitor-audit*` files (sorted by name, most recent first) instead of single file.

**3. `scripts/diary_rotate.py`** (line 29):
- Remove day-based rotation logic (no longer needed — entries are already separate files)
- Import scheduled entries directly as individual files into `docs/diary/`:
  - World digests: `docs/diary/YYYY-MM-DD-world-digest.md`
  - Git reports: `docs/diary/YYYY-MM-DD-git-report.md`
- Remove archival from this FR's scope (see note below on archive threshold)

**4. `examples/shared/diary.py`** (line 13):
```python
# Before:
DIARY_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "diary.md"

# After:
DIARY_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "diary"

def write_diary(state: dict) -> dict:
    # ...parse entry as before...
    date_str = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    prefix = state.get("diary_prefix", "World Digest")
    entry_type = prefix.lower().replace(" ", "-")  # "World Digest" → "world-digest"
    filename = f"{date_str}-{entry_type}.md"
    entry_path = DIARY_DIR / filename
    entry_path.write_text(entry)
    return {"written": True}
```
- `append_to_diary()` replaced by `write_text()` to individual files
- `format_diary_entry()` unchanged (formats the content, not the destination)

**5. `scripts/diary_digest.sh`** (line 23):
```bash
# Before:
if git diff --quiet docs/diary.md; then
    echo "No diary changes"
else
    git add docs/diary.md

# After:
if git diff --quiet docs/diary/; then
    echo "No diary changes"
else
    git add docs/diary/
```

**6. `scripts/enforce_worktree.sh`** (line 59):
```bash
# Before:
validate_clean_working_tree(exclude_paths=['docs/diary.md', 'feature-requests/'])

# After:
validate_clean_working_tree(exclude_paths=['docs/diary/', 'feature-requests/'])
```

**7. `yamlgraph/utils/worktree_helpers.py`** (line 58):
- Update docstring example from `docs/diary.md` to `docs/diary/`
- The prefix matching logic already handles directory paths correctly

**8. `scripts/absolution.py`** (line 16):
```python
# Before:
"**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md."
# After:
"**Distill.** After completing a task list, add a metacognitive entry to docs/diary/."
```

**9. `examples/demos/commit-delta-gate/demo.sh`** (lines 5-6, 18-19):
```bash
# Before:
LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' docs/diary.md 2>/dev/null | head -1)

# After:
LATEST_AUDIT=$(ls docs/diary/*inquisitor-audit* 2>/dev/null | sort -r | head -1)
LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' "$LATEST_AUDIT" 2>/dev/null | head -1)
```
Update comment on lines 5-6 to reference `docs/diary/` instead of `docs/diary.md`.

### Migration Script

A one-time migration script (`scripts/migrate_diary_to_folder.py`) will:

1. **Parse `docs/diary.md`** by splitting on `\n---\n` delimiters
2. **Extract date** from each entry's `## YYYY-MM-DD:` header
3. **Infer type** from header text:
   - Contains `Inquisitor Audit` → `inquisitor-audit`
   - Contains `Implementation Reflection` or starts with `FR-` → `reflection`
   - Contains `World Digest` → `world-digest`
   - Contains `Git Report` → `git-report`
   - Default → `digest`
4. **Infer ID** from header text:
   - `FR-XXX` → `fr-xxx` (lowercase)
   - `Audit XXV` → `xxv` (roman numeral lowercase)
   - Otherwise omitted
5. **Write each entry** to `docs/diary/YYYY-MM-DD-<type>-<id>.md`
6. **Handle duplicates**: Append `-N` suffix if filename already exists
7. **Reuse `tmp/split_diary.py`** as reference — it already implements date extraction and block splitting for the same file format

The script lives in `scripts/` (not `tmp/`) since it documents the migration approach and may be re-run during review.

### Archive Threshold — Deferred

The original proposal included "move entries older than N days to `docs/diary/archive/`". This is deferred to a separate FR because:
- The per-file structure already reduces file count pressure (no single file grows unbounded)
- An undefined threshold cannot be implemented or tested
- Archive policy is a separate concern from conflict elimination

`diary_rotate.py` rotation logic (archive the previous day's monolithic diary) is removed entirely — it served the single-file model and has no purpose in the per-file model.

## Acceptance Criteria

- [ ] `docs/diary/` folder exists with naming convention `YYYY-MM-DD-<type>-<id>.md`
- [ ] `finalize_merge.sh` writes reflection stubs as individual files to `docs/diary/`
- [ ] `diary_rotate.py` writes scheduled imports (world digests, git reports) as individual files
- [ ] `examples/shared/diary.py` `write_diary()` creates individual files in `docs/diary/` (DIARY_PATH → DIARY_DIR)
- [ ] `.chaplain/inquisitor.sh` creates new audit entry files in `docs/diary/`
- [ ] Inquisitor SHA extraction uses filename-sorted lookup (`sort -r | head -1`), not `ls -t`
- [ ] Inquisitor propose mode scans `docs/diary/*inquisitor-audit*` files
- [ ] `enforce_worktree.sh` excludes `docs/diary/` instead of `docs/diary.md`
- [ ] `worktree_helpers.py` docstring and exclude path updated; tests pass
- [ ] `diary_digest.sh` stages `docs/diary/` changes
- [ ] `absolution.py` doctrine reference updated to `docs/diary/`
- [ ] `examples/demos/commit-delta-gate/demo.sh` updated for folder-based audit lookup
- [ ] Migration script `scripts/migrate_diary_to_folder.py` splits `docs/diary.md` into individual files
- [ ] `docs/diary.md` removed after migration
- [ ] Archived diary files (`docs/diary-YYYY-MM-DD.md`) remain untouched (historical)
- [ ] Example prompts referencing `docs/diary.md` updated (`examples/ebook/prompts/`, `examples/copilot/`)
- [ ] Pre-commit `diary-rotate` hook updated for folder-based operation
- [ ] Tests updated: `test_finalize_merge.py`, `test_inquisitor_gate.py`, `test_diary_rotate.py`, `test_diary_digest.py`, `test_worktree_helpers.py`
- [ ] `.github/copilot-instructions.md` doctrine references updated (lines 31, 145)
- [ ] `ARCHITECTURE.md` REQ-YG-131 and inquisitor spec references updated (lines 640, 663)
- [ ] No merge conflicts occur when two actors write diary entries simultaneously
- [ ] Archive threshold deferred — no archival logic in this FR

## Alternatives Considered

1. **File locking (`flock`)**: Would serialize writes but doesn't solve the git merge conflict — two branches modifying the same file still conflict on merge. Rejected.

2. **Git rerere (reuse recorded resolution)**: Learns merge conflict resolutions, but diary entries are unique content each time — no pattern to learn. Rejected.

3. **Append-only with markers**: Use unique section markers per actor so git can merge without conflict. Fragile — doesn't handle concurrent line-adjacent appends. Rejected.

4. **Keep single file + rebase workflow**: Require `git pull --rebase` instead of merge. Doesn't solve the fundamental problem of concurrent pre-commit and post-commit hooks modifying the same file. Rejected.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Reviewed:** 2026-03-08

### Assessment

The FR is well-researched with accurate file/line references (all 10 verified), a sound design (per-file entries eliminate merge conflicts by construction), and measurable acceptance criteria. The archive threshold is correctly deferred. Alternatives are well-reasoned rejections.

### Observations (address during enforcement)

1. **Missing references: `.github/copilot-instructions.md`** — Lines 31 and 145 reference `docs/diary.md` in the Distill doctrine. Must be updated alongside `scripts/absolution.py`. Add to acceptance criteria.

2. **Missing references: `ARCHITECTURE.md`** — Lines 640 and 663 (REQ-YG-131) reference `docs/diary.md` in the inquisitor specification. Must be updated. Add to acceptance criteria.

3. **Runtime duplicate filenames** — The migration script handles collisions (append `-N`), but runtime writers (`examples/shared/diary.py` using `write_text()`, `diary_rotate.py`) silently overwrite if the same `<type>` runs twice on the same day. This is acceptable for idempotent scheduled imports (world-digest, git-report) but should be documented as intentional. Reflections and audits are inherently unique (FR number, audit number).

4. **`diary_rotate.py` wording** — The FR says "rotation logic removed entirely" (line 190) and "writes scheduled imports as individual files" (line 88). These are not contradictory — rotation (archive previous day) is removed while import (write new entries) is refactored — but implementer should note this distinction clearly in commit messages.

5. **Historical references** — Feature requests, changelogs, ebook content, and archived diary files (`docs/diary-YYYY-MM-DD.md`) that mention `docs/diary.md` are historical records and do NOT need updating. This aligns with acceptance criterion line 208.

## Related

- REQ-YG-131: Inquisitor commit-delta gate (extracts SHA from diary)
- REQ-YG-125: `finalize_merge.sh` diary reflection stub
- REQ-YG-072: Diary Digest Tools
- REQ-YG-090: Chaplain Diary Append
- `scripts/finalize_merge.sh` (line 81)
- `.chaplain/inquisitor.sh` (lines 23, 61, 78)
- `scripts/diary_rotate.py` (line 29)
- `scripts/enforce_worktree.sh` (line 59)
- `yamlgraph/utils/worktree_helpers.py` (line 58)
- `examples/shared/diary.py` (line 13)
- `examples/demos/commit-delta-gate/demo.sh` (lines 5, 19)
- `scripts/absolution.py` (line 16)
- `tmp/split_diary.py` (migration reference)
