## 2026-04-19: Inquisitor Audit — Persistent REQ Cross-Wiring

**Context:** Audited the 5 most recent commits (bc739f22..cac26a7f) covering FR-234, FR-235, FR-236, FR-237 work delivered 2026-04-18/19. This is the second audit cycle examining the REQ cross-wiring first identified in audit-171.

**Findings:**

1. ✗ **VIOLATION — REQ cross-wiring persists from audit-171, now 2nd cycle unfixed.** FR-234 changelog fragment (`req: REQ-YG-235`) should be `REQ-YG-237`. FR-235 changelog fragment (`req: REQ-YG-235`) should be `REQ-YG-236`. Both fragments share the same wrong REQ, confirming the copy-paste origin diagnosed in audit-171. Two audit cycles without correction triggers the `audit_as_ritual` trap: auditing the same defect without fixing it is ritual, not process.

2. ✗ **VIOLATION — FR-234 commit body cites wrong CAP and REQ.** Body says "Capability: CAP-93, Requirement: REQ-YG-162" but the actual capability file is `CAP-95-parallel-fanout-edges.yaml` and ARCHITECTURE.md maps FR-234 → REQ-YG-237. CAP-93 is `chatterbox-voice-clone-demo`. This is a second instance of cross-wiring from the same session, reinforcing the copy-paste root cause.

3. ✓ **COMPLIANT — All 5 commits follow Conventional Commits.** Types: `docs`, `chore`, `feat`, `fix`. FR references present on all `feat`/`fix` commits.

4. ✓ **COMPLIANT — Test req tags correct.** FR-234 tests tagged `REQ-YG-237`, FR-235 tests tagged `REQ-YG-236` — both match ARCHITECTURE.md. The cross-wiring is isolated to changelog fragments and commit bodies, not test traceability.

5. ✓ **COMPLIANT — Diary, confessions, demos present.** All feat/fix commits have diary reflections. CONF-035–038 line references updated after FR-236 worktree changes. Demo-output.logs updated in chore commit.

**Heuristic:** The `audit_as_ritual` trap is now active. Audit-171 diagnosed the defect and even proposed a mechanical cure (extending `req_coverage.py` to validate changelog fragment `req:` fields). No action was taken between audits. When an Inquisitor finding survives two cycles, it must escalate to a Feature Request — advisory findings decay into noise.

**Seed:** Should an Inquisitor finding that survives N audit cycles auto-generate a Feature Request in `.chaplain/inbox/`, converting the observation into an enforceable work item? What is the right threshold for N — 2 (current case) or 3 (the Scripture's existing `audit_as_ritual` threshold)?
