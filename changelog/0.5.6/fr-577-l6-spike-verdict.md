---
type: feat
scope: examples
---
- **FR-577 L6 spike GO (enables 0.96)**: end-to-end causality layer —
  `assign_causality` graph/prompt, `run.py --mode assign-causality` (Mode 6),
  and the `main_l6` evaluator (`score_l6`/`summarise_l6`). Spike across 5
  synopses: enables recall 43/45 (0.96) ≥ 0.75 gate → GO, precision 43/46
  (0.93). motivation/threatens recall are informational (J:C3); agent-only
  recall 0.83/0.81 vs full recall 0.26/0.00 isolates a goal-vocabulary gap
  (forward signal for FR-583), not a comprehension gap. Unblocks FR-578 (L7).
