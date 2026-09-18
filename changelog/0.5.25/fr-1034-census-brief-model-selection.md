---
type: feat
scope: census
req: REQ-YG-675
---
- **FR-1034 Independent model selection for the census brief**: the synthesis
  call takes its own `brief_provider`/`brief_model`, each falling back
  independently to `provider`/`model`, so a cheap per-item model no longer
  forces itself on the one long synthesis call. `render_brief` now stamps the
  model that actually produced the brief and raises rather than reverting to
  the per-item model. (REQ-YG-675)
