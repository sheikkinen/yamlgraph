---
type: fix
scope: scripts
---
- **FR-739 per-session cost view**: `tap.py` prints a per-session table
  (exact tokens, calibrated credits, LIVE/idle) answering "what do
  ongoing sessions cost"; README gains a cost cookbook (tap vs ledger,
  seam semantics, pricing anchors, tap arming). Session titles joined
  from chatSessions `customTitle` into both tap and ledger seam tables.
