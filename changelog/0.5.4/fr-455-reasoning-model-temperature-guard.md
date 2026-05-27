---
type: fix
scope: llm
---
- **FR-455 Reasoning Model Temperature Guard**: `create_llm()` detects OpenAI reasoning models (`o1-*`, `o3-*`, `o4-*`) and omits the `temperature` parameter, which these models reject with a 400 error. (REQ-YG-010)
