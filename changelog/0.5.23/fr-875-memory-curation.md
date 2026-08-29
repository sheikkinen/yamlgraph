---
type: feat
scope: examples
req: REQ-YG-620
---
- **FR-875 Memory-Corpus Curation Graph (selective amnesia)**: `examples/memory-curation/` judges every repo-scope memory note (map node; keep/redact/forget + audience + staleness with cited evidence) and renders a human-review disposition draft under `tmp/memory-curation/` only. Deterministic collect freezes the corpus; reconcile proves count-in == count-out with Pydantic cross-field invariants; apply executes amnesia only under a hash-bound written sign-off and refuses all mutation on live-file drift. Judge-stage egress is provider-gated (vertex/azure approved). (REQ-YG-620)
