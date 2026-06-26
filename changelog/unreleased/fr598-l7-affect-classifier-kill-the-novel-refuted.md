---
type: removal
scope: plot-modeller
req: REQ-YG-020
---
- **FR-598 L7 affect throughline — kill the novel (hypothesis REFUTED)**: Rewrote
  `affect_throughline.yaml` from free-prose narration into a single-pass per-beat
  **classifier** (typed YAML, closed verbatim vocabulary, default none, no cross-beat
  connective tissue, the "every arc that opens should close" completion mandate
  **deleted**), **retired** `encode_affect.yaml` (two-pass collapsed to one node), and
  updated `spike_affect.py` coherently. Measured against the frozen FR-578 gate the
  hypothesis was **refuted**: `detection` collapsed 0.52 → 0.24 and `affect_recall`
  regressed 0.15 → 0.06. Reading the raw output (`read_raw_output_first`) showed the
  failure mode inverted — the prose flooded (recall rewards shots on goal) while the
  terse classifier went near-silent (Marren 2 ops vs GT 8). The one permitted format
  iteration is spent; the residual is a real beat-alignment / kind-discrimination
  ceiling that fires the reserved escalation, not a second wording pass. The frozen
  FR-578 evaluator was not modified. (REQ-YG-020)
