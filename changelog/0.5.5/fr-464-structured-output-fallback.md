---
type: feat
scope: executor
req: REQ-YG-464
---
- **FR-464 Structured Output JSON Fallback**: When `with_structured_output()` fails (DeepSeek V4 thinking mode rejects `response_format`), fall back to schema-hinted plain invoke + `extract_json()` + `model_validate()`. Covers `executor.py` and `race_node.py`. (REQ-YG-464, REQ-YG-465)
