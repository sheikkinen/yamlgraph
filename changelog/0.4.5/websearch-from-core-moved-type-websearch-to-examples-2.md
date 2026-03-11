---
type: removal
scope: websearch
---
- **Websearch from core** - Moved `type: websearch` to examples (243 LOC)
  - `yamlgraph/tools/websearch.py` deleted
  - Removed `websearch_tools` parameter from graph_loader, node_compiler, agent
  - Core LOC: 9,958 → 9,694 (-264 lines)
