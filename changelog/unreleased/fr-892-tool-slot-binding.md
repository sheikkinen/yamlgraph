---
type: feat
scope: tools
---
- **FR-892 Corpus-Census Pipeline — Tool-Slot Binding**: graph `tools:`
  entries may declare `slot: true` with a `contract:` block; callers bind
  FR-768 manifests at invocation via repeatable `--tool SLOT=manifest.yaml`.
  Contaminated bindings (missing, duplicate, undeclared, invalid manifest,
  contract mismatch) fail closed with `ToolSlotBindingError` before any
  LLM call. (REQ-YG-018)
