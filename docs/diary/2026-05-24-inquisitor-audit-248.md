## 2026-05-24: Inquisitor Audit — Deep Pass on Stale Window

**Context:** The top 5 commits on `main` (e764eeba..0977bfed) are identical to those audited in audit 247 (2026-05-23). No new commits in 24 hours. This audit performs a deeper cross-reference pass on requirement traceability, noqa confession coverage, and unresolved drift from prior audits.

**Findings:**

1. ⚠ DRIFT — **REQ-YG-162 misapplied in FR-446 changelog fragment.** The fragment `changelog/unreleased/FR-446-copilot-skill-promotion.md` declares `req: REQ-YG-162`, which describes the *append-only changelog system itself*, not Copilot skill promotion. The `req:` field should reference the requirement that the *feature* fulfills. FR-446 created documentation skills — if no REQ exists for that capability, one should be created rather than borrowing an unrelated ID. The `changelog-req-gate` CI validates the ID is *valid*, not that it's *semantically correct* — shape over substance (trap: `gate_checks_shape_not_substance`).

2. ⚠ DRIFT — **`scripts/langsmith_traces.py` still untested (escalation from audit 247).** A 259-line operational script with argument parsing, API calls, and output formatting has zero tests. Flagged as drift in audit 247, unresolved 2 days later. Commandment 7 (TDD) applies to non-trivial logic regardless of directory. Two consecutive audits flagging the same gap approaches the `audit_as_ritual` trap.

3. ✓ COMPLIANT — **noqa confession coverage: 95/95 suppressions documented.** `scripts/noqa_coverage.py` confirms every `# noqa` suppression in `yamlgraph/` has a corresponding CONF-XXX entry in `docs/confessions.md`. 149 confessions documented total.

4. ✓ COMPLIANT — **Requirement traceability: 274/274 requirements covered.** `scripts/req_coverage.py` reports full coverage across 4,430 tagged tests. No gaps.

5. ✓ COMPLIANT — **All feat commits have diary reflections and changelog fragments.** FR-446 has both `2026-05-22-reflection-fr-446-skills-knowledge-compression.md` and a changelog fragment. Chore commits appropriately excluded.

**Heuristic:** A CI gate that validates *existence* of a `req:` field but not its *semantic accuracy* is a shape-not-substance gate (CONF analogy: a confession that says "because reasons"). The `changelog-req-gate` should cross-reference the REQ description against the changelog entry's scope — or at minimum, the FR number — to catch misapplied references. When the same drift appears in two consecutive audits without remediation, the audit itself is approaching ritual status; escalate to an FR.

**Seed:** Can `changelog-req-gate` be extended to validate that the referenced REQ-YG-XXX belongs to the same capability (CAP-XX) as the FR referenced in the changelog entry — a semantic cross-reference rather than just an ID existence check?
