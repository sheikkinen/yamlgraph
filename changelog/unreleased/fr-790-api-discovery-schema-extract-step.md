---
type: feat
scope: examples
req: REQ-YG-594
---
- **FR-790 API Discovery Schema-Extract Step**: routed llm graph under `examples/api-discovery/steps/schema-extract/` turns a confirmed platform into a nine-field `CapabilityReport`. v1 frozen to OpenAPI (deterministic `tool_call` on FR-783 `parse_openapi` → llm mapping into `EndpointInfo` entries) and CKAN (llm extraction of dataset count, orgs, freshness, languages from the FR-788 `sample_response`); other families return a structured `limitations` entry, never inference or error. All llm nodes `on_error: fail`. Committed OpenAPI/CKAN fixtures; exposed to the orchestrator as `schema_extract.tool.yaml`. (REQ-YG-594)
