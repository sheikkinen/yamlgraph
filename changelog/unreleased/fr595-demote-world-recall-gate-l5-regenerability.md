---
type: fix
scope: plot-modeller
req: REQ-YG-020
---
- **FR-595 Demote world_recall, gate L5 on regenerability discrimination**: The L5
  layer no longer gates on `world_recall` (which FR-594 proved scores agreement
  with a lossy ground-truth predicate skeleton, not story capture). `summarise_l5`
  now emits `verdict: "informational"` and retains `world_recall` as a diagnostic.
  The powered L5 gate is the new `measure_l5_verdict` pure tool — the GT-anchored
  simulability discrimination (`gt_sim − ours_sim`, corpus mean), grounded in the
  FR-594 power analysis (n=5, paired gap 0.337 ± 0.035, t(4)=21.6). The live corpus
  flips from a false KILL (world_recall 0.49) to GO (gap 0.294). (REQ-YG-020)
