---
type: feat
scope: copilot
req: REQ-YG-265
---
- **FR-266 Copilot Node Model Selection**: Copilot nodes now support `model` at the node level and `defaults.model` fallback, consistent with LLM nodes. Priority chain: `cli_flags.model` > node-level `model` > `defaults.model` > omit. (REQ-YG-265)
