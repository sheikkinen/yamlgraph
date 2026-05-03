---
type: fix
scope: chaplain
---
- **Judge prompt anchoring**: Judge prompt now uses explicit `{fr_path}` variable instead of unanchored `feature-requests/` directory reference, preventing evaluation of wrong FR in fresh sessions.
