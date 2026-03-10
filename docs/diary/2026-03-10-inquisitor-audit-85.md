## 2026-03-10: Inquisitor Audit — CHANGELOG erasure unresolved; anonymous authorship persists

**Context:** Audited the 5 most recent commits on `main` (e4a76fb..68d138b). Window contains 2 `fix`, 2 `docs(FR)`, 1 `chore`. Prior audit-84 flagged CHANGELOG history deletion and anonymous authorship — this audit checks for remediation and new issues.

**Findings:**

1. ✗ VIOLATION — CHANGELOG entries for FR-176, FR-169, FR-173, FR-172, FR-167 deleted in `39ca88b` remain missing after `68d138b`. Five shipped capability records erased. Audit-84 flagged this; no remediation applied. Commandment 10: "let the CHANGELOG bear witness to the evolution of the Word." Current `[Unreleased]` section contains zero mentions of these FRs. The entries existed before `39ca88b` and were removed as collateral in a conflict resolution.

2. ⚠ DRIFT (recurrent x4) — 4 of 5 commits authored by `Test <test@test.com>`. Flagged in audits 82, 83, 84 without remedy. Per Scripture's `audit_as_ritual` trap: "3+ audits without fix → ritual, not process." This has graduated from drift to unresolved defect. Only `e4a76fb` carries proper attribution (`sheikki@yahoo.com`).

3. ⚠ DRIFT — `68d138b` (`fix(tests)`) also modifies `examples/enforce/graph.yaml`, simplifying prompt content. Scope extends beyond the stated test fix. Commandment 7 expects surgical commits. The graph change is reasonable but belongs in a separate commit or a broader scope declaration.

4. ⚠ DRIFT — Neither `fix` commit (68d138b, 39ca88b) has a diary reflection. diary-gate CI only blocks `feat`/`fix` with `FR-XXX` reference, so non-FR fixes bypass the Distill step. Enforcement gap persists from audit-84.

5. ✓ COMPLIANT — All test files touched (test_enforce_reflexion_loop.py, test_enforce_yamlgraphication.py, test_bugfix_pipeline.py) carry class-level `@pytest.mark.req` tags. Both `# noqa` suppressions (ANN001, ARG002) remain confessed in `docs/confessions.md`. ADR-001 and noqa Confessions doctrine intact.

**Heuristic:** An audit finding that persists across 3+ audits without action is no longer a finding — it is an accepted defect masquerading as a tracked risk. The `audit_as_ritual` trap applies: either fix the root cause (configure enforce pipeline git identity; restore deleted CHANGELOG entries) or explicitly accept the deviation in a documented ADR. Repeated flagging without resolution erodes the audit's authority.

**Seed:** Should unresolved VIOLATION findings from prior audits be tracked as GitHub Issues with a `doctrine-debt` label, so they enter the normal triage/assignment workflow instead of accumulating silently in diary prose?
