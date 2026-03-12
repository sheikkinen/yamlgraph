## 2026-03-12: Inquisitor Audit — FR-186/187 Traceability Gaps

**Context:** Audited the 5 most recent commits (09c8077..ad568d6) covering FR-185 philosopher copilot migration, FR-186 serialization sweep, FR-187 CI security scan, and a philosopher bugfix. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), diary entries (Sermon: Distill), and noqa confessions.

**Findings:**

1. **✗ VIOLATION — FR-187 REQ cross-reference mismatch.** Changelog fragment `FR-187-ci-dependency-security-scan.md` and ARCHITECTURE.md capability table row 68 both cite `REQ-YG-185`, but the actual requirement for CI security scan is `REQ-YG-186`. The capability YAML (`CAP-68`) and tests correctly use `REQ-YG-186`. The changelog and architecture table are wrong. Root cause: REQ-YG-185 was allocated to FR-185 (philosopher copilot nodes); the FR-187 author likely copied the number without incrementing.

2. **✗ VIOLATION — FR-186 missing changelog fragment.** Commit 80f0614 (`feat(contrib): FR-186`) has no entry in `changelog/unreleased/`. The `changelog-gate` CI job should have blocked this, but the commit was a squash merge that touched 152 files including bulk changelog format migrations — the gate may have matched on those modified files rather than requiring a new fragment.

3. **✗ VIOLATION — FR-186 missing diary entry.** No diary reflection exists for FR-186 anywhere in `docs/diary/`. The `diary-gate` CI job requires feat PRs with FR-XXX to include a diary file. Same squash-merge bypass concern as finding #2.

4. **⚠ DRIFT — Philosopher fix diary staged but uncommitted.** Commit 09c8077 (`fix(philosopher)`) has a well-written diary entry (`2026-03-12-philosopher-fix.md`) that exists only as a staged file (`git status: A`), not committed. The reflection was written but not sealed into history.

5. **✓ COMPLIANT — Conventional Commits, TDD, noqa confessions.** All 5 commits follow Conventional Commits format. FR-185 and FR-187 show clean RED/GREEN separation in squash history. All 55 noqa suppressions are documented in `docs/confessions.md` (verified by `noqa_coverage.py`).

**Heuristic:** **Verify cross-references at the boundary, not downstream.** When a new REQ-YG-XXX is allocated, the changelog fragment and ARCHITECTURE.md capability table should be updated in the same commit that creates the capability YAML — not copied from a neighboring FR. The cost of a wrong REQ reference compounds: it pollutes `req_coverage.py` output and misleads future audits.

**Seed:** Could `validate_capabilities.py` be extended to cross-check that every REQ-YG-XXX cited in `changelog/unreleased/*.md` front matter actually exists in the corresponding capability YAML, catching copy-paste REQ mismatches before they reach `main`?
