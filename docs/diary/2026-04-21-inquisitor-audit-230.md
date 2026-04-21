## 2026-04-21: Inquisitor Audit — Recent Commits (a7a609c8..20e9eb9c)

**Context:** Routine audit of the 5 most recent commits on `main` against Scripture, ADR-001, and process doctrine. Commits span chore config, FR docs, diary landings, and a fix.

**Findings:**

1. **✗ VIOLATION — Mixed-concern commit (`a7a609c8 chore: watcher timeout`)**
   Bundles a config change (`.chaplain/graphs/copilot/graph.yaml`), 6 diary entries, a git report, and a new feature request (FR-259) in a single commit. Scripture process rule `mixed_commits_erode_auditability`: "One concern per commit → clear blame, clear revert." Reverting the timeout change would also revert 4 inquisitor audits and an FR.

2. **⚠ DRIFT — Duplicate commit messages (`897fd4cc` and `20e9eb9c`)**
   Two sequential commits share the identical message `fix(a2a): skip a2a SDK tests when package not installed`. The first (`897fd4cc`) carries the code change + one changelog fragment; the second (`20e9eb9c`) adds a second changelog fragment. Same fix, two changelog entries (`fix-a2a-sdk-optional-tests.md`, `fix-a2a-sdk-optional-skip.md`). This muddies the audit trail and will produce duplicate CHANGELOG lines on aggregation.

3. **✓ COMPLIANT — Conventional Commits format**
   All 5 commits follow `type(scope): description` or `type: description`. Types (`chore`, `docs`, `fix`) are valid.

4. **✓ COMPLIANT — Changelog present for `fix` commit**
   `20e9eb9c` has a changelog fragment in `changelog/unreleased/`. The `docs` and `chore` commits correctly omit changelog (not required).

5. **✓ COMPLIANT — Diary entries landed**
   `7dc44faa` lands 9 diary reflections spanning multiple FRs. The FR-253 reflection is thorough with traps, heuristic, and seed.

**Heuristic:** `kitchen_sink_commit` — When a watcher or daemon accumulates artifacts (diary entries, FRs, config tweaks), flush each concern as a separate commit before they merge into an undifferentiated blob. The commit message should describe *one* change; if you need "and" to describe it, split it.

**Seed:** Could the Chaplain's commit step enforce single-concern commits by checking that modified paths share a common prefix or category (e.g., all `docs/diary/`, all `feature-requests/`, or all source code — but never a mix)?
