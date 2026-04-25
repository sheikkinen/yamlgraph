---
type: feat
scope: watcher2
req: REQ-YG-309
---
- **FR-285 Watcher2 Forensic Failure Diary**: Added automated forensic analysis to watcher2's handle_failure function that captures failure context (reason, topic content, logs, worktree state), performs LLM-driven root cause analysis, and generates structured diary entries in docs/diary/ with evidence and recommendations for institutional learning. (REQ-YG-309)