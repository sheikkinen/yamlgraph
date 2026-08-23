---
type: fix
scope: race
---
- **Race node success marker**: Race node now logs `Node <name> completed successfully` on the winning path, matching llm/control nodes — a race-only demo previously could not satisfy the FR-325 demo-log success-evidence gate despite succeeding.
