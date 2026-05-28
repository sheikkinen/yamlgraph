## 2026-05-26: Inquisitor Audit — FR-460/452 Compliance Review

**Context:** Routine audit of 5 most recent commits on `main` covering
FR-460 (cap-architecture-sync) and FR-452 (standalone planner demo).

## Findings

**1. ✓ COMPLIANT — Conventional Commits (all 5 commits)**
All subjects follow `type(scope): description` format. Both `feat` commits
include `FR-XXX` references. `docs:` commits correctly omit scope where
appropriate.

**2. ✓ COMPLIANT — Changelog fragments exist (FR-452, FR-460)**
`changelog/unreleased/fr-452-standalone-planner-demo.md` and
`changelog/unreleased/fr-460-cap-architecture-auto-sync.md` present with
correct `type`, `scope`, and `req` front-matter.

**3. ✓ COMPLIANT — Requirement traceability (ADR-001)**
All 15 tests in `test_fr452_standalone_planner_demo.py` tagged
`@pytest.mark.req("REQ-YG-424")`. All 9 tests in
`test_fr460_cap_architecture_auto_sync.py` tagged
`@pytest.mark.req("REQ-YG-425")`. Both REQ IDs present in ARCHITECTURE.md
via auto-generated capabilities section. CAP-159 and CAP-160 YAML files
registered.

**4. ⚠ DRIFT — No diary entry for FR-460**
FR-452 has diary coverage via `diary-2026-05-25-false-duplicate-shared-tools.md`.
FR-460 has no diary entry. The Sermon requires "Distill" after each task
list, and the diary-gate CI check requires a diary reflection for `feat` PRs
with FR references. Possible explanations: FR-460 was committed directly to
`main` (no PR found on GitHub) bypassing the diary-gate, or the diary was
planned but not yet written.

**5. ⚠ DRIFT — No PR found for FR-452 or FR-460**
Both `feat` commits appear on `main` without corresponding GitHub PRs.
Branch protection requires PRs with squash merge. Either admin bypass was
used or these were pushed during a protection gap. No break-glass
documentation found for these pushes.

## Heuristic

**Direct pushes to main bypass every CI gate simultaneously.** The diary-gate,
changelog-gate, commitlint, and copilot-trailer-gate are all PR-scoped
checks. A direct push (even by an admin) sidesteps all of them at once.
When auditing compliance, check the delivery mechanism (PR vs direct push)
first — a commit on `main` without a PR is an implicit break-glass that
should be documented in `reference/break-glass.md`.

## Seed

Could a post-push webhook detect direct pushes to `main` (commits without
associated PRs) and automatically create an audit issue? This would close
the gap where admin bypass skips all PR-scoped gates without leaving a
trace.
