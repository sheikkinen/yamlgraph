---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-599 L7 affect-recall miss-decomposition probe**: Read-only diagnostic
  (`examples/plot_modeller/probe_l7_misses.py`) that partitions every GT affect delta the
  frozen FR-578 gate counts as a miss into five mutually-exclusive buckets (UNLICENSED /
  ABSENT / BEAT-OFF / KIND-WRONG / TOWARD-WRONG), each × window (±1/±2/±3) × op
  (open/close), ties out to the gate's own `_l7_counts` recall_hits, and routes the
  reserved escalation to one named lever. Verdict on the haiku corpus: **MULTI-CAUSE** —
  UNLICENSED ground truth and model-scale ABSENT tied at 39%, so no single lever clears
  the floor. The UNLICENSED bucket uses a fixture-pinned, conservatively-gated LLM
  licensing pass (`affect_licensing.yaml`); reading every (e) member caught an open-biased
  judge and flipped the verdict from single- to multi-cause. (REQ-YG-020)
