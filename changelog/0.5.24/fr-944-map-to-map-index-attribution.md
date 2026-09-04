---
type: fix
scope: graph
req: REQ-YG-568
---
- **FR-944 Map-to-Map Index Attribution**: chained map nodes (`map1 -> map2`) now compile through a generated post-fan-in pass-through join, so the second fan-out fires once on merged state. Previously the downstream Send router fired per upstream branch on task-local state: every second-map branch received `_map_index: 0`, fan-in order was race-timing arbitrary, error rows were attributed to index 0, and an independent `over` list fanned out N×M. A synthetic join-name collision now fails compilation explicitly. (REQ-YG-568)
