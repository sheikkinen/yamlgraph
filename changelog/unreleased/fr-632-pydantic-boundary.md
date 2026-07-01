---
type: fix
scope: graph
req: REQ-YG-004
---
- **FR-632 Pydantic boundary normalization**: LLM structured outputs are now `model_dump()`'d to plain dicts before storing in state. Fixes `tojson` crashes in downstream Jinja2 prompts.
