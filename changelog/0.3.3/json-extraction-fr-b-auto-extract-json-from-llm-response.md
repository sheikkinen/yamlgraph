---
type: feat
scope: json
---
- **JSON Extraction** (FR-B) - Auto-extract JSON from LLM responses
  - Node-level `parse_json: true` extracts JSON from markdown code blocks
  - `extract_json()` utility in `yamlgraph.utils`
  - Cascading extraction: raw → ```json``` → ```...``` → `{...}` pattern
  - See [reference/graph-yaml.md](reference/graph-yaml.md#type-llm---standard-llm-node)
