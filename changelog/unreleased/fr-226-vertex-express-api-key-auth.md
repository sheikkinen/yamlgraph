---
type: feat
scope: llm_factory
---
- **FR-226 Vertex Express API Key Auth**: `_create_vertex_llm` now supports Express mode — when `VERTEX_API_KEY` is set, passes `google_api_key` without `project`/`location`, avoiding the SDK `ValueError` on key+project collision. ADC branch (project+location) unchanged.
