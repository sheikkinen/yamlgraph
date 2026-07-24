---
type: fix
scope: hooks
---
- **PermissionRequest decision-hook misregistration**: the FR-743
  plain-text session probe was registered on `PermissionRequest`, a
  fail-closed decision hook — every permission in non-interactive
  child CLI sessions (judge/review adapters) was denied with
  "PermissionRequest hook failed". Probe unregistered from the
  decision hook; witness test pins the boundary (observability probes
  on fail-open notification events only).
