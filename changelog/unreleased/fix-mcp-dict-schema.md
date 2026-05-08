---
type: fix
scope: mcp
---
- **MCP schema**: normalize bare `dict` state fields to `{"type": "object", "additionalProperties": {}}` so graphs with dict-typed inputs are included in MCP typed tools instead of excluded. Fixes FR-355 gate test and four graphs (booking-assistant, encounter-turn, ocr-cleanup, yamlgraph-generator).
