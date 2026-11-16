---
type: fix
scope: authoring
req: REQ-YG-728
---
- **FR-1161 Authoring-proof checks accept Windows report paths**: `scripts/check_authoring_proof.py` and `scripts/author.sh` replace `\` with `/` when reading `tmp/draft-authoring-report.md`, so a report written on Windows no longer fails the proof for files that exist. (REQ-YG-728)
