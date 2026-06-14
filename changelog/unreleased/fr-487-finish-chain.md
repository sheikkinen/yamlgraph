---
type: fix
scope: examples
---
- **FR-487 DM v2 finish chain**: Accepting a closing artifact now walks the DM
  through all three — the continuous Final Cut (FR-484) → the turn-structured
  Final Cut (FR-485) → the full-text Walkthrough (FR-487) — instead of stranding
  the page on the first finish (the reported "Final Cut shown, then the page
  closed"). The chain also drafts the FR-485 cut spine the Walkthrough renders, so
  the rendered finish is reachable through Accept without a manual breadcrumb
  detour. The Walkthrough is the true terminal leaf; accepting it stays put.
