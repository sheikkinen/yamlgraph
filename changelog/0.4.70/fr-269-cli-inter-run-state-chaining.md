---
type: feat
scope: cli
req: REQ-YG-267
---
- **FR-269 CLI Inter-Run State Chaining**: `--import-state` and `--export-state` flags for `yamlgraph graph run` enable external orchestrators to chain graph invocations across shell boundaries while preserving state, including `CopilotResult.session_id` for copilot session resume. (REQ-YG-267, REQ-YG-268)
