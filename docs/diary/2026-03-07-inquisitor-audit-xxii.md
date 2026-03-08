## 2026-03-07: Inquisitor Audit XXII — catch-all commit, missing trailers

**Context:** Twenty-second audit covering commits `b171dee`..`4ef6efd` (5 commits: `chore:` ×1, `docs(FR):` ×2, `fix(enforce):` ×1, `docs(diary):` ×1). Commits 2–5 were already covered by Audit XXI; only `4ef6efd` is new. That commit bundles copilot instructions, diary entries (including AI-generated Inquisitor audits), 4 new feature requests, and 2 FR deletions into a single `chore:` commit. No Python code changed. No tests added.

**Findings:**

1. **✗ VIOLATION — `4ef6efd` lacks Co-authored-by trailer despite AI-generated content.** The commit contains 116 lines of diary entries including Inquisitor audit reflections — clearly AI-assisted. The git commit trailer rule is unconditional: "always include the following Co-authored-by trailer." Fifth consecutive audit citing missing trailers. This is now a CALCIFIED finding per the audit-as-ritual trap.

2. **⚠ DRIFT — `4ef6efd` is a catch-all commit (9 files, 4 unrelated concerns).** Copilot instructions, diary entries, new FRs (FR-120, FR-122, FR-123, FR-126), and deleted FRs (FR-115, FR-116) bundled into one `chore: copilot instructions and fr`. Atomic commit principle violated. The vague subject ("copilot instructions and fr") gives no meaningful signal in `git log`.

3. **✓ COMPLIANT — Conventional Commits format across all 5 commits.** Valid prefixes: `chore:`, `docs(FR):` ×2, `fix(enforce):`, `docs(diary):`. Commandment 10 satisfied on format (though `4ef6efd` subject is imprecise).

4. **✓ COMPLIANT — CHANGELOG current for code changes.** `f3c6b73` (fix) has a matching `[Unreleased] → Fixed` entry. No `feat:` commits in batch, so no CHANGELOG gap.

5. **✓ COMPLIANT — noqa confessions current.** Both existing suppressions (`ANN001` in `executor_async.py`, `ARG002` in `token_tracker.py`) remain documented. No new suppressions introduced.

**Heuristic:** *A catch-all commit is a confession that the work outpaced the discipline.* When accumulating changes across sessions, the temptation is to `git add . && git commit -m "stuff"`. The cure: commit each concern as it completes — copilot instructions alone, then each FR individually, then diary separately. The Co-authored-by trailer absence is now CALCIFIED-4: five consecutive audits without resolution. Per the graduated heuristic, this should spawn a pre-commit hook that rejects commits touching AI-generated files without the trailer.

**Seed:** Should a pre-commit hook enforce Co-authored-by trailers when the diff contains known AI-generated patterns (e.g., diary entries with "Inquisitor Audit" headers, or files in `.github/copilot-instructions.md`)? The pattern is detectable; the enforcement is missing.
