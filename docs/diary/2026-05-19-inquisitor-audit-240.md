## 2026-05-19: Inquisitor Audit — Questionnaire utilities and chaplain investigation

**Context:** Audited the latest 5 commits on `main` (fbeb44c0..17da4033) covering FR-421 (questionnaire gap utilities), FR-419 (ActionConfig schema boundary), FR-416 (event_key passthrough), and two `chore: investigation` WIP commits. Checked Conventional Commits, changelog fragments, req traceability, diary entries, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — FR-421 (`fbeb44c0`) exemplary: Conventional Commit with FR ref, changelog fragment with REQ-YG-409, all tests carry `@pytest.mark.req`, diary reflection present, ARCHITECTURE.md updated.
- ✓ COMPLIANT — FR-419 (`b925bff9`) and FR-416 (`17da4033`) both carry Conventional Commit format, changelog fragments, and `@pytest.mark.req("REQ-YG-319")` on all test functions.
- ⚠ DRIFT — Two identical `chore: investigation of chaplain failures, wip` commits (`f35a3254`, `27795d03`) landed on main with the same subject line. WIP commits on the default branch violate Commandment 8 (kill entropy) and the squash-merge convention. These should have been squashed or kept on a feature branch.
- ✗ VIOLATION — Commit `27795d03` introduces `# noqa: S105 — ANSI colour label, not a credential` without a corresponding CONF-XXX entry in `docs/confessions.md`. The inline rationale is sound but the doctrine requires a formal confession (noqa Confessions rule).
- ✓ COMPLIANT — No new noqa suppressions in the feat/fix commits. Existing `CONF-126` reference in FR-419 diff is properly registered.

**Heuristic:** WIP commits that bypass squash-merge erode the auditability that Conventional Commits exist to provide. When investigation work must land incrementally, each commit should carry a distinct scope suffix (e.g., `chore(fsm): FR-420 extract_event dict reproduction`) rather than a generic "wip" label. The commit log is a legal record, not a scratch pad.

**Seed:** Could a pre-commit hook detect duplicate commit subjects within the last N commits on the current branch and warn before allowing the push?
