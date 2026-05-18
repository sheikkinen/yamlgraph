# Fix: Watcher produces mixed-concern commits

## Violation

Audits 232 and 233 (2026-04-21) both flagged commit `a7a609c8` (`chore: watcher timeout`) as a ✗ VIOLATION for bundling unrelated concerns in a single commit: a 2-line config change in `.chaplain/graphs/copilot/graph.yaml`, 4–6 diary entries, a git report, and an FR planning doc — 9 files across 4 unrelated directories in one commit.

The Scripture states: `mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"`. The violation persisted across two consecutive audits because the root cause is structural — the `watch.sh` batch-commit pattern stages everything modified and commits it in one pass with a fixed message template.

## Suggested Fix

Structural gap: the watcher needs per-concern commit grouping.

### FR Outline

**Goal:** Change `watch.sh` (or its equivalent batch-commit step) to group staged files by top-level concern directory and emit one commit per group rather than one commit per enforcement cycle.

**Grouping heuristic:**
- `.chaplain/` config changes → `chore(chaplain): <description>`
- `docs/diary/` entries → `docs(diary): land N reflection entries`
- `feature-requests/` additions/updates → `docs(FR): add/update FR-XXX`
- `changelog/unreleased/` fragments → `chore(changelog): add fragment <name>`
- All other files → one commit per top-level directory

**Acceptance criteria:**
1. A single enforcement cycle that touches `.chaplain/graphs/` AND `docs/diary/` produces two separate commits, not one.
2. `git log --oneline` shows distinct, independently-revertable commits for each concern.
3. Existing watcher smoke test (FR-217) still passes.

**Implementation approach:**
- In the commit step of `watch.sh`, group `git diff --cached --name-only` output by first path component.
- For each group: `git add <files>`, `git commit -m "<typed message>"`.
- Derive the typed message from the group's directory (mapping table in `watch.sh`).
