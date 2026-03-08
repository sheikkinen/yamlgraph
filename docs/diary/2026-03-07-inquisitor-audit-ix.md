## 2026-03-07: Inquisitor Audit IX — CHANGELOG debt compounds, known deviations persist

**Context:** Ninth audit covering commits `63db5d3`..`6c737d9` (5 commits: FR-114 revert, FR-115/FR-116 chore, FR-116 feat PR merge, two enforce_worktree chore fixes). Primary question: has the FR-116 CHANGELOG gap flagged in Audit VIII been addressed? Have the two formally-accepted known deviations (provider count, FR-112 status) changed?

**Findings:**

1. **✗ VIOLATION — FR-116 still missing CHANGELOG entry (2nd audit).** `4765fdc` (`feat: FR-116 implementation`) added CAP-35, REQ-YG-116, 5 tagged tests, a demo script — but `CHANGELOG.md` under `[Unreleased]` has zero mention of FR-116, watch-enforce integration, or worktree spawning. Commandment 10: "let the CHANGELOG bear witness." Audit VIII flagged this; it remains unfixed.

2. **✓ COMPLIANT — FR-116 requirement traceability (ADR-001).** REQ-YG-116 in ARCHITECTURE.md (line 631), CAP-35 (line 311), `req_coverage.py` updated, all 5 test functions tagged `@pytest.mark.req("REQ-YG-116")`. Internal traceability is exemplary.

3. **✓ COMPLIANT — Conventional Commits.** All 5 commits use valid prefixes: `chore(enforce):` ×2, `feat:` ×1, `chore:` ×1. The revert (`63db5d3`) uses git's auto-format which is acceptable. The problematic FR-114 merge commit (`eeb0aa7`) has scrolled out of the 5-commit window.

4. **⚠ DRIFT — Known deviations unchanged.** ARCHITECTURE.md line 1125 still reads "7 providers" (should be 8). FR-112 status still reads "Draft" (should be "Done"). Both formally accepted in Audit VIII with v0.5.0 deadline. No action required until release.

5. **✓ COMPLIANT — noqa confessions.** Both existing suppressions (`ANN001` in executor_async.py, `ARG002` in token_tracker.py) covered by CONF-003 and CONF-002. No new unconfessed suppressions found.

**Heuristic:** *A feat commit that passes ADR-001 traceability (requirements, tests, capability table) but fails CHANGELOG is a systematic gap, not a one-off miss.* The `enforce_worktree.sh` pipeline automates code and test scaffolding but has no CHANGELOG step. When the same gap recurs across consecutive audits, the fix belongs in the pipeline, not in human memory.

**Seed:** Could `enforce_worktree.sh` inject a CHANGELOG entry by parsing the FR title and inserting a line under `[Unreleased] → Added` before committing? The template is mechanical: `- **FR-XXX [Title]**: [one-line summary]. (REQ-YG-XXX)`. Automating this would close the last systematic gap in the feat→merge pipeline.
