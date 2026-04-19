## 2026-04-19: Inquisitor Audit — Partial Remediation in FR-242 Changelog Fix

**Context:** Audited latest 5 commits (eb2a6a25..230d160b) covering FR-240 (a2a_call node), FR-241 (worktree self-heal), FR-242 (changelog req cross-wiring fix), a chatterbox voice-cloning fix, and an FR-244 docs commit.

**Findings:**

1. **✗ VIOLATION — FR-240 changelog body text still cross-wired.** Fragment `fr-240-a2a-call-node-type.md` front-matter correctly reads `req: REQ-YG-243` (fixed by FR-242), but the body text still says `(REQ-YG-239)`. The condemning test in `test_changelog_req_cross_wiring.py` validates only front-matter, not body text — the `partial_remediation` trap. Fix all occurrences, not just the cited one.

2. **⚠ DRIFT — FR-242 has no changelog fragment of its own.** A `fix` PR should produce a changelog fragment per the changelog-gate. The commit modified existing fragments but created none for itself. The CI gate likely passed because fragments were present in the diff, but the fix itself is unrecorded in the changelog.

3. **⚠ DRIFT — Generic author identity on eb2a6a25.** The HEAD commit (`docs(FR): add FR-244...`) uses `Test <test@test.com>` as author — an automated/placeholder identity that obscures provenance.

4. **✓ COMPLIANT — TDD followed across all feat/fix commits.** FR-240, FR-241, FR-242 each have condemning tests with `@pytest.mark.req` tags. Diary reflections present for all FR-referenced work.

5. **✓ COMPLIANT — All noqa suppressions documented.** `noqa_coverage.py` reports 0 undocumented suppressions.

**Heuristic:** When a fix targets metadata (front-matter, headers, config keys), extend the condemning test to also validate the corresponding prose/body text. Structural fixes that leave semantic echoes of the old value are the `partial_remediation` trap wearing a "metadata-only" costume.

**Seed:** Should the changelog aggregation script cross-check `req:` front-matter against `(REQ-YG-XXX)` references in body text and fail on mismatch — closing the partial-remediation gap at generation time?
