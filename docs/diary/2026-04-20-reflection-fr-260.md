
---

## 2026-04-20: Chaplain — FR-260 Acceptance Tests Before Enforce

The core insight: separating test authorship from implementation authorship creates an independent verification gate. The fox no longer guards the henhouse — tests exist before the implementing agent sees the codebase.

**Trap encountered:** `downstream_fix` — the original pipeline diagnosed weak tests at enforce time (downstream) instead of gatekeeping at judge time (boundary). Moving worktree creation and test writing upstream normalizes verification at the entry boundary.

**Pattern applied:** The bugfix-condemn template (FR-173) provided a direct template for the `write-acceptance-tests` prompt. Same structure: read criteria, write tests, run to confirm RED, commit with `SKIP=pytest`. Commandment 4 — conform before extending.

**Implementation detail:** The `test_research_to_judge_edge` test from FR-257 needed updating — it asserted a direct `research → judge` edge. FR-260 intentionally replaces this with `research → create_worktree → write_acceptance_tests → judge`. The fix: trace reachability instead of direct edge existence. This is a lesson in test fragility — asserting path existence is more robust than asserting specific edge topology when the pipeline evolves.

**Seed:** Can the acceptance test suite quality be evaluated quantitatively? Metrics like AC-to-test ratio, structural coverage of the FR, or test specificity could inform whether judge should AMEND for insufficient test coverage.
