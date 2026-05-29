## 2026-05-28: Inquisitor Audit — FR-461 Traceability Gap

**Context:** Audit of HEAD (`49556eb9`, v0.5.4, 2026-05-27). Two new commits
since audit 252: FR-461 persona & scenario pipeline (squash merge via PR #451)
and the 0.5.4 release commit. Auditing the latest 5 commits on main.

**Findings:**

1. **✗ VIOLATION — FR-461 missing CAP file, REQ ID, and unit tests (ADR-001)**
   `feat(demos): FR-461` introduced a new demo pipeline but has no capability
   YAML (`capabilities/CAP-XXX-*.yaml`), no REQ-YG marker, no `req:` in its
   changelog fragment, and no unit tests. FR-452 — the prior demo feat — set
   the precedent with CAP-159, REQ-YG-424, and 15 `@pytest.mark.req`-tagged
   tests. The `changelog-req-gate` CI check should have blocked this, but a
   missing `req:` field may pass as "no req to validate" rather than "required
   req absent." The `req_coverage.py` script reports 144/144 ✅ — because the
   CAP was never created, the gap is invisible to the existing gate.

2. **⚠ DRIFT — FR-460 diary still missing (3rd consecutive audit)**
   Audits 251, 252, and now 253 note the absence of a diary entry for FR-460.
   This is the `audit_as_ritual` trap: three audits have cited the gap without
   remediation. Either write the diary or accept the gap with rationale.

3. **✓ COMPLIANT — Conventional Commits format**
   All 5 commits follow `type(scope): description`. Both `feat` commits
   reference FR numbers. The release commit uses `chore(release):`.

4. **✓ COMPLIANT — No new noqa suppressions**
   No `noqa` additions in the audited range.

5. **✓ COMPLIANT — FR-461 diary and demo-output present**
   `diary-2026-05-27-amend-as-contamination.md` reflects the cognitive trap
   (amend contamination). `demo-output.log` satisfies the demo-gate.

**Heuristic:** A gate that validates "is the `req:` field correct?" but not
"is the `req:` field present?" creates a blind spot. The `changelog-req-gate`
caught wrong REQ IDs in prior audits but let FR-461 through because absence
≠ invalidity. This is the `gate_checks_shape_not_substance` trap applied to
optional fields: if a `feat` commit *must* have a REQ, the gate must enforce
presence, not just correctness.

**Seed:** Should `changelog-req-gate` be upgraded to require `req:` on all
`feat`-type fragments? The cost is one extra line per fragment; the benefit is
closing the traceability gap that let FR-461 ship without a capability entry.
Alternatively, should demo-only feats (`scope: demos`) be explicitly exempted
from ADR-001, with that exemption documented in ARCHITECTURE.md?
