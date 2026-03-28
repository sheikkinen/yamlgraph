---

## 2026-03-27: Inquisitor Audit — Enforcement Ultimatum

**Context:** Audited the 5 most recent commits on `main` (e4a7d27..16e4973): two `docs(FR):` adding FR-203/FR-204, three `chore(examples):` improving the image pipeline. Fifth consecutive audit of this commit window (#139–#143). Prior audits identified two persistent issues. This audit shifts from observation to ultimatum.

**Findings:**

1. ✗ VIOLATION (5th flag — ENFORCEMENT ULTIMATUM) — **28/34 test functions in `tests/unit/test_image_pipeline.py` lack `@pytest.mark.req` tags.** Five audits have flagged this. The `audit_as_ritual` trap (threshold: 3) was breached at #141. The `detection_without_enforcement` cure demands: "add CI block or remove claim." `req_coverage.py` masks the gap — it counts per-capability (6 tagged → green), not per-function (82% untagged → invisible). **This is the final advisory audit for this finding.** Next occurrence must produce either (a) a `.chaplain/inbox/` proposal for remediation, or (b) explicit acceptance as technical debt documented in `docs/confessions.md`.

2. ⚠ DRIFT — The multi-commit image pipeline design arc (5 `chore(examples):` commits spanning 3 audit windows) remains without diary reflection. ThreadPoolExecutor choice, EXIF metadata strategy, and PromptMetadata dataclass introduction are undocumented design decisions. Flagged in audits #140–#142.

3. ✓ COMPLIANT — Conventional Commits format correct on all 5 commits. No changelog/diary CI gates applicable (no `feat`/`fix`).

4. ✓ COMPLIANT — All `# noqa` suppressions confessed. Requirement traceability 132/132 green.

5. ✓ COMPLIANT — FR-203/FR-204 properly structured, honouring Commandment 1.

**Heuristic:** The Inquisitor's value is bounded by its escalation power. Five identical findings prove that advisory audits are a ceiling, not a ramp. The Knowledge Graph's `inquisitor_auto_escalation` seed — "auto-create FR when audit pattern hits threshold" — is no longer speculative. It is the only path from observation to consequence. An Inquisitor that cannot escalate is a logger with opinions.

**Seed:** Should the Inquisitor carry a `--enforce` flag that, when a violation count exceeds its threshold, writes a machine-readable `.audit/violations.json` and a `.chaplain/inbox/` proposal in a single atomic action — making escalation the default and silence the opt-in?
