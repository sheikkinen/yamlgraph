## 2026-04-13: Inquisitor Audit — Diary-gate enforcement gap on feat PRs

**Context:** Audited the 5 most recent commits on `main` (e9d42ea..1346e5d) covering FR-221, FR-223, FR-224, FR-225, and a docs housekeeping commit. Checked Conventional Commits, changelog fragments, diary reflections, noqa confessions, and requirement traceability.

**Findings:**

1. ✗ **VIOLATION — FR-223 and FR-225 merged without diary reflections.** Both `feat` PRs (#90, #89) carry FR-XXX references and are subject to the `diary-gate` CI job. Neither squash-merge commit includes a `docs/diary/` file in its diff. FR-221 (#87), merged the same day, correctly included its diary entry. The gate either failed silently or was bypassed via admin override without break-glass documentation.

2. ✓ **COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description` format with correct FR-XXX references on feat/test types.

3. ✓ **COMPLIANT — Changelog fragments.** FR-221, FR-223, and FR-225 each have a fragment in `changelog/unreleased/`. Types `test` and `docs` correctly omitted.

4. ✓ **COMPLIANT — noqa confessions and requirement traceability.** `scripts/noqa_coverage.py` reports 0 undocumented suppressions. `scripts/req_coverage.py --strict` passes with full coverage across all 87 capabilities.

5. ⚠ **DRIFT — `2026-04-13-git-report.md` is an activity summary, not a metacognitive reflection.** The Sermon demands diary entries that name a cognitive trap, extract a heuristic, and plant a Seed. This file is a git log analysis — useful, but not a reflection per doctrine.

**Heuristic:** A gate that passes intermittently is worse than no gate — it creates false confidence. When two of three same-day feat PRs pass without diary entries while one correctly includes its diary, the enforcement mechanism itself must be audited, not just the content it guards. (Trap: `detection_without_enforcement`)

**Seed:** Should the diary-gate CI job log which file it matched (or failed to match) so bypass vs. bug can be distinguished from the Actions run log alone?
