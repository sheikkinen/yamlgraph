---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-591 Perspective-to-L5 conversion graph**: Promote the per-character L5
  decomposition from a throwaway Python spike into a proper YAMLGraph graph — an
  outer `perspective_l5.yaml` (map-over-agents) fanning out an inner
  `perspective_agent.yaml` subgraph (viewpoint prose → typed encoding →
  `parse_perspective` assembly), then a deterministic `combine_perspectives`
  union into the unified per-beat L5. Adds a `perspective` run mode and a
  `spike_perspective.sh` driver; conversion is separated from scoring. The
  per-character ENCODING contract is **provisional** (recall-preserving,
  precision-open). (REQ-YG-020)
