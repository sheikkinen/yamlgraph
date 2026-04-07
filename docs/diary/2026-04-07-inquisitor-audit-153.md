## 2026-04-07: Inquisitor Audit — Post-Release 0.4.66 (34e0920..b733056)

**Context:** Second audit today, focused on the 5 most recent commits after the previous audit shifted HEAD. Covers the 0.4.66 release cycle, FR-214 bug fix, reference additions, and batch script bundling. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), diary entries, and noqa confessions.

**Findings:**

1. ✓ **COMPLIANT** — `fix(template): FR-214` (28eba56) is textbook Scripture: condemning test with RED, fix with GREEN, `@pytest.mark.req("REQ-YG-216")` on both tests, REQ-YG-216 added to ARCHITECTURE.md, capability updated in CAP-04, changelog fragment in `changelog/0.4.66/`, diary reflection included. Exemplary.

2. ✓ **COMPLIANT** — Release 0.4.66 (877bb2c, 8fc47ae) follows the release checklist: changelog freeze then version sync. Fragment correctly moved from `unreleased/` to `0.4.66/`.

3. ✓ **COMPLIANT** — noqa confessions: `noqa_coverage.py` reports 57 suppressions, 0 undocumented. All accounted for.

4. ✗ **VIOLATION** — Commit 34e0920 (`chore: image pipeline batch scripts`) bundles 15 diary files spanning 9 dates (2026-03-29 through 2026-04-07) with 2 unrelated batch scripts. Recurrence of audit-152 finding #2 — same commit, same violation. `mixed_commits_erode_auditability` violated twice in the same commit. This is now a pattern, not an incident.

5. ⚠ **DRIFT** — Commit b733056 (`chore: Reference updates`) is functionally valid but the message is generic. `chore(reference): add probe-recap-questionnaire` would improve auditability.

**Heuristic:** When the same violation recurs across audits without remediation, it has graduated from drift to systemic pattern. The diary-accumulation antipattern needs a structural fix, not another finding.

**Seed:** Should the diary-gate CI job be extended to detect diary files with timestamps older than 48 hours from the commit date, flagging batch-accumulated entries before they reach `main`?
