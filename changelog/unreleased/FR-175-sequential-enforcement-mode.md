---
type: feat
scope: sequential
req: REQ-YG-158
---
- **FR-175 Sequential Enforcement Mode**: Replace parallel `nohup ... &` enforcement spawning in `.chaplain/watch.sh` with a sequential queue that waits for each enforcement pipeline to complete before starting the next. Eliminates concurrent PR merge conflicts by serializing enforcement. (REQ-YG-158)
