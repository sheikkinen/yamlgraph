---
type: feat
scope: tools
---
- **FR-892 Corpus-Census Pipeline — Tool-Slot Binding**: graph `tools:`
  entries may declare `slot: true` with a `contract:` block; callers bind
  FR-768 manifests at invocation via repeatable `--tool SLOT=manifest.yaml`.
  Contaminated bindings (missing, duplicate, undeclared, invalid manifest,
  contract mismatch) fail closed with `ToolSlotBindingError` before any
  LLM call. Ships `examples/demos/corpus_census/` — the shared
  discover–extract–map–reduce census pipeline consuming the slots, with a
  fail-closed 8-column evidence ledger (md+jsonl). Two proof
  configurations shipped as manifest pairs + rubric only: PDF-library
  census and git-history intent-timeline census. (REQ-YG-018)
