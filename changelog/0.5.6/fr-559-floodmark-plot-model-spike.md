---
type: feat
scope: examples
---
- **FR-559 floodmark plot-model spike (M0)**: standalone `unified-planning` spike under
  `examples/dungeon_master/spikes/floodmark_up/` proving a classical planner can author the typed
  floodmark `PlotPlan`, compile belief-as-fluent, and prove the early-reveal variant unsolvable
  (complete blind-A* search) while the world-revival variant trips the hand-written
  monotonic-lifecycle invariant. Optional `unified-planning[fast-downward]` install; the test
  skips gracefully when absent.
