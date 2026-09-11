---
type: feat
scope: scripts
req: REQ-YG-678
---

- **FR-1047 Clean dirty main**: `scripts/dirty_main_triage.py` classifies each dirty path on the main checkout by content provenance — `TARGET_IDENTICAL` (bytes equal `origin/main` at the same path) is the only safe class; `KNOWN_BLOB`, `UNSEEN_BLOB`, unsupported git states and failed probes all preserve and exit non-zero. A non-regular target mode in `origin/main` (symlink, gitlink) is never safe even when the bytes match, malformed porcelain records can never become untracked files, and a reported `KNOWN_BLOB` source revision is verified to contain the blob rather than merely to have deleted it. The `clean-dirty-main` skill runs the classifier before any mutation, stops before unlocking on any non-safe result, cleans only explicit pathspecs, and restores the FR-889 lock on every exit. (REQ-YG-678)
