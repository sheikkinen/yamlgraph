## 2026-04-19: Inquisitor Audit — REQ-YG-238 ID Collision; Sixth-Cycle Cross-Wiring

**Context:** Audited the 5 most recent commits on `feat/fr-238-pipeline-accumulated-state-docs` (a25efc08..391467f3) covering FR-238 pipeline accumulated state implementation, FR-237/238 feature request docs, demo-output updates, and a diary whitespace fix. This is the sixth consecutive audit cycle examining the FR-234 changelog `req` cross-wiring first identified in audit-171.

**Findings:**

1. ✗ **VIOLATION — REQ-YG-238 ID collision.** Two unrelated requirements share REQ-YG-238 in ARCHITECTURE.md: (a) Chatterbox speak CLI (FR-237, line 540) and (b) Pipeline Accumulated State (FR-238, newly added). FR-237 work pre-allocated the ID before FR-238 was created. The Chatterbox speak CLI entry must be renumbered. This is the `partial_remediation` trap — the FR-237 author claimed REQ-YG-238 for a sub-capability, then FR-238 legitimately used the same ID for a different feature. Requirement IDs are a shared namespace; allocation without checking for future collisions creates silent conflicts that `req_coverage.py` cannot detect because both entries parse correctly.

2. ✗ **VIOLATION — FR-234 changelog `req` cross-wiring survives 6th cycle.** `changelog/unreleased/fr-234-parallel-fan-out-edges.md` has `req: REQ-YG-235` (Chatterbox voice clone) instead of `req: REQ-YG-237` (parallel fan-out edges). Six audits, zero corrections. The structural deadlock identified in audit-175 (Inquisitor lacks `.chaplain/inbox/` write authority) remains. This finding is now administrative record; convergence requires human action or authority expansion.

3. ⚠ **DRIFT — RED-GREEN separation absent.** Commit e40e87cd (`feat(state-builder)`) bundles 267 lines of new tests (`test_state_builder_reducers.py`) with 55 lines of production changes (`state_builder.py`) in a single commit. Commandment 7 requires RED (failing test) and GREEN (fix) as separate commits. The tests exist and are tagged, but the proof trail is a single commit, not the mandated two-step.

4. ⚠ **DRIFT — Residual merge conflict marker fixed incidentally.** The feat commit replaced `>>>>>>>origin/main` in ARCHITECTURE.md with the correct CAP-96 row. This means a merge conflict marker survived in a tracked file across prior commits — a defect that `conflict-check` CI and `check-merge-conflict` pre-commit hook should have caught. The fix is welcome but the prior escape is concerning.

5. ✓ **COMPLIANT — FR-238 traceability otherwise complete.** Conventional Commits on all 5 commits. FR reference in feat title. Changelog fragment (`fr-238-pipeline-accumulated-state.md`) with correct `req: REQ-YG-238`. CAP-96 registered. 17 test functions tagged `@pytest.mark.req("REQ-YG-238")`. noqa coverage 83/95, 0 undocumented. ARCHITECTURE.md requirement entry added.

**Heuristic:** Requirement IDs are a monotonic shared counter, not a per-FR allocation. When FR-N creates requirement entries, it must check `max(REQ-YG-*)` and allocate from the next unused ID, regardless of whether the FR number matches. The convention `FR-N → REQ-YG-N` is a heuristic, not a contract — when an FR produces multiple requirements (FR-237 needed REQ-YG-234, REQ-YG-235, REQ-YG-238), collisions become inevitable unless the allocator scans the namespace first.

**Seed:** Should `req_coverage.py` grow a `--unique` flag that fails when two distinct requirement rows share the same REQ-YG-XXX ID? This would catch ID collisions at CI time, preventing the silent conflict that allowed two capabilities to claim REQ-YG-238.
