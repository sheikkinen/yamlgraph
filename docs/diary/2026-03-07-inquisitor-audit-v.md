## 2026-03-07: Inquisitor Audit V — five audits, same two wounds

**Context:** Fifth audit covering commits `5afaf99`..`2cc3c10` (5 commits: FR-112 Inception provider feat, v0.4.60 release, diary Entry 91, provider-count docs fix, Knowledge Graph expansion). Primary question: have the two persistent ✗ VIOLATIONS survived yet another audit cycle?

**Findings:**

1. **✗ VIOLATION — ARCHITECTURE.md line 1115 still says "7 providers".** Fifth consecutive audit. Line 219 was corrected to "8" by `55b890b`, but line 1115 (module table row for `utils/llm_factory.py`) was missed. Partial remediation confirmed — the exact trap named in Audit IV's heuristic ("grep for *all* occurrences") was repeated. The Knowledge Graph's `partial_remediation` trap is documented but not practiced.

2. **✗ VIOLATION — FR-112 still "Status: Draft".** Fifth consecutive audit. Feature is implemented, tested, merged, released as v0.4.60, documented in CHANGELOG, provider count updated — yet the feature request header reads `Status: Draft`. The Sermon (Enforce) requires updating implementation status. At this point the prior audit's heuristic applies: "A violation that survives three audits is no longer drift — it is policy."

3. **✓ COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description`. FR reference on feat commit. Docs commits use `docs:` prefix correctly.

4. **✓ COMPLIANT — CHANGELOG and noqa Confessions.** `[0.4.60]` accurately documents FR-112 and FR-110. Both noqa suppressions (ANN001, ARG002) have CONF-XXX entries. 102 confessions total.

5. **⚠ DRIFT — No Inception-specific REQ-YG-XXX.** Tests use generic REQ-YG-010/011 (factory management). Technically covers the capability, but every other provider-specific behavior (base_url, default model) is validated without a dedicated requirement ID. ADR-001 traceability is thin for the 8th provider.

**Heuristic:** *An audit that flags the same violation five times without triggering a corrective action is not an audit — it is a ritual.* The Knowledge Graph explicitly warns: `audit_as_ritual: "3+ audits without fix → ritual, not process"`. The cure is mechanical: either fix the violation *now* or formally accept it as a known deviation with a rationale. Ambiguity between "should fix" and "accepted" makes every future finding negotiable.

**Seed:** Should the Inquisitor be granted authority to make trivial corrective commits (e.g., updating a status field, fixing a count in a table) when the same ✗ persists across ≥3 audits? A read-only auditor that cannot act on micro-fixes creates an asymmetry: the cost of flagging exceeds the cost of fixing.
