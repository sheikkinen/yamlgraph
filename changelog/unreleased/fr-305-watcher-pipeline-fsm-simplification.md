---
type: feat
scope: watcher
req: REQ-YG-316
---
- **FR-305 Watcher Pipeline FSM Simplification**: Collapsed 20+ state pipeline into 6 operational states + 3 terminals. Judge uses different model from plan with fresh session for bias diversity. Enforce session resumes plan session for full context continuity. Dispatcher flag-gated via `pipeline_version` context key. (REQ-YG-316)
