## 2026-03-12: Reflection — FR-190 Graduate `infrastructure_self_exempt` to Scripture

**Context:** Implemented FR-190, graduating the `infrastructure_self_exempt` trap to the Scripture Knowledge Graph based on 3 confirmed diary occurrences (audits 94, 95, 97). The pattern names the cognitive blind spot where meta-tooling exempts itself from the quality gates it enforces.

**Process:** Followed the graduation precedent set by FR-189 (`downstream_fix` refinement). TDD cycle: wrote 6 failing tests first (trap present, in correct section, no existing entries changed), then made the single-line addition to `.github/copilot-instructions.md`. The test structure mirrors `test_knowledge_graph_fr189.py` with an additional guard for process entries — conforming before extending (Commandment 4).

**Trap:** `partial_remediation` — After adding the new trap, FR-189's `test_no_other_traps_changed` also needed updating to include `infrastructure_self_exempt` in its expected set. Fixing only the new file would have left the guard incomplete.

**Heuristic:** When graduating a Knowledge Graph entry, every existing test that enumerates the section must be updated to include the new entry. The enumeration test is itself infrastructure — and per the newly graduated trap, infrastructure must not exempt itself from completeness checks.

**Seed:** Should the Knowledge Graph tests be auto-generated from a machine-readable source (e.g., parsing the YAML block in copilot-instructions.md) rather than maintaining parallel string literals in each test file? Three graduation FRs would mean three test files with overlapping trap dictionaries — a `false_duplicate` waiting to drift.
