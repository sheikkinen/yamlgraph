---
type: removal
scope: hooks
req: REQ-YG-720
---
- **FR-1134 Retire FR knowledge graph and FR-275 meta-tests**: Removes the stale FR-814 knowledge graph (`scripts/extract_fr_graph.py`, `reference/fr-knowledge-graph.{yaml,md}`, its fixture, `test_fr_graph.py`, CAP-240) and the prior-art hook's graph cluster boost. Hook output is unchanged: it is byte-identical before and after across all 243 FRs above FR-819. `test_fr275_test_speed_optimization.py` shrinks from 13 tests, including subprocess pytest re-runs, to a single marker-registration check. REQ-YG-275 now covers only that check. Summed test time saved is about 137 s. (REQ-YG-720)
