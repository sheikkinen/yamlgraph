---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-587 L5 snapshot-then-diff spike (Gate 1 KILL)**: Added a comprehend/represent
  spike for the plot_modeller L5 wound — Node A emits per-beat world-state
  *snapshots* (`prompts/assign_pre_eff_snapshot.yaml`) and a deterministic
  `diff_snapshots` helper (`nodes/tools.py`) computes the salient change
  (intra-chapter `at`-run collapse + first-departure-only). Gate 1 on
  `claude-haiku-4-5`: `at`-FP fell only 86→69 (still 85% of all FPs) with recall
  0.32 — below the 0.50 floor — so the snapshot+diff seam is falsified at this tier
  and the work escalates to FR-578 (larger model). `diff_snapshots` ships as a
  unit-tested pure helper regardless of the spike verdict. (REQ-YG-020)
