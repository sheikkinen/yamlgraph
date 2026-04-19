## 2026-04-19: Inquisitor Audit — FR-251/252/253 Compliance Review

**Context:** Audited the 5 most recent commits on `main` (bdfb5faa through a0e46835) covering three feature implementations (FR-251 remote inbox hardening, FR-252 python node variables, FR-253 a2a consumer demotion) and two docs-only FR staging commits. Checked against Conventional Commits, changelog fragments, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow `type(scope): FR-XXX description` format. The three feat commits include FR references. The two docs commits use `docs(FR):` correctly.

2. ✓ **COMPLIANT — Changelog Fragments**: All three feat PRs (FR-251, FR-252, FR-253) include changelog fragments in `changelog/unreleased/` with appropriate YAML front-matter. FR-251 and FR-252 include `req:` in front-matter.

3. ⚠ **DRIFT — FR-253 changelog fragment omits `req:` front-matter**: The FR-253 changelog fragment references `(REQ-YG-253)` in the body text but omits the `req:` field from YAML front-matter. REQ-YG-253 exists in both `ARCHITECTURE.md` and `CAP-105`. The `changelog-req-gate` CI validates front-matter `req:` — omitting it bypasses the cross-validation that other fragments (FR-251, FR-252) correctly participate in. The field is documented as optional, so CI passes, but the inconsistency undermines the gate's purpose.

4. ✓ **COMPLIANT — ADR-001 Requirement Traceability**: All three feat commits include `@pytest.mark.req` tags on tests (29 in a2a_contrib, 8 in harden_remote_inbox, 32 in python_nodes). ARCHITECTURE.md updated in FR-251 and FR-253. No orphaned requirements detected.

5. ✓ **COMPLIANT — Diary Reflections**: All three features have diary entries: FR-252 (2026-04-19), FR-251 (2026-04-20), FR-253 (2026-04-21). Each contains traps, heuristics, and seeds per the Sermon's Distill requirement.

**Heuristic:** `optional_field_as_escape_hatch` — When a CI gate validates an optional field, omitting the field bypasses the gate silently. If the field's value exists (REQ referenced in body), omitting it from the structured location is not a deliberate choice but accidental inconsistency. Consider: should the gate warn when a `REQ-YG-XXX` pattern appears in the body but `req:` front-matter is absent?

**Seed:** Could the `changelog-req-gate` be extended to detect REQ-YG-XXX patterns in the fragment body and warn (or fail) when they exist but `req:` front-matter is missing? This would close the gap between "optional field" and "field present but misplaced" — a distinction the current gate cannot make.
