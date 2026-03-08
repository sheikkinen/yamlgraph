## 2026-03-07: Inquisitor Audit XVI — ghost SHA, calcified findings, clean commits

**Context:** Sixteenth audit covering commits `ff1faca`..`65f9e95` (5 commits: `docs(chaplain)` ×2, `chore(tests)` ×1, `chore(graph)` ×1, `docs(diary)` ×1). Two new commits since Audit XV: `bfa1dd1` and `65f9e95`. Zero `feat:` or `fix:` in window. Audit XV referenced commit `856a13e` which no longer exists — it was rebased/amended into `bfa1dd1`, resolving the mixed-commit violation Audit XV flagged (diary entries split out, test fix now standalone).

**Findings:**

1. **⚠ DRIFT — Audit XV references ghost commit `856a13e`.** History was rewritten (rebase or amend), splitting the mixed commit into clean single-purpose commits. The violation Audit XV flagged is retroactively resolved, but the diary record now cites a SHA that `git log` cannot find. Audit records become unreliable when they reference rewritten history.

2. **✓ COMPLIANT — `bfa1dd1` is clean.** Single-purpose commit: renames `l` → `line` (E741) and converts try/except to `contextlib.suppress` (SIM105). One file changed, 3 insertions, 4 deletions. No mixed content.

3. **⚠ DRIFT — Standing findings calcified (CALCIFIED-3, 8th+ consecutive audit).** ARCHITECTURE.md line 1125: "7 providers" (should be 8). FR-112 status: "Draft" (should be "Done"). FR-116 CHANGELOG entry: absent. Per Audit XV's Seed, this audit adopts the CALCIFIED-3 shorthand and will not repeat the full description.

4. **✓ COMPLIANT — Conventional Commits, ADR-001, noqa confessions.** All 5 commits use valid prefixes. No new capabilities, tests, or suppressions. All 55 noqa suppressions confessed (verified via `noqa_coverage.py`).

5. **✓ COMPLIANT — Diary entries current.** FR-115 judgement reflection committed. Audit XV recorded. Distill step honored.

**Heuristic:** *An audit record that cites a dead SHA is a broken hyperlink in the project's memory.* When history is rewritten (rebase, amend, force-push), diary entries referencing the old SHAs become unverifiable. The cure: reference branch-relative ranges (`HEAD~5..HEAD`) or tag auditable snapshots, not bare SHAs that rebase can erase.

**Seed:** Should the Inquisitor pre-flight verify that all SHAs cited in the previous audit still exist in `git log`? A simple `git cat-file -t <sha>` check would surface ghost references before the next audit compounds the problem.
