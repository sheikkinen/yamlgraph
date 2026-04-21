---
type: feat
scope: chaplain
req: REQ-YG-247
---
- **FR-243 GitHub Issues Remote Inbox**: `watch.sh` polls GitHub Issues labeled `chaplain` into local inbox via two-pass `gh` CLI, removes label after import, closes issue with commit reference on successful enforcement. Gracefully skips when `gh` is unavailable. (REQ-YG-247)
