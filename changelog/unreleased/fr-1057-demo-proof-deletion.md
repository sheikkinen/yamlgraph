---
type: fix
scope: ci
req: REQ-YG-685
---

- **FR-1057 The demo-proof gate cannot be satisfied by a deletion**: The CI gate collected every demo directory touched by a diff and demanded a fresh `demo-output.log` for each, so retiring a demo created an obligation with no possible discharge. A demo whose directory is absent at HEAD is now skipped; the proof obligation for demos that continue to exist is unchanged. (REQ-YG-685)
