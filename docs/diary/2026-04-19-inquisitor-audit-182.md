## 2026-04-19: Inquisitor Audit — FR-032, FR-069, FR-237 and CAP Numbering

**Context:** Audited the 5 most recent commits spanning three merged PRs (#103 FR-069 per-node timeout, #104 FR-032 node-level cache, #105 FR-237 race/pipeline docs) plus a chore CAP-renumber commit on the `feat/fr-238` branch and a merge commit.

**Findings:**

1. **✓ COMPLIANT — Conventional Commits & Traceability:** All non-merge commits follow `type(scope): FR-XXX description` format. Both `feat` PRs reference their FR numbers. CHANGELOG fragments exist in `changelog/unreleased/` for all three PRs. ARCHITECTURE.md has REQ entries (REQ-YG-078, REQ-YG-239, REQ-YG-240). All new test files carry `@pytest.mark.req` tags. Diary reflections exist for FR-032, FR-069, and FR-237. noqa suppressions are fully covered in `docs/confessions.md`.

2. **⚠ DRIFT — CAP-96 Numbering Collision:** PRs #103 (FR-069) and #105 (FR-237) both created `CAP-96`, requiring a post-hoc chore commit to renumber. The `aggregate_capabilities.py` script and CI did not prevent this collision. Two PRs merged in close succession each claimed the next sequential number independently.

3. **⚠ DRIFT — Mixed Concern in Squash Merge:** PR #103 (FR-069 timeout) includes `feature-requests/FR-240-a2a-call-node-type.md` — an unrelated feature request. Per `mixed_commits_erode_auditability`: one concern per commit for clear blame and revert. Unrelated FR files should ship in their own commit or PR.

4. **✓ COMPLIANT — Demo Gate Adherence:** Both feat PRs include `demo-output.log` files proving demo execution (cache demo, map-timeout demo).

5. **✓ COMPLIANT — Diary Quality:** All three diary reflections name specific traps avoided (downstream_fix, partial_remediation, false_duplicate, intent_drift), extract actionable heuristics, and plant forward-looking Seeds. High signal, no ritual.

**Heuristic:** CAP ID assignment needs an atomic gate — either `aggregate_capabilities.py` should fail on duplicate IDs at pre-commit, or a CI check should block PRs that introduce a CAP ID already present on `main`. Advisory numbering + parallel PRs = guaranteed collisions.

**Seed:** Could `aggregate_capabilities.py` auto-assign the next available CAP ID from a monotonic counter stored in a single source-of-truth file, removing human-assigned numbering entirely?
