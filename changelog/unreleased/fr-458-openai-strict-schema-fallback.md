---
type: fix
scope: agent
---
- **FR-458 OpenAI strict schema fallback**: When OpenAI rejects a JSON schema lacking `additionalProperties: false`, retry `with_structured_output()` using `method="function_calling"` for lenient schema handling.
