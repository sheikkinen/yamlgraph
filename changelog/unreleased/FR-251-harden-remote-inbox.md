---
type: feat
scope: chaplain
req: REQ-YG-255
---
- **FR-251 Harden Remote Inbox**: `watch.sh` gates GitHub Issue imports on `.chaplain/allowed-authors.txt` author allowlist, truncates bodies exceeding 10,000 characters, and prepends `<!-- author: @login -->` forensic audit header to every imported file. Untrusted authors are skipped with the `chaplain` label retained for manual review. (REQ-YG-255)
