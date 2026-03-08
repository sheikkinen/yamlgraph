## 2026-03-07: Inquisitor Audit X — self-repair in motion, CHANGELOG gap persists

**Context:** Tenth audit covering commits `b14960e`..`963a67f` (5 commits: FR-115/FR-116 chore scaffolding, FR-116 feat PR merge, two enforce_worktree chore fixes, FR-115 chaplain approval). New pattern: the audit process has spawned its own remediation — FR-115 (inquisitor auto-propose) was approved in `963a67f`, designed to automate the very fixes this series of audits has been flagging.

**Findings:**

1. **✗ VIOLATION — FR-116 still missing CHANGELOG entry (3rd consecutive audit).** `4765fdc` (`feat: FR-116 implementation (#4)`) added CAP-35, REQ-YG-116, 5 tagged tests, a demo script — but `CHANGELOG.md [Unreleased]` has zero mention. Audits VIII, IX, and now X have flagged this. Per Audit VII's principle: a finding that persists across 3+ audits without action must either escalate or be formally accepted. **Escalation: FR-116 CHANGELOG entry should block next release.**

2. **✓ COMPLIANT — Conventional Commits.** All 5 commits use valid prefixes: `docs(chaplain):`, `chore(enforce):` ×2, `feat:`, `chore:`. Co-authored-by trailer present where Copilot participated.

3. **✓ COMPLIANT — ADR-001 traceability for FR-116.** REQ-YG-116 in ARCHITECTURE.md, CAP-35, `req_coverage.py` updated, all 5 test functions tagged `@pytest.mark.req("REQ-YG-116")`.

4. **⚠ DRIFT — Known deviations unchanged.** ARCHITECTURE.md line 1125 still reads "7 providers" (should be 8). FR-112 status still "Draft" (should be "Done"). Both formally accepted in Audit VIII with v0.5.0 deadline. No action until release.

5. **✓ COMPLIANT — noqa confessions and diary entries.** Both existing suppressions (ANN001 in executor_async.py, ARG002 in token_tracker.py) covered by confessions. Diary entries exist for the Judgement and prior chaplain work.

**Heuristic:** *When the audit process generates its own feature request (FR-115), the system is self-repairing — but only if the FR ships.* Nine audits produced the diagnosis; the tenth witnesses the prescription (FR-115 approved). The risk now is that FR-115 joins FR-116's CHANGELOG in the backlog of approved-but-unshipped fixes. A process that diagnoses and prescribes but doesn't treat has merely added a step.

**Seed:** FR-115 (auto-propose) is approved and FR-116's CHANGELOG gap is escalated. What is the right forcing function to ensure FR-115 implementation doesn't itself become a recurring audit finding? Should the next Inquisitor audit be conditional — "no audit until FR-115 ships or FR-116 CHANGELOG is written"?
