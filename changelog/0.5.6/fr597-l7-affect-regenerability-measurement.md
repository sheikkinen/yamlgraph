---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-597 L7 affect-regenerability ruler**: Added a diagnostic `l7_measure` graph (the affect port of FR-594's `l5_measure`) measuring whether an L7 affect encoding's emotional arc is regenerable from the affect deltas alone, on two orthogonal axes — deterministic *simulability* (`[UNDERDETERMINED]` markers / affect-bearing beats) and an advisory LLM *fidelity* judge. New pure tools `render_l7_affect`/`score_affect_simulability`/`combine_l7_measure`, prompts `regenerate_affect_arc`/`judge_affect_fidelity`, and `run.py --mode measure-l7` with a corpus-POOLED headline. The binary anti-deferral exit fired **branch (b) — thesis REFUTED**: the GT affect skeleton is regenerable (pooled under-determination 0.464 < 0.70; detective `betrayal→Hagen` regenerated cleanly), so `affect_recall` stands as the primary L7 gate and the protagonist-throughline encoder work resumes against its original ≥0.50 gate. Diagnostic only; FR-578 gate untouched. (REQ-YG-020)
