---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-594 L5 prose-regenerability measurement graph**: Graduate the
  `spike_regenerate_prose.py` probe into a declarative five-node graph
  (`l5_measure.yaml`): render L5 beats → regenerate the chapter from only the
  world-state machine → count `[UNDERDETERMINED]` markers (deterministic
  simulability) → judge the regen against the synopsis (LLM fidelity) →
  `combine_l5_measure` into a two-axis verdict that keeps the axes orthogonal and
  attributable (never one averaged scalar). Adds three pure tools
  (`render_l5_beats`, `score_simulability`, `combine_l5_measure`), a
  `judge_fidelity` prompt, eleven `REQ-YG-020` unit tests, and a
  `run.py --mode measure-l5` corpus runner. Diagnostic only — `world_recall`
  remains the primary L5 signal. The acceptance run reproduced the probe's
  discrimination (ours simulability 0.313 ≪ gt 0.697) and witnessed the fidelity
  judge firing non-empty `inverted` on scifi climax-drift. The retired spike is
  deleted. (REQ-YG-020)
