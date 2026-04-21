---
type: feat
scope: copilot
req: REQ-YG-265
---
- **FR-266 Copilot Node Model Selection**: Support `model` as a top-level node config key for copilot nodes, with fallback to `defaults.model` from graph metadata. Model resolution follows `cli_flags.model` > node-level `model` > `defaults.model` > omit. (REQ-YG-265)
