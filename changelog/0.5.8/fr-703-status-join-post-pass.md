---
type: feat
scope: demos
req: REQ-YG-535
---
- **FR-703 Recap Status Join Post-Pass**: the FR-id → status join in the recap demo moved from model to code — `attach_statuses` post-pass parses the `fr_statuses` grep lines into an id→status map (trimmed, duplicate-id first-wins) and appends `[Status: …]` tags deterministically, with per-id tags when a merged workstream's statuses differ. The prompt sheds all disposition language and gains a full-id formatting bound. Kills the silent join-failure class from the FR-702 field run (`[no FR status]` on FRs whose statuses exist) and the `[Status: **Status:** …]` double prefix. (REQ-YG-535)
