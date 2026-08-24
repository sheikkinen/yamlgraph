---
type: feat
scope: examples
---
- **FR-879 Image Pipeline v2**: critic-filtered prompt pipeline — one
  LLM node generates candidates, the FR-876 deviant-daily critic scores
  them (per-register NLL band + boundary), only top-k survivors render
  via Replicate z-image. Frozen-critic alternative to LLM-as-judge.
