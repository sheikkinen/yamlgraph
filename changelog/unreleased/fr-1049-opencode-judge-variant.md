---
type: feat
scope: judge
req: REQ-YG-682
---
- **FR-1049 opencode judge variant**: the sole-route judge adapter gains a third backend node `judge_opencode` (`backend: opencode`, a single `provider/model` pin, no tool/permission flag), selected by three mutually exclusive state-conditioned edges. `scripts/judge.sh` admits `opencode` in the closed backend set (`copilot|claude|opencode`). (REQ-YG-682)
