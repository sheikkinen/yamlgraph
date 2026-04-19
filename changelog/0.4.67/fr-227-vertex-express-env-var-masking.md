---
type: fix
scope: llm_factory
---
- **FR-227 Vertex Express env-var masking**: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and `VERTEXAI_PROJECT` are now temporarily removed from `os.environ` during `ChatGoogleGenerativeAI` construction in Express mode (`VERTEX_API_KEY` set), preventing the google-genai SDK from silently falling back to ADC auth. Env vars are unconditionally restored after construction (including on exception). `_VERTEX_CONSTRUCT_LOCK` and `_masked_env` added to `llm_factory`. (REQ-YG-010)
