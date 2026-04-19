## 2026-04-19: Inquisitor Audit — FR-239 numbering collision recurrence and changelog REQ mismatch

**Context:** Audited the 5 most recent commits (`172b4189`..`629895ff`) covering FR-239 (chatterbox multilingual CLI), FR-240 (a2a_call node type, in-progress), and FR-241 (worktree teardown self-heal, planning). Checked Conventional Commits format, changelog fragments, ADR-001 traceability, `@pytest.mark.req` tags, diary reflections, and noqa confessions.

**Findings:**

1. **✗ VIOLATION — FR-239 numbering collision (recurring).** Two feature requests share FR-239: `FR-239-chatterbox-speak-multilingual.md` and `FR-239-meta-yamlgraph-self-improving-graphs.md`. This is the same class of defect found in audit #183 (FR-237 collision). The seed from that audit proposed a pre-commit hook to detect duplicate FR numbers — it was not implemented, and the error recurred immediately. Traceability queries (`git log --grep FR-239`) now return unrelated commits.

2. **⚠ DRIFT — Wrong REQ in changelog fragment.** `changelog/unreleased/fr-239-chatterbox-speak-multilingual.md` declares `req: REQ-YG-239`, but ARCHITECTURE.md maps FR-239/CAP-100 to REQ-YG-242. REQ-YG-239 is "Node-Level Caching (FR-032)" — a completely different capability. The test file correctly uses `@pytest.mark.req("REQ-YG-242")`, so the changelog fragment is the sole inconsistency.

3. **✓ COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description`. The feat commit (`42c2a72b`) includes FR reference and PR number (`#108`).

4. **✓ COMPLIANT — TDD, diary, and demo gates.** FR-239 has tests tagged `@pytest.mark.req("REQ-YG-242")`, a diary reflection, and `demo-output.log`. FR-240 has a diary reflection committed separately.

5. **✓ COMPLIANT — noqa confessions.** All noqa suppressions in the codebase have corresponding CONF-XXX entries in `docs/confessions.md`.

**Heuristic:** When the same class of defect recurs after being identified, the audit seed should be treated as an action item, not a suggestion. Audit #183 identified the FR numbering collision pattern and proposed a pre-commit hook. That hook was never created, and the identical defect appeared in the very next feature. Seeds that address structural enforcement gaps should be escalated to FRs within 24 hours of the audit.

**Seed:** Should the Inquisitor audit itself track "open seeds" — unimplemented enforcement proposals from prior audits — and auto-escalate them to FRs after a configurable recurrence threshold (e.g., same defect class seen twice)?
