---
type: feat
scope: rag
---
- **RAG Tool Demo Fixes & Script**
  - Fixed `examples/rag/graph.yaml` structure: flat YAML (not nested `graph:`), proper `from/to` edges
  - Added `rag_retrieve_node()` state-based wrapper for `type: python` nodes
  - Fixed `prompts/answer.yaml` schema format (`schema:` with `name/fields`)
  - Added `examples/rag/demo.sh` script for one-command demo execution
  - Added `vectorstore/` to `.gitignore`
