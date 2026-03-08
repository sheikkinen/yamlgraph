## 2026-03-07: Inquisitor Audit XIX — pipeline delivers three features, CHANGELOG gap widens

**Context:** Nineteenth audit covering commits `65f9e95`..`66e4403` (5 commits: `feat` ×3, `chore(precommit)` ×1, `docs(chaplain)` ×1). Three FR implementations landed (FR-118, FR-119, FR-121) via `enforce_worktree.sh` pipeline. FR-116 CHANGELOG entry now present in [Unreleased] — resolving one leg of CALCIFIED-3. FR-121 adds a cross-check test guarding ARCHITECTURE.md provider count against `ProviderType`, targeting the "7 providers" drift directly.

**Findings:**

1. **✗ VIOLATION — Three `feat:` commits, zero CHANGELOG entries.** FR-118, FR-119, FR-121 all implemented and merged without CHANGELOG [Unreleased] entries. Commandment 10 ("let the CHANGELOG.md bear witness") violated systematically. The `enforce_worktree.sh` pipeline automates code delivery but not changelog updates. This is now the dominant defect pattern.

2. **✗ VIOLATION — FR-119 has no ARCHITECTURE.md capability or requirement.** No CAP entry, no REQ-YG-119. Tests correctly use existing REQ-YG-003 and REQ-YG-061 markers, suggesting FR-119 extends existing capabilities — but ADR-001 requires explicit registration when a `feat:` commit introduces new linter behavior (W016/W017 checks). The new checks are untraceable to a dedicated requirement.

3. **✓ COMPLIANT — FR-118 and FR-121 ADR-001 exemplary.** CAP-36 + REQ-YG-118 and CAP-37 + REQ-YG-121 added to ARCHITECTURE.md. `req_coverage.py` updated. All tests carry `@pytest.mark.req` markers. Full traceability chain intact.

4. **⚠ DRIFT — No implementation diary entries for FR-118, FR-119, or FR-121.** Sermon's Distill step mandates metacognitive reflection after completing a task. Three features shipped without implementation reflections. Audit entries are not substitutes.

5. **✓ COMPLIANT — Conventional Commits, noqa clean, Co-authored-by.** All 5 commits follow valid prefixes. No noqa suppressions in new code. PR merge commits carry Copilot trailer. CALCIFIED-3 partially resolved: FR-116 CHANGELOG entry present; provider count test now guards drift.

**Heuristic:** *The `enforce_worktree.sh` pipeline has become a CHANGELOG bypass — it automates feat delivery from plan to merge but skips the CHANGELOG gate entirely.* Three consecutive `feat:` commits without entries proves this is structural, not forgetfulness. The pipeline needs a CHANGELOG-update step or a pre-merge check.

**Seed:** Could `enforce_worktree.sh` auto-generate a CHANGELOG entry by extracting the FR title and REQ markers from `feature-requests/FR-XXX-*.md`? The data is already present in the feature request files — the pipeline just never reads it.
