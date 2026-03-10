---
type: removal
scope: langsmith
---
- **LangSmith utils from core** - Moved to `examples/demos/run-analyzer/` (464 LOC)
  - `yamlgraph/utils/langsmith.py` → `examples/demos/run-analyzer/utils/`
  - `yamlgraph/utils/langsmith_trace.py` → `examples/demos/run-analyzer/utils/`
  - Tests moved to `examples/demos/run-analyzer/tests/`
  - **Breaking:** `from yamlgraph.utils.langsmith import` no longer works
  - Core LOC: 9,694 → 9,266 (-428 lines)
