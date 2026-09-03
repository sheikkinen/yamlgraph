---
type: fix
scope: hooks
req: REQ-YG-631
---
- **FR-889 docs exception removed**: `docs/` and `feature-requests/` join the OS-locked governed roots — agents have no business writing to main; only runtime lanes (`tmp/`, `logs/`, `changelog/`) stay open. `main-lock.json` marker gitignored. (REQ-YG-631)
