## 2026-04-19: Inquisitor Audit — REQ Cross-Wiring Persists; Renumber Incomplete

**Context:** Audited the 5 most recent commits (7a6804a2..be7ea746) spanning FR-238 user-configurable reducers, FR-237 Chatterbox consolidation, and associated chore/docs work. This is the sixth audit cycle examining the FR-234 changelog REQ cross-wiring first identified in audit-171.

**Findings:**

1. ✗ **VIOLATION — FR-234 changelog REQ cross-wiring survives 6th cycle.** `changelog/unreleased/fr-234-parallel-fan-out-edges.md` has `req: REQ-YG-235` (Chatterbox voice clone) instead of `req: REQ-YG-237` (parallel fan-out edges). ARCHITECTURE.md correctly maps CAP-95 → REQ-YG-237. Six observations, zero corrections. The `audit_as_ritual` trap is fully activated — the Inquisitor's diary-only write scope prevents depositing the prescribed `.chaplain/inbox/` escalation artifact, creating a structural deadlock where detection cannot trigger correction.

2. ⚠ **DRIFT — FR-238 changelog fragment not renumbered.** Merge commit `be7ea746` ("renumber REQ-YG-238→241") updated ARCHITECTURE.md and `test_state_builder_reducers.py` to REQ-YG-241, but `changelog/unreleased/fr-238-pipeline-accumulated-state.md` still says `req: REQ-YG-238`. ARCHITECTURE.md now defines REQ-YG-238 as "Chatterbox speak CLI" (FR-237), not pipeline accumulated state. The changelog fragment points to the wrong requirement — a `partial_remediation` trap: the renumber was applied to tests and architecture but missed the changelog boundary.

3. ✓ **COMPLIANT — Conventional Commits, test traceability, diary entries, noqa confessions.** All 5 commits follow Conventional Commits with correct types and FR references. 17 new tests in `test_state_builder_reducers.py` tagged `REQ-YG-241`. Both FR-237 and FR-238 have diary reflections with cognitive traps and seeds. All 19 `# noqa` suppressions in `yamlgraph/` have corresponding CONF-XXX entries in `docs/confessions.md`.

**Heuristic:** When a renumber operation touches multiple artifact types (ARCHITECTURE.md, tests, changelog fragments, capability YAML), verify completeness by grepping for the old identifier across all artifact boundaries — not just the ones that come to mind. The `partial_remediation` trap activates precisely when the operator believes the job is done after fixing the most visible occurrences. A post-renumber `grep -r "REQ-YG-238"` would have caught the changelog fragment in seconds.

**Seed:** Should `scripts/req_coverage.py` be extended to cross-check changelog fragment `req:` fields against ARCHITECTURE.md requirement definitions, catching cross-wiring at CI rather than during manual audit?
