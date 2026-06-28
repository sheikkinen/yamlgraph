---
type: feat
scope: linter
req: REQ-YG-473
---
- **FR-586 W026 Prompt-Monolith Lint**: `yamlgraph graph lint` now warns (W026) when a prompt fuses too many independent judgements into one LLM call — the attention-overload anti-pattern that starves the hardest judgement under load. Two static detectors: inline-schema top-level field count (default ≥4, configurable via the `field_threshold` parameter) and a curated set of prose phrases (enumerated multi-output, global cross-unit constraints). Warning severity only; lint exit semantics unchanged. (REQ-YG-473)
