# Feature Request: FR-314 watcher2 retry/requeue workflow docs in `.chaplain/README.md`

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 days
**Requested:** 2026-05-03

## Summary

Document the operator retry/requeue procedure for failed watcher2 GitHub topics in `.chaplain/README.md`, including required cleanup commands and the re-label trigger.

## Value Statement

Watcher2 operators get a deterministic recovery runbook for failed cycles, reducing repeated stuck items and duplicate manual debugging.

## Problem

GitHub issue #287 requests a concrete retry/requeue workflow near "Troubleshooting Common Issues" in `.chaplain/README.md`.

Current gap:

1. `.chaplain/README.md` documents failures generally but does not provide an explicit requeue procedure for `gh-<NUM>.md` items in `.chaplain/failed/`.
2. `.chaplain/lib/watcher/inbox_sync.sh` intentionally skips issues already present in `.chaplain/inbox/`, `.chaplain/processing/`, or `.chaplain/failed/`, so re-labeling alone is insufficient when a failed marker remains.
3. Operators lack one canonical sequence for cleaning stale worktree/branch state before re-labeling the issue.

## Objectives

1. Add one minimal troubleshooting subsection describing retry/requeue for failed GitHub topics.
2. Include exact cleanup and requeue commands with `<NUM>` placeholders.
3. Explicitly explain why removing `.chaplain/failed/gh-<NUM>.md` is required before re-labeling.

## Constraints

- Scope is documentation-only: `.chaplain/README.md` plus documentation test updates.
- Do not change watcher2 runtime behavior (`inbox_sync.sh`, `watcher2.sh`, worktree scripts).
- Keep the section localized near existing troubleshooting guidance.
- Preserve existing terminology and command style used in `.chaplain/README.md`.

## Proposed Solution

Add a new troubleshooting subsection in `.chaplain/README.md` (near current pipeline failure guidance) titled along the lines of:

- `Retry/Requeue Failed GitHub Topics`

Include this ordered operator flow:

1. Remove failed marker:
   - `rm .chaplain/failed/gh-<NUM>.md`
2. Remove stale worktree:
   - `git worktree remove tmp/worktrees/feat/watcher2-gh-<NUM> --force`
3. Remove stale branch (local + remote):
   - `git branch -D feat/watcher2-gh-<NUM> && git push origin --delete feat/watcher2-gh-<NUM>`
4. Re-add trigger label:
   - `gh issue edit <NUM> --add-label chaplain`
5. Wait for next dispatcher cycle:
   - `inbox_sync.sh` (dispatcher `syncing_inbox` phase) re-imports the issue automatically.

Add a short note stating that step 1 is mandatory because `inbox_sync.sh` skips issues already represented in `failed/`, `processing/`, or `inbox/`.

## Acceptance Criteria

- [x] **AC-01:** `.chaplain/README.md` includes a dedicated retry/requeue troubleshooting subsection for failed GitHub topics.
- [x] **AC-02:** The subsection documents all four required operator commands (remove failed marker, remove worktree, remove branch local+remote, re-add `chaplain` label).
- [x] **AC-03:** The subsection explicitly states that removing `.chaplain/failed/gh-<NUM>.md` is required because `inbox_sync.sh` skips issues present in `failed/`, `processing/`, or `inbox/`.
- [x] **AC-04:** The subsection states that watcher2 picks the issue back up via the normal inbox sync cycle after re-labeling.
- [x] **AC-05:** Documentation tests are updated to enforce presence of this retry/requeue guidance.
- [x] **AC-06:** No watcher runtime scripts are modified.

## Failing Acceptance Tests (RED)

Current failing checks in this worktree:

```bash
rg -n 'Retry/Requeue Failed GitHub Topics' .chaplain/README.md
# exits 1 (section missing)

rg -n 'rm \.chaplain/failed/gh-<NUM>\.md' .chaplain/README.md
# exits 1 (required command missing)

rg -n 'gh issue edit <NUM> --add-label chaplain' .chaplain/README.md
# exits 1 (requeue command missing)

python - <<'PY'
from pathlib import Path
text = Path(".chaplain/README.md").read_text()
required = [
    "rm .chaplain/failed/gh-<NUM>.md",
    "git worktree remove tmp/worktrees/feat/watcher2-gh-<NUM> --force",
    "git branch -D feat/watcher2-gh-<NUM> && git push origin --delete feat/watcher2-gh-<NUM>",
    "gh issue edit <NUM> --add-label chaplain",
]
missing = [line for line in required if line not in text]
assert not missing, f"missing retry/requeue lines: {missing}"
PY
# exits 1 (multiple lines missing)
```

Planned RED test command after adding a dedicated docs assertion:

```bash
pytest tests/unit/test_chaplain_readme_documentation.py -q --no-cov
```

## Alternatives Considered

1. **Leave guidance only in issue/PR discussion** — Rejected. Operational runbook belongs in `.chaplain/README.md`, not ephemeral threads.
2. **Automate requeue from `.chaplain/failed/` without docs** — Rejected for this FR as over-scope; this request is documentation clarity.
3. **Only document re-labeling step** — Rejected. Incomplete because failed markers block re-import.

## Related

- Topic source: GitHub issue #287 (`https://github.com/sheikkinen/yamlgraph/issues/287`)
- Requested local topic file: `.chaplain/processing/gh-287.md` (not present in this worktree)
- Target doc: `.chaplain/README.md`
- Relevant behavior sources:
  - `.chaplain/lib/watcher/inbox_sync.sh`
  - `.chaplain/watcher2.sh`
  - `.chaplain/lib/watcher/worktree_teardown.sh`
  - `tests/unit/test_chaplain_readme_documentation.py`
  - `tests/unit/test_harden_remote_inbox.py`
  - `feature-requests/FR-243-github-issues-remote-inbox.md`

## Research Brief

### Existing Abstractions

- `inbox_sync.sh` already codifies stage dedup by skipping files present in inbox/processing/failed, which is the mechanical reason failed markers must be removed before re-labeling.
- `watcher2.sh` archives failed topics to `.chaplain/failed/gh-<NUM>.md`, so retry requires explicit operator cleanup when a failed cycle should be re-run.
- `worktree_teardown.sh` already contains the canonical cleanup primitives (worktree removal and branch deletion), making this a documentation alignment task rather than a new runtime behavior task.

### Prior Art in This Codebase

- FR-243 established remote issue ingestion and explicitly describes re-labeling `chaplain` as the retry trigger.
- `.chaplain/README.md` already contains troubleshooting patterns, so adding one focused subsection is consistent with current documentation structure.

### Classification Signal

- Abstraction level: **operator runbook documentation**
- Recommended approach: **build** (small docs + docs-test contract update)
- Key risk: command drift if scripts change; mitigate by adding explicit test assertions for the documented workflow.
