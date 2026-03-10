---
type: feat
scope: sequential
---
- **FR-175 Sequential Enforcement Mode**: Replace parallel `nohup ... &` enforcement spawning in `.chaplain/watch.sh` with sequential queue. Each enforcement pipeline completes before the next starts, eliminating merge conflicts on shared bookkeeping files (ARCHITECTURE.md, CHANGELOG.md, req_coverage.py).
