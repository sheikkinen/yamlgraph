---
type: fix
scope: agent
---
- **FR-456 Structured Output JSON Fallback**: When `with_structured_output()` fails (provider rejects `response_format`), fall back to lenient `model_construct()` from `extract_json()` parsed content instead of crashing. Recovers structured verdicts from models like DeepSeek that complete agent loops but don't support the formal structured output API. (REQ-YG-010)
