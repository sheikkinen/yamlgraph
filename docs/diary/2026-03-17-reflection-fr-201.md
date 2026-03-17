# Diary: FR-201 Checkpointer String Shorthand

**Date:** 2026-03-17
**FR:** FR-201
**Theme:** Boundary normalization and traceability completeness

## Reflection

A three-line code change — `if isinstance(config, str): config = {"type": config}` — was already implemented but lacked the full traceability chain: no requirement, no test, no feature request, no capability entry, no changelog. The implementation was correct but invisible to the project's audit infrastructure.

**Trap:** `partial_remediation` — The code change was made at the right boundary (entry to `get_checkpointer`), but without the surrounding artifacts it was an undocumented behavior change. A future contributor wouldn't know this was intentional, tested, or tracked.

**Heuristic:** A code change without its traceability chain is a hypothesis, not a feature. The doctrine's full pipeline (FR → REQ → CAP → test → changelog → diary) exists not for ceremony but for auditability. The cheapest part of this work was the code; the most valuable part was the tests that prove the boundary contract.

**Observation:** The normalization itself is a textbook application of `the_one_law`: normalize at the boundary where external data enters. YAML configs may deliver either `checkpointer: memory` (string) or `checkpointer: {type: memory}` (dict). Converting at entry means every downstream path sees a consistent dict — no scattered `isinstance` checks.

**Seed:** Should `graph_loader.py` enforce this normalization during YAML parsing (schema level), making the factory's string acceptance redundant? Or is defense-in-depth at both layers the right call for a boundary that crosses YAML → Python?
