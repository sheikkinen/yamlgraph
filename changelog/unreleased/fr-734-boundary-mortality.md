---
type: fix
scope: examples
req: REQ-YG-561
---
- **FR-734 CWE Boundary Run-Mortality**: the FR-733 baseline killed 19
  of 33 runs at the reducer boundary. Off-population claims (real
  catalog rows without view-699 membership — the model volunteers
  famous MITRE-Discouraged Classes from prior knowledge) now divert to
  `meta.off_population_claims` with best-effort spans instead of
  killing the run; classification slots stay population-only;
  nonexistent codes still raise. Span alignment gains multi-block
  interior-omission repair (coverage ≥ 0.85, window-capped): elided
  enumeration markers and list segments repair to the true contiguous
  window restoring the elided text verbatim; scattered fabrications
  still die. Loader ships a full-catalog `usage_index` via merged dict
  return. (REQ-YG-561)
