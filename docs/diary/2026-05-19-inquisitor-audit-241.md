## 2026-05-19: Inquisitor Audit — WIP Commits on Main, Mixed Concerns

**Context:** Routine audit of the 5 most recent commits on `main` (17da4033..fbeb44c0). Scope: Conventional Commits compliance, changelog coverage, ADR-001 req traceability, diary discipline, noqa confessions.

**Findings:**

1. ✗ **VIOLATION — WIP commits on main** (`f35a3254`, `27795d03`): Two commits with identical message `chore: investigation of chaplain failures, wip` landed on main. "wip" signals unfinished work on the protected branch. These appear to be direct pushes (no PR number), bypassing branch protection without documented break-glass rationale.

2. ✗ **VIOLATION — Mixed-concern commits** (`f35a3254`): A single commit bundles 7 production files (action.py, helpers.py, two test suites), 18+ diary/chapter files, investigation proofs, and reference docs — 25 files, 1391 insertions, 815 deletions. Violates `mixed_commits_erode_auditability`: "One concern per commit → clear blame, clear revert."

3. ⚠ **DRIFT — Changelog fragments missing `req:` field** (FR-416, FR-419): Both `fix` changelog fragments omit the `req:` front-matter key. The `changelog-req-gate` CI check validates `req:` references against the capabilities registry. While the gate may tolerate omission for `fix` type, the omission creates traceability gaps between fixes and the requirements they defend.

4. ✓ **COMPLIANT — FR-421 exemplary** (`fbeb44c0`): Merged via PR #423, Conventional Commit with FR reference, changelog fragment with `req: REQ-YG-409`, tests carry `@pytest.mark.req`, diary reflection written. Full doctrine compliance.

5. ✓ **COMPLIANT — ADR-001 req traceability** (all test files): Every new test file in scope carries `@pytest.mark.req` tags — either via decorator or module-level `pytestmark`. No noqa suppressions found in changed production files.

**Heuristic:** A "chore: wip" commit that touches production code is not a chore — it is an unreviewed fix wearing a chore costume. If investigation requires code changes, the investigation diary and the code fix must be separate commits with separate types, or the mixed commit erodes the very auditability the diary was meant to provide.

**Seed:** Should the pre-commit `commit-msg` hook reject messages containing "wip" on `main`, or would a CI check that detects mixed file-type clusters (production code + docs + diary in one commit) be more surgical?
